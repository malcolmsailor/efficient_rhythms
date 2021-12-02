import itertools

from efficient_rhythms import er_voice_leadings as er_vls
from efficient_rhythms import er_exceptions


def test_efficient_voice_leading():
    triads = [(0, 3, 7), (0, 4, 7), (0, 1, 2), (0, 4, 8), (0, 2, 6)]
    doubled_triads = [(0, 0, 3, 7), (0, 0, 4, 7)]
    tetrads = [(0, 2, 4, 6), (0, 1, 2, 3), (0, 3, 6, 10), (0, 4, 8, 11)]
    sextads = [(0, 2, 4, 6, 8, 10), (0, 3, 4, 7, 8, 11)]
    # The following slow the test *way* down
    # heptads = [(0, 2, 4, 5, 7, 9, 11), (0, 2, 3, 5, 7, 9, 11)]

    chord_pairs = (
        list(itertools.product(triads, repeat=2))
        + list(itertools.product(doubled_triads, repeat=2))
        + list(itertools.product(tetrads, repeat=2))
        # + list(itertools.product(heptads, repeat=2))
        + list(itertools.product(sextads, repeat=2))
    )

    for c1, c2 in chord_pairs:
        for i in range(12):
            c3 = [(p + i) % 12 for p in c2]
            displacement = -1
            while True:
                try:
                    out1, displacement1 = er_vls.efficient_voice_leading(
                        c1,
                        c3,
                        tet=12,
                        displacement_more_than=displacement,
                        exclude_motions=None,
                    )
                except er_exceptions.NoMoreVoiceLeadingsError:
                    break
                for vl in out1:
                    assert set((p + i) % 12 for (p, i) in zip(c1, vl)) == set(
                        c3
                    )
                assert displacement1 > displacement
                displacement = displacement1


if __name__ == "__main__":
    test_efficient_voice_leading()
