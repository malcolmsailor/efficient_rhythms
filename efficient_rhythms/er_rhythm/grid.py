import numpy as np

from .. import er_misc_funcs

from .cont_rhythm import ContinuousRhythm, ContRhythmBase, ContRhythmBase2


class Grid2(ContRhythmBase2):
    def __init__(
        self,
        rhythm_len,
        min_dur,
        num_onset_positions,
        increment,
        overlap,
        num_vars,
        vary_consistently=False,
        dtype=np.float64,
    ):

        super().__init__(
            rhythm_len,
            min_dur,
            num_onset_positions,
            increment,
            overlap,
            num_vars,
            vary_consistently,
            dtype,
        )

    def vary_rhythm(self, onsets, durs):
        # This function will only work as expected if the onsets are all in
        #   the grid.
        indices = np.nonzero(np.isin(self._onsets[0], onsets))[0]
        # We assert that onsets are all in the grid
        assert len(indices) == len(onsets)
        new_onsets = self._onsets[:, indices]
        # TODO durs
        # TODO investigate other functions I used to call (like truncate_or_extend())
        return new_onsets

    @classmethod
    def from_er_settings(cls, er):
        def _num_onset_positions():
            out = max(
                [r / s for (r, s) in zip(er.rhythm_len, er.onset_subdivision)]
            )
            return int(round(out))

        # TODO warnings in preprocessing
        return cls(
            er.rhythm_len[0],
            er.min_dur[0],
            _num_onset_positions(),
            er.cont_var_increment[0],
            er.overlap,
            er.num_cont_rhythm_vars[0],
            er.vary_rhythm_consistently[0],
        )

    @property
    def onset_positions(self):
        return self._onsets[0]


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
