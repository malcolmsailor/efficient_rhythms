import random
import warnings

import numpy as np

from . import utils
from .cont_rhythm import ContRhythm


class Grid(ContRhythm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._releases = None

    def set_onsets_and_durs(self, onsets, durs):
        super().set_onsets_and_durs(onsets, durs)
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
        return cls(
            er.dur_density[
                0
            ],  # TODO how do we deal with voices of different dur_density?
            er.rhythm_len[0],
            er.min_dur[0],
            cls._num_onset_positions(er.rhythm_len[0], er.onset_subdivision),
            er.cont_var_increment[0],
            er.overlap,
            er.num_cont_rhythm_vars[0],
            er.vary_rhythm_consistently[0],
            er.cont_var_palindrome,
        )

    # _num_onset_positions() is a static method because we want to be able to
    # call it before any instance is initialized
    @staticmethod
    def _num_onset_positions(rhythm_len, onset_subdivisions):
        out = rhythm_len / min(onset_subdivisions)
        return int(round(out))

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
                    "`cont_rhythms = 'grid'` is only implemented with a unique "
                    f"value for `{attr}`; ignoring all but the {take} value of "
                    f"`{attr}`"
                )
            setattr(er, attr, _homogenize_list(getattr(er, attr), take))

        _enforce_unique_value("pattern_len")
        _enforce_unique_value("rhythm_len")

        if er.pattern_len[0] != er.rhythm_len[0]:
            warn_(
                "`cont_rhythms = 'grid'` is only implemented when "
                "`pattern_len` "
                "and `rhythm_len` have the same value (or when `rhythm_len` is "
                "omitted). Ignoring `rhythm_len`."
            )
        er.rhythm_len = er.pattern_len

        _enforce_unique_value("num_cont_rhythm_vars")
        _enforce_unique_value("vary_rhythm_consistently")
        _enforce_unique_value("cont_var_increment")
        _enforce_unique_value("min_dur", "smallest")

        min_sub = min(er.onset_subdivision)
        if er.min_dur[0] > min_sub:
            warn_(
                "`min_dur` is greater than smallest `onset_subdivision`; "
                f"reducing `min_dur` to `{min_sub}`."
            )
            er.min_dur = [min_sub for _ in er.min_dur]

        if er.min_dur[0] == min_sub:
            warn_(
                "`cont_rhythms = 'grid'` will have no effect because "
                "`min_dur == min(onset_subdivision)`. To allow "
                "`cont_rhythms = 'grid'` to have an effect, reduce `min_dur` "
                "to less than the smallest value in `onset_subdivision`"
            )
