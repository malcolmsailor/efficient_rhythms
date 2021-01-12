"""Does the indescribable.
"""
import os

import src.er_choirs as er_choirs
import src.er_interface as er_interface
import src.er_make as er_make
import src.er_misc_funcs as er_misc_funcs
import src.er_midi as er_midi
import src.er_midi_settings as er_midi_settings
import src.er_preprocess as er_preprocess

# MAYBE make old directory and check it when looking for files
# MAYBE wait a moment when sending midi messages, see if this solves
#   issue of first messages sometimes not sounding?

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))


def main():

    args = er_interface.parse_cmd_line_args()

    midi_in = args.input_midi
    if midi_in:
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
        midi_player = er_midi.init_and_return_midi_player(
            midi_settings.tet, shell=args.midi_port
        )
        if super_pattern.attacks_adjusted_by != 0:
            er_midi.write_midi(super_pattern, midi_settings, fname_path)
        er_interface.input_loop(
            midi_settings, super_pattern, midi_player,
        )

    else:
        er = er_preprocess.preprocess_settings(
            args.settings, script_path=SCRIPT_DIR, random_settings=args.random
        )
        midi_player = er_midi.init_and_return_midi_player(
            er.tet, shell=args.midi_port
        )
        super_pattern = er_make.make_super_pattern(er)
        er_make.complete_pattern(er, super_pattern)
        er_choirs.assign_choirs(er, super_pattern)
        er_midi.write_er_midi(er, super_pattern)
        er_interface.input_loop(er, super_pattern, midi_player)


if __name__ == "__main__":
    main()
