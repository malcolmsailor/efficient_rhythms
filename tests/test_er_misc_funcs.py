import itertools
import os
import sys
import traceback

# INTERNET_TODO install hypothesis, uncomment
# import hypothesis
# import hypothesis.strategies as st

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

import src.er_misc_funcs as er_misc_funcs  # pylint: disable=wrong-import-position
import src.er_notes as er_notes  # pylint: disable=wrong-import-position
import src.er_preprocess as er_preprocess  # pylint: disable=wrong-import-position


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
        assert er_misc_funcs.check_interval_class(
            ic, given_pitch, other_pitches
        ), f"er_misc_funcs.check_interval_class({ic}, {given_pitch}, {other_pitches}) != True"
    for ic in (2, 3, 6, 9, 10, 0, 12):
        assert not er_misc_funcs.check_interval_class(
            ic, given_pitch, other_pitches
        ), f"er_misc_funcs.check_interval_class({ic}, {given_pitch}, {other_pitches}) != False"
    for ic in (5, 8, 4, 9, 11, 2):
        assert er_misc_funcs.check_interval_class(
            ic, given_pitch, other_pitches, tet=13
        ), f"er_misc_funcs.check_interval_class({ic}, {given_pitch}, {other_pitches}, tet=13) != True"
    for ic in (0, 1, 3, 6, 7, 10, 12, 13):
        assert not er_misc_funcs.check_interval_class(
            ic, given_pitch, other_pitches, tet=13
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
        for (v, p, a, d, l) in notes:  # pylint: disable=invalid-name
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


def test_empty_nested():
    tests = [
        ([(), ()], True),
        ([[], []], True),
        (["", ""], False),
        (((), ()), True),
        (([], [], [""]), False),
        ([1, 2, 3], False),
        ([[[[[4]]]]], False),
        ([], True),
    ]
    for seq, result in tests:
        try:
            assert (
                er_misc_funcs.empty_nested(seq) == result
            ), "er_misc_funcs.empty_nested(seq) != result"
        except:  # pylint: disable=bare-except
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(
                exc_type, exc_value, exc_traceback, file=sys.stdout
            )
            breakpoint()


def test_chord_in_list():
    # ########################
    # # octave_equi = "all", #
    # ########################
    chords = ((0, 4, 7), (0, 3, 7))
    in_list = [
        # close positions
        [60, 64, 67],
        [61, 64, 68],
        [62, 65, 70],
        [63, 67, 72],
        [64, 69, 73],
        [65, 70, 73],
        # open positions
        [60, 67, 76],
        [61, 68, 76],
        [62, 70, 77],
        [63, 72, 79],
        [64, 73, 81],
        [65, 73, 82],
        # doublings (not all combinations should pass with doublings == "complete")
        [60, 64, 67, 72],
        [61, 64, 68, 76],
        [62, 65, 70, 82],
    ]
    for item_i, item in enumerate(in_list):
        for r in range(1, 4):
            for combination in itertools.combinations(item, r):
                try:
                    try:
                        assert er_misc_funcs.chord_in_list(
                            combination,
                            chords,
                            octave_equi="all",
                            permit_doublings="complete",
                        ), (
                            "er_misc_funcs.chord_in_list(combination, chords, "
                            "octave_equi='all', permit_doublings='complete')"
                        )
                    except AssertionError:
                        assert item_i >= 10, "item_i < 10"
                        assert er_misc_funcs.chord_in_list(
                            combination,
                            chords,
                            octave_equi="all",
                            permit_doublings="all",
                        ), (
                            "er_misc_funcs.chord_in_list(combination, "
                            "chords, octave_equi='all', permit_doublings='all')"
                        )
                except:  # pylint: disable=bare-except
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    traceback.print_exception(
                        exc_type, exc_value, exc_traceback, file=sys.stdout
                    )
                    breakpoint()
    not_in_list = [
        # Intervals not present
        [60, 61],
        [70, 72],
        [50, 56],
        [40, 50],
        [80, 81],
        [60, 64, 68],
        [63, 66, 69],
    ]
    for item in not_in_list:
        try:
            assert not er_misc_funcs.chord_in_list(
                item, chords
            ), "er_misc_funcs.chord_in_list(item, chords) != False"
        except:  # pylint: disable=bare-except
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(
                exc_type, exc_value, exc_traceback, file=sys.stdout
            )
            breakpoint()
    doublings = [
        [60, 64, 67, 72],
        [61, 64, 68, 76],
        [62, 65, 70, 82],
    ]
    no_doublings = [
        [60, 64, 67],
        [61, 64, 68],
        [62, 65, 70],
    ]
    for doubling, no_doubling in zip(doublings, no_doublings):
        try:
            assert not er_misc_funcs.chord_in_list(
                doubling, chords, octave_equi="all", permit_doublings="none",
            ), (
                "not er_misc_funcs.chord_in_list(doubling, chords, "
                "octave_equi='all', permit_doublings='none')"
            )
            assert er_misc_funcs.chord_in_list(
                no_doubling, chords, octave_equi="all", permit_doublings="none",
            ), (
                "er_misc_funcs.chord_in_list(no_doubling, chords, "
                "octave_equi='all', permit_doublings='none')"
            )
        except:  # pylint: disable=bare-except
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(
                exc_type, exc_value, exc_traceback, file=sys.stdout
            )
            breakpoint()
    #########################
    # octave_equi = "bass", #
    #########################
    # chords = [[0, 4, 7, 10]]
    # in_list = [
    #     # close positions
    #     [60, 64, 67, 70],
    #     [61, 65, 68, 71],
    #     # open positions
    #     [60, 67, 70, 76],
    #     [60, 64, 70, 79],
    #     [49, 65, 68, 71],
    #     [61, 65, 68, 83],
    #     # doublings (not all combinations should pass with doublings == "complete")
    #     [60, 64, 67, 70, 72],
    #     [60, 64, 67, 70, 76],
    #     [61, 65, 68, 71, 80],
    #     [61, 65, 68, 71, 83],
    # ]
    # for item_i, item in enumerate(in_list):
    #     for r in range(2, 4):
    #         for combination in itertools.combinations(item, r):
    #             try:
    #                 if combination[0] == item[0]:
    #                     try:
    #                         assert er_misc_funcs.chord_in_list(
    #                             combination,
    #                             chords,
    #                             octave_equi="bass",
    #                             permit_doublings="complete",
    #                         ), (
    #                             "er_misc_funcs.chord_in_list(combination, "
    #                             "chords, octave_equi='bass', "
    #                             "permit_doublings='complete')"
    #                         )
    #                     except AssertionError:
    #                         # should only fail with doublings after index 5
    #                         assert item_i >= 6, "item_i < 6"
    #                         assert er_misc_funcs.chord_in_list(
    #                             combination,
    #                             chords,
    #                             octave_equi="bass",
    #                             permit_doublings="all",
    #                         ), (
    #                             "er_misc_funcs.chord_in_list(combination, "
    #                             "chords, octave_equi='bass', "
    #                             "permit_doublings='all')"
    #                         )
    #                 else:
    #                     assert not er_misc_funcs.chord_in_list(
    #                         combination,
    #                         chords,
    #                         octave_equi="bass",
    #                         permit_doublings="complete",
    #                     ), (
    #                         "not er_misc_funcs.chord_in_list(combination, "
    #                         "chords, octave_equi='bass', "
    #                         "permit_doublings='complete')"
    #                     )
    #
    #             except:  # pylint: disable=bare-except
    #                 exc_type, exc_value, exc_traceback = sys.exc_info()
    #                 traceback.print_exception(
    #                     exc_type, exc_value, exc_traceback, file=sys.stdout
    #                 )
    #                 breakpoint()

    #########################
    # octave_equi = "order" #
    #########################
    chords = [
        [0, 4, 7, 10],
    ]
    in_list = [
        # close positions
        [60, 64, 67, 70],
        [61, 65, 68, 71],
    ]
    for item in in_list:
        for r in range(2, 4):
            for combination in itertools.combinations(item, r):
                try:
                    if list(combination) == item[:r]:
                        assert er_misc_funcs.chord_in_list(
                            combination,
                            chords,
                            octave_equi="order",
                            permit_doublings="complete",
                        ), (
                            "er_misc_funcs.chord_in_list(combination, "
                            "chords, octave_equi='order', "
                            "permit_doublings='complete')"
                        )
                    else:
                        assert not er_misc_funcs.chord_in_list(
                            combination,
                            chords,
                            octave_equi="order",
                            permit_doublings="complete",
                        ), (
                            "not er_misc_funcs.chord_in_list(combination, "
                            "chords, octave_equi='order', "
                            "permit_doublings='complete')"
                        )
                except:  # pylint: disable=bare-except
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    traceback.print_exception(
                        exc_type, exc_value, exc_traceback, file=sys.stdout
                    )
                    breakpoint()

    def _sub_test(octave_equi, tests):
        for test_chord, all_val, comp_val, none_val in tests:
            try:
                assert (
                    er_misc_funcs.chord_in_list(
                        test_chord,
                        chords,
                        octave_equi=octave_equi,
                        permit_doublings="all",
                    )
                    == all_val
                ), (
                    "er_misc_funcs.chord_in_list(test_chord, chords, "
                    f'octave_equi="{octave_equi}", '
                    'permit_doublings="all") != all_val'
                )
                assert (
                    er_misc_funcs.chord_in_list(
                        test_chord,
                        chords,
                        octave_equi=octave_equi,
                        permit_doublings="complete",
                    )
                    == comp_val
                ), (
                    "er_misc_funcs.chord_in_list(test_chord, chords, "
                    f'octave_equi="{octave_equi}", '
                    'permit_doublings="complete") != comp_val'
                )
                assert (
                    er_misc_funcs.chord_in_list(
                        test_chord,
                        chords,
                        octave_equi=octave_equi,
                        permit_doublings="none",
                    )
                    == none_val
                ), (
                    "er_misc_funcs.chord_in_list(test_chord, chords, "
                    f'octave_equi="{octave_equi}", '
                    'permit_doublings="none") != none_val'
                )
            except:  # pylint: disable=bare-except
                exc_type, exc_value, exc_traceback = sys.exc_info()
                traceback.print_exception(
                    exc_type, exc_value, exc_traceback, file=sys.stdout
                )
                breakpoint()

    # permit_doublings with octave_equi = "order"
    chords = [
        [0, 4, 7, 10],
    ]
    # test_chord, all_val, comp_val, none_val
    tests = [
        ([48, 60, 64, 67, 70], True, False, False,),
        ([60, 64, 67, 70, 82], True, True, False,),
        ([60, 64, 67, 70, 72], False, False, False,),
        ([48, 60, 64, 76, 88], True, False, False,),
        ([48, 52, 55], True, True, True),
        ([48, 64, 79, 94], True, True, True),
    ]
    _sub_test("order", tests)

    # permit_doublings with octave_equi = "none"
    chords = [
        [0, 4, 7, 10],
    ]
    # test_chord, all_val, comp_val, none_val
    tests = [
        ([48, 48, 52, 55, 58], True, False, False),
        ([48, 60, 64, 67, 70], False, False, False,),
        ([48, 52, 55, 58, 58, 58], True, True, False),
        ([60, 64, 67, 70], True, True, True),
        ([60, 64, 64, 67, 67], True, False, False),
        ([72, 76], True, True, True),
    ]
    _sub_test("none", tests)

    # permit_doublings with octave_equi = "bass"
    chords = [
        [0, 4, 7, 10],
    ]
    # test_chord, all_val, comp_val, none_val
    tests = [
        ([36, 48, 55], True, False, False),
        ([48, 55, 70, 72, 76], True, True, False),
        ([48, 55, 70, 76, 76, 79, 84], True, True, False),
        ([48, 55, 70], True, True, True),
        ([64, 67, 70, 72], False, False, False),
    ]
    _sub_test("bass", tests)


# INTERNET_TODO install hypothesis, uncomment
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
    test_empty_nested()
    test_chord_in_list()
