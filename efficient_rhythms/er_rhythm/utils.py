import numpy as np


def get_iois(onsets, rhythm_len, overlap, dtype=np.float64):
    # iois = inter-onset-intervals
    # TODO dtype
    iois = np.empty(len(onsets), dtype=dtype)
    iois[:-1] = onsets[1:] - onsets[:-1]
    iois[-1] = rhythm_len - onsets[-1]
    if overlap:
        iois[-1] += onsets[0]
    return iois
