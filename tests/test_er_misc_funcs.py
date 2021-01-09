import os
import sys
import traceback

# TODO install hypothesis, uncomment
# import hypothesis
# import hypothesis.strategies as st

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

import er_misc_funcs
import er_notes
import er_preprocess


def test_check_modulo():
    assert (
        er_misc_funcs.check_modulo(3, 2) == 1
    ), "er_misc_funcs.check_modulo(3, 2) != 1"
    assert (
        er_misc_funcs.check_modulo(10, [2, 5]) == 0
    ), "er_misc_funcs.check_modulo(10, [2, 5]) != 0"


def test_check_interval_class():
    given_pitch = 60
    other_pitches = [55, 64, 71]
    for ic in (5, 7, 4, 8, 11, 1):
        assert (
            er_misc_funcs.check_interval_class(ic, given_pitch, other_pitches)
            == True
        ), f"er_misc_funcs.check_interval_class({ic}, {given_pitch}, {other_pitches}) != True"
    for ic in (2, 3, 6, 9, 10, 0, 12):
        assert (
            er_misc_funcs.check_interval_class(ic, given_pitch, other_pitches)
            == False
        ), f"er_misc_funcs.check_interval_class({ic}, {given_pitch}, {other_pitches}) != False"
    for ic in (5, 8, 4, 9, 11, 2):
        assert (
            er_misc_funcs.check_interval_class(
                ic, given_pitch, other_pitches, tet=13
            )
            == True
        ), f"er_misc_funcs.check_interval_class({ic}, {given_pitch}, {other_pitches}, tet=13) != True"
    for ic in (0, 1, 3, 6, 7, 10, 12, 13):
        assert (
            er_misc_funcs.check_interval_class(
                ic, given_pitch, other_pitches, tet=13
            )
            == False
        ), f"er_misc_funcs.check_interval_class({ic}, {given_pitch}, {other_pitches}, tet=13) != False"


def test_get_prev_voice_indices():
    settingsdict = {"num_voices": 2, "tet": 12}
    er = er_preprocess.preprocess_settings(settingsdict)

    # voice, pitch, attack, dur, evaluates_to
    notes1 = [
        (0, 60, 1.5, 0.5, []),
        (1, 64, 1.75, 0.25, [0]),
        (0, 64, 2, 0.25, []),
        (1, 64, 2, 0.5, [0]),
    ]
    notes2 = [
        (1, 64, 1.75, 0.25, []),
        (0, 60, 1.5, 0.5, [1]),
        (1, 64, 2, 0.5, []),
        (0, 64, 2, 0.25, [1]),
    ]
    for notes in (notes1, notes2):
        score = er_notes.Score(num_voices=er.num_voices, tet=er.tet)
        for (v, p, a, d, l) in notes:
            try:
                assert (
                    er_misc_funcs.get_prev_voice_indices(score, a, d) == l
                ), "er_misc_funcs.get_prev_voice_indices(score, a, d) != l"
            except:  # pylint: disable=bare-except
                exc_type, exc_value, exc_traceback = sys.exc_info()
                traceback.print_exception(
                    exc_type, exc_value, exc_traceback, file=sys.stdout
                )
                breakpoint()

            score.add_note(v, p, a, d)


# TODO install hypothesis, uncomment
# @hypothesis.given(list_and_item(),)
# def test_binary_search(tup):
#     list_, item = tup
#     assert item == list_[mal_misc.binary_search(list_, item)]
#
#
# @hypothesis.given(list_and_missing_item(),)
# def test_binary_search_not_found(tup):
#     list_, item = tup
#     assert mal_misc.binary_search(list_, item) is None
#     assert mal_misc.binary_search(list_, item, not_found="none") is None
#     upper = list_[mal_misc.binary_search(list_, item, not_found="upper")]
#     lower = list_[mal_misc.binary_search(list_, item, not_found="lower")]
#     nearest = list_[mal_misc.binary_search(list_, item, not_found="nearest")]
#     assert upper >= lower
#     assert nearest == upper or nearest == lower
#     if upper != lower:
#         assert (nearest == upper) == (upper - item < item - lower)
#     force_upper_i = mal_misc.binary_search(list_, item, not_found="force_upper")
#     force_lower_i = mal_misc.binary_search(list_, item, not_found="force_lower")
#     if item > max(list_):
#         assert force_upper_i == len(list_)
#         assert list_[force_lower_i] == nearest
#     elif item < min(list_):
#         assert force_lower_i == -1
#         assert list_[force_upper_i] == nearest


if __name__ == "__main__":
    test_check_modulo()
    test_check_interval_class()
    test_get_prev_voice_indices()
