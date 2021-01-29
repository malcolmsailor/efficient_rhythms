"""This module tests whether various transformers/filters run without crashing.
It doesn't actually veryify that they behave as expected!
"""
import os
import subprocess
import sys

# import pytest

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

import src.er_changers as er_changers  # pylint: disable=wrong-import-position

SCRIPT_DIR = os.path.dirname((os.path.realpath(__file__)))
EFFRHY = os.path.join(SCRIPT_DIR, "../efficient_rhythms.py")
SETTINGS = os.path.join(SCRIPT_DIR, "test_settings/test_interface_settings.py")

N_PROB_FUNCS = 9


class ProcError(Exception):
    pass


def run(user_input):
    proc = subprocess.run(
        ["python3", EFFRHY, "--settings", SETTINGS, "--debug"],
        input=user_input.encode(encoding="utf-8"),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if proc.returncode != 0:
        print(proc.stdout.decode())
        raise ProcError


# @pytest.mark.skip(
#     reason="better to run this test independently from shell "
#     "(there is a git pre-commit hook that does this)"
# )
# assay_changers() rather than test_changers() because we don't want pytest
#   to run
def assay_changers():
    # does every filter and transformer have the same number of prob_funcs?
    prob_funcs = range(1, N_PROB_FUNCS + 1)
    prob_func_input = [
        "a",  # add filter
        "2",  # pitch filter
        "1",  # prob_func
        None,  # select prob_func at index 3
        "",  # return to changer prompt
        "",  # return to playback prompt
        "q\n",  # quit
    ]
    for prob_func in prob_funcs:
        prob_func_input[3] = str(prob_func)
        run("\n".join(prob_func_input))
    # CHANGER_TODO write more tests
    filters = range(1, len(er_changers.FILTERS))
    input_loop = "\n".join(
        [
            "a",  # add changer
            "{}",  # select changer
            "",  # return to changer prompt
            "",  # return to playback prompt (applying changer)
            "a",  # back to changer prompt
            "1",  # select active changer
            "r",  # remove active changer
            "",  # return to playback prompt
        ]
    )
    input_commands = (
        "\n".join([input_loop.format(i) for i in filters]) + "\nq\n"  # quit
    )
    run(input_commands)


if __name__ == "__main__":
    assay_changers()
