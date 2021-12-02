import os
import subprocess
import tempfile

from efficient_rhythms import er_output_notation
from efficient_rhythms import er_misc_funcs
from efficient_rhythms import er_classes


def test_get_kern():
    # A case that was failing:
    notes = (
        ((60, 0, 1.75), (61, 1.75, 1.5), (62, 3.25, 0.75), (63, 4, 1)),
        ((48, 0, 1), (49, 1, 1), (50, 2, 1), (51, 3, 1), (52, 4, 1)),
    )
    score = er_classes.Score(
        num_voices=len(notes),
        tet=12,
        time_sig=(2, 4),
        harmony_len=(2,),
        total_len=6,
    )
    for voice_i, voice in enumerate(notes):
        for pitch, onset, dur in voice:
            score.add_note(voice_i, pitch, onset, dur)
    kern = er_output_notation.get_kern(score)
    _, temp_path = tempfile.mkstemp()
    # If the input is incorrect, verovio should fail
    try:
        er_misc_funcs.silently_run_process(
            ["verovio", "-o", temp_path, "-"], stdin=kern
        )
    except subprocess.CalledProcessError:
        os.remove(temp_path)
        raise
    os.remove(temp_path)


def test_dur_to_kern():
    # LONGTERM write more tests
    time_sig_dur = 2
    tests = {
        1.5: {  # duration
            0: (1, 0.5),
            0.25: (0.75, 0.75),
            0.5: (0.5, 1),
            0.75: (0.25, 1, 0.25),
        }
    }
    for dur, offset_dict in tests.items():
        for offset, vals in offset_dict.items():
            rval = er_output_notation.dur_to_kern(
                dur, offset=offset, time_sig_dur=time_sig_dur
            )
            assert (
                tuple(x[0] for x in rval) == vals
            ), "tuple(x[0] for x in rval) != vals"


if __name__ == "__main__":
    test_get_kern()
    test_dur_to_kern()
