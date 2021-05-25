import os
import sys
import traceback

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
)

import src.er_classes as er_classes  # pylint: disable=wrong-import-position


def test_comparisons():
    # pitch, finetune, onset, dur, velocity
    note_attrs = (
        (60, 0, 10.0, 2.0, 64),
        # greater than
        (60, 0, 11.0, 2.0, 64),
        (60, 0, 10.0, 2.5, 64),
        (60, 0, 11.0, 1.5, 64),
        (61, 0, 10.0, 2.0, 64),
        (60, 4, 10.0, 2.0, 64),
        (60, 0, 10.0, 2.0, 67),
        # less than
        (60, 0, 9.0, 2.0, 64),
        (60, 0, 10.0, 1.5, 64),
        (60, 0, 9.0, 2.5, 64),
        (59, 0, 10.0, 2.0, 64),
        (60, -14, 10.0, 2.0, 64),
        (60, 0, 10.0, 2.0, 60),
    )
    notes = tuple(
        er_classes.Note(pitch, onset, dur, velocity=velocity, finetune=finetune)
        for (pitch, finetune, onset, dur, velocity) in note_attrs
    )
    main_note = notes[0]
    greater = notes[1:7]
    less = notes[7:]
    equal = [
        er_classes.Note(60, 10, 2, velocity=64, finetune=0, choir=17),
        er_classes.Note(60, 10, 2, velocity=64, finetune=0, voice=11),
    ]
    try:
        for note in greater:
            assert note > main_note, "note <= main_note"
            assert note >= main_note, "note < main_note"
            assert main_note < note, "main_note >= note"
            assert main_note <= note, "main_note > note"
            assert note != main_note, "note == main_note"
            assert not main_note > note
            assert not main_note >= note
            assert not note < main_note
            assert not note <= main_note
            assert not main_note == note
        for note in less:
            assert note < main_note, "note >= main_note"
            assert note <= main_note, "note > main_note"
            assert main_note > note, "main_note <= note"
            assert main_note >= note, "main_note < note"
            assert note != main_note, "note == main_note"
            assert not main_note < note
            assert not main_note <= note
            assert not note > main_note
            assert not note >= main_note
            assert not main_note == note
        for note in equal:
            assert note <= main_note, "note > main_note"
            assert main_note >= note, "main_note < note"
            assert note == main_note, "note != main_note"
            assert not main_note < note
            assert not note > main_note
            assert not main_note != note
    except:  # pylint: disable=bare-except
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(
            exc_type, exc_value, exc_traceback, file=sys.stdout
        )
        breakpoint()


if __name__ == "__main__":
    test_comparisons()
