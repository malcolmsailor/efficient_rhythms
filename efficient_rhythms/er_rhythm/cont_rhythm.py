import fractions
import functools
import math
import warnings

import numpy as np

from .. import er_globals

from .utils import get_iois
from .rhythm import RhythmBase, OldRhythm
from efficient_rhythms.er_rhythm import utils

RANDOM_CARD = 200
COMMA = 10 ** -5

# max value for int64 is 2**63 - 1, but we need a buffer because we may exceed
#   this value sometimes when adding deltas, before renormalizing
INT_MAX = np.int64(2 ** 62 - 1)


# def _enforce_min_dur(onsets, rhythm_len, overlap, min_dur):
#     # How to enforce min_dur after applying random variation to rhythms is
#     # a subtle problem. There is probably a very elegant solution out there
#     # somewhere, but here we take a very simple approach. We just add back
#     # any "excess" below the threshold. (So if min_dur is 0.25, and the ioi
#     # between two onsets is initially 0.2, the new onset will be set to
#     # 0.3 ("adding back" the excess 0.05 adjustment).) Thus the variation
#     # can be thought of bouncing off a limit represented by min_dur.

#     # TODO we need to calculate the maximum total displacement allowed
#     # as a function of rhythm_len and min_dur

#     # TODO actually I'm not at all sure whether this will work
#     iois = get_iois(onsets, rhythm_len, overlap)
#     overflow = iois - min_dur
#     overflow = np.where(overflow < 0, overflow * 2, 0.0)
#     if np.any(overflow):
#         # len_iois_less_one = len(iois) - 1
#         # for i in np.nonzero(overflow):
#         #     if i < len_iois_less_one:
#         #         onsets[i + 1] -= overflow[i]
#         #         onsets[i + 2] += overflow[i]
#         onsets[1:] -= overflow[:-1]
#         # To "move" the first onset, we have to move all the other onsets
#         # in the opposite direction. For better or worse, this means that
#         # the first onset always remains at 0. Is this OK?
#         onsets[1:] += overflow[-1]
#         # TODO is this in danger of recursing endlessly?
#         _enforce_min_dur(onsets, rhythm_len, overlap, min_dur)


class ContRhythmBase2(RhythmBase):
    def __init__(
        self,
        rhythm_len,
        min_dur,
        num_notes,
        increment,
        overlap,
        num_vars,
        vary_consistently=False,
        dtype=np.float64,
    ):
        super().__init__()
        self.rhythm_len = rhythm_len
        self.min_dur = min_dur
        self.num_notes = num_notes
        # TODO reduce increment if necessary as a function of min_dur etc.
        self.increment = increment
        self.overlap = overlap
        # TODO raise an error if overfull
        self.full = self.rhythm_len <= self.min_dur * self.num_notes
        if self.full:
            # TODO warn?
            self.num_vars = 1
        else:
            self.num_vars = num_vars
        self.vary_consistently = vary_consistently
        self.dtype = dtype
        # I think the first iteration of the rhythm should always start at zero.
        # But perhaps subsequent repetitions can start elsewhere. I am leaving
        # this flag here for now but not yet implementing always_start_at_zero
        # = False.
        self.always_start_at_zero = True

        # init onsets
        self._onsets = np.empty(
            (self.num_vars, self.num_notes), dtype=self.dtype
        )

        # cached math results
        self._min_int_dur = np.int64(
            INT_MAX / ((self.rhythm_len - self.min_dur) / self.min_dur)
        )
        self._rand_int_u_bound = INT_MAX - (self.num_notes - 1) * (
            self._min_int_dur - 1
        )
        self._int_increment = INT_MAX / self.rhythm_len * self.increment

    @property
    def onsets(self):
        return self._onsets

    @property
    def durs(self):
        return self._durs

    def _update_onset_deltas(self):
        #     # TODO maybe try the effect of a normal distribution as well?
        deltas = (
            er_globals.RNG.random(size=self.num_notes, dtype=self.dtype) - 1
        )
        deltas = deltas / deltas.sum() * self._int_increment
        self.deltas = deltas.astype(dtype=np.int64)

    def _space_ints(self, unspaced):
        return unspaced + np.arange(self.num_notes, dtype=np.int64) * (
            self._min_int_dur - 1
        )

    def _ints_to_onsets(self, ints):
        # we want the last onset to be at least min_dur from the first onset,
        #   so we subtract min_dur from the end.
        return np.array(
            ints / INT_MAX * (self.rhythm_len - self.min_dur),
            dtype=self.dtype,
        )

    def _vary_onsets_unif(self, i):
        if not self.vary_consistently or i == 1:
            self._update_onset_deltas()
        # We assume that we will always vary the rhythm iteratively (so A
        # becomes B and B becomes C, and so on, and we never go back to A),
        # so we don't have to keep previous values of unspaced around
        self.unspaced = self.unspaced + self.deltas
        # stable sort = timsort
        self.unspaced.sort(kind="stable")
        # TODO how do we prevent more than the first item from becoming negative?
        if self.always_start_at_zero:
            # I guess doing this biases the output a little. TODO think about
            # a better way of always starting from zero.
            self.unspaced[0] = 0
        else:
            raise NotImplementedError(
                "always_start_at_zero = False is not yet implemented"
            )
        # The following lines are a bit of a hack. We don't constrain the final
        # onset from growing larger, so it can get too close to the first onset
        # (on looping around). To avoid this, we divide all the onsets as
        # follows.
        if self.unspaced[-1] > self._rand_int_u_bound:
            self.unspaced //= self.unspaced[-1]
        spaced = self._space_ints(self.unspaced)
        # breakpoint()
        self._onsets[i] = self._ints_to_onsets(spaced)
        # breakpoint()

    def _init_onsets(self):
        if self.full:
            self._onsets[0] = self.min_dur * np.arange(self.num_notes)

        # after https://mathematica.stackexchange.com/a/201905
        # we want to sample from [0, upper_bound] without replacement. Using
        # np's choice method is out of the question (we'd have to create such
        # a large array). But in any case, for any reasonable size of array,
        # the probability of selecting the same number twice from such a large
        # range wil be so low that I think we can just ignore it.

        # unspaced doesn't have min_dur added in between the onsets; we keep
        # this around because if and when we vary the rhythm, we will vary
        # beginning with this

        # We use signed ints because it's at least possible that we may want the
        # option of moving the first onsets before 0 on repeats of the rhythm
        self.unspaced = er_globals.RNG.integers(
            low=1,
            high=self._rand_int_u_bound,
            size=self.num_notes,
            dtype=np.int64,
            endpoint=True,
        )
        self.unspaced.sort()
        # We always want 0 as the first onset for the first rhythm
        self.unspaced[0] = 0
        spaced = self._space_ints(self.unspaced)
        self._onsets[0] = self._ints_to_onsets(spaced)

    def generate(self):
        self._init_contents()
        for i in range(1, self.num_vars):
            self._fill_contents(i)

    def _init_contents(self):
        self._init_onsets()

    def _fill_contents(self, i):
        self._vary_onsets_unif(i)


class ContRhythm2(ContRhythmBase2):
    def __init__(self, dur_density, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dur_density = dur_density
        self._durs = np.empty_like(self._onsets)

    def _init_contents(self):
        self._init_onsets()
        self._init_durs()

    def _fill_contents(self, i):
        self._vary_onsets_unif(i)
        self._fill_durs(i)

    def _fill_durs(self, i):
        # this is a very elementary implementation. It just copies the first
        # set of durs and, where these would be longer than the current ioi,
        # subtracts the excess.
        # It seems clear to me that this is not a satisfactory approach. For
        # instance, in the case where dur_density = 1.0, this approach will
        # insert rests when iois get longer.
        # TODO revise
        iois = utils.get_iois(self.onsets[i])
        self._durs[i] = self.durs[0]
        excess = iois - self.durs[0]
        excess = np.where(excess < 0, excess, 0)
        self._durs[i] += excess

    # TODO choose a sensible value for this
    DUR_INT_MAX = np.int64(2 ** 16 - 1)
    # TODO choose good value
    DUR_TRANCHE_SIZE = INT_MAX // 2 ** 9

    def _init_durs(self):
        float_iois = utils.get_iois(
            self.onsets[0], self.rhythm_len, self.overlap, dtype=self.dtype
        )
        min_density = self.min_dur / self.rhythm_len * self.num_notes

        density = self.dur_density
        if min_density >= density:
            return np.full(self.num_notes, min_density, dtype=self.dtype)

        density = (density - min_density) / (1 - min_density)

        if density == 1:
            return float_iois
        elif density == 0:
            # TODO
            raise NotImplementedError("What to do here?")
        if density <= 0.5:
            subtract = False
        else:
            density = 1 - density
            subtract = True

        available_iois = float_iois - self.min_dur
        int_iois = np.array(
            INT_MAX / available_iois.max() * available_iois, dtype=np.int64
        )
        # we divide the size of int_iois into "tranches" of approximately
        #  equal size
        tranche_counts = np.rint(int_iois / self.DUR_TRANCHE_SIZE)
        n_tranches = int(tranche_counts.sum())
        x = er_globals.RNG.random(n_tranches)
        # the next line is an attempt to enforce a maximum distance ( we
        #   can't take more than 1 * each tranche) on
        #   the output. It works (I think), but I'm not certain that it's
        #   efficient or doesn't bias the output unnecessarily.
        # The idea is that the maximum distance between items in x
        # can be at most 1/(n_tranches * density). So we take the
        # cumulative sum of x (so items can have differences of at most
        # 1) and then divide, then "wrap" the values by taking modulo 1.
        # This will have a bias towards lower numbers. For example, here
        # is the counts from np.histogram(x):
        # array([232, 230, 234, 226, 225, 232, 214, 229, 153, 116])
        # This means that the adjacent intervals at the end of the array will
        # tend to be longer than those at the start. For this reason, we shuffle
        # y below.
        x = x.cumsum() / (n_tranches * density) % 1
        x.sort()

        # We will undershoot the target density slightly since it is
        # unlikely that the last item in x will be exactly 1.0. We could
        # hit it exactly by dividing x by x[-1] but then y.max() may
        # overshoot 1, which seems worse. In any case, we are talking about
        # 0.49998087412817604 rather than 0.5 so it's probably not even worth
        # the extra computation.

        x = x * n_tranches * density
        y = np.empty(n_tranches)
        y[0] = x[0]
        y[1:] = np.diff(x)
        # TODO I think the mean of y asymptotically approaches 0.5; maybe think
        # more about this?
        er_globals.RNG.shuffle(y)

        tranche_starts = np.empty(int(self.rhythm_len), dtype=np.int64)
        tranche_starts[0] = 0
        tranche_starts[1:] = np.cumsum(tranche_counts[:-1])
        int_durs = np.add.reduceat(y, tranche_starts) * self.DUR_TRANCHE_SIZE
        float_durs = int_durs / (INT_MAX / available_iois.max())
        if subtract:
            float_durs = available_iois - float_durs
        self.durs[0] = self.min_dur + float_durs


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
