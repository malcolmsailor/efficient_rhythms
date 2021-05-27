import os
import sys
import traceback

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

import efficient_rhythms.er_tuning as er_tuning  # pylint: disable=wrong-import-position
import efficient_rhythms.er_constants as er_constants  # pylint: disable=wrong-import-position


def test_approximate_just_interval():
    tests = [
        (er_constants.C * er_constants.OCTAVE4, 12, 60),
        (er_constants.A * er_constants.OCTAVE0, 12, 21),
        (er_constants.C * er_constants.OCTAVE8, 12, 108),
        (er_constants.C * er_constants.OCTAVE4, 31, 5 * 31),
        (er_constants.A * er_constants.OCTAVE0, 31, 54),
        (er_constants.C * er_constants.OCTAVE8, 31, 9 * 31),
    ]
    try:
        for item, tet, return_value in tests:
            assert (
                er_tuning.approximate_just_interval(item, tet) == return_value
            ), "er_tuning.approximate_just_interval(item, tet) != return_value"

    except:  # pylint: disable=bare-except
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(
            exc_type, exc_value, exc_traceback, file=sys.stdout
        )
        breakpoint()


if __name__ == "__main__":
    test_approximate_just_interval()
