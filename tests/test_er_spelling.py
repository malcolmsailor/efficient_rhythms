import efficient_rhythms.er_spelling as er_spelling


def test_build_spelling_dict():
    for tet in (12, 19, 31):
        spell_dict = er_spelling.build_spelling_dict(tet)
        spell_dict2 = er_spelling.build_spelling_dict(tet, forward=False)
        for pc, spelled in spell_dict.items():
            assert spell_dict2[spelled] == pc, "spell_dict2[spelled] != pc"
    spell_dict = er_spelling.build_spelling_dict(12)
    kern_dict = er_spelling.build_spelling_dict(12, letter_format="kern")
    tests = [
        (0, "C", "c"),
        (5, "F", "f"),
        (3, "Eb", "e-"),
        (1, "C#", "c#"),
    ]
    for pc, shell_spelled, kern_spelled in tests:
        assert (
            spell_dict[pc] == shell_spelled
        ), "spell_dict[pc] != shell_spelled"
        assert kern_dict[pc] == kern_spelled, "kern_dict[pc] != kern_spelled"


def test_build_fifth_class_spelling_dict():
    spell_dict = er_spelling.build_fifth_class_spelling_dict()
    spell_dict2 = er_spelling.build_fifth_class_spelling_dict(forward=False)
    kern_dict = er_spelling.build_fifth_class_spelling_dict(
        letter_format="kern"
    )
    for pc, spelled in spell_dict.items():
        assert spell_dict2[spelled] == pc, "spell_dict2[spelled] != pc"
    tests = [
        (0, "D", "d"),
        (7, "D#", "d#"),
        (-7, "Db", "d-"),
        (3, "B", "b"),
        (17, "B##", "b##"),
        (-11, "Bbb", "b--"),
    ]
    for pc, shell_spelled, kern_spelled in tests:
        assert (
            spell_dict[pc] == shell_spelled
        ), "spell_dict[pc] != shell_spelled"
        assert kern_dict[pc] == kern_spelled, "kern_dict[pc] != kern_spelled"


def test_speller():
    speller = er_spelling.Speller(pitches=True)
    assert speller(60) == "C4", "speller(60) " '!= "C4"'


def test_group_speller():
    tests = [
        (),
        (2,),
        (3,),
        (1,),
        (1, 4, 9),
        (0, 3, 8),
        (1, 3, 4, 6, 8, 9, 11),
        (0, 1, 3, 5, 6, 8, 10),
        (0, 2, 3, 5, 7, 9, 11),
        (0, 1, 3, 4, 6, 8, 10),
        (0, 2, 3, 5, 6, 8, 10),
        (1, 9, 4, 1, 4, 9, 4, 9, 1),
    ]
    results = [
        [],
        ["D"],
        ["Eb"],
        ["C#"],
        ["C#", "E", "A"],
        ["C", "Eb", "Ab"],
        ["C#", "D#", "E", "F#", "G#", "A", "B"],
        ["C", "Db", "Eb", "F", "Gb", "Ab", "Bb"],
        ["C", "D", "Eb", "F", "G", "A", "B"],
        ["B#", "C#", "D#", "E", "F#", "G#", "A#"],
        ["C", "D", "Eb", "F", "Gb", "Ab", "Bb"],
        ["C#", "A", "E", "C#", "E", "A", "E", "A", "C#"],
    ]
    group_speller = er_spelling.GroupSpeller()
    for test, result in zip(tests, results):
        assert (
            list(group_speller(test)) == result
        ), "list(group_speller(test)) != result"
    tests = [
        ((60, 63, 66), ("C4", "Eb4", "Gb4"), ("c", "e-", "g-")),
        ((24, 48, 60, 71), ("C1", "C3", "C4", "B4"), ("CCC", "C", "c", "b")),
        # Next tests ensure that Cb and B# are in the right octaves
        (
            (58, 59, 61, 63, 65),
            ("Bb3", "Cb4", "Db4", "Eb4", "F4"),
            ("B-", "c-", "d-", "e-", "f"),
        ),
        (
            (51, 52, 54, 57, 60, 61),
            ("D#3", "E3", "F#3", "A3", "B#3", "C#4"),
            ("D#", "E", "F#", "A", "B#", "c#"),
        ),
    ]
    for (test, shell, kern) in tests:
        assert group_speller.pitches(test) == list(
            shell
        ), "group_speller.pitches(test) != list(shell)"
        assert group_speller.pitches(test, letter_format="kern") == list(
            kern
        ), 'group_speller.pitches(test, letter_format="kern") != list(kern)'
    tests = [
        ((60, 63, None, 66), ("C4", "Eb4", "", "Gb4"), ("c", "e-", "r", "g-")),
        (
            (24, None, 48, 60, 71, None),
            ("C1", "", "C3", "C4", "B4", ""),
            ("CCC", "r", "C", "c", "b", "r"),
        ),
    ]
    for (test, shell, kern) in tests:
        assert group_speller.pitches(test, rests="") == list(shell), (
            "group_speller.pitches(test, rests=" ") != list(shell)"
        )
        assert group_speller.pitches(
            test, letter_format="kern", rests="r"
        ) == list(
            kern
        ), 'group_speller.pitches(test, letter_format="kern", rests="r") != list(kern)'


if __name__ == "__main__":
    test_build_spelling_dict()
    test_build_fifth_class_spelling_dict()
    test_speller()
    test_group_speller()
