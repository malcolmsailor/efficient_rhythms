{
    "seed": 0,
    "note_width": 0.95,
    "max_connection_line_interval": 24,
    "bg_colors": [(255, 255, 255, 255)],
    "connection_line_end_offset": 0.1,
    "connection_line_start_offset": 0.1,
    # expects to be run by the makefile in the docs/ directory
    "default_bracket_settings": {"x_offset": 0.02, "text_size": 2.0},
    "voice_settings": {
        0: {
            "bracket_settings": {
                "rlen": {"color": (126, 145, 139),},
                "plen": {"color": (0, 0, 0)},
                "hlen": {"color": (72, 115, 134)},
            },
            "default_bracket_settings": {"above": True, "text_y_offset": 0.7},
            "color_loop_var_amount": 164,
        },
        1: {
            "bracket_settings": {
                "rlen": {"color": (126, 145, 139)},
                "plen": {"color": (0, 0, 0)},
                "hlen": {"color": (72, 115, 134)},
            },
            "default_bracket_settings": {"text_y_offset": 0.3},
            "color_loop_var_amount": 128,
        },
        # 2: {
        #     "color": (128, 128, 128, 64),
        #     # "color": (128, 128, 128, 128),
        #     "connection_lines": False,
        #     "note_width": 1.0,
        #     "color_loop": None,
        #     # "con_line_offset_color": (255, 255, 255, 0),
        #     # "con_line_offset_prop": 0.5,
        # },
        # 3: {"color": (128, 128, 128, 64),},
    },
    "voice_order_reverse": True,
    "duplicate_voice_settings": {2: (3,)},
}
