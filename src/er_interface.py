"""Provides the user interface for efficient_rhythms.py
"""
import argparse
import collections
import copy
import math
import os
import subprocess
import sys
import traceback

import src.er_changers as er_changers
import src.er_midi as er_midi
import src.er_misc_funcs as er_misc_funcs
import src.er_output_notation as er_output_notation
import src.er_playback as er_playback
import src.er_prob_funcs as er_prob_funcs
import src.er_settings as er_settings
import src.er_shell_constants as er_shell_constants


SELECT_HEADER = "Active filters and transformers"
FILTERS_HEADER = "Filters"
TRANSFORMERS_HEADER = "Transformers"
GITHUB_URL = "https://github.com/malcolmsailor/efficient_rhythms"


def clear():  # from https://stackoverflow.com/a/684344/10155119
    os.system("cls" if os.name == "nt" else "clear")


def line_width():
    try:
        return os.get_terminal_size().columns
    except OSError:
        return 80


class BuildStatusPrinter:
    # header_strs = {
    #     "attempt_strs": ("Overall attempt:", "Attempt:"),
    #     "initial_pattern_strs": ("Initial pattern:", "IP:",),
    #     "voice_leading_strs": ("Voice-leading:", "VL:",),
    # }
    _spin_segments = "|/-\\"
    ip_header_strs = [
        "No pcs",
        "No pitches",
        "M interval",
        "Parallels",
        "Alternates",
        "Repeats",
        "Loops",
    ]
    ip_col_width = max(len(item) for item in ip_header_strs)
    vl_header_strs = [
        "Range",
        "H interval",
        "Dissonant",
        "M interval",
        "Parallels",
    ]
    vl_col_width = max(len(item) for item in vl_header_strs)

    def _get_header(self, er):
        attempt_digits = math.ceil(math.log10(er.voice_leading_attempts))
        attempt_num_str = f"{{:>{attempt_digits}}}/{er.voice_leading_attempts} "
        # attempt_len = 2 * attempt_digits + 2
        ip_digits = math.ceil(math.log10(er.initial_pattern_attempts))
        ip_num_str = f"{{:>{ip_digits}}}/{er.initial_pattern_attempts} "
        # ip_len = 2 * ip_digits + 1
        # vl_digits = math.ceil(math.log10(er.voice_leading_attempts))
        # vl_num_str = f"{{:>{vl_digits}}}/{er.voice_leading_attempts} "
        # vl_len = 2 * vl_digits + 1
        # total_num_len = attempt_len + ip_len + vl_len
        # num_joins = 5

        # for i, join_ch in itertools.product(range(2), (" ", "")):
        #     text_len = sum([len(item[i]) for item in self.header_strs.values()])
        #     # 2 added for width of spinning line
        #     if text_len + total_num_len + num_joins + 2 < self.line_width:
        #         break
        # self._header_fmt_str = join_ch.join(
        #     [
        #         self.header_strs["attempt_strs"][i],
        #         attempt_num_str,
        #         self.header_strs["initial_pattern_strs"][i],
        #         ip_num_str,
        #         self.header_strs["voice_leading_strs"][i],
        #         vl_num_str,
        #     ]
        # )
        self._total_header_fmt_str = (
            f"Building pattern: overall attempt {attempt_num_str}"
        )
        self._ip_header_fmt_str = f"Initial pattern attempt {ip_num_str}"

    def __init__(self, er):
        # We hope that the user doesn't change the window width too much during
        # building!
        self.line_width = line_width()
        self._get_header(er)
        self.ip_n_cols = min(
            math.floor(self.line_width / (self.ip_col_width + 2)),
            len(self.ip_header_strs),
        )
        self.ip_header_strs = self.ip_header_strs[: self.ip_n_cols]
        self.vl_n_cols = min(
            math.floor(self.line_width / (self.vl_col_width + 2)),
            len(self.vl_header_strs),
        )
        self.vl_header_strs = self.vl_header_strs[: self.vl_n_cols]
        self.spin_i = -1
        self.total_attempt_count = 0
        self.ip_attempt_count = 0
        self.initial_print()

    def increment_ip_attempt(self):
        self.ip_attempt_count += 1

    def increment_total_attempt_count(self):
        self.total_attempt_count += 1
        self.print_header()

    def reset_ip_attempt_count(self):
        self.ip_attempt_count = 0

    @property
    def _spinning_line(self):
        self.spin_i += 1
        return self._spin_segments[self.spin_i % 4]

    @property
    def header(self):
        return er_misc_funcs.make_header(
            self._total_header_fmt_str.format(self.total_attempt_count),
            fill_char="=",
            bold=True,
        )

    def spin(self):
        print(f"\r{self._spinning_line} ", end="")

    @staticmethod
    def _table(subhead, colheads, n_cols, col_width, *vals):
        return "\n".join(
            [
                er_misc_funcs.make_header(
                    subhead, fill_char="-", bold=False, indent=4,
                ),
                er_misc_funcs.make_table(
                    [
                        colheads,
                        [
                            "{} ({})".format(val[0], val[1])
                            for val in vals[:n_cols]
                        ],
                    ],
                    divider="",
                    borders=False,
                    col_width=col_width,
                ),
            ]
        )

    def ip_table(self, vals):
        return self._table(
            self._ip_header_fmt_str.format(self.ip_attempt_count),
            self.ip_header_strs,
            self.ip_n_cols,
            self.ip_col_width,
            *vals,
        )

    def vl_table(self, vals):
        return self._table(
            "Voice-leading dead-ends: ",
            self.vl_header_strs,
            self.vl_n_cols,
            self.vl_col_width,
            *vals,
        )

    def voice_leading_status(self, *vals):
        print(er_shell_constants.START_OF_PREV_LINE * 3, end="")
        print(self.vl_table(vals))
        assert (
            self.vl_table(vals).count("\n") == 2
        ), 'self.vl_table(vals).count("\n") != 2'
        self.spin()
        # breakpoint()

    def initial_pattern_status(self, *vals):
        print(er_shell_constants.START_OF_PREV_LINE * 6, end="")
        print(
            self.ip_table(vals), end=er_shell_constants.START_OF_NEXT_LINE * 4
        )
        self.spin()
        # breakpoint()

    def print_header(self):
        print(er_shell_constants.START_OF_PREV_LINE * 7, end="")
        print(self.header, end=er_shell_constants.START_OF_NEXT_LINE * 7)
        # breakpoint()

    def initial_print(self):
        # print(
        #     "\n"
        #     + er_shell_constants.BOLD_TEXT
        #     + "Building pattern..."
        #     + er_shell_constants.RESET_TEXT,
        # )
        print("")
        print(self.header)
        print(self.ip_table([(0, 0) for _ in range(self.ip_n_cols)]))
        print(self.vl_table([(0, 0) for _ in range(self.vl_n_cols)]))
        # breakpoint()

    @staticmethod
    def success():
        print(
            "\r"
            + er_shell_constants.BOLD_TEXT
            + "Success!"
            + er_shell_constants.RESET_TEXT,
            end="\n\n",
        )
        # breakpoint()


def parse_cmd_line_args():
    parser = argparse.ArgumentParser(
        description=(
            "Generates a splendiferous midi file. "
            "Settings are accessed by editing er_settings.py\n"
        )
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
    #     help="Maximum denominator for attack/durations for midi file specified "
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
    parser.add_argument(
        "--debug",
        action="store_true",
        help="provide option to enter a breakpoint in user input loop",
    )
    # LONGTERM
    # parser.add_argument(
    #     "--filters",
    # )
    args = parser.parse_args()

    return args


def print_hello():
    title = "Efficient rhythms: generate splendiferous midi loops"
    underline = "=" * min(len(title), line_width())
    print(
        "\n".join(
            [
                er_shell_constants.BOLD_TEXT + title,
                underline + er_shell_constants.RESET_TEXT,
                GITHUB_URL,
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
    if attribute.startswith("prob_func."):
        obj = changer.prob_func
        attribute = attribute[10:]
    else:
        obj = changer
    header_text = obj.pretty_name + ": " + obj.interface_dict[attribute]
    validator = obj.validation_dict[attribute]
    if validator.type_ == bool and validator.unique:  # review
        setattr(obj, attribute, bool(getattr(obj, attribute)))
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
            if attribute == "prob_func":
                update_prob_func(obj, validated)
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
    for i, changer in changer_dict.items():
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
        elif answer in ("x", ""):
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


def select_changer_prompt(
    changer_dict, active_changers, score, changer_counter
):
    clear()
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


def changer_interface(super_pattern, active_changers, changer_counter, debug):
    def _get_changers():
        i = 1
        changer_dict = {}
        for filter_ in er_changers.FILTERS:
            changer_dict[i] = getattr(er_changers, filter_)
            i += 1
        # The next dictionary entry is added to mark the boundary
        #   between filters and transformers.
        changer_dict[-1] = None
        for transformer in er_changers.TRANSFORMERS:
            changer_dict[i] = getattr(er_changers, transformer)
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
        except er_changers.ChangeFuncError as err:
            # CHANGER_TODO are ChangeFuncErrors also bugs? Should they be caught below?
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
        except Exception:  # pylint: disable=broad-except
            if debug:
                raise
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(
                exc_type, exc_value, exc_traceback, limit=5, file=sys.stdout
            )
            print(
                er_shell_constants.BOLD_TEXT
                + "There was an exception applying "
                f"{active_changer.pretty_name}\n"
                "This is a bug in `efficient_rhythms.py`. I would be "
                "grateful if you would file an "
                f"issue at {GITHUB_URL}" + er_shell_constants.RESET_TEXT
            )
            input("press <enter> to continue")
    print("")

    if not success:
        return None, active_changers
    return copied_pattern, active_changers


def mac_open(midi_path):
    subprocess.run(["open", midi_path], check=False)


def verovio_interface(super_pattern, midi_path, verovio_arguments):
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
            super_pattern, midi_path, verovio_arguments, file_types[answer]
        )
    except er_misc_funcs.ProcError as exc:
        er_output_notation.clean_up_temporary_notation_files()
        print(exc)
        input("press <enter> to continue")


def update_midi_type(er):
    """For writing voices and/or choirs to separate tracks.
    """

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


def failure_message(exc, random_failures=None):
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
                er_misc_funcs.add_line_breaks(msg, indent_type="none",),
            ]
        )
    )
    sys.exit(1)


def input_loop(
    er, super_pattern, midi_player, verovio_arguments=None, debug=False
):
    """Run the user input loop for efficient_rhythms.py
    """

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
                    if debug
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

    playback_on = True
    # we set non_empty to True because this function should only be called
    # when the initial midi file exists and is non-empty
    non_empty = True
    if isinstance(er, er_settings.ERSettings) or os.path.exists(er.output_path):
        midi_path = er.output_path
    else:
        midi_path = er.original_path

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
                super_pattern, active_changers, changer_counter, debug
            )
            if changed_pattern is not None and active_changers:
                # LONGTERM allow specification of transformers from external
                #    settings files
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
                current_pattern = super_pattern
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
                current_pattern, current_midi_path, verovio_arguments
            )

        elif debug and answer == "p":
            print(current_pattern.head())

        elif debug and answer == "b":
            breakpoint()
