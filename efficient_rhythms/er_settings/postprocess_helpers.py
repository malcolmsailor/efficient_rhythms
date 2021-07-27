import math
import os

from .. import er_constants
from .. import er_misc_funcs
from .. import er_tuning

from .. import PACKAGE_DIR


def generate_interval_cycle(er, field_name):
    assert field_name == "foot_pcs"
    if not er.interval_cycle or er.scales_and_chords_specified_in_midi:
        return er.foot_pcs
    foot_pcs = [er.foot_pcs[0]]
    for interval_i in range(er.num_harmonies):
        interval = er.get(interval_i, "interval_cycle")
        foot_pcs.append(foot_pcs[-1] + interval)
    return foot_pcs


def get_augmented_triad(er, field_name):
    assert field_name == "exclude_augmented_triad"
    if not er.exclude_augmented_triad:
        return er.exclude_augmented_triad
    augmented_triad = tuple(er_constants.AUGMENTED_TRIAD)
    return er_tuning.temper_pitch_materials(augmented_triad, er.tet)


def process_voice_relations(er, field_name):
    assert field_name in (
        "rhythmic_unison",
        "rhythmic_quasi_unison",
        "hocketing",
    )
    val = getattr(er, field_name)
    if isinstance(val, bool):
        if val:
            return (tuple(range(er.num_voices)),)
        return ()
    val = list(val)
    val = er_misc_funcs.remove_non_existing_voices(val, er.num_voices)
    accounted_for_voices = [False for _ in range(er.num_voices)]
    for voice_group in val:
        for voice_i in voice_group:
            accounted_for_voices[voice_i] = True
    for voice_i, bool_ in enumerate(accounted_for_voices):
        if not bool_:
            val.append((voice_i,))
    return tuple(val)


def get_output_path(er, field_name):
    output_path = getattr(er, field_name)
    # TODO find a better solution for saving files than parent directory
    if output_path.startswith("EFFRHY/"):
        output_path = os.path.join(
            PACKAGE_DIR, output_path.replace("EFFRHY/", "", 1)
        )
    dir_name = os.path.dirname(output_path)
    if dir_name and not os.path.exists(dir_name):
        os.makedirs(dir_name)
    if dir_name == output_path.rstrip(os.path.sep):
        if er._user_settings is None:
            output_path = os.path.join(output_path, "effrhy.mid")
        else:
            output_path = os.path.join(
                output_path,
                os.path.splitext(os.path.basename(er._user_settings[-1]))[0]
                + ".mid",
            )
    if os.path.exists(output_path):
        output_path = er_misc_funcs.increment_fname(output_path)
    return output_path


def check_force_parallel_motion(er, field_name):
    force_parallel_motion = getattr(er, field_name)
    if isinstance(force_parallel_motion, bool):
        force_parallel_motion = {
            tuple(er.voice_order): (
                "within_harmonies" if force_parallel_motion else "false"
            )
        }
    return force_parallel_motion


def check_min_dur(er, field_name):
    min_dur = getattr(er, field_name)
    for voice_i, rhythm_len in enumerate(er.rhythm_len):
        if rhythm_len < min_dur[voice_i] * er.num_notes[voice_i]:
            new_min_dur = er_misc_funcs.convert_to_fractions(
                rhythm_len / er.num_notes[voice_i]
            )
            print(
                f"Notice: min_dur too long in voice {voice_i} rhythm; "
                f"reducing from {min_dur[voice_i]} to {new_min_dur}."
            )
            min_dur[voice_i] = new_min_dur
    return min_dur


def check_num_vars(er, field_name):
    num_cont_rhythm_vars = list(getattr(er, field_name))
    for voice_i in range(er.num_voices):
        pattern_len = er.pattern_len[voice_i]
        if num_cont_rhythm_vars[voice_i] < 0:
            num_cont_rhythm_vars[voice_i] = math.ceil(
                er.total_len / pattern_len
            )
    return tuple(num_cont_rhythm_vars)


def check_invert_consonances(er, field_name):
    consonances = getattr(er, field_name)
    if er.invert_consonances:
        consonances = tuple(i for i in range(er.tet) if i not in consonances)
    return consonances


def check_rhythm_len(er, field_name):
    rhythm_len = getattr(er, field_name)
    for j, pattern_length in enumerate(er.pattern_len):
        if rhythm_len[j] > pattern_length or rhythm_len[j] == 0:
            rhythm_len[j] = pattern_length
    return rhythm_len


def scale_by_neutral_dur(er, field_name):
    val = getattr(er, field_name)
    return val / er.scale_chord_tone_neutral_dur


def truncate_to_num_harmonies(er, field_name):
    val = getattr(er, field_name)
    return val[: er.num_harmonies]


def set_to_num_harmonies(er, field_name):
    val = getattr(er, field_name)
    if er.num_harmonies < len(val):
        return val[: er.num_harmonies]
    else:
        while er.num_harmonies > len(val):
            val.extend(val[: er.num_harmonies - len(val)])
        return val
