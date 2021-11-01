from fractions import Fraction
import warnings

import numpy as np

import efficient_rhythms.er_settings as er_settings
import efficient_rhythms.er_rhythm as er_rhythm


def test_pad_truncations():
    # data = {
    #     0: 0.5,
    #     1: 0.25,
    # }
    initial_onsets = np.array([0.0, 1.0])
    initial_durs = np.array([0.5, 0.25])
    settingsdict = {
        "num_voices": 2,
        "rhythm_len": [1.5, 2],
        "pattern_len": [2.5, 3],
        "truncate_patterns": True,
    }
    onsets_ = [
        [0, 1, 1.5, 2.5],
        [0, 1, 2],
    ]
    er = er_settings.get_settings(settingsdict, silent=True)
    for k, onsets in enumerate(onsets_):

        rhythm = er_rhythm.rhythm.Rhythm.from_er_settings(
            er, k, initial_onsets, initial_durs
        )
        assert len(onsets) == len(rhythm._data)
        for i, j in zip(onsets, rhythm._data):
            assert i == j

    # data = {
    #     0: 0.25,
    #     0.5: 0.25,
    #     1.0: 0.25,
    #     1.5: 0.25,
    # }
    initial_onsets = np.array([0.0, 0.5, 1.0, 1.5])
    initial_durs = np.array([0.25, 0.25, 0.25, 0.25])
    settingsdict = {
        "num_voices": 3,
        "rhythm_len": [1.75, 2, 3.25],
        "pattern_len": [3, 3.75, 7],
        "truncate_patterns": True,
    }
    onsets_ = [
        [
            0,
            0.5,
            1.0,
            1.5,
            1.75,
            2.25,
            2.75,
            3.0,
            3.5,
            4.0,
            4.5,
            4.75,
            5.25,
            5.75,
            6.0,
            6.5,
        ],
        [
            0,
            0.5,
            1.0,
            1.5,
            2.0,
            2.5,
            3.0,
            3.5,
            3.75,
            4.25,
            4.75,
            5.25,
            5.75,
            6.25,
            6.75,
        ],
        [
            0,
            0.5,
            1.0,
            1.5,
            3.25,
            3.75,
            4.25,
            4.75,
            6.5,
        ],
    ]
    er = er_settings.get_settings(settingsdict, silent=True)
    for k, onsets in enumerate(onsets_):

        rhythm = er_rhythm.rhythm.Rhythm.from_er_settings(
            er, k, initial_onsets, initial_durs
        )
        assert len(onsets) == len(rhythm._data)
        for i, j in zip(onsets, rhythm._data):
            assert i == j


def test_update_pattern_vl_order():
    pattern_lens_list = [(2.5, 3, 3.5, 4), (2, 3, 5)]
    for pattern_lens in pattern_lens_list:
        for truncate in (True, False):
            settingsdict = {
                "num_voices": len(pattern_lens),
                "tet": 12,
                "pattern_len": pattern_lens,
                "truncate_patterns": truncate,
            }
            er = er_settings.get_settings(settingsdict, silent=True)
            er_rhythm.init_rhythms(er)
            er_rhythm.rhythms_handler(er)
            voice_is = {}
            for item in er.pattern_vl_order:
                voice_i = item.voice_i
                rhythm = er.rhythms[voice_i]
                assert item.start_time <= rhythm.at_or_after(item.start_i)[0]
                assert item.end_time <= rhythm.at_or_after(item.end_i)[0]
                pattern_len = pattern_lens[voice_i]
                if truncate:
                    truncate_len = max(pattern_lens)
                    truncate_start = truncate_len // pattern_len * pattern_len
                if voice_i in voice_is:
                    assert (
                        item.start_i == voice_is[voice_i]
                    ), "item.start_i != voice_is[voice_i]"
                # TODO following test no longer works after rewrite of rhythm
                # code because len(rhythm) is now the entire pattern including
                # all truncations.
                # try:
                #     assert item.end_i - item.start_i == len(
                #         er.rhythms[voice_i]
                #     ), (
                #         "item.end_i - item.start_i "
                #         "!= len(er.rhythms[voice_i])"
                #     )
                # except AssertionError:
                #     # we should only get an AssertionError if truncate_len is
                #     # defined
                #         assert (
                #             item.start_time >= truncate_len
                #             or item.start_time % truncate_len == truncate_start
                #         ), (
                #             "item.start_time < truncate_len and item.start_time % "
                #             "truncate_len != truncate_start"
                #         )

                voice_is[voice_i] = item.end_i


def test_get_i():
    # settingsdict = {
    #     "num_voices": 2,
    #     "onset_density": 0.5,
    #     "rhythm_len": [1.5, 7],
    #     "pattern_len": [4, 7],
    # }
    # er = er_settings.get_settings(settingsdict)
    # rhythm = er_rhythm.rhythms_handler(er)[0]
    # num_reps = 2
    # rhythm_onsets = []
    # for rep in range(num_reps):
    #     rhythm_onsets.extend(
    #         [a + rep * rhythm.total_rhythm_len for a in rhythm.onsets]
    #     )
    # try:
    #     for i in range(settingsdict["pattern_len"][0] * 4 * num_reps):
    #         time = i / 4
    #         j = rhythm.get_i_at_or_after(time)
    #         onsets = [a for a in rhythm_onsets if a >= time]
    #         assert rhythm.get_onset_and_dur(j)[0] == min(onsets)
    #         j = rhythm.get_i_before(time)
    #         try:
    #             onset = max([a for a in rhythm_onsets if a < time])
    #         except ValueError:
    #             # max() got an empty iterable because time is < all onset times
    #             assert j == -1
    #         else:
    #             assert rhythm.get_onset_and_dur(j)[0] == onset
    #         j = rhythm.get_i_at_or_before(time)
    #         try:
    #             onset = max([a for a in rhythm_onsets if a <= time])
    #         except ValueError:
    #             # max() got an empty iterable because time is < all onset times
    #             assert j == -1
    #         else:
    #             assert rhythm.get_onset_and_dur(j)[0] == onset

    # except:  # pylint: disable=bare-except

    #     exc_type, exc_value, exc_traceback = sys.exc_info()
    #     traceback.print_exception(
    #         exc_type, exc_value, exc_traceback, file=sys.stdout
    #     )
    #     breakpoint()
    settingsdict = {
        "pattern_len": [1.5, 4],
        "truncate_patterns": True,
        "harmony_len": 4,
        "num_harmonies": 4,
        "num_voices": 2,
        "onset_density": 0.7,
    }
    onsets_and_durs = {
        Fraction(0, 1): Fraction(1, 4),
        Fraction(1, 4): Fraction(1, 4),
        Fraction(1, 2): Fraction(1, 4),
        Fraction(3, 4): Fraction(3, 4),
    }
    initial_onsets = np.array(list(onsets_and_durs.keys()))
    initial_durs = np.array(list(onsets_and_durs.values()))
    er = er_settings.get_settings(settingsdict, silent=True)
    rhythm = er_rhythm.rhythm.Rhythm.from_er_settings(
        er, 0, initial_onsets, initial_durs
    )
    max_onset = max(rhythm.onsets)
    for i in range(50):
        time = i / 8
        before = rhythm.get_i_before(time)
        at_or_after = rhythm.get_i_at_or_after(time)
        at_or_before = rhythm.get_i_at_or_before(time)
        after = rhythm.get_i_after(time)
        assert before + 1 == at_or_after
        assert at_or_before + 1 == after
        # if there is a note at time, then both comparisons should be false;
        # otherwise, they should both be true
        assert (before == at_or_before) == (at_or_after == after)
        assert (before == at_or_before) or (at_or_before == at_or_after)
        assert (after == at_or_after) or (at_or_before == at_or_after)
        assert rhythm.get_onset_and_dur(at_or_after) == rhythm.at_or_after(time)


def test_onset_positions():
    basesettings = {
        "rhythm_len": 4,
        "pattern_len": 4,
        "onset_subdivision": 1,
        "sub_subdivisions": (4, 3),
    }
    er = er_settings.get_settings(basesettings, silent=True)
    onset_positions = er_rhythm.make._onset_positions(er, 0)
    assert np.all(np.less(onset_positions[:4] - [0, 4 / 7, 1, 11 / 7], 1e-6))
    basesettings["onset_subdivision"] = 0.5
    er = er_settings.get_settings(basesettings, silent=True)
    onset_positions = er_rhythm.make._onset_positions(er, 0)
    assert np.all(
        np.less(onset_positions[:4] - [0, 4 / 14, 0.5, 11 / 14], 1e-6)
    )


def test_new_onsets():
    # presently, if the number of notes implied by onset_density is smaller than
    #   the number of notes implied by obligatory onsets, excess obligatory
    #   onsets will be ignored in an undefined order
    basesettings = {
        "num_voices": 1,
        "pattern_len": 2,
        "onset_subdivision": 0.25,
    }
    settingsdict1 = {
        "obligatory_onsets": (0,),
        "obligatory_onsets_modulo": 0.25,
        "onset_density": 1.0,
    }
    test1 = lambda x: np.all(np.equal(x, np.arange(8) * 0.25))

    settingsdict2 = {
        "obligatory_onsets": (0, 0.75),
        "obligatory_onsets_modulo": 1,
        "onset_density": 0.75,
    }
    test2 = lambda x: len(x) == 6 and all([t in x for t in (0, 0.75, 1, 1.75)])

    settingsdict3 = {
        "onset_density": 0.8,
    }
    test3 = lambda x: len(x) == 6
    settingsdict4 = {
        "onset_density": 0.0,
    }
    test4 = lambda x: len(x) == 1
    tests = [
        (settingsdict1, test1),
        (settingsdict2, test2),
        (settingsdict3, test3),
        (settingsdict4, test4),
    ]
    for settingsdict, test_func in tests:
        settingsdict.update(basesettings)
        er = er_settings.get_settings(settingsdict, silent=True)
        onsets = er_rhythm.make.get_onsets(er, 0, ())
        assert test_func(onsets)
        assert all([t for t in onsets >= 0])
        assert all([t for t in onsets < 2])

    basesettings = {
        "num_voices": 4,
        "hocketing": ((0, 2), (0, 3)),
        "rhythmic_quasi_unison": ((0, 1, 3),),
        "pattern_len": 2,
        "truncate_patterns": True,
        "onset_density": 0.75,
    }
    oblig_settings = {
        "obligatory_onsets": (0, 0.75, 1.75),
        "obligatory_onsets_modulo": 2,
    }
    oblig_settings.update(basesettings)
    prev_onsets = np.array([0.25, 1.0])
    prev_durs = np.array([0.5, 0.25])

    er = er_settings.get_settings(basesettings, silent=True)
    prev_rhythm = er_rhythm.rhythm.Rhythm.from_er_settings(
        er, 0, prev_onsets, prev_durs
    )
    for _ in range(5):
        onsets = er_rhythm.make.get_onsets(er, 1, (prev_rhythm,))
        assert np.all(np.isin(prev_onsets, onsets))
    for _ in range(5):
        onsets = er_rhythm.make.get_onsets(er, 2, (prev_rhythm,))
        assert np.all(np.isin(prev_onsets, onsets, invert=True))
    for _ in range(5):
        onsets = er_rhythm.make.get_onsets(er, 3, (prev_rhythm,))
        assert np.all(np.isin(prev_onsets, onsets))


def test_new_iois():
    basesettings = {
        "num_voices": 1,
        "pattern_len": 2,
    }
    onsets = np.array([0.25, 1.0, 1.125, 1.875])
    tests = [
        (True, (0.75, 0.125, 0.75, 0.375)),
        (False, (0.75, 0.125, 0.75, 0.125)),
    ]
    for overlap, iois in tests:
        basesettings["overlap"] = overlap
        er = er_settings.get_settings(basesettings, silent=True)
        result = er_rhythm.make.get_iois_from_er(er, 0, onsets)
        assert np.all(np.equal(result, iois))


def test_new_comma():
    basesettings = {
        "num_voices": 1,
        "pattern_len": 2.125,
        "overlap": True,
    }
    comma = 0.125
    onsets = np.array([0.25, 1.0, 1.125, 1.875])
    for i in range(len(onsets) + 1):
        basesettings["comma_position"] = i
        er = er_settings.get_settings(basesettings, silent=True)
        temp = onsets.copy()
        er_rhythm.make._add_comma(er, 0, temp, comma)

        comparison = onsets.copy()
        comparison[i:] += 0.125
        assert np.all(np.equal(temp, comparison))

    tests = [
        ("end", lambda x: np.all(np.equal(x, [0.25, 1.0, 1.125, 1.875]))),
        (
            "beginning",
            lambda x: np.all(
                np.equal(x, np.array([0.25, 1.0, 1.125, 1.875]) + 0.125)
            ),
        ),
        ("middle", lambda x: 0.125 <= sum(x - onsets) < 0.5),
        ("anywhere", lambda x: 0 <= sum(x - onsets) <= 0.5),
    ]
    for setting, test_func in tests:
        basesettings["comma_position"] = setting
        er = er_settings.get_settings(basesettings, silent=True)
        for _ in range(5):
            temp = onsets.copy()
            er_rhythm.make._add_comma(er, 0, temp, comma)
            assert test_func(temp)


def test_new_durs():
    basesettings = {
        "num_voices": 1,
        "pattern_len": 2,
        "overlap": True,
    }
    onsets = np.arange(4)
    iois = np.array((0.75, 0.125, 0.75, 0.375))

    for density in (0, 0.25, 0.5, 0.75, 1.0):
        basesettings["dur_density"] = density
        er = er_settings.get_settings(basesettings, silent=True)

        # We do it a few times to get some randomnesss
        for _ in range(3):
            durs = er_rhythm.make.get_durs(er, 0, iois, onsets, ())
            assert (
                abs(density - (sum(durs) / er.rhythm_len[0]))
                <= er.dur_subdivision[0] / 2
            ) or np.all(np.equal(durs, np.minimum(iois, er.min_dur[0])))
            assert np.all(np.less_equal(durs, iois))

    basesettings = {
        "num_voices": 2,
        "pattern_len": 4,
        "min_dur": 1 / 8,
        "dur_subdivision": 1 / 8,
        "rhythmic_quasi_unison": True,
        "rhythmic_quasi_unison_constrain": True,
        "onset_density": 0.5,
    }
    leader_onsets = np.array([0.0, 1.0, 2.25, 3.5])
    leader_durs = np.array([0.25, 0.75, 0.5, 0.5])
    leader_density = 0.5
    for density in (0, 0.25, 0.5, 0.75, 1.0):
        basesettings["dur_density"] = density
        er = er_settings.get_settings(basesettings, silent=True)
        l_rhythm = er_rhythm.rhythm.Rhythm.from_er_settings(
            er, 0, leader_onsets, leader_durs
        )
        onsets = er_rhythm.make.get_onsets(er, 1, (l_rhythm,))
        iois = er_rhythm.make.get_iois_from_er(er, 1, onsets)
        durs = er_rhythm.make.get_durs(er, 1, iois, onsets, (l_rhythm,))
        actual_density = sum(durs) / er.rhythm_len[1]
        # TODO write a function to test that:
        #   - if actual_density is less than leader_density, all durations
        #       lie within leader durations
        #   - otherwise, leader_density is "full"
        warnings.warn(
            "test_new_durs() with rhythmic_quasi_unison_constrain is not complete"
        )


def test_hocketing_indices():
    basesettings = {
        "num_voices": 3,
        "hocketing": True,
        "rhythmic_quasi_unison": True,
        "rhythm_len": 2,
    }
    er = er_settings.get_settings(basesettings, silent=True)
    empty_prev_rhythm1 = er_rhythm.rhythm.Rhythm.from_er_settings(er, 0, (), ())
    nonempty_prev_rhythm1 = er_rhythm.rhythm.Rhythm.from_er_settings(
        er,
        0,
        np.array([0.0, 1.0, 1.5, 1.875]),
        np.array([0.25, 0.25, 0.25, 0.125]),
    )
    empty_prev_rhythm2 = er_rhythm.rhythm.Rhythm.from_er_settings(er, 1, (), ())
    onset_positions = er_rhythm.make._onset_positions(er, 2)
    oblig_indices = [0, 1, 5, 7]
    # w/ empty previous rhythms, no oblig onsets
    hocket_indices = er_rhythm.make._hocketing_indices(
        er, 2, onset_positions, (empty_prev_rhythm1, empty_prev_rhythm2), ()
    )
    qu_indices, constrain_indices = er_rhythm.make._quasi_unison_indices(
        er, 2, onset_positions, (empty_prev_rhythm1, empty_prev_rhythm2), ()
    )
    assert set(hocket_indices) == {i for i in range(8)}
    assert len(qu_indices) == 0
    assert len(constrain_indices) == 0
    # w/ empty previous rhythms, oblig onsets
    hocket_indices = er_rhythm.make._hocketing_indices(
        er,
        2,
        onset_positions,
        (empty_prev_rhythm1, empty_prev_rhythm2),
        (oblig_indices),
    )
    qu_indices, constrain_indices = er_rhythm.make._quasi_unison_indices(
        er,
        2,
        onset_positions,
        (empty_prev_rhythm1, empty_prev_rhythm2),
        (oblig_indices),
    )
    assert set(hocket_indices) == {2, 3, 4, 6}
    assert len(qu_indices) == 0
    assert len(constrain_indices) == 0
    # w/ one non-empty previous rhythms
    hocket_indices = er_rhythm.make._hocketing_indices(
        er,
        2,
        onset_positions,
        (nonempty_prev_rhythm1, empty_prev_rhythm2),
        (),
    )
    qu_indices, constrain_indices = er_rhythm.make._quasi_unison_indices(
        er,
        2,
        onset_positions,
        (nonempty_prev_rhythm1, empty_prev_rhythm2),
        (),
    )
    assert set(hocket_indices) == {1, 2, 3, 5, 7}
    assert set(qu_indices) == {0, 4, 6}
    # w/ one non-empty previous rhythm, oblig onsets
    hocket_indices = er_rhythm.make._hocketing_indices(
        er,
        2,
        onset_positions,
        (nonempty_prev_rhythm1, empty_prev_rhythm2),
        (oblig_indices),
    )
    qu_indices, constrain_indices = er_rhythm.make._quasi_unison_indices(
        er,
        2,
        onset_positions,
        (nonempty_prev_rhythm1, empty_prev_rhythm2),
        (oblig_indices),
    )
    assert set(hocket_indices), {2, 3}
    assert set(qu_indices), {4, 6}


def test_quasi_unison_constrained_indices():
    basesettings = {
        "num_voices": 3,
        "hocketing": True,
        "rhythmic_quasi_unison": True,
        "pattern_len": [2, 3, 1.5],
        "truncate_patterns": True,
    }
    er = er_settings.get_settings(basesettings, silent=True)
    empty_prev_rhythm1 = er_rhythm.rhythm.Rhythm.from_er_settings(er, 0, (), ())
    nonempty_prev_rhythm1 = er_rhythm.rhythm.Rhythm.from_er_settings(
        er,
        0,
        np.array([0.25, 1.0, 1.5, 1.875]),
        np.array([0.5, 0.25, 0.375, 0.125]),
    )
    nonempty_prev_rhythm2 = er_rhythm.rhythm.Rhythm.from_er_settings(
        er,
        0,
        np.array([0.0]),
        np.array([1.55]),
    )
    onset_positions1 = er_rhythm.make._onset_positions(er, 1)
    onset_positions2 = er_rhythm.make._onset_positions(er, 2)
    oblig_indices = [0, 1, 5, 7]
    at, during = er_rhythm.make._quasi_unison_constrained_indices(
        er, 1, onset_positions1, (empty_prev_rhythm1,), ()
    )
    assert len(at) == 0
    assert len(during) == 0
    at, during = er_rhythm.make._quasi_unison_constrained_indices(
        er, 1, onset_positions1, (nonempty_prev_rhythm1,), ()
    )
    assert at == {1, 4, 6, 9}
    assert during == {2, 7, 10}
    at, during = er_rhythm.make._quasi_unison_constrained_indices(
        er, 1, onset_positions1, (nonempty_prev_rhythm1,), oblig_indices
    )
    assert at == {4, 6, 9}
    assert during == {2, 10}
    at, during = er_rhythm.make._quasi_unison_constrained_indices(
        er, 1, onset_positions1, (nonempty_prev_rhythm2,), ()
    )
    assert at == {0, 8}
    assert during == {1, 2, 3, 4, 5, 6, 9, 10, 11}
    at, during = er_rhythm.make._quasi_unison_constrained_indices(
        er, 2, onset_positions2, (nonempty_prev_rhythm1,), ()
    )
    assert at == {1, 4}
    assert during == {2}
    at, during = er_rhythm.make._quasi_unison_constrained_indices(
        er, 2, onset_positions2, (nonempty_prev_rhythm2,), ()
    )
    assert at == {0}
    assert during == {1, 2, 3, 4, 5}


def test_indices_handler():
    basesettings = {
        "num_voices": 4,
        "hocketing": ((0, 2), (0, 3)),
        "rhythmic_quasi_unison": ((0, 1, 3),),
        "pattern_len": 2,
        "truncate_patterns": True,
    }
    oblig_settings = {
        "obligatory_onsets": (0, 0.75, 1.75),
        "obligatory_onsets_modulo": 2,
    }
    oblig_settings.update(basesettings)
    prev_onsets = np.array([0.25, 1.0])
    prev_durs = np.array([0.5, 0.25])

    er = er_settings.get_settings(basesettings, silent=True)
    prev_rhythm = er_rhythm.rhythm.Rhythm.from_er_settings(
        er, 0, prev_onsets, prev_durs
    )
    onset_positions0 = er_rhythm.make._onset_positions(er, 0)
    indices, ends = er_rhythm.make._indices_handler(er, 0, (), onset_positions0)
    assert np.all(np.equal(indices, np.arange(8)))
    assert ends == [0, 0, 0, 0]
    onset_positions1 = er_rhythm.make._onset_positions(er, 1)
    indices, ends = er_rhythm.make._indices_handler(
        er, 1, (prev_rhythm,), onset_positions1
    )
    assert np.all(np.equal(indices[:2], [1, 4]))
    assert set(indices[2:]) == {0, 2, 3, 5, 6, 7}
    assert ends == [0, 2, 2, 2]
    onset_positions2 = er_rhythm.make._onset_positions(er, 2)
    indices, ends = er_rhythm.make._indices_handler(
        er, 2, (prev_rhythm,), onset_positions2
    )
    assert np.all(np.equal(indices[:6], [0, 2, 3, 5, 6, 7]))
    assert set(indices[6:]) == {1, 4}
    assert ends == [0, 0, 0, 6]
    onset_positions3 = er_rhythm.make._onset_positions(er, 3)
    indices, ends = er_rhythm.make._indices_handler(
        er, 3, (prev_rhythm,), onset_positions3
    )
    assert np.all(np.equal(indices[:2], [1, 4]))
    assert set(indices[2:]) == {0, 2, 3, 5, 6, 7}
    assert ends == [0, 2, 2, 8]
    # With obligatory onsets
    er = er_settings.get_settings(oblig_settings, silent=True)
    onset_positions0 = er_rhythm.make._onset_positions(er, 0)
    indices, ends = er_rhythm.make._indices_handler(er, 0, (), onset_positions0)
    assert np.all(np.equal(indices[:3], [0, 3, 7]))
    assert set(indices[3:]) == {1, 2, 4, 5, 6}
    assert ends == [3, 3, 3, 3]
    onset_positions1 = er_rhythm.make._onset_positions(er, 1)
    indices, ends = er_rhythm.make._indices_handler(
        er, 1, (prev_rhythm,), onset_positions1
    )
    assert np.all(np.equal(indices[:3], [0, 3, 7]))
    assert np.all(np.equal(indices[3:5], [1, 4]))
    assert set(indices[3:5]) == {1, 4}
    assert set(indices[5:]) == {2, 5, 6}
    assert ends == [3, 5, 5, 5]
    onset_positions2 = er_rhythm.make._onset_positions(er, 2)
    indices, ends = er_rhythm.make._indices_handler(
        er, 2, (prev_rhythm,), onset_positions2
    )
    assert np.all(np.equal(indices[:3], [0, 3, 7]))
    assert set(indices[3:6]) == {2, 5, 6}
    assert set(indices[6:]) == {1, 4}
    assert ends == [3, 3, 3, 6]
    onset_positions3 = er_rhythm.make._onset_positions(er, 3)
    indices, ends = er_rhythm.make._indices_handler(
        er, 3, (prev_rhythm,), onset_positions3
    )
    assert np.all(np.equal(indices[:3], [0, 3, 7]))
    assert set(indices[3:5]) == {1, 4}
    assert set(indices[5:]) == {2, 5, 6}
    assert ends == [3, 5, 5, 8]


def test_within_leader_durs():
    basesettings = {
        "num_voices": 2,
        "rhythmic_quasi_unison": True,
        "rhythmic_quasi_unison_constrain": True,
        "pattern_len": 2,
    }
    er = er_settings.get_settings(basesettings, silent=True)
    leader1_onsets = np.array([0, 0.75])
    leader1_durs = np.array([0.5, 0.875])
    leader1 = er_rhythm.rhythm.Rhythm.from_er_settings(
        er, 0, leader1_onsets, leader1_durs
    )
    leader2_onsets = np.arange(16) * 0.125
    leader2_durs = np.repeat(0.125, 16)
    leader2 = er_rhythm.rhythm.Rhythm.from_er_settings(
        er, 0, leader2_onsets, leader2_durs
    )
    follower_onsets = np.array([0, 0.25, 0.75, 1.125, 1.25, 1.375])
    follower_iois = er_rhythm.make.get_iois_from_er(er, 1, follower_onsets)
    out = er_rhythm.make._within_leader_durs(
        er, 1, follower_iois, follower_onsets, leader1
    )
    assert np.all(np.equal(out, [0.25, 0.25, 0.375, 0.125, 0.125, 0.25]))
    out = er_rhythm.make._within_leader_durs(
        er, 1, follower_iois, follower_onsets, leader2
    )
    assert np.all(np.equal(out, [0.25, 0.5, 0.375, 0.125, 0.125, 0.625]))


def test_yield_onset_and_consecutive_release():
    basesettings = {
        "num_voices": 1,
        "pattern_len": 2,
    }
    er = er_settings.get_settings(basesettings, silent=True)
    onsets = np.array([0, 0.25, 0.75, 1.0, 1.5, 1.625])
    durs = np.array([0.25, 0.25, 0.125, 0.5, 0.125, 0.125])
    rhythm1 = er_rhythm.rhythm.Rhythm.from_er_settings(er, 0, onsets, durs)
    onsets = np.array([])
    durs = np.array([])
    rhythm2 = er_rhythm.rhythm.Rhythm.from_er_settings(er, 0, onsets, durs)
    onsets = np.arange(16) * 0.125
    durs = np.repeat(0.125, 16)
    rhythm3 = er_rhythm.rhythm.Rhythm.from_er_settings(er, 0, onsets, durs)
    out = list(er_rhythm.make._yield_onset_and_consecutive_release(rhythm1))
    assert out == [(0, 0.5), (0.75, 0.875), (1.0, 1.75)]
    out = list(er_rhythm.make._yield_onset_and_consecutive_release(rhythm2))
    assert out == []
    out = list(er_rhythm.make._yield_onset_and_consecutive_release(rhythm3))
    assert out == [(0, 2)]


def test_onsets_between():
    basesettings = {
        "num_voices": 1,
        "pattern_len": 2,
    }
    er = er_settings.get_settings(basesettings, silent=True)
    onsets = np.array([0, 0.5, 1.0, 1.5])
    durs = np.repeat(0.25, 4)
    rm = er_rhythm.rhythm.Rhythm.from_er_settings(er, 0, onsets, durs)
    out = rm.onsets_between(0, 2)
    assert np.all(out == onsets)
    out = rm.onsets_between(0, 4)
    assert np.all(out == np.concatenate([onsets, onsets + 2]))
    out = rm.onsets_between(0, 8)
    assert np.all(
        out == np.concatenate([onsets, onsets + 2, onsets + 4, onsets + 6])
    )
    out = rm.onsets_between(0.25, 1.5)
    assert np.all(out == onsets[1:3])
    out = rm.onsets_between(0.25, 2.25)
    assert np.all(out == [0.5, 1.0, 1.5, 2.0])
    out = rm.onsets_between(0.25, 3.25)
    assert np.all(out == [0.5, 1.0, 1.5, 2.0, 2.5, 3.0])


if __name__ == "__main__":
    test_pad_truncations()
    test_get_i()
    test_update_pattern_vl_order()
    # test_fill_onset_durs()
    # test_get_onset_and_dur()
    test_new_onsets()
    test_new_comma()
    test_new_iois()
    test_new_durs()
    # test_new_fit_rhythm_to_pattern()
    test_hocketing_indices()
    test_quasi_unison_constrained_indices()
    test_indices_handler()
    test_within_leader_durs()
    test_yield_onset_and_consecutive_release()
