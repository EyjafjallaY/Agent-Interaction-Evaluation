"""Non-destructive participant selection; identifiers stay in private input data."""
import pandas as pd


def select_participants(frame, keep_ids):
    if 'Participant_ID' not in frame:
        raise ValueError('Participant_ID is required')
    keep = {str(i) for i in keep_ids}
    if not keep:
        raise ValueError('The keep list is empty')
    known = set(frame.Participant_ID.astype(str))
    if not keep.issubset(known):
        raise ValueError('The keep list contains identifiers absent from the input')
    selected = frame[frame.Participant_ID.astype(str).isin(keep)].copy()
    return selected, {'participants_before':len(known), 'participants_after':len(keep),
                      'rows_before':len(frame), 'rows_after':len(selected)}
