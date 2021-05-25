"""Rhythm functions for efficient_rhythms2.py.
"""
import collections
import fractions
import functools
import math
import random
import warnings

import numpy as np

import src.er_midi as er_midi
import src.er_misc_funcs as er_misc_funcs

RANDOM_CARD = 200
COMMA = 10 ** -5


class RhythmicDict(collections.UserDict):
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


class Rhythm(RhythmicDict):
    # TODO refactor this using some sort of sorted container
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
        # TODO "rhythm_dur" rather than "rhythm_len"
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
            # LONGTERM move this notice outside of the initial_pattern loop
            if isinstance(self, (Grid, ContinuousRhythm)):
                print(
                    "Notice: 'cont_rhythms' will have no effect in voice "
                    f"{self.voice_i} because "
                    "'min_dur' is the maximum value compatible with "
                    "'rhythm_len' and 'onset_subdivision'. "
                    "To allow 'cont_rhythms' to have an effect, reduce "
                    f"'min_dur' to less than {self.min_dur}"
                )
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
        # TODO rename this property?
        # it is the number of notes in the rhythm up to the end of the truncate
        return (
            self.truncate_len // self.pattern_len * self.total_num_notes
            + self.truncated_pattern_num_notes
        )

    def get_i_at_or_after(self, time):
        # TODO use sortedcontainers
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


class ContinuousRhythmicObject(RhythmicDict):
    """Used as a base for ContinuousRhythm and Grid objects."""

    # def round(self, precision=4):
    def round(self):
        try:
            self.pattern_len
        except AttributeError:
            # Grid object does not have pattern_len attribute.
            adj_len = self.rhythm_len  # pylint: disable=no-member
        else:
            if (
                self.rhythm_len < self.pattern_len
                and self.pattern_len % self.rhythm_len != 0
            ):
                adj_len = self.pattern_len
            else:
                adj_len = self.rhythm_len
        for var in self.rel_onsets:  # pylint: disable=no-member
            for j, dur in enumerate(var):
                var[j] = round(dur, 4)
            var[j] += adj_len - var.sum()
        try:
            self.durs  # pylint: disable=no-member
        except AttributeError:
            # Grid object does not have .durs attribute.
            return
        for var in self.durs:  # pylint: disable=no-member
            for j, dur in enumerate(var):
                var[j] = round(dur, 4)

    # def round_to_frac(self, max_denominator=10000):
    #     # This function doesn't work because fractions are not a valid
    #     # datatype for np arrays.
    #     try:
    #         self.pattern_len
    #     except AttributeError:
    #         # Grid object does not have .pattern_len attribute.
    #         adj_len = self.rhythm_len
    #     else:
    #         if (self.rhythm_len < self.pattern_len and
    #                 self.pattern_len % self.rhythm_len != 0):
    #             adj_len = self.pattern_len
    #         else:
    #             adj_len = self.rhythm_len
    #     for var_i, var in enumerate(self.rel_onsets):
    #         for j, dur in enumerate(var):
    #             var[j] = fractions.Fraction(dur).limit_denominator(
    #                 max_denominator=max_denominator)
    #         var[j] += adj_len - var.sum()
    #     try:
    #         self.durs
    #     except AttributeError:
    #         # Grid object does not have .durs attribute.
    #         return
    #     for var_i, var in enumerate(self.durs):
    #         for j, dur in enumerate(var):
    #             var[j] = fractions.Fraction(dur).limit_denominator(
    #                 max_denominator=max_denominator)

    def apply_min_dur_to_rel_onsets(self, rel_onsets):
        while True:
            remaining = 0
            indices = np.ones(self.num_notes)
            for i, rel_onset in enumerate(rel_onsets):
                if rel_onset >= self.min_dur:
                    continue
                indices[i] = 0
                remaining += rel_onset - self.min_dur
                rel_onsets[i] = self.min_dur
            if not remaining:
                break
            adjust = np.where(
                indices == 1,
                np.random.randint(0, RANDOM_CARD, self.num_notes),
                0,
            )
            if adjust.sum():
                adjust = adjust / adjust.sum() * remaining
            rel_onsets = rel_onsets + adjust
        return rel_onsets

    def generate_continuous_onsets(self):
        rand_array = np.random.randint(0, RANDOM_CARD, self.num_notes)
        onsets = rand_array / rand_array.sum() * self.rhythm_len
        self.rel_onsets[0] = self.apply_min_dur_to_rel_onsets(onsets)

    def vary_continuous_onsets(self, apply_to_durs=True):

        # def _vary_continuous_onsets_randomly(self, i, apply_to_durs=True):
        def _vary_continuous_onsets_randomly(
            rhythm, i
        ):  # LONGTERM apply_to_durs?
            deltas = np.random.randint(0, RANDOM_CARD, rhythm.num_notes)
            deltas = deltas / deltas.sum() * rhythm.increment
            deltas = deltas - deltas.mean()
            onsets = rhythm.rel_onsets[i] + deltas
            rhythm.rel_onsets[i + 1] = self.apply_min_dur_to_rel_onsets(onsets)
            # LONGTERM vary durations

        def _vary_continuous_onsets_consistently(rhythm, i, apply_to_durs=True):
            def _update_deltas():
                deltas = np.random.randint(1, RANDOM_CARD, rhythm.num_notes)
                deltas2 = deltas / deltas.sum()
                deltas3 = deltas2 - deltas2.mean()
                if abs(deltas3).sum() == 0:
                    # LONGTERM investigate and fix whatever it is that results in
                    #   this condition. Returning 0 is a kludge.
                    rhythm.deltas = np.zeros(rhythm.num_notes)
                    return
                deltas4 = deltas3 / (abs(deltas3).sum() / rhythm.increment)
                indices = np.array([True for i in range(rhythm.num_notes)])

                while True:
                    if np.all(
                        rhythm.rel_onsets[i] + deltas4 >= rhythm.min_dur - COMMA
                    ):
                        rhythm.deltas = deltas4
                        return
                    if np.all(
                        rhythm.rel_onsets[i] + deltas4 * -1
                        >= rhythm.min_dur - COMMA
                    ):
                        rhythm.deltas = deltas4 * -1
                        return
                    indices = np.array(
                        [
                            rhythm.rel_onsets[i][j] + deltas4[j]
                            >= rhythm.min_dur - COMMA
                            and indices[j]
                            for j in range(rhythm.num_notes)
                        ]
                    )

                    deltas = np.where(indices, deltas, 0)
                    deltas2 = deltas / deltas.sum()
                    deltas3 = np.where(
                        indices, deltas2 - deltas2[indices].mean(), 0
                    )
                    if abs(deltas3).sum() == 0:
                        # LONGTERM investigate and fix whatever it is that results in
                        #   this condition. Returning 0 is a kludge.
                        rhythm.deltas = np.zeros(rhythm.num_notes)
                        return
                    deltas4 = deltas3 / (abs(deltas3).sum() / rhythm.increment)

            if rhythm.deltas is None:
                _update_deltas()
            elif np.any(rhythm.rel_onsets[i] + rhythm.deltas < rhythm.min_dur):
                _update_deltas()

            rhythm.rel_onsets[i + 1] = rhythm.rel_onsets[i] + rhythm.deltas

            if apply_to_durs:
                rhythm.durs[i + 1] = rhythm.durs[i]
                remaining_durs = rhythm.rel_onsets[i + 1] - rhythm.durs[i + 1]
                while np.any(remaining_durs < 0):
                    negative_durs = np.where(
                        remaining_durs < 0, remaining_durs, 0
                    )
                    rhythm.durs[i + 1] += negative_durs
                    available_durs = np.where(
                        remaining_durs > 0, remaining_durs, 0
                    )
                    dur_to_add = np.abs(negative_durs).sum()
                    deltas = np.where(
                        available_durs > 0,
                        np.random.randint(1, RANDOM_CARD, rhythm.num_notes),
                        0,
                    )
                    deltas2 = deltas / deltas.sum() * dur_to_add
                    rhythm.durs[i + 1] += deltas2
                    remaining_durs = (
                        rhythm.rel_onsets[i + 1] - rhythm.durs[i + 1]
                    )

        for i in range(self.num_cont_rhythm_vars - 1):
            if self.full:
                self.rel_onsets[i + 1] = self.rel_onsets[i]
            elif self.vary_rhythm_consistently:
                _vary_continuous_onsets_consistently(
                    self, i, apply_to_durs=apply_to_durs
                )
            else:
                _vary_continuous_onsets_randomly(self, i)

    def rel_onsets_to_rhythm(
        self, offset=0, first_var_only=False, comma=fractions.Fraction(1, 5000)
    ):

        if first_var_only:
            # For use with Grid
            rel_onsets = self.rel_onsets[0]  # pylint: disable=no-member
        else:
            rel_onsets = self.rel_onsets.reshape(  # pylint: disable=no-member
                -1
            )

        try:
            durs = self.durs.reshape(-1)
        except AttributeError:
            # Grid does not have durs attribute.
            durs = rel_onsets

        for i, rel_onset in enumerate(rel_onsets):
            frac_rel_onset = fractions.Fraction(rel_onset).limit_denominator(
                max_denominator=100000
            )
            frac_dur = fractions.Fraction(durs[i]).limit_denominator(
                max_denominator=100000
            )
            if frac_rel_onset == 0:
                continue
            self[offset] = frac_dur
            offset += frac_rel_onset
            # if rel_onset == 0:
            #     continue
            # self[offset] = durs[i]
            # offset += rel_onset

        for onset_i, onset in enumerate(self.onsets[:-1]):
            overlap = onset + self[onset] - self.onsets[onset_i + 1]
            if overlap > comma:
                warnings.warn("Unexpectedly long overlap in rhythm")
            if overlap > 0:
                self[onset] = self.onsets[onset_i + 1] - onset


def get_cont_rhythm(er, voice_i):
    rhythm = ContinuousRhythm(er, voice_i)
    if rhythm.num_notes == 0:
        print(f"Notice: voice {voice_i} is empty.")
        return rhythm
    rhythm.generate_continuous_onsets()
    rhythm.fill_continuous_durs()
    rhythm.vary_continuous_onsets()
    rhythm.truncate_or_extend()
    rhythm.round()
    rhythm.rel_onsets_to_rhythm()
    return rhythm


class ContinuousRhythm(Rhythm, ContinuousRhythmicObject):
    def __init__(self, er, voice_i):
        super().__init__(er, voice_i)

        (
            self.cont_var_increment,
            self.num_cont_rhythm_vars,
            self.vary_rhythm_consistently,
        ) = er.get(
            voice_i,
            "cont_var_increment",
            "num_cont_rhythm_vars",
            "vary_rhythm_consistently",
        )
        self.increment = self.rhythm_len * self.cont_var_increment
        self.rel_onsets = np.zeros((self.num_cont_rhythm_vars, self.num_notes))
        self.durs = np.full_like(self.rel_onsets, self.min_dur)
        self.deltas = None
        if (
            self.rhythm_len < self.pattern_len
            and self.pattern_len % self.rhythm_len != 0
        ):
            self.total_rhythm_len = self.pattern_len * self.num_cont_rhythm_vars
        else:
            self.total_rhythm_len = self.rhythm_len * self.num_cont_rhythm_vars
        self.total_num_notes = self.num_notes * self.num_cont_rhythm_vars

    def fill_continuous_durs(self):
        target_total_dur = min(
            (self.dur_density * self.rhythm_len, self.rhythm_len)
        )
        actual_total_dur = self.durs[0].sum()
        available_durs = self.rel_onsets[0] - self.durs[0]
        if not available_durs.sum():
            return
        available_durs_prop = available_durs / available_durs.sum()
        missing_dur = target_total_dur - actual_total_dur

        while missing_dur > 0:
            weights = np.where(
                available_durs > 0,
                np.random.randint(0, RANDOM_CARD, self.num_notes),
                0,
            )
            weights_2 = weights / weights.sum()
            weights_3 = weights_2 - weights_2[available_durs > 0].mean() + 1
            deltas = (weights_3) * (missing_dur * available_durs_prop)
            self.durs[0] += deltas
            overlaps = np.where(
                self.durs[0] - self.rel_onsets[0] > 0,
                self.durs[0] - self.rel_onsets[0],
                0,
            )
            self.durs[0] -= overlaps
            actual_total_dur = self.durs[0].sum()
            available_durs = self.rel_onsets[0] - self.durs[0]
            if available_durs.sum():
                available_durs_prop = available_durs / available_durs.sum()
                missing_dur = target_total_dur - actual_total_dur
            else:
                missing_dur = 0
                # this delete statement is in place for safety, so if it the
                # loop runs again when there are no available durations, it
                # will throw an error
                # That won't work because it's not persistent!
                del available_durs_prop

    def truncate_or_extend(self):
        if (
            self.rhythm_len < self.pattern_len
            and self.pattern_len % self.rhythm_len != 0
        ):
            min_j = (
                math.ceil(self.pattern_len / self.rhythm_len) * self.num_notes
            )
            temp_rel_onsets = np.zeros((self.num_cont_rhythm_vars, min_j))
            temp_durs = np.zeros((self.num_cont_rhythm_vars, min_j))
            for var_i, var in enumerate(self.rel_onsets):
                temp_rel_onsets[var_i, : self.num_notes] = var
                temp_durs[var_i, : self.num_notes] = self.durs[var_i]
                time = self.rhythm_len
                j = self.num_notes
                while time < self.pattern_len:
                    onset_dur = var[j % self.num_notes]
                    dur = self.durs[var_i][j % self.num_notes]
                    temp_rel_onsets[var_i, j] = min(
                        (onset_dur, self.pattern_len - time)
                    )
                    temp_durs[var_i, j] = min((dur, self.pattern_len - time))
                    time += onset_dur
                    j += 1
                if j < min_j:
                    min_j = j
            # If each repetition of the rhythm doesn't have the same number of
            # notes, the algorithm won't work. For now we just address this
            # by truncating to the minumum length.
            self.rel_onsets = temp_rel_onsets[:, :min_j]
            self.durs = temp_durs[:, :min_j]
            # If we truncated one (or conceivably more) onsets from some
            # rhythms, we need to add the extra duration back on to the onsets.
            # Thus doesn't effect rhythm.durs, however.
            for var_i, var in enumerate(self.rel_onsets):
                var[min_j - 1] += self.pattern_len - var.sum()


def print_rhythm(rhythm):
    if isinstance(rhythm, list):
        strings = []
        strings.append("#" * 51)
        for onset in rhythm:
            strings.append("Attack:{:>10.3}" "".format(float(onset)))
        strings.append("\n")
        print("\n".join(strings)[:-2])
    elif isinstance(rhythm, dict):
        strings = []
        strings.append("#" * 51)
        for onset, dur in rhythm.items():
            strings.append(
                "Attack:{:>10.3}  Duration:{:>10.3}"
                "".format(float(onset), float(dur))
            )
        strings.append("\n")
        print("\n".join(strings)[:-2])


def _get_onset_positions(er, voice_i):

    if er.cont_rhythms == "grid":
        return list(er.grid.keys())

    rhythm_len, sub_subdiv_props = er.get(
        voice_i, "rhythm_len", "sub_subdiv_props"
    )
    onset_positions = []
    time_i = 0
    time = fractions.Fraction(0, 1)
    while time < rhythm_len:
        onset_positions.append(time)
        time += sub_subdiv_props[time_i % len(sub_subdiv_props)]
        time_i += 1

    return onset_positions


def _get_available_for_hocketing(er, voice_i, prev_rhythms, onset_positions):
    """Used for er.hocketing. Returns those subdivisions
    that are available for to be selected. (I.e., those
    that do not belong to the previously constructed
    rhythms, and those that do not belong to obligatory
    beats in other voices.)
    """
    out = []
    for onset in onset_positions:
        write = True
        for prev_rhythm in prev_rhythms:
            if onset in prev_rhythm:
                write = False
                break
        if not write:
            continue
        for oblig_onsets_i, oblig_onsets in enumerate(er.obligatory_onsets):
            if oblig_onsets_i != voice_i % len(er.obligatory_onsets):
                if onset in oblig_onsets:
                    write = False
                    break
        if not write:
            continue
        out.append(onset)

    return out


def _get_available_for_quasi_unison(
    er, voice_i, leader_rhythms, onset_positions
):
    out = []
    for onset in onset_positions:
        go_on = False
        for leader_rhythm in leader_rhythms:
            if onset in leader_rhythm:
                out.append(onset)
                go_on = False
                break
        if go_on:
            continue
        for oblig_onsets_i, oblig_onsets in enumerate(er.obligatory_onsets):
            if oblig_onsets_i != voice_i % len(er.obligatory_onsets):
                if onset in oblig_onsets:
                    out.append(onset)
                    break

    return out


def _get_leader_available(er, remaining, leader_rhythm):
    # LONGTERM make this work when the follower rhythm is a different length
    #   (especially longer) than the leader rhythm?
    out = []
    for time in remaining:
        leader_time = time

        while leader_time >= 0 and leader_time not in leader_rhythm:
            leader_time -= er.onset_subdivision_gcd
        if leader_time < 0:
            continue
        if time <= leader_time + leader_rhythm[leader_time]:
            out.append(time)

    return out


def _get_onset_list(
    er, voice_i, onset_positions, available, leader_rhythm=None
):
    def _add_onset(onset, remove_oblig=False):
        nonlocal num_notes
        out.append(onset)
        num_notes -= 1
        if onset in remaining:
            remaining.remove(onset)
        if onset in available:
            available.remove(onset)
        if remove_oblig and onset in oblig:
            oblig.remove(onset)

    num_notes, obligatory_onsets = er.get(
        voice_i, "num_notes", "obligatory_onsets"
    )
    remaining = onset_positions.copy()
    # I'm not sure whether it's necessary to make a copy of obligatory
    #   onsets, but doing it to be safe, for now, at least.
    oblig = obligatory_onsets.copy()

    out = []
    if voice_i == 0 and er.force_foot_in_bass in (
        "first_beat",
        "global_first_beat",
    ):
        _add_onset(fractions.Fraction(0, 1), remove_oblig=True)

    for onset in oblig:
        if onset in remaining:
            _add_onset(onset)
        else:
            print(
                f"Note: obligatory onset {onset} in voice {voice_i} "
                "not available."
            )

    while num_notes and available:
        choose = random.choice(available)
        _add_onset(choose)

    if num_notes and leader_rhythm:
        available = _get_leader_available(er, remaining, leader_rhythm)
        while num_notes and available:
            choose = random.choice(available)
            _add_onset(choose)

    # Add onsets to obtain the specified number of notes.
    for _ in range(num_notes):
        choose = random.choice(remaining)
        _add_onset(choose)
    out.sort()

    return out


def _get_onset_dict_and_durs_to_next_onset(er, voice_i, onset_list):
    """Returns a dictionary of onsets (with minimum durations)
    as well as a dictionary of the duration between onsets
    """

    min_dur, rhythm_len = er.get(voice_i, "min_dur", "rhythm_len")

    onsets = {}
    durs = {}

    for onset_i, onset in enumerate(onset_list):
        try:
            dur = onset_list[onset_i + 1] - onset
        except IndexError:
            dur = rhythm_len - onset
            if er.overlap:
                dur += onset_list[0]
        durs[onset] = dur
        onsets[onset] = min(dur, min_dur)

    return onsets, durs


def _fill_quasi_unison_durs(er, voice_i, onsets, leader_rhythm):
    leader_durs_at_onsets = {}
    rhythm_length = er.rhythm_len[voice_i]
    time = rhythm_length
    leader_onset = rhythm_length
    current_dur = 0
    while time > 0:
        time -= er.onset_subdivision_gcd
        if time in leader_rhythm:
            leader_dur = leader_rhythm[time]
            if time + leader_dur == leader_onset:
                current_dur += leader_dur
            else:
                current_dur = leader_dur
            if time in onsets:
                leader_durs_at_onsets[time] = current_dur
            leader_onset = time

    return leader_durs_at_onsets


def _fill_onset_durs(
    er, voice_i, onsets, durs, leader_i=None, leader_durs_at_onsets=()
):
    """Adds to the onset durations until the specified
    density is achieved. Doesn't return anything, just
    alters the onset dictionary in place.
    """

    def _fill_onsets_sub(dur_dict, remaining_dict):
        actual_total_dur = sum(onsets.values())
        available = []
        for time in onsets:
            if time in dur_dict and onsets[time] != dur_dict[time]:
                available.append(time)

        # We round dur_density to the nearest dur_subdivision
        while (
            target_total_dur - actual_total_dur > dur_subdivision / 2
            and available
        ):
            choose = random.choice(available)
            remaining_dur = remaining_dict[choose] - onsets[choose]
            dur_to_add = min(dur_subdivision, remaining_dur)
            onsets[choose] += dur_to_add
            actual_total_dur += dur_to_add
            if (
                onsets[choose] >= dur_dict[choose]
                or onsets[choose] >= remaining_dict[choose]
            ):
                available.remove(choose)

        return actual_total_dur

    dur_subdivision = er.get(voice_i, "dur_subdivision")

    target_total_dur = fractions.Fraction(
        er.dur_density[voice_i] * er.rhythm_len[voice_i]
    ).limit_denominator(max_denominator=8192)

    if leader_durs_at_onsets:
        actual_total_dur = _fill_onsets_sub(leader_durs_at_onsets, durs)
        if (actual_total_dur >= target_total_dur) or (
            er.rhythmic_quasi_unison_constrain
            and er.onset_density[voice_i] < er.onset_density[leader_i]
        ):
            return

    _fill_onsets_sub(durs, durs)


def _add_comma(er, voice_i, onsets):

    # This function shouldn't run with any sort of continuous rhythms.
    if er.cont_rhythms != "none":
        return

    # LONGTERM verify that this is working with complex subdivisions
    rhythm_length = er.rhythm_len[voice_i]
    subdivision = er.onset_subdivision[voice_i]
    comma_position = er.comma_position[voice_i]

    if comma_position == "end":
        return

    comma = rhythm_length % subdivision

    if isinstance(comma_position, int):
        comma_i = comma_position
        if comma_i > len(onsets):
            warnings.warn(
                f"Comma position for voice {voice_i} greater "
                "than number of onsets in rhythm. Choosing a "
                "random comma position."
            )
            comma_i = random.randrange(len(onsets))
    else:
        comma_i = 0

        if comma_position == "middle":
            comma_i = random.randrange(1, len(onsets))
        else:
            comma_i = random.randrange(len(onsets) + 1)

    onset_list = list(onsets.keys())

    for onset in onset_list[comma_i:]:
        new_onset = onset + comma
        dur = onsets[onset]
        del onsets[onset]
        onsets[new_onset] = dur


def _fit_rhythm_to_pattern(er, voice_i, onsets):
    """If the rhythm is shorter than the pattern, extend it as necessary."""

    if not onsets:
        return

    rhythm_len, pattern_len, num_notes = er.get(
        voice_i, "rhythm_len", "pattern_len", "num_notes"
    )

    if rhythm_len >= pattern_len:
        return

    onset_list = list(onsets.keys())

    onset_i = num_notes
    while True:
        prev_onset = onset_list[onset_i % len(onset_list)]
        new_onset = prev_onset + rhythm_len * (onset_i // num_notes)
        if new_onset >= pattern_len:
            break
        onsets[new_onset] = onsets[prev_onset]
        onset_i += 1

    last_onset = max(onsets)
    last_onset_dur = onsets[last_onset]
    overshoot = last_onset + last_onset_dur - pattern_len
    if er.overlap:
        first_onset = min(onsets)
        overshoot -= first_onset
    if overshoot > 0:
        onsets[last_onset] -= overshoot


def generate_rhythm1(er, voice_i, prev_rhythms=()):
    """Constructs a rhythm randomly according to the arguments supplied.

    Keyword args:
        prev_rhythms (list of dictionaries): used in the construction of
            hocketed rhythms.

    Returns:
        A dictionary of (Fraction:onset time, Fraction:duration) pairs.
    """

    if voice_i in er.rhythmic_unison_followers:
        leader_i = er.rhythmic_unison_followers[voice_i]
        return prev_rhythms[leader_i]

    if er.cont_rhythms == "all":
        return get_cont_rhythm(er, voice_i)

    subdivision = er.onset_subdivision[voice_i]

    if er.min_dur[voice_i] == 0:
        er.min_dur[voice_i] = subdivision
    if er.dur_subdivision[voice_i] == 0:
        er.dur_subdivision[voice_i] = subdivision

    onset_positions = _get_onset_positions(er, voice_i)

    available = []
    if voice_i in er.hocketing_followers:
        leaders = []
        for leader_i in er.hocketing_followers[voice_i]:
            leaders.append(prev_rhythms[leader_i % len(prev_rhythms)])
        available = _get_available_for_hocketing(
            er, voice_i, leaders, onset_positions
        )
    elif voice_i in er.rhythmic_quasi_unison_followers:
        leader_i = er.rhythmic_quasi_unison_followers[voice_i]
        leader_rhythm = prev_rhythms[leader_i % len(prev_rhythms)]
        available = _get_available_for_quasi_unison(
            er,
            voice_i,
            [
                prev_rhythms[leader_i],
            ],
            onset_positions,
        )

        if (
            er.onset_density[voice_i] > er.onset_density[leader_i]
            and er.rhythmic_quasi_unison_constrain
        ):
            onset_list = _get_onset_list(
                er, voice_i, onset_positions, available, leader_rhythm
            )
        else:
            onset_list = _get_onset_list(
                er, voice_i, onset_positions, available
            )

        onsets, durs = _get_onset_dict_and_durs_to_next_onset(
            er, voice_i, onset_list
        )

        leader_durs_at_onsets = _fill_quasi_unison_durs(
            er,
            voice_i,
            onsets,
            prev_rhythms[leader_i],
        )

        _fill_onset_durs(
            er,
            voice_i,
            onsets,
            durs,
            leader_i=leader_i,
            leader_durs_at_onsets=leader_durs_at_onsets,
        )
        if er.cont_rhythms == "grid":
            rhythm = er.grid.return_varied_rhythm(er, onsets, voice_i)
            return rhythm
        _add_comma(er, voice_i, onsets)

        _fit_rhythm_to_pattern(er, voice_i, onsets)

        rhythm = Rhythm(er, voice_i)
        rhythm.data = onsets
        return rhythm
    # LONGTERM consolidate this code with above (a lot of duplication!)
    onset_list = _get_onset_list(er, voice_i, onset_positions, available)

    onsets, durs = _get_onset_dict_and_durs_to_next_onset(
        er, voice_i, onset_list
    )

    _fill_onset_durs(er, voice_i, onsets, durs)

    _add_comma(er, voice_i, onsets)

    if er.cont_rhythms == "grid":
        rhythm = er.grid.return_varied_rhythm(er, onsets, voice_i)
        return rhythm

    _fit_rhythm_to_pattern(er, voice_i, onsets)

    rhythm = Rhythm(er, voice_i)
    rhythm.data = onsets
    return rhythm


def update_pattern_vl_order(er, rhythms):
    if er.cont_rhythms != "none":
        er.num_notes_by_pattern = [
            len(rhythms[voice_i].rel_onsets[0])
            # len(rhythms[voice_i].onsets[0])
            for voice_i in range(er.num_voices)
        ]
        # The next lines seem a little kludgy, it would be nice to
        # treat all rhythms in a more homogenous way. But for now, at least
        # it works.
        for voice_i in range(er.num_voices):
            pattern_len, rhythm_len = er.get(
                voice_i, "pattern_len", "rhythm_len"
            )
            if pattern_len % rhythm_len == 0:
                num_repeats_of_rhythm = pattern_len // rhythm_len
                er.num_notes_by_pattern[voice_i] *= num_repeats_of_rhythm

    else:
        # The length of each rhythm is equal to the number of notes
        # per pattern because of the _fit_rhythm_to_pattern function
        # previously run.
        er.num_notes_by_pattern = [len(rhythm) for rhythm in rhythms]

    # if er.truncate_patterns:
    #     max_len = max(er.pattern_len)
    #     truncate_lens = [
    #         max_len % pattern_len for pattern_len in er.pattern_len
    #     ]
    #     er.num_notes_by_truncated_pattern = [0 for i in range(er.num_voices)]
    #     for voice_i, truncate_len in enumerate(truncate_lens):
    #         if truncate_len:
    #             for onset in rhythms[voice_i]:
    #                 if onset >= truncate_len:
    #                     break
    #                 er.num_notes_by_truncated_pattern[voice_i] += 1

    totals = [0 for rhythm in rhythms]
    for i in range(len(er.pattern_vl_order)):
        vl_item = er.pattern_vl_order[i]
        start_rhythm_i = totals[vl_item.voice_i]
        if (
            er.truncate_patterns
            and (vl_item.end_time - vl_item.start_time)
            < er.pattern_len[vl_item.voice_i]
        ):
            # totals[vl_item.voice_i] += er.num_notes_by_truncated_pattern[
            #     vl_item.voice_i
            # ]
            totals[vl_item.voice_i] += rhythms[
                vl_item.voice_i
            ].truncated_pattern_num_notes
        else:
            totals[vl_item.voice_i] += er.num_notes_by_pattern[vl_item.voice_i]
        # end_rhythm_i is the first note *after* the rhythm ends
        end_rhythm_i = totals[vl_item.voice_i]
        vl_item.start_i = start_rhythm_i
        vl_item.end_i = end_rhythm_i
        vl_item.len = end_rhythm_i - start_rhythm_i


class Grid(ContinuousRhythmicObject):
    def __init__(self, er):
        super().__init__()
        # For now, this only works if all rhythm lengths are the same.
        # MAYBE handle non-identical rhythm lengths.
        class GridError(Exception):
            pass

        if len(set(er.rhythm_len)) > 1:
            raise GridError(
                "Generate grid only works if all rhythm lengths are the same."
            )
        self.rhythm_len = er.rhythm_len[0]

        if (
            len(set(er.pattern_len)) > 1
            or er.pattern_len[0] != er.rhythm_len[0]
        ):
            raise GridError(
                "Generate grid only works if rhythm and pattern lengths are same."
            )

        if len(set(er.num_cont_rhythm_vars)) > 1:
            raise GridError(
                "Generate grid only works if 'num_cont_rhythm_vars' has a single value."
            )
        self.num_cont_rhythm_vars = er.num_cont_rhythm_vars[0]

        if len(set(er.vary_rhythm_consistently)) > 1:
            raise GridError(
                "Generate grid only works if 'vary_rhythm_consistently' "
                "has a single value."
            )
        self.vary_rhythm_consistently = er.vary_rhythm_consistently[0]

        if len(set(er.cont_var_increment)) > 1:
            raise GridError(
                "Generate grid only works if 'cont_var_increment' "
                "has a single value."
            )
        self.increment = er.cont_var_increment[0]

        self.min_dur = min(er.min_dur)
        if len(set(er.min_dur)) > 1:
            print(
                "Notice: more than one value for 'min_dur', using minimum ("
                f"{self.min_dur})"
            )

        # Below we take the "num_div" as done in subfunction _num_notes() in
        #   er_preprocess.py. It would also be possible to use num_notes instead,
        #   with a somewhat different result.
        num_divs = [
            int(er.rhythm_len[voice_i] / er.onset_subdivision[voice_i])
            for voice_i in range(er.num_voices)
        ]
        # Although "num_notes" is perhaps not the best name for the next
        #   attribute, it allows us to re-use functions that work with Rhythm
        #   objects.
        self.num_notes = max(num_divs)

        if self.rhythm_len < self.min_dur * self.num_notes:
            new_min_dur = er_misc_funcs.convert_to_fractions(
                self.rhythm_len / self.num_notes
            )
            print(
                "Notice: grid min_dur too long; "
                f"reducing from {self.min_dur} to {new_min_dur}."
            )
            self.min_dur = new_min_dur
        if self.rhythm_len == self.min_dur * self.num_notes:
            print(
                "Notice: 'cont_rhythms' will have no effect because "
                "'min_dur' is the maximum value compatible with "
                "'rhythm_len' and 'onset_subdivision'. "
                "To allow 'cont_rhythms' to have an effect, reduce 'min_dur' "
                f"to less than {self.min_dur}"
            )
            self.full = True
        else:
            self.full = False

        self.rel_onsets = np.zeros((self.num_cont_rhythm_vars, self.num_notes))
        self.deltas = None
        self.generate_continuous_onsets()
        self.vary_continuous_onsets(apply_to_durs=False)
        self.round()
        self.rel_onsets_to_rhythm(first_var_only=True)
        self.cum_onsets = self.rel_onsets.cumsum(axis=1) - self.rel_onsets
        # self.dur_deltas is the difference between the rel_onset time
        # of each grid position on each variation. (The first row is
        # the difference between the last variation and the first.)
        # It would have been better to do this directly when creating
        # the variations, and not have the somewhat useless .deltas
        # attribute above.
        # LONGTERM revise?
        self.dur_deltas = np.zeros((self.num_cont_rhythm_vars, self.num_notes))
        for var_i in range(self.num_cont_rhythm_vars):
            self.dur_deltas[var_i] = (
                self.rel_onsets[var_i]
                - self.rel_onsets[(var_i - 1) % self.num_cont_rhythm_vars]
            )

    def return_varied_rhythm(self, er, onsets, voice_i):
        def _get_grid_indices():
            indices = []
            for time_i, time in enumerate(self):
                if time in onsets:
                    indices.append(time_i)
            return indices

        rhythm_num_notes = len(onsets)
        if rhythm_num_notes == 0:
            print(f"Notice: voice {voice_i} is empty.")
            return ContinuousRhythm(er, voice_i)
        indices = _get_grid_indices()
        var_onsets = np.zeros((self.num_cont_rhythm_vars, rhythm_num_notes))
        rel_onsets = np.zeros((self.num_cont_rhythm_vars, rhythm_num_notes))
        # var_onsets[0] = list(onsets.keys())
        var_durs = np.zeros((self.num_cont_rhythm_vars, rhythm_num_notes))
        var_durs[0] = list(onsets.values())
        for var_i in range(self.num_cont_rhythm_vars):
            var_onsets[var_i] = self.cum_onsets[var_i, indices]
            rel_onsets[var_i, : rhythm_num_notes - 1] = np.diff(
                var_onsets[var_i]
            )
            rel_onsets[var_i, rhythm_num_notes - 1] = (
                self.rhythm_len - var_onsets[var_i, rhythm_num_notes - 1]
            )
            if var_i != 0:
                var_durs[var_i] = (
                    var_durs[var_i - 1] + self.dur_deltas[var_i, indices]
                )

        rhythm = ContinuousRhythm(er, voice_i)
        rhythm.rel_onsets = rel_onsets
        rhythm.durs = var_durs
        rhythm.truncate_or_extend()
        rhythm.round()
        rhythm.rel_onsets_to_rhythm()
        return rhythm


def rhythms_handler(er):
    """According to the parameters in er, return rhythms."""

    if er.rhythms_specified_in_midi:
        rhythms = er_midi.get_rhythms_from_midi(er)
    else:
        rhythms = []
        if er.cont_rhythms == "grid":
            er.grid = Grid(er)
        for voice_i in range(er.num_voices):
            rhythms.append(generate_rhythm1(er, voice_i, prev_rhythms=rhythms))

    if not any(rhythms):

        class EmptyRhythmsError(Exception):
            pass

        raise EmptyRhythmsError(
            "No notes in any rhythms! This is a bug in the script."
        )

    update_pattern_vl_order(er, rhythms)

    return rhythms


def get_onset_order(er):

    end_time = max(er.pattern_len)

    class NoMoreAttacksError(Exception):
        pass

    def _get_next_onset():
        next_onset = end_time ** 2
        increment_i = -1
        for i in er.voice_order:
            try:
                next_onset_in_voice = onsets[i][voice_is[i]]
            except IndexError:
                continue
            if next_onset_in_voice < next_onset:
                next_onset = next_onset_in_voice
                increment_i = i
        if next_onset == end_time ** 2:
            raise NoMoreAttacksError("No more onsets found")
        voice_is[increment_i] += 1
        return next_onset, increment_i

    onsets = [list(rhythm.keys()) for rhythm in er.rhythms]
    voice_is = [0 for i in range(er.num_voices)]
    ordered_onsets = []
    while True:
        try:
            next_onset, voice_i = _get_next_onset()
        except NoMoreAttacksError:
            break
        if next_onset >= end_time:
            break
        ordered_onsets.append((voice_i, next_onset))

    return ordered_onsets


def rest_before_next_note(rhythm, onset, min_rest_len):
    release = onset + rhythm[onset]
    for next_onset in sorted(rhythm.keys()):
        if next_onset >= release:
            break

    gap = next_onset - release
    if gap >= min_rest_len:
        return True

    return False
