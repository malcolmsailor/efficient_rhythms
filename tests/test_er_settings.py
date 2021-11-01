import typing

import numpy as np

import efficient_rhythms.er_settings as er_settings
import efficient_rhythms.er_constants as er_constants


def test_categories():
    cats = er_settings.CATEGORIES
    for field_name, a in er_settings.ERSettings.__dataclass_fields__.items():
        try:
            c = a.metadata["category"]
        except KeyError:
            assert field_name[0] == "_"
        else:
            assert c in cats


def test_field_process():
    num_voices = 3
    basesettings = {"num_voices": num_voices}
    tests = [
        ("rhythm_len", [0.25, 1, 2, 3, 4], [0.25, 1, 2]),
        ("pattern_len", None, 16),
        ("pattern_len", 2.5),
        ("pattern_len", [1, 2]),
        ("chord_tone_before_rests", 0.125),
        ("chord_tones_no_diss_treatment", [True, False]),
        ("chord_tones_no_diss_treatment", [True]),
        ("dur_density", 0.125),
        ("dur_density", 14),
        ("obligatory_onsets", [0, 2], [[0, 2], [0, 2], [0, 2]]),
        ("transpose_intervals", None, ()),
        ("transpose_intervals", 2),
        ("interval_cycle", None, ()),
        ("interval_cycle", 2),
        ("forbidden_interval_modulo", None, []),
        ("forbidden_interval_modulo", [[0, 2]]),
    ]
    for test in tests:
        if len(test) == 3:
            name, val, result = test
        else:
            name, val = test  # pylint: disable=unbalanced-tuple-unpacking
            result = val
        settings = basesettings.copy()
        settings[name] = val
        er = er_settings.ERSettings(**settings)
        out = getattr(er, name)
        assert isinstance(out, (tuple, list))
        if not isinstance(val, typing.Sequence):
            assert all(item == result for item in out)
        else:
            assert all(
                item == result[i % len(result)] for i, item in enumerate(out)
            )
        print(out, result)


def test_from_if_none():
    er = er_settings.ERSettings()
    assert er.max_interval_for_non_chord_tones == er.max_interval


def test_replace_pitch_constants():
    # attr_name, constants, translated value
    tests = [
        (
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
            "CONTIGUOUS_OCTAVES * C * OCTAVE2",
            er_constants.CONTIGUOUS_OCTAVES
            * er_constants.C
            * er_constants.OCTAVE2,
        ),
        (
            ("MAJOR_TRIAD", "MINOR_TRIAD * D", "MAJOR_63 * E", "MINOR_64 * A"),
            [
                er_constants.MAJOR_TRIAD,
                er_constants.MINOR_TRIAD * er_constants.D,
                er_constants.MAJOR_63 * er_constants.E,
                er_constants.MINOR_64 * er_constants.A,
            ],
        ),
        (
            "GENERIC_UNISON",
            er_constants.GENERIC_UNISON,
        ),
        (
            "-OCTAVE",
            -1 * er_constants.OCTAVE,
        ),
        (
            "-MINOR_SECOND",
            -1 * er_constants.MINOR_2ND,
        ),
    ]
    for constants, vals in tests:
        out = er_settings.settings_base.replace_pitch_constants(constants)
        assert np.equal(out, vals).all()


if __name__ == "__main__":
    test_categories()
    test_field_process()
    test_from_if_none()
    test_replace_pitch_constants()
