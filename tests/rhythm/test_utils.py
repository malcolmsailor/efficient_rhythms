from efficient_rhythms.er_rhythm import utils


def test_loop_seq():
    tests = [
        ((1, 3), 5, (1, 3, 6, 8, 11, 13, 16)),
        ((0.1, 0.2), 0.5, (0.1, 0.2, 0.6, 0.7, 1.1)),
    ]
    for seq, loop_len, result in tests:
        ls = utils.LoopSeq(seq, loop_len)
        for i, item in enumerate(result):
            assert next(ls) == item
            assert ls[i] == item


def test_get_indices_from_sorted():
    tests = [
        ((0, 4), (0, 1, 2, 3, 4, 5), (0, 4), None),
        ((2.7, 1.23), (0.14, 1.23, 2.4, 2.7), (3, 1), None),
        ((2, 1, 7), (0, 1, 4, 7), (1, 3), 10),
        ((0, 4, 6), (0, 1, 2, 3, 4, 5), (0, 4), None),
        ((0, 4, 6), (0, 1, 2, 3, 4, 5), (0, 4, 6), 6),
        ((0, 4, 10), (0, 1, 2, 3, 4, 5), (0, 4, 10), 6),
        ((2.7, 1.23, 3.14), (0.14, 1.23, 2.4, 2.7), (3, 1, 4), 3),
    ]
    for elements, sorted_seq, result, loop_len in tests:
        assert utils.get_indices_from_sorted(
            elements, sorted_seq, loop_len=loop_len
        ) == list(result)
