"""Provides the user interface for efficient_rhythms.py
"""
import argparse
import collections
import copy
import os
import subprocess
import sys
import threading

import pygame

from mal_str import make_header

import er_filters
import er_midi
import er_misc_funcs
import er_output_notation

import er_prob_funcs


SOUND_FONT = "/Users/Malcolm/Music/SoundFonts/GeneralUser GS 1.471/GeneralUser_GS_v1.471.sf2"
NOTE_DIR = "/Users/Malcolm/Google Drive/Notes/"

LINE_WIDTH = os.get_terminal_size().columns
SELECT_HEADER = "Active filters and transformers"
FILTERS_HEADER = "Filters"
TRANSFORMERS_HEADER = "Transformers"


def parse_cmd_line_args():
    parser = argparse.ArgumentParser(
        description=(
            "Generates a splendiferous midi file. "
            "Settings are accessed by editing er_settings.py\n"
        )
    )
    parser.add_argument(
        "-f", help="path to a midi file to be filtered and" "/or transformed"
    )
    parser.add_argument(
        "-t",
        "--tet",
        help="TET of input midi file specified with -m",
        default=12,
        type=int,
    )
    parser.add_argument(
        "-m",
        "--midi-port",
        help="send midi via a virtual port for use in a DAW, "
        "rather than using in-shell midi player",
        action="store_false",
    )
    parser.add_argument("-r", help="randomize settings", action="store_true")
    parser.add_argument(
        "-ts",
        help="Time signature to use with midi file "
        "specified with -f, format m/n",
    )
    parser.add_argument(
        "-d",
        help="Maximum denominator for attack/durations for midi file specified "
        "with -f",
        default=0,
        type=int,
    )
    parser.add_argument(
        "-s",
        "--settings",
        help="path to settings file containing a Python dictionary",
    )
    args = parser.parse_args()

    return args


def get_changed_midi_path(midi_path):
    dirname, basename = os.path.split(midi_path)
    if not dirname:
        dirname = os.getcwd()
    no_ext = basename[:-4]
    prev_fnames = []
    for fname in os.listdir(dirname):
        if fname.startswith(no_ext) and fname != basename:
            prev_fnames.append(fname)
    prev_num_strs = [
        prev_fname[:-4].replace(no_ext + "_", "") for prev_fname in prev_fnames
    ]
    prev_nums = []
    for prev_num_str in prev_num_strs:
        try:
            prev_nums.append(int(prev_num_str))
        except ValueError:
            pass
    if prev_nums:
        num = max(prev_nums) + 1
    else:
        num = 1
    new_basename = no_ext + "_" + str(num).zfill(2) + ".mid"
    return os.path.join(dirname, new_basename)


def playback_midi(midi_player, breaker, midi_path):
    """Plays a midi file.
    """
    if midi_player == "pygame":
        pygame.mixer.music.load(midi_path)
        pygame.mixer.music.play()
    elif midi_player == "fluidsynth":
        subprocess.run(["fluidsynth", SOUND_FONT, midi_path], check=False)
    elif midi_player == "self":
        playback_thread = threading.Thread(
            target=er_midi.playback,
            args=[midi_path, breaker],
            kwargs={"multi_output": False},
        )
        playback_thread.start()


def stop_playback_midi(midi_player, breaker):
    if midi_player == "pygame":
        pygame.mixer.music.stop()
    elif midi_player == "self":
        breaker.break_ = True
        breaker.reset()


def print_path(in_path, offset=0):
    if len(in_path) < LINE_WIDTH:
        return in_path
    while "/" in in_path:
        in_path = in_path.split("/", maxsplit=1)[1]
        if len(in_path) < LINE_WIDTH - 4 - offset:
            return ".../" + in_path
    return in_path


# def make_header(text):
#     return " " + text + " " + "#" * (LINE_WIDTH - len(text) - 2)


def make_changer_prompt_line(i, attr_name, value, hint_name="", hint_value=""):
    num_str = f"({i})"
    out = f"{num_str:>8} {attr_name}: {value}"
    if hint_name:
        if hint_value:
            hint_str = f"{hint_name}: {hint_value:<10}"
        else:
            hint_str = hint_name + " " * 2
        if len(out) + len(hint_str) > LINE_WIDTH - 2:
            hint_str_formatted = er_misc_funcs.add_line_breaks(
                hint_str, indent_type="all", indent_width=16, align="right"
            )
            out = out + "\n" + hint_str_formatted
        else:
            out = out + " " * (LINE_WIDTH - len(out) - len(hint_str)) + hint_str
    return out


def make_prompt_line(i, line):
    num_str = f"({i})"
    out = f"{num_str:>8} {line}"
    return out


def add_to_changer_attribute_dict(
    obj, lines, attribute_dict, attribute_i, prefix=""
):
    attributes = vars(obj)
    for attribute, value in attributes.items():
        if (
            attribute not in obj.interface_dict
            or attribute == "prob_func"
            or not obj.display(attribute)
        ):
            continue
        if isinstance(value, list) and len(value) == 1:
            value = value[0]
        if isinstance(value, er_prob_funcs.ProbFunc):
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


def possible_values_prompt(lines, possible_values):
    for pv_i, possible_value in enumerate(possible_values):
        lines.append(make_prompt_line(pv_i + 1, possible_value))
    lines.append("")


def update_changer_attribute(changer, attribute):
    update_prompt = (
        "Enter new value (or values, separated by commas), "
        "'h' for possible values, or leave blank to cancel: "
    )
    if attribute.startswith("prob_func."):
        obj = changer.prob_func
        attribute = attribute.replace("prob_func.", "")
    else:
        obj = changer
    header_text = obj.pretty_name + ": " + obj.interface_dict[attribute]
    lines = ["", make_header(header_text), ""]
    validator = obj.validation_dict[attribute]
    if validator.type_ == bool and validator.unique:
        setattr(obj, attribute, bool(getattr(obj, attribute)))
        # if vars(obj)[attribute]:
        #     vars(obj)[attribute] = False
        # else:
        #     vars(obj)[attribute] = True
        return
    if validator.possible_values:
        possible_values_prompt(lines, validator.possible_values)
    print("\n".join(lines))
    answer = input(er_misc_funcs.add_line_breaks(update_prompt))
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
            if attribute == "prob_func":
                update_prob_func(obj, validated)
            else:
                setattr(obj, attribute, validated)
                # vars(obj)[attribute] = validated
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
    lines = ["", make_header(changer.pretty_name), ""]
    attribute_i = 1
    attribute_dict = {}
    prob_func_name = changer.interface_dict["prob_func"]
    lines.append(
        make_changer_prompt_line(
            attribute_i, prob_func_name, changer.prob_func.pretty_name
        )
    )
    attribute_dict[attribute_i] = "prob_func"
    attribute_i += 1
    attribute_i = add_to_changer_attribute_dict(
        changer.prob_func,
        lines,
        attribute_dict,
        attribute_i,
        prefix="prob_func.",
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
            except er_filters.ChangeFuncError as err:
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
            for i in active_changers:
                if i > 0 and i - 1 not in active_changers:
                    j = i - 1
                    while j >= 0 and j - 1 not in active_changers:
                        j -= 1
                    active_changers[j] = active_changers[i]
                    del active_changers[i]
            break
        answer = int(answer)
        attribute = attribute_dict[answer]
        update_changer_attribute(changer, attribute)
        prompt, attribute_dict = update_adjust_changer_prompt(changer)


def add_changer_prompt(changer_dict):

    add_prompt = (
        "Enter the number corresponding to the filter or transformer "
        "you would like to select, or <enter> to continue: "
    )
    lines = ["", make_header(FILTERS_HEADER), ""]
    for i, changer in changer_dict.items():
        if i == -1:
            lines += ["", make_header(TRANSFORMERS_HEADER), ""]
        else:
            lines.append(make_prompt_line(i, changer.pretty_name))
    lines += [
        "",
    ]
    lines.append(er_misc_funcs.add_line_breaks(add_prompt))
    return "\n".join(lines)


def update_prob_func(changer, prob_func_name):
    new_prob_func = vars(er_prob_funcs)[prob_func_name]()
    old_prob_func = changer.prob_func
    for attr, value in vars(old_prob_func).items():
        if attr in new_prob_func.interface_dict:
            setattr(new_prob_func, attr, value)
        # if attr in vars(new_prob_func)["interface_dict"]:
        # vars(new_prob_func)[attr] = value

    changer.prob_func = new_prob_func


def add_changer_loop(changer_dict, active_changers, score, changer_counter):

    answer = input(add_changer_prompt(changer_dict)).lower()

    while True:
        if answer.isdigit():
            if int(answer) in changer_dict:
                break
        elif answer == "x":
            return
        answer = input(
            er_misc_funcs.add_line_breaks(
                "Invalid input. Please enter the digit corresponding "
                "to a filter or transformer above, or 'x' to cancel: "
            )
        ).lower()

    changer = changer_dict[int(answer)](score, changer_counter=changer_counter)

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
    lines = ["", make_header(header), ""] + get_changer_strings(active_changers)
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
    # MAYBE replace this individual functions with a single function
    # that takes a header, and a prompt
    header = "Copy filters or transformers"
    copy_prompt = (
        "Enter the number corresponding to the filter or "
        "transformer you would like to copy, or <enter> to "
        "continue: "
    )
    lines = ["", make_header(header), ""] + get_changer_strings(active_changers)
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
    lines = ["", make_header(SELECT_HEADER), ""] + get_changer_strings(
        active_changers
    )
    lines += ["", er_misc_funcs.add_line_breaks(select_prompt)]
    return "\n".join(lines)


def select_changer_prompt(
    changer_dict, active_changers, score, changer_counter
):

    prompt = update_prompt_for_adjusting_changers(active_changers)
    answer = input(prompt).lower()
    while True:
        if answer == "":
            return False
        if answer == "a":
            add_changer_loop(
                changer_dict, active_changers, score, changer_counter
            )
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


def changer_interface(super_pattern, active_changers, changer_counter):
    def _get_changers():
        filters = []
        transformers = []
        for item in dir(er_filters):
            if "Filter" in item:
                filters.append(getattr(er_filters, item))
                # filters.append(vars(er_filters)[item])
            if "Transformer" in item and item != "Transformer":
                transformers.append(getattr(er_filters, item))
                # transformers.append(vars(er_filters)[item])

        i = 1
        changer_dict = {}
        for filter_ in filters:
            changer_dict[i] = filter_
            i += 1
        # The next dictionary entry is added to mark the boundary
        #   between filters and transformers.
        changer_dict[-1] = None
        for transformer in transformers:
            changer_dict[i] = transformer
            i += 1

        return changer_dict

    changer_dict = _get_changers()

    first_loop = True

    # select changer loop:
    while True:
        if first_loop and not active_changers:
            add_changer_loop(
                changer_dict, active_changers, super_pattern, changer_counter
            )
        first_loop = False
        if not select_changer_prompt(
            changer_dict, active_changers, super_pattern, changer_counter
        ):
            print("")
            break

    copied_pattern = copy.deepcopy(super_pattern)
    success = False
    if active_changers:
        print("Applying:")

    for active_changer in active_changers.values():
        print(f"    {active_changer.pretty_name}... ", end="")
        try:
            active_changer.apply(copied_pattern)
            print("done.")
            success = True
        except er_filters.ChangeFuncError as err:
            print("ERROR!")
            print(
                er_misc_funcs.add_line_breaks(
                    err.args[0], indent_width=8, indent_type="all"
                )
            )
            input(
                er_misc_funcs.add_line_breaks(
                    "Press enter to continue",
                    indent_width=12,
                    indent_type="all",
                )
            )
    print("")

    if not success:
        return None, active_changers
    return copied_pattern, active_changers


def mac_open(midi_path):
    subprocess.run(["open", midi_path], check=False)


def run_verovio(super_pattern, midi_path):

    copied_pattern = copy.deepcopy(super_pattern)
    copied_pattern.fill_with_rests(super_pattern.get_total_len())

    kern_path = midi_path.replace(".mid", ".krn")
    dirname = os.path.dirname(kern_path)

    er_output_notation.write_kern(copied_pattern, kern_path)
    er_output_notation.write_notation(kern_path, dirname)


def update_midi_type(er):
    """For writing voices and/or choirs to separate tracks.
    """

    def _update_midi_type_prompt():
        prompt_strs = [make_header("Midi settings")]
        for param_i, (pretty_name, name) in enumerate(params):
            # val = vars(er)[name]

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
        # val = vars(er)[name]
        # if val:
        #     val = False
        # else:
        #     val = True
        # vars(er)[name] = val

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


def input_loop(er, super_pattern, midi_player, midi_path):
    """Run the user input loop for efficient_rhythms.py
    """

    def get_input_prompt():
        return (
            "Press:\n"
            "    'a' to apply filters and/or transformers\n"
            + (
                "    'o' to open with macOS 'open' command\n"
                if sys.platform == "darwin"
                else ""
            )
            + "    'v' to write to PDF using Verovio\n"
            "    'p' to print out text representation of score\n"
            "    'b' to enter a breakpoint (for debugging)\n"
            "{}"
            "    {}\n"
            "    'q' to quit\n"
            "".format(
                "    'c' to change writing of voices "
                "and choirs to midi tracks\n"
                if er
                else "",
                "'s' to stop playback"
                if playback_on
                else "'<enter>' to resume playback",
            )
        )

    playback_on = True

    answer = ""

    active_changers = {}
    changer_counter = collections.Counter()
    current_pattern = super_pattern
    changer_midi_i = 0
    current_midi_path = midi_path
    breaker = er_midi.Breaker()

    while True:
        print("File name:", print_path(current_midi_path, offset=11))
        if answer == "":
            breaker.reset()
            playback_midi(midi_player, breaker, current_midi_path)
            playback_on = True
        answer = input(get_input_prompt()).lower()

        if answer in ("q", "s"):
            stop_playback_midi(midi_player, breaker)
            if answer == "q":
                break
            playback_on = False

        elif answer == "a":
            changed_pattern, active_changers = changer_interface(
                super_pattern, active_changers, changer_counter
            )
            if changed_pattern is not None and active_changers:
                changer_midi_i += 1
                changed_midi_path = get_changed_midi_path(midi_path)
                if er:
                    er_midi.write_er_midi(
                        er, changed_pattern, changed_midi_path
                    )
                else:
                    er_midi.write_midi(changed_pattern, changed_midi_path)
                current_midi_path = changed_midi_path
                current_pattern = changed_pattern
            else:
                current_midi_path = midi_path
                current_pattern = super_pattern
            answer = ""

        if answer == "c":
            update_midi_type(er)
            er_midi.write_er_midi(er, current_pattern, current_midi_path)

        elif answer == "o":
            mac_open(current_midi_path)

        elif answer == "v":
            run_verovio(current_pattern, current_midi_path)

        elif answer == "p":
            print(current_pattern.head())

        elif answer == "b":
            breakpoint()
