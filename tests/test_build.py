import efficient_rhythms.er_exceptions as er_exceptions
import efficient_rhythms.er_make_handler as er_make_handler
import efficient_rhythms.er_settings as er_settings


def test_build():
    base_settings = {
        "num_voices": 2,
        "num_harmonies": 4,
        "num_reps_super_pattern": 1,
        "harmony_len": 2,
        "seed": 0,
        "initial_pattern_attempts": 3,
        "voice_leading_attempts": 3,
        "_silent": True,
    }
    test_settings = [
        {"consonance_modulo": 1},
        {"tet": 1},
        {"tet": 1000},
        # TODO existing_voices
        {"time_sig": (3, 4)},
        {"voice_ranges": ((52, 64), (64, 76))},
        {"voice_ranges": ((52, 64), (64, 76)), "hard_bounds": ((52, 76),)},
        {"voice_order_str": "reverse"},
        {"allow_voice_crossings": False},
        # TODO scales_and_chords_specified_in_midi
        {"foot_pcs": 1, "interval_cycle": (3, 4)},
        {
            "voices_separate_tracks": False,
            "choirs_separate_tracks": False,
            "choirs_separate_channels": False,
            "write_program_changes": False,
            "humanize": False,
        },
        {"humanize_onset": 0.5, "humanize_dur": 0.5, "humanize_tuning": 0.5},
        {"tet": 31, "logic_type_pitch_bend": True},
        {
            "tet": 31,
            "integers_in_12_tet": True,
            "scales": ((0, 4, 8, 12, 16),),
            "chords": ((0, 8, 16),),
        },
        {"parallel_voice_leading": True},
        {"parallel_voice_leading": True, "parallel_direction": "up"},
        {"parallel_voice_leading": True, "parallel_direction": "down"},
        {"voice_lead_chord_tones": True},
        {"preserve_foot_in_bass": "lowest"},
        {"preserve_foot_in_bass": "all"},
        {"extend_bass_range_for_foots": 15},
        {"constrain_voice_leading_to_ranges": True},
        {"allow_flexible_voice_leading": True},
        {"allow_strict_voice_leading": False},
        {"vl_maintain_consonance": False},
        {"vl_maintain_limit_intervals": "all"},
        {"vl_maintain_limit_intervals": "none"},
        {"vl_maintain_forbidden_intervals": False},
        {"vl_maintain_prohibit_parallels": False},
        {"chord_tone_and_foot_disable": True},
        {"chord_tone_selection": False},
        {"chord_tone_prob_curve": "quadratic"},
        {"max_n_between_chord_tones": 0},
        {"min_prob_chord_tone": 0},
        {"min_prob_chord_tone": 1},
        {"try_to_force_non_chord_tones": True},
        {"len_to_force_chord_tone": 0, "scale_chord_tone_prob_by_dur": False},
        {"scale_chord_tone_neutral_dur": 0.1},
        {"scale_short_chord_tones_down": True},
        {"chord_tone_before_rests": 0.0},
        {"chord_tones_no_diss_treatment": True},
        {"force_chord_tone": "global_first_beat"},
        {"force_chord_tone": "global_first_note"},
        {"force_chord_tone": "first_beat"},
        {"force_chord_tone": "first_note"},
        {"chord_tones_sync_onset_in_all_voices": True},
        {"force_foot_in_bass": "global_first_beat"},
        {"force_foot_in_bass": "global_first_note"},
        {"force_foot_in_bass": "first_beat"},
        {"force_foot_in_bass": "first_note"},
        {"prefer_small_melodic_intervals": False},
        {"prefer_small_melodic_intervals_coefficient": 0.01},
        {"unison_weighted_as": 1},
        {"max_interval": 1},
        {"max_interval_for_non_chord_tones": 1},
        {"min_interval": 1},
        {"min_interval_for_non_chord_tones": 1},
        {"force_repeated_notes": True},
        {"max_repeated_notes": 0},
        {"max_repeated_notes": 10},
        {"max_alternations": 0},
        {"max_alternations": 1},
        {"pitch_loop": 1},
        {"pitch_loop": 2},
        {"hard_pitch_loop": True},
        {"prohibit_parallels": ()},
        {"prohibit_parallels": (0, 5, 7)},
        {"antiparallels": False},
        {"force_parallel_motion": True},
        {"consonance_treatment": "all_durs"},
        {"consonance_treatment": "none"},
        {"consonance_treatment": "all_durs", "consonance_type": "chordwise"},
        {"consonance_treatment": "all_onsets", "consonance_type": "chordwise"},
        {"min_dur_for_cons_treatment": 0},
        {"min_dur_for_cons_treatment": 0.25},
        {"forbidden_intervals": [0, 12, 19]},
        {"forbidden_interval_classes": [0, 7]},
        {"forbidden_intervals": [0, 12, 19], "forbidden_interval_modulo": 1},
        {"exclude_augmented_triad": False},
        {"consonances": (1, 2, 6, 10, 11)},
        {"invert_consonances": True},
        {
            "consonant_chords": ((0, 2, 4), (0, 5, 10)),
            "consonance_type": "chordwise",
        },
        {"consonance_type": "chordwise", "chord_octave_equi_type": "bass"},
        {"consonance_type": "chordwise", "chord_octave_equi_type": "order"},
        {"consonance_type": "chordwise", "chord_octave_equi_type": "none"},
        {"consonance_type": "chordwise", "chord_permit_doublings": "complete"},
        {"consonance_type": "chordwise", "chord_permit_doublings": "none"},
        {"rhythmic_unison": True},
        {"rhythmic_unison": ((0, 1),)},
        {"rhythmic_quasi_unison": True},
        {"rhythmic_quasi_unison": ((0,), (1, 2))},
        {"hocketing": True},
        {"hocketing": ((0, 1),)},
        {
            "rhythmic_quasi_unison": True,
            "rhythmic_quasi_unison_constrain": True,
        },
        # TODO cont_rhythms
        # TODO rhythms_specified_in_midi, rhythms_in_midi_reverse_voices
        {
            "pattern_len": 3,
            "onset_subdivision": 2 / 3,
            "comma_position": "anywhere",
        },
        {
            "pattern_len": 3,
            "onset_subdivision": 2 / 3,
            "comma_position": "beginning",
        },
        {
            "pattern_len": 3,
            "onset_subdivision": 2 / 3,
            "comma_position": "middle",
        },
        {"pattern_len": 3, "onset_subdivision": 2 / 3, "comma_position": 0},
        {"pattern_len": 3, "onset_subdivision": 2 / 3, "comma_position": 150},
        {"pattern_len": 3, "onset_subdivision": 2 / 3, "comma_position": 1},
        {"overlap": False},
        {"choirs": [0, 1, 2, 3]},
        {"choir_assignments": [3, 2, 1, 0]},
        {"randomly_distribute_between_choirs": True},
        {
            "randomly_distribute_between_choirs": True,
            "length_choir_segments": 0.25,
        },
        {"randomly_distribute_between_choirs": True, "length_choir_loop": 1},
        {"randomly_distribute_between_choirs": True, "length_choir_loop": 0},
        {"randomly_distribute_between_choirs": True, "length_choir_loop": 100},
        {
            "randomly_distribute_between_choirs": True,
            "choir_segments_dovetail": True,
        },
        {
            "randomly_distribute_between_choirs": True,
            "max_consec_seg_from_same_choir": 1,
        },
        {
            "randomly_distribute_between_choirs": True,
            "all_voices_from_different_choirs": True,
        },
        {
            "randomly_distribute_between_choirs": True,
            "each_choir_combination_only_once": True,
        },
        {
            "transpose": True,
            "transpose_len": 2,
            "transpose_before_repeat": True,
        },
        {"transpose": True, "transpose_type": "generic"},
        {"transpose": True, "transpose_intervals": 2},
        {"transpose": True, "transpose_intervals": (2, 5)},
        {"transpose": True, "cumulative_max_transpose_interval": 0},
        {"tempo": [80, 120], "tempo_len": 2},
        {"tempo": [80, 120], "tempo_len": (1, 1.5)},
        {"tempo": (), "tempo_len": 1},
        {"tempo_bounds": (96, 112), "tempo_len": 1, "tempo": ()},
    ]
    for test_setting in test_settings:
        settings = base_settings.copy()
        settings.update(test_setting)
        er = er_settings.get_settings(settings)
        try:
            er_make_handler.make_super_pattern(er)
        except (
            er_exceptions.VoiceLeadingError,
            er_exceptions.AvailablePitchMaterialsError,
        ):
            # TODO investigate these
            pass


if __name__ == "__main__":
    test_build()
