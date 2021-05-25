from fractions import Fraction
import os
import sys
import traceback

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

import src.er_preprocess as er_preprocess  # pylint: disable=wrong-import-position
import src.er_rhythm as er_rhythm  # pylint: disable=wrong-import-position


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
            er = er_preprocess.preprocess_settings(settingsdict)
            er.rhythms = er_rhythm.rhythms_handler(er)
            voice_is = {}
            for item in er.pattern_vl_order:
                voice_i = item.voice_i
                pattern_len = pattern_lens[voice_i]
                if truncate:
                    truncate_len = max(pattern_lens)
                    truncate_start = truncate_len // pattern_len * pattern_len
                if voice_i in voice_is:
                    assert (
                        item.start_i == voice_is[voice_i]
                    ), "item.start_i != voice_is[voice_i]"
                try:
                    assert item.end_i - item.start_i == len(
                        er.rhythms[voice_i]
                    ), (
                        "item.end_i - item.start_i "
                        "!= len(er.rhythms[voice_i])"
                    )
                except AssertionError:
                    # we should only get an AssertionError if truncate_len is
                    # defined
                    try:
                        assert (
                            item.start_time >= truncate_len
                            or item.start_time % truncate_len == truncate_start
                        ), (
                            "item.start_time < truncate_len and item.start_time % "
                            "truncate_len != truncate_start"
                        )
                    except:  # pylint: disable=bare-except
                        exc_type, exc_value, exc_traceback = sys.exc_info()
                        traceback.print_exception(
                            exc_type, exc_value, exc_traceback, file=sys.stdout
                        )
                        breakpoint()

                voice_is[voice_i] = item.end_i


def test_fill_onset_durs():
    densities = tuple(i / 10 for i in range(1, 10))
    rhythm_lens = (i / 2 for i in range(1, 13))
    min_dur = 1 / 4
    for density in densities:
        for rhythm_len in rhythm_lens:
            settingsdict = {
                "onset_density": density,
                "dur_density": density,
                "min_dur": min_dur,
                "num_voices": 1,
                "rhythm_len": rhythm_len,
                "pattern_len": rhythm_len,  # ensure we don't truncate rhythm
            }
            er = er_preprocess.preprocess_settings(settingsdict)
            rhythm = er_rhythm.rhythms_handler(er)[0]
            try:
                assert all(
                    val == min_dur for val in rhythm.values()
                ), "all(val == min_dur for val in rhythm.values())"
            except:  # pylint: disable=bare-except
                exc_type, exc_value, exc_traceback = sys.exc_info()
                traceback.print_exception(
                    exc_type, exc_value, exc_traceback, file=sys.stdout
                )
                breakpoint()


def test_get_onset_and_dur():
    pattern_lens_list = [(2.5, 3, 3.5, 4), (2, 3, 5)]
    for pattern_lens in pattern_lens_list:
        for truncate in (True, False):
            settingsdict = {
                "num_voices": len(pattern_lens),
                "tet": 12,
                "pattern_len": pattern_lens,
                "truncate_patterns": truncate,
            }
            er = er_preprocess.preprocess_settings(settingsdict)
            er.rhythms = er_rhythm.rhythms_handler(er)
            for rhythm in er.rhythms:
                prev_onset = -10
                for i in range(1000):
                    onset, _ = rhythm.get_onset_and_dur(i)
                    try:
                        assert onset > prev_onset, "onset <= prev_onset"
                    except:  # pylint: disable=bare-except
                        exc_type, exc_value, exc_traceback = sys.exc_info()
                        traceback.print_exception(
                            exc_type, exc_value, exc_traceback, file=sys.stdout
                        )
                        breakpoint()

                    prev_onset = onset
    obligatory_onsets = [0, 0.75, 1.5]
    obligatory_onsets_modulo = 2
    settingsdict = {
        "num_voices": 1,
        "pattern_len": 4,
        "obligatory_onsets": obligatory_onsets,
        "obligatory_onsets_modulo": obligatory_onsets_modulo,
        "onset_density": 1,
    }
    er = er_preprocess.preprocess_settings(settingsdict)
    rhythm = er_rhythm.rhythms_handler(er)[0]
    for i in range(100):
        try:
            assert (
                rhythm.get_onset_and_dur(i)[0] % obligatory_onsets_modulo
                == obligatory_onsets[i % len(obligatory_onsets)]
            ), (
                f"rhythm.get_onset_and_dur({i})[0] % "
                "obligatory_onsets_modulo "
                f"!= obligatory_onsets[{i} % len(obligatory_onsets)]"
            )
        except:  # pylint: disable=bare-except
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(
                exc_type, exc_value, exc_traceback, file=sys.stdout
            )
            breakpoint()


def test_get_i():
    # settingsdict = {
    #     "num_voices": 2,
    #     "onset_density": 0.5,
    #     "rhythm_len": [1.5, 7],
    #     "pattern_len": [4, 7],
    # }
    # er = er_preprocess.preprocess_settings(settingsdict)
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
    er = er_preprocess.preprocess_settings(settingsdict)
    rhythm = er_rhythm.Rhythm(er, voice_i=0)
    rhythm.data = onsets_and_durs
    try:
        for i in range(25):
            time = i / 4
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
    except:  # pylint: disable=bare-except

        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(
            exc_type, exc_value, exc_traceback, file=sys.stdout
        )
        breakpoint()


if __name__ == "__main__":
    test_get_i()
    test_update_pattern_vl_order()
    test_fill_onset_durs()
    test_get_onset_and_dur()
