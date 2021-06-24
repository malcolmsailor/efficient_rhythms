import random

import numpy as np

from .. import er_misc_funcs

from . import utils
from .cont_rhythm import ContRhythm
from .deprecated import ContinuousRhythm, ContRhythmBase  # TODO remove


class Grid2(ContRhythm):
    # def __init__(
    #     self,
    #     rhythm_len,
    #     min_dur,
    #     num_onset_positions,
    #     increment,
    #     overlap,
    #     num_vars,
    #     vary_consistently=False,
    #     dtype=np.float64,
    # ):

    #     super().__init__(
    #         rhythm_len,
    #         min_dur,
    #         num_onset_positions,
    #         increment,
    #         overlap,
    #         num_vars,
    #         vary_consistently,
    #         dtype,
    #     )
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._releases = None

    def add_onsets_and_durs(self, onsets, durs):
        super().add_onsets_and_durs(onsets, durs)
        # We construct _releases_2d from _releases (and not the other way
        # around) because _onsets has been adjusted to be monotonically
        # increasing whereas each row of _onsets_2d always starts at 0. (See
        # the parent's add_onset_and_durs() method).
        self._releases = (self.onsets + self.durs).round(8)
        self._releases_2d = self._releases.reshape(
            (self.num_vars, self.num_notes)
        )

    @property
    def releases(self):
        return self._releases

    def _init_contents(self):
        super()._init_contents()
        # self._releases_2d[0] = (self._onsets_2d[0] + self._durs_2d[0]).round(
        #     decimals=8
        # )

    def _fill_contents(self, i):
        super()._fill_contents(i)
        # self._releases_2d[i] = self._onsets_2d[i] + self._durs_2d[i]

    def onset_indices(self, onsets):
        onset_indices = np.nonzero(np.isin(self._onsets_2d[0], onsets))[0]
        # We assert that onsets are all in the grid
        try:
            assert len(onset_indices) == len(onsets)
        except:
            breakpoint()
        return onset_indices

    def vary(self, onsets, durs):
        # This function will only work as expected if the onsets and releases
        #   are all in the grid.
        onset_indices = self.onset_indices(onsets)
        releases = (onsets + durs).round(decimals=8)
        # after implementing the out_of_bounds check below I think wraparound
        # is no longer necessary
        # wraparound = releases[-1] > self.total_dur
        # if wraparound:
        #     releases[-1] = (releases[-1] - self.total_dur).round(8)
        release_indices = utils.get_indices_from_sorted(
            releases, self.releases, loop_len=self.total_dur
        )
        assert len(release_indices) == len(releases)

        new_onsets = self._onsets_2d[:, onset_indices]
        # we have to catch the edge case where the last item in release indices
        # is out of bounds. (It can't happen that more than the last
        # index is out of bounds).
        out_of_bounds = release_indices[-1] >= self.num_notes
        if out_of_bounds:
            wrapped_i = release_indices[-1] % self.num_notes
            new_releases = np.empty_like(new_onsets)
            new_releases[:, :-1] = self._releases_2d[:, release_indices[:-1]]
            new_releases[:-1, -1] = self._releases_2d[1:, wrapped_i]
            new_releases[-1, -1] = (
                self._releases_2d[0, wrapped_i] + self.total_dur
            ).round(8)
        else:
            new_releases = self._releases_2d[:, release_indices]

        new_durs = (new_releases - new_onsets).round(8)
        # if wraparound:
        #     new_durs[-1, -1] = (new_durs[-1, -1] + self.total_dur).round(8)
        assert np.all(new_durs > 0) and np.all(new_durs < self.rhythm_len)
        # TODO investigate other functions I used to call (like truncate_or_extend())
        return new_onsets.reshape(-1), new_durs.reshape(-1)

    def _get_max_releases(self, onset_indices):
        # We expect this function to only ever be called on indices <
        # self.num_notes (i.e., belonging to the first 'variation')

        max_releases = np.empty(len(onset_indices), dtype=self.dtype)
        releases_iter = iter(
            utils.LoopSeq(self.releases, self.total_dur, decimals=8)
        )
        release = next(releases_iter)
        for i in range(len(onset_indices) - 1):
            next_onset_i = onset_indices[i + 1]
            next_onset = self.onsets[next_onset_i].round(8)
            while (next_release := next(releases_iter)) <= next_onset:
                release = next_release
            max_releases[i] = release
            release = next_release
        if self.overlap:
            next_onset_i = onset_indices[0] + self.num_notes
            try:
                next_onset = self.onsets[next_onset_i]
            except IndexError:
                assert self.num_vars == 1
                next_onset = (
                    self.onsets[next_onset_i % self.num_notes] + self.rhythm_len
                ).round(8)
            while (next_release := next(releases_iter)) - next_onset < 1e-7:
                release = next_release
            max_releases[-1] = release
        else:
            max_releases[-1] = self.rhythm_len
        return max_releases

    def _durs_handler(self, er, voice_i, onsets, onset_indices, durs):
        releases = utils.LoopSeq(self.releases, self.total_dur, decimals=8)
        max_releases = self._get_max_releases(onset_indices)
        total_remaining = (
            er.dur_density[voice_i] * er.rhythm_len[voice_i] - durs.sum()
        )

        available_indices = list(range(len(onsets)))
        # map onset_indices to release indices
        release_indices = {
            i: k for (i, k) in zip(available_indices, onset_indices)
        }
        # remove any indices that are already at the maximum release
        for i, k in release_indices.items():
            if releases[k] == max_releases[i]:
                available_indices.remove(i)

        while total_remaining > 0 and available_indices:
            i = random.choice(available_indices)
            k = release_indices[i] = release_indices[i] + 1
            release = releases[k]
            increment = release - releases[k - 1]
            durs[i] += increment
            # release = (durs[i] + onsets[i]).round(decimals=8)
            total_remaining -= increment
            if release == max_releases[i]:
                available_indices.remove(i)
            elif abs(release - max_releases[i]) < 1e-7:
                breakpoint()
            assert release <= max_releases[i]
        return durs

    def get_durs(self, er, voice_i, onsets, prev_rhythms):
        # TODO handle prev_rhythms
        onset_indices = self.onset_indices(onsets)
        # durs are initialized as the interval to the next release
        durs = self._releases[onset_indices] - onsets
        # then we possibly fill durs further
        durs = self._durs_handler(er, voice_i, onsets, onset_indices, durs)

        return durs

    @property
    def onset_positions(self):
        return self.onsets

    @property
    def initial_onset_positions(self):
        return self._onsets_2d[0]

    @classmethod
    def from_er_settings(cls, er):
        def _num_onset_positions():
            out = max(
                [r / s for (r, s) in zip(er.rhythm_len, er.onset_subdivision)]
            )
            return int(round(out))

        # TODO warnings in preprocessing
        return cls(
            er.dur_density[
                0
            ],  # TODO how do we deal with voices of different dur_density?
            er.rhythm_len[0],
            er.min_dur[0],
            _num_onset_positions(),
            er.cont_var_increment[0],
            er.overlap,
            er.num_cont_rhythm_vars[0],
            er.vary_rhythm_consistently[0],
            er.cont_var_palindrome,
        )


class Grid(ContRhythmBase):
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
        self.get_continuous_onsets()
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

    def return_varied_rhythm(self, er, onsets, durs, voice_i):
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
        # var_durs[0] = list(onsets.values())
        var_durs[0] = list(durs)
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
