import numpy as np

import pytest

import efficient_rhythms.er_preprocess as er_preprocess
import efficient_rhythms.er_rhythm as er_rhythm
import efficient_rhythms.er_misc_funcs as er_misc_funcs

er_misc_funcs.set_seed(0)


def _get_cont_base(
    rhythm_len=8.0,
    num_notes=16,
    min_dur=0.25,
    increment=0.1,
    overlap=True,
    num_vars=8,
    vary_consistently=True,
    dtype=np.float64,
):
    return er_rhythm.cont_rhythm.ContRhythmBase2(
        rhythm_len,
        min_dur,
        num_notes,
        increment,
        overlap,
        num_vars,
        vary_consistently,
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
    dtype=np.float64,
):
    return er_rhythm.cont_rhythm.ContRhythm2(
        dur_density,
        rhythm_len,
        min_dur,
        num_notes,
        increment,
        overlap,
        num_vars,
        vary_consistently,
        dtype,
    )


def _get_er(settingsdict):
    return er_preprocess.preprocess_settings(settingsdict, silent=True)


# @dataclasses.dataclass
# class DummyRhythm:
#     num_notes: int = 16
#     rhythm_len: float = 8.0
#     min_dur: float = 1 / 4
#     increment: float = 0.1
#     overlap: bool = True


def test_get_continuous_onsets():
    def _verify_onsets(onsets, r):
        assert len(onsets) == r.num_notes
        assert onsets[-1] <= r.rhythm_len - r.min_dur
        assert onsets[0] == 0
        for x, y in zip(onsets, onsets[1:]):
            assert y - x >= r.min_dur - 1e-8

    # TODO add more test cases, check that min_dur is reduced if necessary
    tests = (
        (16, 8.0, 0.25),
        (16, 4.0, 0.25),
        (15, 4.0, 0.25000001),
    )
    num_vars = 8
    for num_notes, rhythm_len, min_dur in tests:
        for vary_consistently in (True, False):
            r = _get_cont_base(
                rhythm_len,
                num_notes,
                min_dur,
                num_vars=num_vars,
                vary_consistently=vary_consistently,
            )
            r._init_onsets()
            onsets = r._onsets[0]
            _verify_onsets(onsets, r)

            # test _vary_onsets_unif()
            if r.full:
                continue
            for i in range(1, num_vars):
                r._vary_onsets_unif(i)
                new_onsets = r._onsets[i]
                _verify_onsets(new_onsets, r)
                try:
                    assert not np.all(np.equal(onsets, new_onsets))
                except AssertionError:
                    assert r.full
                # TODO ensure that total absolute change equals increment
                # print(np.abs(onsets - new_onsets).sum())
                onsets = new_onsets


def test_fill_durs():
    def _verify_durs(onsets, durs, cr):
        min_density = cr.min_dur / cr.rhythm_len * len(onsets)
        iois = er_rhythm.utils.get_iois(onsets, cr.rhythm_len, cr.overlap)
        assert np.all(np.less_equal(durs, iois))
        if min_density >= cr.dur_density:
            target_density = min_density
        else:
            target_density = cr.dur_density
        assert abs(durs.sum() - cr.rhythm_len * target_density) < 0.1
        assert np.all(durs >= cr.min_dur)

    densities = [0.625, 0.8, 0.5, 0.1, 0.4, 0.99, 1.0]
    for density in densities:
        print("DENSITY: ", density)
        cr = _get_cont_rhythm(dur_density=density)
        cr.generate()
        # float_durs = cr.fill_durs(cr.onsets[0])
        float_durs = cr.durs[0]
        _verify_durs(cr.onsets[0], float_durs, cr)
        # for i in range(10):
        #     print("I: ", i)
        #     float_durs = cr.fill_durs(cr.onsets[0])
        #     _verify_durs(cr.onsets[0], float_durs, cr)


def test_grid():
    num_vars = 8
    settings_dict = {
        "cont_rhythms": "grid",
        "num_cont_rhythm_vars": num_vars,
        "pattern_len": 2,
        "onset_subdivision": 0.25,
        "min_dur": 0.125,
    }
    er = _get_er(settings_dict)
    g = er_rhythm.grid.Grid2.from_er_settings(er)
    # len of g._onsets[0] should be 8
    indices = [1, 3, 6]
    onsets = g.onset_positions[indices]
    varied_onsets = g.vary_rhythm(onsets, None)
    for i in range(num_vars):
        assert np.all(np.equal(varied_onsets[i], g._onsets[i][indices]))
