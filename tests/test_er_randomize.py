import os
import sys
import traceback

from efficient_rhythms import er_choirs
from efficient_rhythms import er_exceptions
from efficient_rhythms import er_make
from efficient_rhythms import er_settings


def test_many_seeds():
    num_seeds = 100
    start_seed = 350
    bad_seeds = []
    excs = []
    for i in range(start_seed, start_seed + num_seeds):
        user_settings = {
            "seed": i,
            "initial_pattern_attempts": 1,
            "voice_leading_attempts": 1,
            "max_available_pitch_materials_deadends": 50,
        }
        try:
            er = er_settings.get_settings(user_settings, random_settings=True)
            super_pattern = er_make.make_super_pattern(er)
            er_make.complete_pattern(er, super_pattern)
            er_choirs.assign_choirs(er, super_pattern)
        except er_exceptions.VoiceLeadingError:
            pass
        except Exception:  # pylint: disable=broad-except
            bad_seeds.append(i)
            excs.append(sys.exc_info())

    for seed, (exc_type, exc_value, exc_traceback) in zip(bad_seeds, excs):
        try:
            term_size = os.get_terminal_size().columns
        except OSError:
            term_size = 80
        print("#" * term_size)
        print("SEED: ", seed)
        traceback.print_exception(
            exc_type, exc_value, exc_traceback, file=sys.stdout
        )


if __name__ == "__main__":
    test_many_seeds()
