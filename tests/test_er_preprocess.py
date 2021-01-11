import os
import sys
import traceback

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

import er_preprocess  # pylint: disable=wrong-import-position


def test_process_pattern_voice_leading_order():
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
            for item in er.pattern_voice_leading_order:
                voice_i = item.voice_i
                pattern_len = pattern_lens[voice_i]
                modulo = max(pattern_lens) if truncate else pattern_len
                start_time = item.start_time
                while item.prev_item is not None:
                    item = item.prev_item
                    assert item.voice_i == voice_i, "item.voice_i != voice_i"
                    try:
                        try:
                            assert (
                                item.start_time % modulo == start_time % modulo
                            ), "item.start_time % modulo != start_time % modulo"
                        except AssertionError:
                            assert (
                                item.start_time < modulo
                            ), "item.start_time >= modulo"
                    except:  # pylint: disable=bare-except
                        exc_type, exc_value, exc_traceback = sys.exc_info()
                        traceback.print_exception(
                            exc_type, exc_value, exc_traceback, file=sys.stdout
                        )
                        breakpoint()

                assert item.start_time == 0, "item.start_time != 0"


if __name__ == "__main__":
    test_process_pattern_voice_leading_order()
