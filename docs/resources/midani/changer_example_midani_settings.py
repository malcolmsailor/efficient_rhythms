{
    "seed": 0,
    "frame_len": 30,
    "note_width": 0.95,
    "bg_colors": [(255, 255, 255, 255)],
    "connection_lines": False,
    # expects to be run by the makefile in the docs/ directory
    "default_bracket_settings": {"x_offset": 0.02, "text_size": 2.0},
    "voice_settings": {
        0: {
            "color_loop_var_amount": 164,
        },
        1: {
            "color_loop_var_amount": 128,
        },
        2: {
            "color_loop_var_amount": 112,
        },
        3: {
            "color": (128, 128, 128, 64),
            # "color": (128, 128, 128, 128),
            "connection_lines": False,
            "note_width": 1.0,
            "color_loop": None,
            # "con_line_offset_color": (255, 255, 255, 0),
            # "con_line_offset_prop": 0.5,
        },
        4: {
            "color": (128, 128, 128, 64),
        },
        5: {
            "color": (128, 128, 128, 64),
        },
        # 3: {"color": (128, 128, 128, 64),},
    },
    "voice_order_reverse": True,
    "duplicate_voice_settings": {3: (4, 5)},
    "resolution": (1280, 450),
}
