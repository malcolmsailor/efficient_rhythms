"""This script performs preprocessing on various settings to prepare them for
use.
"""

import collections
import fractions
import math
import numbers
import random
import warnings

import numpy as np

import er_choirs
import er_midi
import er_misc_funcs
import er_randomize
import er_settings
import er_tuning


class SettingsError(Exception):
    pass


def notify_user_of_unusual_settings(er):
    def print_(text):
        print(er_misc_funcs.add_line_breaks(text))

    # TODO update these messages so as not to say "er."
    if er.len_to_force_chord_tone == 0 and er.scale_chord_tone_prob_by_dur:
        raise SettingsError(
            "If er.scale_chord_tone_prob_by_dur is True, then "
            "er.len_to_force_chord_tone must be non-zero."
        )
    if er.scale_short_chord_tones_down and er.force_non_chord_tones:
        print_(
            "Warning: er.scale_short_chord_tones_down and "
            "er.force_non_chord_tones are both true. Strange results may occur, "
            "particularly if there are many short notes."
        )
    if (
        er.chord_tones_sync_attack_in_all_voices
        and er.scale_chord_tone_prob_by_dur
    ):
        print(
            "Notice: er.chord_tones_sync_attack_in_all_voices and "
            "er.scale_chord_tone_prob_by_dur are both true. Long notes in some "
            "voices may be non chord tones."
        )
    if er.chord_tone_selection != er.voice_lead_chord_tones:
        print_(
            f"Notice: er.chord_tone_selection is {er.chord_tone_selection} "
            f"and er.voice_lead_chord_tones is {er.voice_lead_chord_tones}"
        )

    if er.logic_type_pitch_bend:
        if er.tet == 12:
            print("Notice: er.logic_type_pitch_bend is True and 12-tet.")
        else:
            if not er.voices_separate_tracks and er.num_voices > 1:
                warnings.warn(
                    "er.logic_type_pitch_bend and "
                    "not er.voices_separate_tracks"
                )
            if not er.choirs_separate_tracks and er.num_choirs > 1:
                warnings.warn(
                    "er.logic_type_pitch_bend and "
                    "not er.choirs_separate_tracks"
                )
            if er.choirs_separate_channels and er.num_choirs > 1:
                warnings.warn(
                    "er.logic_type_pitch_bend and "
                    "er.choirs_separate_channels\n"
                    "   Ignoring er.choirs_separate_channels..."
                )

    if er.parallel_voice_leading and er.vl_maintain_consonance:
        print_(
            "Notice: er.parallel_voice_leading is not compatible with "
            "checking voice-leadings for consonance. Ignoring "
            "er.vl_maintain_consonance"
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
                "one voice and er.chord_tone_selection is true. "
                "This is likely to lead to excess repeated notes."
            )
        )


def prepare_warnings(er):
    """Certain warnings should only occur once, even though the situation
    that provokes them may occur many times. This function initializes
    a dictionary for keeping track of this.
    """
    er.already_warned = {
        "force_root": collections.Counter(),
    }


def preprocess_temper_pitch_materials(er):
    """Tempers pitch materials as necessary.
    """

    pitch_material_lists = (
        er.scales,
        er.chords,
        er.root_pcs,
        er.interval_cycle,
        er.voice_ranges,
        er.consonances,
        er.consonant_chords,
        er.forbidden_interval_classes,
        er.prohibit_parallels,
        er.transpose_intervals,
        # CONSONANCES,
        # PERFECT_CONSONANCES,
        # IMPERFECT_CONSONANCES,
    )

    for pitch_material in pitch_material_lists:
        if pitch_material is None:
            continue
        er_tuning.temper_pitch_materials_in_place(
            pitch_material, er.tet, integers_in_12_tet=er.integers_in_12_tet
        )

    er.cumulative_max_transpose_interval = er_tuning.temper_pitch_materials(
        er.cumulative_max_transpose_interval,
        er.tet,
        integers_in_12_tet=er.integers_in_12_tet,
    )

    # If er.max_interval is < 0, it is a specific interval and must be
    # processed as follows:
    for interval_list in (
        er.max_interval,
        er.max_interval_for_non_chord_tones,
        er.min_interval,
        er.min_interval_for_non_chord_tones,
    ):
        for i in range(  # pylint: disable=consider-using-enumerate
            len(interval_list)
        ):
            if interval_list[i] < 0:
                # TODO why are there *two* minus signs? I think the second one
                #   may be in error
                interval_list[i] = -(
                    er_tuning.temper_pitch_materials(
                        -(interval_list[i]), tet=er.tet
                    )
                )

    er.extend_bass_range_for_roots = er_tuning.temper_pitch_materials(
        er.extend_bass_range_for_roots, tet=er.tet
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
        # "min_dur", # this is done sperately in "_min_dur_process()" below
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
        "num_vars",
        "cont_var_increment",
        "interval_cycle",
        "force_chord_tone",
        "tempo",
        "tempo_len",
    ]
    for prop in to_list:
        if getattr(er, prop) is None:
            continue
        if not isinstance(getattr(er, prop), (list, tuple)):
            setattr(er, prop, [getattr(er, prop)])

    to_list_of_iters = [
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

    # TODO this does not work at the moment!
    for setting, value in vars(er).items():
        setattr(er, setting, _np_array_to_list(value))
        # vars(er)[setting] = _np_array_to_list(value)


def process_choir_settings(er):
    """Prepares the choir settings."""
    if not er.choirs:
        raise SettingsError("er.choirs cannot be empty")
    if not er.randomly_distribute_between_choirs:
        if not er.choir_assignments:
            er.choir_assignments = [0 for _ in range(er.num_voices)]
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
                        f"\ner.length_choir_loop ({er.length_choir_loop}) / "
                        "er.length_choir_segments "
                        f"({er.length_choir_segments}) "
                        "is not a whole number. Rounding..."
                    )
            num_choir_segments = round(num_choir_segments)
            er.choir_order = er_choirs.order_choirs(
                er,
                max_len=num_choir_segments,
                warn_if_loop_too_short=warn_if_loop_too_short,
            )

    er.choir_programs = []
    for choir_i in range(er.num_choirs):
        choir = er.choirs[choir_i]
        if isinstance(choir, numbers.Number):
            er.choir_programs.append(choir)
        else:
            sub_choirs, split_points = choir
            if not isinstance(split_points, (list, tuple)):
                split_points = [
                    split_points,
                ]
            er.choirs[choir_i] = er_choirs.Choir(sub_choirs, split_points)
            er.choirs[choir_i].temper_split_points(
                er.tet, er.integers_in_12_tet
            )
            er.choir_programs += sub_choirs

    er.num_choir_programs = len(er.choir_programs)


def process_parallel_motion(er):
    """Prepares parallel motion settings.

    Prepares the dictionaries er.force_parallel_motion and
    er.parallel_motion_followers.
    """

    class ParallelMotionInfo:
        def __init__(self, leader_i, motion_type):
            self.leader_i = leader_i
            self.motion_type = motion_type

    if isinstance(er.force_parallel_motion, str):
        er.force_parallel_motion = {
            tuple(er.voice_order): er.force_parallel_motion
        }

    er.parallel_motion_leaders = {}
    er.parallel_motion_followers = {}
    for voice_tuple, motion_type in er.force_parallel_motion.items():
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

    # TODO make this more sensible!
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


def chord_tone_and_root_toggle(er):
    if not er.chord_tone_and_root_disable:
        return

    er.chord_tone_selection = False
    er.chord_tones_no_diss_treatment = [False for i in range(er.num_voices)]
    # er.force_chord_tone_at_global_start = "false"
    # er.force_chord_tone_at_start_of_each_harmony = "false"
    er.force_chord_tone = ["none" for i in range(er.num_voices)]
    er.force_root_in_bass = "none"
    er.max_interval_for_non_chord_tones = [0 for i in range(er.num_voices)]
    er.min_interval_for_non_chord_tones = [0 for i in range(er.num_voices)]
    er.voice_lead_chord_tones = False
    er.preserve_root_in_bass = "none"
    er.extend_bass_range_for_roots = 0


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
        sub_subdiv = er.sub_subdiv_props[voice_i]
        num_div = int(rhythm_len / attack_div * len(sub_subdiv))
        if isinstance(density, float):
            num_notes = min(round(density * num_div), num_div)
        elif isinstance(density, int):
            if density > num_div:
                print(
                    f"Notice: voice {voice_i} attack density of {density} "
                    f"is greater than {num_div}, the number of divisions.  "
                    f"Reducing to {num_div}."
                )
            num_notes = min(density, num_div)
        er.num_notes[voice_i] = num_notes

    if er.rhythms_specified_in_midi:
        return
    # TODO warning if er.rhythmic_unison and er.rhythmic_quasi_unison conflict
    if isinstance(er.rhythmic_quasi_unison, list):
        er.rhythmic_quasi_unison = er_misc_funcs.remove_non_existing_voices(
            er.rhythmic_quasi_unison, er.num_voices, "er.rhythmic_quasi_unison"
        )
        _rhythmic_relations_process(er.rhythmic_quasi_unison)
    elif er.rhythmic_quasi_unison and not er.rhythmic_unison:
        er.rhythmic_quasi_unison = [tuple(range(er.num_voices))]
    else:
        er.rhythmic_quasi_unison = []

    er.rhythmic_quasi_unison_followers = _rhythmic_relations_dict_process(
        er.rhythmic_quasi_unison
    )

    if isinstance(er.hocketing, list):
        er.hocketing = er_misc_funcs.remove_non_existing_voices(
            er.hocketing, er.num_voices, "er.hocketing"
        )
        _rhythmic_relations_process(er.hocketing)
    elif er.hocketing and not er.rhythmic_unison:
        er.hocketing = [tuple(range(er.num_voices))]
    else:
        er.hocketing = []

    er.hocketing_followers = _hocketing_dict_process(er.hocketing)

    if isinstance(er.rhythmic_unison, list):
        er.rhythmic_unison = er_misc_funcs.remove_non_existing_voices(
            er.rhythmic_unison, er.num_voices, "er.rhythmic_unison"
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

    er.pattern_voice_leading_order is used to voice-lead each pattern. It
    consists of tuples of form (voice_i, start_time, pattern_len),
    sorted by start_time, then by descending pattern_len, then by voice_i
    (following er.voice_order)

    After building the rhythms, I replace these tuples with 4-tuples of form
    (voice_i, start_time, pattern_len, (start_rhythm_i, end_rhythm_i)).
    (See er_rhythm.py)
    """

    # QUESTION put parallel voices immediately after their leader in voice
    #       order? or put them after all other voices? or setting to control
    #       this?

    class VoiceLeadingOrderItem:
        def __init__(
            self,
            voice_i,
            start_time,
            end_time,
            start_rhythm_i=None,
            end_rhythm_i=None,
        ):
            self.voice_i = voice_i
            self.start_time = start_time
            self.end_time = end_time
            self.start_rhythm_i = start_rhythm_i
            self.end_rhythm_i = end_rhythm_i

    er.pattern_voice_leading_order = []

    if er.truncate_patterns:
        truncate_len = max(er.pattern_len)

        for voice_i in er.voice_order:
            start_time = 0
            next_truncate = truncate_len
            pattern_len = er.pattern_len[voice_i]
            while start_time < er.super_pattern_len:
                if start_time == next_truncate:
                    next_truncate += truncate_len
                end_time = min(start_time + pattern_len, next_truncate)
                er.pattern_voice_leading_order.append(
                    VoiceLeadingOrderItem(voice_i, start_time, end_time)
                )
                start_time = end_time
    else:
        for voice_i in er.voice_order:
            start_time = 0
            pattern_len = er.pattern_len[voice_i]
            while start_time < er.super_pattern_len:
                end_time = start_time + pattern_len
                er.pattern_voice_leading_order.append(
                    VoiceLeadingOrderItem(voice_i, start_time, end_time)
                )
                start_time = end_time

    er.pattern_voice_leading_order.sort(key=lambda x: x.end_time, reverse=True)
    er.pattern_voice_leading_order.sort(key=lambda x: x.start_time)


def num_cont_vars(er):
    new_num_vars = []
    for voice_i in range(er.num_voices):
        num_vars, pattern_len = er.get(voice_i, "num_vars", "pattern_len")
        if num_vars < 0:
            num_vars = math.ceil(er.total_len / pattern_len)
        new_num_vars.append(num_vars)
    er.num_vars = new_num_vars


def cum_mod_lists(er):
    cum_mod_params = [
        "consonance_modulo",
        "forbidden_interval_modulo",
    ]

    for param in cum_mod_params:
        # for list_i, list_ in enumerate(vars(er)[param]):
        #     vars(er)[param][list_i] = [
        #         sum(list_[: i + 1]) for i in range(len(list_))
        #     ]
        for list_i, list_ in enumerate(getattr(er, param)):
            getattr(er, param)[list_i] = [
                sum(list_[: i + 1]) for i in range(len(list_))
            ]


def preprocess_settings(
    script_name, script_dir, random_settings, user_settings_path,
):

    fname_path, _ = er_misc_funcs.return_fname_path(script_name, script_dir)
    if user_settings_path is None:
        user_settings = {}
    else:
        print(f"Reading settings from {user_settings_path}")
        with open(user_settings_path, "r", encoding="utf-8") as inf:
            user_settings = eval(inf.read())
    er = er_settings.ERSettings(**user_settings)

    er.seed = er_misc_funcs.set_seed(er.seed)

    if random_settings:
        randomize = er_randomize.ERRandomize(er)
        randomize.apply(er)

    process_np_arrays(er)

    ensure_lists_or_tuples(er)

    if er.scales_and_chords_specified_in_midi is not None:
        (
            er.scales,
            er.chords,
            er.root_pcs,
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

    preprocess_temper_pitch_materials(er)

    # If root_pcs are not specified, generate them randomly
    if not er.root_pcs:
        if er.num_harmonies <= 0:

            class KeyNotesError(Exception):
                pass

            raise KeyNotesError("num_harmonies = 0 and no key notes specified")
        er.root_pcs = [
            random.randrange(0, er.tet) for i in range(er.num_harmonies)
        ]

    if er.num_harmonies < 0:  # TODO shouldn't this be <= 0?
        er.num_harmonies = len(er.root_pcs)

    # if (er.interval_cycle and er.interval_cycle[0] # not sure why er.interval_cycle[0] condition
    if er.interval_cycle and not er.scales_and_chords_specified_in_midi:
        temp_root_pcs = []
        interval_i = 0
        temp_root_pcs.append(er.root_pcs[0])
        while len(temp_root_pcs) < er.num_harmonies:
            interval = er.get(interval_i, "interval_cycle")
            temp_root_pcs.append(temp_root_pcs[-1] + interval)
            interval_i += 1
        er.root_pcs = temp_root_pcs

    er.root_pcs = [root_pc % er.tet for root_pc in er.root_pcs]

    if len(er.root_pcs) > er.num_harmonies:
        er.root_pcs = er.root_pcs[: er.num_harmonies]

    # Truncate scales and root_pcs if necessary
    if er.num_harmonies:
        if er.num_harmonies < len(er.scales):
            er.scales = er.scales[: er.num_harmonies]
        if er.num_harmonies < len(er.root_pcs):
            er.root_pcs = er.root_pcs[: er.num_harmonies]

    er.pc_chords = []
    er.pc_scales = []

    for scs, pcsets in [(er.chords, er.pc_chords), (er.scales, er.pc_scales)]:
        for i, root_pc in enumerate(er.root_pcs):
            set_class = scs[i % len(scs)]
            pcsets.append([(pc + root_pc) % er.tet for pc in set_class])

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
            if er.rhythm_len[i] > pattern_length:
                er.rhythm_len[i] = pattern_length

    if er.truncate_patterns:
        er.super_pattern_len = er_misc_funcs.lcm(
            [max(er.pattern_len), er.length_of_all_harmonies]
        )
    else:
        er.super_pattern_len = er_misc_funcs.lcm(
            er.pattern_len + [er.length_of_all_harmonies,]
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
        if not isinstance(rhythm_list, (list, tuple)):
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
        if isinstance(er.min_dur, (list, tuple)):
            for min_dur_i, min_dur in enumerate(er.min_dur):
                if isinstance(min_dur, int):
                    er.min_dur[min_dur_i] = er.tempo[0] / 60 * (0.001 * min_dur)
        else:
            er.min_dur = er.tempo[0] / 60 * (0.001 * er.min_dur)
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

    # If consonances list is empty, generate list of consonances from
    # consonances constants:
    # TODO delete
    # if not er.consonances:
    #     er.consonances = CONSONANCES

    # if er.no_imperfect_consonances:
    #     for octave in [j * er.tet for j in range(num_octaves_in_range)]:
    #         for consonance in IMPERFECT_CONSONANCES:
    #             try:
    #                 er.consonances.remove(octave + consonance)
    #             except ValueError:
    #                 continue

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

    er.control_log_base = 10 ** (er.control_coefficient * 0.1)

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

    chord_tone_and_root_toggle(er)

    rhythm_preprocessing(er)

    process_pattern_voice_leading_order(er)

    notify_user_of_unusual_settings(er)

    prepare_warnings(er)

    cum_mod_lists(er)

    return er, fname_path


# Constants

# TODO move to er_constants?
# CONSONANCES = [1.0, 3 / 2, 4 / 3, 5 / 4, 6 / 5, 8 / 5, 10 / 6]
# PERFECT_CONSONANCES = [1.0, 3 / 2, 4 / 3]
# IMPERFECT_CONSONANCES = [5 / 4, 6 / 5, 8 / 5, 10 / 6]

# Constants for accessing er.pattern_voice_leading_order

VOICE_I = 0
PATTERN_START = 1
PATTERN_END = 2
