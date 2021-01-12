"""Rhythm functions for efficient_rhythms2.py.

March 13 2019: begun rewrite to remove reliance on arrays of 1's and 0's.
"""
import collections
import fractions
import functools
import math
import random
import warnings

import numpy as np

import er_cont_rhythm
import er_midi
import er_misc_funcs


class RhythmicDict(collections.UserDict):
    def __str__(self):
        strings = []
        strings.append("#" * 51)
        for attack_time, dur in self.items():
            strings.append(
                "Attack:{:>10.6}  Duration:{:>10.6}"
                "".format(float(attack_time), float(dur))
            )
        strings.append("\n")
        return "\n".join(strings)[:-2]

    # def make_attack_and_dur_lists(self):
    #     self.attack_times = list(self.keys())
    #     self.attack_times_and_durs = list(self.items())

    # LONGTERM attack_times and attack_times_and_durs assume that
    #   the contents will no longer be changed after their first access.
    #   Is there a way to enforce this?
    @functools.cached_property
    def attack_times(self):
        return list(self.keys())

    @functools.cached_property
    def attack_times_and_durs(self):
        return list(self.items())


class Rhythm(RhythmicDict):
    @functools.cached_property
    def total_num_notes(self):
        # LONGTERM check whether this works with truncate
        out = self.num_notes
        running_length = self.rhythm_len
        while running_length < self.total_rhythm_len:
            break_out = False
            if running_length + self.rhythm_len <= self.total_rhythm_len:
                running_length += self.rhythm_len
                out += self.num_notes
            else:
                for attack_time in self:
                    if running_length + attack_time >= self.total_rhythm_len:
                        break_out = True
                        break
                    out += 1
            if break_out:
                break
        return out

    def __init__(self, er, voice_i):
        super().__init__()
        self.voice_i = voice_i
        (
            self.num_notes,
            self.rhythm_len,
            self.pattern_len,
            self.min_dur,
            self.dur_density,
            self.overlap,
        ) = er.get(
            voice_i,
            "num_notes",
            "rhythm_len",
            "pattern_len",
            "min_dur",
            "dur_density",
            "overlap",
        )
        self.total_rhythm_len = self.pattern_len
        if er.truncate_patterns:
            # max_len = max(er.pattern_len)
            # self.truncate_len = max_len % self.pattern_len
            self.truncate_len = max(er.pattern_len)
            if self.truncate_len == self.pattern_len:
                self.truncate_len = 0
            else:
                self.n_patterns_per_truncate = math.ceil(
                    self.truncate_len / self.pattern_len
                )
        else:
            self.truncate_len = 0
        # self.total_num_notes is overwritten in ContinuousRhythm and used
        # in get_attack_time_and_dur
        # self.total_num_notes = self.num_notes

        # self._get_offsets(er.max_super_pattern_len)
        self._check_min_dur()

    def _check_min_dur(self):
        if self.rhythm_len < self.min_dur * self.num_notes:
            new_min_dur = er_misc_funcs.convert_to_fractions(
                self.rhythm_len / self.num_notes
            )
            print(
                f"Notice: min_dur too long in voice {self.voice_i} rhythm; "
                f"reducing from {self.min_dur} to {new_min_dur}."
            )
            self.min_dur = new_min_dur
        if self.rhythm_len <= self.min_dur * self.num_notes:
            # TODO move this notice outside of the initial_pattern loop
            print(
                "Notice: 'cont_rhythms' will have no effect in voice "
                f"{self.voice_i} because "
                "'min_dur' is the maximum value compatible with "
                "'rhythm_len', 'attack_subdivision', and 'sub_subdivisions'. "
                "To allow 'cont_rhythms' to have an effect, reduce 'min_dur' "
                f"to less than {self.min_dur}"
            )
            self.full = True
        else:
            self.full = False

    @functools.cached_property
    def truncated_pattern_num_notes(self):
        if not self.truncate_len:
            raise ValueError
        self._truncated_pattern_num_notes = 0
        for attack_time in self:
            if (attack_time + self.min_dur) >= (
                self.truncate_len % self.total_rhythm_len
            ):
                break
            self._truncated_pattern_num_notes += 1
        return self._truncated_pattern_num_notes

    @functools.cached_property
    def loop_num_notes(self):
        return (
            self.truncate_len // self.pattern_len * self.total_num_notes
            + self.truncated_pattern_num_notes
        )

    def get_attack_time_and_dur(self, rhythm_i):
        if not self.truncate_len:
            offset = (rhythm_i // self.total_num_notes) * self.total_rhythm_len
            attack_time, dur = self.attack_times_and_durs[
                rhythm_i % self.total_num_notes
            ]
            return attack_time + offset, dur
        # else: we need to take truncated patterns into account
        # LONGTERM it would probably be better to just write the whole
        #   loop to the rhythm rather than do all this complicated logic
        #   every time
        loop_offset = (rhythm_i // self.loop_num_notes) * self.truncate_len
        n_patterns = (rhythm_i % self.loop_num_notes) // self.total_num_notes
        offset = n_patterns * self.total_rhythm_len
        attack_time, dur = self.attack_times_and_durs[
            (rhythm_i % self.loop_num_notes) % self.total_num_notes
        ]
        attack_time += loop_offset + offset
        if n_patterns != self.n_patterns_per_truncate - 1:
            return attack_time, dur
        overdur = loop_offset + self.truncate_len - (attack_time + dur)
        if self.overlap:
            overdur += self.attack_times[0]
        return attack_time, dur + min(0, overdur)


class ContinuousRhythmicObject(RhythmicDict):
    """Used as a base for ContinuousRhythm and Grid objects."""

    # def round(self, precision=4):
    def round(self):
        try:
            self.pattern_len
        except AttributeError:
            # Grid object does not have pattern_len attribute.
            adj_len = self.rhythm_len  # pylint: disable=no-member
        else:
            if (
                self.rhythm_len < self.pattern_len
                and self.pattern_len % self.rhythm_len != 0
            ):
                adj_len = self.pattern_len
            else:
                adj_len = self.rhythm_len
        for var in self.rel_attacks:  # pylint: disable=no-member
            for j, dur in enumerate(var):
                var[j] = round(dur, 4)
            var[j] += adj_len - var.sum()
        try:
            self.durs  # pylint: disable=no-member
        except AttributeError:
            # Grid object does not have .durs attribute.
            return
        for var in self.durs:  # pylint: disable=no-member
            for j, dur in enumerate(var):
                var[j] = round(dur, 4)

    # def round_to_frac(self, max_denominator=10000):
    #     # This function doesn't work because fractions are not a valid
    #     # datatype for np arrays.
    #     try:
    #         self.pattern_len
    #     except AttributeError:
    #         # Grid object does not have .pattern_len attribute.
    #         adj_len = self.rhythm_len
    #     else:
    #         if (self.rhythm_len < self.pattern_len and
    #                 self.pattern_len % self.rhythm_len != 0):
    #             adj_len = self.pattern_len
    #         else:
    #             adj_len = self.rhythm_len
    #     for var_i, var in enumerate(self.rel_attacks):
    #         for j, dur in enumerate(var):
    #             var[j] = fractions.Fraction(dur).limit_denominator(
    #                 max_denominator=max_denominator)
    #         var[j] += adj_len - var.sum()
    #     try:
    #         self.durs
    #     except AttributeError:
    #         # Grid object does not have .durs attribute.
    #         return
    #     for var_i, var in enumerate(self.durs):
    #         for j, dur in enumerate(var):
    #             var[j] = fractions.Fraction(dur).limit_denominator(
    #                 max_denominator=max_denominator)

    def rel_attacks_to_rhythm(
        self, offset=0, first_var_only=False, comma=fractions.Fraction(1, 5000)
    ):

        if first_var_only:
            # For use with Grid
            rel_attacks = self.rel_attacks[0]  # pylint: disable=no-member
        else:
            rel_attacks = self.rel_attacks.reshape(  # pylint: disable=no-member
                -1
            )

        try:
            durs = self.durs.reshape(-1)
        except AttributeError:
            # Grid does not have durs attribute.
            durs = rel_attacks

        for i, rel_attack in enumerate(rel_attacks):
            frac_rel_attack = fractions.Fraction(rel_attack).limit_denominator(
                max_denominator=100000
            )
            frac_dur = fractions.Fraction(durs[i]).limit_denominator(
                max_denominator=100000
            )
            if frac_rel_attack == 0:
                continue
            self[offset] = frac_dur
            offset += frac_rel_attack
            # if rel_attack == 0:
            #     continue
            # self[offset] = durs[i]
            # offset += rel_attack

        for attack_i, attack_time in enumerate(self.attack_times[:-1]):
            overlap = (
                attack_time
                + self[attack_time]
                - self.attack_times[attack_i + 1]
            )
            if overlap > comma:
                warnings.warn("Unexpectedly long overlap in rhythm")
            if overlap > 0:
                self[attack_time] = (
                    self.attack_times[attack_i + 1] - attack_time
                )


class ContinuousRhythm(Rhythm, ContinuousRhythmicObject):
    def __init__(self, er, voice_i):
        super().__init__(er, voice_i)

        (
            self.cont_var_increment,
            self.num_cont_rhythm_vars,
            self.vary_rhythm_consistently,
        ) = er.get(
            voice_i,
            "cont_var_increment",
            "num_cont_rhythm_vars",
            "vary_rhythm_consistently",
        )
        self.increment = self.rhythm_len * self.cont_var_increment
        self.rel_attacks = np.zeros((self.num_cont_rhythm_vars, self.num_notes))
        self.durs = np.full_like(self.rel_attacks, self.min_dur)
        self.deltas = None
        if (
            self.rhythm_len < self.pattern_len
            and self.pattern_len % self.rhythm_len != 0
        ):
            self.total_rhythm_len = self.pattern_len * self.num_cont_rhythm_vars
        else:
            self.total_rhythm_len = self.rhythm_len * self.num_cont_rhythm_vars
        self.total_num_notes = self.num_notes * self.num_cont_rhythm_vars


def print_rhythm(rhythm):
    if isinstance(rhythm, list):
        strings = []
        strings.append("#" * 51)
        for attack_time in rhythm:
            strings.append("Attack:{:>10.3}" "".format(float(attack_time)))
        strings.append("\n")
        print("\n".join(strings)[:-2])
    elif isinstance(rhythm, dict):
        strings = []
        strings.append("#" * 51)
        for attack_time, dur in rhythm.items():
            strings.append(
                "Attack:{:>10.3}  Duration:{:>10.3}"
                "".format(float(attack_time), float(dur))
            )
        strings.append("\n")
        print("\n".join(strings)[:-2])


def _get_attack_positions(er, voice_i):

    if er.cont_rhythms == "grid":
        return list(er.grid.keys())

    rhythm_len, sub_subdiv_props = er.get(
        voice_i, "rhythm_len", "sub_subdiv_props"
    )
    attack_positions = []
    time_i = 0
    time = fractions.Fraction(0, 1)
    while time < rhythm_len:
        attack_positions.append(time)
        time += sub_subdiv_props[time_i % len(sub_subdiv_props)]
        time_i += 1

    return attack_positions


def _get_available_for_hocketing(er, voice_i, prev_rhythms, attack_positions):
    """Used for er.hocketing. Returns those subdivisions
    that are available for to be selected. (I.e., those
    that do not belong to the previously constructed
    rhythms, and those that do not belong to obligatory
    beats in other voices.)
    """
    out = []
    for attack in attack_positions:
        write = True
        for prev_rhythm in prev_rhythms:
            if attack in prev_rhythm:
                write = False
                break
        if not write:
            continue
        for oblig_attacks_i, oblig_attacks in enumerate(er.obligatory_attacks):
            if oblig_attacks_i != voice_i % len(er.obligatory_attacks):
                if attack in oblig_attacks:
                    write = False
                    break
        if not write:
            continue
        out.append(attack)

    return out


def _get_available_for_quasi_unison(
    er, voice_i, leader_rhythms, attack_positions
):
    out = []
    for attack in attack_positions:
        go_on = False
        for leader_rhythm in leader_rhythms:
            if attack in leader_rhythm:
                out.append(attack)
                go_on = False
                break
        if go_on:
            continue
        for oblig_attacks_i, oblig_attacks in enumerate(er.obligatory_attacks):
            if oblig_attacks_i != voice_i % len(er.obligatory_attacks):
                if attack in oblig_attacks:
                    out.append(attack)
                    break

    return out


def _get_leader_available(er, remaining, leader_rhythm):
    # LONGTERM make this work when the follower rhythm is a different length
    #   (especially longer) than the leader rhythm?
    out = []
    for time in remaining:
        leader_time = time

        while leader_time >= 0 and leader_time not in leader_rhythm:
            leader_time -= er.attack_subdivision_gcd
        if leader_time < 0:
            continue
        if time <= leader_time + leader_rhythm[leader_time]:
            out.append(time)

    return out


def _get_attack_list(
    er, voice_i, attack_positions, available, leader_rhythm=None
):
    def _add_attack(attack, remove_oblig=False):
        nonlocal num_notes
        out.append(attack)
        num_notes -= 1
        if attack in remaining:
            remaining.remove(attack)
        if attack in available:
            available.remove(attack)
        if remove_oblig and attack in oblig:
            oblig.remove(attack)

    num_notes, obligatory_attacks = er.get(
        voice_i, "num_notes", "obligatory_attacks"
    )
    remaining = attack_positions.copy()
    # I'm not sure whether it's necessary to make a copy of obligatory
    #   attacks, but doing it to be safe, for now, at least.
    oblig = obligatory_attacks.copy()

    out = []
    if voice_i == 0 and er.force_root_in_bass in (
        "first_beat",
        "global_first_beat",
    ):
        _add_attack(fractions.Fraction(0, 1), remove_oblig=True)

    for attack in oblig:
        if attack in remaining:
            _add_attack(attack)
        else:
            print(
                f"Note: obligatory attack {attack} in voice {voice_i} "
                "not available."
            )

    while num_notes and available:
        choose = random.choice(available)
        _add_attack(choose)

    if num_notes and leader_rhythm:
        available = _get_leader_available(er, remaining, leader_rhythm)
        while num_notes and available:
            choose = random.choice(available)
            _add_attack(choose)

    # Add attacks to obtain the specified number of notes.
    for _ in range(num_notes):
        choose = random.choice(remaining)
        _add_attack(choose)
    out.sort()

    return out


def _get_attack_dict_and_durs_to_next_attack(er, voice_i, attack_list):
    """Returns a dictionary of attacks (with minimum durations)
    as well as a dictionary of the duration between attacks
    """

    min_dur, rhythm_len = er.get(voice_i, "min_dur", "rhythm_len")

    attack_times = {}
    durs = {}

    for attack_i, attack in enumerate(attack_list):
        try:
            dur = attack_list[attack_i + 1] - attack
        except IndexError:
            dur = rhythm_len - attack
            if er.overlap:
                dur += attack_list[0]
        durs[attack] = dur
        attack_times[attack] = min(dur, min_dur)

    return attack_times, durs


def _fill_quasi_unison_durs(er, voice_i, attacks, leader_rhythm):
    leader_durs_at_attacks = {}
    rhythm_length = er.rhythm_len[voice_i]
    time = rhythm_length
    leader_attack = rhythm_length
    current_dur = 0
    while time > 0:
        time -= er.attack_subdivision_gcd
        if time in leader_rhythm:
            leader_dur = leader_rhythm[time]
            if time + leader_dur == leader_attack:
                current_dur += leader_dur
            else:
                current_dur = leader_dur
            if time in attacks:
                leader_durs_at_attacks[time] = current_dur
            leader_attack = time

    return leader_durs_at_attacks


def _fill_attack_durs(
    er, voice_i, attacks, durs, leader_i=None, leader_durs_at_attacks=()
):
    """Adds to the attack durations until the specified
    density is achieved. Doesn't return anything, just
    alters the attack dictionary in place.
    """

    def _fill_attacks_sub(dur_dict, remaining_dict):
        actual_total_dur = sum(attacks.values())
        available = []
        for time in attacks:
            if time in dur_dict and attacks[time] != dur_dict[time]:
                available.append(time)

        while target_total_dur > actual_total_dur and available:
            choose = random.choice(available)
            remaining_dur = remaining_dict[choose] - attacks[choose]
            dur_to_add = min(dur_subdivision, remaining_dur)
            attacks[choose] += dur_to_add
            actual_total_dur += dur_to_add
            if (
                attacks[choose] >= dur_dict[choose]
                or attacks[choose] >= remaining_dict[choose]
            ):
                available.remove(choose)

        return actual_total_dur

    dur_subdivision = er.get(voice_i, "dur_subdivision")

    target_total_dur = fractions.Fraction(
        er.dur_density[voice_i] * er.rhythm_len[voice_i]
    ).limit_denominator(max_denominator=8192)

    if leader_durs_at_attacks:
        actual_total_dur = _fill_attacks_sub(leader_durs_at_attacks, durs)
        if (actual_total_dur >= target_total_dur) or (
            er.rhythmic_quasi_unison_constrain
            and er.attack_density[voice_i] < er.attack_density[leader_i]
        ):
            return

    _fill_attacks_sub(durs, durs)


def _add_comma(er, voice_i, attacks):

    # This function shouldn't run with any sort of continuous rhythms.
    if er.cont_rhythms != "none":
        return

    # LONGTERM verify that this is working with complex subdivisions
    rhythm_length = er.rhythm_len[voice_i]
    subdivision = er.attack_subdivision[voice_i]
    comma_position = er.comma_position[voice_i]

    if comma_position == "end":
        return

    comma = rhythm_length % subdivision

    if isinstance(comma_position, int):
        comma_i = comma_position
        if comma_i > len(attacks):
            warnings.warn(
                f"Comma position for voice {voice_i} greater "
                "than number of attacks in rhythm. Choosing a "
                "random comma position."
            )
            comma_i = random.randrange(len(attacks))
    else:
        comma_i = 0

        if comma_position == "middle":
            comma_i = random.randrange(1, len(attacks))
        else:
            comma_i = random.randrange(len(attacks) + 1)

    attack_list = list(attacks.keys())

    for attack in attack_list[comma_i:]:
        new_attack = attack + comma
        dur = attacks[attack]
        del attacks[attack]
        attacks[new_attack] = dur


def _fit_rhythm_to_pattern(er, voice_i, attacks):
    """If the rhythm is shorter than the pattern, extend it as necessary.
    """

    if not attacks:
        return

    rhythm_len, pattern_len, num_notes = er.get(
        voice_i, "rhythm_len", "pattern_len", "num_notes"
    )

    if rhythm_len >= pattern_len:
        return

    attack_list = list(attacks.keys())

    attack_i = num_notes
    while True:
        prev_attack = attack_list[attack_i % len(attack_list)]
        new_attack = prev_attack + rhythm_len * (attack_i // num_notes)
        if new_attack >= pattern_len:
            break
        attacks[new_attack] = attacks[prev_attack]
        attack_i += 1

    last_attack_time = max(attacks)
    last_attack_dur = attacks[last_attack_time]
    overshoot = last_attack_time + last_attack_dur - pattern_len
    if er.overlap:
        first_attack_time = min(attacks)
        overshoot -= first_attack_time
    if overshoot > 0:
        attacks[last_attack_time] -= overshoot


def generate_rhythm1(er, voice_i, prev_rhythms=()):
    """Constructs a rhythm randomly according to the arguments supplied.

    Keyword args:
        prev_rhythms (list of dictionaries): used in the construction of
            hocketed rhythms.

    Returns:
        A dictionary of (Fraction:attack time, Fraction:duration) pairs.
    """

    if voice_i in er.rhythmic_unison_followers:
        leader_i = er.rhythmic_unison_followers[voice_i]
        return prev_rhythms[leader_i]

    if er.cont_rhythms == "all":
        return er_cont_rhythm.get_rhythm(er, voice_i)

    subdivision = er.attack_subdivision[voice_i]

    if er.min_dur[voice_i] == 0:
        er.min_dur[voice_i] = subdivision
    if er.dur_subdivision[voice_i] == 0:
        er.dur_subdivision[voice_i] = subdivision

    attack_positions = _get_attack_positions(er, voice_i)

    available = []
    if voice_i in er.hocketing_followers:
        leaders = []
        for leader_i in er.hocketing_followers[voice_i]:
            leaders.append(prev_rhythms[leader_i % len(prev_rhythms)])
        available = _get_available_for_hocketing(
            er, voice_i, leaders, attack_positions
        )
    elif voice_i in er.rhythmic_quasi_unison_followers:
        leader_i = er.rhythmic_quasi_unison_followers[voice_i]
        leader_rhythm = prev_rhythms[leader_i % len(prev_rhythms)]
        available = _get_available_for_quasi_unison(
            er, voice_i, [prev_rhythms[leader_i],], attack_positions
        )

        if (
            er.attack_density[voice_i] > er.attack_density[leader_i]
            and er.rhythmic_quasi_unison_constrain
        ):
            attack_list = _get_attack_list(
                er, voice_i, attack_positions, available, leader_rhythm
            )
        else:
            attack_list = _get_attack_list(
                er, voice_i, attack_positions, available
            )

        attacks, durs = _get_attack_dict_and_durs_to_next_attack(
            er, voice_i, attack_list
        )

        leader_durs_at_attacks = _fill_quasi_unison_durs(
            er, voice_i, attacks, prev_rhythms[leader_i],
        )

        _fill_attack_durs(
            er,
            voice_i,
            attacks,
            durs,
            leader_i=leader_i,
            leader_durs_at_attacks=leader_durs_at_attacks,
        )
        if er.cont_rhythms == "grid":
            rhythm = er.grid.return_varied_rhythm(er, attacks, voice_i)
            return rhythm
        _add_comma(er, voice_i, attacks)

        _fit_rhythm_to_pattern(er, voice_i, attacks)

        rhythm = Rhythm(er, voice_i)
        rhythm.data = attacks
        return rhythm
    # LONGTERM consolidate this code with above (a lot of duplication!)
    attack_list = _get_attack_list(er, voice_i, attack_positions, available)

    attacks, durs = _get_attack_dict_and_durs_to_next_attack(
        er, voice_i, attack_list
    )

    _fill_attack_durs(er, voice_i, attacks, durs)

    _add_comma(er, voice_i, attacks)

    if er.cont_rhythms == "grid":
        rhythm = er.grid.return_varied_rhythm(er, attacks, voice_i)
        return rhythm

    _fit_rhythm_to_pattern(er, voice_i, attacks)

    rhythm = Rhythm(er, voice_i)
    rhythm.data = attacks
    return rhythm


def update_pattern_voice_leading_order(er, rhythms):
    if er.cont_rhythms != "none":
        er.num_notes_by_pattern = [
            len(rhythms[voice_i].rel_attacks[0])
            # len(rhythms[voice_i].attack_times[0])
            for voice_i in range(er.num_voices)
        ]
        # The next lines seem a little kludgy, it would be nice to
        # treat all rhythms in a more homogenous way. But for now, at least
        # it works.
        for voice_i in range(er.num_voices):
            pattern_len, rhythm_len = er.get(
                voice_i, "pattern_len", "rhythm_len"
            )
            if pattern_len % rhythm_len == 0:
                num_repeats_of_rhythm = pattern_len // rhythm_len
                er.num_notes_by_pattern[voice_i] *= num_repeats_of_rhythm

    else:
        # The length of each rhythm is equal to the number of notes
        # per pattern because of the _fit_rhythm_to_pattern function
        # previously run.
        er.num_notes_by_pattern = [len(rhythm) for rhythm in rhythms]

    # if er.truncate_patterns:
    #     max_len = max(er.pattern_len)
    #     truncate_lens = [
    #         max_len % pattern_len for pattern_len in er.pattern_len
    #     ]
    #     er.num_notes_by_truncated_pattern = [0 for i in range(er.num_voices)]
    #     for voice_i, truncate_len in enumerate(truncate_lens):
    #         if truncate_len:
    #             for attack_time in rhythms[voice_i]:
    #                 if attack_time >= truncate_len:
    #                     break
    #                 er.num_notes_by_truncated_pattern[voice_i] += 1

    totals = [0 for rhythm in rhythms]
    for i in range(len(er.pattern_voice_leading_order)):
        vl_item = er.pattern_voice_leading_order[i]
        start_rhythm_i = totals[vl_item.voice_i]
        if (
            er.truncate_patterns
            and (vl_item.end_time - vl_item.start_time)
            < er.pattern_len[vl_item.voice_i]
        ):
            # totals[vl_item.voice_i] += er.num_notes_by_truncated_pattern[
            #     vl_item.voice_i
            # ]
            totals[vl_item.voice_i] += rhythms[
                vl_item.voice_i
            ].truncated_pattern_num_notes
        else:
            totals[vl_item.voice_i] += er.num_notes_by_pattern[vl_item.voice_i]
        # end_rhythm_i is the first note *after* the rhythm ends
        end_rhythm_i = totals[vl_item.voice_i]
        vl_item.start_rhythm_i = start_rhythm_i
        vl_item.end_rhythm_i = end_rhythm_i


class Grid(ContinuousRhythmicObject):
    def __init__(self, er):
        super().__init__()
        # For now, this only works if all rhythm lengths are the same.
        # MAYBE handle non-identical rhythm lengths.
        class GridError(Exception):
            pass

        if len(set(er.rhythm_len)) > 1:
            raise GridError(
                "Generate grid only works if all rhythm lengths are the same."
            )
        self.rhythm_len = er.rhythm_len[0]

        if (
            len(set(er.pattern_len)) > 1
            or er.pattern_len[0] != er.rhythm_len[0]
        ):
            raise GridError(
                "Generate grid only works if rhythm and pattern lengths are same."
            )

        if len(set(er.num_cont_rhythm_vars)) > 1:
            raise GridError(
                "Generate grid only works if 'num_cont_rhythm_vars' has a single value."
            )
        self.num_cont_rhythm_vars = er.num_cont_rhythm_vars[0]

        if len(set(er.vary_rhythm_consistently)) > 1:
            raise GridError(
                "Generate grid only works if 'vary_rhythm_consistently' "
                "has a single value."
            )
        self.vary_rhythm_consistently = er.vary_rhythm_consistently[0]

        if len(set(er.cont_var_increment)) > 1:
            raise GridError(
                "Generate grid only works if 'cont_var_increment' "
                "has a single value."
            )
        self.increment = er.cont_var_increment[0]

        self.min_dur = min(er.min_dur)
        if len(set(er.min_dur)) > 1:
            print(
                "Notice: more than one value for 'min_dur', using minimum ("
                f"{self.min_dur})"
            )

        # Below we take the "num_div" as done in subfunction _num_notes() in
        #   er_preprocess.py. It would also be possible to use num_notes instead,
        #   with a somewhat different result.
        num_divs = [
            int(
                er.rhythm_len[voice_i]
                / er.attack_subdivision[voice_i]
                * len(er.sub_subdiv_props[voice_i])
            )
            for voice_i in range(er.num_voices)
        ]
        # Although "num_notes" is perhaps not the best name for the next
        #   attribute, it allows us to re-use functions that work with Rhythm
        #   objects.
        self.num_notes = max(num_divs)

        if self.rhythm_len < self.min_dur * self.num_notes:
            new_min_dur = er_misc_funcs.convert_to_fractions(
                self.rhythm_len / self.num_notes
            )
            print(
                "Notice: grid min_dur too long; "
                f"reducing from {self.min_dur} to {new_min_dur}."
            )
            self.min_dur = new_min_dur
        if self.rhythm_len == self.min_dur * self.num_notes:
            print(
                "Notice: 'cont_rhythms' will have no effect because "
                "'min_dur' is the maximum value compatible with "
                "'rhythm_len', 'attack_subdivision', and 'sub_subdivisions'. "
                "To allow 'cont_rhythms' to have an effect, reduce 'min_dur' "
                f"to less than {self.min_dur}"
            )
            self.full = True
        else:
            self.full = False

        self.rel_attacks = np.zeros((self.num_cont_rhythm_vars, self.num_notes))
        self.deltas = None
        er_cont_rhythm.generate_continuous_attacks(self)
        er_cont_rhythm.vary_continuous_attacks(self, apply_to_durs=False)
        self.round()
        self.rel_attacks_to_rhythm(first_var_only=True)
        self.cum_attacks = self.rel_attacks.cumsum(axis=1) - self.rel_attacks
        # self.dur_deltas is the difference between the rel_attack time
        # of each grid position on each variation. (The first row is
        # the difference between the last variation and the first.)
        # It would have been better to do this directly when creating
        # the variations, and not have the somewhat useless .deltas
        # attribute above.
        # LONGTERM revise?
        self.dur_deltas = np.zeros((self.num_cont_rhythm_vars, self.num_notes))
        for var_i in range(self.num_cont_rhythm_vars):
            self.dur_deltas[var_i] = (
                self.rel_attacks[var_i]
                - self.rel_attacks[(var_i - 1) % self.num_cont_rhythm_vars]
            )

    def return_varied_rhythm(self, er, attacks, voice_i):
        def _get_grid_indices():
            indices = []
            for time_i, time in enumerate(self):
                if time in attacks:
                    indices.append(time_i)
            return indices

        rhythm_num_notes = len(attacks)
        if rhythm_num_notes == 0:
            print(f"Notice: voice {voice_i} is empty.")
            return ContinuousRhythm(er, voice_i)
        indices = _get_grid_indices()
        var_attacks = np.zeros((self.num_cont_rhythm_vars, rhythm_num_notes))
        rel_attacks = np.zeros((self.num_cont_rhythm_vars, rhythm_num_notes))
        # var_attacks[0] = list(attacks.keys())
        var_durs = np.zeros((self.num_cont_rhythm_vars, rhythm_num_notes))
        var_durs[0] = list(attacks.values())
        for var_i in range(self.num_cont_rhythm_vars):
            var_attacks[var_i] = self.cum_attacks[var_i, indices]
            rel_attacks[var_i, : rhythm_num_notes - 1] = np.diff(
                var_attacks[var_i]
            )
            rel_attacks[var_i, rhythm_num_notes - 1] = (
                self.rhythm_len - var_attacks[var_i, rhythm_num_notes - 1]
            )
            if var_i != 0:
                var_durs[var_i] = (
                    var_durs[var_i - 1] + self.dur_deltas[var_i, indices]
                )

        rhythm = ContinuousRhythm(er, voice_i)
        rhythm.rel_attacks = rel_attacks
        rhythm.durs = var_durs
        er_cont_rhythm.truncate_or_extend(rhythm)
        rhythm.round()
        rhythm.rel_attacks_to_rhythm()
        return rhythm


def rhythms_handler(er):
    """According to the parameters in er, return rhythms.
    """

    if er.rhythms_specified_in_midi:
        rhythms = er_midi.get_rhythms_from_midi(er)
    else:
        rhythms = []
        if er.cont_rhythms == "grid":
            er.grid = Grid(er)
        for voice_i in range(er.num_voices):
            rhythms.append(generate_rhythm1(er, voice_i, prev_rhythms=rhythms))

    if not any(rhythms):

        class EmptyRhythmsError(Exception):
            pass

        raise EmptyRhythmsError(
            "No notes in any rhythms! This is a bug in the script."
        )

    update_pattern_voice_leading_order(er, rhythms)

    return rhythms


def get_attack_order(er):

    end_time = max(er.pattern_len)

    class NoMoreAttacksError(Exception):
        pass

    def _get_next_attack():
        next_attack = end_time ** 2
        increment_i = -1
        for i in er.voice_order:
            try:
                next_attack_in_voice = attacks[i][voice_is[i]]
            except IndexError:
                continue
            if next_attack_in_voice < next_attack:
                next_attack = next_attack_in_voice
                increment_i = i
        if next_attack == end_time ** 2:
            raise NoMoreAttacksError("No more attacks found")
        voice_is[increment_i] += 1
        return next_attack, increment_i

    attacks = [list(rhythm.keys()) for rhythm in er.rhythms]
    voice_is = [0 for i in range(er.num_voices)]
    ordered_attacks = []
    while True:
        try:
            next_attack, voice_i = _get_next_attack()
        except NoMoreAttacksError:
            break
        if next_attack >= end_time:
            break
        ordered_attacks.append((voice_i, next_attack))

    return ordered_attacks


def rest_before_next_note(rhythm, attack, min_rest_len):
    release = attack + rhythm[attack]
    for next_attack in sorted(rhythm.keys()):
        if next_attack >= release:
            break

    gap = next_attack - release
    if gap >= min_rest_len:
        return True

    return False
