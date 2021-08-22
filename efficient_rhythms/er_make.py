"""Makes the actual music.
"""
import bisect
import functools
import itertools
import math
import os
import random

import numpy as np

from . import er_choirs
from . import er_classes
from . import er_exceptions
from . import er_make2
from . import er_misc_funcs
from . import er_rhythm
from . import er_vl_strict_and_flex


class PossibleNoteError(Exception):
    pass


class PossibleNote:
    """A class for storing the properties of a possible note."""

    def __init__(self, er, super_pattern, onset_i):
        self.onset_i = onset_i
        try:
            self.voice_i, self.onset = er.initial_pattern_order[onset_i]
        except IndexError:
            raise PossibleNoteError()  # pylint: disable=raise-missing-from
        self.voice = super_pattern.voices[self.voice_i]
        self.dur = er.rhythms[self.voice_i][self.onset]
        self.harmony_i = super_pattern.get_harmony_i(self.onset)
        self.score = super_pattern

    def __repr__(self):
        return (
            f"{self.__class__.__name__}(voice_i={self.voice_i}, "
            f"onset_i={self.onset_i}, onset={self.onset}, dur={self.dur}, "
            f"harmony_i={self.harmony_i})"
        )

    @functools.cached_property
    def prev_pitch(self):
        """Returns the previous pitch, skipping over any intervening rest.

        Returns -1 at start of score.
        """
        return self.score.get_prev_pitch(self.onset, self.voice_i)

    @functools.cached_property
    def prev_note(self):
        """Returns the previous Note, skipping over any intervening rest.

        Returns None at start of score.
        """
        return self.score.voices[self.voice_i].get_prev_note(self.onset)

    @functools.cached_property
    def other_voice_indices(self):
        return er_misc_funcs.get_prev_voice_indices(
            self.score, self.onset, self.dur
        )


def get_repeated_pitch(super_pattern, poss_note):
    # voice = super_pattern.voices[poss_note.voice_i]
    harmony_start_time = super_pattern.get_harmony_times(
        poss_note.harmony_i
    ).start_time
    return er_make2.get_repeated_pitch(
        poss_note=poss_note, min_onset=harmony_start_time
    )


def get_looped_pitch(er, poss_note):

    loop_len = er.get(poss_note.voice_i, "pitch_loop")
    prev_n_pitches = poss_note.voice.get_prev_n_pitches(
        loop_len, poss_note.onset
    )
    pitch_to_loop = prev_n_pitches[0]

    if pitch_to_loop <= 0:
        return 0
    scale = er.get(poss_note.harmony_i, "gamut_scales")
    if pitch_to_loop not in scale:
        look_first = random.choice([1, -1])
        look_second = -1 * look_first
        i = 1
        while True:
            pitch_to_test = pitch_to_loop + look_first * i
            if (
                pitch_to_test in scale
                and len(
                    set(
                        [
                            pitch_to_test,
                        ]
                        + prev_n_pitches[1:]
                    )
                )
                != 1
            ):
                pitch_to_loop = pitch_to_test
                break
            pitch_to_test = pitch_to_loop + look_second * i
            if (
                pitch_to_test in scale
                and len(
                    set(
                        [
                            pitch_to_test,
                        ]
                        + prev_n_pitches[1:]
                    )
                )
                != 1
            ):
                pitch_to_loop = pitch_to_test
                break
            i += 1

    return pitch_to_loop


def get_forced_parallel_motion(er, super_pattern, poss_note):

    parallel_motion_info = er.parallel_motion_followers[poss_note.voice_i]
    leader_i = parallel_motion_info.leader_i
    motion_type = parallel_motion_info.motion_type

    leader = super_pattern.voices[leader_i]
    follower = super_pattern.voices[poss_note.voice_i]

    if poss_note.onset not in leader:
        return None

    harmony_start_time = super_pattern.get_harmony_times(
        poss_note.harmony_i
    ).start_time

    if motion_type == "within_harmonies":

        leader_prev_pitch, leader_pitch = leader.get_last_n_pitches(
            2,
            poss_note.onset,
            min_onset=harmony_start_time,
            stop_at_rest=True,
        )

        follower_prev_pitch = follower.get_prev_pitch(
            poss_note.onset,
            min_onset=harmony_start_time,
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

        min_pitch, max_pitch = get_boundary_pitches(
            er, super_pattern, poss_note
        )

        if follower_pitch < min_pitch:
            follower_pitch += er.tet
        elif follower_pitch > max_pitch:
            follower_pitch -= er.tet

        if (
            follower_prev_pitch != follower_pitch
            and (follower_pitch - leader_pitch) % er.tet
            in er.prohibit_parallels
        ):
            return None

        return follower_pitch

    # LONGTERM I'm not sure whether "global" parallel motion of this
    #       type of parallel motion is coherent... mull this over!

    if motion_type == "global":
        raise NotImplementedError("Global parallel motion not yet implemented.")
    return None


def check_other_voices_for_chord_tones(
    er, super_pattern, onset, prev_voices, harmony_i
):

    # This function assumes that the other voices are monophonic.

    for prev_voice_i in prev_voices:
        prev_voice = super_pattern.voices[prev_voice_i]
        if onset not in prev_voice:
            continue
        prev_note = prev_voice[onset][0]
        pc = prev_note.pitch % er.tet
        if pc in er.get(harmony_i, "pc_chords"):
            return True
    return False


def get_n_since_chord_tone(er, super_pattern, onset, voice_i):
    voice = super_pattern.voices[voice_i]
    n = 0
    for note in reversed(voice):
        time = note.onset
        if time >= onset:
            continue
        if er_make2.check_if_chord_tone(
            er, super_pattern, note.onset, note.pitch
        ):
            return n
        n += 1

    # When constructing the first note, arbitrarily set n to 1.
    if n == 0:
        return 1
    return n


def choose_whether_chord_tone(er, super_pattern, poss_note):
    def _chord_tone_probability():
        x = er.max_n_between_chord_tones
        if x == 0:
            return 1
        if er.chord_tone_prob_curve == "quadratic":
            result = (n_since_chord_tone / x) ** (1 / 2)

        elif er.chord_tone_prob_curve == "linear":
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

    force_chord_tone = er.force_chord_tone

    if force_chord_tone != "none":
        if poss_note.onset == 0:
            return True
        if force_chord_tone == "global_first_note":
            if poss_note.prev_pitch <= 0:
                return True
        else:
            harmony_start_time = super_pattern.get_harmony_times(
                poss_note.harmony_i
            ).start_time
            if (
                force_chord_tone == "first_beat"
                and poss_note.onset == harmony_start_time
            ):
                return True
            if force_chord_tone == "first_note":
                prev_note = poss_note.prev_note
                if prev_note is None or (
                    prev_note.pitch <= 0
                    and prev_note.onset >= harmony_start_time
                ):
                    return True

    # Next, if er.chord_tone_selection is false, return false.
    if not er.chord_tone_selection:
        return False

    # Finally, apply remaining chord_tone settings.
    rest_dur = er.get(poss_note.voice_i, "chord_tone_before_rests")

    if rest_dur:
        if er.rhythms[poss_note.voice_i].rest_before_onset(
            poss_note.onset, rest_dur
        ):
            return True

    if er.chord_tones_sync_onset_in_all_voices:
        if poss_note.other_voice_indices:
            if check_other_voices_for_chord_tones(
                er,
                super_pattern,
                poss_note.onset,
                poss_note.other_voice_indices,
                poss_note.harmony_i,
            ):
                return True
            # QUESTION should there be a "soft" version of chord tones
            # syncing in all voices? Where the absence of a chord tone
            # in other voices doesn't force the absence of a chord tone
            # in this voice? (Although non-chord tones are only forced
            # if er.try_to_force_non_chord_tones.) In that case one would probably
            # have to use only one voice as the "leader" to determine whether
            # to have chord_tones. (Although this may be effectively what
            # happens already.)
            return False

    n_since_chord_tone = get_n_since_chord_tone(
        er, super_pattern, poss_note.onset, poss_note.voice_i
    )

    # LONGTERM chord tone probability influenced by metric position

    if random.random() < _chord_tone_probability():
        return True

    return False


# def check_for_voice_crossings(super_pattern, pitch, onset, dur, voice_i):
#     voices_above = [i for i in range(super_pattern.num_voices) if i > voice_i]
#     pitches_above = super_pattern.get_all_ps_sounding_in_dur(
#         onset, dur, voices=voices_above)
#     if pitch > min(pitches_above):
#         return True
#
#     voices_below = [i for i in range(super_pattern.num_voices) if i < voice_i]
#     pitches_below = super_pattern.get_all_ps_sounding_in_dur(
#         onset, dur, voices=voices_below)
#     if pitch < max(pitches_below):
#         return True
#
#     return False


def get_pitches_to_check_for_crossings(super_pattern, onset, dur, voice_i):
    # MAYBE make work with existing voices?
    voices_above = [i for i in range(super_pattern.num_voices) if i > voice_i]
    pitches_above = super_pattern.get_all_ps_sounding_in_dur(
        onset, dur, voices=voices_above
    )
    above = min(pitches_above) if pitches_above else None
    voices_below = [i for i in range(super_pattern.num_voices) if i < voice_i]
    pitches_below = super_pattern.get_all_ps_sounding_in_dur(
        onset, dur, voices=voices_below
    )
    below = max(pitches_below) if pitches_below else None
    return below, above


def _get_available_pcs(er, super_pattern, poss_note, include_if_possible=None):

    pc_chord = er.get(poss_note.harmony_i % er.num_harmonies, "pc_chords")
    pc_scale = er.get(poss_note.harmony_i % er.num_harmonies, "pc_scales")

    chord_tone = choose_whether_chord_tone(er, super_pattern, poss_note)

    pc_non_chord = [pc for pc in pc_scale if pc not in pc_chord]

    if chord_tone:
        # Take a copy of pc_chord because we don't want to alter the original
        #   in er. (It is potentially altered in the `if include_in_possible`
        #   loop below)
        out = [pc_chord[:], pc_non_chord[:]]
    elif er.chord_tone_selection and er.try_to_force_non_chord_tones:
        out = [pc_non_chord[:], pc_chord[:]]
    else:
        # We don't copy pc_scale because it is never altered (but it might be
        # smart to enforce this somehow, e.g., by having it be a tuple?)
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


def get_boundary_pitches(er, super_pattern, poss_note):
    min_pitch, max_pitch = er.get(poss_note.voice_i, "voice_ranges")
    if not er.get(poss_note.voice_i, "allow_voice_crossings"):
        (
            highest_pitch_below,
            lowest_pitch_above,
        ) = get_pitches_to_check_for_crossings(
            super_pattern,
            poss_note.onset,
            poss_note.dur,
            poss_note.voice_i,
        )
        if highest_pitch_below is not None and highest_pitch_below > min_pitch:
            min_pitch = highest_pitch_below
        if lowest_pitch_above is not None and lowest_pitch_above < max_pitch:
            max_pitch = lowest_pitch_above
    return min_pitch, max_pitch


def get_available_pitches(er, score, available_pcs, poss_note):

    min_pitch, max_pitch = get_boundary_pitches(er, score, poss_note)

    out = []

    for sub_available_pcs in available_pcs:
        available_pitches = er_misc_funcs.get_all_pitches_in_range(
            sub_available_pcs, (min_pitch, max_pitch), tet=er.tet
        )
        sub_out = []
        for available_pitch in available_pitches:
            if er_make2.check_harmonic_intervals(
                er,
                score,
                available_pitch,
                poss_note.onset,
                poss_note.dur,
                poss_note.voice_i,
            ):
                if er.get(
                    poss_note.voice_i, "chord_tones_no_diss_treatment"
                ) and er_make2.check_if_chord_tone(
                    er, score, poss_note.onset, available_pitch
                ):
                    sub_out.append(available_pitch)
                elif poss_note.dur < er.get(
                    poss_note.voice_i, "min_dur_for_cons_treatment"
                ):
                    sub_out.append(available_pitch)
                else:
                    consonant = er_make2.check_consonance(
                        er,
                        score,
                        available_pitch,
                        poss_note.onset,
                        poss_note.dur,
                        poss_note.voice_i,
                    )
                    if consonant:
                        sub_out.append(available_pitch)
        out.append(sub_out)
    return out


def within_limit_intervals(er, super_pattern, available_pitches, poss_note):

    prev_note = poss_note.prev_note

    if prev_note is None:
        return available_pitches
    chord_tone = er_make2.check_if_chord_tone(
        er, super_pattern, prev_note.onset, prev_note.pitch
    )
    max_interval, min_interval = er_make2.get_limiting_intervals(
        er, poss_note.voice_i, chord_tone
    )

    return [
        er_make2.check_melodic_intervals(
            er,
            sub_available_pitches,
            prev_note.pitch,
            max_interval,
            min_interval,
            poss_note.harmony_i,
        )
        for sub_available_pitches in available_pitches
    ]


def remove_parallels(er, super_pattern, available_pitches, poss_note):

    forbidden_parallels = er.prohibit_parallels

    for other_voice_i in poss_note.other_voice_indices:
        if not super_pattern.onset(poss_note.onset, other_voice_i):
            continue
        other_prev_pitch, other_pitch = super_pattern.get_last_n_pitches(
            2, poss_note.onset, other_voice_i
        )
        if -1 in (other_prev_pitch, other_pitch):
            continue
        if other_prev_pitch == other_pitch:
            continue
        prev_interval = poss_note.prev_pitch - other_prev_pitch
        if prev_interval % er.tet not in forbidden_parallels:
            continue
        for available_pitch in available_pitches.copy():
            interval = available_pitch - other_pitch
            if prev_interval % er.tet == interval % er.tet:
                if er.antiparallels or np.sign(prev_interval) == np.sign(
                    interval
                ):
                    available_pitches.remove(available_pitch)


def weight_intervals_and_choose(intervals, log_base=1.01, unison_weighted_as=3):
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
    # maybe cache weighted_choices
    weighted_choices = []
    for interval in intervals:
        weight = math.log(
            (unison_weighted_as if interval == 0 else abs(interval))
            + log_base
            - 1,
            log_base,
        )
        weighted_choices.append((interval, 100 / weight))

    choices, weights = zip(*weighted_choices)
    cum_dist = list(itertools.accumulate(weights))
    random_x = random.random() * cum_dist[-1]
    choice = choices[bisect.bisect(cum_dist, random_x)]
    return choice


def apply_melodic_control(er, available_pitches, poss_note):
    # prev_pitch should be -1 at start of score, in which case
    # applying melodic control is meaningless
    prev_pitch = poss_note.prev_pitch
    if prev_pitch < 0:
        # Not sure that we really want to choose the initial pitch
        #   from a uniform distribution
        return random.choice(available_pitches)
    available_intervals = {}
    harmony_i = poss_note.harmony_i
    for available_pitch in available_pitches:
        generic_interval = er_misc_funcs.get_generic_interval(
            er, harmony_i, available_pitch, prev_pitch
        )
        available_intervals[generic_interval] = available_pitch
    chosen_interval = weight_intervals_and_choose(
        list(available_intervals.keys()),
        log_base=er.control_log_base,
        unison_weighted_as=er.unison_weighted_as,
    )
    pitch = available_intervals[chosen_interval]
    return pitch


def too_many_alternations(er, super_pattern, pitch, onset, voice_i):
    max_alternations = er.get(voice_i, "max_alternations")
    prev_n_pitches = super_pattern.get_prev_n_pitches(
        max_alternations * 2 - 1, onset, voice_i
    )
    if pitch == prev_n_pitches[-1]:
        # we don't want to filter out repeated pitches with this function
        return False
    for i in range(-2, max_alternations * -2, -2):
        if prev_n_pitches[i] != pitch:
            return False
        if prev_n_pitches[i - 1] != prev_n_pitches[-1]:
            return False
    return True


def too_many_repeated_notes(er, super_pattern, pitch, onset, voice_i):
    num_notes = er.max_repeated_notes + 1
    prev_n_pitches = super_pattern.get_prev_n_pitches(num_notes, onset, voice_i)
    last_n_pitches = prev_n_pitches + [
        pitch,
    ]
    if len(set(last_n_pitches)) == 1:
        return True
    return False


def choose_pitch(
    er, super_pattern, available_pitches, poss_note, choose_first=None
):
    if choose_first and choose_first in available_pitches:
        pitch = choose_first
    elif er.prefer_small_melodic_intervals:
        pitch = apply_melodic_control(er, available_pitches, poss_note)
    else:
        pitch = random.choice(available_pitches)

    if er.get(poss_note.voice_i, "max_alternations") and too_many_alternations(
        er, super_pattern, pitch, poss_note.onset, poss_note.voice_i
    ):
        return pitch, "too_many_alternations"
    if er.max_repeated_notes >= 0 and too_many_repeated_notes(
        er, super_pattern, pitch, poss_note.onset, poss_note.voice_i
    ):
        return pitch, "too_many_repeated_notes"
    if isinstance(er.get(poss_note.voice_i, "pitch_loop_complete"), bool):
        last_n_pitches = super_pattern.voices[
            poss_note.voice_i
        ].get_prev_n_pitches(
            er.get(poss_note.voice_i, "pitch_loop") - 1, poss_note.onset
        ) + [
            pitch,
        ]
        if -1 in last_n_pitches:
            pass
        elif len(set(last_n_pitches)) == 1:
            return pitch, "pitch_loop_just_one_pitch"

    return pitch, "success"


def choose_from_pitches(
    er, super_pattern, available_pitches, poss_note, choose_first=None
):
    result = ""
    failure_count = er_exceptions.UnableToChoosePitchError()
    while result != "success":
        if not available_pitches:
            raise failure_count
        pitch, result = choose_pitch(
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


def check_whether_to_force_foot(er, super_pattern, poss_note):

    # MAYBE move this function to a more opportune location
    if er.force_foot_in_bass == "none":
        return False
    if poss_note.onset == 0 and er.force_foot_in_bass == "global_first_beat":
        return True
    if (
        er.force_foot_in_bass == "global_first_note"
        and poss_note.onset == er.rhythms[BASS].onsets[0]
    ):
        return True
    if er.force_foot_in_bass in ("first_note", "first_beat"):
        harmony_start_time = super_pattern.get_harmony_times(
            poss_note.harmony_i
        ).start_time
        if (
            poss_note.onset == harmony_start_time
            and er.force_foot_in_bass == "first_beat"
        ):
            return True
        if (
            poss_note.onset
            == er.rhythms[BASS].at_or_after(harmony_start_time)[0]
        ):
            return True
    return False


def attempt_initial_pattern(
    er, super_pattern, available_pitch_error, onset_i=0
):

    er.build_status_printer.spin()
    er.check_time()

    try:
        poss_note = PossibleNote(er, super_pattern, onset_i)
    except PossibleNoteError:
        return True

    choose_first = None

    pitch_loop, hard_pitch_loop = er.get(
        poss_note.voice_i, "pitch_loop", "hard_pitch_loop"
    )
    if pitch_loop:
        looped_pitch = get_looped_pitch(er, poss_note)
        if looped_pitch:
            if hard_pitch_loop:
                poss_note.voice.add_note(
                    looped_pitch, poss_note.onset, poss_note.dur
                )
                if attempt_initial_pattern(
                    er,
                    super_pattern,
                    available_pitch_error,
                    onset_i=onset_i + 1,
                ):
                    return True
                del poss_note.voice[poss_note.onset]
                return False
            choose_first = looped_pitch

    if (
        poss_note.voice_i == BASS
        and (not er.bass_in_existing_voice)
        and check_whether_to_force_foot(er, super_pattern, poss_note)
    ):
        forced_foot = er_make2.get_foot_to_force(
            er, poss_note.voice_i, poss_note.harmony_i
        )
        if forced_foot:
            poss_note.voice.add_note(
                forced_foot, poss_note.onset, poss_note.dur
            )
            if attempt_initial_pattern(
                er, super_pattern, available_pitch_error, onset_i=onset_i + 1
            ):
                return True
            del poss_note.voice[poss_note.onset]
            return False

    if er.force_repeated_notes:
        repeated_pitch = get_repeated_pitch(super_pattern, poss_note)
        if repeated_pitch:
            poss_note.voice.add_note(
                repeated_pitch, poss_note.onset, poss_note.dur
            )
            if attempt_initial_pattern(
                er, super_pattern, available_pitch_error, onset_i=onset_i + 1
            ):
                return True
            del poss_note.voice[poss_note.onset]
            return False

    if poss_note.voice_i in er.parallel_motion_followers:
        # MAYBE allow parallel motion to follow an existing voice?
        parallel_pitch = get_forced_parallel_motion(
            er, super_pattern, poss_note
        )
        if parallel_pitch:
            poss_note.voice.add_note(
                parallel_pitch, poss_note.onset, poss_note.dur
            )
            if attempt_initial_pattern(
                er, super_pattern, available_pitch_error, onset_i=onset_i + 1
            ):
                return True
            del poss_note.voice[poss_note.onset]
            return False

    available_pcs = _get_available_pcs(
        er, super_pattern, poss_note, include_if_possible=choose_first
    )

    if er_misc_funcs.empty_nested(available_pcs):
        available_pitch_error.no_available_pcs()
        return False

    available_pitches = get_available_pitches(
        er, super_pattern, available_pcs, poss_note
    )
    if er_misc_funcs.empty_nested(available_pitches):
        available_pitch_error.no_available_pitches()
        return False
    available_pitches = within_limit_intervals(
        er, super_pattern, available_pitches, poss_note
    )
    if er_misc_funcs.empty_nested(available_pitches):
        available_pitch_error.exceeding_max_interval()
        return False

    if er.prohibit_parallels:
        for sub_available_pitches in available_pitches:
            remove_parallels(
                er, super_pattern, sub_available_pitches, poss_note
            )
        if er_misc_funcs.empty_nested(available_pitches):
            available_pitch_error.forbidden_parallels()
            return False
    for sub_available_pitches in available_pitches:
        while sub_available_pitches:
            try:
                pitch = choose_from_pitches(
                    er,
                    super_pattern,
                    sub_available_pitches,
                    poss_note,
                    choose_first=choose_first,
                )

            except er_exceptions.UnableToChoosePitchError as unable_error:
                # LONGTERM refactor
                available_pitch_error.unable_to_choose_pitch()
                available_pitch_error.excess_alternations(
                    unable_error.too_many_alternations
                )
                available_pitch_error.excess_repeated_notes(
                    unable_error.too_many_repeated_notes
                )
                available_pitch_error.pitch_loop_just_one_pitch(
                    unable_error.pitch_loop_just_one_pitch
                )
                break
            poss_note.voice.add_note(pitch, poss_note.onset, poss_note.dur)
            if attempt_initial_pattern(
                er, super_pattern, available_pitch_error, onset_i=onset_i + 1
            ):
                return True
            sub_available_pitches.remove(pitch)
            del poss_note.voice[poss_note.onset]

    return False


def _get_bass_foot_times(er, super_pattern):
    bass = super_pattern.voices[BASS]
    er.bass_foot_times = []
    harmony_times = er_classes.HarmonyTimes(0, 0, BASS)
    for note in bass:
        onset = note.onset
        if (
            harmony_times.end_time is not None
            and onset >= harmony_times.end_time
        ):
            harmony_i = super_pattern.get_harmony_i(onset)
            harmony_times = super_pattern.get_harmony_times(harmony_i)
            all_pitches_in_harmony = bass.get_all_ps_onset_between(
                harmony_times.start_time, harmony_times.end_time
            )
            foot_pc = er.get(harmony_i, "pc_chords")[FOOT]
            lowest_of_each_pc = er_misc_funcs.get_lowest_of_each_pc_in_set(
                all_pitches_in_harmony, tet=er.tet
            )

        if note.pitch % er.tet != foot_pc:
            continue

        if er.preserve_foot_in_bass == "all":
            er.bass_foot_times.append(onset)
            continue

        if lowest_of_each_pc[note.pitch % er.tet] == note.pitch:
            er.bass_foot_times.append(onset)

        # if er_misc_funcs.lowest_occurrence_of_pc_in_set(
        #     note.pitch, all_pitches_in_harmony, tet=er.tet
        # ):
        #     er.bass_foot_times.append(onset)


def make_initial_pattern(er, available_pitch_error):
    """Makes the basic pattern."""

    er.build_status_printer.reset_ip_attempt_count()
    er_rhythm.init_rhythms(er)
    for rep in itertools.count(start=1):
        for _ in range(er.initial_pattern_attempts):
            available_pitch_error.reset_inner_counts()
            er.build_status_printer.increment_ip_attempt()
            available_pitch_error.status()
            er_rhythm.rhythms_handler(er)
            er.initial_pattern_order = er_rhythm.get_onset_order(er)
            super_pattern = er_classes.Score(
                num_voices=er.num_voices,
                tet=er.tet,
                harmony_len=er.harmony_len,
                total_len=er.total_len,
                ranges=er.voice_ranges,
                time_sig=er.time_sig,
                existing_score=er.existing_score,
            )
            try:
                if attempt_initial_pattern(
                    er, super_pattern, available_pitch_error
                ):
                    success = True
                    break
            except er_exceptions.AvailablePitchMaterialsError:
                pass
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
        er.build_status_printer.reset_ip_attempt_count()

    if not success:
        raise available_pitch_error

    if er.preserve_foot_in_bass != "none":
        _get_bass_foot_times(er, super_pattern)

    return super_pattern


def transpose_foots(er, super_pattern):

    bass = super_pattern.voices[BASS]
    lowest_pitch = (
        er.voice_ranges[BASS][LOWEST_PITCH] - er.extend_bass_range_for_foots
    )
    harmony_times = er_classes.HarmonyTimes(0, 0, BASS)

    for note in bass:
        new_pitch = note.pitch - er.tet
        if new_pitch < lowest_pitch:
            continue

        if (
            harmony_times.end_time is not None
            and note.onset >= harmony_times.end_time
        ):
            harmony_i = super_pattern.get_harmony_i(note.onset)
            harmony_times = super_pattern.get_harmony_times(harmony_i)
            # harmony_dur = harmony_times.end_time - harmony_times.start_time
            all_pitches_in_harmony = bass.get_all_ps_onset_between(
                harmony_times.start_time, harmony_times.end_time
            )

            foot_pc = er.get(harmony_i, "pc_chords")[FOOT]
            lowest_pitch_in_harmony = min(all_pitches_in_harmony)
            lowest_of_each_pc = er_misc_funcs.get_lowest_of_each_pc_in_set(
                all_pitches_in_harmony, tet=er.tet
            )

        if note.pitch % er.tet != foot_pc:
            continue

        if lowest_pitch_in_harmony == note.pitch:
            continue

        if lowest_of_each_pc[note.pitch % er.tet] == note.pitch:
            note.pitch = new_pitch

        # if er_misc_funcs.lowest_occurrence_of_pc_in_set(
        #     note.pitch, all_pitches_in_harmony, tet=er.tet
        # ):
        #     note.pitch = new_pitch


def voice_lead_pattern(er, super_pattern, voice_lead_error):

    voice_lead_error.reset_inner_counts()

    if (
        er.allow_strict_voice_leading
        and er_vl_strict_and_flex.voice_lead_pattern_strictly(
            er, super_pattern, voice_lead_error, pattern_vl_i=er.num_voices
        )
    ):
        return True

    if (
        er.allow_flexible_voice_leading
        and er_vl_strict_and_flex.voice_lead_pattern_flexibly(
            er, super_pattern, voice_lead_error, pattern_vl_i=er.num_voices
        )
    ):
        return True

    return False


def make_super_pattern(er):
    """Makes the super pattern."""

    voice_lead_error = er_exceptions.VoiceLeadingError(er)
    available_pitch_error = er_exceptions.AvailablePitchMaterialsError(er)

    for rep in itertools.count(start=1):
        for _ in range(er.voice_leading_attempts):
            er.build_status_printer.increment_total_attempt_count()
            super_pattern = make_initial_pattern(er, available_pitch_error)
            if voice_lead_pattern(er, super_pattern, voice_lead_error):
                er.build_status_printer.success()
                success = True
                break
            er.build_status_printer.spin()
            er.check_time()
            voice_lead_error.status()

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

    if er.extend_bass_range_for_foots > 0:
        transpose_foots(er, super_pattern)

    complete_pattern(er, super_pattern)

    return super_pattern


def repeat_super_pattern(er, super_pattern, apply_to_existing_voices=False):
    """Repeats the super pattern the indicated number of times."""

    # First clear up any stray notes beyond the end of the pattern
    super_pattern.remove_passage(
        er.super_pattern_len,
        end_time=None,
        apply_to_existing_voices=apply_to_existing_voices,
    )

    if er.cont_rhythms == "none" or not er.super_pattern_reps_cont_var:
        repetition_start_time = er.super_pattern_len
        for _ in range(1, er.num_reps_super_pattern):
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
        num_onsets = len(voice)
        for onset_i in range(num_onsets):
            _, notes = voice.peekitem(onset_i)
            for note in notes:
                for rep_i in range(1, er.num_reps_super_pattern):
                    new_onset_i = onset_i + rep_i * num_onsets
                    new = note.copy()
                    new.onset, new.dur = rhythm.get_onset_and_dur(new_onset_i)
                    voice.add_note(new)

    if apply_to_existing_voices:
        for voice in super_pattern.existing_voices:
            repetition_start_time = er.super_pattern_len
            for _ in range(1, er.num_reps_super_pattern):
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
            start_time=start_time,
            end_time=end_time,
            apply_to_existing_voices=apply_to_existing_voices,
        )

        if er.transpose_intervals:
            transpose_interval += er.get(transpose_i, "transpose_intervals")
        else:
            transpose_interval += random.randrange(1, er.tet) * random.choice(
                (1, -1)
            )

        if er.cumulative_max_transpose_interval != 0:
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
        super_pattern.transpose(
            transpose_interval,
            er=er,
            max_interval=er.cumulative_max_transpose_interval,
            start_time=start_time,
            end_time=end_time,
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
        transpose_func = apply_specific_transpositions
    elif er.transpose_type == "generic":
        transpose_func = apply_generic_transpositions
    else:
        raise ValueError(
            "Transposition type not recognized.\n"
            "er.transpose_type should be either 'specific' "
            "or 'generic'"
        )
    transpose_func(
        er,
        super_pattern,
        end,
        apply_to_existing_voices=apply_to_existing_voices,
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
        # why apply_to_existing_voices=er.existing_voices_transpose
        # The name suggests that argument is meant to apply to *transposition*,
        # not repeating
        er,
        super_pattern,
        apply_to_existing_voices=er.existing_voices_transpose,
    )

    if not er.transpose_before_repeat:
        apply_transpositions(
            er,
            super_pattern,
            er.total_len,
            apply_to_existing_voices=er.existing_voices_transpose,
        )

    er_choirs.assign_choirs(er, super_pattern)


try:
    LINE_WIDTH = os.get_terminal_size().columns
except OSError:
    # Thrown when running pytest
    LINE_WIDTH = 80

# Constants for accessing voice ranges

LOWEST_PITCH = 0
HIGHEST_PITCH = 1

# Constants for accessing voices

BASS = 0

FOOT = 0


if __name__ == "__main__":
    pass
