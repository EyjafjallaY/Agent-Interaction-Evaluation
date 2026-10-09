"""Reviewed analysis primitives adapted from archived study notebooks.
See docs/provenance.md and docs/methods.md for version boundaries.
"""
import numpy as np
import pandas as pd

AU_COMPUTE = ["AU06_r", "AU09_r", "AU12_r", "AU15_r"]

def build_pivots_from_timestamp(ts_df, start_col, int_col,
                               min_start_exclusive=5.0, merge_within=3.0):
    df1 = ts_df.copy()
    df1 = df1[df1[int_col] == 1].copy()
    df1 = df1.dropna(subset=[start_col])
    df1 = df1[df1[start_col] > min_start_exclusive].sort_values(start_col)

    starts = df1[start_col].values.astype(float)
    pivots = []
    if len(starts) == 0:
        return pivots

    i = 0
    while i < len(starts):
        first = starts[i]
        pivots.append(first)
        j = i + 1
        while j < len(starts) and (starts[j] - first) <= merge_within:
            j += 1
        i = j
    return pivots

def align_pivot_to_openface(pivot, of_timestamps):
    idx = np.searchsorted(of_timestamps, pivot)
    if idx <= 0:
        return float(of_timestamps[0])
    if idx >= len(of_timestamps):
        return float(of_timestamps[-1])
    left = of_timestamps[idx-1]
    right = of_timestamps[idx]
    return float(left if abs(left - pivot) <= abs(right - pivot) else right)

def compute_segment_masks(of_df, pivots, pre=0.5, post=5.0):
    ts = of_df["timestamp"].values.astype(float)
    all_mask = np.ones(len(ts), dtype=bool)
    if len(pivots) == 0:
        in_mask = np.zeros(len(ts), dtype=bool)
        out_mask = np.ones(len(ts), dtype=bool)
        return in_mask, out_mask, all_mask, []

    aligned = []
    in_mask = np.zeros(len(ts), dtype=bool)
    for p in pivots:
        pa = align_pivot_to_openface(p, ts)
        aligned.append(pa)
        lo = pa - pre
        hi = pa + post
        in_mask |= ((ts >= lo) & (ts <= hi))
    out_mask = ~in_mask
    return in_mask, out_mask, all_mask, aligned

def segment_means(of_df, mask, au_cols):
    sub = of_df.loc[mask, au_cols]
    means = {c: float(sub[c].mean()) for c in au_cols}
    return means, int(sub.shape[0])


def aggregate_sessions(frames, events):
    """Average AUs using the archived union-of-windows rules; preserve missing windows."""
    from .validation import validate_frames, validate_events
    validate_frames(frames)
    validate_events(events)
    keys = ["Participant_ID", "Original_Phase", "Condition"]
    frame_keys = set(frames[keys].itertuples(index=False, name=None))
    event_keys = set(events[keys].itertuples(index=False, name=None))
    if not event_keys.issubset(frame_keys):
        raise ValueError("events: session keys without matching frames")
    rows = []
    for key, group in frames.groupby(keys, sort=True):
        group = group.sort_values("timestamp").reset_index(drop=True)
        person, phase, condition = key
        pivots = []
        metric = "IN" if phase in [2,3] else "ALL"
        if metric == "IN":
            selected = events[(events.Participant_ID == person) & (events.Original_Phase == phase) & (events.Condition == condition)]
            pivots = build_pivots_from_timestamp(selected, "start", "interruption")
            ts = group.timestamp.to_numpy(dtype=float)
            if any(p < ts[0] or p > ts[-1] for p in pivots):
                raise ValueError("events: interruption outside frame coverage; check seconds and synchronization")
        in_mask, _, all_mask, aligned = compute_segment_masks(group, pivots)
        means, n = segment_means(group, in_mask if metric == "IN" else all_mask, AU_COMPUTE)
        for au in AU_COMPUTE:
            rows.append(dict(zip(keys,key)) | {"metric":metric, "DV":au, "DV_value":means[au],
                        "n_frames":n, "n_valid_au_frames":int(group.loc[in_mask if metric == "IN" else all_mask, au].notna().sum()),
                        "n_pivots":len(pivots), "note":"no_in_window_frames" if n==0 else ""})
    return pd.DataFrame(rows)
