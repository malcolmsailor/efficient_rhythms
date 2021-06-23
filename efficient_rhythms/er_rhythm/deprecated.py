"""Keeping this old code around temporarily to consult it while I complete the 
refactor.
"""
import math
import fractions
import warnings

import numpy as np

from .. import er_globals
from .rhythm import RhythmBase, OldRhythm

RANDOM_CARD = 200
COMMA = 10 ** -5


class ContRhythmBase(RhythmBase):
    """Used as a base for ContinuousRhythm and Grid objects."""

    # def round(self, precision=4):
    # TODO review what the heck this function is for
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
                # np.random.randint(0, RANDOM_CARD, self.num_notes),
                er_globals.RNG.integers(
                    low=0, high=RANDOM_CARD, size=self.num_notes
                ),
                0,
            )
            if adjust.sum():
                adjust = adjust / adjust.sum() * remaining
            rel_onsets = rel_onsets + adjust
        return rel_onsets

        # rand_array = er_globals.RNG.integers(
        #     low=0, high=RANDOM_CARD, size=self.num_notes
        # )
        # onsets = rand_array / rand_array.sum() * self.rhythm_len
        # self.rel_onsets[0] = self.apply_min_dur_to_rel_onsets(onsets)

    def vary_continuous_onsets(self, apply_to_durs=True):

        # def _vary_continuous_onsets_randomly(self, i, apply_to_durs=True):
        def _vary_continuous_onsets_randomly(
            rhythm, i
        ):  # LONGTERM apply_to_durs?
            # deltas = np.random.randint(0, RANDOM_CARD, rhythm.num_notes)
            deltas = er_globals.RNG.integers(
                low=0, high=RANDOM_CARD, size=self.num_notes
            )
            deltas = deltas / deltas.sum() * rhythm.increment
            deltas = deltas - deltas.mean()
            onsets = rhythm.rel_onsets[i] + deltas
            rhythm.rel_onsets[i + 1] = self.apply_min_dur_to_rel_onsets(onsets)
            # LONGTERM vary durations

        def _vary_continuous_onsets_consistently(rhythm, i, apply_to_durs=True):
            def _update_deltas():
                # deltas = np.random.randint(1, RANDOM_CARD, rhythm.num_notes)
                deltas = er_globals.RNG.integers(
                    low=0, high=RANDOM_CARD, size=self.num_notes
                )
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
                        er_globals.RNG.integers(
                            low=1, high=RANDOM_CARD, size=self.num_notes
                        ),
                        # np.random.randint(1, RANDOM_CARD, rhythm.num_notes),
                        0,
                    )
                    deltas2 = deltas / deltas.sum() * dur_to_add
                    rhythm.durs[i + 1] += deltas2
                    remaining_durs = (
                        rhythm.rel_onsets[i + 1] - rhythm.durs[i + 1]
                    )

        for i in range(self.num_cont_rhythm_vars - 1):
            if self.full:
                # TODO surely there is a more efficient solution in this case
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


class ContinuousRhythm(OldRhythm, ContRhythmBase):
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
            self.total_dur = self.pattern_len * self.num_cont_rhythm_vars
        else:
            self.total_dur = self.rhythm_len * self.num_cont_rhythm_vars
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
                # np.random.randint(0, RANDOM_CARD, self.num_notes),
                er_globals.RNG.integers(
                    low=0, high=RANDOM_CARD, size=self.num_notes
                ),
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
