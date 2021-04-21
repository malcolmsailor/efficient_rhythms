"""This script performs preprocessing on various settings to prepare them for
use.
"""

import collections
import fractions
import math
import os
import random
import typing
import warnings

import numpy as np

import src.er_choirs as er_choirs
import src.er_constants as er_constants
import src.er_interface as er_interface
import src.er_midi as er_midi
import src.er_misc_funcs as er_misc_funcs
import src.er_randomize as er_randomize
import src.er_settings as er_settings
import src.er_tuning as er_tuning
import src.er_voice_leadings as er_voice_leadings

SCRIPT_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..")

PITCH_MATERIAL_LISTS = (
    "scales",
    "chords",
    "foot_pcs",
    "interval_cycle",
    "voice_ranges",
    "hard_bounds",
    "consonances",
    "consonant_chords",
    "forbidden_intervals",
    "forbidden_interval_classes",
    "prohibit_parallels",
    "transpose_intervals",
    "max_interval",
    "max_interval_for_non_chord_tones",
    "min_interval",
    "min_interval_for_non_chord_tones",
)

PITCH_MATERIALS = (
    # TODO finish populating this list?
    "unison_weighted_as",
)


# INTERNET_TODO either replace `warnings` module with simple print statements
#   or figure out a way to integrate their appearance more closely into the
#   rest of the script


class SettingsError(Exception):
    pass


def notify_user_of_unusual_settings(er):
    def print_(text):
        print(er_misc_funcs.add_line_breaks(text))

    if er.cont_rhythms != "none" and (
        len(set(er.pattern_len)) != 1
        or len(set(er.rhythm_len)) != 1
        or er.pattern_len != er.rhythm_len
    ):
        # LONGTERM implement this
        raise NotImplementedError(
            "'cont_rhythms' is not implemented unless 'pattern_len' and "
            "'rhythm_len' have the same, unique value"
        )

    if er.len_to_force_chord_tone == 0 and er.scale_chord_tone_prob_by_dur:
        raise SettingsError(
            "If 'scale_chord_tone_prob_by_dur' is True, then "
            "'len_to_force_chord_tone' must be non-zero."
        )
    if len(er.voice_ranges) < er.num_voices:
        raise SettingsError("len(voice_ranges) < num_voices")
    if er.scale_short_chord_tones_down and er.try_to_force_non_chord_tones:
        print_(
            "Warning: 'scale_short_chord_tones_down' and "
            "'try_to_force_non_chord_tones' are both true. Strange results may occur, "
            "particularly if there are many short notes."
        )
    if (
        er.chord_tones_sync_attack_in_all_voices
        and er.scale_chord_tone_prob_by_dur
    ):
        print(
            "Notice: 'chord_tones_sync_attack_in_all_voices' and "
            "'scale_chord_tone_prob_by_dur' are both true. Long notes in some "
            "voices may be non chord tones."
        )
    if er.chord_tone_selection != er.voice_lead_chord_tones:
        print_(
            f"Notice: 'chord_tone_selection' is {er.chord_tone_selection} "
            f"and 'voice_lead_chord_tones' is {er.voice_lead_chord_tones}"
        )

    if er.logic_type_pitch_bend:
        if er.tet == 12:
            print("Notice: 'logic_type_pitch_bend' is True and 12-tet.")
        else:
            if not er.voices_separate_tracks and er.num_voices > 1:
                warnings.warn(
                    "'logic_type_pitch_bend' and "
                    "not 'voices_separate_tracks'"
                )
            if not er.choirs_separate_tracks and er.num_choirs > 1:
                warnings.warn(
                    "'logic_type_pitch_bend' and "
                    "not 'choirs_separate_tracks'"
                )
            if er.choirs_separate_channels and er.num_choirs > 1:
                warnings.warn(
                    "'logic_type_pitch_bend' and "
                    "'choirs_separate_channels'\n"
                    "   Ignoring 'choirs_separate_channels'..."
                )

    if er.parallel_voice_leading and er.vl_maintain_consonance:
        print_(
            "Notice: 'parallel_voice_leading' is not compatible with "
            "checking voice-leadings for consonance. Ignoring "
            "'vl_maintain_consonance'"
        )

    soft_loop_max_alt_conflicts = []
    for voice_i in range(er.num_voices):
        if (
            er.get(voice_i, "pitch_loop")
            and not er.get(voice_i, "hard_pitch_loop")
            and (er.get(voice_i, "max_alternations") > 0)
        ):
            soft_loop_max_alt_conflicts.append(voice_i)
    if soft_loop_max_alt_conflicts:
        print_(
            "Notice: in {} {}, soft pitch loops are enabled and "
            "max_alternations is set as well. This "
            "may lead to shorter loops than expected in {}."
            "".format(
                "voice" if len(soft_loop_max_alt_conflicts) == 1 else "voices",
                soft_loop_max_alt_conflicts,
                "this voice"
                if len(soft_loop_max_alt_conflicts) == 1
                else "these voices",
            )
        )

    for limit_interval in ("max_interval", "min_interval"):
        soft_loop_limit_interval_conflicts = []
        for voice_i in range(er.num_voices):
            if (
                er.get(voice_i, "pitch_loop")
                and not er.get(voice_i, "hard_pitch_loop")
                and er.get(voice_i, limit_interval + "_for_non_chord_tones")
                and (
                    er.get(voice_i, limit_interval + "_for_non_chord_tones")
                    != er.get(voice_i, limit_interval)
                )
            ):
                soft_loop_limit_interval_conflicts.append(voice_i)
        if soft_loop_limit_interval_conflicts:
            voice_str = (
                "voice"
                if len(soft_loop_limit_interval_conflicts) == 1
                else "voices"
            )
            this_str = (
                "this voice"
                if len(soft_loop_limit_interval_conflicts) == 1
                else "these voices"
            )
            print_(
                f"Notice: in {voice_str} {soft_loop_limit_interval_conflicts}, "
                "soft pitch loops are enabled and "
                f"{limit_interval}_for_non_chord_tones is not equal to "
                f"{limit_interval}. Since chord tones can "
                "proceed by different intervals than non chord tones in "
                f"{this_str}, this may lead to shorter loops than expected."
            )

    if 1 in er.max_interval and er.chord_tone_selection:
        warnings.warn(
            er_misc_funcs.add_line_breaks(
                "Max interval of 1 (i.e., a 2nd) in at least "
                "one voice and 'chord_tone_selection' is true. "
                "This is likely to lead to excess repeated notes."
            )
        )


def check_min_dur(er):
    for voice_i, rhythm_len in enumerate(er.rhythm_len):
        if rhythm_len < er.min_dur[voice_i] * er.num_notes[voice_i]:
            new_min_dur = er_misc_funcs.convert_to_fractions(
                rhythm_len / er.num_notes[voice_i]
            )
            print(
                f"Notice: min_dur too long in voice {voice_i} rhythm; "
                f"reducing from {er.min_dur[voice_i]} to {new_min_dur}."
            )
            er.min_dur[voice_i] = new_min_dur


def prepare_warnings(er):
    """Certain warnings should only occur once, even though the situation
    that provokes them may occur many times. This function initializes
    a dictionary for keeping track of this.
    """
    er.already_warned = {
        "force_foot": collections.Counter(),
    }


# PITCH_CONSTANT_OP_MAP = {
#     "*": ("__mul__", "__rmul__"),
#     "+": ("__add__", "__radd__"),
#     "-": ("__sub__", "__rsub__"),
#     "/": ("__truediv__", "__rtruediv__"),  # MAYBE test
# }


def replace_pitch_constants(er):
    # class PitchConstantError(Exception):
    #     pass

    def _process_str(pitch_str):
        pitch_str = pitch_str.replace("#", "_SHARP")
        return eval(pitch_str, vars(er_constants))
        # bits = pitch_str.split()
        # val = 1
        # next_op, rnext_op = "__mul__", "__rmul__"
        # for bit in bits:
        #     if next_op is None:
        #         try:
        #             next_op, rnext_op = PITCH_CONSTANT_OP_MAP[bit]
        #         except KeyError:
        #             raise PitchConstantError(  # pylint: disable=raise-missing-from
        #                 f"{bit} is not an implemented operation on pitch "
        #                 "constants. Implemented pitch constant operations are "
        #                 f"{tuple(PITCH_CONSTANT_OP_MAP.keys())}."
        #                 # MAYBE see documentation for more help
        #             )
        #     else:
        #         # MAYBE document sign flip with "-" for descending intervals
        #         if bit[0] == "-":
        #             sign = -1
        #             bit = bit[1:]
        #         else:
        #             sign = 1
        #         try:
        #             constant = sign * getattr(er_constants, bit)
        #         except AttributeError:
        #             raise PitchConstantError(  # pylint: disable=raise-missing-from
        #                 f"{bit} is not an implemented pitch constant."
        #             )
        #             # TODO see documentation for more help
        #         next_val = getattr(val, next_op)(constant)
        #         if next_val is NotImplemented:
        #             val = getattr(constant, rnext_op)(val)
        #         else:
        #             val = next_val
        #         next_op = None
        # if next_op is not None:
        #     raise PitchConstantError(
        #         f"Trailing operation in pitch constant {pitch_str}"
        #     )
        # return val

    def _replace(pitch_material, i):
        if isinstance(pitch_material[i], str):
            pitch_material[i] = _process_str(pitch_material[i])
        elif isinstance(pitch_material[i], typing.Sequence):
            for j in range(len(pitch_material[i])):
                pitch_material[i] = list(pitch_material[i])
                _replace(pitch_material[i], j)

    for pitch_material_name in PITCH_MATERIAL_LISTS + PITCH_MATERIALS:
        pitch_material = getattr(er, pitch_material_name)
        if pitch_material is not None:
            if isinstance(pitch_material, str):
                pitch_material = _process_str(pitch_material)
            elif isinstance(pitch_material, typing.Sequence):
                # LONGTERM handle list conversion elsewhere?
                pitch_material = list(pitch_material)
                for i in range(len(pitch_material)):
                    _replace(pitch_material, i)
            setattr(er, pitch_material_name, pitch_material)


def preprocess_temper_pitch_materials(er):
    """Tempers pitch materials as necessary.
    """

    for pitch_material_name in PITCH_MATERIAL_LISTS:
        pitch_material = getattr(er, pitch_material_name)
        if pitch_material is None:
            continue
        setattr(
            er,
            pitch_material_name,
            er_tuning.temper_pitch_materials(
                pitch_material, er.tet, integers_in_12_tet=er.integers_in_12_tet
            ),
        )

    er.cumulative_max_transpose_interval = er_tuning.temper_pitch_materials(
        er.cumulative_max_transpose_interval,
        er.tet,
        integers_in_12_tet=er.integers_in_12_tet,
    )

    # If limit_intervals are <= 0, they are specific intervals and must be
    # processed as follows:
    for interval_list in (
        er.max_interval,
        er.max_interval_for_non_chord_tones,
        er.min_interval,
        er.min_interval_for_non_chord_tones,
    ):
        if interval_list is None:
            continue
        for i in range(  # pylint: disable=consider-using-enumerate
            len(interval_list)
        ):
            if interval_list[i] <= 0:
                interval_list[i] = er_tuning.temper_pitch_materials(
                    (interval_list[i]), tet=er.tet
                )

    er.extend_bass_range_for_foots = er_tuning.temper_pitch_materials(
        er.extend_bass_range_for_foots, tet=er.tet
    )


def rhythmic_values_to_fractions(er):
    to_fractions = [
        "pattern_len",
        "rhythm_len",
        "harmony_len",
        "transpose_len",
        "attack_subdivision",
        "sub_subdivisions",
        "dur_subdivision",
        "obligatory_attacks",
        "obligatory_attacks_modulo",
        "length_choir_segments",
        "length_choir_loop",
        "chord_tone_before_rests",
        "min_dur_for_cons_treatment",
    ]

    for prop in to_fractions:
        if getattr(er, prop) is None:
            continue
        setattr(er, prop, er_misc_funcs.convert_to_fractions(getattr(er, prop)))


def ensure_lists_or_tuples(er):
    def _ensure_list_of_iterables(in_iter):
        try:
            iter(in_iter[0])
            return in_iter
        except (TypeError, IndexError):
            try:
                iter(in_iter)
                return [in_iter]
            except TypeError:
                # MAYBE make this function recursive, although I doubt
                #   I'l need deeper lists
                return [[in_iter,]]

    to_list = [
        "harmony_len",
        "rhythm_len",
        "pitch_loop",
        "hard_pitch_loop",
        "allow_voice_crossings",
        "pattern_len",
        "transpose_len",
        "transpose_intervals",
        "min_dur_for_cons_treatment",
        "chord_tones_no_diss_treatment",
        "max_interval",
        "max_interval_for_non_chord_tones",
        "min_interval",
        "min_interval_for_non_chord_tones",
        "max_alternations",
        "vary_rhythm_consistently",
        "num_cont_rhythm_vars",
        "cont_var_increment",
        "interval_cycle",
        "force_chord_tone",
        "tempo",
        "tempo_len",
    ]
    for attr in to_list:
        val = getattr(er, attr)
        if val is None:
            continue
        if not isinstance(val, typing.Sequence) or isinstance(val, str):
            setattr(er, attr, [val])

    to_list_of_iters = [
        "hard_bounds",
        "scales",
        "chords",
        "obligatory_attacks",
        "sub_subdivisions",
        "consonance_modulo",
        "forbidden_interval_modulo",
    ]

    for prop in to_list_of_iters:
        setattr(er, prop, _ensure_list_of_iterables(getattr(er, prop)))


def guess_time_sig(er):
    temp_time_signature = max(er.pattern_len + [sum(er.harmony_len),])
    i = 0
    numer = temp_time_signature
    while numer % 1 != 0:
        i += 1
        numer = temp_time_signature * 2 ** i
        if i == 8:

            class TimeSigError(Exception):
                pass

            raise TimeSigError(
                f"No time signature denominator below {4 * 2**i}"
            )

    denom = 4 * 2 ** i

    for i in range(2, int(numer) + 1):
        if numer % i == 0:
            numer = i
            break

    return (numer, denom)


def fill_list(in_list, num_voices):
    """If a list is shorter than the number of voices, populate it as
    necessary.

    Simply indexing using mod arithmetic would largely obviate the need
    to do this but there are some difficult cases due to rhythmic unison
    settings.
    """

    original_len = len(in_list)
    i = original_len
    while len(in_list) < num_voices:
        in_list.append(in_list[i % original_len])
        i += 1


def process_np_arrays(er):
    def _np_array_to_list(item):
        if isinstance(item, np.ndarray):
            out = []
            for sub_item in item:
                out.append(_np_array_to_list(sub_item))
            return out
        try:
            iter(item)
            iterable = True
        except TypeError:
            iterable = False
        if (
            iterable
            and not isinstance(item, dict)
            and not isinstance(item, str)
        ):
            out = []
            for sub_item in item:
                out.append(_np_array_to_list(sub_item))
            return out
        return item

    for setting, value in vars(er).items():
        setattr(er, setting, _np_array_to_list(value))


def process_choir_settings(er):
    """Prepares the choir settings."""
    # LONGTERM check if midi programs are defined in midi player? (To avoid
    #   tracks that mysteriously don't play back.)
    if not er.choirs:
        raise SettingsError("'choirs' cannot be empty")
    if not er.randomly_distribute_between_choirs:
        if not er.choir_assignments:
            er.choir_assignments = [
                i % len(er.choirs) for i in range(er.num_voices)
            ]
        if max(er.choir_assignments) > len(er.choirs) - 1:
            raise SettingsError(
                "'choir_assignments' assigns a voice to choir "
                f"{max(er.choir_assignments)}, but the "
                f"maximum index for 'choirs' is {len(er.choirs) - 1}"
            )
        er.num_choirs = len(set(er.choir_assignments))
        er.choir_order = [
            er.choir_assignments,
        ]
    else:
        er.num_choirs = len(er.choirs)
        if er.length_choir_segments < 0:
            er.choir_order = er_choirs.order_choirs(er, max_len=1)
        else:
            if er.length_choir_loop <= 0:
                warn_if_loop_too_short = False
                num_choir_segments = er.total_len / er.length_choir_segments
            else:
                warn_if_loop_too_short = True
                num_choir_segments = (
                    er.length_choir_loop / er.length_choir_segments
                )
                if num_choir_segments % 1 != 0:
                    warnings.warn(
                        f"\n'length_choir_loop' ({er.length_choir_loop}) / "
                        "'length_choir_segments' "
                        f"({er.length_choir_segments}) "
                        "is not a whole number. Rounding..."
                    )
            num_choir_segments = round(num_choir_segments)
            er.choir_order = er_choirs.order_choirs(
                er,
                max_len=num_choir_segments,
                warn_if_loop_too_short=warn_if_loop_too_short,
            )

    def _get_choir(choir):
        if isinstance(choir, int):
            return choir
        try:
            return getattr(er_constants, choir)
        except AttributeError:
            raise ValueError(  # pylint: disable=raise-missing-from
                f"{choir} is not an implemented choir constant."
            )
            # TODO see documentation for more help

    er.choir_programs = []
    for choir_i in range(er.num_choirs):
        # Why are both choir_programs and choirs necessary?
        choir = er.choirs[choir_i]
        if isinstance(choir, (int, str)):
            er.choir_programs.append(_get_choir(choir))
        else:
            raise NotImplementedError(
                "'choirs' must be integers or strings defined in "
                "er_constants.py"
            )
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

    er.num_choir_programs = len(er.choir_programs)


def process_parallel_motion(er):
    """Prepares parallel motion settings.

    Prepares the dictionaries er.force_parallel_motion and
    er.parallel_motion_followers.
    """

    class ParallelMotionInfo:
        def __init__(self, leader_i, motion_type):
            self.leader_i = leader_i
            # LONGTERM implement "global" parallel motion
            # (that's why this translation to a string is here, so eventually
            # force_parallel_motion in ERSettings can be specified by a
            # string with minimum fuss)
            self.motion_type = "within_harmonies" if motion_type else "false"

    if isinstance(er.force_parallel_motion, bool):
        er.force_parallel_motion = {
            tuple(er.voice_order): (
                "within_harmonies" if er.force_parallel_motion else "false"
            )
        }

    er.parallel_motion_leaders = {}
    er.parallel_motion_followers = {}
    for voice_tuple, motion_type in er.force_parallel_motion.items():
        if motion_type == "false":
            continue
        voices = list(voice_tuple)
        leader_i = voices.pop(0)
        er.parallel_motion_leaders[leader_i] = voices[:]
        while voices:
            follower_i = voices.pop(0)
            er.parallel_motion_followers[follower_i] = ParallelMotionInfo(
                leader_i, motion_type
            )


def fill_rhythm_lists_by_voice(er):
    """Adds voices to each list to bring it up to the number of voices.

    For the most part this just enacts would we could otherwise be done
    with modular arithmetic (e.g., pattern_len[voice_i % len(pattern_len]),
    but doing it this way avoids certain complications with rhythmic unison
    parts.
    """

    # LONGTERM make this more sensible!
    er.rhythm_lists_by_voice = [
        er.pattern_len,
        er.rhythm_len,
        er.attack_density,
        er.dur_density,
        er.attack_subdivision,
        er.dur_subdivision,
        er.min_dur,
        er.obligatory_attacks,
        er.obligatory_attacks_modulo,
        er.comma_position,
    ]

    for list_to_fill in er.rhythm_lists_by_voice:
        fill_list(list_to_fill, er.num_voices)


def chord_tone_and_foot_toggle(er):
    if not er.chord_tone_and_foot_disable:
        return

    er.chord_tone_selection = False
    er.chord_tones_no_diss_treatment = [False for i in range(er.num_voices)]
    er.force_chord_tone = ["none" for i in range(er.num_voices)]
    er.force_foot_in_bass = "none"
    er.max_interval_for_non_chord_tones = er.max_interval
    er.min_interval_for_non_chord_tones = er.max_interval
    er.voice_lead_chord_tones = False
    er.preserve_foot_in_bass = "none"
    er.extend_bass_range_for_foots = 0


def rhythm_preprocessing(er):
    def _rhythmic_relations_process(in_list):
        unaccounted_for_voices = list(range(er.num_voices))
        for group in in_list:
            for voice in group:
                try:
                    unaccounted_for_voices.remove(voice)
                except ValueError:
                    pass
        if unaccounted_for_voices:
            for voice in unaccounted_for_voices:
                in_list.append((voice,))

    def _rhythmic_relations_dict_process(in_list):
        out_dict = {}
        for group in in_list:
            leader = group[0]
            for follower in group[1:]:
                out_dict[follower] = leader
        return out_dict

    def _hocketing_dict_process(in_list):
        out_dict = {}
        for group in in_list:
            for follower_i, follower in enumerate(group[1:]):
                follower_i += 1
                out_dict[follower] = [group[i] for i in range(follower_i)]
        return out_dict

    def _num_notes(voice_i):

        if voice_i in er.rhythmic_unison_followers:
            leader_i = er.rhythmic_unison_followers[voice_i]
            er.num_notes[voice_i] = er.num_notes[leader_i]
            return
        rhythm_len = er.rhythm_len[voice_i]
        density = er.attack_density[voice_i]
        attack_div = er.attack_subdivision[voice_i]

        len_sub_subdiv = (
            len(er.sub_subdiv_props[voice_i])
            if er.cont_rhythms == "none"
            else 1
        )
        num_div = int(rhythm_len / attack_div * len_sub_subdiv)
        if isinstance(density, int):
            if density > num_div:
                print(
                    f"Notice: voice {voice_i} attack density of {density} "
                    f"is greater than {num_div}, the number of divisions.  "
                    f"Reducing to {num_div}."
                )
            num_notes = min(density, num_div)
        else:
            # if isinstance(density, float):
            num_notes = min(round(density * num_div), num_div)
        er.num_notes[voice_i] = max(
            num_notes, 1, len(er.obligatory_attacks[voice_i])
        )

    if er.rhythms_specified_in_midi:
        return
    # LONGTERM warning if er.rhythmic_unison and er.rhythmic_quasi_unison conflict
    if isinstance(er.rhythmic_quasi_unison, typing.Sequence):
        er.rhythmic_quasi_unison = er_misc_funcs.remove_non_existing_voices(
            er.rhythmic_quasi_unison, er.num_voices, "rhythmic_quasi_unison"
        )
        _rhythmic_relations_process(er.rhythmic_quasi_unison)
    elif er.rhythmic_quasi_unison and not er.rhythmic_unison:
        er.rhythmic_quasi_unison = [tuple(range(er.num_voices))]
    else:
        er.rhythmic_quasi_unison = []

    er.rhythmic_quasi_unison_followers = _rhythmic_relations_dict_process(
        er.rhythmic_quasi_unison
    )

    if isinstance(er.hocketing, typing.Sequence):
        er.hocketing = er_misc_funcs.remove_non_existing_voices(
            er.hocketing, er.num_voices, "hocketing"
        )
        _rhythmic_relations_process(er.hocketing)
    elif er.hocketing and not er.rhythmic_unison:
        er.hocketing = [tuple(range(er.num_voices))]
    else:
        er.hocketing = []

    er.hocketing_followers = _hocketing_dict_process(er.hocketing)

    if isinstance(er.rhythmic_unison, typing.Sequence):
        er.rhythmic_unison = er_misc_funcs.remove_non_existing_voices(
            er.rhythmic_unison, er.num_voices, "rhythmic_unison"
        )
        _rhythmic_relations_process(er.rhythmic_unison)
    elif er.rhythmic_unison:
        er.rhythmic_unison = [tuple(range(er.num_voices))]
    else:
        er.rhythmic_unison = []

    for group in er.rhythmic_unison:
        leader = group[0]
        for follower in group[1:]:
            for list_by_voice in er.rhythm_lists_by_voice:
                list_by_voice[follower] = list_by_voice[leader]

    er.rhythmic_unison_followers = _rhythmic_relations_dict_process(
        er.rhythmic_unison
    )

    er.num_notes = [None for i in range(er.num_voices)]
    for voice_i in range(er.num_voices):
        _num_notes(voice_i)


def process_pattern_voice_leading_order(er):
    """Adds er.pattern_voice_leading_order to ERSettings object.
    """

    # QUESTION put parallel voices immediately after their leader in voice
    #       order? or put them after all other voices? or setting to control
    #       this?

    er.pattern_voice_leading_order = []

    if er.truncate_patterns:
        truncate_len = max(er.pattern_len)
    voice_offset = 0
    for voice_i in er.voice_order:
        pattern_i = 0
        start_time = 0
        pattern_len = er.pattern_len[voice_i]
        if er.truncate_patterns:
            next_truncate = truncate_len
            n_since_prev_pattern = math.ceil(truncate_len / pattern_len)
        else:
            n_since_prev_pattern = 1
        while start_time < er.super_pattern_len:
            end_time = start_time + pattern_len
            if er.truncate_patterns:
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
                prev_item = er.pattern_voice_leading_order[
                    prev_pattern_i + voice_offset
                ]
            er.pattern_voice_leading_order.append(
                er_voice_leadings.VoiceLeadingOrderItem(
                    voice_i, start_time, end_time, prev_item=prev_item,
                )
            )
            start_time = end_time
            pattern_i += 1
        voice_offset += pattern_i

    er.pattern_voice_leading_order.sort(key=lambda x: x.end_time, reverse=True)
    er.pattern_voice_leading_order.sort(key=lambda x: x.start_time)


def num_cont_vars(er):
    new_num_vars = []
    for voice_i in range(er.num_voices):
        num_cont_rhythm_vars, pattern_len = er.get(
            voice_i, "num_cont_rhythm_vars", "pattern_len"
        )
        if num_cont_rhythm_vars < 0:
            num_cont_rhythm_vars = math.ceil(er.total_len / pattern_len)
        new_num_vars.append(num_cont_rhythm_vars)
    er.num_cont_rhythm_vars = new_num_vars


def cum_mod_lists(er):
    cum_mod_params = [
        "consonance_modulo",
        "forbidden_interval_modulo",
    ]

    for param in cum_mod_params:
        for list_i, list_ in enumerate(getattr(er, param)):
            getattr(er, param)[list_i] = [
                sum(list_[: i + 1]) for i in range(len(list_))
            ]


def read_in_settings(settings_input, settings_class):
    def _merge(dict1, dict2):
        for key, val in dict2.items():
            if (
                isinstance(val, dict)
                and key in dict1
                and isinstance(dict1[key], dict)
            ):
                _merge(dict1[key], val)
                dict2[key] = dict1[key]
        dict1.update(dict2)

    if settings_input is None:
        settings_input = {}
    if isinstance(settings_input, dict):
        return settings_class(**settings_input)
    merged_dict = {}
    for user_settings_path in settings_input:
        print(f"Reading settings from {user_settings_path}")
        with open(user_settings_path, "r", encoding="utf-8") as inf:
            user_settings = eval(inf.read(), vars(er_constants))
        _merge(merged_dict, user_settings)
    return settings_class(**merged_dict)


def preprocess_settings(
    user_settings, script_dir=SCRIPT_DIR, random_settings=False, seed=None
):

    er = read_in_settings(user_settings, er_settings.ERSettings)
    if seed is not None:
        er.seed = seed
    er.seed = er_misc_funcs.set_seed(er.seed)

    if er.output_path.startswith("EFFRHY/"):
        er.output_path = os.path.join(
            script_dir, er.output_path.replace("EFFRHY/", "", 1)
        )

    dir_name = os.path.dirname(er.output_path)
    if dir_name and not os.path.exists(dir_name):
        os.makedirs(dir_name)
    if dir_name == er.output_path.rstrip(os.path.sep):
        if user_settings is None:
            er.output_path = os.path.join(er.output_path, "effrhy.mid")
        else:
            er.output_path = os.path.join(
                er.output_path,
                os.path.splitext(os.path.basename(user_settings[-1]))[0]
                + ".mid",
            )

    if not er.overwrite and os.path.exists(er.output_path):
        er.output_path = er_misc_funcs.increment_fname(er.output_path)

    if er.max_super_pattern_len is None:
        er.max_super_pattern_len = (
            er_settings.MAX_SUPER_PATTERN_LEN_RANDOM
            if random_settings
            else er_settings.MAX_SUPER_PATTERN_LEN
        )

    if random_settings:
        randomize = er_randomize.ERRandomize(er)
        randomize.apply(er)
        # we re-set the seed in the hopes that the music will be reproducible
        er_misc_funcs.set_seed(er.seed, print_out=False)

    if er.max_interval_for_non_chord_tones == "take_from_max_interval":
        er.max_interval_for_non_chord_tones = er.max_interval
    if er.min_interval_for_non_chord_tones == "take_from_min_interval":
        er.min_interval_for_non_chord_tones = er.min_interval

    process_np_arrays(er)

    ensure_lists_or_tuples(er)

    if er.scales_and_chords_specified_in_midi is not None:
        (
            er.scales,
            er.chords,
            er.foot_pcs,
        ) = er_midi.get_scales_and_chords_from_midi(
            er.scales_and_chords_specified_in_midi
        )

    # Convert rhythmic parameters to fractions to avoid any float
    # weirdness:

    rhythmic_values_to_fractions(er)

    er.len_to_force_chord_tone = math.log2(
        er.len_to_force_chord_tone / er.scale_chord_tone_neutral_dur
    )

    ###################################################################
    # Process pcsets (scales, chords, etc.).

    # Temper pitch materials:

    replace_pitch_constants(er)
    preprocess_temper_pitch_materials(er)

    # If foot_pcs are not specified, generate them randomly
    if not er.foot_pcs:
        if er.num_harmonies is None:
            er.num_harmonies = er_settings.DEFAULT_NUM_HARMONIES
        if er.num_harmonies <= 0:

            class KeyNotesError(Exception):
                pass

            raise KeyNotesError("num_harmonies <= 0 and no key notes specified")
        er.foot_pcs = [
            random.randrange(0, er.tet) for i in range(er.num_harmonies)
        ]
    elif er.num_harmonies is None:
        er.num_harmonies = len(er.foot_pcs)
    elif len(er.foot_pcs) < er.num_harmonies:
        while len(er.foot_pcs) < er.num_harmonies:
            er.foot_pcs.extend(
                er.foot_pcs[: er.num_harmonies - len(er.foot_pcs)]
            )

    # if er.num_harmonies <= 0:
    #     er.num_harmonies = len(er.foot_pcs)

    # if (er.interval_cycle and er.interval_cycle[0] # not sure why er.interval_cycle[0] condition
    if er.interval_cycle and not er.scales_and_chords_specified_in_midi:
        temp_foot_pcs = []
        interval_i = 0
        temp_foot_pcs.append(er.foot_pcs[0])
        while len(temp_foot_pcs) < er.num_harmonies:
            interval = er.get(interval_i, "interval_cycle")
            temp_foot_pcs.append(temp_foot_pcs[-1] + interval)
            interval_i += 1
        er.foot_pcs = temp_foot_pcs

    er.foot_pcs = [foot_pc % er.tet for foot_pc in er.foot_pcs]

    if len(er.foot_pcs) > er.num_harmonies:
        er.foot_pcs = er.foot_pcs[: er.num_harmonies]

    # Truncate scales and foot_pcs if necessary
    if er.num_harmonies:
        if er.num_harmonies < len(er.scales):
            er.scales = er.scales[: er.num_harmonies]
        if er.num_harmonies < len(er.foot_pcs):
            er.foot_pcs = er.foot_pcs[: er.num_harmonies]

    er.pc_chords = []
    er.pc_scales = []

    for scs, pcsets in [(er.chords, er.pc_chords), (er.scales, er.pc_scales)]:
        for i, foot_pc in enumerate(er.foot_pcs):
            set_class = scs[i % len(scs)]
            pcsets.append([(pc + foot_pc) % er.tet for pc in set_class])

    # Check to ensure chords and scales are consistent.

    for chord_i, chord in enumerate(er.pc_chords):
        for pitch_class in chord:
            if pitch_class not in er.get(chord_i, "pc_scales"):

                class InconsistentChordsAndScalesError(Exception):
                    pass

                raise InconsistentChordsAndScalesError(
                    "pitch-class {} in chord {} but not in scale {}!"
                    "".format(pitch_class, chord_i, chord_i % len(er.pc_scales))
                )

    # Calculate augmented triad, if necessary

    if er.exclude_augmented_triad:
        just_augmented_triad = np.array([1.0, 5 / 4, (5 / 4) ** 2])
        er.exclude_augmented_triad = er_tuning.temper_pitch_materials(
            just_augmented_triad, er.tet
        )

    er.scales = []
    for pc_scale in er.pc_scales:
        er.scales.append(
            sorted([i + j * er.tet for i in pc_scale for j in range(12)])
        )

    er.prohibit_parallels = [
        interval % er.tet for interval in er.prohibit_parallels
    ]

    ###################################################################
    # Process harmony and pattern lengths, etc.

    er.length_of_all_harmonies = (
        sum(er.harmony_len) / len(er.harmony_len) * er.num_harmonies
    )

    if not er.pitch_loop:
        er.pitch_loop = [
            0,
        ]
    er.pitch_loop_complete = []
    for pitch_loop in er.pitch_loop:
        if pitch_loop:
            er.pitch_loop_complete.append(False)
        else:
            er.pitch_loop_complete.append(None)

    for pattern_i in range(len(er.pattern_len)):
        if er.pattern_len[pattern_i] <= 0:
            er.pattern_len[pattern_i] = er.length_of_all_harmonies

    if er.rhythm_len is None:
        er.rhythm_len = er.pattern_len
    else:
        i = 0
        while len(er.rhythm_len) < len(er.pattern_len):
            er.rhythm_len.append(er.pattern_len[i])
            i += 1
        while len(er.pattern_len) < len(er.rhythm_len):
            er.pattern_len.append(er.pattern_len[i % len(er.pattern_len)])
            i += 1
        for i, pattern_length in enumerate(er.pattern_len):
            if er.rhythm_len[i] > pattern_length or er.rhythm_len[i] == 0:
                er.rhythm_len[i] = pattern_length
    try:
        max_super_pattern_len = (
            er.max_super_pattern_len
            if er.max_super_pattern_len
            else er_settings.MAX_SUPER_PATTERN_LEN
        )
        # if er.truncate_patterns:
        #     er.super_pattern_len = er_misc_funcs.lcm(
        #         (max(er.pattern_len), er.length_of_all_harmonies),
        #         max_n=max_super_pattern_len,
        #     )
        # else:
        er.super_pattern_len = er_misc_funcs.lcm(
            ([max(er.pattern_len)] if er.truncate_patterns else er.pattern_len)
            + [er.length_of_all_harmonies,],
            max_n=max_super_pattern_len,
        )
    except er_misc_funcs.LCMError as exc:
        er.super_pattern_len = max_super_pattern_len
        print(
            f"Notice: {exc} Reducing `super_pattern_len` to "
            f"{max_super_pattern_len}"
        )

    if (
        er.max_super_pattern_len
        and er.super_pattern_len > er.max_super_pattern_len
    ):
        er.super_pattern_len = er.max_super_pattern_len

    er.total_len = er.super_pattern_len * er.num_reps_super_pattern

    if er.time_sig is None:
        er.time_sig = guess_time_sig(er)

    ###################################################################
    # Process rhythmic settings.

    def _process_rhythm_list(rhythm_list, replace_negative_with_random=False):
        if not isinstance(rhythm_list, typing.Sequence) or isinstance(
            rhythm_list, str
        ):
            item = rhythm_list
            if replace_negative_with_random and item < 0:
                rhythm_list = [random.random() for i in range(er.num_voices)]
            else:
                rhythm_list = [item for i in range(er.num_voices)]
        elif replace_negative_with_random:
            for i in range(  # pylint: disable=consider-using-enumerate
                len(rhythm_list)
            ):
                if rhythm_list[i] < 0:
                    rhythm_list[i] = random.random()

        return rhythm_list

    def _prepare_sub_subdivisions(er):
        er.sub_subdiv_props = []
        for voice_i in range(er.num_voices):
            subs, attack_div = er.get(
                voice_i, "sub_subdivisions", "attack_subdivision"
            )
            er.sub_subdiv_props.append(
                [
                    fractions.Fraction(sub, sum(subs)) * attack_div
                    for sub in subs
                ]
            )

    def _min_dur_process(er):
        if isinstance(er.min_dur, typing.Sequence):
            for min_dur_i, min_dur in enumerate(er.min_dur):
                if min_dur <= 0:
                    er.min_dur[min_dur_i] = er.get(
                        min_dur_i, "attack_subdivision"
                    )
                # QUESTION what is this? Is it for continuous rhythms?
                # if isinstance(min_dur, int):
                # er.min_dur[min_dur_i] = er.tempo[0] / 60 * (0.001 * min_dur)
        elif er.min_dur <= 0:
            er.min_dur = er.get(0, "attack_subdivision")
            # QUESTION what is this? Is it for continuous rhythms?
            # er.min_dur = er.tempo[0] / 60 * (0.001 * er.min_dur)
        er.min_dur = er_misc_funcs.convert_to_fractions(er.min_dur)

    er.attack_density = _process_rhythm_list(
        er.attack_density, replace_negative_with_random=True
    )
    er.dur_density = _process_rhythm_list(
        er.dur_density, replace_negative_with_random=True
    )
    er.attack_subdivision = _process_rhythm_list(er.attack_subdivision)
    _prepare_sub_subdivisions(er)
    er.dur_subdivision = _process_rhythm_list(er.dur_subdivision)
    _min_dur_process(er)
    er.min_dur = _process_rhythm_list(er.min_dur)
    er.obligatory_attacks_modulo = _process_rhythm_list(
        er.obligatory_attacks_modulo
    )
    if not er.comma_position:
        er.comma_position = "end"
    er.comma_position = _process_rhythm_list(er.comma_position)
    er.chord_tone_before_rests = _process_rhythm_list(
        er.chord_tone_before_rests
    )

    for sub_list_i, sub_list in enumerate(er.obligatory_attacks):
        beats = sub_list.copy()
        for beat in beats:
            for i in range(
                1,
                math.ceil(
                    er.get(sub_list_i, "pattern_len")
                    / er.get(sub_list_i, "obligatory_attacks_modulo")
                ),
            ):
                sub_list.append(
                    beat + i * er.get(sub_list_i, "obligatory_attacks_modulo")
                )

    er.attack_subdivision_gcd = er_misc_funcs.gcd_from_list(
        er.attack_subdivision,
        er.sub_subdiv_props,  # pylint: disable=no-member
        er.pattern_len,
        er.harmony_len,
        er.rhythm_len,
        er.obligatory_attacks,
        er.obligatory_attacks_modulo,
    )
    er.dur_gcd = er_misc_funcs.gcd_from_list(
        er.attack_subdivision_gcd, er.dur_subdivision, er.min_dur
    )

    # Continuous rhythm settings

    num_cont_vars(er)

    ###################################################################
    # Process consonances.

    if er.invert_consonances:
        er.consonances = [i for i in range(er.tet) if i not in er.consonances]

    ###################################################################
    # Process choir settings.

    process_choir_settings(er)

    ###################################################################
    # Process misc other settings.

    if er.existing_voices:
        if not er.existing_voices_max_denominator:
            er.existing_voices_max_denominator = 8192
        er.existing_score = er_midi.read_midi_to_internal_data(
            er.existing_voices,
            tet=er.tet,
            time_sig=er.time_sig,
            track_num_offset=1 + er.num_voices,
            max_denominator=er.existing_voices_max_denominator,
        )
        er.existing_voices_indices = [
            i + 1 + er.num_voices for i in range(er.existing_score.num_voices)
        ]
        er.existing_score.displace_passage(er.existing_voices_offset)
    else:
        er.existing_score = None
        er.existing_voices_indices = []

    er.control_log_base = 10 ** (
        er.prefer_small_melodic_intervals_coefficient * 0.1
    )

    def _return_voice_order(er):
        out = list(range(er.num_voices))
        if er.voice_order_str != "reverse":
            return out
        out.reverse()
        return out

    er.voice_order = _return_voice_order(er)

    process_parallel_motion(er)

    if er.tet != 12:
        er.pitch_bend_tuple_dict = er_tuning.return_pitch_bend_tuple_dict(
            er.tet
        )

    fill_rhythm_lists_by_voice(er)

    chord_tone_and_foot_toggle(er)

    rhythm_preprocessing(er)

    process_pattern_voice_leading_order(er)

    notify_user_of_unusual_settings(er)

    prepare_warnings(er)

    cum_mod_lists(er)

    check_min_dur(er)

    # There are a few calls to random in the preceding pre-processing functions,
    # so we re-set the seed once more in the hopes of making files produced
    # with the --random flag reproducible, even if the above code changes
    # slightly
    er_misc_funcs.set_seed(er.seed, print_out=False)

    er.build_status_printer = er_interface.BuildStatusPrinter(er)

    return er


# Constants for accessing er.pattern_voice_leading_order

VOICE_I = 0
PATTERN_START = 1
PATTERN_END = 2
