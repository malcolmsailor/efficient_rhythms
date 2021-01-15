{
    # Shared among all example midani settings
    "midi_fname": "examples/midi/example6.mid",
    "seed": 0,
    "note_width": 0.95,
    "max_connection_line_interval": 24,
    "bg_colors": [(255, 255, 255, 255)],
    "highlight_strength": 0,
    "max_flutter_size": 0,
    "min_flutter_size": 0,
    "bounce_size": 0,
    "connection_line_end_offset": 0.1,
    "connection_line_start_offset": 0.1,
    "frame_len": 4.3,
    "voice_settings": {0: {"shadow_strength": 0.3}},
    "end_time": 6,
    "output_dirname": "docs/resources/pngs/",
    "default_bracket_settings": {"x_offset": 0.02, "text_size": 2.0},
    "voice_settings": {
        0: {
            "bracket_settings": {
                "plen": {"color": (0, 0, 0)},
                "hlen": {"color": (72, 115, 134), "y_offset": 4},
            },
            "default_bracket_settings": {"above": True, "text_y_offset": 0.7},
            "brackets": [
                (0.0, 2.0, "plen", "pattern_len = 4"),
                (2.0, 4.0, "plen", "", 2),
            ],
            "color_loop": 11,
            "color_loop_var_amount": 164,
        },
        1: {
            "bracket_settings": {
                "plen": {"color": (0, 0, 0)},
                "hlen": {"color": (72, 115, 134), "y_offset": 4},
            },
            "default_bracket_settings": {"text_y_offset": 0.3},
            "brackets": [
                (0.0, 0.75, "plen", "pattern_len = 1.5"),
                (0.75, 1.5, "plen", ""),
                (1.5, 2.25, "plen", "not truncated!"),
                (2.25, 3.0, "plen", "", 0.75),
            ],
            "color_loop": 4,
            "color_loop_var_amount": 128,
        },
    },
    "bracket_settings": {},
    "brackets": [
        (0.0, 2.0, "hlen", "harmony_len = 4"),
        (2.0, 4.0, "hlen", "", 2),
    ],
    "channel_settings": {0: {"l_padding": 0.2, "h_padding": 0.2}},
}
