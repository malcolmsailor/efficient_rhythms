import math
import typing

import numpy as np

from . import er_misc_funcs
from . import er_tuning


def get_accidental(n, flat_sign="b"):
    if n >= 0:
        return n * "#"
    return -n * flat_sign


def build_fifth_class_spelling_dict(
    bounds=(-28, 28), forward=True, letter_format="shell"
):
    flat_sign = "b" if letter_format == "shell" else "-"
    alphabet = "DAEBFCG" if letter_format == "shell" else "daebfcg"
    len_alphabet = 7
    out = {}
    for fc in range(bounds[0], bounds[1] + 1):
        letter = alphabet[fc % len_alphabet]
        accidental = get_accidental(
            math.floor((fc + 3) / len_alphabet), flat_sign=flat_sign
        )
        if forward:
            out[fc] = letter + accidental
        else:
            out[letter + accidental] = fc
    return out


class GroupSpeller:
    """Finds the 'best' spelling for lists of pitch-classes.

    'Best' means with the shortest span on the line of fifths, and with least
    absolute summed distance from 'D' (the central pitch of the white-key
    diatonic) of its unique spellings.

    The Pythagorean approach to spelling taken only works if the greatest common
    denominator of the (approximation to the just) fifth and the temperament
    cardinality is 1. If this is not true, raises a ValueError.

    Keyword args:
        tet: sets temperament.

    Methods:
        __call__: takes a sequence of ints, returns an np array of strings

    Raises:
        ValueError if gcd(tet, fifth) is not 1.
    """

    # keys: temperament cardinalities
    # values: tuples of form (fifth, zero_pc)
    tet_dict = {
        12: (7, 2),
        19: (11, 3),
        31: (18, 5),
    }

    def __init__(self, tet=12):
        self.tet = tet
        if tet in self.tet_dict:
            self.fifth, self.zero_pc = self.tet_dict[tet]
        else:
            self.fifth = er_tuning.approximate_just_interval(3 / 2, tet)
            if math.gcd(tet, self.fifth) != 1:
                raise ValueError
            self.zero_pc = 2 * self.fifth % self.tet
        self._shell_dict = build_fifth_class_spelling_dict()
        self._kern_dict = build_fifth_class_spelling_dict(letter_format="kern")
        # self.half_tet = self.tet // 2
        # self.ref_pc = (self.zero_pc - self.fifth * self.half_tet) % self.tet

    def _pc_to_fc(self, pc):
        # return (pc - self.ref_pc) * self.fifth % self.tet - self.half_tet
        return (pc - self.zero_pc) * self.fifth % self.tet

    def __call__(self, pcs, letter_format="shell"):
        """Takes a sequence of ints, returns an np array of spelled strings.

        Args:
            pcs: sequence of ints.

        Keyword args:
            letter_format: either "shell" (C#, Bb, ...) or "kern" (c#, b-, ...)

        Returns:
            Numpy array
        """
        if len(pcs) == 0:
            return np.array(pcs)
        unique_pcs, inv_indices = np.unique(pcs, return_inverse=True)
        fcs = self._pc_to_fc(unique_pcs)
        indices = np.argsort(fcs)
        lower_bound = None
        span = fcs[indices[-1]] - fcs[indices[0]]
        if span > 6:
            for i, j in zip(indices, indices[1:]):
                newspan = (fcs[i] + self.tet) - fcs[j]
                if newspan < span:
                    lower_bound = fcs[j]
                    span = newspan
            if lower_bound is not None:
                fcs = np.array(
                    [fc + self.tet if fc < lower_bound else fc for fc in fcs]
                )
        fcs_sum = fcs.sum()
        while True:
            flat_fcs = fcs - self.tet
            flat_sum = abs(flat_fcs.sum())
            if flat_sum < fcs_sum:
                fcs = flat_fcs
                fcs_sum = flat_sum
            else:
                break
        if letter_format == "shell":
            spellings = [self._shell_dict[fc] for fc in fcs]
        else:
            spellings = [self._kern_dict[fc] for fc in fcs]
        return np.array(spellings)[inv_indices]

    def pitches(self, pitches, letter_format="shell", rests=None):
        """Takes a sequence of ints, returns a list array of spelled strings.

        Args:
            pitches: sequence of ints (and possibly NoneType, if rests is
                passed).

        Keyword args:
            letter_format: either "shell" (C#4, Bb2, ...)
                or "kern" (cc#, B-, ...)
            rests: if passed, then any items in `pitches` with the value of
                `None` will be replaced with this value.

        Returns:
            List
        """

        def _kern_octave(pitch, letter):
            octave = pitch // self.tet - 5
            if octave >= 0:
                return letter * (octave + 1)
            return letter.upper() * (-octave)

        if rests is not None:
            pitches = list(pitches)
            rest_indices = [
                i for (i, pitch) in enumerate(pitches) if pitch is None
            ]
            for i in reversed(rest_indices):
                pitches.pop(i)

        pcs = self(pitches, letter_format=letter_format)

        # The next three lines (and the subtraction of alterations below) ensure
        # that Cb or B# (or even Dbbb, etc.) appear in the correct octave. It
        # feels a little hacky, but it works.
        sharp_sign = "#"
        flat_sign = "b" if letter_format == "shell" else "-"
        alterations = [
            0 + pc.count(sharp_sign) - pc.count(flat_sign) for pc in pcs
        ]

        if letter_format == "shell":
            out = [
                pc + str((pitch - alteration) // self.tet - 1)
                for (pitch, pc, alteration) in zip(pitches, pcs, alterations)
            ]
        else:
            out = [
                _kern_octave(pitch - alteration, pc[0]) + pc[1:]
                for (pitch, pc, alteration) in zip(pitches, pcs, alterations)
            ]
        if rests is not None:
            for i in rest_indices:
                out.insert(i, rests)
        return out


def build_spelling_dict(tet, forward=True, letter_format="shell", fifth=None):
    """Provides a spelling for each pitch-class in given temperament.

    The preferred spelling is determined by proceeding alternately up and down
    in Pythagorean manner from D (the central pitch of the diatonic, when
    proceeding by 5ths). This only works, however, if the greatest common
    denominator of the (approximation to the just) fifth and the temperament
    cardinality is 1. If this is not true, raises a ValueError.

    The spelling is always normalized so that the letter C is assigned to
    pitch_class 0.

    Keyword args:
        forward: boolean. If True, then dictionary is of form (pitch-class,
            letter). Otherwise, dictionary is of form (letter, pitch-class).
            Default: True.
        letter_format: either "shell" (C#, Bb, ...) or "kern" (c#, b-, ...)
        fifth: optionally, pass the size of a fifth in the given temperament.
            Otherwise, this is calculated by a call to
            `tuning.approximate_just_interval(3/2, tet)`

    Raises:
        ValueError if gcd(tet, fifth) is not 1.
    """

    alphabet = "fcgdaeb"

    unnormalized_dict = {}

    counter = 0

    if fifth is None:
        fifth = er_tuning.approximate_just_interval(3 / 2, tet)

    if math.gcd(tet, fifth) != 1:
        raise ValueError

    flat_sign = "b" if letter_format == "shell" else "-"
    accidental_n = 0

    while True:
        if len(unnormalized_dict.items()) >= tet and (
            forward or abs(accidental_n) > 3
        ):
            break

        pitch_class = (counter * fifth) % tet

        accidental_n = math.floor((3 + counter) / len(alphabet))
        accidental = get_accidental(accidental_n, flat_sign=flat_sign)

        letter = alphabet[(3 + counter) % len(alphabet)]

        if letter + accidental == "c":
            c_pitch_class = pitch_class

        if letter_format == "shell":
            letter = letter.upper()

        if forward:
            unnormalized_dict[pitch_class] = letter + accidental
        else:
            unnormalized_dict[letter + accidental] = pitch_class

        if counter > 0:
            counter = -counter
        else:
            counter = -counter + 1

    if forward:
        return {
            (k - c_pitch_class) % tet: v for k, v in unnormalized_dict.items()
        }

    return {k: (v - c_pitch_class) % tet for k, v in unnormalized_dict.items()}


class Speller:
    """Spells pitches or pitch-classes in specified temperament.

    When spelling pitches, C4 is always 5 * c, where c is the cardinality of the
    temperament. So in 12-tet, C4 = 60; in 31-tet, C4 = 155, and so on.

    Double-sharps and flats (and beyond) are always indicated by repetition of
    the accidental symbol (e.g., F##).

    Keyword args:
        tet: integer. Default 12.
        pitches: boolean. If true, spells pitches (e.g., in 12-tet, 60 = "C4").
            If false, spells pitch-classes (e.g., in 12-tet, 60 = "C").
            Default: False.
        rests: boolean. If true, spells None as "Rest". If false, raises a
            TypeError on None values.
        return_type: string. If "string", when instance is called, it will
            delegate to self.spelled_string(); if "list", it will delegate to
            self.spelled_list(). Other values will raise a ValueError.
            Default: "string".
        letter_format: string.
            Possible values:
                "shell": e.g., "C4", "Ab2", "F#7"
                "kern": e.g., "c", "DD", "b-", "F#"

    Raises:
        ValueError: if return_type is not "string" or "list".
        ValueError: if letter_format is not "shell" or "kern".
        ValueError: if gcd(tet, tuning.approximate_just_interval(3/2, tet))
            is not 1.

    Methods:
    # QUESTION where and how to document __call__()?
        spelled_list(item, pitches=None)
        spelled_string(item, pitches=None)
    """

    def __init__(
        self,
        tet=12,
        pitches=False,
        rests=True,
        return_type="string",
        letter_format="shell",
    ):
        self._tet = tet
        self._pitches = pitches
        self._rests = rests
        if return_type not in ("string", "list"):
            raise ValueError(
                f"return_type {return_type} not in ('string', 'list')"
            )
        self._return_type = return_type
        if letter_format == "shell":
            self._pitch = self._shell_pitch
        elif letter_format == "kern":
            self._pitch = self._kern_pitch
        else:
            raise ValueError(
                f"letter_format {letter_format} not in ('shell', 'kern')"
            )
        self._spelling_dict = build_spelling_dict(
            tet, letter_format=letter_format
        )

    def __call__(self, item, pitches=None):
        if self._return_type == "string":
            return self.spelled_string(item, pitches=pitches)
        return self.spelled_list(item, pitches=pitches)

    def _shell_pitch(self, pc_string, pitch_num):
        """Appends an octave number to a pitch-class (e.g., "C#" becomes "C#3")"""
        octave = pitch_num // self._tet - 1
        return pc_string + str(octave)

    def _kern_pitch(self, pc_string, pitch_num):
        if pc_string[0] == "c" and pc_string[-1] == "-":
            pitch_num += self._tet
        temp_num = (pitch_num % self._tet) + (self._tet * 5)

        if temp_num > pitch_num:
            pc_string = pc_string[0].upper() + pc_string[1:]
            temp_num -= self._tet
        while temp_num > pitch_num:
            pc_string = pc_string[0] + pc_string
            temp_num -= self._tet
        while temp_num < pitch_num:
            pc_string = pc_string[0] + pc_string
            temp_num += self._tet

        return pc_string

    @er_misc_funcs.nested_method
    def spelled_list(self, item, pitches=None):
        """Spells integers as musical pitches or pitch-classes.

        Args:
            item: either an integer, or an (arbitrarily deep and nested)
                list-like of integers (and None values, if Speller was
                initialized with rests=True).

        Keyword args:
            pitches: boolean. Temporarily overrides the current setting for
                the Speller instance. If true, spells pitches (e.g., in 12-tet,
                60 = "C4"). If false, spells pitch-classes (e.g., in 12-tet,
                60 = "C").
                Default: None.

        Returns:
            A string representing a single pitch, if item is an integer.
            A list of strings, if item is a list-like, with the same depth and
                nesting as item.

        Raises:
            TypeError if iter() fails on item and item is not an integer (or
                None, if Speller was not initialized with rests=False.)
        """
        if pitches is None:
            pitches = self._pitches

        if not isinstance(item, (int, np.integer)):
            if item is not None or not self._rests:
                raise TypeError(
                    "Speller.spelled_list() can only take iterables of "
                    "integers, or None for rests"
                )

        if item is None:
            return "Rest"

        if item < 0:
            return item

        pitch_class = self._spelling_dict[item % self._tet]
        if not pitches:
            return pitch_class

        return self._pitch(pitch_class, item)

    def spelled_string(self, item, pitches=None):
        if isinstance(item, typing.Sequence) and not isinstance(item, str):
            flat = flatten(item)
            if any([isinstance(f, str) for f in flat]):
                if not all([isinstance(f, str) for f in flat]):
                    raise TypeError
                return " ".join(flat)
            return " ".join(self.spelled_list(flat, pitches=pitches))

        if isinstance(item, str):
            return item
        return self.spelled_list(item, pitches=pitches)


def flatten(item, iter_types=(list, tuple)):
    """Flattens an iterable of iterables. Can contain irregularly nested
    iterables. Returns a list.

    Keyword args:
        iter_types: a tuple of types that should be considered 'iterables'.
            Default: (list, tuple).

    Returns:
        list

    Raises:
        TypeError if outer item is not in iter_types.
    """

    def _sub(item):
        iterable = isinstance(item, iter_types)
        if iterable:
            out = []
            for sub_item in item:
                out += _sub(sub_item)
            return out

        return [
            item,
        ]

    if not isinstance(item, iter_types):
        raise TypeError("Outer item must be an iterable in iter_types")
    out = []
    out += _sub(item)
    return out
