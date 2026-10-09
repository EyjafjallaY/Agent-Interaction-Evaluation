"""Synthetic demonstrations generated independently of participant records."""
import numpy as np
import pandas as pd
from .openface import AU_COMPUTE
from .validation import TRAITS


def generate_demo(seed=2026, n_people=48):
    rng = np.random.default_rng(seed)
    q_rows, frame_rows, event_rows = [], [], []
    times = np.arange(0, 20.01, .25)
    for i in range(n_people):
        person = f"SYN_{i+1:03d}"
        traits = dict(zip(TRAITS, rng.uniform(2,6,5)))
        age, gender = int(rng.integers(19,31)), "F" if i % 2 else "M"
        offset = rng.normal(0,.7)
        for phase, n_questions in [(1,12),(2,11),(4,11)]:
            order = int(rng.integers(1,3))
            slope = rng.normal(.2,.45)
            au_offset = rng.uniform(.2,1.5,4)
            au_slope = rng.normal(.15,.15,4)
            for condition in [1,2]:
                for question in range(1,n_questions+1):
                    value = 3.8 + offset + (condition-1)*slope + .1*(traits['E']-4)*(condition-1) + rng.normal(0,.65)
                    score = float(np.clip(np.round(value),1,7))
                    q_rows.append({"Participant_ID":person, "Original_Phase":phase, "Condition":condition,
                                   "Question":question, "Score":score, "Order_Sequence":order, "Age":age,
                                   "Gender":gender, **traits})
                for timestamp in times:
                    values = np.clip(au_offset+(condition-1)*au_slope+rng.normal(0,.12,4),0,5)
                    frame_rows.append({"Participant_ID":person, "Original_Phase":phase, "Condition":condition,
                                       "timestamp":float(timestamp),"confidence":float(rng.uniform(.75,1)), **dict(zip(AU_COMPUTE,values))})
                if phase == 2:
                    for start in [5.,6.,8.,12.]:
                        event_rows.append({"Participant_ID":person,"Original_Phase":phase,"Condition":condition,
                                           "start":start,"interruption":1})
    return pd.DataFrame(q_rows), pd.DataFrame(frame_rows), pd.DataFrame(event_rows)
