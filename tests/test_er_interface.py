import os
import sys

# import traceback

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

import src.er_interface as er_interface  # pylint: disable=wrong-import-position

# import src.er_preprocess as er_preprocess  # pylint: disable=wrong-import-position
import src.er_settings as er_settings  # pylint: disable=wrong-import-position


def test_build_state_printer():
    return
    # # This test is not implemented.
    # # In the end I tested BuildStatusPrinter just by running the script and
    # # visual inspection of the results...
    # # Both of the following files are of use in that connection:
    # #       tests/test_settings/test_fail_initial_pattern.py
    # #       tests/test_settings/test_fail_voice_lead.py
    # settings = er_settings.ERSettings({})
    # bsp = er_interface.BuildStatusPrinter(settings)


if __name__ == "__main__":
    # test_build_state_printer()
    pass
