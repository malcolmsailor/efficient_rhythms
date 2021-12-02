import itertools
import math
import typing
import warnings
from functools import cached_property

import numpy as np

from .. import er_choirs
from .. import er_constants
from ..er_interface import BuildStatusPrinter
from .. import er_midi
from .. import er_misc_funcs
from .. import er_tuning
from .. import er_validate
from .. import er_voice_leadings


from .settings import SettingsDataclass
from .warnings_ import notify_user_of_unusual_settings


class SettingsPostprocessor(SettingsDataclass):
    """Cached properties for settings that are derived from other settings."""

    def __post_init__(self):
        super().__post_init__()
        self._postprocess_fields()
        self._chord_pcs = {}
        self._nonchord_pcs = {}
        self._chord_indices = {}
        self._nonchord_indices = {}
        self._get_scales_and_chords_from_midi()
        self._chord_tone_and_foot_toggle()
        er_validate.validate_settings(self)
        notify_user_of_unusual_settings(self, silent=self._silent)
        self._set_seed()

    def _get_scales_and_chords_from_midi(self):
        if not self.scales_and_chords_specified_in_midi:
            return
        (
            self.scales,
            self.chords,
            self.foot_pcs,
        ) = er_midi.get_scales_and_chords_from_midi(
            self.scales_and_chords_specified_in_midi
        )

    def _postprocess_fields(self):
        for field_name, field_args in self._fields:
            if "postprocess" in field_args.metadata:
                postprocess_funcs = field_args.metadata["postprocess"]
                if isinstance(postprocess_funcs, typing.Callable):
                    postprocess_funcs = (postprocess_funcs,)
                for func in postprocess_funcs:
                    setattr(self, field_name, func(self, field_name))

    def _chord_tone_and_foot_toggle(self):
        if not self.chord_tone_and_foot_disable:
            return

        self.chord_tone_selection = False
        self.chord_tones_no_diss_treatment = [
            False for i in range(self.num_voices)
        ]
        self.force_chord_tone = ["none" for i in range(self.num_voices)]
        self.force_foot_in_bass = "none"
        self.max_interval_for_non_chord_tones = self.max_interval
        self.min_interval_for_non_chord_tones = self.max_interval
        self.voice_lead_chord_tones = False
        self.preserve_foot_in_bass = "none"
        self.extend_bass_range_for_foots = 0

    def _pcsets(self, scs):
        out = []
        for i, foot_pc in enumerate(self.foot_pcs):
            set_class = scs[i % len(scs)]
            out.append([(pc + foot_pc) % self.tet for pc in set_class])
        return out

    @cached_property
    def pc_chords(self):
        return self._pcsets(self.chords)

    @cached_property
    def pc_scales(self):
        return self._pcsets(self.scales)

    @cached_property
    def build_status_printer(self):
        if self._silent:
            return None
        return BuildStatusPrinter(self)

    @cached_property
    def len_all_harmonies(self):
        return (
            sum(self.harmony_len) / len(self.harmony_len) * self.num_harmonies
        )

    @cached_property
    def pitch_loop_complete(self):
        out = []
        for pitch_loop in self.pitch_loop:
            if pitch_loop:
                out.append(False)
            else:
                out.append(None)
        return out

    @cached_property
    def super_pattern_len(self):
        try:
            out = er_misc_funcs.lcm(
                (
                    [max(self.pattern_len)]
                    if self.truncate_patterns
                    else self.pattern_len
                )
                + [
                    self.len_all_harmonies,
                ],
                max_n=self.max_super_pattern_len,
            )
        except er_misc_funcs.LCMError as exc:
            out = self.max_super_pattern_len
            if not self._silent:
                print(
                    f"Notice: {exc} Reducing `super_pattern_len` to "
                    f"{self.max_super_pattern_len}"
                )

        if out > self.max_super_pattern_len:
            return self.max_super_pattern_len
        return out

    @cached_property
    def total_len(self):
        return self.super_pattern_len * self.num_reps_super_pattern

    @cached_property
    def control_log_base(self):
        return 10 ** (self.prefer_small_melodic_intervals_coefficient * 0.1)

    @cached_property
    def pitch_bend_tuple_dict(self):
        return er_tuning.return_pitch_bend_tuple_dict(self.tet)

    @cached_property
    def voice_order(self):
        out = list(range(self.num_voices))
        if self.voice_order_str != "reverse":
            return out
        out.reverse()
        return out

    @cached_property
    @staticmethod
    def already_warned():
        """Certain warnings should only occur once, even though the situation
        that provokes them may occur many times. This dictionary helps keep
        track of that.
        """
        return {
            "force_foot": set(),
            "hard_bounds": set(),
        }

    @cached_property
    def sub_subdiv_props(self):
        out = []
        for voice_i in range(self.num_voices):
            subs = self.get(voice_i, "sub_subdivisions")
            if not subs or len(subs) == 1:
                out.append(None)
            else:
                out.append(
                    # TODO data type
                    np.cumsum([0] + list(subs)[:-1], dtype=np.float32)
                    / np.sum(subs, dtype=np.float32)
                )
        return out

    @cached_property
    def num_notes(self):
        def _num_notes(voice_i):
            if voice_i in self.rhythmic_unison_followers:
                leader_i = self.rhythmic_unison_followers[voice_i]
                return out[leader_i]
            rhythm_len = self.rhythm_len[voice_i]
            density = self.onset_density[voice_i]
            onset_div = self.onset_subdivision[voice_i]

            subdiv_props = self.sub_subdiv_props[voice_i]
            len_sub_subdiv = (
                len(subdiv_props)
                if self.cont_rhythms == "none" and subdiv_props is not None
                else 1
            )
            num_div = int(rhythm_len / onset_div * len_sub_subdiv)
            if isinstance(density, int):
                if density > num_div:
                    print(
                        f"Notice: voice {voice_i} onset density of {density} "
                        f"is greater than {num_div}, the number of divisions.  "
                        f"Reducing to {num_div}."
                    )
                num_notes = min(density, num_div)
            else:
                # if isinstance(density, float):
                num_notes = min(round(density * num_div), num_div)
            # this will fail if self.obligatory_onsets contains many notes and they
            #   are not valid times (don't lie on onset_subdivision)
            # TODO raise an error for invalid obligatory onsets
            return max(num_notes, 1, len(self.obligatory_onsets[voice_i]))

        out = [None for _ in range(self.num_voices)]
        for group in self.rhythmic_unison:
            for voice_i in group:
                out[voice_i] = _num_notes(voice_i)
        for voice_i in range(self.num_voices):
            if out[voice_i] is None:
                out[voice_i] = _num_notes(voice_i)
        return tuple(out)

    # It appears the gcd properties below are unused
    # TODO remove
    # @cached_property
    # def onset_subdivision_gcd(self):
    #     return er_misc_funcs.gcd_from_list(
    #         self.onset_subdivision,
    #         self.sub_subdiv_props,
    #         self.pattern_len,
    #         self.harmony_len,
    #         self.rhythm_len,
    #         self.obligatory_onsets,
    #         self.obligatory_onsets_modulo,
    #     )

    # @cached_property
    # def er_dur_gcd(self):
    #     return er_misc_funcs.gcd_from_list(
    #         self.onset_subdivision_gcd, self.dur_subdivision, self.min_dur
    #     )

    @cached_property
    def rhythmic_unison_followers(self):
        return self._get_rhythmic_unison_followers(self.rhythmic_unison)

    @cached_property
    def rhythmic_quasi_unison_followers(self):
        return self._get_rhythmic_unison_followers(self.rhythmic_quasi_unison)

    @staticmethod
    def _get_rhythmic_unison_followers(unison_val):
        follower_dict = {}
        for group in unison_val:
            leader = group[0]
            for follower in group[1:]:
                follower_dict[follower] = leader
        return follower_dict

    @cached_property
    def hocketing_followers(self):
        follower_dict = {}
        for group in self.hocketing:
            for follower_i, follower in zip(itertools.count(1), group[1:]):
                follower_dict[follower] = tuple(
                    group[i] for i in range(follower_i)
                )
        return follower_dict

    @cached_property
    def pattern_vl_order(self):
        # QUESTION put parallel voices immediately after their leader in voice
        #       order? or put them after all other voices? or setting to control
        #       this?

        out = []

        if self.truncate_patterns:
            truncate_len = max(self.pattern_len)
        voice_offset = 0
        for voice_i in self.voice_order:
            pattern_i = 0
            start_time = 0
            pattern_len = self.pattern_len[voice_i]
            if self.truncate_patterns:
                next_truncate = truncate_len
                n_since_prev_pattern = math.ceil(truncate_len / pattern_len)
            else:
                n_since_prev_pattern = 1
            while start_time < self.super_pattern_len:
                end_time = start_time + pattern_len
                if self.truncate_patterns:
                    if start_time == next_truncate:
                        next_truncate += truncate_len
                    end_time = min(end_time, next_truncate)
                if pattern_i == 0:
                    prev_item = None
                else:
                    if pattern_i < n_since_prev_pattern:
                        prev_pattern_i = pattern_i - 1
                    else:
                        prev_pattern_i = pattern_i - n_since_prev_pattern
                    prev_item = out[prev_pattern_i + voice_offset]
                out.append(
                    er_voice_leadings.VLOrderItem(
                        voice_i,
                        start_time,
                        end_time,
                        prev=prev_item,
                    )
                )
                start_time = end_time
                pattern_i += 1
            voice_offset += pattern_i

        out.sort(key=lambda x: x.end_time, reverse=True)
        out.sort(key=lambda x: x.start_time)
        return out

    def _parallel_motion_leaders_and_followers(self, from_leaders=True):
        parallel_motion_leaders = {}
        parallel_motion_followers = {}
        for voice_tuple, motion_type in self.force_parallel_motion.items():
            if motion_type == "false":
                continue
            voices = list(voice_tuple)
            leader_i = voices.pop(0)
            parallel_motion_leaders[leader_i] = voices[:]
            while voices:
                follower_i = voices.pop(0)
                parallel_motion_followers[
                    follower_i
                ] = er_voice_leadings.ParallelMotionInfo(leader_i, motion_type)
        if from_leaders:
            self.parallel_motion_followers = parallel_motion_followers
            return parallel_motion_leaders
        self.parallel_motion_leaders = parallel_motion_leaders
        return parallel_motion_followers

    @cached_property
    def parallel_motion_leaders(self):  # pylint: disable=method-hidden
        return self._parallel_motion_leaders_and_followers()

    @cached_property
    def parallel_motion_followers(self):  # pylint: disable=method-hidden
        return self._parallel_motion_leaders_and_followers(from_leaders=False)

    @cached_property
    def num_choirs(self):
        if self.randomly_distribute_between_choirs:
            return len(self.choirs)
        return len(set(self.choir_assignments))

    @cached_property
    def choir_order(self):
        if not self.randomly_distribute_between_choirs:
            return (self.choir_assignments,)
        if self.length_choir_segments < 0:
            return er_choirs.order_choirs(self, max_len=1)
        if self.length_choir_loop is None or self.length_choir_loop <= 0:
            warn_if_loop_too_short = False
            num_choir_segments = self.total_len / self.length_choir_segments
        else:
            warn_if_loop_too_short = True
            num_choir_segments = (
                self.length_choir_loop / self.length_choir_segments
            )
            if num_choir_segments % 1 != 0:
                warnings.warn(
                    f"\n'length_choir_loop' ({self.length_choir_loop}) / "
                    "'length_choir_segments' "
                    f"({self.length_choir_segments}) "
                    "is not a whole number. Rounding..."
                )
        num_choir_segments = round(num_choir_segments)
        return er_choirs.order_choirs(
            self,
            max_len=num_choir_segments,
            warn_if_loop_too_short=warn_if_loop_too_short,
        )

    @cached_property
    def choir_programs(self):
        def _get_choir(choir):
            if isinstance(choir, int):
                return choir
            try:
                return getattr(er_constants, choir)
            except AttributeError:
                raise ValueError(  # pylint: disable=raise-missing-from
                    f"{choir} is not an implemented choir constant. See "
                    "docs/er_constants.html for a list of available constants."
                )

        choir_programs = []
        for choir_i in range(self.num_choirs):
            # Why are both choir_programs and choirs necessary?
            # er.num_choirs is determined by choir_assignments, and is potentially
            # longer than er.choirs. I should do something about this!
            choir = self.choirs[choir_i % len(self.choirs)]
            if isinstance(choir, (int, str)):
                choir_programs.append(_get_choir(choir))
            else:
                raise NotImplementedError(
                    "'choirs' must be integers or strings defined in "
                    "er_constants.py"
                )
        return choir_programs
        # # LONGTERM implement choir split points
        # #   it seems I never actually completed implementing this
        ############
        # # here is the old docstring from er_settings which provides a spec:
        # choirs: a sequence of ints or tuples.
        #
        #     Integers specify the program numbers of GM midi instruments.
        #     Constants defining these can be found in `er_constants.py`.
        #
        #     Tuples can be used to combine multiple instruments (e.g., violins
        #     and cellos) into a single "choir". They should consist of two items:
        #         - a sequence of GM midi instruments, listed from low to high
        #         - an integer or sequence of integers, specifying a split point
        #         or split points, that is, the pitches at which the instruments
        #         should be switched between.
        #     Default: (er_constants.MARIMBA, er_constants.VIBRAPHONE,
        #     er_constants.ELECTRIC_PIANO, er_constants.GUITAR,)
        ############
        # sub_choirs, split_points = choir
        # if not isinstance(split_points, typing.Sequence):
        #     split_points = [
        #         split_points,
        #     ]
        # sub_choir_progs = [
        #     _get_choir(sub_choir) for sub_choir in sub_choirs
        # ]
        # er.choirs[choir_i] = er_choirs.Choir(sub_choir_progs, split_points,)
        # er.choirs[choir_i].temper_split_points(
        #     er.tet, er.integers_in_12_tet
        # )
        # er.choir_programs += sub_choir_progs

    @cached_property
    def num_choir_programs(self):
        return len(self.choir_programs)

    @cached_property
    def existing_score(self):
        if not self.existing_voices:
            return None
        existing_score = er_midi.read_midi_to_internal_data(
            self.existing_voices,
            tet=self.tet,
            time_sig=self.time_sig,
            track_num_offset=1 + self.num_voices,
            max_denominator=self.existing_voices_max_denominator,
        )
        existing_score.displace_passage(self.existing_voices_offset)
        return existing_score

    @cached_property
    def existing_voices_indices(self):
        if not self.existing_voices:
            return ()
        return tuple(
            i + 1 + self.num_voices
            for i in range(self.existing_score.num_voices)
        )

    @cached_property
    def gamut_scales(self):
        out = []
        for pc_scale in self.pc_scales:
            out.append(
                sorted([i + j * self.tet for i in pc_scale for j in range(12)])
            )
        return out

    def nonchord_pcs_at_harmony_i(self, i):
        if i not in self._nonchord_pcs:
            self._get_chord_and_nonchord_pcs(i)
        return self._nonchord_pcs[i]

    def chord_pcs_at_harmony_i(self, i):
        if i not in self._chord_pcs:
            self._get_chord_and_nonchord_pcs(i)
        return self._chord_pcs[i]

    def _get_chord_and_nonchord_pcs(self, i):
        chord_pcs = []
        non_chord_pcs = []
        pc_scale, pc_chord = self.get(i, "pc_scales", "pc_chords")
        for pc in pc_scale:
            if pc in pc_chord:
                chord_pcs.append(pc)
            else:
                non_chord_pcs.append(pc)
        self._chord_pcs[i] = tuple(chord_pcs)
        self._nonchord_pcs[i] = tuple(non_chord_pcs)

    def nonchord_indices_at_harmony_i(self, i):
        if i not in self._nonchord_indices:
            self._get_chord_and_nonchord_indices(i)
        return self._nonchord_indices[i]

    def chord_indices_at_harmony_i(self, i):
        if i not in self._chord_indices:
            self._get_chord_and_nonchord_indices(i)
        return self._chord_indices[i]

    def _get_chord_and_nonchord_indices(self, i):
        # TODO should we combine this and _get_chord_and_nonchord_pcs? How
        # likely are the functions to be called/not-called at the same time?
        chord_indices = {}
        chord_i = 0
        nonchord_indices = {}
        nonchord_i = 0
        pc_scale, pc_chord = self.get(i, "pc_scales", "pc_chords")
        for j, pc in enumerate(pc_scale):
            if pc in pc_chord:
                chord_indices[chord_i] = j
                chord_i += 1
            else:
                nonchord_indices[nonchord_i] = j
                nonchord_i += 1
        self._chord_indices[i] = chord_indices
        self._nonchord_indices[i] = nonchord_indices
