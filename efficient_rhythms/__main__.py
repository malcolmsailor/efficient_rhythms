import itertools
import os
import random
import subprocess
import sys

from . import er_changers
from . import er_exceptions
from . import er_globals
from . import er_interface
from . import er_make_handler
from . import er_misc_funcs
from . import er_midi
from . import er_midi_settings
from . import er_output_notation
from . import er_settings

MAX_RANDOM_TRIES = 10


def get_settings(args, seed, settings_dict=None):
    if args.input_midi:
        settings = er_settings.read_in_settings(
            args.settings,
            er_midi_settings.MidiSettings,
            output_path=args.output,
        )
    else:
        settings = er_settings.get_settings(
            args.settings if settings_dict is None else settings_dict,
            random_settings=args.random,
            seed=seed,
            output_path=args.output,
        )
    return settings


def get_changer_settings(args):
    if args.changers is None:
        return []
    changer_settings = []
    for path in args.changers:
        print(f"Reading changers from {path}")
        with open(path, "r", encoding="utf-8") as inf:
            changer_settings.extend(eval(inf.read()))
    return changer_settings


def save(args, settings, pattern):
    if args.input_midi:
        if pattern.onsets_adjusted_by != 0:
            er_midi.write_midi(pattern, settings)
    else:
        non_empty = er_midi.write_er_midi(
            settings, pattern, settings.output_path
        )
        if not non_empty:
            print(
                "Midi file is empty! Nothing to write. "
                "(Check your settings and try again.)"
            )
            sys.exit(1)


def get_changers(changer_settings, pattern):
    return {
        i: getattr(er_changers, name)(pattern, **kwargs)
        for i, (name, kwargs) in enumerate(changer_settings)
    }


def make_pattern(args, settings):
    if args.input_midi:
        abs_path = os.path.abspath(args.input_midi)
        pattern = er_midi.read_midi_to_internal_data(
            abs_path,
            tet=settings.tet,
            time_sig=settings.time_sig,
            max_denominator=settings.max_denominator,
        )
        settings.num_tracks_from(pattern)
        settings.original_path = abs_path
        return pattern
    pattern = er_make_handler.make_super_pattern(settings)
    return pattern


def build(args, seed=None, settings_dict=None):
    for try_i in itertools.count():
        # The reason we re-initialize the settings inside this loop is because,
        # if args.random is True, there is randomness in how the settings
        # are initialized. Eventually it would be nice to design the settings
        # class so that it is capable of "re-randomizing" itself without
        # being re-initialized, so that we can put the settings initialization
        # in a more intuitive place (e.g., before calling build()) and don't
        # have to return it from this function.
        settings = get_settings(args, seed, settings_dict=settings_dict)
        try:
            pattern = make_pattern(args, settings)
            break
        except er_exceptions.ErMakeError as exc:
            if not args.random:
                er_interface.fail_and_exit(exc)
            elif try_i + 1 >= MAX_RANDOM_TRIES:
                er_interface.fail_and_exit(
                    exc, random_failures=MAX_RANDOM_TRIES
                )
        # we should only get here if args.random is True and er_make failed
        print("Random settings failed, trying again with another seed")
        seed = random.randint(0, 2 ** 32)

    changer_settings = get_changer_settings(args)
    changers = get_changers(changer_settings, pattern)
    changed_pattern = er_changers.apply(pattern, changers)

    save(
        args,
        settings,
        changed_pattern if changed_pattern is not None else pattern,
    )
    return settings, changers, pattern, changed_pattern


def output_notation(settings, pattern, args):
    rhythms_ok = er_output_notation.check_rhythms(settings)
    if not rhythms_ok:
        # check_rhythms already prints an error message so we don't print
        # another one here
        # TODO document this error code
        sys.exit(1)
    try:
        result = er_output_notation.run_verovio(
            pattern,
            settings.output_path,
            args.verovio_arguments,
            "." + args.output_notation,
        )
    except subprocess.CalledProcessError as exc:
        if not er_globals.DEBUG:
            er_output_notation.clean_up_temporary_notation_files()
        print(exc)
        sys.exit(1)
    if not result:
        sys.exit(1)


def main():
    er_interface.print_hello()
    args = er_interface.parse_cmd_line_args()
    settings, changers, pattern, changed_pattern = build(args)

    if args.no_interface:
        print(f"Output written to {settings.output_path}")
        if args.output_notation:
            output_notation(
                settings,
                changed_pattern if changed_pattern is not None else pattern,
                args,
            )
    else:
        er_interface.input_loop(settings, pattern, args, changers)


if __name__ == "__main__":
    main()
