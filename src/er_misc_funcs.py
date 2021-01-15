"""Misc. functions for efficient_rhythms2.py.
"""

import fractions
import itertools
import math
import os
import random
import typing

import numpy as np

MAX_DENOMINATOR = 8192


def check_modulo(n, mod):
    """ arguments:
            mod: an int, or a list. If an int just returns n % mod.
                If a list, needs to be in 'cumulative' format.
    """
    try:
        return n % mod
    except TypeError:
        pass
    total_mod = max(mod)

    x_vals = []
    for m in mod:
        x = (n - m) % total_mod
        if x > total_mod / 2:
            x = abs(x - total_mod)
        x_vals.append(x)

    return min(x_vals)


def add_line_breaks(
    in_str,
    line_width=None,
    indent_type="hanging",
    indent_width=4,
    indent_char=" ",
    align="left",
    join=True,
    fill=False,
    force_breaks=True,
    preserve_trailing_ws=True,
):
    """Adds line breaks to a string for printing in the shell.

    Keyword args:
        line_width: int. If None, taken from os.get_terminal_size().
        indent_type: str. "hanging", "leading", "all", or "none". Default
            "hanging".
        indent_width: int.
        indent_char: Char to use for indentation. Default = " ".
        align: str. "left", "center", or "right".
        join: boolean. If true, return a single string joined by new lines.
            If false, returns a list of strings.
        fill: boolean. If true, all lines will be filled to the full length
            with space characters.
        force_breaks: whether to break words in the event that a single word
            is longer than one line.
        preserve_trailing_ws: whether to preserve trailing whitespace
            at the end of `in_str`. Even if True, will not add trailing
            whitespace to the last line if that leads to it being more
            than one line long. Default: True

    """

    def align_line(line, current_line_width, align):
        line = line.strip()
        if align == "right":
            return (current_line_width - len(line)) * " " + line
        if align == "center":
            before = math.ceil((current_line_width - len(line)) / 2)
            after = math.floor((current_line_width - len(line)) / 2)
            return before * " " + line + after * " "
        if align == "left" and fill:
            return line + (current_line_width - len(line)) * " "
        return line

    if preserve_trailing_ws:
        for i in range(len(in_str) - 1, -1, -1):
            if not in_str[i].isspace():
                break
        trailing_ws = in_str[i + 1 :]
    if line_width is None:
        try:
            line_width = os.get_terminal_size().columns
        except OSError:
            # thrown when running pylint
            line_width = 80
    lines = []
    start_line_i = 0
    last_whitespace_i = 0
    line_i = 0
    if indent_type in ("leading", "all"):
        current_line_width = line_width - indent_width
    else:
        current_line_width = line_width
    for char_i, char in enumerate(in_str):
        if indent_type in ("hanging", "all") and line_i > 0:
            current_line_width = line_width - indent_width
        elif indent_type == "leading" and line_i > 0:
            current_line_width = line_width
        if char.isspace():
            last_whitespace_i = char_i
        if char == "\n":
            lines.append(
                align_line(
                    in_str[start_line_i:char_i], current_line_width, align
                )
            )
            start_line_i = char_i + 1
            line_i += 1
        if char_i - start_line_i >= current_line_width:
            if last_whitespace_i > start_line_i:
                line_break_i = last_whitespace_i
            elif force_breaks:
                line_break_i = char_i
            line = align_line(
                in_str[start_line_i:line_break_i], current_line_width, align
            )
            lines.append(line)
            start_line_i = line_break_i + 1
            line_i += 1

    line = align_line(in_str[start_line_i:], current_line_width, align)
    lines.append(line)
    spacing_to_add = indent_width // 2 if align == "center" else indent_width
    if indent_type in ("hanging", "all"):
        temp_lines = [
            lines[0],
        ]
        for line in lines[1:]:
            temp_lines.append(spacing_to_add * indent_char + line)
        lines = temp_lines
    if indent_type in ("leading", "all"):
        lines[0] = spacing_to_add * indent_char + lines[0]
    if preserve_trailing_ws and len(lines[-1]) + len(trailing_ws) < line_width:
        lines[-1] = lines[-1] + trailing_ws
    if join:
        return "\n".join(lines)
    return lines


# def add_line_breaks(
#     in_str, line_width=None, indent_type="hanging", indent_width=4, align="left"
# ):
#     """Adds line breaks to a string for printing in the shell.
#
#     Keyword args:
#         line_width: int. Default None (a call to os.get_terminal_size is made).
#         indent_type: str. "hanging", "leading", "all", or "none". Default
#             "hanging".
#         indent_width: int.
#         align: str. "left", "center", or "right".
#
#     """
#
#     def align_line(line, current_line_width, align):
#         line = line.strip()
#         if align == "right":
#             return (current_line_width - len(line)) * " " + line
#         if align == "center":
#             before = math.ceil((current_line_width - len(line)) / 2)
#             after = math.floor((current_line_width - len(line)) / 2)
#             return before * " " + line + after * " "
#         return line
#
#     if line_width is None:
#         line_width = os.get_terminal_size().columns
#     lines = []
#     start_line_i = 0
#     last_whitespace_i = 0
#     line_i = 0
#     if indent_type in ("leading", "all"):
#         current_line_width = line_width - indent_width
#     else:
#         current_line_width = line_width
#     for char_i, char in enumerate(in_str):
#         if indent_type in ("hanging", "all") and line_i > 0:
#             current_line_width = line_width - indent_width
#         elif indent_type == "leading" and line_i > 0:
#             current_line_width = line_width
#         if char.isspace():
#             last_whitespace_i = char_i
#         if char == "\n":
#             lines.append(
#                 align_line(
#                     in_str[start_line_i:char_i], current_line_width, align
#                 )
#             )
#             start_line_i = char_i + 1
#             line_i += 1
#         if (
#             char_i - start_line_i > current_line_width
#             and last_whitespace_i > start_line_i
#         ):
#             line = align_line(
#                 in_str[start_line_i:last_whitespace_i],
#                 current_line_width,
#                 align,
#             )
#             lines.append(line)
#             start_line_i = last_whitespace_i + 1
#             line_i += 1
#     line = align_line(in_str[start_line_i:], current_line_width, align)
#     lines.append(line)
#     spacing_to_add = indent_width // 2 if align == "center" else indent_width
#     if indent_type in ("hanging", "all"):
#         temp_lines = [
#             lines[0],
#         ]
#         for line in lines[1:]:
#             temp_lines.append(spacing_to_add * " " + line)
#         lines = temp_lines
#     if indent_type in ("leading", "all"):
#         lines[0] = spacing_to_add * " " + lines[0]
#     return "\n".join(lines)


def no_empty_lists(item):
    if isinstance(item, (list, tuple)):
        if not item:
            return False
        for sub_item in item:
            if not no_empty_lists(sub_item):
                return False
    return True


def empty_nested(seq):
    """Check if all (non-str) sub-sequences of a (nested) sequence are empty.

    Returns True if empty, False otherwise.
    """

    def _sub(item):
        if isinstance(item, typing.Sequence) and not isinstance(item, str):
            for sub_item in item:
                if _sub(sub_item):
                    return True
            return False
        return True

    if _sub(seq):
        return False
    return True


def remove_non_existing_voices(iterable, num_voices, iter_name=None):
    out = []
    altered_output = False
    for item in iterable:
        if isinstance(item, (list, tuple)):
            sub_out = remove_non_existing_voices(item, num_voices)
            if sub_out is not None:
                altered_output = True
                if len(sub_out) > 0:
                    out.append(sub_out)
            else:
                out.append(item)
        else:
            if item >= num_voices:
                altered_output = True
                continue
            out.append(item)

    if altered_output:
        if iter_name:
            print("Removed non-existing voices from {}" "".format(iter_name))
        return out

    return iterable


def convert_to_fractions(item, max_denominator=MAX_DENOMINATOR):
    """Converts all numbers in an arbitrarily deep list or tuple
    to fractions.
    """

    try:
        iter(item)
        iterable = True
    except TypeError:
        iterable = False
    if iterable:
        out = []
        for sub_item in item:
            sub_item = convert_to_fractions(sub_item)
            out.append(sub_item)
        return out

    return fractions.Fraction(item).limit_denominator(
        max_denominator=max_denominator
    )


def flatten(item):
    """Flattens an iterable of iterables. Can contain irregularly nested
    iterables. Returns a list."""

    def _sub(item):
        try:
            iter(item)
            iterable = True
        except TypeError:
            iterable = False
        if iterable:
            out = []
            for sub_item in item:
                out += _sub(sub_item)
            return out

        return [
            item,
        ]

    out = []
    out += _sub(item)
    return out


def lcm(numbers, max_n=2 ** 15):
    """Can take any list, not necessarily a flat list.

    Converts all numbers to fractions.

    Returns an error if there's no lcm smaller than max_n.
    """

    class LCMError(Exception):
        pass

    def _lcm_sub(num1, num2):
        i = 1
        while True:
            if (num1 * i) % num2 == 0:
                return num1 * i
            i += 1
            if i * num1 > max_n:
                raise LCMError(
                    f"No common multiple of {num1} and {num2} smaller than "
                    f"{max_n}."
                )

    if 0 in numbers:
        raise LCMError(
            "Zero does not have common multiples with any other number."
        )

    numbers = flatten(numbers)
    numbers = convert_to_fractions(numbers)

    while True:
        if len(numbers) == 1:
            return numbers[0]
        new_numbers = []
        for j in range(0, len(numbers), 2):
            num1 = numbers[j]
            if j + 1 < len(numbers):
                num2 = numbers[j + 1]
                new_numbers.append(_lcm_sub(num1, num2))
            else:
                new_numbers.append(num1)
        numbers = new_numbers


def fraction_gcd(frac1, frac2, min_n=2 ** (-15)):
    """Returns the fractional GCD of two numbers."""

    class GCDError(Exception):
        pass

    result = fractions.Fraction(
        math.gcd(frac1.numerator, frac2.numerator),
        lcm([frac1.denominator, frac2.denominator,]),
    )

    if result < min_n:
        raise GCDError(f"No GCD larger than {min_n}.")

    return result


def gcd_from_list(*numbers, min_n=2 ** (-15)):
    """Can take any list, not necessarily a flat list. Converts all numbers
    to fractions.

    Any values of 0 in the input are ignored.
    """

    numbers = [number for number in flatten(numbers) if number != 0]
    numbers = convert_to_fractions(numbers)

    while True:
        if len(numbers) == 1:
            return numbers[0]
        new_numbers = []
        for j in range(0, len(numbers), 2):
            num1 = numbers[j]
            if j + 1 < len(numbers):
                num2 = numbers[j + 1]
                new_numbers.append(fraction_gcd(num1, num2, min_n=min_n))
            else:
                new_numbers.append(num1)

        numbers = new_numbers


def set_seed(seed):
    """If seed is None, sets random seed. Otherwise sets specified seed.
    Either way, returns seed value.
    """
    if seed is None:
        seed = random.randint(0, 2 ** 32)
    print("Seed: ", seed)

    random.seed(seed)
    np.random.seed(seed)

    return seed


def binary_search(num_list, num, not_found="none"):
    """Performs a binary search on a sorted list of numbers, returns index.

    Only works properly if the list is sorted, but does not check whether it is
    or not, this is up to the caller.

    Arguments:
        num_list: a sorted list of numbers.
        num: a number to search for.
        not_found: string. Controls what happens if the number is not in the
            list.
            - "none": None is returned.
            - "upper", "force_upper": upper index is returned
            - "lower", "force_lower": lower index is returned
            - "nearest": index to nearest item is returned
            If num is larger than all numbers in num_list,
                if "upper", "lower", "force_lower", or "nearest":
                    index to the last item of the list is returned.
                if "force_upper":
                    index to the next item past the end of the list is returned.
            If num is smaller than all numbers in num_list,
                if "upper", "force_upper", "lower", or "nearest":
                    0 is returned.
                if "force_lower":
                    -1 is returned.
            Default: None.

    returns:
        None if len(num_list) is 0
        None if num is not in num_list and not_found is "none"
        Integer index to item, or perhaps nearest item (depending on
            "not_found" keyword argument).
    """
    if not_found not in (
        "none",
        "upper",
        "force_upper",
        "lower",
        "force_lower",
        "nearest",
    ):
        raise ValueError(
            f"{not_found} is not a recognized value for argument " "'not_found'"
        )
    lower_i, upper_i = 0, len(num_list)
    if upper_i == 0:
        return None
    if num < num_list[0]:
        if not_found == "none":
            return None
        if not_found == "force_lower":
            return -1
        return 0
    if num > num_list[upper_i - 1]:
        if not_found == "none":
            return None
        if not_found == "force_upper":
            return upper_i
        return upper_i - 1

    while True:
        mid_i = (lower_i + upper_i) // 2
        n = num_list[mid_i]
        if n == num:
            return mid_i
        if mid_i == lower_i:
            if not_found == "none":
                return None
            if not_found in ("upper", "force_upper"):
                return upper_i
            if not_found in ("lower", "force_lower"):
                return lower_i
            return lower_i + (num_list[upper_i] - num < num - n)

        if n > num:
            upper_i = mid_i
        else:
            lower_i = mid_i


# def binary_search(num_list, num, favor="upper"):
#     """Returns the index to the item.
#
#     Arguments:
#         favor: str controlling behavior if item is not in list.
#             - "upper": upper index is returned
#             - "lower": lower index is returned
#             - otherwise: index to nearest item is returned.
#     """
#     lower_i = 0
#     upper_i = len(num_list)
#     if upper_i == 0:
#         return None
#     if upper_i == 1:
#         return lower_i
#     while True:
#         i = (lower_i + upper_i) // 2
#         n = num_list[i]
#         if n == num:
#             return i
#         if upper_i - lower_i == 1:
#             if favor == "upper":
#                 return upper_i
#             if favor == "lower":
#                 return lower_i
#             try:
#                 if num_list[upper_i] - num < num - num_list[lower_i]:
#                     return upper_i
#             except IndexError:
#                 if upper_i >= len(num_list):
#                     return lower_i
#                 return upper_i
#             return lower_i
#         if n > num:
#             upper_i = i
#         elif n < num:
#             lower_i = i


def get_changed_midi_path(midi_path):
    root, ext = os.path.splitext(midi_path)
    return increment_fname(root + "_00" + ext, n_digits=2)
    # if not dirname:
    #     dirname = os.getcwd()

    # no_ext = os.path.splitext(basename)[0]
    # prev_fnames = []
    # for fname in os.listdir(dirname):
    #     if fname.startswith(no_ext) and fname != basename:
    #         prev_fnames.append(fname)
    # prev_num_strs = [
    #     prev_fname[:-4].replace(no_ext + "_", "") for prev_fname in prev_fnames
    # ]
    # prev_nums = []
    # for prev_num_str in prev_num_strs:
    #     try:
    #         prev_nums.append(int(prev_num_str))
    #     except ValueError:
    #         pass
    # if prev_nums:
    #     num = max(prev_nums) + 1
    # else:
    #     num = 1
    # new_basename = no_ext + "_" + str(num).zfill(2) + ".mid"
    # return os.path.join(dirname, new_basename)


def increment_fname(
    path, n_digits=3, overwrite=False, allow_increase_n_digits=True
):
    def _sub(path, n_digits):
        def _get_int_at_end_of_string(string):
            i = 0
            while True:
                try:
                    int(string[-(i + 1) :])
                except ValueError:
                    if i == 0:
                        return None, string, n_digits
                    return int(string[-i:]), string[:-i], i
                i += 1

        root, ext = os.path.splitext(path)
        count, base_str, n_digits = _get_int_at_end_of_string(root)
        if count is None or count < 0:
            count = 0
        elif math.log10(count + 1) >= n_digits:
            if allow_increase_n_digits:
                n_digits += 1
            else:
                raise NotImplementedError("Too many digits to increment")
        i_str = str(count + 1).zfill(n_digits)
        return "".join([base_str, i_str, ext])

    while True:
        path = _sub(path, n_digits)
        if overwrite or not os.path.exists(path):
            return path


# def return_fname_path(script_name, script_dir):
#     """Construct the name of the midi file to generate (incrementing
#     the integer at the end until getting to a filename that
#     does not exist) as well as the dir within which to store it
#     (which will be of the form [script_dir]/script_name + "_midi").
#     """
#
#     script_str = os.path.splitext(script_name)[0]
#
#     fname_dir = os.path.join(script_dir, script_str + "_midi")
#     if not os.path.exists(fname_dir):
#         os.mkdir(fname_dir)
#     # if the script name ends with a digit, append an underscore
#     # to visually separate the file number from the script name
#     if script_str[-1].isdigit():
#         script_str = script_str + "_"
#
#     # find the existing file with the highest number
#     max_fnum = 0
#     for existing_f in os.listdir(fname_dir):
#         if existing_f.startswith(script_str) and existing_f.endswith(".mid"):
#             digits = []
#             digits_on = False
#             for char in existing_f[len(script_str) :]:
#                 if char.isdigit():
#                     digits.append(char)
#                     digits_on = True
#                 elif digits_on:
#                     break
#             digits = "".join(digits)
#             try:
#                 fnum = int(digits)
#
#                 # fnum = int(
#                 #     existing_f.replace(script_str, "").replace(".mid", ""))
#             except ValueError:
#                 pass
#             if fnum > max_fnum:
#                 max_fnum = fnum
#
#     fname = script_str + str(max_fnum + 1).zfill(3) + ".mid"
#     fname_path = os.path.join(fname_dir, fname)
#
#     return fname_path, fname_dir


def get_prev_voice_indices(score, start_time, dur):
    return score.get_sounding_voices(start_time, dur)


# def get_prev_voice_indices(er, voice_i, during_pattern_voice_leading=None):
#     """Returns the indices of the voices that have already been constructed,
#     as well as for previously existing voices.
#
#     If during_pattern_voice_leading, pass attack_time.
#     """
#
#     # QUESTION This seems to omit the case where a voice later in the voice
#     #   order was attacked earlier but has a dur that overlaps with the current
#     #   attack time... is that ok?
#     if during_pattern_voice_leading is None:
#         return (
#             er.voice_order[: er.voice_order.index(voice_i)]
#             + er.existing_voices_indices
#         )
#
#     # Get all voices that have already been written whose end times
#     # are later than the attack time.
#
#     attack_time = during_pattern_voice_leading
#
#     voice_lens = {voice_i: 0 for voice_i in er.voice_order}
#
#     active_voice_i = end_time = -1
#
#     order_i = 0
#     while active_voice_i != voice_i or end_time < attack_time:
#         try:
#             vl_item = er.pattern_voice_leading_order[order_i]
#             end_time = vl_item.end_time
#             active_voice_i = vl_item.voice_i
#         except IndexError:
#             break
#         voice_lens[active_voice_i] = end_time
#         order_i += 1
#
#     prev_voice_indices = []
#
#     for other_voice_i, end_time in voice_lens.items():
#         if other_voice_i != voice_i and end_time > attack_time:
#             prev_voice_indices.append(other_voice_i)
#
#     return prev_voice_indices + er.existing_voices_indices


def get_all_pitches_in_range(pcset, boundary_pitches, tet=12):
    """Returns all pitches belonging to given pcset within the bounds
    set by 2-tuple boundary_pitches (inclusive).
    """
    try:
        iter(pcset)
    except TypeError:
        pcset = [
            pcset,
        ]
    pitches = []
    for pitch in range(min(boundary_pitches), max(boundary_pitches) + 1):
        if pitch % tet in pcset:
            pitches.append(pitch)

    return pitches


def get_scale_index(scale, pitch, up_or_down=0, return_adjustment_sign=False):
    """If prev_pitch is in a previous harmony (and not in the present
    harmony), then the generic interval to it is undefined. But we can get an
    appropriate value by taking the nearest pitch to it in the
    previous scale.

    It's possible this will lead to odd behaviour applying parallel
    motion if, e.g., thirds become seconds across the barline, etc.

    Keyword args:
        up_or_down: if 0, randomly alternates between adjusting first
            upwards and only then downwards. If > 0, upwards is first.
            If < 0, downwards is first.
        return_adjustment_sign: if True, returns a tuple of the scale_index,
            and the sign (-1, 0, or 1) of the adjustment necessary (or not
            necessary, in the case of 0). The idea is that this might be
            useful in some cases...
    """

    try:
        return scale.index(pitch)
    except ValueError:
        i = 1
        while True:
            if up_or_down == 0:
                adjust = random.choice((i, -i))
            elif up_or_down > 0:
                adjust = i
            elif up_or_down < 0:
                adjust = -i
            if pitch + adjust in scale:  # pylint: disable=no-else-return
                if return_adjustment_sign:
                    return (scale.index(pitch + adjust), np.sign(adjust))
                return scale.index(pitch + adjust)
            elif pitch - adjust in scale:
                if return_adjustment_sign:
                    return (scale.index(pitch - adjust), np.sign(-adjust))
                return scale.index(pitch - adjust)
            i += 1


def get_generic_interval(er, harmony_i, pitch, prev_pitch):
    scale = er.get(harmony_i, "scales")
    prev_scale_index = get_scale_index(scale, prev_pitch)
    scale_index = scale.index(pitch)

    return scale_index - prev_scale_index


def apply_generic_interval(er, harmony_i, generic_interval, prev_pitch):
    scale = er.get(harmony_i, "scales")
    prev_scale_index = get_scale_index(scale, prev_pitch)
    new_pitch = scale[prev_scale_index + generic_interval]
    return new_pitch


def same_set_class(pcset1, pcset2, tet=12):
    """Doesn't check for inversional equivalence.
    """
    pcset1_min = min(pcset1)
    pcset1 = {pc - pcset1_min for pc in pcset1}
    for adjust_pc in pcset2:
        if pcset1 == {(pc - adjust_pc) % tet for pc in pcset2}:
            return True
    return False


def pair_of_pcs_consonant(
    pc1, pc2, consonances, tet=12, inversional_equivalence=True
):
    """Checks if the pitch-class interval between two pitch-classes
    (or pitches) is consonant.

    Needs to be passed a list of consonances and merely checks
    if the interval is in the list.

    If inversional_equivalence is False, then only the interval from
    pc1 to pc2 is measured (i.e., pc2 - pc1); otherwise pc2 to pc1
    is measured as well.
    """
    # If one of the pcs is None, then consider it consonant.
    if None in [pc1, pc2]:
        return True
    if (pc2 - pc1) % tet in consonances:
        return True
    if inversional_equivalence and (pc1 - pc2) % tet in consonances:
        return True

    return False


def pair_of_pitches_consonant(
    pitch1, pitch2, consonances, tet=12, octave_equivalence=True
):
    """Checks if the interval between two pitches is consonant.

    Needs to be passed a list of consonances and merely checks
    if the interval is in the list.

    If octave equivalence is False, then e.g. 19 (in 12-tet)
    has to be in the list of consonances for a perfect twelth
    to return consonant.
    """
    # If one of the pitches is None, then consider it consonant.
    if None in [pitch1, pitch2]:
        return True
    interval = abs(pitch2 - pitch1)
    if octave_equivalence:
        interval %= tet
    if interval in consonances:
        return True

    return False


def pcs_consonant(pcset, consonances, tet=12, inversional_equivalence=True):
    """Checks if the intervals between all pairs of pitch-classes
    (or pitches) is consonant.

    Needs to be passed a list of consonances and merely checks
    if the interval is in the list.

    If inversional_equivalence is False, then only the interval from
    pc1 to pc2 is measured (i.e., pc2 - pc1); otherwise pc2 to pc1
    is measured as well.
    """
    for pc1, pc2 in itertools.combinations(pcset, 2):
        if not pair_of_pcs_consonant(
            pc1,
            pc2,
            consonances,
            tet=tet,
            inversional_equivalence=inversional_equivalence,
        ):
            return False

    return True


def pitches_consonant(
    pitch_set,
    consonances,
    tet=12,
    octave_equivalence=True,
    augmented_triad=False,
):
    """Checks if the intervals between all pairs of pitches is consonant.

    Needs to be passed a list of consonances and merely checks
    if the interval is in the list.

    If octave equivalence is False, then e.g. 19 (in 12-tet)
    has to be in the list of consonances for a perfect twelth
    to return consonant.
    """
    if augmented_triad:
        if same_set_class(augmented_triad, pitch_set, tet=tet):
            return False
    for pitch1, pitch2 in itertools.combinations(pitch_set, 2):
        if not pair_of_pitches_consonant(
            pitch1,
            pitch2,
            consonances,
            tet=tet,
            octave_equivalence=octave_equivalence,
        ):
            return False
    return True


def lowest_occurrence_of_pc_in_set(pitch, pitch_set, tet=12):
    """Check if a pitch is the lowest occurence of its pitch-class
    in given pitch-set.

    Returns True for ties.
    """
    same_pitch_classes = [
        other_pitch
        for other_pitch in pitch_set
        if other_pitch % tet == pitch % tet
    ]
    if min(same_pitch_classes) == pitch:
        return True
    return False


def _get_consec_intervals(chord, tet, octave_equi):
    """Used by chord_in_list()
    """
    out = []
    if octave_equi in ("all", "bass"):
        chord = [(pitch - chord[0]) % tet for pitch in chord]
        chord.sort()
    for pitch_i, pitch in enumerate(chord[:-1]):
        interval = chord[pitch_i + 1] - pitch
        if octave_equi in ("all", "bass", "order"):
            interval %= tet
        out.append(interval)
    if octave_equi == "all":
        interval = (chord[0] - chord[-1]) % tet
        out.append(interval)
    return out


def chord_in_list(
    chord,
    list_of_chords,
    tet=12,
    octave_equi="all",
    permit_doublings="complete",
):
    """Returns true if the passed chord is is among the chords
    in the list (under transpositional equivalence, and according to
    the octave equivalence and doubling settings).

    Keyword arguments:
        tet: int.
        octave_equi: str. Possible values:
            "all": Default. All octave equivalence and octave permutations
                are allowed.
            "bass": all octave equivalence and octave permutations are allowed
                except that bass note must be preserved (the bass note being
                assumed to be the first listed pitch/pitch-class of the
                chords in the list)
            "order": octave equivalence is allowed but pitch-classes must be
                in the order listed. (This is order from lowest to highest,
                not by voice. So if the alto is lower than the tenor, the
                alto's pitch-class comes first.)
            "none": no octave equivalence, in thse sense that (C3, E4, G4) is
                not considered the same as (C4, E4, G4) because of the tenth/
                third. Nevertheless, transpositional equivalence still applies,
                including when the interval of transposition is an octave,
                so (C3, E3, G3) will match (C4, E4, G4).
        permit_doublings: str. Possible values:
            "all": permit any and all doublings.
            "complete": doublings only permitted after the chord is complete.
            "none": no doublings permitted.
    """

    chord = list(chord)
    chord.sort()
    list_of_chords_ = []
    for lchord in list_of_chords:
        lchord_ = [pitch - lchord[0] for pitch in lchord]
        lchord_.sort()
        list_of_chords_.append(lchord_)
    if permit_doublings in ("all", "complete"):
        orig_card = len(chord)
        chord = np.array(chord)
        unique_is = np.unique(chord % 12, return_index=True)[1]
        unique_is.sort()
        chord = chord[unique_is].tolist()
    chord_card = len(chord)
    consec_intervals = _get_consec_intervals(chord, tet, octave_equi)
    for listed_chord in list_of_chords_:
        if chord_card > len(listed_chord):
            continue
        if (
            permit_doublings == "complete"
            and chord_card < len(listed_chord)
            and chord_card < orig_card
        ):
            continue
        listed_consec_intervals = _get_consec_intervals(
            listed_chord, tet, octave_equi
        )[: chord_card - 1]
        if octave_equi == "all":
            mod_consec_intervals = consec_intervals + consec_intervals
            for i in range(chord_card):
                consec_slice = mod_consec_intervals[i : i + chord_card - 1]
                if consec_slice == listed_consec_intervals:
                    return True
        else:
            if consec_intervals == listed_consec_intervals:
                return True

    return False


def remove_interval_class(interval_class, given_pitch, other_pitches, tet=12):
    """Returns pitches that don't form given interval class from given pitch.
    """
    out = []
    for other_pitch in other_pitches:
        if (given_pitch - other_pitch) % tet != interval_class % tet and (
            other_pitch - given_pitch
        ) % tet != interval_class % tet:
            out.append(other_pitch)
    return out


def remove_octave_equivalent_interval(
    interval, given_pitch, other_pitches, tet=12
):
    """Returns pitches that don't form given interval from given pitch.

    "Octave equivalent" means that 19 = 7 (in 12-tet), etc.
    """
    out = []
    for other_pitch in other_pitches:
        higher_pitch = max(other_pitch, given_pitch)
        lower_pitch = min(other_pitch, given_pitch)
        if (higher_pitch - lower_pitch) % tet != interval % tet:
            out.append(other_pitch)
    return out


def remove_interval(interval, given_pitch, other_pitches):
    """Returns pitches that don't form given interval from given pitch.

    Interval is *not* octave equivalent, meaning that 19 != 7 (in 12-tet), etc.

    For octave-equivalent intervals, use remove_octave_equivalent_interval()
    """
    out = []
    for other_pitch in other_pitches:
        higher_pitch = max(other_pitch, given_pitch)
        lower_pitch = min(other_pitch, given_pitch)
        if (higher_pitch - lower_pitch) != interval:
            out.append(other_pitch)
    return out


def check_interval_class(interval_class, given_pitch, other_pitches, tet=12):
    """Returns true if given pitch forms given interval_class
    from other pitches.
    """
    for other_pitch in other_pitches:
        if (given_pitch - other_pitch) % tet == interval_class % tet or (
            other_pitch - given_pitch
        ) % tet == interval_class % tet:
            return True
    return False


def generic_transpose(
    er,
    score,
    interval,
    max_interval,
    start_time,
    end_time,
    apply_to_existing_voices=False,
):
    """Transposes a passage diatonically.
    """
    # (specific) "transpose" is a method of the Score class. Perhaps
    #   this should be as well but because it requires the ERSettings
    #   object as well I've made it an independent function...
    def _update_harmony(time):
        harmony_i = score.get_harmony_i(time)
        harmony_end_time = score.get_harmony_times(harmony_i)[1]
        scale = er.get(harmony_i, "scales")
        adjusted_interval = interval
        while adjusted_interval > max_interval:
            adjusted_interval -= len(er.get(harmony_i, "pc_scales"))
        while adjusted_interval < min_interval:
            adjusted_interval += len(er.get(harmony_i, "pc_scales"))
        return harmony_i, harmony_end_time, scale, adjusted_interval

    def _apply_generic_transpose(voice):
        (
            # I don't know why pylint thinks harmony_i is unused
            harmony_i,  # pylint: disable=unused-variable
            harmony_end_time,
            scale,
            adjusted_interval,
        ) = _update_harmony(start_time)
        for note in voice:
            if note.attack_time < start_time:
                continue
            if note.attack_time >= harmony_end_time:
                (
                    harmony_i,
                    harmony_end_time,
                    scale,
                    adjusted_interval,
                ) = _update_harmony(note.attack_time)
            orig_sd = scale.index(note.pitch)
            new_pitch = scale[orig_sd + adjusted_interval]
            note.pitch = new_pitch
            if note.attack_time > end_time:
                break

    min_interval = -max_interval

    for voice in score.voices:
        _apply_generic_transpose(voice)

    if apply_to_existing_voices:
        for voice in score.existing_voices:
            _apply_generic_transpose(voice)


def nested_method(method):
    """Decorator to extend method arbitrarily deep/nested list-likes.

    Same as `nested` decorator, but passes "self" as first argument.

    If iter() succeeds on the first argument to func, returns a list
    (with nested lists replicating the structure of the argument). Otherwise
    returns a single item of the return type of func.
    """

    def f(self, item, *args, **kwargs):
        if isinstance(item, typing.Sequence) and not isinstance(item, str):
            out = []
            for sub_item in item:
                out.append(f(self, sub_item, *args, **kwargs))
            return out
        return method(self, item, *args, **kwargs)

    return f
