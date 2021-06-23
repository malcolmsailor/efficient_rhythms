import numpy as np


def get_iois(onsets, rhythm_len, overlap, dtype=np.float64):
    # iois = inter-onset-intervals
    # TODO dtype
    iois = np.empty(len(onsets), dtype=dtype)
    iois[:-1] = onsets[1:] - onsets[:-1]
    iois[-1] = rhythm_len - onsets[-1]
    if overlap:
        iois[-1] += onsets[0]
    assert np.all(iois >= -1e-10)
    return iois


def get_rois(onsets, releases, rhythm_len, overlap, dtype=np.float64):
    # rois = release-to-onset intervals
    rois = np.empty(len(onsets), dtype=dtype)
    rois[:-1] = onsets[1:] - releases[:-1]
    rois[-1] = rhythm_len - releases[-1]
    if overlap:
        rois[-1] += onsets[0]
    assert np.all(rois >= -1e-10)
    return rois
