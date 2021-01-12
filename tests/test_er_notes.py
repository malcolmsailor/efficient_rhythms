import os
import sys
import traceback

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

import src.er_notes as er_notes  # pylint: disable=wrong-import-position
import src.er_preprocess as er_preprocess  # pylint: disable=wrong-import-position


def test_score_get_prev_and_last_notes():
    settingsdict = {"num_voices": 2, "tet": 12}
    er = er_preprocess.preprocess_settings(settingsdict)
    # voice, pitch, attack, dur, evaluates_to
    notes = [
        (0, 57, 0, 0.75, None),
        (1, 58, 0.25, 0.25, None),
        (1, 59, 0.5, 0.75, 58),
        (0, 60, 0.75, 0.75, 57),
    ]
    score = er_notes.Score(num_voices=er.num_voices, tet=er.tet)
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


def test_score_get_sounding_pitches():
    settingsdict = {"num_voices": 2, "tet": 12}
    er = er_preprocess.preprocess_settings(settingsdict)
    score = er_notes.Score(num_voices=er.num_voices, tet=er.tet)
    # voice, pitch, attack, dur
    notes = [
        (0, 57, 0, 0.75),
        (1, 58, 0.25, 0.25),
        (1, 59, 0.5, 0.75),
        (0, 60, 0.75, 0.75),
    ]
    for (v, p, a, d) in notes:  # pylint: disable=invalid-name
        score.add_note(v, p, a, d)
    # attack_time, dur, min_attack_time, min_dur, sounding_pitches
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
                    a, dur=d, min_attack_time=m1, min_dur=m2
                )
                == sp
            ), f"score.get_sounding_pitches({a}, dur={d}, min_attack_time={m1}, min_dur={m2}) != {sp}"
        except:  # pylint: disable=bare-except
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(
                exc_type, exc_value, exc_traceback, file=sys.stdout
            )
            breakpoint()


if __name__ == "__main__":
    test_score_get_prev_and_last_notes()
    test_score_get_sounding_pitches()
