{
    "midi_fname": ["examples/midi/example2.mid",],
    "color_loop": 12,
    "voice_settings": {
        0: {
            "bracket_settings": {
                "plen": {"y_offset": 4,},
                "hlen": {"y_offset": 8,},
            },
        },
        1: {
            "bracket_settings": {
                "plen": {"y_offset": 4,},
                "hlen": {"y_offset": 8,},
            },
        },
    },
    "brackets": [
        (0.0, 2.0, "plen", "pattern_len = 4"),
        (2.0, 4.0, "plen", "", 2),
        (0.0, 1.0, "rlen", "rhythm_len = 2"),
        (1.0, 2.0, "rlen", "", 1),
        (0.0, 2.0, "hlen", "harmony_len = 4"),
        (2.0, 4.0, "hlen", "", 2),
    ],
    "channel_settings": {0: {"l_padding": 0.25, "h_padding": 0.25}},
}
