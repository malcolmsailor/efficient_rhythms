import numpy as np

import sortedcontainers


class RhythmBase:
    def __init__(self):
        self._data = None
        self._onsets = None
        self._durs = None

    @property
    def onsets(self):
        return self._onsets

    @property
    def durs(self):
        return self._durs

    def set_onsets_and_durs(self, onsets, durs):
        if onsets is not None and durs is not None:
            dict_ = {o: d for (o, d) in zip(onsets, durs)}
        else:
            dict_ = {}
        self._data = sortedcontainers.SortedDict(dict_)
        self._onsets = onsets
        self._durs = durs

    def __iter__(self):
        return self._data.items().__iter__()

    def __len__(self):
        return self._data.__len__()

    def __getitem__(self, key):
        try:
            return self._data.__getitem__(key % self.rhythm_len)
        except KeyError:
            # The above sometimes fails due to rounding error
            # Longterm I should figure out a more robust solution
            i_at_or_after = self.get_i_at_or_after(key)
            onset, dur = self._data.peekitem(i_at_or_after)
            if onset - key < 1e-8:
                return dur
            onset, dur = self._data.peekitem(i_at_or_after - 1)
            if key - onset < 1e-8:
                return dur
            raise

    def __repr__(self):
        return (
            f"{self.__class__.__name__}(total_dur={self.total_dur}, "
            f"contents: {self._data})"
        )

    def onsets_between(self, start, end):
        start_i = self.get_i_at_or_after(start)
        end_i = self.get_i_at_or_after(end)
        start_reps, start_i = divmod(start_i, len(self))
        end_reps, end_i = divmod(end_i, len(self))
        if start_reps == end_reps:
            return self.onsets[start_i:end_i] + start_reps * self.rhythm_len
        out = []
        out.append(self.onsets[start_i:] + self.rhythm_len * start_reps)
        for j in range(start_reps + 1, end_reps):
            out.append(self.onsets + self.rhythm_len * (start_reps + j))
        out.append(self.onsets[:end_i] + end_reps * self.rhythm_len)
        return np.concatenate(out)

    def get_i_at_or_after(self, time):
        prev_reps, remaining = divmod(time, self.total_dur)
        return int(prev_reps) * len(self._data) + self._data.bisect_left(
            remaining
        )

    def get_i_at_or_before(self, time):
        prev_reps, remaining = divmod(time, self.total_dur)
        return (
            int(prev_reps) * len(self._data)
            + self._data.bisect_right(remaining)
            - 1
        )

    def get_i_before(self, time):
        prev_reps, remaining = divmod(time, self.total_dur)
        rem_i = self._data.bisect_right(remaining) - 1

        if remaining == self._data.peekitem(rem_i)[0]:
            rem_i -= 1

        return int(prev_reps) * len(self._data) + rem_i

    def get_i_after(self, time):
        prev_reps, remaining = divmod(time, self.total_dur)
        rem_i = self._data.bisect_left(remaining)
        if (
            rem_i < len(self._data)
            and remaining == self._data.peekitem(rem_i)[0]
        ):
            rem_i += 1
        return int(prev_reps) * len(self._data) + rem_i

    def get_onset_and_dur(self, rhythm_i):
        n_reps, rem_i = divmod(rhythm_i, len(self._data))
        reps_time = n_reps * self.total_dur
        onset, dur = self._data.peekitem(rem_i)
        return onset + reps_time, dur

    def at_or_after(self, time):
        # TODO fix cast
        prev_reps, remaining = divmod(time, float(self.total_dur))

        rem_i = self._data.bisect_left(remaining)
        if rem_i >= len(self._data):
            rem_i = 0
            prev_reps += 1
            # raise ValueError(f"No onset at or after {time}")
        onset, dur = self._data.peekitem(rem_i)
        reps_time = prev_reps * self.total_dur
        return onset + reps_time, dur

    def rest_before_onset(self, onset, min_rest_len):
        # TODO test
        release = onset + self[onset]
        next_onset, _ = self.at_or_after(release)
        return next_onset - release >= min_rest_len


class Rhythm(RhythmBase):
    def set_onsets_and_durs(self, onsets, durs):
        onsets, durs = self._pad_truncations(onsets, durs)
        super().set_onsets_and_durs(onsets, durs)

    def __init__(
        self,
        num_notes,
        rhythm_len,
        truncations,
        min_note_dur,
        overlap,
    ):
        super().__init__()
        self.num_notes = num_notes
        self.rhythm_len = rhythm_len
        self.truncations = truncations
        self.overlap = overlap
        self.total_dur = truncations[-1] if truncations else rhythm_len
        self.min_note_dur = min_note_dur
        self.full = self.rhythm_len <= self.min_note_dur * self.num_notes

    def _pad_truncations(self, onsets, durs):
        if len(onsets) == 0:
            return onsets, durs
        for prev_trunc, trunc in zip(
            [self.rhythm_len] + self.truncations, self.truncations
        ):
            n_onsets = len(onsets)
            reps, remainder = divmod(trunc, prev_trunc)
            remainder_i = np.searchsorted(onsets, remainder)
            rep_onsets = np.tile(onsets, reps)
            rep_durs = np.tile(durs, reps)
            temp_onsets = np.concatenate((rep_onsets, onsets[:remainder_i]))
            temp_durs = np.concatenate((rep_durs, durs[:remainder_i]))
            for i in range(reps + 1):
                # TODO fix cast?
                # TODO as it currently stands, this will throw an error if onsets
                #   is int type
                temp_onsets[n_onsets * i : n_onsets * (i + 1)] += i * float(
                    prev_trunc
                )
            overshoot = temp_onsets[-1] + temp_durs[-1] - trunc
            if self.overlap:
                overshoot -= temp_onsets[0]
            if overshoot > 0:
                temp_durs[-1] -= overshoot
            onsets, durs = temp_onsets, temp_durs
        return onsets, durs

    @classmethod
    def from_er_settings(cls, er, voice_i, onsets=None, durs=None):
        (num_notes, rhythm_len, pattern_len, min_note_dur, overlap) = er.get(
            voice_i,
            "num_notes",
            "rhythm_len",
            "pattern_len",
            "min_dur",
            "overlap",
        )
        # rhythm_len should always be <= pattern_len; this is enforced in
        #  er_preprocess.py
        truncations = []
        if er.cont_rhythms == "grid":
            # ultimately I think it might be cleaner to use a different
            # (derived) class for this case
            rhythm_len = (
                er.num_cont_rhythm_vars[voice_i] * er.pattern_len[voice_i]
            )
        else:
            if pattern_len % rhythm_len != 0:
                truncations.append(pattern_len)
            if er.truncate_patterns:
                truncate_dur = max(er.pattern_len)
                if truncate_dur % pattern_len != 0:
                    truncations.append(truncate_dur)
        out = cls(
            num_notes,
            rhythm_len,
            truncations,
            min_note_dur,
            overlap,
        )
        if onsets is not None and durs is not None:
            out.set_onsets_and_durs(onsets, durs)
        return out
