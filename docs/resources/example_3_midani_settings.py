{
    # Shared among all example midani settings
    "midi_fname": "examples/midi/example3.mid",
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
    # Specific to this file
    "voice_settings": {
        0: {
            "bracket_settings": {
                "rlen": {"color": (126, 145, 139),},
                "plen": {"color": (0, 0, 0), "y_offset": 4,},
                "hlen": {"color": (72, 115, 134), "y_offset": 8,},
            },
            "default_bracket_settings": {"above": True, "text_y_offset": 0.7},
            "color_loop_var_amount": 164,
            "color_loop": 13,
        },
        1: {
            "bracket_settings": {
                "rlen": {"color": (126, 145, 139)},
                "plen": {"color": (0, 0, 0), "y_offset": 4,},
                "hlen": {"color": (72, 115, 134), "y_offset": 8,},
            },
            "default_bracket_settings": {"text_y_offset": 0.3,},
            "color_loop_var_amount": 128,
            "color_loop": 11,
        },
    },
    "brackets": [
        (0.0, 2.0, "plen", "pattern_len = 4"),
        (2.0, 4.0, "plen", "", 2),
        (0.0, 0.75, "rlen", "rhythm_len = 1.5"),
        (0.75, 1.5, "rlen", "", 2),
        (1.5, 2.0, "rlen", "truncated"),
        (2.0, 2.75, "rlen", "", 2),
        (3.5, 4.0, "rlen", "", 2),
        (0.0, 2.0, "hlen", "harmony_len = 4"),
        (2.0, 4.0, "hlen", "", 2),
    ],
    "channel_settings": {0: {"l_padding": 0.25, "h_padding": 0.25}},
}
