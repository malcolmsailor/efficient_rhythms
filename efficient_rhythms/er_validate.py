from . import er_exceptions


def _same_cardinality(pitch_seqs):
    n = len(pitch_seqs[0])
    for pitch_seq in pitch_seqs[1:]:
        assert len(pitch_seq) == n


def _check_chords_and_scale_card(er, errors):
    try:
        _same_cardinality(er.chords)
    except AssertionError:
        errors.append("All `chords` must have the same number of pitches.")
    try:
        _same_cardinality(er.scales)
    except AssertionError:
        errors.append("All `scales` must have the same number of pitches.")


def _check_chords_and_scales_consistent(er, errors):
    for chord_i, chord in enumerate(er.pc_chords):
        scale = er.get(chord_i, "pc_scales")
        for pc in chord:
            try:
                assert pc in scale
            except AssertionError:
                errors.append(
                    f"Inconsistent chords and scales: pitch-class {pc} is in "
                    f"chord {chord_i} (zero-indexed) but not in "
                    f"scale {chord_i % len(er.pc_scales)} (zero-indexed). "
                    "Every scale must be a superset of the corresponding chord."
                )


def _misc_errors(er, errors):
    if er.len_to_force_chord_tone == 0 and er.scale_chord_tone_prob_by_dur:
        errors.append(
            "If `scale_chord_tone_prob_by_dur` is True, then "
            "`len_to_force_chord_tone` must be non-zero."
        )
    if len(er.voice_ranges) < er.num_voices:
        errors.append(
            "`voice_ranges` must be at least as long as `num_voices`."
        )


def _choir_errors(er, errors):
    if not er.choirs:
        errors.append("`choirs` cannot be empty.")
    if (
        not er.randomly_distribute_between_choirs
        and max(er.choir_assignments) > len(er.choirs) - 1
    ):
        errors.append(
            "`choir_assignments` assigns a voice to choir "
            f"{max(er.choir_assignments)}, but this voice does not exist. "
            f"The maximum index for `choirs` is {len(er.choirs) - 1}."
        )


def validate_settings(er):
    # (for now) at least, this validation is highly incomplete, and targets
    # just a few important settings that a user is likely to get wrong (e.g.,
    # not all chords having the same number of members).
    #
    # See er_web for a way of making the validation more complete.
    validation_errors = []
    _check_chords_and_scale_card(er, validation_errors)
    _check_chords_and_scales_consistent(er, validation_errors)
    _choir_errors(er, validation_errors)
    _misc_errors(er, validation_errors)
    if validation_errors:
        breakpoint()
        raise er_exceptions.ErSettingsError("\n".join(validation_errors))
