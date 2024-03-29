from efficient_rhythms import er_make2
from efficient_rhythms import er_classes
from efficient_rhythms import er_settings


def test_check_harmonic_intervals():
    settingsdict = {
        "num_voices": 2,
        "tet": 12,
        "forbidden_interval_classes": [
            0,
        ],
    }
    er = er_settings.get_settings(settingsdict)

    # voice, pitch, onset, dur, evaluates_to
    notes1 = [
        (0, 60, 1.5, 0.5, True),
        (1, 64, 1.75, 0.25, True),
        (0, 64, 2, 0.25, True),
        (1, 76, 2, 0.5, False),
    ]
    notes2 = [
        (1, 52, 1.75, 0.25, True),
        (0, 60, 1.5, 0.5, True),
        (1, 64, 2, 0.5, True),
        (0, 64, 2, 0.25, False),
    ]
    for notes in (notes1, notes2):
        score = er_classes.Score(num_voices=er.num_voices, tet=er.tet)
        for (v, p, a, d, b) in notes:  # pylint: disable=invalid-name
            assert (
                er_make2.check_harmonic_intervals(er, score, p, a, d, v) is b
            ), (
                "er_make2.check_harmonic_intervals"
                f"(er, score, {p}, {a}, {d}, {v}) is not {b}"
            )
            score.add_note(v, p, a, d)
    settingsdict = {
        "num_voices": 3,
        "tet": 12,
        "forbidden_intervals": [
            0,
        ],
        "forbidden_interval_classes": [],
    }
    er = er_settings.get_settings(settingsdict)
    notes1 = [
        (0, 60, 0, 1.0, True),
        (1, 72, 0, 1.0, True),
        (2, 60, 0, 0.5, False),
        (2, 72, 0, 0.5, False),
    ]
    for notes in (notes1,):
        score = er_classes.Score(num_voices=er.num_voices, tet=er.tet)
        for (v, p, a, d, b) in notes:  # pylint: disable=invalid-name
            assert (
                er_make2.check_harmonic_intervals(er, score, p, a, d, v) is b
            ), (
                "er_make2.check_harmonic_intervals"
                f"(er, score, {p}, {a}, {d}, {v}) is not {b}"
            )
            score.add_note(v, p, a, d)


def test_check_melodic_intervals():
    def _sub(notes, max_interval, min_interval):
        settingsdict = {
            "seed": 0,
            "num_harmonies": 4,
            "pattern_len": 8,
            "harmony_len": 8,
            "foot_pcs": [0, 5, 10, 3],
            "num_reps_super_pattern": 2,
            "overlap": False,
            "consonance_treatment": "none",
            "obligatory_onsets_modulo": [2],
            "forbidden_interval_classes": [],
            "num_voices": 1,
            "max_interval": max_interval,
            "min_interval": min_interval,
        }
        er = er_settings.get_settings(settingsdict)
        for (test_ps, prev_p, result_ps) in notes:
            assert (
                er_make2.check_melodic_intervals(
                    er, test_ps, prev_p, max_interval, min_interval, 0
                )
                == result_ps
            ), (
                "er_make2.check_melodic_intervals"
                f"(er, test_ps, prev_p, max_interval, min_interval, 0) != {result_ps}"
            )

    # SPECIFIC INTERVALS
    # MAX INTERVAL
    max_interval = -5
    min_interval = 0
    # test_ps, prev_p, result_ps
    notes = [
        ([53, 55, 57, 59, 60, 62, 64, 65], 64, [59, 60, 62, 64, 65]),
        ([60, 62, 64, 65, 67, 69, 71, 72], 60, [60, 62, 64, 65]),
        ([60, 62, 64, 65, 67, 69, 71, 72], 62, [60, 62, 64, 65, 67]),
        ([60, 62, 64, 65, 67, 69, 71, 72], 64, [60, 62, 64, 65, 67, 69]),
        ([60, 62, 64, 65, 67, 69, 71, 72], 65, [60, 62, 64, 65, 67, 69]),
        ([60, 62, 64, 65, 67, 69, 71, 72], 67, [62, 64, 65, 67, 69, 71, 72]),
        ([60, 62, 64, 65, 67, 69, 71, 72], 69, [64, 65, 67, 69, 71, 72]),
    ]
    _sub(notes, max_interval, min_interval)

    # [[53, 55, 57, 59, 60, 62, 64, 65]]
    # 64
    # -5
    # 0
    # 0
    # [[53, 55, 57, 59, 60, 62, 64, 65]]

    # MIN INTERVAL
    max_interval = -5
    min_interval = -3
    # test_ps, prev_p, result_ps
    notes = [
        ([60, 62, 64, 65, 67, 69, 71, 72], 60, [64, 65]),
        ([60, 62, 64, 65, 67, 69, 71, 72], 62, [65, 67]),
        ([60, 62, 64, 65, 67, 69, 71, 72], 64, [60, 67, 69]),
        ([60, 62, 64, 65, 67, 69, 71, 72], 65, [60, 62, 69]),
        ([60, 62, 64, 65, 67, 69, 71, 72], 67, [62, 64, 71, 72]),
        ([60, 62, 64, 65, 67, 69, 71, 72], 69, [64, 65, 72]),
    ]
    _sub(notes, max_interval, min_interval)


if __name__ == "__main__":
    test_check_harmonic_intervals()
    test_check_melodic_intervals()
