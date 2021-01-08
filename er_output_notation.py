"""Outputs the file to kern and to pdf. Can also be used from command line.

Unlike the rest of this package I didn't rewrite this recently, except for
the bare minimum to make it work with the current version of
efficient_rhythms2.py.

Requires quite a few dependencies that are run from the shell:
    - verovio
    - convert (from ImageMagick)
    - img2pdf (obtainable from pypi)
    - hum2xml (part of Craig Sapp's humextra)
"""
# INTERNET: add websites for dependencies
import os
import subprocess
from fractions import Fraction

import er_tuning


class PitchDict:
    """For converting pitch-numbers in a given equal temperament to kern
    letters.
    """

    def __init__(self, tet):
        self.tet = tet
        self.pc_dict = er_tuning.build_spelling_dict(tet, letter_format="kern")

    def to_kern(self, pitch_num):
        letter = self.pc_dict[pitch_num % self.tet]
        if letter[0] == "c" and letter[-1] == "-":
            pitch_num += self.tet
        temp_num = (pitch_num % self.tet) + (self.tet * 5)

        if temp_num > pitch_num:
            letter = letter[0].upper() + letter[1:]
            temp_num -= self.tet
        while temp_num > pitch_num:
            letter = letter[0] + letter
            temp_num -= self.tet
        while temp_num < pitch_num:
            letter = letter[0] + letter
            temp_num += self.tet

        return letter


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

    if offset != 0 and adjusted_input + offset > unbreakable_value:
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


def write_kern(super_pattern, fname):
    """Writes a Score object to a kern file."""

    unbreakable_value = Fraction(1, 1)

    num_voices = len(super_pattern.voices)
    voices = super_pattern.voices

    voice_ps = [[] for voice_i in range(num_voices)]
    ties = [{} for voice_i in range(num_voices)]
    attacks = []

    numer, denom = super_pattern.time_sig
    time_sig_dur = numer * 4 / denom

    for voice_i, voice in enumerate(voices):
        for note in voice:
            attack = note.attack_time
            attacks.append(attack)

            # add supplementary attacks for tied notes where necessary
            # print(note.dur)
            durs = dur_to_kern(
                note.dur,
                offset=attack,
                unbreakable_value=unbreakable_value,
                time_sig_dur=time_sig_dur,
            )
            # print(durs)
            if len(durs) > 1:
                ties[voice_i][attack] = (durs[0][1], note.pitch, "start")
                for i in range(1, len(durs)):
                    supplementary_attack = sum(
                        [attack,] + [durs[j][0] for j in range(i)]
                    )
                    attacks.append(supplementary_attack)
                    ties[voice_i][supplementary_attack] = (
                        durs[i][1],
                        note.pitch,
                        "end" if i == len(durs) - 1 else "middle",
                    )
            if note.pitch:
                voice_ps[voice_i].append(note.pitch)

    attacks = sorted(list(set(attacks)))

    outkern = open(fname, "w", encoding="utf8")

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
            outkern.write(bit)
            outkern.write(_kern_white_space(voice_i))
    for i, clef in enumerate(clefs):
        outkern.write(clef)
        outkern.write(_kern_white_space(i))

    measure_counter = 0

    pitch_dict = PitchDict(super_pattern.tet)

    for attack in attacks:
        if attack % time_sig_dur == 0:
            # write bar line
            measure_counter += 1
            for voice in range(num_voices):
                outkern.write("=" + str(measure_counter))
                outkern.write(_kern_white_space(voice))
        for voice in range(num_voices):
            if attack in ties[voice]:
                kern_dur, pitch_num, tie_status = ties[voice][attack]
                if pitch_num is not None:
                    kern_letter = pitch_dict.to_kern(pitch_num)
                    # kern_letter = pitch_num_to_kern(
                    #     pitch_num, tet=super_pattern.tet)
                else:
                    kern_letter = "r"
                if tie_status == "end":
                    outkern.write(kern_dur + kern_letter + "]")
                elif tie_status == "start":
                    outkern.write("[" + kern_dur + kern_letter)
                else:
                    outkern.write(kern_dur + kern_letter)
            elif attack in super_pattern.voices[voice]:
                note = super_pattern.voices[voice][attack][0]
                if len(super_pattern.voices[voice][attack]) > 1:
                    raise NotImplementedError(
                        "No support for writing polyphonic voices to kern yet"
                    )
                dur = note.dur
                pitch_num = note.pitch
                if pitch_num is not None:
                    kern_letter = pitch_dict.to_kern(pitch_num)
                    # kern_letter = pitch_num_to_kern(
                    #     pitch_num, tet=super_pattern.tet)
                else:
                    kern_letter = "r"
                kern_dur = dur_to_kern(dur)
                if len(kern_dur) != 1:
                    input("Tied note seems to have gotten through!")
                kern_dur = kern_dur[0][1]
                outkern.write(kern_dur + kern_letter)
            else:
                outkern.write(".")
            outkern.write(_kern_white_space(voice))

    afterword_bits = [
        "=" + str(measure_counter),
        "*-",
    ]

    for bit in afterword_bits:
        for voice in range(num_voices):
            outkern.write(bit)
            outkern.write(_kern_white_space(voice))
    outkern.write("!!!filter: autobeam")

    outkern.close()


def write_notation(fname, fname_path):
    """Runs shell commands to convert a kern file to pdf.
    """
    vrv_in = fname
    vrv_out = vrv_in.replace("krn", "svg")
    subprocess.run(
        [
            "verovio",
            vrv_in,
            "-o",
            vrv_out,
            "--no-footer",
            "--no-header",
            "--all-pages",
        ],
        check=False,
    )

    # convert svg to png
    print("Converting svgs to pngs...")
    dir_contents = os.listdir(fname_path)
    png_paths = []
    svg_paths = []
    for file_name in dir_contents:
        if file_name.startswith(
            fname.split("/")[-1].replace(".krn", "")
        ) and file_name.endswith("svg"):
            svg_paths.append(os.path.join(fname_path, file_name))

    for svg_path in svg_paths:
        png_path = svg_path.replace("svg", "png")
        subprocess.run(["convert", svg_path, png_path], check=False)
        png_paths.append(png_path)

    # convert png to pdf
    print("Converting pngs to pdf...")
    if not os.path.exists(os.path.join(fname_path, "pdfs")):
        os.mkdir(os.path.join(fname_path, "pdfs"))

    pdf_path = fname.replace(".krn", ".pdf").replace("_midi/", "_midi/pdfs/")
    subprocess.run(["img2pdf",] + png_paths + ["-o", pdf_path], check=False)
    subprocess.run(["open", pdf_path], check=False)

    # clean up temp files
    for file_name in png_paths + svg_paths:
        # We could also delete the kern file ("fname"),
        # but for now I'm leaving it for debugging purposes.
        os.remove(file_name)


if __name__ == "__main__":
    print(dur_to_kern(Fraction(1, 3)))
