import warnings

import numpy as np

from efficient_rhythms import er_settings
from efficient_rhythms import er_rhythm

from tests.fixtures import set_seed  # pylint: disable=unused-import


def _get_cont_base(
    rhythm_len=8.0,
    num_notes=16,
    min_dur=0.25,
    increment=0.1,
    overlap=True,
    num_vars=8,
    vary_consistently=True,
    var_palindrome=True,
    dtype=np.float64,
    cls=er_rhythm.cont_rhythm.ContRhythmBase,
):
    return cls(
        rhythm_len,
        min_dur,
        num_notes,
        increment,
        overlap,
        num_vars,
        vary_consistently,
        var_palindrome,
        dtype,
    )


def _get_cont_rhythm(
    dur_density=0.5,
    rhythm_len=8.0,
    num_notes=8,
    min_dur=0.25,
    increment=0.1,
    overlap=True,
    num_vars=8,
    vary_consistently=True,
    var_palindrome=True,
    dtype=np.float64,
    cls=er_rhythm.cont_rhythm.ContRhythm,
):
    return cls(
        dur_density,
        rhythm_len,
        min_dur,
        num_notes,
        increment,
        overlap,
        num_vars,
        vary_consistently,
        var_palindrome,
        dtype,
    )


def _get_grid(*args, **kwargs):
    return _get_cont_rhythm(*args, cls=er_rhythm.grid.Grid, **kwargs)


def _get_er(settingsdict):
    return er_settings.get_settings(settingsdict, silent=True)


def _get_grid_from_er(settingsdict):
    er = _get_er(settingsdict)
    gd = er.grid = er_rhythm.grid.Grid.from_er_settings(er)
    return er, gd


# @dataclasses.dataclass
# class DummyRhythm:
#     num_notes: int = 16
#     rhythm_len: float = 8.0
#     min_dur: float = 1 / 4
#     increment: float = 0.1
#     overlap: bool = True


def _verify_onsets(
    onsets,
    num_notes,
    rhythm_len,
    min_dur,
    starts_at_zero=True,
    start_offset=0,
    error_tolerance=1e-8,
):
    assert len(onsets) == num_notes
    assert onsets[-1] <= start_offset + rhythm_len - min_dur
    if starts_at_zero:
        assert onsets[0] == start_offset
    for x, y in zip(onsets, onsets[1:]):
        assert y - x >= min_dur - error_tolerance


def test_get_continuous_onsets(
    set_seed,
):  # pylint: disable=unused-argument, redefined-outer-name

    # TODO add more test cases, check that min_dur is reduced if necessary
    tests = (
        (16, 8.0, 0.25),
        (16, 4.0, 0.25),
        (15, 4.0, 0.25000001),
    )
    non_defaults = (
        ("increment", 0.0),
        ("increment", 1.0),
        ("increment", 100.0),
        ("num_vars", 1),
        ("overlap", False),
        ("vary_consistently", False),
        ("var_palindrome", False),
    )
    for kw, val in non_defaults:
        for num_notes, rhythm_len, min_dur in tests:
            kwargs = {
                kw: val,
                "num_notes": num_notes,
                "rhythm_len": rhythm_len,
                "min_dur": min_dur,
            }
            cr = _get_cont_base(**kwargs)
            cr._init_onsets()
            onsets = cr._onsets_2d[0]
            _verify_onsets(onsets, cr.num_notes, cr.rhythm_len, cr.min_dur)

            # test _vary_onsets_unif()
            if cr.full:
                continue
            for i in range(1, cr.num_vars):
                cr._vary_onsets_unif(i)
                new_onsets = cr._onsets_2d[i]
                _verify_onsets(
                    new_onsets, cr.num_notes, cr.rhythm_len, cr.min_dur
                )
                try:
                    assert not np.all(np.equal(onsets, new_onsets))
                except AssertionError:
                    assert cr.full
                # TODO ensure that total absolute change equals increment
                # print(cr.increment)
                # print(np.abs(onsets - new_onsets).sum())
                onsets = new_onsets


def _verify_durs(
    onsets,
    durs,
    dur_density,
    min_dur,
    rhythm_len,
    num_vars,
    overlap,
    error_tolerance=0.2,  # TODO this seems way too high!
):
    min_density = min_dur / rhythm_len * len(onsets)
    iois = er_rhythm.utils.get_iois(onsets, rhythm_len * num_vars, overlap)
    assert np.all(durs - iois < 1e-7)
    if min_density >= dur_density:
        target_density = min_density
    else:
        target_density = dur_density
    actual_density = durs.sum() / rhythm_len
    # pretty sure we need to increase error tolerance for Grid
    if error_tolerance > 0.05:
        warnings.warn(
            "error tolerance is quite high, this needs to be debugged"
        )
    assert abs(target_density - actual_density) < error_tolerance
    # assert abs(durs.sum() - cr.rhythm_len * target_density) < 0.1
    assert np.all(durs >= min_dur)
    assert np.all(durs <= rhythm_len)


def test_fill_durs(
    set_seed,
):  # pylint: disable=unused-argument, redefined-outer-name
    densities = [0.625, 0.8, 0.5, 0.1, 0.4, 0.99, 1.0]
    non_defaults = (
        ("increment", 0.0),
        ("increment", 1.0),
        ("increment", 100.0),
        ("num_vars", 1),
        ("overlap", False),
        ("vary_consistently", False),
        ("var_palindrome", False),
    )
    for kw, val in non_defaults:
        for density in densities:
            kwargs = {kw: val, "dur_density": density}
            cr = _get_cont_rhythm(**kwargs)
            cr.generate()
            for i in range(cr.num_vars):
                float_durs = cr._durs_2d[i]
                _verify_durs(
                    cr._onsets_2d[i],
                    float_durs,
                    cr.dur_density,
                    cr.min_dur,
                    cr.rhythm_len,
                    1,
                    cr.overlap,
                )


def test_palindrome(
    set_seed,
):  # pylint: disable=unused-argument, redefined-outer-name
    num_vars = (1, 2, 5, 10, 17, 40)
    for n in num_vars:
        cr = _get_cont_rhythm(var_palindrome=True, num_vars=n)
        cr.generate()
        for i in range(n):
            j = cr._get_palindromic_index(i)
            if j is None:
                continue

            assert np.all(
                np.abs(
                    cr._onsets_2d[i]
                    + (j - i) * cr.rhythm_len
                    - cr._onsets_2d[j]
                )
                < 1e-10
            )
            assert np.all(cr._durs_2d[i] == cr._durs_2d[j])


def test_grid(
    set_seed,
):  # pylint: disable=unused-argument, redefined-outer-name
    def test_get_max_releases(gd, onset_indices, overlap):
        onsets = gd.onset_positions[indices]
        max_releases = gd._get_max_releases(onset_indices)
        assert np.all(max_releases[:-1] - onsets[1:] < 1e-7)
        releases = gd.releases
        for i in range(len(onsets) - 1):
            next_onset = onsets[i + 1]
            earlier_releases = releases - next_onset < 1e-7
            max_r = np.max(releases[earlier_releases])
            assert abs(max_releases[i] - max_r) < 1e-7

        # test last release separately:
        if not overlap:
            assert abs(max_releases[-1] - gd.rhythm_len) < 1e-10
        else:
            next_onset_i = onset_indices[0] + gd.num_notes
            if next_onset_i >= len(gd.onset_positions):
                next_onset_i %= len(gd.onset_positions)
                offset = gd.total_dur
            else:
                offset = 0
            next_onset = (gd.onset_positions[next_onset_i] + offset).round(8)
            assert abs(max_releases[-1] - next_onset) < 1e-7

    basesettings = {
        "num_voices": 3,
        "min_dur": 0.05,
        "num_cont_rhythm_vars": -1,
        "rhythm_len": 2,
    }
    non_defaults = (
        ("cont_var_increment", 0.0),
        ("overlap", False),
        ("cont_var_increment", 0.1),
        ("cont_var_increment", 100.0),
        ("num_cont_rhythm_vars", 1),
        ("vary_rhythm_consistently", False),
        ("cont_var_palindrome", False),
    )
    for kw, val in non_defaults:
        settingsdict = basesettings.copy()
        settingsdict[kw] = val
        print(settingsdict)
        er, gd = _get_grid_from_er(settingsdict)
        gd.generate()
        div3 = gd.num_notes // 3
        for j in range(div3):
            indices = [j, j + div3, j + div3 * 2]
            test_get_max_releases(gd, indices, er.overlap)
            onsets = gd.onset_positions[indices]
            voice_i = 0
            durs = gd.get_durs(er, voice_i, onsets, ())
            varied_onsets, varied_durs = gd.vary(onsets, durs)
            varied_onsets = varied_onsets.reshape((gd.num_vars, len(onsets)))
            varied_durs = varied_durs.reshape((gd.num_vars, len(onsets)))
            for i in range(gd.num_vars):
                assert np.all(
                    np.equal(varied_onsets[i], gd._onsets_2d[i][indices])
                )
                varied_releases = (varied_onsets[i] + varied_durs[i]).round(
                    decimals=8
                )
                varied_releases = np.where(
                    varied_releases > gd.total_dur,
                    (varied_releases % gd.total_dur).round(decimals=8),
                    varied_releases,
                )
                assert np.all(np.isin(varied_releases, gd.releases))
                _verify_onsets(
                    varied_onsets[i],
                    3,
                    er.rhythm_len[voice_i],
                    er.min_dur[voice_i],
                    starts_at_zero=False,
                    start_offset=i * er.rhythm_len[voice_i],
                )
                _verify_durs(
                    varied_onsets[i],
                    varied_durs[i],
                    er.dur_density[voice_i],
                    er.min_dur[voice_i],
                    er.rhythm_len[voice_i],
                    er.num_cont_rhythm_vars[voice_i],
                    er.overlap,
                    error_tolerance=0.5,
                )


def test_get_onsets_from_grid(
    set_seed,
):  # pylint: disable=unused-argument, redefined-outer-name
    basesettings = {
        "num_voices": 3,
        "min_dur": 0.05,
        "num_cont_rhythm_vars": -1,
        "rhythm_len": 2,
        "pattern_len": 2,
        "cont_rhythms": "grid",
    }
    non_defaults = (
        ("cont_var_increment", 0.0),
        ("overlap", False),
        ("cont_var_increment", 1.0),
        ("cont_var_increment", 100.0),
        ("num_cont_rhythm_vars", 1),
        ("vary_rhythm_consistently", False),
        ("cont_var_palindrome", False),
    )
    for kw, val in non_defaults:
        settingsdict = basesettings.copy()
        settingsdict[kw] = val
        er, gd = _get_grid_from_er(settingsdict)
        gd.generate()
        er_rhythm.make.get_onsets(er, 0, None)
