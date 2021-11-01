import copy
import os
import sys

import efficient_rhythms.er_classes as er_classes


def test_dumb_sorted_list():
    dsl1 = er_classes.DumbSortedList((4, 2, 6, 1))
    dsl2 = dsl1.copy()
    assert dsl1 == dsl2
    dsl3 = copy.copy(dsl1)
    assert dsl1 == dsl2 == dsl3
    dsl4 = copy.deepcopy(dsl1)
    assert dsl1 == dsl2 == dsl3 == dsl4


def test_get_index():
    notes = (
        (60, 0, 0.5),
        (61, 0.5, 0.25),
        (62, 1.5, 0.5),
        (63, 1.5, 0.5),
    )
    note_objs = [
        er_classes.Note(pitch, onset, dur) for pitch, onset, dur in notes
    ]
    voice = er_classes.Voice()
    assert (
        voice.get_i_at_or_before(0) == -1
    ), "voice.get_index_at_or_before(0) != -1"
    # TODO implement or delete this test
    # assert (
    #     voice.get_index_before(0) == -1
    # ), "voice.get_index_before(0) != -1"
    for note_obj in note_objs:
        voice.add_note(note_obj)
    assert (
        voice.get_i_at_or_before(0) == 0
    ), "voice.get_index_at_or_before(0) != 0"
    assert (
        voice.get_i_at_or_before(0.25) == 0
    ), "voice.get_index_at_or_before(0.25) != 0"
    assert (
        voice.get_i_at_or_before(-0.1) == -1
    ), "voice.get_index_at_or_before(-0.1) != -1"
    assert (
        voice.get_i_at_or_before(100) == 2
    ), "voice.get_index_at_or_before(100) != 2"
    assert voice.get_i_before(0) == -1, "voice.get_index_before(0) != -1"
    assert voice.get_i_before(0.25) == 0, "voice.get_index_before(0.25) != 0"
    assert voice.get_i_before(-0.1) == -1, "voice.get_index_before(-0.1) != -1"
    assert voice.get_i_before(100) == 2, "voice.get_index_before(100) != 2"
    assert voice.get_i_at_or_after(100) == 3
    assert voice.get_i_at_or_after(1.5) == 2
    assert voice.get_i_at_or_after(0) == 0
    assert voice.get_i_at_or_after(-1) == 0
    assert voice.get_i_at_or_after(0.1) == 1


def test_voice():
    notes = (
        (60, 0, 0.5),
        (61, 0.5, 0.25),
        (62, 1.5, 0.5),
        (63, 1.5, 0.5),
    )
    note_objs = [
        er_classes.Note(pitch, onset, dur) for pitch, onset, dur in notes
    ]
    voice = er_classes.Voice()
    for note_obj in note_objs:
        voice.add_note(note_obj)
    more_notes = [n for n in voice.between()]
    assert note_objs == more_notes
    more_notes = [n for n in voice.between(start_time=0.5)]
    assert note_objs[1:] == more_notes
    more_notes = [n for n in voice.between(start_time=0.25)]
    assert note_objs[1:] == more_notes
    more_notes = [n for n in voice.between(end_time=1.5)]
    assert note_objs[:2] == more_notes
    more_notes = [n for n in voice.between(end_time=1.25)]
    assert note_objs[:2] == more_notes
    more_notes = [n for n in voice.between(start_time=0.5, end_time=1.5)]
    assert note_objs[1:2] == more_notes
    more_notes = [n for n in voice.between(start_time=1.0, end_time=1.25)]
    assert more_notes == []
    prev = voice.get_prev_n_notes(3, 0)
    assert prev == [None, None, None], "prev != [None, None, None]"
    prev = voice.get_prev_n_notes(3, 0, include_start_time=True)
    assert prev == [
        None,
        None,
        note_objs[0],
    ], "prev != [note_objs[0], None, None]"
    prev = voice.get_prev_n_notes(3, 1.5)
    assert prev == [
        None,
        note_objs[0],
        note_objs[1],
    ], "prev != [None, note_objs[0], note_objs[1]]"
    prev = voice.get_prev_n_notes(1, 2)
    assert prev == [note_objs[3]]
    prev = voice.get_prev_n_notes(3, 1.5, stop_at_rest=True)
    assert prev == [None, None, None], "prev != [None, None, None]"
    prev = voice.get_prev_n_notes(3, 1.5, include_start_time=True)
    assert prev == [
        note_objs[1],
        note_objs[2],
        note_objs[3],
    ], "prev != [note_objs[1], note_objs[2], note_objs[3]]"
    prev = voice.get_prev_n_notes(
        3, 1.5, include_start_time=True, stop_at_rest=True
    )
    assert prev == [
        None,
        note_objs[2],
        note_objs[3],
    ], "prev != [None, note_objs[2], note_objs[3]]"
    prev = voice.get_prev_n_notes(3, 1.5, include_start_time=True, min_onset=1)
    assert prev == [
        None,
        note_objs[2],
        note_objs[3],
    ], "prev != [None, note_objs[2], note_objs[3]]"
    last = voice.get_last_n_pitches(2, 1.5)
    assert last == [62, 63]
    last = voice.get_last_n_pitches(1, 1.5)
    assert last == [63]
    s = voice.get_sounding_pitches(1.5)
    assert s == [62, 63], "s != [62, 63]"
    s = voice.get_sounding_pitches(2.0)
    assert s == [], "s != []"
    s = voice.get_sounding_pitches(0, end_time=2, min_dur=0.5)
    assert s == [60, 62, 63], "s != [60, 62, 63]"
    s = voice.get_sounding_pitches(
        0.3, end_time=2.3, min_onset=0.2, min_dur=0.5
    )
    assert s == [62, 63], "s != [62, 63]"
    p = voice.get_passage(1, 2)
    for note_i, note in enumerate(p):
        assert note != note_objs[note_i], "note == note_objs[note_i]"
        assert note == note_objs[note_i + 2], "note != note_objs[note_i + 2]"
        assert (
            note is not note_objs[note_i + 2]
        ), "note is note_objs[note_i + 2]"
    p = voice.get_passage(1, 2, make_copy=False)
    for note_i, note in enumerate(p):
        assert (
            note is note_objs[note_i + 2]
        ), "note is not note_objs[note_i + 2]"
    voice.transpose(2, start_time=0, end_time=1)
    assert note_objs[0].pitch == 62, "note_objs[0].pitch != 62"
    assert note_objs[1].pitch == 63, "note_objs[1].pitch != 63"
    assert note_objs[2].pitch == 62, "note_objs[2].pitch != 62"
    assert note_objs[3].pitch == 63, "note_objs[3].pitch != 63"
    voice.transpose(-4)
    assert note_objs[0].pitch == 58, "note_objs[0].pitch != 58"
    assert note_objs[1].pitch == 59, "note_objs[1].pitch != 59"
    assert note_objs[2].pitch == 58, "note_objs[2].pitch != 58"
    assert note_objs[3].pitch == 59, "note_objs[3].pitch != 59"
    voice.repeat_passage(0.5, 2.0, 3.0)
    p1 = voice.get_passage(0.5, 2.0)
    p2 = voice.get_passage(3.0, 4.5)
    for n1, n2 in zip(p1, p2):
        assert n1.partial_equality(
            n2, onset=False
        ), "n1.partial_equality(n2, onset=False)"
    assert len(voice[4.0]) == 2, "len(voice[4.0]) != 2"
    voice.displace_passage(-1, 2.0)
    assert len(voice[3.0]) == 2, "len(voice[3.0]) != 2"
    p1 = voice.get_passage(0.5, 2.0)
    p2 = voice.get_passage(2.0, 10.0)
    for n1, n2 in zip(p1, p2):
        assert n1.partial_equality(
            n2, onset=False
        ), "n1.partial_equality(n2, onset=False)"
    voice.displace_passage(-0.5)
    for note in voice:
        assert note is note_objs[1], "note is not note_objs[1]"
        break
    voice.displace_passage(-10)
    for note in voice:
        raise AssertionError("Voice should empty!")
    note_objs = [
        er_classes.Note(pitch, onset, dur) for pitch, onset, dur in notes
    ]
    for note_obj in note_objs:
        voice.add_note(note_obj)
    voice.remove_passage(start_time=1.0)
    assert len(voice._data) == 2  # pylint: disable=protected-access
    voice.add_note(note_objs[2])
    voice.add_note(note_objs[3])
    voice.remove_passage(end_time=1.0)
    assert len(voice[1.5]) == 2, "len(voice[1.5]) != 2"
    voice.remove_passage()
    assert voice.is_empty
    for note_obj in note_objs:
        voice.add_note(note_obj)
    voice.displace_passage(1)
    voice.fill_with_rests(10)
    assert voice[0][0].pitch is None, "voice[0][0].pitch is not None"
    assert voice[1.75][0].pitch is None, "voice[1.75][0].pitch is not None"
    assert voice[3.0][0].pitch is None, "voice[3.0][0].pitch is not None"


if __name__ == "__main__":
    test_dumb_sorted_list()
    test_get_index()
    test_voice()
