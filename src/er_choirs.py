"""Choir functions for efficient_rhythms2.py"""

import copy
import itertools
import random
import warnings

import src.er_tuning as er_tuning


class ChoirError(Exception):
    pass


class Choir:
    def __init__(self, sub_choirs, split_points):
        if len(split_points) != len(sub_choirs) - 1:
            raise ChoirError(
                "Wrong number of split points for the number of " "sub choirs."
            )
        if list(split_points) != sorted(split_points):
            raise ChoirError(
                "Split points in wrong order (must be in "
                "ascending numerical order)"
            )
        self.split_points = sorted(split_points)
        self.sub_choirs = sub_choirs
        self.split_points = split_points

    def get_sub_choir_i(self, pitch):
        sub_choir_i = 0
        for split_point in self.split_points:
            if split_point > pitch:
                break
            sub_choir_i += 1

        return sub_choir_i

    def temper_split_points(self, tet, integers_in_12_tet):
        er_tuning.temper_pitch_materials_in_place(
            self.split_points, tet, integers_in_12_tet
        )


def get_choir_prog(choirs, choir_i, pitch):
    choir_program_i = 0
    for i in range(choir_i):
        try:
            choir_program_i += len(choirs[i].sub_choirs)
        except (AttributeError, IndexError):
            choir_program_i += 1

    try:
        choir_program_i += choirs[choir_i].get_sub_choir_i(pitch)
    except (AttributeError, IndexError):
        pass
    return choir_program_i


def order_choirs(er, max_len=100, warn_if_loop_too_short=False):
    """Construct a random choir order.

    Keyword args:
        max_len: int. Short values of "max_len" can be
            useful for constructing audible loops.

    Returns:
        A list of tuples. Each tuple is of length num_voices.
        Each tuple consists of indexes for assigning voices to choirs.
    """

    class ChoirOrderError(Exception):
        """Raised when more voice than choirs and
        all_voices_from_different_choirs
        """

        def __init__(self):
            Exception.__init__(self)
            self.message = (
                "More voices than choirs and "
                "all_voices_from_different_choirs."
            )

        def __str__(self):
            return self.message

    def _next_choir_order(out, choices):
        choices = choices.copy()
        while choices:
            choice = random.choice(choices)
            if er.max_consec_seg_from_same_choir <= 0:
                return choice
            if len(out) < er.max_consec_seg_from_same_choir + 1:
                return choice
            continue_on = False
            for voice_i in range(er.num_voices):
                repeats = []
                for j in range(1, er.max_consec_seg_from_same_choir + 1):
                    repeats.append(choice[voice_i] == out[-j][voice_i])
                if all(repeats):
                    choices.remove(choice)
                    continue_on = True
                    break
            if continue_on:
                continue

            return choice
        return None

    if er.all_voices_from_different_choirs:
        if er.num_choirs < er.num_voices:
            raise ChoirOrderError
        choices = list(
            itertools.permutations(range(er.num_choirs), er.num_voices)
        )
    else:
        choices = list(
            itertools.product(range(er.num_choirs), repeat=er.num_voices)
        )

    out = []
    while choices and len(out) < max_len:
        next_order = _next_choir_order(out, choices)
        if next_order is None:
            break
        out.append(next_order)
        if er.each_choir_combination_only_once:
            choices.remove(next_order)

    if len(out) < max_len and warn_if_loop_too_short:
        warnings.warn("Unable to constuct choir loop of sufficient length.")

    out = list(zip(*out))

    return out


def assign_choirs(er, super_pattern):
    """Apply the choir order and settings."""

    if er.randomly_distribute_between_choirs:
        if er.length_choir_segments <= 0:
            for voice_i, voice in enumerate(super_pattern.voices):
                choir = er.choir_order[voice_i][0]
                for note in voice:
                    note.choir = choir
            return

        for voice_i, voice in enumerate(super_pattern.voices):
            prev_choir = None
            choir_assignments = er.choir_order[voice_i]
            for note in voice:
                attack_time = note.attack_time
                choir_i = attack_time // er.length_choir_segments
                if er.choir_segments_dovetail:
                    try:
                        prev_choir = choir
                    except UnboundLocalError:
                        pass
                choir = choir_assignments[choir_i % len(choir_assignments)]
                note.choir = choir
                # if (er.choir_segments_dovetail and choir_i > 0
                #         and prev_choir != choir):
                if (
                    er.choir_segments_dovetail
                    and prev_choir is not None
                    and prev_choir != choir
                ):
                    new_note = copy.copy(note)
                    new_note.choir = prev_choir
                    voice.add_note_object(new_note)

        return

    for voice_i, voice in enumerate(super_pattern.voices):
        choir = er.get(voice_i, "choir_assignments")
        for note in voice:
            note.choir = choir
