"""Provides the user interface for efficient_rhythms
"""

import collections
import copy
import math
import os
import subprocess
import sys
import traceback

from .. import er_changers
from .. import er_globals
from .. import er_midi
from .. import er_misc_funcs
from .. import er_output_notation
from .. import er_playback
from .. import er_settings
from .. import er_shell_constants

from .objects import CHANGER_DICT


SELECT_HEADER = "Active filters and transformers"
FILTERS_HEADER = "Filters"
TRANSFORMERS_HEADER = "Transformers"


def clear():  # from https://stackoverflow.com/a/684344/10155119
    os.system("cls" if os.name == "nt" else "clear")


def line_width():
    try:
        return os.get_terminal_size().columns
    except OSError:
        return 80


def print_hello():
    title = "Efficient rhythms: generate splendiferous midi loops"
    underline = "=" * min(len(title), line_width())
    print(
        "\n".join(
            [
                er_shell_constants.BOLD_TEXT + title,
                underline + er_shell_constants.RESET_TEXT,
                er_globals.GITHUB_URL,
            ]
        ),
        end="\n\n",
    )


def print_path(in_path, offset=0):
    if len(in_path) < line_width():
        return in_path
    while "/" in in_path:
        in_path = in_path.split("/", maxsplit=1)[1]
        if len(in_path) < line_width() - 4 - offset:
            return ".../" + in_path
    return in_path


def make_changer_prompt_line(i, attr_name, value, hint_name="", hint_value=""):
    # The main motivation for _stringify is so that fractions will print out
    # as "1" or "2/3" rather than Fraction(1, 1) or Fraction(2, 3)
    def _stringify(item):
        # I don't think any other types of sequence should show up here
        if isinstance(item, tuple):
            return (
                "("
                + ", ".join([_stringify(sub_item) for sub_item in item])
                + ")"
            )
        if isinstance(item, list):
            return (
                "["
                + ", ".join([_stringify(sub_item) for sub_item in item])
                + "]"
            )
        return item.__str__()

    num_str = f"({i})"
    out = f"{num_str:>8} {attr_name}: {_stringify(value)}"
    if hint_name:
        if hint_value:
            hint_str = f"{hint_name}: {_stringify(hint_value):<10}"
        else:
            hint_str = hint_name + " " * 2
        if len(out) + len(hint_str) > line_width() - 2:
            hint_str_formatted = er_misc_funcs.add_line_breaks(
                hint_str, indent_type="all", indent_width=16, align="right"
            )
            out = out + "\n" + hint_str_formatted
        else:
            out = (
                out + " " * (line_width() - len(out) - len(hint_str)) + hint_str
            )
    return out


def make_prompt_line(i, line, indent=8):
    num_str = f"({i})"
    format_str = "{:>" + str(indent) + "} {}"
    return format_str.format(num_str, line)


def add_to_changer_attribute_dict(
    obj, lines, attribute_dict, attribute_i, prefix=""
):
    attributes = vars(obj)
    for attribute, value in attributes.items():
        if (
            attribute not in obj.interface_dict
            or attribute == "prob_curve"
            or not obj.display(attribute)
        ):
            continue
        if isinstance(value, list) and len(value) == 1:
            value = value[0]
        if isinstance(value, er_changers.NullProbCurve):
            value = value.pretty_name
        attr_name = obj.interface_dict[attribute]
        if attribute in obj.hint_dict:
            if isinstance(obj.hint_dict[attribute], tuple):
                hint_name, hint_value = obj.hint_dict[attribute]
                lines.append(
                    make_changer_prompt_line(
                        attribute_i,
                        attr_name,
                        value,
                        hint_name=hint_name,
                        hint_value=hint_value,
                    )
                )
            else:
                lines.append(
                    make_changer_prompt_line(
                        attribute_i,
                        attr_name,
                        value,
                        hint_name=obj.hint_dict[attribute],
                    )
                )
        else:
            lines.append(
                make_changer_prompt_line(attribute_i, attr_name, value)
            )
        attribute_dict[attribute_i] = prefix + attribute
        attribute_i += 1
    return attribute_i


def possible_values_prompt(possible_values):
    return "\n".join(
        [
            make_prompt_line(pv_i + 1, possible_value)
            for (pv_i, possible_value) in enumerate(possible_values)
        ]
    )


def print_prompt(
    header_text, user_prompt, description=None, possible_values=None
):
    # LONGTERM refactor to use this function more often
    lines = ["", er_misc_funcs.make_header(header_text)]
    if description is not None:
        lines.append(
            er_misc_funcs.add_line_breaks(
                description,
                indent_type="none",
                preserve_existing_line_breaks=False,
            ).rstrip()  # Not sure why sometimes it appends a newline and others not
        )
    lines.append("")
    if possible_values is not None:
        lines.append(possible_values)  # a str
        lines.append("")
    lines.append(
        er_misc_funcs.add_line_breaks(user_prompt, indent_type="hanging")
    )
    return input("\n".join(lines))


def update_changer_attribute(changer, attribute):
    # CHANGER_TODO can we only ask for plural values when plural values are possible?
    update_prompt = (
        "Enter new value (or values, separated by commas), "
        "'h' for possible values, or leave blank to cancel: "
    )
    if attribute.startswith("prob_curve."):
        obj = changer.prob_curve
        attribute = attribute.split(".", maxsplit=1)[1]
    else:
        obj = changer
    header_text = obj.pretty_name + ": " + obj.interface_dict[attribute]
    validator = obj.validation_dict[attribute]
    if validator.type_ == bool and validator.unique:
        setattr(obj, attribute, not bool(getattr(obj, attribute)))
        return
    if attribute in obj.desc_dict:
        description = obj.desc_dict[attribute]
    else:
        description = None
    if validator.possible_values:
        possible_values = possible_values_prompt(validator.possible_values)
    else:
        possible_values = None
    user_prompt = update_prompt
    answer = print_prompt(
        header_text,
        user_prompt,
        description=description,
        possible_values=possible_values,
    )
    while True:
        if answer == "":
            return
        if validator.possible_values and answer.isdigit():
            try:
                answer = validator.possible_values[int(answer) - 1]
            except IndexError:
                pass
        validated = validator.validate(answer)
        if validated is not None:
            if attribute == "prob_curve":
                update_prob_curve(obj, validated)
            else:
                setattr(obj, attribute, validated)
            return
        if answer != "h":
            print("Invalid input.")
        answer = input(
            er_misc_funcs.add_line_breaks(validator.possible_values_str())
        )


def update_adjust_changer_prompt(changer):
    attr_prompt = (
        "Enter the number corresponding to the attribute you "
        "would like to adjust or toggle, 'r' to remove the "
        "filter/transformer, or <enter> to continue: "
    )
    lines = [
        "",
        er_misc_funcs.make_header(changer.pretty_name),
        er_misc_funcs.add_line_breaks("Description: " + changer.description),
        "",
    ]
    attribute_i = 1
    attribute_dict = {}
    prob_curve_name = changer.interface_dict["prob_curve"]
    lines.append(
        make_changer_prompt_line(
            attribute_i, prob_curve_name, changer.prob_curve.pretty_name
        )
    )
    attribute_dict[attribute_i] = "prob_curve"
    attribute_i += 1
    attribute_i = add_to_changer_attribute_dict(
        changer.prob_curve,
        lines,
        attribute_dict,
        attribute_i,
        prefix="prob_curve.",
    )
    attribute_i = add_to_changer_attribute_dict(
        changer, lines, attribute_dict, attribute_i
    )

    lines += ["", er_misc_funcs.add_line_breaks(attr_prompt)]
    prompt = "\n".join(lines)
    return prompt, attribute_dict


def adjust_changer_prompt(active_changers, changer_i):

    changer = active_changers[changer_i]

    prompt, attribute_dict = update_adjust_changer_prompt(changer)
    while True:
        clear()
        answer = input(prompt).lower()
        while not answer in ("", "r"):
            try:
                if int(answer) in attribute_dict:
                    break
            except ValueError:
                pass
            answer = input("Invalid input, try again: ")
        if answer == "":
            try:
                changer.validate()
                break
            except er_changers.ChangeFuncError as err:
                print(
                    er_misc_funcs.add_line_breaks(
                        "Validation error: " + err.args[0],
                        indent_width=8,
                        indent_type="hanging",
                    )
                )
                input(
                    er_misc_funcs.add_line_breaks(
                        "Press enter to continue",
                        indent_width=12,
                        indent_type="all",
                    )
                )
                continue
        elif answer == "r":
            del active_changers[changer_i]
            for i in list(active_changers.keys()):
                if i > 0 and i - 1 not in active_changers:
                    j = i - 1
                    while j > 0 and j - 1 not in active_changers:
                        j -= 1
                    active_changers[j] = active_changers[i]
                    del active_changers[i]
            break
        answer = int(answer)
        attribute = attribute_dict[answer]
        update_changer_attribute(changer, attribute)
        prompt, attribute_dict = update_adjust_changer_prompt(changer)


def add_changer_prompt():
    def _get_table(changer_lines):
        # LONGTERM determine how wide terminal is and adjust n_cols accordingly
        n_cols = 2
        n_rows = math.ceil(len(changer_lines) / n_cols)
        rows = [
            [
                changer_lines[i + j * n_rows]
                if (i + j * n_rows) < len(changer_lines)
                else ""
                for j in range(n_cols)
            ]
            for i in range(n_rows)
        ]
        return er_misc_funcs.make_table(
            rows,
            divider="",
            col_width=line_width() // 2 - 2,
            align_char="<",
            fit_in_window=False,
            borders=False,
        )

    clear()
    add_prompt = (
        "Enter the number corresponding to the filter or transformer "
        "you would like to select, or <enter> to continue: "
    )
    filter_lines = []
    transformer_lines = []
    add_lines_to = filter_lines
    for i, changer in CHANGER_DICT.items():
        if i == -1:
            add_lines_to = transformer_lines
        else:
            add_lines_to.append(
                make_prompt_line(i, changer.pretty_name, indent=4)
            )
    lines = ["", er_misc_funcs.make_header(FILTERS_HEADER), ""]
    lines.append(_get_table(filter_lines))
    lines += ["", er_misc_funcs.make_header(TRANSFORMERS_HEADER), ""]
    lines.append(_get_table(transformer_lines))
    lines += ("", er_misc_funcs.add_line_breaks(add_prompt))
    return "\n".join(lines)


def update_prob_curve(changer, prob_curve_name):
    # new_prob_curve = vars(er_prob_curves)[prob_curve_name]()
    new_prob_curve = getattr(er_changers, prob_curve_name)()
    old_prob_curve = changer.prob_curve
    for attr, value in vars(old_prob_curve).items():
        if attr in new_prob_curve.interface_dict:
            setattr(new_prob_curve, attr, value)
        # if attr in vars(new_prob_curve)["interface_dict"]:
        # vars(new_prob_curve)[attr] = value

    changer.prob_curve = new_prob_curve


def add_changer_loop(active_changers, score, changer_counter):

    answer = input(add_changer_prompt()).lower()

    while True:
        if answer.isdigit():
            if int(answer) in CHANGER_DICT:
                break
        elif answer in ("x", ""):
            return
        answer = input(
            er_misc_funcs.add_line_breaks(
                "Invalid input. Please enter the digit corresponding "
                "to a filter or transformer above, or 'x' to cancel: "
            )
        ).lower()

    changer = CHANGER_DICT[int(answer)](score, changer_counter=changer_counter)

    changer_i = len(active_changers)
    active_changers[changer_i] = changer

    adjust_changer_prompt(active_changers, changer_i)


def get_changer_strings(active_changers):
    if active_changers:
        lines = []
        for i, changer in active_changers.items():
            lines.append(make_prompt_line(i + 1, changer.pretty_name))
    else:
        lines = ["   No active filters or transformers."]
    return lines


def update_move_changer_prompt(active_changers):
    # MAYBE replace this individual functions with a single function
    # that takes a header, and a prompt
    header = "Move filters or transformers"
    move_prompt = (
        "Enter the number corresponding to the filter or "
        "transformer you would like to move, or <enter> to "
        "continue: "
    )
    lines = ["", er_misc_funcs.make_header(header), ""] + get_changer_strings(
        active_changers
    )
    lines += ["", er_misc_funcs.add_line_breaks(move_prompt)]
    return "\n".join(lines)


def move_changer_loop(active_changers):
    def move_changer(active_changers, orig_i, new_i):
        changers = list(active_changers.values())
        moved_changer = changers.pop(orig_i)
        changers.insert(new_i, moved_changer)
        for i in active_changers:
            active_changers[i] = changers[i]

    def get_changer_i(active_changers, prompt):
        answer = input(prompt).lower()
        while True:
            if answer == "":
                return answer
            try:
                return int(answer) - 1
            except ValueError:
                answer = input("Invalid input, try again: ")
                continue
            if answer not in active_changers:
                answer = input("Invalid input, try again: ")
                continue

    if not active_changers:
        input(
            "   No active filters or transformers. Press <enter> to continue."
        )
        return
    if len(active_changers) == 1:
        input(
            "   Nothing to move: only 1 active filter/transformer. "
            "Press <enter> to continue."
        )
    prompt = update_move_changer_prompt(active_changers)
    new_prompt = "Enter the new position for the filter or transformer"
    orig_i = get_changer_i(active_changers, prompt)
    new_i = get_changer_i(active_changers, new_prompt)
    move_changer(active_changers, orig_i, new_i)


def update_copy_changer_prompt(active_changers):
    clear()
    # MAYBE replace these individual functions with a single function
    # that takes a header, and a prompt
    header = "Copy filters or transformers"
    copy_prompt = (
        "Enter the number corresponding to the filter or "
        "transformer you would like to copy, or <enter> to "
        "continue: "
    )
    lines = ["", er_misc_funcs.make_header(header), ""] + get_changer_strings(
        active_changers
    )
    lines += ["", er_misc_funcs.add_line_breaks(copy_prompt)]
    return "\n".join(lines)


def copy_changer_loop(active_changers):
    def copy_changer(active_changers, changer_i):
        new_changer = copy.deepcopy(active_changers[changer_i])
        active_changers[len(active_changers)] = new_changer

    if not active_changers:
        input(
            "   No active filters or transformers. Press <enter> to continue."
        )
        return
    prompt = update_copy_changer_prompt(active_changers)
    answer = input(prompt).lower()
    while True:
        if answer == "":
            return
        try:
            answer = int(answer) - 1
        except ValueError:
            answer = input("Invalid input, try again: ")
            continue
        if answer not in active_changers:
            answer = input("Invalid input, try again: ")
            continue
        copy_changer(active_changers, answer)
        return


def update_prompt_for_adjusting_changers(active_changers):
    select_prompt = (
        "Enter the number corresponding to the filter or "
        "transformer you would like to adjust, 'a'/'c'/'m' to "
        "add/copy/move a filter or transformer, or "
        "<enter> to continue: "
    )
    empty_select_prompt = (
        "Enter 'a' to add a filter or transformer, or <enter> to return to the "
        "main prompt: "
    )
    lines = [
        "",
        er_misc_funcs.make_header(SELECT_HEADER),
        "",
    ] + get_changer_strings(active_changers)
    lines += [
        "",
        er_misc_funcs.add_line_breaks(
            select_prompt if active_changers else empty_select_prompt
        ),
    ]
    return "\n".join(lines)


def select_changer_prompt(active_changers, score, changer_counter):
    clear()
    prompt = update_prompt_for_adjusting_changers(active_changers)
    answer = input(prompt).lower()
    while True:
        if answer == "":
            return False
        if answer == "a":
            add_changer_loop(active_changers, score, changer_counter)
            return True
        if answer == "c":
            copy_changer_loop(active_changers)
            return True
        if answer == "m":
            move_changer_loop(active_changers)
            return True
        try:
            answer = int(answer) - 1
        except ValueError:
            answer = input("Invalid input, try again: ")
            continue
        if answer not in active_changers:
            answer = input("Invalid input, try again: ")
            continue
        adjust_changer_prompt(active_changers, answer)
        return True


def changer_interface(score, active_changers, changer_counter):

    first_loop = True

    # select changer loop:
    while True:
        if first_loop and not active_changers:
            add_changer_loop(active_changers, score, changer_counter)
        first_loop = False
        if not select_changer_prompt(active_changers, score, changer_counter):
            print("")
            break
    try:
        changed_pattern = er_changers.apply(score, active_changers)
    except Exception:  # pylint: disable=broad-except
        if er_globals.DEBUG:
            raise
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(
            exc_type, exc_value, exc_traceback, limit=5, file=sys.stdout
        )
        print(
            er_shell_constants.BOLD_TEXT
            + "There was an exception applying a changer.\n"
            "This is a bug in `efficient_rhythms`. I would be "
            "grateful if you would file an "
            f"issue at {er_globals.GITHUB_URL}" + er_shell_constants.RESET_TEXT
        )
        input("press <enter> to continue")
        changed_pattern = None

    print("")

    return changed_pattern, active_changers


def mac_open(midi_path):
    subprocess.run(["open", midi_path], check=False)


def verovio_interface(score, midi_path, verovio_arguments):
    verovio_prompt = "Enter output file type, or leave blank to cancel: "
    lines = ["", er_misc_funcs.make_header("Output notation"), ""]
    file_types = [".svg", ".png", ".pdf"]
    possible_values = [
        ".svg (requires Verovio)",
        ".png (requires Verovio and ImageMagick)",
        ".pdf (requires Verovio, ImageMagick, and img2pdf)",
    ]
    lines.extend([possible_values_prompt(possible_values), ""])
    print("\n".join(lines))
    while True:
        answer = input(er_misc_funcs.add_line_breaks(verovio_prompt))
        if not answer:
            print("Output notation cancelled")
            return
        try:
            answer = int(answer) - 1
        except ValueError:
            pass
        else:
            if 0 <= answer < len(possible_values):
                break
        print("Invalid input.")
    try:
        er_output_notation.run_verovio(
            score, midi_path, verovio_arguments, file_types[answer]
        )
    except subprocess.CalledProcessError as exc:
        er_output_notation.clean_up_temporary_notation_files()
        print(exc)
        input("press <enter> to continue")


def update_midi_type(er):
    """For writing voices and/or choirs to separate tracks."""

    def _update_midi_type_prompt():
        prompt_strs = [er_misc_funcs.make_header("Midi settings")]
        for param_i, (pretty_name, name) in enumerate(params):

            prompt_strs.append(
                make_changer_prompt_line(
                    param_i + 1, pretty_name, getattr(er, name)
                )
            )

        prompt_str = "\n".join(prompt_strs)
        return prompt_str

    def update_midi_type_param(param_i):
        name = params[param_i][1]
        setattr(er, name, bool(getattr(er, name)))

    update_prompt = er_misc_funcs.add_line_breaks(
        "Enter the number corresponding to the parameter you "
        "would like to toggle, or <enter> to continue: "
    )
    params = [
        ("Write voices to separate tracks", "voices_separate_tracks"),
        ("Write choirs to separate tracks", "choirs_separate_tracks"),
        ("Write choirs to separate channels", "choirs_separate_channels"),
        ("Write program changes", "write_program_changes"),
    ]
    prompt_str = _update_midi_type_prompt()
    print(prompt_str)
    while True:
        answer = input(update_prompt)
        while answer != "" and (
            not answer.isdigit() or int(answer) < 0 or int(answer) > len(params)
        ):
            answer = input("Invalid input, try again: ")
        if answer == "":
            break
        param_to_update = int(answer) - 1
        update_midi_type_param(param_to_update)
        prompt_str = _update_midi_type_prompt()
        print(prompt_str)


def fail_and_exit(exc, random_failures=None):
    if random_failures is not None:
        msg = (
            "Failed to find realizable random settings after "
            f"{random_failures} attempts. If this keeps happening, it "
            "is probably some sort of bug with this script---please "
            "report it!"
        )
    else:
        msg = (
            "The script failed to build the pattern. You can always try "
            "again with a different seed (if you didn't explicitly set the "
            "seed, then a new seed will be chosen automatically next time "
            "you run the script), but you may have to make your settings "
            "more permissive (you might be able to get some hints as to "
            "how from the above failure counts)."
        )
    print(
        "\n".join(
            [
                "",
                er_misc_funcs.make_header("UNABLE TO BUILD PATTERN"),
                exc.__str__(),
                "",
                er_misc_funcs.add_line_breaks(
                    msg,
                    indent_type="none",
                ),
            ]
        )
    )
    sys.exit(1)


def input_loop(er, score, args, active_changers):
    """Run the user input loop for efficient_rhythms"""

    def get_input_prompt():
        return "".join(
            [
                "Press:\n",
                "    'a' to apply filters and/or transformers\n",
                (
                    "    'o' to open midi file with macOS 'open' command\n"
                    if sys.platform.startswith("darwin")
                    else ""
                ),
                "    'v' to write notation using Verovio\n",
                (
                    "    'p' to print out text representation of score\n"
                    "    'b' to enter a breakpoint (for debugging)\n"
                    if er_globals.DEBUG
                    else ""
                ),
                (
                    "    'c' to change how 'voices' and 'choirs' are "
                    "mapped to midi tracks and channels\n"
                    if isinstance(er, er_settings.ERSettings)
                    else ""
                ),
                (
                    "    's' to stop playback\n"
                    if playback_on
                    else "'<enter>' to play again\n"
                ),
                "    'q' to quit\n",
            ]
        )

    midi_player = er_playback.init_and_return_midi_player(shell=args.midi_port)
    playback_on = True
    # we set non_empty to True because this function should only be called
    # when the initial midi file exists and is non-empty
    non_empty = True
    if isinstance(er, er_settings.ERSettings) or os.path.exists(er.output_path):
        midi_path = er.output_path
    else:
        midi_path = er.original_path

    answer = ""
    changer_counter = collections.Counter()
    current_pattern = score
    changer_midi_i = 0
    current_midi_path = midi_path
    breaker = er_midi.Breaker()

    while True:
        print("File name:", print_path(current_midi_path, offset=11))
        if answer == "":
            if non_empty:
                breaker.reset()
                er_playback.playback_midi(
                    midi_player, breaker, current_midi_path
                )
                playback_on = True
            else:
                print("Midi file is empty, nothing to write or play!")
        answer = input(get_input_prompt()).lower()

        if answer in ("q", "s"):
            er_playback.stop_playback_midi(midi_player, breaker)
            if answer == "q":
                break
            playback_on = False

        elif answer == "a":
            changed_pattern, active_changers = changer_interface(
                score, active_changers, changer_counter
            )
            if changed_pattern is not None and active_changers:
                changer_midi_i += 1
                if isinstance(er, er_settings.ERSettings):
                    current_midi_path = er_misc_funcs.get_changed_midi_path(
                        midi_path
                    )
                    non_empty = er_midi.write_er_midi(
                        er, changed_pattern, current_midi_path
                    )
                else:
                    current_midi_path = er.output_path
                    non_empty = er_midi.write_midi(changed_pattern, er)
                current_pattern = changed_pattern
            else:
                current_midi_path = midi_path
                current_pattern = score
            answer = ""

        if answer == "c" and isinstance(er, er_settings.ERSettings):
            update_midi_type(er)
            non_empty = er_midi.write_er_midi(
                er, current_pattern, current_midi_path
            )

        elif answer == "o":
            mac_open(current_midi_path)

        elif answer == "v":
            verovio_interface(
                current_pattern, current_midi_path, args.verovio_arguments
            )

        elif er_globals.DEBUG and answer == "p":
            print(current_pattern.head())

        elif er_globals.DEBUG and answer == "b":
            breakpoint()
