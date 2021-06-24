import numpy as np


def get_iois(onsets, rhythm_len, overlap, dtype=np.float64):
    # iois = inter-onset-intervals
    # TODO dtype
    iois = np.empty(len(onsets), dtype=dtype)
    iois[:-1] = onsets[1:] - onsets[:-1]
    iois[-1] = rhythm_len - onsets[-1] % rhythm_len
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


# class LoopSeq:
#     def __init__(self, sequence, loop_len):
#         self._sequence = sequence
#         self._seq_len = len(sequence)
#         self._loop_len = loop_len
#         self._i = 0

#     def __getitem__(self, key):
#         reps, i = divmod(key, self._seq_len)
#         return reps * self._loop_len + self._sequence[i]

#     def __iter__(self):
#         return self

#     def __next__(self):
#         reps, i = divmod(self._i, self._seq_len)
#         self._i += 1
#         return reps * self._loop_len + self._sequence[i]


class LoopSeq:
    def __init__(self, sequence, loop_len, decimals=None):
        """Makes an infinite loop iterator.

        Takes a sequence of numbers and a total `loop_len`. E.g., if the
        sequence is [1, 3] and the length is 5, the iterator would return
        [1, 3, 6, 8, 11, ...]
        """
        self._sequence = sequence
        self._seq_len = len(sequence)
        self._loop_len = loop_len
        self._i = 0
        self._decimals = decimals

    def __getitem__(self, key):
        reps, i = divmod(key, self._seq_len)
        if self._decimals is not None:
            return (reps * self._loop_len + self._sequence[i]).round(
                self._decimals
            )
        return reps * self._loop_len + self._sequence[i]

    def __iter__(self):
        return self

    def __next__(self):
        reps, i = divmod(self._i, self._seq_len)
        self._i += 1
        if self._decimals is not None:
            return (reps * self._loop_len + self._sequence[i]).round(
                self._decimals
            )
        return reps * self._loop_len + self._sequence[i]


def get_indices_from_sorted(
    elements, sorted_seq, loop_len=None, tolerance=1e-8
):
    """Returns a list containing the indices to the elements in sorted seq.

    E.g., if elements = (2.7, 1.23) and sorted_seq = (0.14, 1.23, 2.4, 2.7),
    will return [3, 1].

    Any elements not in the sorted_seq will be omitted from the return value.
    It's up to the caller to check if the length of the returned list ==
    len(elements).
    """
    indices = np.searchsorted(sorted_seq, elements, side="left")
    out = []
    for i, element in zip(indices, elements):
        if i >= len(sorted_seq):
            if loop_len is None:
                continue
            mod_element = element % loop_len
            mod_i = np.searchsorted(sorted_seq, mod_element, side="left")
            if abs(mod_element - sorted_seq[mod_i]) < tolerance:
                out.append(mod_i + len(sorted_seq))
            elif (
                mod_i > 0
                and abs(mod_element - sorted_seq[mod_i - 1]) < tolerance
            ):
                # it is possible that searchsorted will return the index just
                # *past* the item due to rounding error, so we also inspect
                # the item at the immediately preceding index.
                out.append(mod_i - 1 + len(sorted_seq))
        elif element == sorted_seq[i]:
            out.append(i)
    return out
