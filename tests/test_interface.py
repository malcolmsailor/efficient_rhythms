"""This module only tests whether various transformers/filters run without 
crashing. It doesn't actually veryify that they behave as expected! (That is
still a to-do.)
"""
import os
import subprocess

import efficient_rhythms.er_changers as er_changers

SCRIPT_DIR = os.path.dirname((os.path.realpath(__file__)))

os.environ["PYTHONPATH"] = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
os.environ["EFFICIENT_RHYTHMS_DEBUG"] = "true"

SETTINGS = os.path.join(SCRIPT_DIR, "test_settings/test_interface_settings.py")

N_PROB_CURVES = 9


class ProcError(Exception):
    pass


def run(user_input):
    proc = subprocess.run(
        ["python3", "-m", "efficient_rhythms", "--settings", SETTINGS],
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
    # does every filter and transformer have the same number of prob_curves?
    prob_curves = range(1, N_PROB_CURVES + 1)
    prob_curve_input = [
        "a",  # add filter
        "2",  # pitch filter
        "1",  # prob_curve
        None,  # select prob_curve at index 3
        "",  # return to changer prompt
        "",  # return to playback prompt
        "q\n",  # quit
    ]
    for prob_curve in prob_curves:
        prob_curve_input[3] = str(prob_curve)
        run("\n".join(prob_curve_input))
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
