import er_make2
import er_misc_funcs
import er_notes


def apply_voice_leading(
    er,
    super_pattern,
    prev_note,
    first_note,
    new_attack_time,
    new_dur,
    voice_i,
    new_harmony_i,
    prev_pc_scale,
    voice_leading,
    new_notes,
    voice_lead_error,
):
    # MAYBE something about the number of arguments for this function?
    # LONGTERM use PossibleNote class

    def _try_to_force_root():
        root = er_make2.get_root_to_force2(er, voice_i, new_harmony_i)
        if root is not None:
            new_pitch = root
            new_note = er_notes.Note(new_pitch, new_attack_time, new_dur)
            return new_note
        return None

    def _fail():
        return None, (prev_pitch_index, voice_leading_interval)

    if (
        first_note
        and not er.bass_in_existing_voice
        and voice_i == 0
        and er.force_root_in_bass in ("first_beat", "first_note")
    ):
        new_note = _try_to_force_root()
        if new_note:
            return new_note, None

    if er.force_repeated_notes:
        repeated_pitch = er_make2.get_repeated_pitch(new_notes, new_attack_time)
        if repeated_pitch is not None:
            new_pitch = repeated_pitch
            new_note = er_notes.Note(new_pitch, new_attack_time, new_dur)
            return new_note, None

    if (
        er.preserve_root_in_bass != "none"
        and (not er.bass_in_existing_voice)
        and voice_i == 0
    ):
        pattern_len = er.pattern_len[voice_i]
        if new_attack_time % pattern_len in er.bass_root_times:
            new_note = _try_to_force_root()
            if new_note:
                return new_note, None

    other_voices = er_misc_funcs.get_prev_voice_indices(
        super_pattern, new_attack_time, new_dur
    )

    prev_pitch = prev_note.pitch
    prev_pitch_index = prev_pc_scale.index(prev_pitch % er.tet)
    voice_leading_interval = voice_leading[prev_pitch_index]

    new_pitch = prev_pitch + voice_leading_interval

    if er.constrain_voice_leading_to_ranges:
        min_pitch, max_pitch = er.get(voice_i, "voice_ranges")
        if min_pitch > new_pitch or max_pitch < new_pitch:
            voice_lead_error.temp_failure_counter.out_of_range += 1
            return _fail()

    if er.parallel_voice_leading:
        new_note = er_notes.Note(new_pitch, new_attack_time, new_dur)
        return new_note, (prev_pitch_index, voice_leading_interval)

    if er.vl_maintain_forbidden_intervals:
        if not er_make2.check_harmonic_intervals(
            er,
            super_pattern,
            new_pitch,
            new_attack_time,
            new_dur,
            voice_i,
            other_voices=other_voices,
        ):
            voice_lead_error.temp_failure_counter.check_intervals += 1
            return _fail()
    if er.vl_maintain_consonance:
        if er.get(
            voice_i, "chord_tones_no_diss_treatment"
        ) and er_make2.check_if_chord_tone(
            er, super_pattern, new_attack_time, new_pitch
        ):
            pass
        elif new_dur < er.get(voice_i, "min_dur_for_cons_treatment"):
            pass
        elif not er_make2.check_consonance(
            er, super_pattern, new_pitch, new_attack_time, new_dur, voice_i
        ):
            voice_lead_error.temp_failure_counter.check_consonance += 1
            return _fail()

    if er.vl_maintain_limit_intervals:
        try:
            last_attack = max(new_notes.data)
            last_pitch = new_notes[last_attack][0].pitch
        except ValueError:
            last_attack = max(super_pattern.voices[voice_i].data)
            last_pitch = super_pattern.voices[voice_i][last_attack][0].pitch

        chord_tone = er_make2.check_if_chord_tone(
            er, super_pattern, last_attack, last_pitch
        )

        max_interval, min_interval = er_make2.get_limiting_intervals(
            er, voice_i, chord_tone
        )

        if not er_make2.check_melodic_intervals(
            er, new_pitch, last_pitch, max_interval, min_interval, new_harmony_i
        ):
            voice_lead_error.temp_failure_counter.limit_intervals += 1
            return _fail()

    new_note = er_notes.Note(new_pitch, new_attack_time, new_dur)
    return new_note, (prev_pitch_index, voice_leading_interval)
