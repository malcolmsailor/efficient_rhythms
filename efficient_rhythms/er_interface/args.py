import argparse
import warnings
import sys


def parse_cmd_line_args():
    parser = argparse.ArgumentParser(
        description=("Generates a splendiferous midi file.\n")
    )
    parser.add_argument(
        "-i",
        "--input-midi",
        help="path to a midi file to be filtered and" "/or transformed",
    )
    # parser.add_argument(
    #     "-t",
    #     "--tet",
    #     help="TET of input midi file specified with -m",
    #     default=12,
    #     type=int,
    # )
    parser.add_argument(
        "-m",
        "--midi-port",
        help="send midi via a virtual port for use in a DAW, "
        "rather than using in-shell midi player",
        action="store_false",
    )
    parser.add_argument(
        "-r", "--random", help="randomize settings", action="store_true"
    )
    # parser.add_argument(
    #     "-ts",
    #     help="Time signature to use with midi file "
    #     "specified with -f, format m/n",
    # )
    # parser.add_argument(
    #     "-d",
    #     help="Maximum denominator for onset/durations for midi file specified "
    #     "with -f",
    #     default=0,
    #     type=int,
    # )
    parser.add_argument(
        "-s",
        "--settings",
        nargs="*",
        help="path to settings files, each containing a Python dictionary",
    )
    parser.add_argument(
        "-n",
        "--no-interface",
        help="build midi file, but don't play it back or enter user interface",
        action="store_true",
    )
    parser.add_argument(
        "-v",
        "--verovio-arguments",
        help=(
            "arguments to pass into verovio, replacing the default argument "
            "'--all-pages'. Pass a single string, which will be split by "
            "whitespace"
        ),
    )
    parser.add_argument(
        "--output-notation",
        choices=("png", "pdf", "svg"),
        help=(
            "if passed with '--no-interface', notation in the specified file "
            "format will be generated as well as a midi file"
        ),
    )
    # parser.add_argument(
    #     "--debug",
    #     action="store_true",
    #     help="provide option to enter a breakpoint in user input loop",
    # )
    # LONGTERM
    # parser.add_argument(
    #     "--filters",
    # )
    args = parser.parse_args()
    if args.output_notation and not args.no_interface:
        warnings.warn(
            "'--output-notation' has no effect unless "
            "'--no-interface' is also passed"
        )
    if args.input_midi and args.no_interface:
        print(
            "Both '--input-midi' and '--no-interface' passed. " "Nothing to do!"
        )
        sys.exit(1)

    return args
