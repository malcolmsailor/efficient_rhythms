"""Makes the actual music.
"""
import bisect
import copy
import itertools
import math
import random
import sys

import numpy as np

import er_constants
import er_exceptions
import er_make2
import er_misc_funcs
import er_notes
import er_rhythm
import er_vl_strict_and_flex


class PossibleNoteError(Exception):
    pass


class PossibleNote:
    """A class for storing the properties of a possible note.
    """

    def __init__(self, er, super_pattern, attack_i):
        self.attack_i = attack_i
        try:
            self.voice_i, self.attack_time = er.initial_pattern_order[attack_i]
        except IndexError:
            raise PossibleNoteError()  # pylint: disable=raise-missing-from
        self.voice = super_pattern.voices[self.voice_i]
        self.dur = er.rhythms[self.voice_i][self.attack_time]
        self.harmony_i = super_pattern.get_harmony_i(self.attack_time)


# it appears this function is never called
# TODO check whether this function should be called somewhere?
# def _force_root(er, super_pattern, poss_note):
#     root = get_root_to_force(er, poss_note)
#     if root is not None:
#         super_pattern.add_note(
#             poss_note.voice_i, root, poss_note.attack_time, poss_note.dur
#         )
#         return True
#     return False


def _repeat_pitch(super_pattern, poss_note):
    # voice = super_pattern.voices[poss_note.voice_i]
    harmony_start_time = super_pattern.get_harmony_times(
        poss_note.harmony_i
    ).start_time
    return er_make2.get_repeated_pitch(
        poss_note, min_attack_time=harmony_start_time
    )


def _pitch_loop(er, poss_note):

    loop_len = er.get(poss_note.voice_i, "pitch_loop")
    prev_n_pitches = poss_note.voice.get_prev_n_pitches(
        loop_len, poss_note.attack_time
    )
    pitch_to_loop = prev_n_pitches[0]

    if pitch_to_loop <= 0:
        return 0
    scale = er.get(poss_note.harmony_i, "scales")
    if pitch_to_loop not in scale:
        look_first = random.choice([1, -1])
        look_second = -1 * look_first
        i = 1
        while True:
            pitch_to_test = pitch_to_loop + look_first * i
            if (
                pitch_to_test in scale
                and len(set([pitch_to_test,] + prev_n_pitches[1:])) != 1
            ):
                pitch_to_loop = pitch_to_test
                break
            pitch_to_test = pitch_to_loop + look_second * i
            if (
                pitch_to_test in scale
                and len(set([pitch_to_test,] + prev_n_pitches[1:])) != 1
            ):
                pitch_to_loop = pitch_to_test
                break
            i += 1

    return pitch_to_loop


def _force_parallel_motion(er, super_pattern, poss_note):

    parallel_motion_info = er.parallel_motion_followers[poss_note.voice_i]
    leader_i = parallel_motion_info.leader_i
    motion_type = parallel_motion_info.motion_type

    leader = super_pattern.voices[leader_i]
    follower = super_pattern.voices[poss_note.voice_i]

    if poss_note.attack_time not in leader:
        return None

    harmony_start_time = super_pattern.get_harmony_times(
        poss_note.harmony_i
    ).start_time

    if motion_type == "within_harmonies":

        leader_prev_pitch, leader_pitch = leader.get_last_n_pitches(
            2,
            poss_note.attack_time,
            min_attack_time=harmony_start_time,
            stop_at_rest=True,
        )

        follower_prev_pitch = follower.get_prev_pitch(
            poss_note.attack_time,
            min_attack_time=harmony_start_time,
            stop_at_rest=True,
        )

        if leader_prev_pitch <= 0 or follower_prev_pitch <= 0:
            return None

        generic_interval = er_misc_funcs.get_generic_interval(
            er, poss_note.harmony_i, leader_pitch, leader_prev_pitch
        )
        follower_pitch = er_misc_funcs.apply_generic_interval(
            er, poss_note.harmony_i, generic_interval, follower_prev_pitch
        )

        return follower_pitch

    # LONGTERM I'm not sure whether "global" parallel motion of this
    #       type of parallel motion is coherent... mull this over!

    if motion_type == "global":
        raise NotImplementedError("Global parallel motion not yet implemented.")
    return None


def _check_other_voices_for_chord_tones(
    er, super_pattern, attack_time, prev_voices, harmony_i
):

    # This function assumes that the other voices are monophonic.

    for prev_voice_i in prev_voices:
        prev_voice = super_pattern.voices[prev_voice_i]
        if attack_time not in prev_voice:
            continue
        prev_note = prev_voice[attack_time][0]
        pc = prev_note.pitch % er.tet
        if pc in er.get(harmony_i, "pc_chords"):
            return True
    return False


def _get_n_since_chord_tone(er, super_pattern, attack_time, voice_i):
    voice = super_pattern.voices[voice_i]
    n = 0
    for note in reversed(voice):
        time = note.attack_time
        if time >= attack_time:
            continue
        if er_make2.check_if_chord_tone(
            er, super_pattern, note.attack_time, note.pitch
        ):
            return n
        n += 1

    # When constructing the first note, arbitrarily set n to 1.
    if n == 0:
        return 1
    return n


def _choose_whether_chord_tone(er, super_pattern, poss_note):
    def _chord_tone_probability():
        x = er.max_n_between_chord_tones
        if x == 0:
            return 1
        if er.chord_tone_prob_func == "quadratic":
            result = (n_since_chord_tone / x) ** (1 / 2)

        elif er.chord_tone_prob_func == "linear":
            result = n_since_chord_tone / x

        if result < 1 and er.scale_chord_tone_prob_by_dur:
            note_weight = math.log2(
                poss_note.dur / er.scale_chord_tone_neutral_dur
            )
            if note_weight > 0 or er.scale_short_chord_tones_down:
                prob_adj = (
                    note_weight - er.len_to_force_chord_tone
                ) / er.len_to_force_chord_tone + 1
                result += prob_adj * (1 - result)

        return max(
            0, result * (1 - er.min_prob_chord_tone) + er.min_prob_chord_tone
        )

    if 0 < er.len_to_force_chord_tone <= poss_note.dur:
        return True

    force_chord_tone = er.get(poss_note.voice_i, "force_chord_tone")

    if force_chord_tone != "none":
        if poss_note.attack_time == 0:
            return True
        if force_chord_tone == "global_first_note":
            prev_pitch = super_pattern.get_prev_pitch(
                poss_note.attack_time, poss_note.voice_i
            )
            if prev_pitch <= 0:
                return True
        else:
            harmony_start_time = super_pattern.get_harmony_times(
                poss_note.harmony_i
            ).start_time
            if (
                force_chord_tone == "first_beat"
                and poss_note.attack_time == harmony_start_time
            ):
                return True
            if force_chord_tone == "first_note":
                prev_pitch = super_pattern.get_prev_pitch(
                    poss_note.attack_time,
                    poss_note.voice_i,
                    min_attack_time=harmony_start_time,
                )
                if prev_pitch <= 0:
                    return True

    # Next, if er.chord_tone_selection is false, return false.
    if not er.chord_tone_selection:
        return False

    # Finally, apply remaining chord_tone settings.
    rest_dur = er.get(poss_note.voice_i, "chord_tone_before_rests")

    if rest_dur:
        mod_attack = (
            poss_note.attack_time
            % er.rhythms[poss_note.voice_i].total_rhythm_len
        )
        if er_rhythm.rest_before_next_note(
            er.rhythms[poss_note.voice_i], mod_attack, rest_dur
        ):
            return True

    if er.chord_tones_sync_attack_in_all_voices:
        prev_voices = er_misc_funcs.get_prev_voice_indices(
            super_pattern, poss_note.attack_time, poss_note.dur,
        )
        if prev_voices:
            if _check_other_voices_for_chord_tones(
                er,
                super_pattern,
                poss_note.attack_time,
                prev_voices,
                poss_note.harmony_i,
            ):
                return True
            # QUESTION should there be a "soft" version of chord tones
            # syncing in all voices? Where the absence of a chord tone
            # in other voices doesn't force the absence of a chord tone
            # in this voice? (Although non-chord tones are only forced
            # if er.force_non_chord_tones.) In that case one would probably
            # have to use only one voice as the "leader" to determine whether
            # to have chord_tones. (Although this may be effectively what
            # happens already.)
            return False

    n_since_chord_tone = _get_n_since_chord_tone(
        er, super_pattern, poss_note.attack_time, poss_note.voice_i
    )

    # LONGTERM chord tone probability influenced by metric position

    if random.random() < _chord_tone_probability():
        return True

    return False


# def check_for_voice_crossings(super_pattern, pitch, attack_time, dur, voice_i):
#     voices_above = [i for i in range(super_pattern.num_voices) if i > voice_i]
#     pitches_above = super_pattern.get_all_pitches_sounding_during_duration(
#         attack_time, dur, voices=voices_above)
#     if pitch > min(pitches_above):
#         return True
#
#     voices_below = [i for i in range(super_pattern.num_voices) if i < voice_i]
#     pitches_below = super_pattern.get_all_pitches_sounding_during_duration(
#         attack_time, dur, voices=voices_below)
#     if pitch < max(pitches_below):
#         return True
#
#     return False


def get_pitches_to_check_for_crossings(
    super_pattern, attack_time, dur, voice_i
):
    # MAYBE make work with existing voices?
    voices_above = [i for i in range(super_pattern.num_voices) if i > voice_i]
    pitches_above = super_pattern.get_all_pitches_sounding_during_duration(
        attack_time, dur, voices=voices_above
    )
    voices_below = [i for i in range(super_pattern.num_voices) if i < voice_i]
    pitches_below = super_pattern.get_all_pitches_sounding_during_duration(
        attack_time, dur, voices=voices_below
    )
    return max(pitches_below), min(pitches_above)


def _get_available_pcs(er, super_pattern, poss_note, include_if_possible=None):

    pc_chord = er.get(poss_note.harmony_i % er.num_harmonies, "pc_chords")
    pc_scale = er.get(poss_note.harmony_i % er.num_harmonies, "pc_scales")

    chord_tone = _choose_whether_chord_tone(er, super_pattern, poss_note)

    pc_non_chord = [pc for pc in pc_scale if pc not in pc_chord]

    if chord_tone:
        out = [pc_chord[:], pc_non_chord]
    elif er.chord_tone_selection and er.force_non_chord_tones:
        out = [pc_non_chord, pc_chord[:]]
    else:
        return [
            pc_scale,
        ]

    if include_if_possible:
        if not isinstance(include_if_possible, list):
            include_if_possible = [
                include_if_possible,
            ]
        for pitch in include_if_possible:
            pc = pitch % er.tet
            if pc in pc_scale and pc not in out[0]:
                out[0].append(pc)
                out[1].remove(pc)
    return out


def _get_available_pitches(er, super_pattern, available_pcs, poss_note):

    min_pitch, max_pitch = er.get(poss_note.voice_i, "voice_ranges")
    if not er.get(poss_note.voice_i, "allow_voice_crossings"):
        (
            highest_pitch_below,
            lowest_pitch_above,
        ) = get_pitches_to_check_for_crossings(
            super_pattern,
            poss_note.attack_time,
            poss_note.dur,
            poss_note.voice_i,
        )
        if highest_pitch_below > min_pitch:
            min_pitch = highest_pitch_below
        if lowest_pitch_above < max_pitch:
            max_pitch = lowest_pitch_above

    out = []

    for sub_available_pcs in available_pcs:
        available_pitches = er_misc_funcs.get_all_pitches_in_range(
            sub_available_pcs, (min_pitch, max_pitch), tet=er.tet
        )
        sub_out = []
        for available_pitch in available_pitches:
            permitted_interval = er_make2.check_harmonic_intervals(
                er,
                super_pattern,
                available_pitch,
                poss_note.attack_time,
                poss_note.dur,
                poss_note.voice_i,
            )
            if permitted_interval:
                if er.get(
                    poss_note.voice_i, "chord_tones_no_diss_treatment"
                ) and er_make2.check_if_chord_tone(
                    er, super_pattern, poss_note.attack_time, available_pitch
                ):
                    sub_out.append(available_pitch)
                elif poss_note.dur < er.get(
                    poss_note.voice_i, "min_dur_for_cons_treatment"
                ):
                    sub_out.append(available_pitch)
                else:
                    consonant = er_make2.check_consonance(
                        er,
                        super_pattern,
                        available_pitch,
                        poss_note.attack_time,
                        poss_note.dur,
                        poss_note.voice_i,
                    )
                    if consonant:
                        sub_out.append(available_pitch)
        out.append(sub_out)

    return out


def _within_limit_intervals(er, super_pattern, available_pitches, poss_note):

    prev_note = super_pattern.voices[poss_note.voice_i].get_prev_note(
        poss_note.attack_time
    )

    if prev_note is None:
        return available_pitches

    prev_pitch = prev_note.pitch

    chord_tone = er_make2.check_if_chord_tone(
        er, super_pattern, prev_note.attack_time, prev_pitch
    )

    max_interval, min_interval = er_make2.get_limiting_intervals(
        er, poss_note.voice_i, chord_tone
    )

    return [
        er_make2.check_melodic_intervals(
            er,
            sub_available_pitches,
            prev_pitch,
            max_interval,
            min_interval,
            poss_note.harmony_i,
        )
        for sub_available_pitches in available_pitches
    ]


def _remove_parallels(er, super_pattern, available_pitches, poss_note):

    forbidden_parallels = er.prohibit_parallels
    prev_pitch = super_pattern.get_prev_pitch(
        poss_note.attack_time, poss_note.voice_i
    )
    other_voices = er_misc_funcs.get_prev_voice_indices(
        super_pattern, poss_note.attack_time, poss_note.dur
    )
    other_voices_dict = {}

    for other_voice in other_voices:
        if not super_pattern.attack(poss_note.attack_time, other_voice):
            continue
        other_prev_pitch, other_pitch = super_pattern.get_last_n_pitches(
            2, poss_note.attack_time, other_voice
        )
        if -1 in (other_prev_pitch, other_pitch):
            continue
        prev_interval = prev_pitch - other_prev_pitch
        if prev_interval % er.tet not in forbidden_parallels:
            continue
        other_voices_dict[other_voice] = {
            "prev_interval": prev_interval,
            "other_pitch": other_pitch,
        }

    if not other_voices_dict:
        return

    for other_voice in other_voices_dict.values():
        prev_interval = other_voice["prev_interval"]
        other_pitch = other_voice["other_pitch"]
        for available_pitch in available_pitches.copy():
            interval = available_pitch - other_pitch
            if prev_interval % er.tet == interval % er.tet:

                if er.antiparallels or np.sign(prev_interval) == np.sign(
                    interval
                ):
                    available_pitches.remove(available_pitch)


def _weight_intervals_and_choose(
    intervals, log_base=1.01, unison_weighted_as=3
):
    """Returns a choice from a list of intervals, weighted according
    to the size of each interval, where smaller intervals get a larger weight.

    There's nothing about this function that requires the intervals be
    generic or specific, but generic will probably generally give
    better results.

    Keyword args:
        log_base: Must be greater than 1.0. Increasing it increases the
            probability of larger intervals. 1.5 seems to be a decent value.
        unison_weighted_as: Unisons will be weighted the same as this interval.
    """
    weighted_choices = []
    if unison_weighted_as == 0:
        for interval in intervals:
            if interval == 0:
                weight = math.log(unison_weighted_as + log_base, log_base)
            else:
                weight = math.log(abs(interval) + log_base, log_base)
            weighted_choices.append((interval, 100 / weight))
    else:
        for interval in intervals:
            if interval == 0:
                weight = math.log(unison_weighted_as + log_base - 1, log_base)
            else:
                weight = math.log(abs(interval) + log_base - 1, log_base)
            weighted_choices.append((interval, 100 / weight))

    choices, weights = zip(*weighted_choices)
    cum_dist = list(itertools.accumulate(weights))
    random_x = random.random() * cum_dist[-1]
    choice = choices[bisect.bisect(cum_dist, random_x)]
    return choice


def _apply_melodic_control(er, super_pattern, available_pitches, poss_note):
    prev_pitch = super_pattern.get_prev_pitch(
        poss_note.attack_time, poss_note.voice_i
    )
    available_intervals = {}
    for available_pitch in available_pitches:
        generic_interval = er_misc_funcs.get_generic_interval(
            er, poss_note.harmony_i, available_pitch, prev_pitch
        )
        available_intervals[generic_interval] = available_pitch
    chosen_interval = _weight_intervals_and_choose(
        list(available_intervals.keys()),
        log_base=er.control_log_base,
        unison_weighted_as=er.unison_weighted_as,
    )
    pitch = available_intervals[chosen_interval]
    return pitch


def _too_many_alternations(er, super_pattern, pitch, attack_time, voice_i):
    num_notes = er.get(voice_i, "max_alternations") * 2
    prev_n_pitches = super_pattern.get_prev_n_pitches(
        num_notes - 1, attack_time, voice_i
    )
    last_n_pitches = prev_n_pitches + [
        pitch,
    ]
    even = [last_n_pitches[i] for i in range(num_notes) if i % 2 == 0]
    odd = [last_n_pitches[i] for i in range(num_notes) if i % 2 == 1]
    if len(set(even)) == len(set(odd)) == 1:
        return True
    return False


def _too_many_repeated_notes(er, super_pattern, pitch, attack_time, voice_i):
    num_notes = er.max_repeated_notes + 2
    prev_n_pitches = super_pattern.get_prev_n_pitches(
        num_notes - 1, attack_time, voice_i
    )
    last_n_pitches = prev_n_pitches + [
        pitch,
    ]
    if len(set(last_n_pitches)) == 1:
        return True
    return False


def _choose_pitch(
    er, super_pattern, available_pitches, poss_note, choose_first=None
):
    if choose_first and choose_first in available_pitches:
        pitch = choose_first
    elif er.control_melodic_intervals:
        pitch = _apply_melodic_control(
            er, super_pattern, available_pitches, poss_note
        )
    else:
        pitch = random.choice(available_pitches)

    if er.get(poss_note.voice_i, "max_alternations") and _too_many_alternations(
        er, super_pattern, pitch, poss_note.attack_time, poss_note.voice_i
    ):
        return pitch, "too_many_alternations"
    if er.max_repeated_notes >= 0 and _too_many_repeated_notes(
        er, super_pattern, pitch, poss_note.attack_time, poss_note.voice_i
    ):
        return pitch, "too_many_repeated_notes"
    if isinstance(er.get(poss_note.voice_i, "pitch_loop_complete"), bool):
        last_n_pitches = super_pattern.voices[
            poss_note.voice_i
        ].get_prev_n_pitches(
            er.get(poss_note.voice_i, "pitch_loop") - 1, poss_note.attack_time
        ) + [
            pitch,
        ]
        if -1 in last_n_pitches:
            pass
        elif len(set(last_n_pitches)) == 1:
            return pitch, "pitch_loop_just_one_pitch"

    return pitch, "success"


def _choose_from_pitches(
    er, super_pattern, available_pitches, poss_note, choose_first=None
):
    result = ""
    failure_count = er_exceptions.UnableToChoosePitchError()
    while result != "success":
        if not available_pitches:
            raise failure_count
        pitch, result = _choose_pitch(
            er,
            super_pattern,
            available_pitches,
            poss_note,
            choose_first=choose_first,
        )
        if result == "success":
            break
        available_pitches.remove(pitch)
        if result == "too_many_alternations":
            failure_count.too_many_alternations += 1
        elif result == "too_many_repeated_notes":
            failure_count.too_many_repeated_notes += 1
        elif result == "pitch_loop_just_one_pitch":
            failure_count.pitch_loop_just_one_pitch += 1

    return pitch


def _check_whether_to_force_root(er, super_pattern, poss_note):

    # MAYBE move this function to a more opportune location
    if er.force_root_in_bass == "none":
        return False
    if (
        poss_note.attack_time == 0
        and er.force_root_in_bass == "global_first_beat"
    ):
        return True
    if (
        er.force_root_in_bass == "global_first_note"
        and poss_note.attack_time == min(er.rhythms[BASS])
    ):
        return True
    if er.force_root_in_bass in ("first_note", "first_beat"):
        harmony_start_time = super_pattern.get_harmony_times(
            poss_note.harmony_i
        ).start_time
        if (
            poss_note.attack_time == harmony_start_time
            and er.force_root_in_bass == "first_beat"
        ):
            return True
        if poss_note.attack_time == min(
            [time for time in er.rhythms[BASS] if time >= harmony_start_time]
        ):
            return True
    return False


def _attempt_initial_pattern(
    er, super_pattern, available_pitch_error, attack_i=0
):

    sys.stdout.write(
        "\r"
        + SPINNING_LINE[attack_i % len(SPINNING_LINE)]
        + " "
        + available_pitch_error.status()
    )
    sys.stdout.flush()

    try:
        poss_note = PossibleNote(er, super_pattern, attack_i)
    except PossibleNoteError:
        return True

    # try:
    #     voice_i, attack_time = er.initial_pattern_order[attack_i]
    # except IndexError:
    #     return True

    # voice = super_pattern.voices[voice_i]
    # dur = er.rhythms[voice_i][attack_time]
    # harmony_i = super_pattern.get_harmony_i(attack_time)

    choose_first = None

    pitch_loop, hard_pitch_loop = er.get(
        poss_note.voice_i, "pitch_loop", "hard_pitch_loop"
    )
    if pitch_loop:
        looped_pitch = _pitch_loop(er, poss_note)
        if looped_pitch:
            if hard_pitch_loop:
                poss_note.voice.add_note(
                    looped_pitch, poss_note.attack_time, poss_note.dur
                )
                if _attempt_initial_pattern(
                    er,
                    super_pattern,
                    available_pitch_error,
                    attack_i=attack_i + 1,
                ):
                    return True
                del poss_note.voice[poss_note.attack_time]
                return False
            choose_first = looped_pitch

    if (
        poss_note.voice_i == BASS
        and (not er.bass_in_existing_voice)
        and _check_whether_to_force_root(er, super_pattern, poss_note)
    ):
        forced_root = er_make2.get_root_to_force(
            er, poss_note.voice_i, poss_note.harmony_i
        )
        if forced_root:
            poss_note.voice.add_note(
                forced_root, poss_note.attack_time, poss_note.dur
            )
            if _attempt_initial_pattern(
                er, super_pattern, available_pitch_error, attack_i=attack_i + 1
            ):
                return True
            del poss_note.voice[poss_note.attack_time]
            return False

    if er.force_repeated_notes:
        repeated_pitch = _repeat_pitch(super_pattern, poss_note)
        if repeated_pitch:
            poss_note.voice.add_note(
                repeated_pitch, poss_note.attack_time, poss_note.dur
            )
            if _attempt_initial_pattern(
                er, super_pattern, available_pitch_error, attack_i=attack_i + 1
            ):
                return True
            del poss_note.voice[poss_note.attack_time]
            return False

    if poss_note.voice_i in er.parallel_motion_followers:
        # MAYBE allow parallel motion to follow an existing voice?
        parallel_pitch = _force_parallel_motion(er, super_pattern, poss_note)
        if parallel_pitch:
            poss_note.voice.add_note(
                parallel_pitch, poss_note.attack_time, poss_note.dur
            )
            if _attempt_initial_pattern(
                er, super_pattern, available_pitch_error, attack_i=attack_i + 1
            ):
                return True
            del poss_note.voice[poss_note.attack_time]
            return False

    available_pcs = _get_available_pcs(
        er, super_pattern, poss_note, include_if_possible=choose_first
    )

    if er_misc_funcs.empty_nested(available_pcs):
        available_pitch_error.no_available_pcs += 1
        return False

    available_pitches = _get_available_pitches(
        er, super_pattern, available_pcs, poss_note
    )
    if er_misc_funcs.empty_nested(available_pitches):
        available_pitch_error.no_available_pitches += 1
        return False

    available_pitches = _within_limit_intervals(
        er, super_pattern, available_pitches, poss_note
    )

    if er_misc_funcs.empty_nested(available_pitches):
        available_pitch_error.exceeding_max_interval += 1
        return False

    if er.prohibit_parallels:
        for sub_available_pitches in available_pitches:
            _remove_parallels(
                er, super_pattern, sub_available_pitches, poss_note
            )
        if er_misc_funcs.empty_nested(available_pitches):
            available_pitch_error.forbidden_parallels += 1
            return False

    for sub_available_pitches in available_pitches:
        while True:
            try:
                pitch = _choose_from_pitches(
                    er,
                    super_pattern,
                    sub_available_pitches,
                    poss_note,
                    choose_first=choose_first,
                )

            except er_exceptions.UnableToChoosePitchError as unable_error:
                available_pitch_error.unable_to_choose_pitch += 1
                available_pitch_error.excess_alternations += (
                    unable_error.too_many_alternations
                )
                available_pitch_error.excess_repeated_notes += (
                    unable_error.too_many_repeated_notes
                )
                available_pitch_error.pitch_loop_just_one_pitch += (
                    unable_error.pitch_loop_just_one_pitch
                )
                break

            poss_note.voice.add_note(
                pitch, poss_note.attack_time, poss_note.dur
            )
            if _attempt_initial_pattern(
                er, super_pattern, available_pitch_error, attack_i=attack_i + 1
            ):
                return True
            sub_available_pitches.remove(pitch)
            del poss_note.voice[poss_note.attack_time]

    return False


def _get_bass_root_times(er, super_pattern):
    bass = super_pattern.voices[0]
    er.bass_root_times = []
    for note in bass:
        attack_time = note.attack_time
        harmony_i = super_pattern.get_harmony_i(attack_time)
        root_pc = er.get(harmony_i, "pc_chords")[0]

        if note.pitch % er.tet != root_pc:
            continue

        if er.preserve_root_in_bass == "all":
            er.bass_root_times.append(attack_time)
            continue

        harmony_times = super_pattern.get_harmony_times(harmony_i)
        harmony_dur = harmony_times.end_time - harmony_times.start_time
        all_pitches = bass.get_all_pitches_attacked_during_duration(
            harmony_times.start_time, dur=harmony_dur
        )

        if er_misc_funcs.lowest_occurrence_of_pc_in_set(
            note.pitch, all_pitches, tet=er.tet
        ):
            er.bass_root_times.append(attack_time)


def make_initial_pattern(er):
    """Makes the basic pattern."""

    available_pitch_error = er_exceptions.AvailablePitchMaterialsError(er)

    for rep in itertools.count(start=1):
        for attempt in range(er.initial_pattern_attempts):
            # QUESTION is it possible to "backspace" to previous line
            # (so that "Initial pattern attempt" doesn't have to take a new line
            #   every time)?
            er.rhythms = er_rhythm.rhythms_handler(er)
            er.initial_pattern_order = er_rhythm.get_attack_order(er)
            super_pattern = er_notes.Score(
                num_voices=er.num_voices,
                tet=er.tet,
                harmony_len=er.harmony_len,
                total_len=er.total_len,
                ranges=er.voice_ranges,
                time_sig=er.time_sig,
                existing_score=er.existing_score,
            )
            initial_str = f"\rInitial pattern attempt {attempt + 1}"
            sys.stdout.write(
                initial_str + " " * (LINE_WIDTH - len(initial_str)) + "\n"
            )
            sys.stdout.flush()
            if _attempt_initial_pattern(
                er, super_pattern, available_pitch_error
            ):
                # sys.stdout.write("\n... success!\n")
                # sys.stdout.flush()
                success = True
                break
            success = False
        if success or not er.ask_for_more_attempts:
            break
        answer = input(
            f"\nFailed after {rep * er.initial_pattern_attempts}"
            " initial pattern attempts. Try another "
            f"{er.initial_pattern_attempts} attempts "
            "(y/n)?"
        )
        if answer != "y":
            break

    if not success:
        sys.stdout.write("\n")
        sys.stdout.flush()
        raise available_pitch_error

    if er.preserve_root_in_bass != "none":
        _get_bass_root_times(er, super_pattern)

    return super_pattern


def transpose_roots(er, super_pattern):

    bass = super_pattern.voices[BASS]
    lowest_pitch = (
        er.voice_ranges[BASS][LOWEST_PITCH] - er.extend_bass_range_for_roots
    )
    # pattern_len = er.pattern_len[BASS]

    harmony_end_time = 0

    for note in bass:
        attack_time = note.attack_time

        new_pitch = note.pitch - er.tet
        if new_pitch < lowest_pitch:
            continue

        if attack_time >= harmony_end_time:
            harmony_i = super_pattern.get_harmony_i(attack_time)
            harmony_times = super_pattern.get_harmony_times(harmony_i)
            harmony_dur = harmony_times.end_time - harmony_times.start_time
            all_pitches = super_pattern.get_all_pitches_attacked_during_duration(
                harmony_times.start_time, dur=harmony_dur, voices=[BASS,]
            )
            root_pc = er.get(harmony_i, "pc_chords")[ROOT]

        if note.pitch % er.tet != root_pc:
            continue

        if min(all_pitches) == note.pitch:
            continue

        if er_misc_funcs.lowest_occurrence_of_pc_in_set(
            note.pitch, all_pitches, tet=er.tet
        ):
            note.pitch = new_pitch


def voice_lead_pattern(er, super_pattern, voice_lead_error):

    voice_lead_error.reset_temp_counter()

    if er_vl_strict_and_flex.voice_lead_pattern_strictly(
        er,
        super_pattern,
        voice_lead_error,
        pattern_voice_leading_i=er.num_voices,
    ):
        return True

    if (
        er.allow_flexible_voice_leading
        and er_vl_strict_and_flex.voice_lead_pattern_flexibly(
            er,
            super_pattern,
            voice_lead_error,
            pattern_voice_leading_i=er.num_voices,
        )
    ):
        return True

    return False


def make_super_pattern(er):
    """Makes the super pattern.
    """

    voice_lead_error = er_exceptions.VoiceLeadingError(er)

    for rep in itertools.count(start=1):
        for attempt in range(er.voice_leading_attempts):
            sys.stdout.write(f"Super pattern attempt {attempt + 1}\n")
            sys.stdout.flush()

            super_pattern = make_initial_pattern(er)

            initial_pattern_copy = copy.copy(super_pattern)

            sys.stdout.write("\nSucceeded, attempting voice-leading...  " "\n")
            sys.stdout.flush()
            if voice_lead_pattern(er, super_pattern, voice_lead_error):
                sys.stdout.write(" ... success!\n")
                sys.stdout.flush()
                success = True
                break
            sys.stdout.write(
                "\r"
                + SPINNING_LINE[0]
                + " "
                + str(voice_lead_error.temp_failure_counter)
            )
            sys.stdout.write(" ... failed.\n")
            sys.stdout.flush()

            success = False
        if success or not er.ask_for_more_attempts:
            break
        answer = input(
            f"Failed after {rep * er.voice_leading_attempts}"
            " voice-leading attempts. Try another "
            f"{er.voice_leading_attempts} attempts "
            "(y/n)?"
        )
        if answer != "y":
            break

    if not success:
        raise voice_lead_error

    if er.extend_bass_range_for_roots > 0:
        transpose_roots(er, super_pattern)

    return super_pattern


def repeat_super_pattern(er, super_pattern, apply_to_existing_voices=False):
    """Repeats the super pattern the indicated number of times.
    """

    super_pattern.remove_passage(
        er.super_pattern_len,
        end_time=0,
        apply_to_existing_voices=apply_to_existing_voices,
    )

    if not er.super_pattern_reps_cont_var:
        repetition_start_time = er.super_pattern_len
        for repetition in range(1, er.num_reps_super_pattern):
            super_pattern.repeat_passage(
                0,
                er.super_pattern_len,
                repetition_start_time,
                apply_to_existing_voices=apply_to_existing_voices,
            )
            repetition_start_time += er.super_pattern_len

        return

    for voice_i, voice in enumerate(super_pattern.voices):
        rhythm = er.rhythms[voice_i]
        rhythm_list = list(rhythm.items())
        # rhythm_list_len = er.total_rhythm_len[voice_i]
        num_notes_in_super_pattern = len(voice)
        new_voice = er_notes.Voice()
        for repetition in range(1, er.num_reps_super_pattern):
            repetition_start_time = repetition * er.super_pattern_len
            last_attack_time = -1
            note_attack_i = -1

            for note in voice:
                if note.attack_time > last_attack_time:
                    note_attack_i += 1
                    last_attack_time = note.attack_time
                new_note_attack_i = (
                    repetition * num_notes_in_super_pattern + note_attack_i
                )
                new_note = copy.deepcopy(note)
                new_note.attack_time, new_note.dur = rhythm_list[
                    new_note_attack_i % len(rhythm_list)
                ]
                new_note.attack_time += (
                    new_note_attack_i
                    // len(rhythm_list)
                    * rhythm.total_rhythm_len
                )
                new_voice.add_note_object(new_note, update_sort=False)
        new_voice.update_sort()
        voice.append(new_voice)

    if apply_to_existing_voices:
        for voice in super_pattern.existing_voices:
            repetition_start_time = er.super_pattern_len
            for repetition in range(1, er.num_reps_super_pattern):
                voice.repeat_passage(
                    0, er.super_pattern_len, repetition_start_time
                )
                repetition_start_time += er.super_pattern_len


def apply_specific_transpositions(
    er, super_pattern, end, apply_to_existing_voices=False
):
    start_time = 0
    end_time = 0
    transpose_i = 0
    transpose_interval = 0
    er.negative_max = -er.cumulative_max_transpose_interval
    while start_time < end:
        end_time += er.get(transpose_i, "transpose_len")
        super_pattern.transpose(
            transpose_interval,
            start_time,
            end_time,
            apply_to_existing_voices=apply_to_existing_voices,
        )

        if er.transpose_intervals:
            transpose_interval += er.get(transpose_i, "transpose_intervals")
        else:
            transpose_interval += random.randrange(1, er.tet) * random.choice(
                (1, -1)
            )

        if transpose_interval > er.cumulative_max_transpose_interval:
            transpose_interval -= er.tet
        elif transpose_interval < er.negative_max:
            transpose_interval += er.tet

        transpose_i += 1
        start_time = end_time


def apply_generic_transpositions(
    er, super_pattern, end, apply_to_existing_voices=False
):
    start_time = 0
    end_time = 0
    transpose_i = 0
    transpose_interval = 0
    while start_time < end:
        end_time += er.get(transpose_i, "transpose_len")
        er_misc_funcs.generic_transpose(
            er,
            super_pattern,
            transpose_interval,
            er.cumulative_max_transpose_interval,
            start_time,
            end_time,
            apply_to_existing_voices=apply_to_existing_voices,
        )

        if er.transpose_intervals:
            transpose_interval += er.get(transpose_i, "transpose_intervals")
        else:
            # We guess that the length of the first pc_scale is an octave
            # in generic intervals throughout.
            transpose_interval += random.randrange(
                1, len(er.pc_scales[0])
            ) * random.choice((1, -1))

        transpose_i += 1
        start_time = end_time


def apply_transpositions(
    er, super_pattern, end, apply_to_existing_voices=False
):
    if not er.transpose:
        return
    if er.transpose_type == "specific":
        apply_specific_transpositions(
            er,
            super_pattern,
            end,
            apply_to_existing_voices=apply_to_existing_voices,
        )
        return
    if er.transpose_type == "generic":
        apply_generic_transpositions(
            er,
            super_pattern,
            end,
            apply_to_existing_voices=apply_to_existing_voices,
        )
        return

    class TransposeError(Exception):
        pass

    raise TransposeError(
        "Transposition type not recognized.\n"
        "er.transpose_type should be either 'specific' "
        "or 'generic'"
    )


def complete_pattern(er, super_pattern):

    if er.transpose_before_repeat:
        apply_transpositions(
            er,
            super_pattern,
            er.super_pattern_len,
            apply_to_existing_voices=er.existing_voices_transpose,
        )

    repeat_super_pattern(
        er, super_pattern, apply_to_existing_voices=er.existing_voices_transpose
    )

    if not er.transpose_before_repeat:
        apply_transpositions(
            er,
            super_pattern,
            er.total_len,
            apply_to_existing_voices=er.existing_voices_transpose,
        )


LINE_WIDTH = os.get_terminal_size().columns
SPINNING_LINE = "|/-\\"

# Constants for accessing voice ranges

LOWEST_PITCH = 0
HIGHEST_PITCH = 1

# Constants for accessing voices

BASS = 0

ROOT = 0


if __name__ == "__main__":
    pass
