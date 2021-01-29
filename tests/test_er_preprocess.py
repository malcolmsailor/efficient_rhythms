import os
import sys
import traceback

import numpy as np

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

import src.er_constants as er_constants  # pylint: disable=wrong-import-position
import src.er_preprocess as er_preprocess  # pylint: disable=wrong-import-position
import src.er_settings as er_settings  # pylint: disable=wrong-import-position


def test_process_pattern_voice_leading_order():
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
            er = er_preprocess.preprocess_settings(settingsdict)
            for item in er.pattern_voice_leading_order:
                voice_i = item.voice_i
                pattern_len = pattern_lens[voice_i]
                modulo = max(pattern_lens) if truncate else pattern_len
                start_time = item.start_time
                while item.prev_item is not None:
                    item = item.prev_item
                    assert item.voice_i == voice_i, "item.voice_i != voice_i"
                    try:
                        try:
                            assert (
                                item.start_time % modulo == start_time % modulo
                            ), "item.start_time % modulo != start_time % modulo"
                        except AssertionError:
                            assert (
                                item.start_time < modulo
                            ), "item.start_time >= modulo"
                    except:  # pylint: disable=bare-except
                        exc_type, exc_value, exc_traceback = sys.exc_info()
                        traceback.print_exception(
                            exc_type, exc_value, exc_traceback, file=sys.stdout
                        )
                        breakpoint()

                assert item.start_time == 0, "item.start_time != 0"


def test_replace_pitch_constants():
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
        ("unison_weighted_as", "GENERIC_UNISON", er_constants.GENERIC_UNISON,),
    ]
    for attr_name, constants, vals in tests:
        settingsdict = {attr_name: constants, "num_harmonies": 0}
        # unit test of replace_pitch_constants
        er = er_settings.ERSettings(**settingsdict)
        er_preprocess.replace_pitch_constants(er)
        try:
            assert np.equal(
                getattr(er, attr_name), vals
            ).all(), "np.equal(getattr(er, attr_name), vals).all()"
        except:  # pylint: disable=bare-except
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(
                exc_type, exc_value, exc_traceback, file=sys.stdout
            )
            breakpoint()
        # same test for in the context of er_preprocess
        # doesn't currently work because of this line in er_preprocess.py:
        # er.foot_pcs = [foot_pc % er.tet for foot_pc in er.foot_pcs]
        # er = er_preprocess.preprocess_settings(settingsdict)
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
    test_process_pattern_voice_leading_order()
    test_replace_pitch_constants()
