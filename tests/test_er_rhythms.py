import os
import sys
import traceback

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

import src.er_preprocess as er_preprocess  # pylint: disable=wrong-import-position
import src.er_rhythm as er_rhythm  # pylint: disable=wrong-import-position


def test_update_pattern_voice_leading_order():
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
            for item in er.pattern_voice_leading_order:
                voice_i = item.voice_i
                pattern_len = pattern_lens[voice_i]
                if truncate:
                    truncate_len = max(pattern_lens)
                    truncate_start = truncate_len // pattern_len * pattern_len
                if voice_i in voice_is:
                    assert (
                        item.start_rhythm_i == voice_is[voice_i]
                    ), "item.start_rhythm_i != voice_is[voice_i]"
                try:
                    assert item.end_rhythm_i - item.start_rhythm_i == len(
                        er.rhythms[voice_i]
                    ), (
                        "item.end_rhythm_i - item.start_rhythm_i "
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

                voice_is[voice_i] = item.end_rhythm_i


def test_fill_attack_durs():
    densities = tuple(i / 10 for i in range(1, 10))
    rhythm_lens = (i / 2 for i in range(1, 13))
    min_dur = 1 / 4
    for density in densities:
        for rhythm_len in rhythm_lens:
            settingsdict = {
                "attack_density": density,
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


def test_get_attack_time_and_dur():
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
                prev_attack = -10
                for i in range(1000):
                    attack, _ = rhythm.get_attack_time_and_dur(i)
                    try:
                        assert attack > prev_attack, "attack <= prev_attack"
                    except:  # pylint: disable=bare-except
                        exc_type, exc_value, exc_traceback = sys.exc_info()
                        traceback.print_exception(
                            exc_type, exc_value, exc_traceback, file=sys.stdout
                        )
                        breakpoint()

                    prev_attack = attack


if __name__ == "__main__":
    test_update_pattern_voice_leading_order()
    test_fill_attack_durs()
    test_get_attack_time_and_dur()
