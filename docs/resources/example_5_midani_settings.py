{
    "midi_fname": "examples/midi/example5.mid",
    "voice_settings": {
        0: {
            "bracket_settings": {"hlen": {"y_offset": 4},},
            "brackets": [
                (0.0, 2.0, "plen", "pattern_len = 4"),
                (2.0, 4.0, "plen", "", 2),
            ],
            "color_loop": 11,
        },
        1: {
            "bracket_settings": {"hlen": {"y_offset": 4},},
            "brackets": [
                (0.0, 0.75, "plen", "pattern_len = 1.5"),
                (0.75, 1.5, "plen", "", 2),
                (1.5, 2.0, "plen", "truncated"),
                (2.0, 2.75, "plen", "", 2),
                (3.5, 4.0, "plen", "", 2),
            ],
            "color_loop": 11,
        },
    },
    "brackets": [
        (0.0, 2.0, "hlen", "harmony_len = 4"),
        (2.0, 4.0, "hlen", "", 2),
    ],
    "channel_settings": {0: {"l_padding": 0.2, "h_padding": 0.2}},
}
