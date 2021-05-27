import os
import sys
import traceback

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
)

import efficient_rhythms.er_classes as er_classes  # pylint: disable=wrong-import-position
import efficient_rhythms.er_preprocess as er_preprocess  # pylint: disable=wrong-import-position


def test_get_prev_and_last_notes():
    settingsdict = {"num_voices": 2, "tet": 12}
    er = er_preprocess.preprocess_settings(settingsdict)
    # voice, pitch, onset, dur, evaluates_to
    notes = [
        (0, 57, 0, 0.75, None),
        (1, 58, 0.25, 0.25, None),
        (1, 59, 0.5, 0.75, 58),
        (0, 60, 0.75, 0.75, 57),
        (0, 61, 3.0, 1.0, 60),
    ]
    score = er_classes.Score(num_voices=er.num_voices, tet=er.tet)
    try:
        for (v, p, a, d, ev) in notes:  ##pylint: disable=invalid-name
            if ev is None:
                assert (
                    score.voices[v].get_prev_note(a) is None
                ), "score.voices[v].get_prev_note(a) is not None"
                assert (
                    score.voices[v].get_prev_pitch(a) == -1
                ), "score.voices[v].get_prev_pitch(a) != -1"
            else:
                assert (
                    score.voices[v].get_prev_note(a).pitch == ev
                ), "score.voices[v].get_prev_note(a).pitch != ev"
                assert (
                    score.voices[v].get_prev_pitch(a) == ev
                ), "score.voices[v].get_prev_pitch(a) != ev"
            score.add_note(v, p, a, d)
            assert (
                score.voices[v].get_prev_note(a + 1).pitch == p
            ), "score.voices[v].get_prev_note(a + 1).pitch != p"
            if ev is None:
                try:
                    assert (
                        score.voices[v].get_prev_note(a - 0.1) is None
                    ), "score.voices[v].get_prev_note(a - .1) is not None"
                    assert (
                        score.voices[v].get_prev_pitch(a - 0.1) == -1
                    ), "score.voices[v].get_prev_pitch(a - .1) != -1"
                except:  # pylint: disable=bare-except
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    traceback.print_exception(
                        exc_type, exc_value, exc_traceback, file=sys.stdout
                    )
                    breakpoint()

            else:
                assert (
                    score.voices[v].get_prev_note(a - 0.1).pitch == ev
                ), "score.voices[v].get_prev_note(a - .1).pitch != ev"
                assert (
                    score.voices[v].get_prev_pitch(a - 0.1) == ev
                ), "score.voices[v].get_prev_pitch(a - .1) != ev"
            assert (
                score.voices[v].get_last_n_notes(1, a)[0].pitch == p
            ), "score.voices[v].get_last_n_notes(1, a)[0].pitch != p"
            assert (
                score.voices[v].get_last_n_pitches(1, a)[0] == p
            ), "score.voices[v].get_last_n_pitches(1, a)[0] != p"
    except:  # pylint: disable=bare-except

        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(
            exc_type, exc_value, exc_traceback, file=sys.stdout
        )
        breakpoint()


def test_get_sounding_pitches():
    settingsdict = {"num_voices": 2, "tet": 12}
    er = er_preprocess.preprocess_settings(settingsdict)
    score = er_classes.Score(num_voices=er.num_voices, tet=er.tet)
    # voice, pitch, onset, dur
    notes = [
        (0, 57, 0, 0.75),
        (1, 58, 0.25, 0.25),
        (1, 59, 0.5, 0.75),
        (0, 60, 0.75, 0.75),
    ]
    for (v, p, a, d) in notes:  # pylint: disable=invalid-name
        score.add_note(v, p, a, d)
    # onset, dur, min_onset, min_dur, sounding_pitches
    test_items = [
        (0.5, 0, 0, 0, [57, 59]),
        (0.5, 1, 0, 0, [57, 59, 60]),
        (0.5, 1, 0, 1, []),
        (0.5, 1, 0.5, 0, [59, 60]),
    ]
    for (a, d, m1, m2, sp) in test_items:  # pylint: disable=invalid-name
        try:
            assert (
                score.get_sounding_pitches(
                    a, end_time=a + d, min_onset=m1, min_dur=m2
                )
                == sp
            ), f"score.get_sounding_pitches({a}, dur={d}, min_onset={m1}, min_dur={m2}) != {sp}"
        except:  # pylint: disable=bare-except
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(
                exc_type, exc_value, exc_traceback, file=sys.stdout
            )
            breakpoint()


def test_get_harmony_i():
    settingsdict = {"harmony_len": 4, "tet": 12}
    er = er_preprocess.preprocess_settings(settingsdict)
    score = er_classes.Score(
        num_voices=er.num_voices,
        tet=er.tet,
        harmony_len=er.harmony_len,
        total_len=16,
    )
    try:
        assert score.get_harmony_i(0) == 0
        assert score.get_harmony_i(3.75) == 0
        assert score.get_harmony_i(4.0) == 1
        assert score.get_harmony_i(4.01) == 1
        assert score.get_harmony_i(16) == 3
        assert score.get_harmony_i(27) == 3
        ht = score.get_harmony_times(0)
        assert (ht.start_time, ht.end_time, ht.i) == (0, 4, 0)
        ht = score.get_harmony_times(3)
        # end time of final harmony should be None
        assert (ht.start_time, ht.end_time, ht.i) == (12, None, 3)
    except:  # pylint: disable=bare-except

        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(
            exc_type, exc_value, exc_traceback, file=sys.stdout
        )
        breakpoint()


def test_score_misc_attrs():
    settingsdict = {"num_voices": 2, "tet": 12}
    er = er_preprocess.preprocess_settings(settingsdict)
    score = er_classes.Score(num_voices=er.num_voices, tet=er.tet)
    # voice, pitch, onset, dur
    notes = [
        (0, 57, 0, 0.75),
        (1, 58, 0.25, 0.25),
        (1, 59, 0.5, 0.75),
        (0, 60, 0.75, 0.75),
    ]
    try:
        assert score.total_dur == 0
        for (v, p, a, d) in notes:  # pylint: disable=invalid-name
            score.add_note(v, p, a, d)
        assert score.total_dur == 1.5
        for note in score.voices[0][0.75]:
            score.voices[0].remove_note(note)
        assert score.total_dur == 1.25
        score.add_note(1, 42, 250, 17)
        assert score.total_dur == 267
    except:  # pylint: disable=bare-except

        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(
            exc_type, exc_value, exc_traceback, file=sys.stdout
        )
        breakpoint()


def test_generic_transpose():
    settingsdict = {
        "num_voices": 1,
        "tet": 12,
        "harmony_len": 2,
        "foot_pcs": [0],
        "interval_cycle": 3,
        "num_harmonies": 4,
    }
    er = er_preprocess.preprocess_settings(settingsdict)
    score = er_classes.Score(
        num_voices=er.num_voices,
        tet=er.tet,
        harmony_len=er.harmony_len,
        total_len=16,
    )
    notes = [
        er_classes.Note(p + 60, i * 1, 1)
        for i, p in enumerate([0, 2, 3, 5, 6, 8, 9, 11])
    ]
    for note in notes:  # pylint: disable=invalid-name
        score.add_note(0, note)
    try:
        # TODO review the rationale behind max_interval
        #   should it have a default value?
        #   what is its source in the script?
        score.transpose(2, er=er, max_interval=7)
        for i, p in enumerate([4, 5, 7, 8, 10, 11, 13, 14]):
            assert notes[i].pitch == 60 + p, "notes[i].pitch != 60 + p"
        score.transpose(-2, er=er, max_interval=7)
        for i, p in enumerate([0, 2, 3, 5, 6, 8, 9, 11]):
            assert notes[i].pitch == 60 + p, "notes[i].pitch != 60 + p"
        score.transpose(7, er=er, max_interval=5)
        for i, p in enumerate([0, 2, 3, 5, 6, 8, 9, 11]):
            assert notes[i].pitch == 60 + p, "notes[i].pitch != 60 + p"
        score.transpose(-7, er=er, max_interval=6)
        for i, p in enumerate([0, 2, 3, 5, 6, 8, 9, 11]):
            assert notes[i].pitch == 60 + p, "notes[i].pitch != 60 + p"
        score.transpose(9, er=er, max_interval=7)
        for i, p in enumerate([4, 5, 7, 8, 10, 11, 13, 14]):
            assert notes[i].pitch == 60 + p, "notes[i].pitch != 60 + p"
        score.transpose(-9, er=er, max_interval=6)
        for i, p in enumerate([0, 2, 3, 5, 6, 8, 9, 11]):
            assert notes[i].pitch == 60 + p, "notes[i].pitch != 60 + p"
        score.transpose(2)
        for i, p in enumerate([0, 2, 3, 5, 6, 8, 9, 11]):
            assert notes[i].pitch == 62 + p, "notes[i].pitch != 60 + p"
    except:  # pylint: disable=bare-except

        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(
            exc_type, exc_value, exc_traceback, file=sys.stdout
        )
        breakpoint()


if __name__ == "__main__":
    test_get_prev_and_last_notes()
    test_get_sounding_pitches()
    test_get_harmony_i()
    test_score_misc_attrs()
    test_generic_transpose()
