import importlib.util
import unittest
import warnings
from unittest.mock import patch
import numpy as np
import pandas as pd
from hci_eval.synthetic import generate_demo
from hci_eval.questionnaire import preprocess_questionnaire, build_dv_long
from hci_eval.openface import build_pivots_from_timestamp, compute_segment_masks, aggregate_sessions
from hci_eval.validation import validate_questionnaire, validate_frames, ECSCW_PHASE
from hci_eval.data import select_participants

HAS_STATS = all(importlib.util.find_spec(m) is not None for m in ['scipy','statsmodels'])


class DataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.q, cls.f, cls.e = generate_demo(n_people=8)

    def test_reverse_scores_and_ignored_original_q9(self):
        q = self.q.copy()
        mask = (q.Original_Phase==2) & (q.Question==2)
        q.loc[mask,'Score'] = 7
        prepared = preprocess_questionnaire(q)
        self.assertTrue(prepared.loc[mask[prepared.index],'Score_star'].eq(1).all())
        self.assertTrue(prepared.loc[mask[prepared.index],'Score_raw'].eq(7).all())
        self.assertFalse(((prepared.Original_Phase==1) & (prepared.Question==9)).any())

    def test_trait_centering_counts_people_once(self):
        # Use unequal phase coverage without duplicate keys.
        q = self.q[~((self.q.Participant_ID=='SYN_001') & (self.q.Original_Phase==4))].copy()
        p = preprocess_questionnaire(q)
        dedup = p.drop_duplicates('Participant_ID')
        self.assertAlmostEqual(dedup.E_c.mean(),0,places=12)

    def test_dimension_requires_all_items(self):
        p = preprocess_questionnaire(self.q)
        complete = build_dv_long(p)
        missing = p[~((p.Participant_ID=='SYN_001') & (p.Original_Phase==1) & (p.Condition==1) & (p.Question==1))]
        reduced = build_dv_long(missing)
        key = lambda x: x[(x.Participant_ID=='SYN_001') & (x.Original_Phase==1) & (x.Condition==1) & x.DV.str.contains('Anthropomorphism')]
        self.assertEqual(len(key(complete)),1)
        self.assertEqual(len(key(reduced)),0)

    def test_invalid_and_duplicate_records_rejected(self):
        with self.assertRaisesRegex(ValueError,'duplicate'):
            validate_questionnaire(pd.concat([self.q,self.q.iloc[:1]]))
        q = self.q.copy()
        q.loc[0,'Score'] = 8
        with self.assertRaisesRegex(ValueError,'1..7'):
            validate_questionnaire(q)
        q = self.q.copy()
        q.loc[0,'E'] += 1
        with self.assertRaisesRegex(ValueError,'inconsistent'):
            validate_questionnaire(q)

    def test_phase_mapping_does_not_confuse_persona_and_interruption(self):
        self.assertEqual(ECSCW_PHASE[4],3)
        self.assertIsNone(ECSCW_PHASE[3])

    def test_event_cutoff_and_first_event_merge_rule(self):
        events = pd.DataFrame({'start':[5,5.01,8.01,8.02,10.9,12], 'interruption':[1]*6})
        pivots = build_pivots_from_timestamp(events,'start','interruption')
        self.assertEqual(pivots,[5.01,8.02,12])

    def test_window_union_and_nearest_timestamp_tie(self):
        frames = pd.DataFrame({'timestamp':np.arange(0,16,.5)})
        inside, outside, all_mask, aligned = compute_segment_masks(frames,[6.25,9.5])
        self.assertEqual(aligned,[6.,9.5])
        self.assertEqual(int(inside.sum()),19) # inclusive union 5.5..14.5
        self.assertTrue(np.all(inside ^ outside))
        self.assertTrue(all_mask.all())

    def test_missing_events_remain_missing_not_full_session(self):
        events = self.e[self.e.Participant_ID!='SYN_001']
        au = aggregate_sessions(self.f,events)
        no_windows = au[(au.Participant_ID=='SYN_001') & (au.Original_Phase==2)]
        self.assertTrue(no_windows.DV_value.isna().all())
        self.assertTrue(no_windows.n_frames.eq(0).all())

    def test_timestamp_outside_coverage_rejected(self):
        events = self.e.copy()
        events.loc[0,'start'] = 30
        with self.assertRaisesRegex(ValueError,'coverage'):
            aggregate_sessions(self.f,events)

    def test_frames_invalid_intensity_rejected(self):
        f = self.f.copy()
        f.loc[0,'AU12_r'] = 6
        with self.assertRaisesRegex(ValueError,'0..5'):
            validate_frames(f)

    def test_keep_list_selection_never_mutates_input(self):
        before = self.q.copy(deep=True)
        kept, report = select_participants(self.q,['SYN_001'])
        self.assertEqual(report['participants_after'],1)
        self.assertEqual(kept.Participant_ID.nunique(),1)
        pd.testing.assert_frame_equal(self.q,before)

    def test_synthetic_inputs_reproducible(self):
        for a,b in zip(generate_demo(seed=1,n_people=3),generate_demo(seed=1,n_people=3)):
            pd.testing.assert_frame_equal(a,b)


@unittest.skipUnless(HAS_STATS,'SciPy/statsmodels not available in current environment')
class StatisticalTests(unittest.TestCase):
    def test_corrections_match_statsmodels_with_missing_values(self):
        from statsmodels.stats.multitest import multipletests
        from hci_eval.statistics import bh_fdr, holm_bonferroni
        p = np.array([.2,.01,np.nan,.01,0,1,.051])
        valid = ~np.isnan(p)
        for function,method in [(bh_fdr,'fdr_bh'),(holm_bonferroni,'holm')]:
            adjusted = function(p)
            np.testing.assert_allclose(adjusted[valid],multipletests(p[valid],method=method)[1])
            self.assertTrue(np.isnan(adjusted[~valid]).all())

    def test_nonconverged_fit_is_reported_without_new_fallback(self):
        from hci_eval.statistics import fit_mixedlm
        class Result:
            converged = False
            cov_re = pd.DataFrame([[1,0],[0,.2]])
        class Model:
            def fit(self,**kwargs):
                warnings.warn('test optimizer did not converge',RuntimeWarning)
                return Result()
        data = pd.DataFrame({'Participant_ID':['SYN_001','SYN_002'], 'Condition01':[0,1]})
        with patch('statsmodels.formula.api.mixedlm',return_value=Model()) as factory:
            result, diagnostic = fit_mixedlm('y ~ Condition01',data)
        self.assertFalse(diagnostic['converged'])
        self.assertEqual(factory.call_count,1)
        self.assertIn('did not converge',diagnostic['attempts'][0]['warnings'][0])

    def test_historical_low_slope_variance_fallback(self):
        from hci_eval.statistics import fit_mixedlm
        class Result:
            converged = True
            def __init__(self,slope):
                self.cov_re = pd.DataFrame([[1,0],[0,slope]])
        class Model:
            def __init__(self,slope): self.slope = slope
            def fit(self,**kwargs): return Result(self.slope)
        data = pd.DataFrame({'Participant_ID':['SYN_001','SYN_002'], 'Condition01':[0,1]})
        with patch('statsmodels.formula.api.mixedlm',side_effect=[Model(1e-9),Model(1)]):
            result, diagnostic = fit_mixedlm('y ~ Condition01',data)
        self.assertEqual(diagnostic['re_structure_used'],'1')
        self.assertEqual(len(diagnostic['attempts']),2)

    def test_questionnaire_correction_families_preserved(self):
        from hci_eval.modeling import fit_models
        # Insufficient data exercises output and family construction without unstable optimization.
        q,_,_ = generate_demo(n_people=2)
        long = build_dv_long(preprocess_questionnaire(q))
        condition,traits = fit_models(long,'questionnaire')
        self.assertTrue(condition.correction.eq('holm').all())
        self.assertTrue(traits.family_columns.eq('Original_Phase,Effect,DV').all())
        self.assertTrue(traits.fit_review_required.all())
        self.assertTrue(traits.p_adjusted.isna().all())


if __name__ == '__main__':
    unittest.main()
