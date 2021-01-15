# illustrates different values for pattern_len, with truncate_patterns = True
# Note the permissive settings voice_lead_chord_tones = False and
# consonance_treatment = "none"
{
    "seed": 2,
    "pattern_len": [1.5, 4],
    "truncate_patterns": True,
    "num_harmonies": 4,
    "harmony_len": 4,
    "num_voices": 2,
    "root_pcs": [0],
    "interval_cycle": 3,
    "attack_density": 0.7,
    "prohibit_parallels": [0],
    "forbidden_interval_classes": [0],
    "max_repeated_notes": 0,
    "force_root_in_bass": "global_first_beat",
    "consonance_treatment": "none",
    "voice_lead_chord_tones": False,
    "hocketing": True,
    "max_interval": 4,
    "overlap": False,
    "output_path": "examples/midi/example5.mid",
    "overwrite": True,
}
