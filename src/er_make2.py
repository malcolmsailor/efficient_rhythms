import warnings

import src.er_misc_funcs as er_misc_funcs


def check_parallel_intervals(
    er, super_pattern, new_pitch, prev_pitch, new_onset, voice_i
):
    # LONGTERM make this work with `existing_voices?`
    for other_voice in super_pattern.voices:
        if other_voice.voice_i == voice_i:
            continue
        try:
            other_voice[new_onset]
        except KeyError:
            continue
        # LONGTERM should we stop at rests?
        other_prev_pitch, other_pitch = other_voice.get_last_n_pitches(
            2, new_onset
        )
        if -1 in (other_prev_pitch, other_pitch):
            continue
        if other_prev_pitch == other_pitch:
            # We don't care about unisons
            continue
        prev_interval = (prev_pitch - other_prev_pitch) % er.tet
        if prev_interval not in er.prohibit_parallels:
            continue
        new_interval = (new_pitch - other_pitch) % er.tet
        if new_interval == prev_interval:
            return False
    return True


def get_foot_to_force(er, voice_i, harmony_i):
    foot_pc = er.get(harmony_i, "pc_chords")[0]
    foot_pitches = er_misc_funcs.get_all_pitches_in_range(
        foot_pc, er.voice_ranges[voice_i], er.tet
    )
    if not foot_pitches:
        if er.already_warned["force_foot"][harmony_i] == 0:
            warnings.warn(
                f"Unable to force foot in bass on harmony {harmony_i}.\n"
                "Try increasing voice range."
            )
            er.already_warned["force_foot"][harmony_i] += 1
        return None
    return min(foot_pitches)


def get_repeated_pitch(poss_note, min_onset=0):
    # prev_pitch = poss_note.voice.get_prev_pitch(
    #     poss_note.onset, min_onset=min_onset
    # )
    if poss_note.onset < min_onset or poss_note.prev_pitch < 0:
        return None
    return poss_note.prev_pitch


# LONGTERM consolidate this and previous function!
def get_repeated_pitch2(voice, onset, min_onset=0):
    prev_pitch = voice.get_prev_pitch(onset, min_onset=min_onset)
    if prev_pitch < 0:
        return None
    return prev_pitch


def check_harmonic_intervals(
    er, score, pitch, onset, dur, voice_i, other_voices=None
):
    # LONGTERM poss_note

    other_pitches = score.get_all_ps_sounding_in_dur(
        onset, dur, voices=other_voices
    )

    if not other_pitches:
        return True

    forbidden_interval_modulo = er.get(voice_i, "forbidden_interval_modulo")

    if (
        forbidden_interval_modulo
        != [
            0,
        ]
        and er_misc_funcs.check_modulo(onset, forbidden_interval_modulo) != 0
    ):
        return True

    for forbidden_interval_class in er.forbidden_interval_classes:
        if er_misc_funcs.check_interval_class(
            forbidden_interval_class, pitch, other_pitches, tet=er.tet
        ):
            return False

    for forbidden_interval in er.forbidden_intervals:
        if er_misc_funcs.check_interval(
            forbidden_interval, pitch, other_pitches
        ):
            return False

    return True


def check_if_chord_tone(er, super_pattern, onset, pitch):

    harmony_i = super_pattern.get_harmony_i(onset)
    pc_chord = er.get(harmony_i, "pc_chords")
    if pitch % er.tet in pc_chord:
        return True

    return False


def check_consonance(er, super_pattern, pitch, onset, dur, voice_i):
    """Checks whether the given pitch fulfills the consonance parameters."""
    # LONGTERM use possible note class (but first update voice-leading functions.)

    if er.consonance_treatment == "none":
        return True

    consonance_modulo, min_dur = er.get(
        voice_i, "consonance_modulo", "min_dur_for_cons_treatment"
    )
    if (
        consonance_modulo
        != [
            0,
        ]
        and er_misc_funcs.check_modulo(onset, consonance_modulo) != 0
    ):
        # MAYBE comma here, to allow for very close onsets?
        return True

    if er.consonance_treatment == "all_durs":
        other_pitches = super_pattern.get_all_ps_sounding_in_dur(
            onset, dur, min_dur=min_dur
        )

    else:
        other_pitches = super_pattern.get_simultaneously_onset_ps(
            onset, min_dur=min_dur
        )

    if not other_pitches:
        return True

    pitches = other_pitches + [
        pitch,
    ]

    if er.consonance_type == "pairwise":

        return er_misc_funcs.pitches_consonant(
            pitches,
            er.consonances,
            tet=er.tet,
            augmented_triad=er.exclude_augmented_triad,
        )

    # Otherwise consonance_type is "chordwise"

    return er_misc_funcs.chord_in_list(
        pitches,
        er.consonant_chords,
        tet=er.tet,
        octave_equi=er.chord_octave_equi_type,
        permit_doublings=er.chord_permit_doublings,
    )


def get_limiting_intervals(er, voice_i, chord_tone=False):
    if er.get(voice_i, "max_interval_for_non_chord_tones") and not chord_tone:
        max_interval = er.get(voice_i, "max_interval_for_non_chord_tones")
    else:
        max_interval = er.get(voice_i, "max_interval")

    if er.get(voice_i, "min_interval_for_non_chord_tones") and not chord_tone:
        min_interval = er.get(voice_i, "min_interval_for_non_chord_tones")
    else:
        min_interval = er.get(voice_i, "min_interval")
    return max_interval, min_interval


def check_melodic_intervals(
    er, new_p, prev_pitch, max_interval, min_interval, harmony_i
):
    """
    Args:
        new_p: an int, or a sequence of ints.
        prev_pitch: int.
        max_interval, min_interval: numbers. See ERSettings documentation
            for more detail.
        harmony_i: int.

    Returns:
        a list (possibly empty) of the pitch or pitches from new_p that are
        within the range specified by max_interval and min_interval

    """

    # max_rest_dur = er.get(
    #     poss_note.voice_i, "max_rest_dur_for_interval_limits")

    def _sub_check_mel_ints(item):
        if isinstance(item, (list, tuple)):
            return [
                sub_item for sub_item in item if _sub_check_mel_ints(sub_item)
            ]
        if max_interval is not None:
            if max_interval <= 0:
                if abs(item - prev_pitch) > -max_interval:
                    return None
            elif max_interval > 0:
                generic_interval = er_misc_funcs.get_generic_interval(
                    er, harmony_i, item, prev_pitch
                )
                if abs(generic_interval) > max_interval:
                    return None
        if min_interval is None:
            # if min_interval == 0:
            return item
        if min_interval <= 0:
            if abs(item - prev_pitch) >= -min_interval:
                return item
        elif min_interval > 0:
            try:
                generic_interval
            except UnboundLocalError:
                generic_interval = er_misc_funcs.get_generic_interval(
                    er, harmony_i, item, prev_pitch
                )
            if abs(generic_interval) >= min_interval:
                return item
        return None

    if isinstance(new_p, int):
        new_p = [new_p]

    if max_interval == 0 and min_interval == 0:
        return new_p

    return _sub_check_mel_ints(new_p)

    # # If max_interval < 0, then treat its absolute
    # # value as a specific interval.
    # if max_interval < 0:
    #     out = [pitch for pitch in new_p
    #            if abs(pitch - prev_pitch) <= abs(max_interval)]
    # # Otherwise, if max_interval > 0, then treat it as a
    # # generic interval.
    # elif max_interval > 0:
    #     out = []
    #     for sub_new_p in new_p:
    #         sub_out = []
    #         for pitch in sub_new_p:
    #             generic_interval = er_misc_funcs.get_generic_interval(
    #                 er, harmony_i, pitch, prev_pitch)
    #             if abs(generic_interval) <= max_interval:
    #                 sub_out.append(pitch)
    #         out.append(sub_out)
    #
    # else:
    #     out = new_p
    #
    # if min_interval == 0:
    #     return out
    #
    # if min_interval < 0:
    #     return [pitch for pitch in out
    #             if abs(pitch - prev_pitch) >= abs(min_interval)]
    #
    # out2 = []
    # for sub_new_p in out:
    #     sub_out = []
    #     for pitch in sub_new_p:
    #         generic_interval = er_misc_funcs.get_generic_interval(
    #             er, harmony_i, pitch, prev_pitch)
    #         if abs(generic_interval) >= min_interval:
    #             sub_out.append(pitch)
    #     out2.append(sub_out)
    #
    # return out2
