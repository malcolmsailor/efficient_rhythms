import src.er_make2 as er_make2
import src.er_misc_funcs as er_misc_funcs
import src.er_classes as er_classes


def apply_voice_leading(
    er,
    score,
    prev_note,
    first_note,
    new_onset,
    new_dur,
    voice_i,
    new_harmony_i,
    prev_harmony_i,
    prev_pc_scale,
    voice_leading,
    new_notes,
    voice_lead_error,
):
    # MAYBE something about the number of arguments for this function?
    # LONGTERM use PossibleNote class

    def _try_to_force_foot():
        foot = er_make2.get_foot_to_force(er, voice_i, new_harmony_i)
        if foot is not None:
            new_pitch = foot
            new_note = er_classes.Note(new_pitch, new_onset, new_dur)
            return new_note
        return None

    def _fail():
        return None, (prev_pitch_index, voice_leading_interval)

    if (
        first_note
        and not er.bass_in_existing_voice
        and voice_i == 0
        and er.force_foot_in_bass in ("first_beat", "first_note")
    ):
        new_note = _try_to_force_foot()
        if new_note:
            return new_note, None

    if er.force_repeated_notes:
        # TODO consolidate get_repeated_pitch2 with get_repeated_pitch
        # or at least rename it?
        repeated_pitch = er_make2.get_repeated_pitch2(new_notes, new_onset)
        if repeated_pitch is not None:
            new_pitch = repeated_pitch
            new_note = er_classes.Note(new_pitch, new_onset, new_dur)
            return new_note, None

    if (
        er.preserve_foot_in_bass != "none"
        and (not er.bass_in_existing_voice)
        and voice_i == 0
    ):
        pattern_len = er.pattern_len[voice_i]
        if new_onset % pattern_len in er.bass_foot_times:
            new_note = _try_to_force_foot()
            if new_note:
                return new_note, None

    other_voices = er_misc_funcs.get_prev_voice_indices(
        score, new_onset, new_dur
    )

    prev_pitch = prev_note.pitch
    prev_pitch_index = prev_pc_scale.index(prev_pitch % er.tet)
    voice_leading_interval = voice_leading[prev_pitch_index]

    new_pitch = prev_pitch + voice_leading_interval

    if er.constrain_voice_leading_to_ranges:
        min_pitch, max_pitch = er.get(voice_i, "voice_ranges")
        if min_pitch > new_pitch or max_pitch < new_pitch:
            voice_lead_error.out_of_range()
            return _fail()

    # TODO warn if hard_bounds less than an octave
    hard_bounds = er.get(voice_i, "hard_bounds")
    while new_pitch < hard_bounds[0]:
        new_pitch += er.tet
    while new_pitch > hard_bounds[1]:
        new_pitch -= er.tet

    if er.parallel_voice_leading:
        new_note = er_classes.Note(new_pitch, new_onset, new_dur)
        return new_note, (prev_pitch_index, voice_leading_interval)

    if er.vl_maintain_prohibit_parallels:
        if not er_make2.check_parallel_intervals(
            er, score, new_pitch, prev_pitch, new_onset, voice_i
        ):
            voice_lead_error.parallel_intervals()
            return _fail()

    if er.vl_maintain_forbidden_intervals:
        if not er_make2.check_harmonic_intervals(
            er,
            score,
            new_pitch,
            new_onset,
            new_dur,
            voice_i,
            other_voices=other_voices,
        ):
            voice_lead_error.check_intervals()
            return _fail()
    if er.vl_maintain_consonance:
        if er.get(
            voice_i, "chord_tones_no_diss_treatment"
        ) and er_make2.check_if_chord_tone(er, score, new_onset, new_pitch):
            pass
        elif new_dur < er.get(voice_i, "min_dur_for_cons_treatment"):
            pass
        elif not er_make2.check_consonance(
            er, score, new_pitch, new_onset, new_dur, voice_i
        ):
            voice_lead_error.check_consonance()
            return _fail()

    if er.vl_maintain_limit_intervals == "all" or (
        er.vl_maintain_limit_intervals != "none"
        and new_harmony_i != prev_harmony_i
    ):
        try:
            last_onset, last_notes = new_notes.last_attack_and_notes
        except IndexError:
            # raised when new_notes is empty
            last_onset, last_notes = score.voices[voice_i].last_attack_and_notes
        last_pitch = last_notes[-1].pitch

        chord_tone = er_make2.check_if_chord_tone(
            er, score, last_onset, last_pitch
        )

        max_interval, min_interval = er_make2.get_limiting_intervals(
            er, voice_i, chord_tone
        )
        if not er_make2.check_melodic_intervals(
            er, new_pitch, last_pitch, max_interval, min_interval, new_harmony_i
        ):
            voice_lead_error.limit_intervals()

            return _fail()

    new_note = er_classes.Note(new_pitch, new_onset, new_dur)
    return new_note, (prev_pitch_index, voice_leading_interval)
