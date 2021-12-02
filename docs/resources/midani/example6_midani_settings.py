{
    "midi_fname": "examples/midi/example6.mid",
    "voice_settings": {
        0: {
            "bracket_settings": {
                "hlen": {"y_offset": 4},
            },
            "brackets": [
                (0.0, 2.0, "plen", "pattern_len = 4"),
                (2.0, 4.0, "plen", "", 2),
            ],
            "color_loop": 11,
        },
        1: {
            "bracket_settings": {
                "hlen": {"y_offset": 4},
            },
            "brackets": [
                (0.0, 0.75, "plen", "pattern_len = 1.5"),
                (0.75, 1.5, "plen", ""),
                (1.5, 2.25, "plen", "not truncated!"),
                (2.25, 3.0, "plen", "", 0.75),
            ],
            "color_loop": 4,
        },
    },
    "brackets": [
        (0.0, 2.0, "hlen", "harmony_len = 4"),
        (2.0, 4.0, "hlen", "", 2),
    ],
    "channel_settings": {0: {"l_padding": 0.2, "h_padding": 0.2}},
}
