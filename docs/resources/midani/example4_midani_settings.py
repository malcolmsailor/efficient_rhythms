{
    "midi_fname": "examples/midi/example4.mid",
    "voice_settings": {
        0: {
            "bracket_settings": {
                "plen": {"y_offset": 4,},
                "hlen": {"y_offset": 8,},
            },
            "brackets": [
                (0.0, 1.0, "rlen", "rhythm_len = 2"),
                (1.0, 2.0, "rlen", "", 1.0),
            ],
            "color_loop": 14,
        },
        1: {
            "bracket_settings": {
                "plen": {"y_offset": 4,},
                "hlen": {"y_offset": 8,},
            },
            "brackets": [
                (0.0, 0.75, "rlen", "rhythm_len = 1.5"),
                (0.75, 1.5, "rlen", "", 2),
                (1.5, 2.0, "rlen", "truncated"),
                (2.0, 2.75, "rlen", "", 2),
                (3.5, 4.0, "rlen", "", 2),
            ],
            "color_loop": 12,
        },
    },
    "channel_settings": {0: {"l_padding": 0.25, "h_padding": 0.25}},
    "brackets": [
        (0.0, 2.0, "plen", "pattern_len = 4"),
        (2.0, 4.0, "plen", "", 2),
        (0.0, 2.0, "hlen", "harmony_len = 4"),
        (2.0, 4.0, "hlen", "", 2),
    ],
}
