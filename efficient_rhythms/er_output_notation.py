"""Outputs the file to kern and to pdf. Can also be used from command line.

Unlike the rest of this package I didn't rewrite this recently, except for
the bare minimum to make it work with the current version of
efficient_rhythms2.py.

Requires quite a few dependencies that are run from the shell:
    - verovio
    - convert (from ImageMagick)
    - img2pdf (obtainable from pypi)
"""
# INTERNET: add websites for dependencies
import copy
import math
import os
import re
import shutil
from fractions import Fraction

# TODO document mspell requirements, make sure mspell is on
#   pypi

import mspell


from . import er_misc_funcs
from . import er_tuning


TEMP_NOTATION_DIR = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "../.temp_notation_dir"
)


# def dur_to_kern2(dur, offset, time_sig_dur, unbreakable_value=1):
#     out = []
#     while dur:
#         fragment = min(dur, (unbreakable_value - (offset % unbreakable_value)))
#         out.append(fragment)
#         dur -= fragment
#         offset = 0
#     return out


def check_rhythms(er):
    # the kern function only works if all rhythms have denominator that is a
    # power of 2, so we want to check that first
    # As a heuristic, we just check if the rhythms are divisible by 128.
    # LONGTERM check other rhythmic features besides onset_subdivision,
    #   sub_subdivisions?
    if any(len(x) > 1 for x in er.sub_subdivisions):
        print(
            "Sorry, exporting to notation is not compatible with non-empty "
            "values of er.sub_subdivisions"
        )
        return False
    if all(n % (1 / 128) == 0 for n in er.onset_subdivision):
        return True
    print("Can't export notation because not all rhythms are divisible by 128")
    return False


def dur_to_kern(
    inp,
    offset=0,
    unbreakable_value=Fraction(1, 1),
    rest=False,
    dotted_rests=False,
    time_sig_dur=4,
):
    """Converts a duration to kern format.

    Works with duple rhythms including ties and dotted notes. Probably
    doesn't work yet with triplets and other non-duple subdivisions.

    Was originally based on Craig Sapp's durationToKernRhythm function in
    Convert.cpp from humextra. I'm unsure what the "timebase" parameter
    of Sapp's function does, so I omitted it.

    Keyword arguments:
        unbreakable value: integer/float. 1 = quarter, 0.5 eighth, etc.
        offset: used to specify the division of the unbreakable value upon
            which the note begins.
        time_sig_dur: must be specified for rests, so that rests won't be
            longer than the measure that (should) contain them.

    Returns:
        a list of tuples of form (numeric:dur in quarter notes, str:kern
        representation)

    """
    # The maximum number of dots a note can receive will be one fewer
    # than max_depth. (So max_depth = 3 means double-dotted notes are
    # allowed, but no greater.)
    max_depth = 3

    if rest and not dotted_rests:
        max_depth = 1

    # We can potentially do this with other subdivisions by replacing
    # "2" with "3", "5", etc.

    input_multiplicands = [1] + [
        Fraction(1 * 2 ** i, (2 * 2 ** i - 1)) for i in range(1, max_depth)
    ]

    allowed_error = 0.002

    def subfunc(inp, depth):
        if depth == max_depth:
            return None

        testinput = inp * input_multiplicands[depth]
        basic = 4 / testinput
        diff = basic - int(basic)
        # In Sapp's code, which does not employ recursion, the next
        # condition is only tested when depth == 0.
        if diff > 1 - allowed_error:
            diff = 1 - diff
            basic += allowed_error

        if diff < allowed_error:
            output = str(int(basic)) + depth * "."
            # for i in range(depth):
            #     output += "."
            return output

        return subfunc(inp, depth + 1)

    note_values = [Fraction(4, 2 ** i) for i in range(10)] + [
        Fraction(2, 3 * 2 ** i) for i in range(10)
    ]
    note_values.sort(reverse=True)

    adjusted_input = inp
    output = []

    offset = offset % time_sig_dur
    first_m = True
    while offset + adjusted_input > time_sig_dur:
        within_measure_input = time_sig_dur - offset
        while True:
            temp_output = subfunc(within_measure_input, 0)
            if temp_output:
                output.append((within_measure_input, temp_output))
                break

            for note_value in note_values:
                if within_measure_input > note_value:
                    within_measure_input = within_measure_input - note_value
                    temp_temp_output = subfunc(note_value, 0)
                    if temp_temp_output:
                        output.append((note_value, temp_temp_output))
                        break
        adjusted_input -= time_sig_dur - offset
        if first_m:
            output.reverse()
            first_m = False
        offset = 0

    offset = offset % unbreakable_value

    # if offset != 0 and adjusted_input + offset > unbreakable_value:
    if adjusted_input + offset > unbreakable_value:
        unbroken_input = unbreakable_value - offset
        sub_output = []
        while True:
            temp_output = subfunc(unbroken_input, 0)
            if temp_output:
                sub_output.append((unbroken_input, temp_output))
                break

            for note_value in note_values:
                if unbroken_input > note_value:
                    unbroken_input = unbroken_input - note_value
                    temp_temp_output = subfunc(note_value, 0)
                    if temp_temp_output:
                        sub_output.append((note_value, temp_temp_output))
                        break
        adjusted_input -= unbreakable_value - offset
        if rest:
            sub_output.reverse()
        output += sub_output

    counter = 0
    while True:
        counter += 1
        temp_output = subfunc(adjusted_input, 0)
        if temp_output:
            output.append((adjusted_input, temp_output))
            break

        break_out = False
        for note_value in note_values:
            if note_value < allowed_error:
                break_out = True
                break
            if adjusted_input > note_value:
                adjusted_input = adjusted_input - note_value
                temp_temp_output = subfunc(note_value, 0)
                if temp_temp_output:
                    output.append((note_value, temp_temp_output))
                    break_out = True
                    break
        if break_out:
            break

    return output


def write_kern(super_pattern, kern_file):
    """Writes a Score object to a kern file."""

    with open(kern_file, "w", encoding="utf8") as outf:
        outf.write(get_kern(super_pattern))


def get_kern(super_pattern):
    unbreakable_value = Fraction(1, 1)

    num_voices = len(super_pattern.voices)
    speller = mspell.GroupSpeller(tet=super_pattern.tet, letter_format="kern")

    voice_ps = [[] for voice_i in range(num_voices)]
    ties = [{} for voice_i in range(num_voices)]
    onsets = []

    numer, denom = super_pattern.time_sig
    time_sig_dur = numer * 4 / denom

    # If there are notes in one more voices that extend past the end
    # of the last harmony, then the other voices will be filled with rests
    # during the relevant duration of the last harmony.
    for harmony_time in super_pattern.harmony_times:
        harmony = super_pattern.get_passage(
            harmony_time.start_time, harmony_time.end_time, make_copy=False
        )
        for voice_i, voice in enumerate(harmony.voices):
            spelled = speller.pitches([note.pitch for note in voice])
            voice_ps[voice_i].extend(
                [note.pitch for note in voice if note.pitch]
            )
            for note, spelling in zip(voice, spelled):
                note.spelling = spelling
                onset = note.onset
                onsets.append(onset)

                # add supplementary onsets for tied notes where necessary
                durs = dur_to_kern(
                    note.dur,
                    offset=onset,
                    unbreakable_value=unbreakable_value,
                    time_sig_dur=time_sig_dur,
                )
                if len(durs) > 1:
                    ties[voice_i][onset] = (durs[0][1], note.spelling, "start")
                    for i in range(1, len(durs)):
                        supplementary_onset = sum(
                            [
                                onset,
                            ]
                            + [durs[j][0] for j in range(i)]
                        )
                        onsets.append(supplementary_onset)
                        ties[voice_i][supplementary_onset] = (
                            durs[i][1],
                            note.spelling,
                            "end" if i == len(durs) - 1 else "middle",
                        )

    onsets = sorted(list(set(onsets)))

    # outkern = open(kern_file, "w", encoding="utf8")
    outkern = []

    # select clefs
    clefs = []
    for voice_i in range(num_voices):
        if (
            sum(voice_ps[voice_i]) / len(voice_ps[voice_i])
            < 5 * super_pattern.tet
        ):
            clefs.append("*clefF4")
        else:
            clefs.append("*clefG2")

    preamble_bits = ["**kern", "*M" + str(numer) + "/" + str(denom)]

    def _kern_white_space(voice):
        if voice == num_voices - 1:
            return "\n"
        return "\t"

    for bit in preamble_bits:
        for voice_i in range(num_voices):
            # outkern.write(bit)
            # outkern.write(_kern_white_space(voice_i))
            outkern.append(bit)
            outkern.append(_kern_white_space(voice_i))
    for i, clef in enumerate(clefs):
        outkern.append(clef)
        outkern.append(_kern_white_space(i))

    measure_counter = 0

    for onset in onsets:
        if onset % time_sig_dur == 0:
            # write bar line
            measure_counter += 1
            for voice in range(num_voices):
                outkern.append("=" + str(measure_counter))
                outkern.append(_kern_white_space(voice))
        for voice in range(num_voices):
            if onset in ties[voice]:
                kern_dur, kern_letter, tie_status = ties[voice][onset]
                if tie_status == "end":
                    outkern.append(kern_dur + kern_letter + "]")
                elif tie_status == "start":
                    outkern.append("[" + kern_dur + kern_letter)
                else:
                    outkern.append(kern_dur + kern_letter)
            elif onset in super_pattern.voices[voice]:
                note = super_pattern.voices[voice][onset][0]
                if len(super_pattern.voices[voice][onset]) > 1:
                    raise NotImplementedError(
                        "No support for writing polyphonic voices to kern yet"
                    )
                dur = note.dur
                kern_letter = note.spelling
                kern_dur = dur_to_kern(dur)
                if len(kern_dur) != 1:
                    input("Tied note seems to have gotten through!")
                kern_dur = kern_dur[0][1]
                outkern.append(kern_dur + kern_letter)
            else:
                outkern.append(".")
            outkern.append(_kern_white_space(voice))

    afterword_bits = [
        "=" + str(measure_counter),
        "*-",
    ]

    for bit in afterword_bits:
        for voice in range(num_voices):
            outkern.append(bit)
            outkern.append(_kern_white_space(voice))
    outkern.append("!!!filter: autobeam")

    # outkern.close()
    return "".join(outkern)


def init_temp_notation_dir():
    try:
        os.mkdir(TEMP_NOTATION_DIR)
    except FileExistsError:
        print(
            f"Warning: temporary notation directory {TEMP_NOTATION_DIR} "
            "already exists---it will be deleted at the conclusion of "
            "the script"
        )


def clean_up_temporary_notation_files():
    try:
        shutil.rmtree(TEMP_NOTATION_DIR)
    except FileNotFoundError:
        pass


def tidy_up(temp_paths, permanent_dirname):
    if isinstance(temp_paths, str):
        temp_paths = (temp_paths,)
    permanent_paths = [
        os.path.join(permanent_dirname, os.path.basename(temp_path))
        for temp_path in temp_paths
    ]
    for temp_path, permanent_path in zip(temp_paths, permanent_paths):
        shutil.move(temp_path, permanent_path)
    if len(temp_paths) == 1:
        print("Output file is: ")
    else:
        print("Output files are: ")
    for path in permanent_paths:
        print(path)
    clean_up_temporary_notation_files()


def write_notation(kern_file, dirname, filetype=".pdf", verovio_arguments=None):
    """Runs shell commands to convert a kern file to pdf."""

    if filetype not in [".svg", ".png", ".pdf"]:
        print(f"filetype {filetype} not recognized!")
        return
    if not shutil.which("verovio"):
        print("'verovio' not found! Make sure it is in your path and re-try.")
        return
    if filetype != ".svg" and not shutil.which("convert"):
        print(
            "'convert' not found! Make sure it is in your path (maybe you need "
            "to install ImageMagick) and re-try."
        )
        return
    if filetype == ".pdf" and not shutil.which("img2pdf"):
        print("'img2pdf' not found! Make sure it is in your path and re-try.")
        return
    if verovio_arguments is not None:
        verovio_arguments = verovio_arguments.split()
    else:
        verovio_arguments = ["--all-pages"]

    vrv_out = os.path.splitext(kern_file)[0] + ".svg"
    print("Writing svgs...")

    verovio_proc = er_misc_funcs.silently_run_process(
        [
            "verovio",
            kern_file,
            "-o",
            vrv_out,
            "--no-footer",
            "--no-header",
        ]
        + verovio_arguments
    )

    svg_paths = re.findall(
        r"Output written to (.*\.svg)",
        verovio_proc.stdout.decode(),
        re.MULTILINE,
    )

    if filetype == ".svg":
        tidy_up(svg_paths, dirname)
        return

    # convert svg to png
    print("Converting svgs to pngs...")
    png_paths = []
    for svg_path in svg_paths:
        png_path = os.path.splitext(svg_path)[0] + ".png"
        er_misc_funcs.silently_run_process(["convert", svg_path, png_path])
        png_paths.append(png_path)
    if filetype == ".png":
        tidy_up(png_paths, dirname)
        return

    # convert png to pdf
    pdf_path = os.path.splitext(kern_file)[0] + ".pdf"
    print("Converting pngs to pdf...")
    er_misc_funcs.silently_run_process(
        [
            "img2pdf",
        ]
        + png_paths
        + ["-o", pdf_path]
    )

    tidy_up(pdf_path, dirname)


def run_verovio(super_pattern, midi_path, verovio_arguments, file_type):
    fifth = er_tuning.approximate_just_interval(3 / 2, super_pattern.tet)
    gcd = math.gcd(super_pattern.tet, fifth)
    if gcd != 1:
        print(
            er_misc_funcs.add_line_breaks(
                "Sorry, output to notation is only implemented when the "
                "greatest common denominator of `tet` and the equal-tempered "
                "approximation to a just fifth in that temperament is 1. "
                f"Currently, `tet` = {super_pattern.tet} and the fifth is "
                f"{fifth}, so their GCD is {gcd}.",
                indent_type="none",
            )
        )
        return False

    copied_pattern = copy.deepcopy(super_pattern)
    copied_pattern.fill_with_rests(super_pattern.total_dur)

    kern_basename = os.path.basename(os.path.splitext(midi_path)[0] + ".krn")
    kern_path = os.path.join(TEMP_NOTATION_DIR, kern_basename)
    dirname = os.path.dirname(midi_path)

    init_temp_notation_dir()

    write_kern(copied_pattern, kern_path)
    write_notation(
        kern_path,
        dirname,
        filetype=file_type,
        verovio_arguments=verovio_arguments,
    )
    return True
