import collections
import copy
import fractions
import itertools
import math
import random

import src.er_misc_funcs as er_misc_funcs
import src.er_prob_funcs as er_prob_funcs
import src.er_notes as er_notes

# QUESTION why does program change sometimes not apply to first note when
#           changing midi files imported from logic?

# LONGTERM extend durations transformer
# LONGTERM add an arbitrary note attribute condition (e.g., note.velocity > 64)
# LONGTERM add:
#       - random displacement transformer
#       - diatonic melodic inversion transformer?
#       - insert tempo change transformer
#       - oscillating range transformer
#       - abbreviate/extend score transformer
#       - quantize transformer

# TODO change "filter" to "transformer" for transformers?
EXEMPTIONS_DESC = """'Exemptions' specify notes that the filter will never be
applied to. Exemptions can either be 'metric', meaning that notes attacked on
certain beats are exempt, or 'counting', meaning that notes are counted, and
every 'nth' note is exempt.
"""
EXEMPT_BEATS_DESC = """Beats to exempt from the filter. Zero-indexed (so the
first beat is 0). See also 'Exempt beats modulo' and 'Exempt comma'."""


def _get_prob_funcs():
    """Gets the possible probability functions from er_prob_funcs.py.

    """
    out = []
    for var in vars(er_prob_funcs):
        if var == "NullProbFunc":
            out.append(var)
        if var in ("ProbFunc", "NonStaticFunc", "OscFunc"):
            continue
        try:
            yes = issubclass(
                getattr(er_prob_funcs, var), er_prob_funcs.ProbFunc
            )
        except TypeError:
            continue
        if yes:
            out.append(var)
    return out


def null_condition(*args, **kwargs):  # pylint: disable=unused-argument
    return True


class ChangeFuncError(Exception):
    pass


class Changer(er_prob_funcs.AttributeAdder):
    pretty_name = "Changer"
    description = ""

    def __init__(
        self,
        score,
        start_time=0,
        end_time=0,
        prob_func="Linear",
        condition=null_condition,
        voices=(),
        by_voice=True,
        changer_counter=None,
    ):
        if changer_counter is not None:
            changer_counter[self.pretty_name] += 1
            self.pretty_name += " " + str(changer_counter[self.pretty_name])
        self.condition = condition
        self.total_len = float(score.get_total_len())
        super().__init__()
        self.all_voice_is = score.all_voice_is
        self.num_voices = len(self.all_voice_is)
        self.tet = score.tet
        prob_funcs = vars(er_prob_funcs)
        self.require_score = False
        self.add_attribute(
            "prob_func",
            prob_funcs[prob_func](length=end_time - start_time),
            "Probability function",
            str,
            attr_val_kwargs={"possible_values": _get_prob_funcs()},
            unique=True,
        )
        self.add_attribute(
            "marked_by", "", "Only apply to notes marked by", str, unique=True
        )
        self.add_attribute(
            "start_time",
            start_time,
            "Start time",
            float,
            attr_val_kwargs={"min_value": 0, "max_value": self.total_len},
        )
        self.add_attribute(
            "end_time",
            self.total_len if end_time == 0 else end_time,
            "End time",
            float,
            attr_val_kwargs={"min_value": 0, "max_value": self.total_len},
            attr_hint=("Total length", self.total_len),
        )
        self.add_attribute("by_voice", by_voice, "By voice", bool, unique=True)
        self.add_attribute(
            "voices",
            list(range(self.num_voices)) if not voices else voices,
            "Voices",
            int,
            attr_val_kwargs={"min_value": 0, "max_value": self.num_voices - 1},
            attr_hint=("Number of voices", self.num_voices),
            display_if={"by_voice": "true"},
        )
        # MAYBE explicitly toggle between exempt beats and exempt n
        #       also, add possibility of offset for exempt n?
        self.add_attribute(
            "exemptions",
            "off",
            "Exemptions",
            str,
            attr_val_kwargs={"possible_values": ("off", "metric", "counting")},
            unique=True,
            description=EXEMPTIONS_DESC,
        )
        self.add_attribute(
            "exempt",
            (),
            "Exempt beats",
            fractions.Fraction,
            attr_val_kwargs={"min_value": 0, "max_value": -1, "sort": True},
            description=EXEMPT_BEATS_DESC,
            display_if={"exemptions": "metric"},
        )
        self.add_attribute(
            "exempt_modulo",
            4,
            "Exempt beats modulo",
            fractions.Fraction,
            attr_val_kwargs={"min_value": 0, "max_value": -1},
            unique=True,
            display_if={"exemptions": "metric"},
        )
        self.add_attribute(
            "exempt_n",
            0,
            "Exempt num notes",
            int,
            attr_val_kwargs={"min_value": 0, "max_value": -1},
            display_if={"exemptions": "counting"},
        )
        self.add_attribute(
            "exempt_comma",
            fractions.Fraction(1, 128),
            "Exempt comma",
            fractions.Fraction,
            attr_val_kwargs={"min_value": 0, "max_value": -1},
            unique=True,
            display_if={"exemptions": "metric"},
        )
        self.add_attribute(
            "invert_exempt",
            False,
            "Invert exempt beats",
            bool,
            unique=True,
            display_if={"exemptions": ("metric", "counting")},
        )

    def validate(self, *args):
        if self.exempt_modulo == 0:  # pylint: disable=no-member
            exemptions = list(
                itertools.accumulate(self.exempt_n)  # pylint: disable=no-member
            )
            self.mod_n = exemptions[  # pylint: disable=attribute-defined-outside-init
                -1
            ]
            self.exemptions_n = (  # pylint: disable=attribute-defined-outside-init
                [0,] + exemptions[:-1]
            )
        else:
            self.mod_n = None  # pylint: disable=attribute-defined-outside-init
        if self.marked_by:  # pylint: disable=no-member
            try:
                score = args[0]
                skip_marked_by_validation = False
            except IndexError:
                skip_marked_by_validation = True
            if not skip_marked_by_validation:
                if not isinstance(score, er_notes.Score):
                    raise NotImplementedError()
                no_marked_transformations = True
                for note in score:
                    try:
                        if self.marked_by in note.transformations_:
                            no_marked_transformations = False
                            break
                    except AttributeError:
                        continue
                if no_marked_transformations:
                    raise ChangeFuncError(
                        f"No notes transformed by {self.marked_by}"  # pylint: disable=no-member
                    )

    def beat_exempt(self, attack_time):
        mod_attack_time = (
            attack_time % self.exempt_modulo  # pylint: disable=no-member
        )
        exempt_i = er_misc_funcs.binary_search(
            self.exempt,  # pylint: disable=no-member
            mod_attack_time,
            not_found="nearest",
        )
        mod_diff = min(
            abs(
                self.exempt[exempt_i]  # pylint: disable=no-member
                - mod_attack_time
            ),
            abs(
                self.exempt[exempt_i]  # pylint: disable=no-member
                + self.exempt_modulo  # pylint: disable=no-member
                - mod_attack_time
            ),
        )
        if mod_diff < self.exempt_comma:  # pylint: disable=no-member
            if self.invert_exempt:  # pylint: disable=no-member
                return False
            return True
        if self.invert_exempt:  # pylint: disable=no-member
            return True
        return False

    def n_exempt(self, i):
        mod_i = i % self.mod_n
        if mod_i in self.exemptions_n:
            if self.invert_exempt:  # pylint: disable=no-member
                return False
            return True
        if self.invert_exempt:  # pylint: disable=no-member
            return True
        return False

    def _apply_by_voice(self, score):
        exemptions = (
            self.exempt  # pylint: disable=no-member
            and self.exempt[0] is not None  # pylint: disable=no-member
        )
        for interface_voice_i in self.voices:  # pylint: disable=no-member
            voice_i = self.all_voice_is[interface_voice_i]
            try:
                voice = score.voices[voice_i]
            except IndexError:
                breakpoint()
            notes_to_change = []
            start_time, end_time = self.get(voice_i, "start_time", "end_time")
            # prob_func is a misnomer since it's a class!
            if "length" in vars(self.prob_func):  # pylint: disable=no-member
                self.prob_func.length = (  # pylint: disable=no-member
                    end_time - start_time
                )

            for note_object_i, note_object in enumerate(voice):
                attack_time = note_object.attack_time
                if attack_time < start_time:
                    continue
                if exemptions:
                    if self.mod_n is None and self.beat_exempt(attack_time):
                        continue
                    if self.mod_n and self.n_exempt(note_object_i):
                        continue
                if attack_time >= end_time:
                    break
                if not self.condition(note_object):
                    continue
                try:
                    if (
                        self.marked_by
                        and self.marked_by not in note_object.transformations_
                    ):
                        continue
                except AttributeError:
                    continue

                filter_time = attack_time - start_time
                func_result = self.prob_func.calculate(  # pylint: disable=no-member
                    filter_time, random.random(), voice_i
                )
                if func_result:
                    notes_to_change.append(note_object)

            if self.require_score:
                self.change_func(  # pylint: disable=no-member
                    score, voice_i, notes_to_change
                )
            else:
                self.change_func(  # pylint: disable=no-member
                    voice, notes_to_change
                )

    def _apply_by_score(self, score):
        notes_to_change = []
        start_time, end_time = self.get(0, "start_time", "end_time")
        exemptions = (
            self.exempt  # pylint: disable=no-member
            and self.exempt[0] is not None  # pylint: disable=no-member
        )
        if "length" in vars(self.prob_func):  # pylint: disable=no-member
            self.prob_func.length = (  # pylint: disable=no-member
                end_time - start_time
            )
        for notes in score:
            attack_time = notes[0].attack_time
            if attack_time < start_time:
                continue
            if exemptions and self.beat_exempt(attack_time):
                continue
            if attack_time >= end_time:
                break
            notes_to_process = [
                note
                for note in notes
                if self.condition(note)
                and not note.attack_time
                % self.exempt_modulo  # pylint: disable=no-member
                in self.exempt  # pylint: disable=no-member
            ]
            if not notes_to_process:
                continue
            filter_time = attack_time - start_time
            func_result = self.prob_func.calculate(  # pylint: disable=no-member
                filter_time, random.random(), 0
            )
            if func_result:
                notes_to_change += notes_to_process

        notes_by_voices = {}
        for note in notes_to_change:
            try:
                notes_by_voices[note.voice].append(note)
            except KeyError:
                notes_by_voices[note.voice] = [
                    note,
                ]

        try:
            self._process_all_voices(notes_by_voices)
        except AttributeError:
            pass

        for voice_i, notes in notes_by_voices.items():
            voice = score.voices[voice_i]
            if self.require_score:
                self.change_func(  # pylint: disable=no-member
                    score, voice_i, notes_to_change
                )
            else:
                self.change_func(voice, notes)  # pylint: disable=no-member

    def apply(self, score):
        try:
            self.validate(score)
        except AttributeError:
            pass

        try:
            self.validate_mediator()
        except AttributeError:
            pass

        try:
            self.prob_func.reset()
        except AttributeError:
            pass

        if self.by_voice:  # pylint: disable=no-member
            self._apply_by_voice(score)

        else:
            self._apply_by_score(score)


class Mediator(er_prob_funcs.AttributeAdder):
    def __init__(self):
        super().__init__()
        # QUESTION: anywhere to put the next three lines where they will
        # only be calculated once (instead of when creating each instance?)
        self.func_strs = [
            "thru",
            "linear",
            "quadratic",
            "linear_osc",
            "saw",
            # "saw_decreasing",
            "cosine",
            # "linear_decreasing", "quadratic_decreasing",
        ]
        self.cyclic_func_strs = [
            "linear_osc",
            "saw",
            # "saw_decreasing",
            "cosine",
        ]
        self.noncyclic_func_strs = [
            f
            for f in self.func_strs
            if f not in self.cyclic_func_strs and f != "thru"
        ]
        self.add_attribute(
            "func_str",
            "thru",
            "Mediating function",
            str,
            attr_val_kwargs={"possible_values": self.func_strs},
            unique=True,
        )
        self.add_attribute(
            "med_start_time",
            0,
            "Mediator start time",
            fractions.Fraction,
            attr_val_kwargs={
                "min_value": 0,
                "max_value": self.total_len,  # pylint: disable=no-member
            },
            display_if={"func_str": self.noncyclic_func_strs},
        )
        self.add_attribute(
            "med_end_time",
            self.total_len,  # pylint: disable=no-member
            "Mediator end time",
            fractions.Fraction,
            attr_val_kwargs={
                "min_value": 0,
                "max_value": self.total_len,  # pylint: disable=no-member
            },
            attr_hint=(
                "Total length",
                self.total_len,  # pylint: disable=no-member
            ),
            display_if={"func_str": self.noncyclic_func_strs},
        )
        self.add_attribute(
            "med_period",
            4,
            "Mediator period",
            fractions.Fraction,
            attr_val_kwargs={"min_value": 0, "max_value": -1},
            display_if={"func_str": self.cyclic_func_strs},
        )
        self.add_attribute(
            "med_offset",
            0,
            "Mediator offset",
            fractions.Fraction,
            attr_val_kwargs={"min_value": 0, "max_value": -1},
            display_if={"func_str": self.cyclic_func_strs},
        )
        self.add_attribute(
            "med_decreasing",
            False,
            "Mediator decreasing",
            bool,
            unique=True,
            display_if={
                "func_str": self.cyclic_func_strs + self.noncyclic_func_strs
            },
        )

    def validate_mediator(self):
        if self.func_str == "thru":  # pylint: disable=no-member
            return True
        try:
            self.mediating_func = getattr(  # pylint: disable=attribute-defined-outside-init
                er_prob_funcs, self.func_str  # pylint: disable=no-member
            )
            # vars(er_prob_funcs)[
            #     self.func_str
            # ]
            return True
        except KeyError:
            return False

    def mediate(self, voice_i, unmediated_val, original_val, attack_time):
        if self.func_str == "thru":  # pylint: disable=no-member
            return unmediated_val

        if self.func_str in self.cyclic_func_strs:  # pylint: disable=no-member
            period, offset = self.get(voice_i, "med_period", "med_offset")
        else:
            start_time, end_time = self.get(
                voice_i, "med_start_time", "med_end_time"
            )
            period = end_time - start_time
            offset = 0
            if start_time > attack_time or end_time <= attack_time:
                return unmediated_val

        adjust = self.mediating_func(
            attack_time + offset,
            0,
            1,
            period,
            decreasing=self.med_decreasing,  # pylint: disable=no-member
        )
        return unmediated_val + (original_val - unmediated_val) * adjust


class Filter(Changer):
    pretty_name = "Pitch filter"
    description = pretty_name + " removes notes of any pitch"

    def __init__(
        self,
        score,
        start_time=0,
        end_time=0,
        prob_func="Linear",
        voices=(),
        changer_counter=None,
    ):
        super().__init__(
            score,
            start_time=start_time,
            end_time=end_time,
            prob_func=prob_func,
            voices=voices,
            changer_counter=changer_counter,
        )
        self.add_attribute(
            "adjust_dur",
            "None",
            "Adjust durations",
            str,
            attr_val_kwargs={
                "possible_values": [
                    "None",
                    "Extend_previous_notes",
                    "Subtract_duration",
                ]
            },
            unique=True,
        )
        self.add_attribute(
            "adjust_dur_comma",
            0.25,
            "Adjust durations comma",
            float,
            attr_val_kwargs={"min_value": 0, "max_value": -1},
            unique=True,
            display_if={"adjust_dur": "Extend_previous_notes"},
        )
        self.add_attribute(
            "subtract_dur_modulo",
            0,
            "Subtract durations within length",
            fractions.Fraction,
            attr_val_kwargs={"min_value": 0.001, "max_value": -1},
            unique=True,
            display_if={"adjust_dur": "Subtract_duration"},
        )
        self.dur_adjust_durs = self.dur_adjust_attack_times = None

    def _process_all_voices(self, notes_by_voices):
        if (
            self.adjust_dur != "Subtract_duration"  # pylint: disable=no-member
            or self.by_voice  # pylint: disable=no-member
        ):
            return
        self.dur_adjust_attack_times = []
        self.dur_adjust_durs = []
        dur_adjust_dict = {}
        for notes in notes_by_voices.values():
            for note in notes:
                if note.attack_time in dur_adjust_dict:
                    dur_adjust_dict[note.attack_time] = min(
                        note.dur, dur_adjust_dict[note.attack_time]
                    )
                else:
                    dur_adjust_dict[note.attack_time] = note.dur

        dur_adjustment = 0
        last_mod_attack_time = 0
        for attack_time in sorted(dur_adjust_dict.keys()):
            if self.subtract_dur_modulo:  # pylint: disable=no-member
                mod_attack_time = (
                    attack_time
                    % self.subtract_dur_modulo  # pylint: disable=no-member
                )
                if mod_attack_time < last_mod_attack_time:
                    dur_adjustment = -mod_attack_time
                last_mod_attack_time = mod_attack_time
            dur_adjustment -= dur_adjust_dict[attack_time]
            self.dur_adjust_attack_times.append(attack_time)
            self.dur_adjust_durs.append(dur_adjustment)

    def change_func(self, voice, notes_to_change):

        if (
            self.adjust_dur != "None"  # pylint: disable=no-member
            and voice.is_polyphonic()
        ):
            print(
                er_misc_funcs.add_line_breaks(
                    f"Notice: adjust durations in polyphonic voice {voice.voice_i} "
                    "may produce unexpected results.",
                    indent_width=8,
                    indent_type="all",
                )
            )

        voice.filtered_notes = er_notes.Voice(
            voice_i=voice.voice_i, tet=voice.tet, voice_range=voice.range
        )

        if (
            self.adjust_dur == "Subtract_duration"  # pylint: disable=no-member
            and self.by_voice  # pylint: disable=no-member
        ):
            dur_adjustment = 0
            self.dur_adjust_attack_times = []
            self.dur_adjust_durs = []
            last_mod_attack_time = 0
        for note in notes_to_change:
            if (
                self.adjust_dur  # pylint: disable=no-member
                == "Extend_previous_notes"
            ):
                prev_note = voice.get_prev_note(note.attack_time)
                if prev_note and (
                    note.attack_time - prev_note.attack_time - prev_note.dur
                    < self.adjust_dur_comma  # pylint: disable=no-member
                ):
                    prev_note.dur = (
                        note.attack_time + note.dur - prev_note.attack_time
                    )
            if (
                self.adjust_dur  # pylint: disable=no-member
                == "Subtract_duration"
                and self.by_voice  # pylint: disable=no-member
            ):
                if self.subtract_dur_modulo:  # pylint: disable=no-member
                    mod_attack_time = (
                        note.attack_time
                        % self.subtract_dur_modulo  # pylint: disable=no-member
                    )
                    if mod_attack_time < last_mod_attack_time:
                        dur_adjustment = -mod_attack_time
                    last_mod_attack_time = mod_attack_time
                dur_adjustment -= note.dur
                self.dur_adjust_attack_times.append(note.attack_time)
                self.dur_adjust_durs.append(dur_adjustment)
            voice.filtered_notes.add_note_object(
                copy.copy(note), update_sort=False
            )
            voice.remove_note_object(note)
        voice.filtered_notes.update_sort()
        if self.adjust_dur == "Subtract_duration":  # pylint: disable=no-member
            i = -1
            notes_to_move = []
            dur_adjustment = 0
            for note in voice:
                try:
                    while (
                        note.attack_time >= self.dur_adjust_attack_times[i + 1]
                    ):
                        i += 1
                        dur_adjustment = self.dur_adjust_durs[i]
                except IndexError:
                    pass
                notes_to_move.append((note, note.attack_time + dur_adjustment))
            for note, new_attack_time in notes_to_move:
                voice.move_note(note, new_attack_time, update_sort=False)
            voice.update_sort()


class RangeFilter(Filter):
    pretty_name = "Range filter"
    description = (
        pretty_name
        + " removes notes whose pitches lie outside the specified range(s)"
    )

    def __init__(
        self,
        score,
        start_time=0,
        end_time=0,
        prob_func="Linear",
        voices=(),
        filter_range=((0, 127),),
        # filter_range=(0, 127),
        changer_counter=None,
    ):
        def pitch_in_range(note_object):
            for range_tuple in self.filter_range:  # pylint: disable=no-member
                if range_tuple[0] <= note_object.pitch <= range_tuple[1]:
                    return False
            return True

        super().__init__(
            score,
            start_time=start_time,
            end_time=end_time,
            prob_func=prob_func,
            voices=voices,
            changer_counter=changer_counter,
        )
        self.add_attribute(
            "filter_range",
            filter_range,
            "Range(s) to pass through filter",
            int,
            attr_val_kwargs={"min_value": 0, "max_value": -1, "tuple_of": -2},
            unique=True,  # TODO not sure this should be unique
        )
        self.condition = pitch_in_range


class OscillatingRangeFilter(Filter):
    pretty_name = "Oscillating range filter"
    description = (
        pretty_name
        + " removes notes whose pitches lie outside of a range whose bounds "
        "oscillate according to parameters that you control."
    )

    def pitch_in_osc_range(self, note_object):
        range_width = (
            self.bottom_range[1]  # pylint: disable=no-member
            - self.bottom_range[0]  # pylint: disable=no-member
        )
        l_bound = round(
            er_prob_funcs.linear_osc(
                note_object.attack_time
                + self.osc_offset,  # pylint: disable=no-member
                self.bottom_range[0],  # pylint: disable=no-member
                self.bottom_range[0]  # pylint: disable=no-member
                + self.range_size,  # pylint: disable=no-member
                self.osc_period,  # pylint: disable=no-member
            )
        )
        if l_bound <= note_object.pitch <= l_bound + range_width:
            return False
        return True

    def __init__(
        self,
        score,
        start_time=0,
        end_time=0,
        prob_func="Linear",
        voices=(),
        bottom_range=(0, 127),
        range_size=36,
        osc_period=8,
        osc_offset=0,
        changer_counter=None,
    ):

        super().__init__(
            score,
            start_time=start_time,
            end_time=end_time,
            prob_func=prob_func,
            voices=voices,
            changer_counter=changer_counter,
        )
        self.add_attribute(
            "bottom_range",
            bottom_range,
            "Range at bottom of oscillation",
            int,
            attr_val_kwargs={"min_value": 0, "max_value": -1, "tuple_of": 2},
            unique=True,
        )
        self.add_attribute(
            "range_size",
            range_size,
            "Size in pitches of oscillation",
            int,
            attr_val_kwargs={"min_value": 0, "max_value": -1},
            unique=True,
        )
        self.add_attribute(
            "osc_period",
            osc_period,
            "Oscillation period",
            int,
            attr_val_kwargs={"min_value": 0.01, "max_value": -1},
            unique=True,
        )
        self.add_attribute(
            "osc_offset",
            osc_offset,
            "Oscillation period offset",
            int,
            attr_val_kwargs={"min_value": 0, "max_value": -1},
            unique=True,
        )
        self.condition = self.pitch_in_osc_range


class OddPitchFilter(Filter):
    pretty_name = "Odd pitch filter"
    description = pretty_name + " removes notes of odd pitch"

    def __init__(
        self,
        score,
        start_time=0,
        end_time=0,
        prob_func="Linear",
        voices=(),
        changer_counter=None,
    ):
        def odd_pitch(note_object):
            if note_object.pitch % 2 == 1:
                return True
            return False

        super().__init__(
            score,
            start_time=start_time,
            end_time=end_time,
            prob_func=prob_func,
            voices=voices,
            changer_counter=changer_counter,
        )
        self.condition = odd_pitch


class EvenPitchFilter(Filter):
    pretty_name = "Even pitch filter"
    description = pretty_name + " removes notes of even pitch"

    def __init__(
        self,
        score,
        start_time=0,
        end_time=0,
        prob_func="Linear",
        voices=(),
        changer_counter=None,
    ):
        def even_pitch(note_object):
            if note_object.pitch % 2 == 0:
                return True
            return False

        super().__init__(
            score,
            start_time=start_time,
            end_time=end_time,
            prob_func=prob_func,
            voices=voices,
            changer_counter=changer_counter,
        )
        self.condition = even_pitch


class FilterSelectedPCs(Filter):
    pretty_name = "Selected pitch-class filter"
    description = pretty_name + " removes notes of the selected pitch-classes"

    def __init__(
        self,
        score,
        start_time=0,
        end_time=0,
        prob_func="Linear",
        voices=(),
        selected_pcs=(),
        changer_counter=None,
    ):
        super().__init__(
            score,
            start_time=start_time,
            end_time=end_time,
            prob_func=prob_func,
            voices=voices,
            changer_counter=changer_counter,
        )
        self.condition = self.pitch_in_selected_pcs
        self.add_attribute(
            "selected_pcs",
            selected_pcs,
            "Pitch-classes to filter",
            int,
            attr_val_kwargs={"min_value": 0, "max_value": self.tet - 1},
            attr_hint=("TET", self.tet),
        )

    def pitch_in_selected_pcs(self, note_object):
        if (
            note_object.pitch % self.tet
            in self.selected_pcs  # pylint: disable=no-member
        ):
            return True
        return False


# We don't name this class 'Transformer' because we don't want it to show
#   up in the interface
class TransformBase(Changer):
    pretty_name = "Transformer"

    def __init__(
        self,
        score,
        start_time=0,
        end_time=0,
        prob_func="Linear",
        voices=(),
        changer_counter=None,
    ):
        super().__init__(
            score,
            start_time=start_time,
            end_time=end_time,
            prob_func=prob_func,
            voices=voices,
            changer_counter=changer_counter,
        )

    def mark_note(self, note):
        """Marks notes that have been transformed by appending name of
        transformer to note.transformations_ list. If note has not been
        transformed, it will not have a note.transformations_ list and
        so accessing it will raise an AttributeError.

        This function should be called for each note by the change_func()
        of each transformer.
        """
        try:
            note.transformations_.append(self.pretty_name)
        except AttributeError:
            note.transformations_ = [
                self.pretty_name,
            ]


class ForcePitchTransformer(TransformBase):
    pretty_name = "Force pitch transformer"

    def __init__(
        self,
        score,
        start_time=0,
        end_time=0,
        prob_func="Linear",
        voices=(),
        force_pitches=(),
        changer_counter=None,
    ):
        super().__init__(
            score,
            start_time=start_time,
            end_time=end_time,
            prob_func=prob_func,
            voices=voices,
            changer_counter=changer_counter,
        )
        self.add_attribute(
            "force_pitches",
            force_pitches,
            "Pitches to force",
            int,
            attr_val_kwargs={"min_value": 1, "max_value": -1},
        )

    def change_func(  # pylint: disable=unused-argument
        self, voice, notes_to_change
    ):
        for note in notes_to_change:
            pitch_to_force = random.choice(
                self.force_pitches  # pylint: disable=no-member
            )
            note.pitch = pitch_to_force
            self.mark_note(note)

    def validate(self, *args):
        super().validate(*args)
        if not er_misc_funcs.no_empty_lists(
            self.force_pitches  # pylint: disable=no-member
        ):
            raise ChangeFuncError("'Pitches to force' contains an empty list.")


class ForcePitchClassesTransformer(TransformBase):
    pretty_name = "Force pitch-classes transformer"

    def __init__(
        self,
        score,
        start_time=0,
        end_time=0,
        prob_func="Static",
        voices=(),
        force_pcs=(),
        changer_counter=None,
    ):
        super().__init__(
            score,
            start_time=start_time,
            end_time=end_time,
            prob_func=prob_func,
            voices=voices,
            changer_counter=changer_counter,
        )
        self.add_attribute(
            "force_pcs",
            force_pcs,
            "Pitch-classes to force",
            int,
            attr_val_kwargs={
                "min_value": 0,
                "max_value": 11,
                "iter_of_iters": True,
            },
        )

    def change_func(self, voice, notes_to_change):
        voice_i = voice.voice_i
        pcs = self.get(voice_i, "force_pcs")
        for note in notes_to_change:
            sign = random.choice([1, -1])
            adjust = 0
            pitch = note.pitch
            while True:
                if (pitch + adjust * sign) % voice.tet in pcs:
                    note.pitch = pitch + adjust * sign
                    break
                if (pitch + adjust * sign * -1) % voice.tet in pcs:
                    note.pitch = pitch + adjust * sign * -1
                    break
                adjust += 1
            self.mark_note(note)

    def validate(self, *args):
        super().validate(*args)
        if not er_misc_funcs.no_empty_lists(
            self.force_pcs  # pylint: disable=no-member
        ):
            raise ChangeFuncError(
                "'Pitch-classes to force' contains an empty list."
            )


class VelocityTransformer(TransformBase, Mediator):
    pretty_name = "Velocity transformer"

    def __init__(self, score, changer_counter=None):
        super().__init__(
            score, start_time=0, end_time=0, prob_func="Static", voices=()
        )
        self.add_attribute(
            "trans_type",
            "Scale",
            "Velocity transform type",
            str,
            attr_val_kwargs={"possible_values": ["Scale", "Fix"]},
            unique=True,
        )
        self.add_attribute(
            "scale_by",
            1,
            "Scale factor",
            float,
            attr_val_kwargs={"min_value": 0, "max_value": -1},
            display_if={"trans_type": "Scale"},
        )
        self.add_attribute(
            "fix_to",
            64,
            "Fix velocity to",
            int,
            attr_val_kwargs={"min_value": 0, "max_value": 127},
            display_if={"trans_type": "Fix"},
        )
        self.add_attribute(
            "humanize",
            6,
            "Humanize +/-",
            int,
            attr_val_kwargs={"min_value": 0, "max_value": 127},
        )

    def change_func(self, voice, notes_to_change):
        voice_i = voice.voice_i
        if self.trans_type == "Scale":  # pylint: disable=no-member
            scale_by, humanize = self.get(voice_i, "scale_by", "humanize")
            for note in notes_to_change:
                unmediated_vel = round(
                    max(0, min(127, note.velocity * scale_by))
                )
                mediated_vel = round(
                    self.mediate(
                        voice_i, unmediated_vel, note.velocity, note.attack_time
                    )
                )
                note.velocity = random.randrange(
                    max(mediated_vel - humanize, 0),
                    min(mediated_vel + humanize + 1, 128),
                )
                self.mark_note(note)

        elif self.trans_type == "Fix":  # pylint: disable=no-member
            fix_to, humanize = self.get(voice_i, "fix_to", "humanize")
            for note in notes_to_change:
                unmediated_vel = round(max(0, min(127, fix_to)))
                mediated_vel = round(
                    self.mediate(
                        voice_i, unmediated_vel, note.velocity, note.attack_time
                    )
                )
                try:
                    note.velocity = random.randrange(
                        max(mediated_vel - humanize, 0),
                        min(mediated_vel + humanize + 1, 128),
                    )
                except ValueError:
                    breakpoint()
                self.mark_note(note)


class ChangeDurationsTransformer(TransformBase, Mediator):
    pretty_name = "Change durations transformer"

    def __init__(self, score, changer_counter=None):
        super().__init__(
            score, start_time=0, end_time=0, prob_func="Static", voices=()
        )
        self.add_attribute(
            "trans_type",
            "Scale",
            "Change durations type",
            str,
            attr_val_kwargs={"possible_values": ["Scale", "By_fixed_amount"]},
            unique=True,
        )
        self.add_attribute(
            "scale_by",
            1,
            "Scale factor",
            float,
            attr_val_kwargs={"min_value": 0, "max_value": -1},
            display_if={"trans_type": "Scale"},
        )
        self.add_attribute(
            "fix_amount",
            1,
            "Fixed amount",
            fractions.Fraction,
            attr_val_kwargs={"min_value": -4192, "max_value": -1},
            display_if={"trans_type": "By_fixed_amount"},
        )
        self.add_attribute(
            "min_dur",
            0,
            "Minimum dur",
            fractions.Fraction,
            attr_val_kwargs={"min_value": 0, "max_value": -1},
        )
        self.add_attribute(
            "min_dur_treatment",
            "Enforce_min_dur",
            "Treatment of notes below minumum dur",
            str,
            attr_val_kwargs={"possible_values": ["Enforce_min_dur", "Delete"]},
            unique=True,
        )

    def change_func(self, voice, notes_to_change):
        voice_i = voice.voice_i
        if self.trans_type == "Scale":  # pylint: disable=no-member
            scale_by = self.get(voice_i, "scale_by")
        elif self.trans_type == "By_fixed_amount":  # pylint: disable=no-member
            fix_amount = self.get(voice_i, "self.fix_amount")
        min_dur = self.get(voice_i, "min_dur")
        for note in notes_to_change:
            try:
                unmediated_dur = note.dur * scale_by
            except NameError:
                unmediated_dur = note.dur + fix_amount
            note.dur = fractions.Fraction(
                self.mediate(
                    voice_i, unmediated_dur, note.dur, note.attack_time
                )
            ).limit_denominator(2048)
            if (
                note.dur < min_dur
                and self.min_dur_treatment  # pylint: disable=no-member
                == "Enforce_min_dur"
            ):
                note.dur = min_dur
            elif note.dur < min_dur or note.dur <= 0:
                try:
                    notes_to_remove.append(note)
                except NameError:
                    notes_to_remove = [
                        note,
                    ]
            self.mark_note(note)

        if (
            self.min_dur_treatment  # pylint: disable=no-member
            == "Enforce_min_dur"
        ):
            return

        for note in notes_to_remove:
            voice.remove_note_object(note)


class RandomOctaveTransformer(TransformBase):
    pretty_name = "Random octave transformer"

    def __init__(
        self,
        score,
        start_time=0,
        end_time=0,
        prob_func="Linear",
        voices=(),
        ranges=0,
        avoid_orig_oct=False,
        changer_counter=None,
    ):
        super().__init__(
            score,
            start_time=start_time,
            end_time=end_time,
            prob_func=prob_func,
            voices=voices,
            changer_counter=changer_counter,
        )
        self.add_attribute(
            "ranges",
            ranges,
            "Voice ranges",
            int,
            attr_val_kwargs={
                "min_value": 0,
                "max_value": -1,
                "tuple_of": 2,
                "iter_of_iters": True,
            },
            attr_hint="If voice ranges are 0, they are taken from Voice "
            "objects if possible",
        )
        self.add_attribute(
            "avoid_orig_oct",
            avoid_orig_oct,
            "Avoid original octave if possible",
            bool,
        )

    def change_func(self, voice, notes_to_change):
        voice_i = voice.voice_i
        voice_range, avoid_orig_oct = self.get(
            voice_i, "ranges", "avoid_orig_oct"
        )
        if isinstance(voice_range, tuple):
            voice_range = sorted(voice_range)
        if not voice_range:
            voice_range = voice.range
            if voice_range is None:
                print(
                    f"        No voice_range specified in voice {voice_i}, "
                    "defaulting to (36, 84)"
                )
                voice_range = (36, 84)
        low, high = voice_range
        for note in notes_to_change:
            choices = []
            new_pitch = note.pitch % voice.tet
            while new_pitch <= high:
                if new_pitch >= low:
                    choices.append(new_pitch)
                new_pitch += voice.tet
            if avoid_orig_oct and note.pitch in choices and len(choices) > 1:
                choices.remove(note.pitch)
            new_pitch = random.choice(choices)
            note.pitch = new_pitch
            self.mark_note(note)


class TransposeTransformer(TransformBase):
    pretty_name = "Transpose transformer"

    def __init__(
        self,
        score,
        start_time=0,
        end_time=0,
        prob_func="Linear",
        voices=(),
        transpose=0,
        changer_counter=None,
    ):
        super().__init__(
            score,
            start_time=start_time,
            end_time=end_time,
            prob_func=prob_func,
            voices=voices,
            changer_counter=changer_counter,
        )
        self.add_attribute(
            "transpose",
            transpose,
            "Interval of transposition",
            int,
            attr_val_kwargs={
                "min_value": self.tet * -6,
                "max_value": self.tet * 6,
            },
        )
        self.add_attribute("preserve", False, "Preserve original note", bool)
        self.add_attribute(
            "trans_type",
            "Standard",
            "Transposition type",
            str,
            attr_val_kwargs={
                "possible_values": ["Standard", "Cumulative", "Random"]
            },
            unique=True,
        )
        self.add_attribute(
            "bound",
            0,
            "Cumulative bound",
            int,
            attr_val_kwargs={"min_value": 0, "max_value": self.tet * 6},
            attr_hint="After the cumulative transposition reaches the bound "
            "(inclusive; either up or down), it will be shifted an octave "
            "up/down",
            display_if={"trans_type": "Cumulative"},
        )
        self.add_attribute(
            "seg_dur",
            4,
            "Transposition segment duration",
            fractions.Fraction,
            attr_val_kwargs={"min_value": 0, "max_value": -1},
            attr_hint="If non-zero, then transposition segment number of "
            "notes is ignored",
            display_if={"trans_type": ("Cumulative", "Random")},
        )
        self.add_attribute(
            "seg_card",
            0,
            "Transposition segment number of notes",
            int,
            attr_val_kwargs={"min_value": 1, "max_value": -1},
            display_if={"trans_type": ("Cumulative", "Random")},
        )
        self._count_dict = collections.Counter()

    def standard(self, voice, notes_to_change):
        voice_i = voice.voice_i
        transpose, preserve = self.get(voice_i, "transpose", "preserve")
        for note in notes_to_change:
            if preserve:
                note_copy = copy.copy(note)
                note_copy.pitch += transpose
                voice.add_note_object(note_copy, update_sort=False)
                self.mark_note(note_copy)
                self.mark_note(note)
            else:
                note.pitch += transpose
                self.mark_note(note)
        if preserve:
            voice.update_sort()

    def get_seg_i(self, voice_i, note):
        seg_dur, seg_card = self.get(voice_i, "seg_dur", "seg_card")
        if seg_dur:
            seg_i = int(note.attack_time // seg_dur)
        else:
            seg_i = self._count_dict[voice_i] // seg_card
            self._count_dict[voice_i] += 1
        return seg_i

    def cumulative(self, voice, notes_to_change):
        voice_i = voice.voice_i
        transpose, bound, preserve = self.get(
            voice_i, "transpose", "bound", "preserve"
        )

        for note in notes_to_change:
            seg_i = self.get_seg_i(voice_i, note)
            cum_trans = transpose * seg_i
            if bound:
                if cum_trans > 0:
                    while cum_trans > bound:
                        cum_trans -= voice.tet
                elif cum_trans < 0:
                    while cum_trans < -bound:
                        cum_trans += voice.tet
            # note.pitch += cum_trans
            if preserve:
                note_copy = copy.copy(note)
                note_copy.pitch += cum_trans
                voice.add_note_object(note_copy, update_sort=False)
                self.mark_note(note_copy)
                self.mark_note(note)
            else:
                note.pitch += cum_trans
                self.mark_note(note)
        if preserve:
            voice.update_sort()

    def build_rand_trans(self):
        self.rand_trans = []  # pylint: disable=attribute-defined-outside-init
        length = (
            1
            if not self.by_voice  # pylint: disable=no-member
            else self.num_voices
        )
        for voice_i in range(length):
            self.rand_trans.append([])
            if (
                self.by_voice  # pylint: disable=no-member
                and voice_i not in self.voices  # pylint: disable=no-member
            ):
                continue
            transpose, seg_dur = self.get(voice_i, "transpose", "seg_dur")
            if seg_dur:
                time = 0
                while time < self.total_len:
                    self.rand_trans[-1].append(
                        random.randrange(-transpose, transpose + 1)
                    )
                    time += seg_dur
            else:
                # Thus function doesn't have access to how many
                # segments there will actually be, but we can assume
                # that no one will notice a repeating pattern of 1024!
                seg_i = 0
                while seg_i < 1024:
                    self.rand_trans[-1].append(
                        random.randrange(-transpose, transpose + 1)
                    )
                    seg_i += 1

    def random(self, voice, notes_to_change):
        try:
            self.rand_trans
        except AttributeError:
            self.build_rand_trans()
        voice_i = voice.voice_i
        rand_trans = self.rand_trans[voice_i % len(self.rand_trans)]
        preserve = self.get(voice_i, "preserve")
        for note in notes_to_change:
            seg_i = self.get_seg_i(voice_i, note)
            transpose = rand_trans[seg_i % len(rand_trans)]
            if preserve:
                note_copy = copy.copy(note)
                note_copy.pitch += transpose
                voice.add_note_object(note_copy, update_sort=False)
                self.mark_note(note_copy)
                # QUESTION should the original note be marked in this case?
                self.mark_note(note)
            else:
                note.pitch += transpose
                self.mark_note(note)
        if preserve:
            voice.update_sort()

    def change_func(self, voice, notes_to_change):
        if self.trans_type == "Standard":  # pylint: disable=no-member
            self.standard(voice, notes_to_change)
        elif self.trans_type == "Cumulative":  # pylint: disable=no-member
            self.cumulative(voice, notes_to_change)
        elif self.trans_type == "Random":  # pylint: disable=no-member
            self.random(voice, notes_to_change)
        else:
            raise ChangeFuncError(
                "Unknown or non-implemented transposition type."
            )


class ChannelTransformer(TransformBase):
    pretty_name = "Channel transformer"

    def __init__(
        self,
        score,
        start_time=0,
        end_time=0,
        prob_func="Linear",
        voices=(),
        dest_channels=(),
        changer_counter=None,
    ):
        super().__init__(
            score,
            start_time=start_time,
            end_time=end_time,
            prob_func=prob_func,
            voices=voices,
            changer_counter=changer_counter,
        )
        self.add_attribute(
            "dest_channels",
            dest_channels,
            "Destination channels",
            int,
            attr_val_kwargs={
                "min_value": 0,
                "max_value": 15,
                "iter_of_iters": True,
            },
        )

    def change_func(self, voice, notes_to_change):
        voice_i = voice.voice_i
        dest_channels = self.get(voice_i, "dest_channels")
        for note in notes_to_change:
            note.choir = random.choice(dest_channels)
            self.mark_note(note)


class ChannelExchangerTransformer(TransformBase):
    pretty_name = "Channel exchanger transformer"

    def __init__(
        self,
        score,
        start_time=0,
        end_time=0,
        prob_func="Linear",
        voices=(),
        channel_pairs=(),
        changer_counter=None,
    ):
        super().__init__(
            score,
            start_time=start_time,
            end_time=end_time,
            prob_func=prob_func,
            voices=voices,
            changer_counter=changer_counter,
        )
        self.add_attribute(
            "channel_pairs",
            channel_pairs,
            "Channel source/destination pairs",
            int,
            attr_val_kwargs={"min_value": 0, "max_value": 15, "tuple_of": -2},
        )

    def change_func(  # pylint: disable=unused-argument
        self, voice, notes_to_change
    ):
        try:
            source_channels, dest_channels = zip(
                *self.channel_pairs  # pylint: disable=no-member
            )
        except ValueError as exc:
            raise ChangeFuncError(
                "Invalid value for channel source/destination pairs... "
                "perhaps they are empty?"
            ) from exc
        # voice_i = voice.voice_i
        for note in notes_to_change:
            try:
                i = source_channels.index(note.choir)
            except ValueError:
                continue
            note.choir = dest_channels[i]
            self.mark_note(note)


class ShepherdTransformer(TransformBase):
    pretty_name = "Shepherd tone transformer"

    def __init__(
        self,
        score,
        start_time=0,
        end_time=0,
        prob_func="NullProbFunc",
        voices=(),
        changer_counter=None,
    ):
        super().__init__(
            score,
            start_time=start_time,
            end_time=end_time,
            prob_func=prob_func,
            voices=voices,
            changer_counter=changer_counter,
        )
        self.tet = score.tet
        self.add_attribute(
            "pitch_center",
            5 * score.tet,
            "Pitch center",
            int,
            attr_val_kwargs={"min_value": 0, "max_value": 10 * score.tet},
        )
        self.add_attribute(
            "flat_peak",
            score.tet,
            "Size of flat peak in semitones",
            int,
            attr_val_kwargs={"min_value": 1, "max_value": 10 * score.tet},
        )
        self.add_attribute(
            "num_octaves",
            6,
            "Number of octaves",
            int,
            attr_val_kwargs={"min_value": 0, "max_value": -1},
        )
        self.add_attribute(
            "shape",
            "quadratic",
            "Velocity curve shape",
            str,
            attr_val_kwargs={"possible_values": ["quadratic", "linear"]},
            unique=True,
        )
        # self.add_attribute(
        #     "new_tracks",
        #     True,
        #     "Add new tracks for doubled notes",
        #     bool,
        #     unique=True,
        # ) # LONGTERM
        self.require_score = True
        self.vel_func = self.bottom_pitch = self.top_pitch = None
        self.bottom_flat_peak = self.top_flat_peak = None

    def validate(self, *args):
        super().validate(*args)

        def _get_bottom(pitch_center, num_octaves):
            return max(math.floor(pitch_center - num_octaves * self.tet / 2), 0)

        def _get_top(pitch_center, num_octaves):
            return min(
                math.ceil(pitch_center + num_octaves * self.tet / 2),
                math.floor(self.tet * 127 / 12),
            )

        self.bottom_pitch = []
        self.top_pitch = []
        self.bottom_flat_peak = []
        self.top_flat_peak = []
        for i in range(
            max(
                len(self.pitch_center),  # pylint: disable=no-member
                len(self.num_octaves),  # pylint: disable=no-member
            ),
        ):
            pitch_center, num_octaves, flat_peak = self.get(
                i, "pitch_center", "num_octaves", "flat_peak"
            )
            self.bottom_pitch.append(_get_bottom(pitch_center, num_octaves))
            self.top_pitch.append(_get_top(pitch_center, num_octaves))
            self.bottom_flat_peak.append(
                pitch_center - math.ceil(flat_peak / 2)
            )
            self.top_flat_peak.append(pitch_center + math.floor(flat_peak / 2))
        if self.shape == "quadratic":  # pylint: disable=no-member
            self.vel_func = er_prob_funcs.quadratic
        elif self.shape == "linear":  # pylint: disable=no-member
            self.vel_func = er_prob_funcs.linear

    def get_vel(self, pitch, orig_vel, voice_i):
        (
            bottom_flat_peak,
            top_flat_peak,
            flat_peak,
            num_octaves,
            bottom_pitch,
            top_pitch,
        ) = self.get(
            voice_i,
            "bottom_flat_peak",
            "top_flat_peak",
            "flat_peak",
            "num_octaves",
            "bottom_pitch",
            "top_pitch",
        )
        if pitch < bottom_flat_peak:
            return round(
                orig_vel
                * self.vel_func(
                    pitch - bottom_pitch,
                    0,
                    1,
                    (num_octaves * self.tet - math.ceil(flat_peak / 2)) / 2,
                )
            )
        if pitch > top_flat_peak:
            return round(
                orig_vel
                * self.vel_func(
                    top_pitch - pitch,
                    0,
                    1,
                    (num_octaves * self.tet - math.floor(flat_peak / 2)) / 2,
                )
            )
        return orig_vel

    def change_func(self, score, voice_i, notes_to_change):
        voice = score.voices[voice_i]
        bottom_pitch, top_pitch = self.get(voice_i, "bottom_pitch", "top_pitch")
        if self.new_tracks:  # pylint: disable=no-member
            # LONGTERM
            pass
        for note in notes_to_change:
            self.mark_note(note)
            pc_int = (note.pitch - bottom_pitch) % self.tet
            pitch = bottom_pitch + pc_int
            while pitch <= top_pitch:
                new_vel = self.get_vel(pitch, note.velocity, voice_i)
                if pitch == note.pitch:
                    note.velocity = new_vel
                elif self.new_tracks:  # pylint: disable=no-member
                    # LONGTERM
                    pass
                else:
                    new_note = copy.copy(note)
                    new_note.velocity = new_vel
                    new_note.pitch = pitch
                    voice.add_note_object(new_note, update_sort=False)
                # ...
                pitch += self.tet
        voice.update_sort()


class TrackExchangerTransformer(TransformBase):
    pretty_name = "Track exchanger transformer"

    def __init__(
        self,
        score,
        start_time=0,
        end_time=0,
        prob_func="Linear",
        voices=(),
        track_pairs=(),
        changer_counter=None,
    ):
        super().__init__(
            score,
            start_time=start_time,
            end_time=end_time,
            prob_func=prob_func,
            voices=voices,
            changer_counter=changer_counter,
        )
        self.add_attribute(
            "track_pairs",
            track_pairs,
            "Track source/destination pairs",
            int,
            attr_val_kwargs={"min_value": 0, "max_value": -1, "tuple_of": -2},
        )
        self.require_score = True

    def change_func(self, score, voice_i, notes_to_change):
        try:
            source_tracks, dest_tracks = zip(
                *self.track_pairs  # pylint: disable=no-member
            )
        except ValueError as exc:
            raise ChangeFuncError(
                "Invalid value for track source/destination pairs... "
                "perhaps they are empty?"
            ) from exc
        try:
            i = source_tracks.index(voice_i)
        except ValueError:
            return
        dest_voice_i = dest_tracks[i]
        while dest_voice_i > score.num_voices - 1:
            score.add_voice()

        for note in notes_to_change:
            score.voices[dest_voice_i].add_note_object(note, update_sort=False)
            score.voices[voice_i].remove_note_object(note)
            self.mark_note(note)
        score.voices[dest_voice_i].update_sort()
        # score.voices[voice_i].update_sort()


class InvertTransformer(TransformBase):
    pretty_name = "Melodic inversion transformer"

    def __init__(
        self,
        score,
        start_time=0,
        end_time=0,
        prob_func="Linear",
        voices=(),
        changer_counter=None,
    ):
        super().__init__(
            score,
            start_time=start_time,
            end_time=end_time,
            prob_func=prob_func,
            voices=voices,
            changer_counter=changer_counter,
        )
        self.add_attribute(
            "axis",
            5 * self.tet,
            "Axis of inversion",
            int,
            attr_val_kwargs={"max_value": -1},
            attr_hint=("TET", self.tet),
        )

    def change_func(self, voice, notes_to_change):
        voice_i = voice.voice_i
        axis = self.get(voice_i, "axis")
        notes_to_remove = []
        for note in notes_to_change:
            new_pitch = 2 * axis - note.pitch
            if 0 < new_pitch <= self.tet * 10:
                note.pitch = new_pitch
                self.mark_note(note)
            else:
                notes_to_remove.append(note)

        if notes_to_remove:
            print("\n")
            print(
                "        Removing {} out of range notes in voice {}".format(
                    len(notes_to_remove), voice_i
                )
            )
            for note in notes_to_remove:
                voice.remove_note_object(note)


class TrackRandomizerTransformer(TransformBase):
    pretty_name = "Track randomizer transformer"

    def __init__(
        self,
        score,
        start_time=0,
        end_time=0,
        prob_func="Linear",
        voices=(),
        changer_counter=None,
    ):
        super().__init__(
            score,
            start_time=start_time,
            end_time=end_time,
            prob_func=prob_func,
            voices=voices,
            changer_counter=changer_counter,
        )
        self.add_attribute(
            "dest_voices",
            self.voices,  # pylint: disable=no-member
            "Destination voices",
            int,
            attr_val_kwargs={"min_value": 0, "max_value": -1},
        )
        self.require_score = True

    def validate(self, score, *args):  # pylint: disable=arguments-differ
        super().validate(*args)
        for i, dest_voice_i in enumerate(
            self.dest_voices  # pylint: disable=no-member
        ):
            if dest_voice_i > score.num_voices - 1:
                self.dest_voices[  # pylint: disable=no-member
                    i
                ] = score.num_voices
                score.add_voice()

    def change_func(self, score, voice_i, notes_to_change):
        for note in notes_to_change:
            dest_voice_i = random.choice(
                self.dest_voices  # pylint: disable=no-member
            )
            score.voices[dest_voice_i].add_note_object(note, update_sort=False)
            score.voices[voice_i].remove_note_object(note)
            self.mark_note(note)

        for dest_voice_i in self.dest_voices:  # pylint: disable=no-member
            score.voices[dest_voice_i].update_sort()
        # score.voices[voice_i].update_sort()


class TrackDoublerTransformer(TransformBase):
    pretty_name = "Track doubler transformer"

    def __init__(
        self,
        score,
        start_time=0,
        end_time=0,
        prob_func="Static",
        voices=(),
        changer_counter=None,
    ):
        super().__init__(
            score,
            start_time=start_time,
            end_time=end_time,
            prob_func=prob_func,
            voices=voices,
            changer_counter=changer_counter,
        )
        self.add_attribute(
            "doubling_intervals",
            0,
            "Doubled voices transpositions",
            int,
            attr_val_kwargs={"min_value": -128, "max_value": 128},
        )
        self.require_score = True

    def change_func(  # pylint: disable=unused-argument
        self, score, voice_i, notes_to_change
    ):
        for note in notes_to_change:
            self.mark_note(note)
        for (
            doubling_interval
        ) in self.doubling_intervals:  # pylint: disable=no-member
            dest_track = score.add_voice()
            dest_track.append(notes_to_change)
            dest_track.transpose(doubling_interval)


class SubdivideTransformer(TransformBase):
    pretty_name = "Subdivide transformer"

    def __init__(
        self,
        score,
        start_time=0,
        end_time=0,
        prob_func="Static",
        voices=(),
        subdivision=0.25,
        changer_counter=None,
    ):
        super().__init__(
            score,
            start_time=start_time,
            end_time=end_time,
            prob_func=prob_func,
            voices=voices,
            changer_counter=changer_counter,
        )
        self.add_attribute(
            "subdivision",
            subdivision,
            "Subdivision value",
            fractions.Fraction,
            attr_val_kwargs={"min_value": 1 / 128, "max_value": 4},
        )

    def change_func(self, voice, notes_to_change):
        # add comma support
        voice_i = voice.voice_i
        subdivision = self.get(voice_i, "subdivision")
        for note in notes_to_change:
            time = note.attack_time
            end = time + note.dur
            to_add = min((subdivision, note.dur))
            note.dur = to_add
            time += to_add
            while time < end:
                new_note = copy.copy(note)
                new_note.attack_time = time
                to_add = min((subdivision, end - time))
                if to_add == 0:
                    break
                new_note.dur = to_add
                voice.add_note_object(new_note, update_sort=False)
                time += to_add
            self.mark_note(note)
        voice.update_sort()


class LoopTransformer(TransformBase):
    pretty_name = "Loop transformer"

    def __init__(
        self,
        score,
        start_time=0,
        end_time=0,
        prob_func="Linear",
        voices=(),
        loop_len=4,
        changer_counter=None,
    ):
        super().__init__(
            score,
            start_time=start_time,
            end_time=end_time,
            prob_func=prob_func,
            voices=voices,
            changer_counter=changer_counter,
        )
        self.add_attribute(
            "loop_len",
            loop_len,
            "Loop length",
            fractions.Fraction,
            attr_val_kwargs={"min_value": 0, "max_value": -1},
        )

    def change_func(self, voice, notes_to_change):
        voice_i = voice.voice_i
        loop_len = self.get(voice_i, "loop_len")
        # What to do if the attack % loop_len does not
        # occur in the initial loop?
        # And what about note attributes other than pitch?
        # (duration, choir, ...)
        for note in notes_to_change:
            time = note.attack_time
            ref_time = time % loop_len
            # For now, I just take the first note, arbitrarily,
            # at the earlier time
            try:
                ref_note = voice[ref_time][0]
            except KeyError:
                continue
            note.pitch = ref_note.pitch
            self.mark_note(note)


# INTERNET_TODO is there a better way of doing this?
FILTERS = tuple(item for item in locals() if "Filter" in item)
TRANSFORMERS = tuple(item for item in locals() if "Transformer" in item)
