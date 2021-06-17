import collections
import functools
import math

import numpy as np

import sortedcontainers




class RhythmicDict:
    def __init__(self, initial_onsets=None, initial_durs=None):
        if initial_onsets is not None and initial_durs is not None:
            initial_data = {
                o: d for (o, d) in zip(initial_onsets, initial_durs)
            }
        else:
            initial_data = {}
        self._data = sortedcontainers.SortedDict(initial_data)
        self.onsets = initial_onsets
        self.durs = initial_durs

    def __iter__(self):
        return self._data.items().__iter__()

    def __len__(self):
        return self._data.__len__()

    # TODO review uses of this
    def __getitem__(self, key):
        return self._data.__getitem__(key)


class Rhythm(RhythmicDict):
    def __init__(
        self,
        onsets,
        durs,
        num_notes,
        rhythm_dur,
        truncations,
        min_note_dur,
        overlap,
    ):
        onsets, durs = self._pad_truncations(
            rhythm_dur, truncations, onsets, durs, overlap
        )
        super().__init__(initial_onsets=onsets, initial_durs=durs)
        # TODO eliminate "num_notes" argument?
        self.num_notes = num_notes
        self.rhythm_dur = rhythm_dur
        self.truncations = truncations
        self.total_dur = truncations[-1] if truncations else rhythm_dur
        self.min_note_dur = min_note_dur
        self.full = self.rhythm_dur <= self.min_note_dur * self.num_notes

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
        return onset + reps_time, dur + reps_time

    def at_or_after(self, time):
        # TODO fix cast
        prev_reps, remaining = divmod(time, float(self.total_dur))
        reps_time = prev_reps * self.total_dur
        rem_i = self._data.bisect_left(remaining)
        if rem_i >= len(self._data):
            raise ValueError(f"No onset at or after {time}")
        onset, dur = self._data.peekitem(rem_i)
        return onset + reps_time, dur + reps_time

    def rest_before_onset(self, onset, min_rest_len):
        # TODO test
        release = onset + self._data[onset]
        next_onset, _ = self.at_or_after(release)
        return next_onset - release >= min_rest_len

    # def _pad_truncations2(self):
    #     if not self._data:
    #         # if rhythm is empty, following loop will throw an exception
    #         return
    #     for prev_trunc, trunc in zip(
    #         [self.rhythm_dur] + self.truncations, self.truncations
    #     ):
    #         for i in itertools.count():
    #             prev_onset, dur = self._data.peekitem(i)
    #             new_onset = prev_onset + prev_trunc
    #             if new_onset >= trunc:
    #                 break
    #             self._data[new_onset] = dur

    @staticmethod
    def _pad_truncations(rhythm_dur, truncations, onsets, durs, overlap):
        # This is a static method because we want to call it before we
        # call super().__init__() and so we can't actually access any
        # attributes from the instance yet.
        if len(onsets) == 0:
            return onsets, durs
        for prev_trunc, trunc in zip([rhythm_dur] + truncations, truncations):
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
            if overlap:
                overshoot -= temp_onsets[0]
            if overshoot > 0:
                temp_durs[-1] -= overshoot
            onsets, durs = temp_onsets, temp_durs
        return onsets, durs

    @classmethod
    def from_er_settings(cls, er, voice_i, onsets=None, durs=None):
        (num_notes, rhythm_dur, pattern_dur, min_note_dur, overlap) = er.get(
            voice_i,
            "num_notes",
            "rhythm_len",
            "pattern_len",
            "min_dur",
            "overlap",
        )
        # rhythm_dur should always be <= pattern_dur; this is enforced in
        #  er_preprocess.py
        truncations = []
        if pattern_dur % rhythm_dur != 0:
            truncations.append(pattern_dur)
        if er.truncate_patterns:
            truncate_dur = max(er.pattern_len)
            if truncate_dur % pattern_dur != 0:
                truncations.append(truncate_dur)
        return cls(
            onsets,
            durs,
            num_notes,
            rhythm_dur,
            truncations,
            min_note_dur,
            overlap,
        )

# TODO remove after revising ContinuousRhythm
class OldRhythmicDict(collections.UserDict):
    def __str__(self):
        strings = []
        strings.append("#" * 51)
        for onset, dur in self.items():
            strings.append(
                "Attack:{:>10.6}  Duration:{:>10.6}"
                "".format(float(onset), float(dur))
            )
        strings.append("\n")
        return "\n".join(strings)[:-2]

    # def make_onset_and_dur_lists(self):
    #     self.onsets = list(self.keys())
    #     self.onsets_and_durs = list(self.items())

    # LONGTERM onsets and onsets_and_durs assume that
    #   the contents will no longer be changed after their first access.
    #   Is there a way to enforce this?
    @functools.cached_property
    def onsets(self):
        return list(self.keys())

    @functools.cached_property
    def onsets_and_durs(self):
        return list(self.items())

    def __repr__(self):
        return f"{self.__class__.__name__}({self.data})"


# TODO remove after revising ContinuousRhythm
class OldRhythm(OldRhythmicDict):
    # LONGTERM provide "re-generate" method, rather than
    #   re-initializing an entire new rhythm at each failure in er_make.py
    @functools.cached_property
    def total_num_notes(self):
        # LONGTERM check whether this works with truncate
        out = self.num_notes
        running_length = self.rhythm_len
        while running_length < self.total_rhythm_len:
            break_out = False
            if running_length + self.rhythm_len <= self.total_rhythm_len:
                running_length += self.rhythm_len
                out += self.num_notes
            else:
                for onset in self:
                    if running_length + onset >= self.total_rhythm_len:
                        break_out = True
                        break
                    out += 1
            if break_out:
                break
        return out

    def __init__(self, er, voice_i):
        super().__init__()
        self.voice_i = voice_i
        (
            self.num_notes,
            self.rhythm_len,
            self.pattern_len,
            self.min_dur,
            self.dur_density,
            self.overlap,
        ) = er.get(
            voice_i,
            "num_notes",
            "rhythm_len",
            "pattern_len",
            "min_dur",
            "dur_density",
            "overlap",
        )
        self.total_rhythm_len = self.pattern_len
        if er.truncate_patterns:
            # max_len = max(er.pattern_len)
            # self.truncate_len = max_len % self.pattern_len
            self.truncate_len = max(er.pattern_len)
            if self.truncate_len == self.pattern_len:
                self.truncate_len = 0
            else:
                self.n_patterns_per_truncate = math.ceil(
                    self.truncate_len / self.pattern_len
                )
            self._truncated_pattern_num_notes = None
        else:
            self.truncate_len = 0
        self._check_min_dur()

    def _check_min_dur(self):
        if self.rhythm_len <= self.min_dur * self.num_notes:
            self.full = True
        else:
            self.full = False

    @functools.cached_property
    def truncated_pattern_num_notes(self):
        if not self.truncate_len:
            raise ValueError("This is a bug in the 'efficient_rhythms' script")
        self._truncated_pattern_num_notes = 0
        for onset in self:
            if (onset + self.min_dur) > (
                self.truncate_len % self.total_rhythm_len
            ):
                break
            self._truncated_pattern_num_notes += 1
        return self._truncated_pattern_num_notes

    @functools.cached_property
    def loop_num_notes(self):
        # it is the number of notes in the rhythm up to the end of the truncate
        return (
            self.truncate_len // self.pattern_len * self.total_num_notes
            + self.truncated_pattern_num_notes
        )

    def get_i_at_or_after(self, time):
        if self.truncate_len:
            truncated, untruncated = divmod(time, self.truncate_len)
            truncated_num_notes = int(truncated) * self.loop_num_notes
        else:
            truncated_num_notes, untruncated = 0, time
        reps, remainder = divmod(untruncated, self.total_rhythm_len)
        for remainder_i, onset in enumerate(self.onsets):
            if onset >= remainder:
                break
        if remainder > onset:
            remainder_i += 1
        return (
            truncated_num_notes + int(reps) * self.total_num_notes + remainder_i
        )

    def get_i_before(self, time):
        if self.truncate_len:
            truncated, untruncated = divmod(time, self.truncate_len)
            truncated_num_notes = int(truncated) * self.loop_num_notes
        else:
            truncated_num_notes, untruncated = 0, time
        reps, remainder = divmod(untruncated, self.total_rhythm_len)
        for remainder_i, onset in enumerate(self.onsets):
            if onset >= remainder:
                remainder_i -= 1
                break
        return (
            truncated_num_notes + int(reps) * self.total_num_notes + remainder_i
        )

    def get_i_at_or_before(self, time):
        """Returns -1 if time is before first note in rhythm."""
        if self.truncate_len:
            truncated, untruncated = divmod(time, self.truncate_len)
            truncated_num_notes = int(truncated) * self.loop_num_notes
        else:
            truncated_num_notes, untruncated = 0, time
        reps, remainder = divmod(untruncated, self.total_rhythm_len)
        # 0 1 2 3
        #    ^
        for remainder_i, onset in enumerate(self.onsets):
            if onset > remainder:
                remainder_i -= 1
                break
        return (
            truncated_num_notes + int(reps) * self.total_num_notes + remainder_i
        )

    def get_i_after(self, time):
        if self.truncate_len:
            truncated, untruncated = divmod(time, self.truncate_len)
            truncated_num_notes = int(truncated) * self.loop_num_notes
        else:
            truncated_num_notes, untruncated = 0, time
        reps, remainder = divmod(untruncated, self.total_rhythm_len)
        for remainder_i, onset in enumerate(self.onsets):
            if onset > remainder:
                break
        if remainder >= onset:
            remainder_i += 1
        return (
            truncated_num_notes + int(reps) * self.total_num_notes + remainder_i
        )

    def get_onset_and_dur(self, rhythm_i):
        if not self.truncate_len:
            offset = (rhythm_i // self.total_num_notes) * self.total_rhythm_len
            onset, dur = self.onsets_and_durs[rhythm_i % self.total_num_notes]
            return onset + offset, dur
        # else: we need to take truncated patterns into account
        # LONGTERM it would probably be better to just write the whole
        #   loop to the rhythm rather than do all this complicated logic
        #   every time
        loop_offset = (rhythm_i // self.loop_num_notes) * self.truncate_len
        n_patterns = (rhythm_i % self.loop_num_notes) // self.total_num_notes
        offset = n_patterns * self.total_rhythm_len
        onset, dur = self.onsets_and_durs[
            (rhythm_i % self.loop_num_notes) % self.total_num_notes
        ]
        onset += loop_offset + offset
        if n_patterns != self.n_patterns_per_truncate - 1:
            return onset, dur
        overdur = loop_offset + self.truncate_len - (onset + dur)
        if self.overlap:
            overdur += self.onsets[0]
        return onset, dur + min(0, overdur)
