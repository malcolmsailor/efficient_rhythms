# TODO rename this file?

import os

import numpy as np

import efficient_rhythms.er_constants as er_constants
import efficient_rhythms.er_settings as er_settings

SCRIPT_DIR = os.path.dirname((os.path.realpath(__file__)))


def test_process_pattern_vl_order():
    # LONGTERM is there a way to redirect stdout and stderr while running
    #   the tests?
    pattern_lens_list = [(2.5, 3, 3.5, 4), (2, 3, 5)]
    for pattern_lens in pattern_lens_list:
        for truncate in (True, False):
            settingsdict = {
                "num_voices": len(pattern_lens),
                "tet": 12,
                "pattern_len": pattern_lens,
                "truncate_patterns": truncate,
            }
            er = er_settings.get_settings(settingsdict)
            for item in er.pattern_vl_order:
                voice_i = item.voice_i
                pattern_len = pattern_lens[voice_i]
                modulo = max(pattern_lens) if truncate else pattern_len
                start_time = item.start_time
                while item._prev is not None:
                    item = item._prev
                    assert item.voice_i == voice_i, "item.voice_i != voice_i"
                    try:
                        assert (
                            item.start_time % modulo == start_time % modulo
                        ), "item.start_time % modulo != start_time % modulo"
                    except AssertionError:
                        assert (
                            item.start_time < modulo
                        ), "item.start_time >= modulo"

                assert item.start_time == 0, "item.start_time != 0"


def test_read_in_settings():
    result = er_settings.read_in_settings(
        [
            os.path.join(
                SCRIPT_DIR, "test_input/test_read_in_settings_merge1.py"
            ),
            os.path.join(
                SCRIPT_DIR, "test_input/test_read_in_settings_merge2.py"
            ),
        ],
        dict,
    )
    assert result["foo"] == 2, 'result["foo"] != 2'
    assert result["bar"] == 1, 'result["bar"] != 1'
    assert result["raboof"]["foo"] == 1, 'result["raboof"]["foo"] != 1'
    assert result["raboof"]["bar"] == 2, 'result["raboof"]["bar"] != 2'
    assert result["oofrab"]["foo"] == 2, 'result["oofrab"]["foo"] != 2'


def test_pitch_constants():
    result = er_settings.read_in_settings(
        [
            os.path.join(SCRIPT_DIR, "test_settings/test_er_constants1.py"),
        ],
        dict,
    )
    assert isinstance(
        result["scales"][0], np.ndarray
    ), 'not isinstance(result["scales"][0], np.ndarray)'


# TODO fix this test
def test_replace_pitch_constants():
    return
    # attr_name, constants, translated value
    tests = [
        (
            "foot_pcs",
            ("B", "B#", "Bb", "B##", "Bbb", "B_SHARP", "B_SHARP_SHARP"),
            [
                er_constants.B,
                er_constants.B * er_constants.SHARP,
                er_constants.B * er_constants.FLAT,
                er_constants.B * er_constants.SHARP * er_constants.SHARP,
                er_constants.B * er_constants.FLAT * er_constants.FLAT,
                er_constants.B * er_constants.SHARP,
                er_constants.B * er_constants.SHARP * er_constants.SHARP,
            ],
        ),
        (
            "voice_ranges",
            "CONTIGUOUS_OCTAVES * C * OCTAVE2",
            er_constants.CONTIGUOUS_OCTAVES
            * er_constants.C
            * er_constants.OCTAVE2,
        ),
        (
            "chords",
            ("MAJOR_TRIAD", "MINOR_TRIAD * D", "MAJOR_63 * E", "MINOR_64 * A"),
            [
                er_constants.MAJOR_TRIAD,
                er_constants.MINOR_TRIAD * er_constants.D,
                er_constants.MAJOR_63 * er_constants.E,
                er_constants.MINOR_64 * er_constants.A,
            ],
        ),
        (
            "unison_weighted_as",
            "GENERIC_UNISON",
            er_constants.GENERIC_UNISON,
        ),
        (
            "max_interval_for_non_chord_tones",
            "-OCTAVE",
            -1 * er_constants.OCTAVE,
        ),
        (
            "min_interval_for_non_chord_tones",
            "-MINOR_SECOND",
            -1 * er_constants.MINOR_2ND,
        ),
    ]
    for attr_name, constants, vals in tests:
        settingsdict = {
            attr_name: constants,
            "num_harmonies": 0,
            "max_interval_for_non_chord_tones": "-OCTAVE",
            "min_interval_for_non_chord_tones": "-MINOR_SECOND",
        }
        # unit test of replace_pitch_constants
        er = er_settings.ERSettings(**settingsdict)
        # er_preprocess.replace_pitch_constants(er)
        assert np.equal(
            getattr(er, attr_name), vals
        ).all(), "np.equal(getattr(er, attr_name), vals).all()"

        # same test for in the context of er_preprocess
        # doesn't currently work because of this line in er_preprocess.py:
        # er.foot_pcs = [foot_pc % er.tet for foot_pc in er.foot_pcs]
        # er = er_settings.get_settings(settingsdict)
        # tempered_vals = er_tuning.temper_pitch_materials(
        #     vals, er.tet, er.integers_in_12_tet
        # )
        # try:
        #     assert np.equal(
        #         getattr(er, attr_name), tempered_vals,
        #     ).all(), "np.equal(getattr(er, attr_name), tempered_vals).all()"
        # except:  # pylint: disable=bare-except
        #     exc_type, exc_value, exc_traceback = sys.exc_info()
        #     traceback.print_exception(
        #         exc_type, exc_value, exc_traceback, file=sys.stdout
        #     )
        #     breakpoint()
        # print(getattr(er, attr_name))


if __name__ == "__main__":
    test_process_pattern_vl_order()
    test_read_in_settings()
    test_pitch_constants()
    test_replace_pitch_constants()
