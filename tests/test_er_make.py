from efficient_rhythms import er_classes
from efficient_rhythms import er_make
from efficient_rhythms import er_settings


def _init_score_with_notes(notes, er):
    score = er_classes.Score(num_voices=er.num_voices, tet=er.tet)
    for note_i, note in enumerate(notes):
        score.add_note(0, note, 1 * note_i, note)
    return score


def _init_score_with_voices_and_notes(voices_and_notes, er):
    score = er_classes.Score(num_voices=er.num_voices, tet=er.tet)
    for voice_i, voice in enumerate(voices_and_notes):
        for note_i, note in enumerate(voice):
            score.add_note(voice_i, note, 1 * note_i, note)
    return score


def test_too_many_alternations():

    settingsdict = {"num_voices": 1, "max_alternations": 3}
    er = er_settings.get_settings(settingsdict)
    # pitch, onset, dur, evaluates_to

    notes = [60, 62, 60, 62, 60]
    score = _init_score_with_notes(notes, er)
    assert er_make.too_many_alternations(er, score, 62, 5, 0)
    assert er_make.too_many_alternations(er, score, 62, 10, 0)
    assert not er_make.too_many_alternations(er, score, 60, 5, 0)
    notes = [60, 60, 60, 60, 60]
    score = _init_score_with_notes(notes, er)
    assert not er_make.too_many_alternations(er, score, 62, 5, 0)
    assert not er_make.too_many_alternations(er, score, 60, 5, 0)
    notes = [60, 62, 60, 62]
    score = _init_score_with_notes(notes, er)
    assert not er_make.too_many_alternations(er, score, 62, 5, 0)


class BasicPossibleNote(er_make.PossibleNote):
    def __init__(  # pylint: disable=super-init-not-called
        self, score, onset, dur, voice_i
    ):
        self.score = score
        self.onset = onset
        self.dur = dur
        self.voice_i = voice_i


def test_remove_parallels():
    settingsdict = {
        "num_voices": 4,
        "max_alternations": 3,
        "prohibit_parallels": (7, 0),
    }
    er = er_settings.get_settings(settingsdict)
    voices_and_notes = [(60, 62), (64, 65), (71,), (72,)]
    score = _init_score_with_voices_and_notes(voices_and_notes, er)
    poss_note = BasicPossibleNote(score, 1, 1, 2)
    available_pitches = [45, 47, 48, 50, 69, 71, 72, 74]
    er_make.remove_parallels(er, score, available_pitches, poss_note)
    assert available_pitches == [45, 47, 50, 69, 71, 74]
    poss_note = BasicPossibleNote(score, 1, 1, 3)
    available_pitches = [45, 47, 48, 50, 69, 71, 72, 74]
    er_make.remove_parallels(er, score, available_pitches, poss_note)
    assert available_pitches == [45, 47, 48, 69, 71, 72]


if __name__ == "__main__":
    test_too_many_alternations()
    test_remove_parallels()
