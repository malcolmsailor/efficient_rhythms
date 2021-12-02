import abc
import warnings

import numpy as np

from .. import er_globals
from . import utils
from .rhythm import RhythmBase


# max value for int64 is 2**63 - 1, but we need a buffer because we may exceed
#   this value sometimes when adding deltas, before renormalizing
INT_MAX = np.int64(2 ** 62 - 1)

# These values seem to work ok but I'm not sure they couldn't be improved upon:
# DUR_INT_MAX = np.int64(2 ** 16 - 1)
DUR_TRANCHE_SIZE = INT_MAX // 2 ** 9


class ContRhythmBase(RhythmBase):
    __metaclass__ = abc.ABCMeta

    def __repr__(self):
        return (
            f"{self.__class__.__name__}(rhythm_len={self.rhythm_len}, "
            f"contents: {self._data})"
        )

    def __init__(
        self,
        rhythm_len,
        min_dur,
        num_notes,
        increment,
        overlap,
        num_vars,
        vary_consistently=False,
        var_palindrome=True,
        dtype=np.float64,
    ):
        super().__init__()
        self.rhythm_len = dtype(rhythm_len)
        self.min_dur = dtype(min_dur)
        self.num_notes = num_notes
        # would be nice to reduce increment if necessary as a function of
        # min_dur etc.
        self.increment = min(increment, rhythm_len)
        self.overlap = overlap
        self.var_palindrome = var_palindrome
        self.full = self.rhythm_len <= self.min_dur * self.num_notes

        if self.full or increment == 0:
            self.num_vars = 1
        else:
            self.num_vars = num_vars
        self.total_dur = self.num_vars * self.rhythm_len
        self.vary_consistently = vary_consistently
        self.dtype = dtype
        # I think the first iteration of the rhythm should always start at zero.
        # But perhaps subsequent repetitions can start elsewhere. I am leaving
        # this flag here for now but not yet implementing always_start_at_zero
        # = False.
        self.always_start_at_zero = True

        # attributes to be initialized later
        self._onsets_2d = np.empty(
            (self.num_vars, self.num_notes), dtype=self.dtype
        )
        self._durs_2d = np.empty_like(self._onsets_2d)
        self._deltas = self._unspaced = None
        self._iois = np.empty_like(self._onsets_2d)

        # cached math results
        self._min_int_dur = np.int64(
            INT_MAX / ((self.rhythm_len - self.min_dur) / self.min_dur)
        )
        self._rand_int_u_bound = INT_MAX - (self.num_notes - 1) * (
            self._min_int_dur - 1
        )
        self._int_increment = INT_MAX / self.rhythm_len * self.increment

    def _get_iois(self, i=0):
        self._iois[i] = utils.get_iois(
            self._onsets_2d[i], self.rhythm_len, self.overlap, dtype=self.dtype
        )

    def _update_onset_deltas(self):
        # maybe try the effect of a normal distribution as well?
        deltas = (
            er_globals.RNG.random(size=self.num_notes, dtype=self.dtype) - 1
        )
        deltas = deltas / deltas.sum() * self._int_increment
        self._deltas = deltas.astype(dtype=np.int64)

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
        self._unspaced = self._unspaced + self._deltas
        # stable sort = timsort
        self._unspaced.sort(kind="stable")
        # how do we prevent more than the first item from becoming
        # negative? (Later: I no longer understand what this comment is
        # referring to)
        if self.always_start_at_zero:
            # I guess doing this biases the output a little. LONGTERM think about
            # a better way of always starting from zero.
            self._unspaced[0] = 0
        else:
            raise NotImplementedError(
                "always_start_at_zero = False is not yet implemented"
            )
        # The following lines are a bit of a hack. We don't constrain the final
        # onset from growing larger, so it can get too close to the first onset
        # (on looping around). To avoid this, when necessary, we divide all
        # the onsets as follows.
        if self._unspaced[-1] > self._rand_int_u_bound:
            self._unspaced = (
                self._unspaced * (self._rand_int_u_bound / self._unspaced[-1])
            ).astype(np.int64)
        spaced = self._space_ints(self._unspaced)
        self._onsets_2d[i] = self._ints_to_onsets(spaced)

    def _init_onsets(self):
        if self.full:
            self._onsets_2d[0] = self.min_dur * np.arange(self.num_notes)

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
        self._unspaced = er_globals.RNG.integers(
            low=1,
            high=self._rand_int_u_bound,
            size=self.num_notes,
            dtype=np.int64,
            endpoint=True,
        )
        self._unspaced.sort()
        # We always want 0 as the first onset for the first rhythm
        self._unspaced[0] = 0
        spaced = self._space_ints(self._unspaced)
        self._onsets_2d[0] = self._ints_to_onsets(spaced)

    def set_onsets_and_durs(self, onsets, durs):
        # expects 2d onsets and 2d durs, reshapes them
        onsets = onsets.reshape(-1)
        durs = durs.reshape(-1)
        super().set_onsets_and_durs(onsets, durs)

    @abc.abstractmethod
    def _init_contents(self):
        return

    @abc.abstractmethod
    def _fill_contents(self, i):
        return

    def generate(self):
        # _init_contents() and _fill_contents() are to be provided by child
        # classes
        self._init_contents()
        for i in range(1, self.num_vars):
            if self.var_palindrome and i > self.num_vars / 2:
                j = self._get_palindromic_index(i)
                self._fill_palindrome(j, i)
            else:
                self._fill_contents(i)
        # Every row of _onsets_2d is generated to start at 0. Here, we
        # add offsets so that every row starts at row_i * rhythm_len.
        # Ultimately it would be more parsimonious to do this when generating
        # the onsets. Although doing it this way simplifies the case where
        # `cont_var_palindrome` is True.
        onset_offsets = (
            np.repeat(np.arange(self.num_vars), self.num_notes).reshape(
                (self.num_vars, self.num_notes)
            )
            * self.rhythm_len
        )
        self._onsets_2d = (self._onsets_2d + onset_offsets).round(8)
        self._durs_2d = self._durs_2d.round(8)

        self.set_onsets_and_durs(self._onsets_2d, self._durs_2d)

    def _get_palindromic_index(self, i):
        """Maps index i to its "palindromic" index j.

        When `self.cont_vars` (which I will call n below) is even, we don't
        create true palindromes because this would create two unnecessary
        instances of no change between adjacent variations, e.g.,
        (0, 3) and (1, 2) when n = 4:

        |‾‾‾‾‾|
        | |‾| |
        0 1 2 3

        Instead, the 0th and n / 2th elements have no "paired" indices, and this
        function will return None if called on those indices.

          |‾‾‾|
        0 1 2 3

        With an odd number of elements, adjacent variations with no change are
        inevitable; we make these the middle two elements.

          |‾‾‾‾‾|
          | |‾| |
        0 1 2 3 4

        Note also that if we consider the end of the sequence to be not n - 1
        but n (i.e., the repetition of the 0th element), then these *are* in
        fact palindromes.
        """
        n = self.num_vars
        if i % (n / 2) == 0:
            return None
        return n - i

    def _fill_palindrome(self, src_i, dst_i):
        self._onsets_2d[dst_i] = self._onsets_2d[src_i]


class ContRhythm(ContRhythmBase):
    def __init__(self, dur_density, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dur_density = dur_density
        self._min_density = self.min_dur / self.rhythm_len * self.num_notes
        if self._min_density == 1 or self.dur_density - self._min_density == 0:
            self._free_dur_density = 0
        else:
            self._free_dur_density = (self.dur_density - self._min_density) / (
                1 - self._min_density
            )

    def _init_contents(self):
        self._init_onsets()
        self._get_iois()
        self._init_durs()

    def _fill_contents(self, i):
        self._vary_onsets_unif(i)
        self._get_iois(i)
        self._fill_durs(i)

    def _fill_palindrome(self, src_i, dst_i):
        self._onsets_2d[dst_i] = self._onsets_2d[src_i]
        self._durs_2d[dst_i] = self._durs_2d[src_i]
        self._iois[dst_i] = self._iois[src_i]

    def _fill_durs(self, i):
        prev_durs = self._durs_2d[i - 1]
        self._durs_2d[i] = prev_durs.copy()
        current_durs = self._durs_2d[i]
        onsets = self._onsets_2d[i]
        if self._free_dur_density <= 0:
            # In this case there is nothing to do, because the onsets cannot be
            # moved closer than min_dur in any case.
            return

        if self.dur_density == 1:
            self._durs_2d[i] = self._iois[i]
            return
        assert (
            self._iois[i].sum()
            + (0 if self.overlap else onsets[0])
            - self.rhythm_len
            < 1e-10
        )
        ioi_deltas = self._iois[i] - self._iois[i - 1]
        neg_deltas = np.where(ioi_deltas < 0, ioi_deltas, 0)
        # Can this be made more efficient?
        current_durs += neg_deltas
        too_short = current_durs < self.min_dur
        add_back = self.min_dur - current_durs[too_short]
        neg_deltas[too_short] += add_back
        current_durs[too_short] = self.min_dur

        # The first onset is presently fixed at zero, so this works.
        #   Otherwise, we would need to get the first onset of the next
        #   repetition already.

        wraparound = current_durs[-1] + onsets[-1] - self.rhythm_len
        if wraparound > 0:
            current_durs[-1] -= wraparound
            neg_deltas[-1] -= wraparound
        assert (
            abs(current_durs.sum() - neg_deltas.sum()) - prev_durs.sum()
            <= 1e-10
        )
        releases = onsets + current_durs
        rois = utils.get_rois(onsets, releases, self.rhythm_len, self.overlap)
        assert (
            current_durs.sum()
            + rois.sum()
            + (0 if self.overlap else onsets[0])
            - self.rhythm_len
            < 1e-10
        )
        assert np.all(np.abs(current_durs + rois - self._iois[i]) < 1e-10)
        missing_density = (-neg_deltas.sum()) / rois.sum()
        current_durs += self._fill_durs_from_iois(rois, missing_density)
        assert np.all(current_durs - self._iois[i] < 1e-10)

    def _init_durs(self):
        if self.dur_density == 1:
            self._durs_2d[0] = self._iois[0]
            return
        if self._free_dur_density <= 0:
            self._durs_2d[0] = np.full(
                self.num_notes, self.min_dur, dtype=self.dtype
            )
            return
        available_iois = self._iois[0] - self.min_dur
        self._durs_2d[0] = self.min_dur + self._fill_durs_from_iois(
            available_iois, self._free_dur_density
        )
        assert np.all(self._durs_2d[0] <= self._iois[0])

    def _fill_durs_from_iois(self, available_iois, density):
        if not density:
            return np.zeros(len(available_iois), dtype=self.dtype)
        if density <= 0.5:
            subtract = False
        else:
            density = 1 - density
            subtract = True

        # available_iois = float_iois - self.min_dur
        int_iois = np.array(
            INT_MAX / available_iois.max() * available_iois, dtype=np.int64
        )
        # we divide the size of int_iois into "tranches" of approximately
        #  equal size
        tranche_counts = np.rint(int_iois / DUR_TRANCHE_SIZE)
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
        # the mean of y asymptotically approaches 0.5 rather than ever actually
        # getting there; maybe there is a better solution
        er_globals.RNG.shuffle(y)

        # Previously, I was taking the size of tranche_starts
        # from self.rhythm_len as follows:
        # tranche_starts = np.empty(int(self.rhythm_len), dtype=np.int64)
        # Presumably that was just an oversight but I don't see why it wasn't
        # causing more test failures.

        tranche_starts = np.empty_like(int_iois, dtype=np.int64)
        tranche_starts[0] = 0
        tranche_starts[1:] = np.cumsum(tranche_counts[:-1])
        # In spite of its name, int_durs is not an int type. Its name comes
        # from the fact that it measures the proportion of INT_MAX to take.

        # it is possible for the last tranche or even several tranches to
        # have 0 items, if the corresponding value in int_iois is <
        # DUR_TRANCHE_SIZE. If the call to rint rounds some other
        # tranches *up*, it is even possible for the last items in
        # tranche_starts to be > len(y). In that case, we need this special
        # case code.
        if tranche_starts[-1] >= len(y):
            j = 0
            while tranche_starts[j - 1] >= len(y):
                j -= 1
            int_durs = np.empty(len(int_iois))
            int_durs[:-j] = (
                np.add.reduceat(y, tranche_starts[:-j]) * DUR_TRANCHE_SIZE
            )
            int_durs[-j:] = 0
        else:
            int_durs = np.add.reduceat(y, tranche_starts) * DUR_TRANCHE_SIZE
        float_durs = int_durs / (INT_MAX / available_iois.max())
        # It seems that it is possible for float_durs to be > available_iois.
        # Due to rounding error, I imagine? I guess this is worth investigating
        # further. But for now, we just take the minimum of the two.
        out = np.minimum(float_durs, available_iois)
        if subtract:
            out = available_iois - out
        assert not np.any(np.isnan(out))
        return out

    @classmethod
    def from_er_settings(cls, er, voice_i):
        return cls(
            er.dur_density[voice_i],
            er.rhythm_len[voice_i],
            er.min_dur[voice_i],
            er.num_notes[voice_i],
            er.cont_var_increment[voice_i],
            er.overlap,
            er.num_cont_rhythm_vars[voice_i],
            er.vary_rhythm_consistently,
            er.cont_var_palindrome,
        )

    @staticmethod
    def validate_er_settings(er, silent=False):
        def warn_(text):
            if not silent:
                warnings.warn(text)

        def _homogenize_list(l, take):
            if take == "smallest":
                min_ = min(l)
                return [min_ for _ in l]
            return [l[0] for _ in l]

        def _enforce_unique_value(attr, take="first"):
            if len(set(getattr(er, attr))) > 1:
                warn_(
                    "`cont_rhythms = 'all'` is only implemented with a unique "
                    f"value for `{attr}`; ignoring all but the {take} value of "
                    f"`{attr}`"
                )
            setattr(er, attr, _homogenize_list(getattr(er, attr), take))

        _enforce_unique_value("pattern_len")
        _enforce_unique_value("rhythm_len")

        # LONGTERM can I remove this constraint?
        if er.pattern_len[0] != er.rhythm_len[0]:
            warn_(
                "`cont_rhythms = 'all'` is only implemented when "
                "`pattern_len` "
                "and `rhythm_len` have the same value (or when `rhythm_len` is "
                "omitted). Ignoring `rhythm_len`."
            )
        er.rhythm_len = er.pattern_len

        for i in range(er.num_voices):
            density = er.onset_density[i]
            min_dur = er.min_dur[i]
            onset_sub = er.onset_subdivision[i]

            if density * min_dur > onset_sub:
                warn_(
                    f"In voice {i}, `onset_density * min_dur` is greater than "
                    "`onset_subdivision`; "
                    "reducing `min_dur` to `onset_subdivision / "
                    f"onset_density = {onset_sub / density}` in this voice."
                )
                er.min_dur[i] = onset_sub / density
            if density * min_dur == onset_sub:
                warn_(
                    f"`cont_rhythms = 'all'` will have no effect in voice {i} "
                    "because `min_dur * onset_density == onset_subdivision` in "
                    "this voice. To allow "
                    "`cont_rhythms = 'all'` to have an effect in this voice, "
                    "reduce `min_dur` "
                )
