import os
import sys
import traceback

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

import efficient_rhythms.er_exceptions as er_exceptions
import efficient_rhythms.er_preprocess as er_preprocess
import efficient_rhythms.er_make_handler as er_make_handler


def test_timeout():
    settingsdict = {
        "num_voices": 6,
        "num_harmonies": 2,
        "harmony_len": 100,
        "timeout": 0.2,
    }
    er = er_preprocess.preprocess_settings(settingsdict)
    try:
        er_make_handler.make_super_pattern(er)
    except er_exceptions.TimeoutError:
        pass
    else:
        raise AssertionError("There should have been a timeout")
    settingsdict = {
        "num_voices": 1,
        "num_harmonies": 2,
        "timeout": 10,
    }
    er = er_preprocess.preprocess_settings(settingsdict)
    # We don't expect timeout
    er_make_handler.make_super_pattern(er)


if __name__ == "__main__":
    test_timeout()
