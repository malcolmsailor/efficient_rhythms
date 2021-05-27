# moved to __main__.py
# TODO remove this file
# """Does the indescribable.
# """
# import itertools
# import os
# import random
# import sys


# from . import er_exceptions
# from . import er_interface
# from . import er_make
# from . import er_misc_funcs
# from . import er_midi
# from . import er_midi_settings
# from . import er_output_notation
# from . import er_preprocess

# # MAYBE wait a moment when sending midi messages, see if this solves
# #   issue of first messages sometimes not sounding?


# MAX_RANDOM_TRIES = 10


# def get_super_pattern(settings, midi_in=None):
#     if midi_in is None:
#         return build_pattern(settings)
#     return er_midi.read_midi_to_internal_data(
#         midi_in,
#         tet=settings.tet,
#         time_sig=settings.time_sig,
#         max_denominator=settings.max_denominator,
#     )


# def get_settings(args, seed, settings_dict=None):
#     if args.input_midi:
#         return er_preprocess.read_in_settings(
#             args.settings, er_midi_settings.MidiSettings
#         )
#     return er_preprocess.preprocess_settings(
#         args.settings if settings_dict is None else settings_dict,
#         random_settings=args.random,
#         seed=seed,
#     )


# def save(args, settings, pattern):
#     if args.input_midi:
#         if pattern.onsets_adjusted_by != 0:
#             er_midi.write_midi(pattern, settings)
#     else:
#         non_empty = er_midi.write_er_midi(
#             settings, pattern, settings.output_path
#         )
#         if not non_empty:
#             print(
#                 "Midi file is empty! Nothing to write. "
#                 "(Check your settings and try again.)"
#             )
#             sys.exit(1)


# def make_pattern(args, settings):
#     if args.input_midi:
#         abs_path = os.path.abspath(args.input_midi)
#         pattern = er_midi.read_midi_to_internal_data(
#             abs_path,
#             tet=settings.tet,
#             time_sig=settings.time_sig,
#             max_denominator=settings.max_denominator,
#         )
#         settings.num_tracks_from(pattern)
#         settings.original_path = abs_path
#         return pattern
#     pattern = er_make.make_super_pattern(settings)
#     save(args, settings, pattern)


# def build(args, seed=None, settings_dict=None):
#     for try_i in itertools.count():
#         # The reason we re-initialize the settings inside this loop is because,
#         # if args.random is True, there is randomness in how the settings
#         # are initialized. Eventually it would be nice to design the settings
#         # class so that it is capable of "re-randomizing" itself without
#         # being re-initialized, so that we can put the settings initialization
#         # in a more intuitive place (e.g., before calling build()) and don't
#         # have to return it from this function.
#         settings = get_settings(args, seed, settings_dict=settings_dict)
#         try:
#             return settings, make_pattern(args, settings)
#         except er_exceptions.ErMakeException as exc:
#             if not args.random:
#                 er_interface.fail_and_exit(exc)
#             elif try_i + 1 >= MAX_RANDOM_TRIES:
#                 er_interface.fail_and_exit(
#                     exc, random_failures=MAX_RANDOM_TRIES
#                 )
#         # we should only get here if args.random is True and er_make failed
#         print("Random settings failed, trying again with another seed")
#         seed = random.randint(0, 2 ** 32)


# def output_notation(settings, pattern, args):
#     rhythms_ok = er_output_notation.check_rhythms(settings)
#     if not rhythms_ok:
#         # check_rhythms already prints an error message so we don't print
#         # another one here
#         sys.exit(1)
#     try:
#         result = er_output_notation.run_verovio(
#             pattern,
#             settings.output_path,
#             args.verovio_arguments,
#             "." + args.output_notation,
#         )
#     # TODO remove ProcError
#     except er_misc_funcs.ProcError as exc:
#         if not er_interface.DEBUG:
#             er_output_notation.clean_up_temporary_notation_files()
#         print(exc)
#         sys.exit(1)
#     if not result:
#         sys.exit(1)


# def main():
#     er_interface.print_hello()
#     args = er_interface.parse_cmd_line_args()
#     settings, pattern = build(args)
#     if args.no_interface:
#         print(f"Output written to {settings.output_path}")
#         if args.output_notation:
#             output_notation(settings, pattern, args)
#     else:
#         er_interface.input_loop(settings, pattern, args)


# # def main():
# #     er_interface.print_hello()
# #     args = er_interface.parse_cmd_line_args()
# #     if not args.no_interface:
# #         midi_player = er_playback.init_and_return_midi_player(
# #             shell=args.midi_port
# #         )
# #     midi_in = args.input_midi
# #     if midi_in:
# #         if args.output_notation:
# #             print(
# #                 "'--output-notation' not implemented when running on an "
# #                 "external midi file"
# #             )
# #         # if args.no_interface:
# #         #     print(
# #         #         "Both '--input-midi' and '--no-interface' passed. "
# #         #         "Nothing to do!"
# #         #     )
# #         #     return
# #         midi_in = os.path.abspath(midi_in)
# #         midi_settings = er_preprocess.read_in_settings(
# #             args.settings, er_midi_settings.MidiSettings
# #         )
# #         super_pattern = er_midi.read_midi_to_internal_data(
# #             midi_in,
# #             tet=midi_settings.tet,
# #             time_sig=midi_settings.time_sig,
# #             max_denominator=midi_settings.max_denominator,
# #         )
# #         midi_settings.num_tracks_from(super_pattern)
# #         midi_settings.original_path = midi_in
# #         if super_pattern.onsets_adjusted_by != 0:
# #             er_midi.write_midi(super_pattern, midi_settings)
# #         er_interface.input_loop(
# #             midi_settings,
# #             super_pattern,
# #             midi_player,
# #             args.verovio_arguments,
# #             debug=args.debug,
# #         )

# #     else:
# #         seed = None

# #         # LONGTERM move this loop to er_make.py or something
# #         for try_i in itertools.count():
# #             er = er_preprocess.preprocess_settings(
# #                 args.settings,
# #                 script_dir=SCRIPT_DIR,
# #                 random_settings=args.random,
# #                 seed=seed,
# #             )
# #             try:
# #                 super_pattern = er_make.make_super_pattern(er)
# #                 er_make.complete_pattern(er, super_pattern)
# #                 break
# #             except er_exceptions.ErMakeException as exc:
# #                 if not args.random:
# #                     er_interface.fail_and_exit(exc)
# #                 elif try_i + 1 >= MAX_RANDOM_TRIES:
# #                     er_interface.fail_and_exit(
# #                         exc, random_failures=MAX_RANDOM_TRIES
# #                     )
# #             # we should only get here if args.random is True and er_make failed
# #             print("Random settings failed, trying again with another seed")
# #             seed = random.randint(0, 2 ** 32)
# #         er_choirs.assign_choirs(
# #             er, super_pattern
# #         )
# #         non_empty = er_midi.write_er_midi(er, super_pattern, er.output_path)
# #         if not non_empty:
# #             print(
# #                 "Midi file is empty! Nothing to write. "
# #                 "(Check your settings and try again.)"
# #             )
# #             return
# #         if args.no_interface:
# #             print(f"Output written to {er.output_path}")
# #             if args.output_notation:
# #                 if er_output_notation.check_rhythms(er):
# #                     try:
# #                         result = er_output_notation.run_verovio(
# #                             super_pattern,
# #                             er.output_path,
# #                             args.verovio_arguments,
# #                             "." + args.output_notation,
# #                         )
# #                     except er_misc_funcs.ProcError as exc:
# #                         if not args.debug:
# #                             er_output_notation.clean_up_temporary_notation_files()
# #                         print(exc)
# #                         sys.exit(1)
# #                     if not result:
# #                         sys.exit(1)
# #             return
# #         er_interface.input_loop(
# #             er,
# #             super_pattern,
# #             midi_player,
# #             args.verovio_arguments,
# #             debug=args.debug,
# #         )
