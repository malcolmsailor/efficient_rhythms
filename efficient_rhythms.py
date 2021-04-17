"""Does the indescribable.
"""
import itertools
import os
import random
import sys

import src.er_choirs as er_choirs
import src.er_exceptions as er_exceptions
import src.er_interface as er_interface
import src.er_make as er_make
import src.er_misc_funcs as er_misc_funcs
import src.er_midi as er_midi
import src.er_midi_settings as er_midi_settings
import src.er_output_notation as er_output_notation
import src.er_playback as er_playback
import src.er_preprocess as er_preprocess

# MAYBE wait a moment when sending midi messages, see if this solves
#   issue of first messages sometimes not sounding?

# TODO fix printing of scores to include note octave

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
MAX_RANDOM_TRIES = 10


def main():

    er_interface.print_hello()
    args = er_interface.parse_cmd_line_args()
    if not args.no_interface:
        midi_player = er_playback.init_and_return_midi_player(
            shell=args.midi_port
        )
    midi_in = args.input_midi
    if midi_in:
        if args.output_notation:
            print(
                "'--output-notation' not implemented when running on an "
                "external midi file"
            )
        if args.no_interface:
            print(
                "Both '--input-midi' and '--no-interface' passed. "
                "Nothing to do!"
            )
            return
        midi_in = os.path.abspath(midi_in)
        midi_settings = er_preprocess.read_in_settings(
            args.settings, er_midi_settings.MidiSettings
        )
        super_pattern = er_midi.read_midi_to_internal_data(
            midi_in,
            tet=midi_settings.tet,
            time_sig=midi_settings.time_sig,
            max_denominator=midi_settings.max_denominator,
        )
        midi_settings.num_tracks_from(super_pattern)
        midi_settings.original_path = midi_in
        if super_pattern.attacks_adjusted_by != 0:
            er_midi.write_midi(super_pattern, midi_settings)
        er_interface.input_loop(
            midi_settings,
            super_pattern,
            midi_player,
            args.verovio_arguments,
            debug=args.debug,
        )

    else:
        seed = None

        # LONGTERM move this loop to er_make.py or something
        for try_i in itertools.count():
            er = er_preprocess.preprocess_settings(
                args.settings,
                script_dir=SCRIPT_DIR,
                random_settings=args.random,
                seed=seed,
            )
            try:
                super_pattern = er_make.make_super_pattern(er)
                er_make.complete_pattern(er, super_pattern)
                break
            except er_exceptions.ErMakeException as exc:
                if not args.random:
                    er_interface.failure_message(exc)
                elif try_i + 1 >= MAX_RANDOM_TRIES:
                    er_interface.failure_message(
                        exc, random_failures=MAX_RANDOM_TRIES
                    )
            # we should only get here if args.random is True and er_make failed
            print("Random settings failed, trying again with another seed")
            seed = random.randint(0, 2 ** 32)
        er_choirs.assign_choirs(er, super_pattern)
        non_empty = er_midi.write_er_midi(er, super_pattern, er.output_path)
        if not non_empty:
            print(
                "Midi file is empty! Nothing to write. "
                "(Check your settings and try again.)"
            )
            return
        if args.no_interface:
            print(f"Output written to {er.output_path}")
            if args.output_notation:
                if er_output_notation.check_rhythms(er):
                    try:
                        result = er_output_notation.run_verovio(
                            super_pattern,
                            er.output_path,
                            args.verovio_arguments,
                            "." + args.output_notation,
                        )
                    except er_misc_funcs.ProcError as exc:
                        if not args.debug:
                            er_output_notation.clean_up_temporary_notation_files()
                        print(exc)
                        sys.exit(1)
                    if not result:
                        sys.exit(1)
            return
        er_interface.input_loop(
            er,
            super_pattern,
            midi_player,
            args.verovio_arguments,
            debug=args.debug,
        )


if __name__ == "__main__":
    main()
