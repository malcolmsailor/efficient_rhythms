{
    # NB MARIMBA and VIBRAPHONE patches are missing from freepats, used by
    #   pygame in Ubuntu (and possibly with other Linux distributions),
    #   so those voices do not play back
    "choirs": ("PIANO", "VIBRAPHONE", "ELECTRIC_PIANO"),
    "num_reps_super_pattern": 4,
    "seed": 2,
    "pattern_len": 4,
    "consonance_treatment": "none",
    "harmony_len": 4,
    "output_path": "EFFRHY/docs/examples/midi/",
    "overwrite": True,
    "force_foot_in_bass": "first_beat",
    "extend_bass_range_for_foots": 7,
    "voice_lead_chord_tones": True,
    "onset_density": 0.7,
    "dur_density": 0.7,
    "unison_weighted_as": "SECOND",
    "randomly_distribute_between_choirs": True,
    "length_choir_segments": 1 / 4,
    "tempo": 132,
    "choirs_separate_tracks": False,
    # overriding web defaults
    "max_consec_seg_from_same_choir": 0,
    "preserve_foot_in_bass": "none",
    "scales": ["DIATONIC_SCALE"],
    "chords": ["MAJOR_TRIAD"],
}
