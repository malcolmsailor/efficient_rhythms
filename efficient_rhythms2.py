"""Does the indescribable.
"""
import os

import er_choirs
import er_interface
import er_make
import er_misc_funcs
import er_midi
import er_midi_settings
import er_preprocess

# MAYBE make old directory and check it when looking for files
# MAYBE wait a moment when sending midi messages, see if this solves
#   issue of first messages sometimes not sounding?

SCRIPT_DIR, SCRIPT_BASE = os.path.split((os.path.realpath(__file__)))


def main():

    args = er_interface.parse_cmd_line_args()

    midi_in = args.input_midi
    if midi_in:  # pylint: disable=no-else-raise
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

        midi_player = er_midi.init_and_return_midi_player(
            midi_settings.tet, shell=args.midi_port
        )

        if super_pattern.attacks_adjusted_by != 0:
            fname_path = er_interface.get_changed_midi_path(midi_in)
            er_midi.write_midi(super_pattern, midi_settings, fname_path)
        else:
            fname_path = midi_in

        er_interface.input_loop(
            None,
            super_pattern,
            midi_player,
            fname_path,
            midi_settings=midi_settings,
        )

    else:
        fname_path, _ = er_misc_funcs.return_fname_path(SCRIPT_BASE, SCRIPT_DIR)
        er = er_preprocess.preprocess_settings(
            args.settings, random_settings=args.r
        )

        midi_player = er_midi.init_and_return_midi_player(
            er.tet, shell=args.midi_port
        )

        super_pattern = er_make.make_super_pattern(er)

        er_make.complete_pattern(er, super_pattern)

        er_choirs.assign_choirs(er, super_pattern)

        er_midi.write_er_midi(er, super_pattern, fname_path)

        er_interface.input_loop(
            er, super_pattern, midi_player, fname_path, midi_settings=None
        )


if __name__ == "__main__":
    main()
