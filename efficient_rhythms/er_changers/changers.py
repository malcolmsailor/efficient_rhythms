import fractions
import itertools
import random

from .. import er_classes
from .. import er_misc_funcs

from . import prob_curves
from .attribute_adder import AttributeAdder
from .get_info import InfoGetter

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

# CHANGER_TODO change "filter" to "transformer" for transformers?
EXEMPTIONS_DESC = """'Exemptions' specify notes that the filter will never be
applied to. Exemptions can either be 'metric', meaning that notes onset on
certain beats are exempt, or 'counting', meaning that notes are counted, and
every 'nth' note is exempt.
"""
EXEMPT_BEATS_DESC = """Beats to exempt from the filter. Zero-indexed (so the
first beat is 0). See also 'Exempt beats modulo' and 'Exempt comma'."""


# def _get_prob_curves():
#     """Gets the possible probability curves from prob_curves.py."""
#     out = []
#     for var in vars(prob_curves):
#         if var == "NullProbCurve":
#             out.append(var)
#         if var in ("ProbCurve", "NonStaticFunc", "OscFunc"):
#             continue
#         try:
#             yes = issubclass(getattr(prob_curves, var), prob_curves.ProbCurve)
#         except TypeError:
#             continue
#         if yes:
#             out.append(var)
#     return out


def null_condition(*args, **kwargs):  # pylint: disable=unused-argument
    return True


class ChangeFuncError(Exception):
    pass


class Changer(AttributeAdder, InfoGetter):
    pretty_name = "Changer"
    description = ""

    def __init__(
        self,
        score,
        start_time=0,
        end_time=0,
        prob_curve="Static",
        condition=null_condition,
        voices=(),
        by_voice=True,
        changer_counter=None,
        **kwargs,  # any additional kwargs are passed through to prob_curve
    ):
        if changer_counter is not None:
            changer_counter[self.pretty_name] += 1
            self.pretty_name += " " + str(changer_counter[self.pretty_name])
        self.condition = condition
        self.total_len = float(score.total_dur)
        super().__init__()
        self.all_voice_idxs = score.all_voice_idxs
        self.num_voices = len(self.all_voice_idxs)
        self.tet = score.tet
        prob_curve = getattr(prob_curves, prob_curve)(
            length=end_time - start_time, **kwargs
        )
        self.require_score = False
        self.add_attribute(
            "prob_curve",
            prob_curve,
            "Probability curve",
            str,
            attr_val_kwargs={"possible_values": prob_curves.PROB_CURVES},
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
            attr_val_kwargs={"min_value": 0.0, "max_value": self.total_len},
        )
        self.add_attribute(
            "end_time",
            self.total_len if end_time == 0 else end_time,
            "End time",
            float,
            attr_val_kwargs={"min_value": 0.0, "max_value": self.total_len},
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
            self.mod_n = exemptions[
                -1
            ]  # pylint: disable=attribute-defined-outside-init
            self.exemptions_n = (
                [  # pylint: disable=attribute-defined-outside-init
                    0,
                ]
                + exemptions[:-1]
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
                if not isinstance(score, er_classes.Score):
                    raise NotImplementedError()
                no_marked_transformations = True
                # TODO it seems this is expecting single notes but iterating
                #   over the score will return a list of notes?
                # TODO iterate over voices separately
                for voice in score:
                    for note in voice:
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

    def beat_exempt(self, onset):
        mod_onset = onset % self.exempt_modulo  # pylint: disable=no-member
        exempt_i = er_misc_funcs.binary_search(
            self.exempt,  # pylint: disable=no-member
            mod_onset,
            not_found="nearest",
        )
        mod_diff = min(
            abs(self.exempt[exempt_i] - mod_onset),  # pylint: disable=no-member
            abs(
                self.exempt[exempt_i]  # pylint: disable=no-member
                + self.exempt_modulo  # pylint: disable=no-member
                - mod_onset
            ),
        )
        if mod_diff < self.exempt_comma:  # pylint: disable=no-member
            return not self.invert_exempt  # pylint: disable=no-member
        return self.invert_exempt  # pylint: disable=no-member

    def n_exempt(self, i):
        # TODO debug? or de-implement?
        mod_i = i % self.mod_n
        if mod_i in self.exemptions_n:
            return not self.invert_exempt  # pylint: disable=no-member
        return self.invert_exempt  # pylint: disable=no-member

    def _apply_by_voice(self, score):
        exemptions = (
            self.exempt  # pylint: disable=no-member
            and self.exempt[0] is not None  # pylint: disable=no-member
        )
        for interface_voice_i in self.voices:  # pylint: disable=no-member
            voice_i = self.all_voice_idxs[interface_voice_i]
            voice = score.voices[voice_i]
            notes_to_change = []
            start_time, end_time = self.get(voice_i, "start_time", "end_time")
            if "length" in vars(self.prob_curve):  # pylint: disable=no-member
                self.prob_curve.length = (  # pylint: disable=no-member
                    end_time - start_time
                )

            offset_i = voice.get_i_at_or_before(start_time)
            for i, note in enumerate(voice.between(start_time, end_time)):
                onset = note.onset
                if exemptions:
                    if self.mod_n is None and self.beat_exempt(onset):
                        continue
                    if self.mod_n and self.n_exempt(i + offset_i):
                        continue
                if not self.condition(note):
                    continue
                # TODO what exactly is this code doing?
                try:
                    if (
                        self.marked_by
                        and self.marked_by not in note.transformations_
                    ):
                        continue
                except AttributeError:
                    continue

                filter_time = onset - start_time
                func_result = (
                    self.prob_curve.calculate(  # pylint: disable=no-member
                        filter_time, random.random(), voice_i
                    )
                )
                if func_result:
                    notes_to_change.append(note)

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
        if "length" in vars(self.prob_curve):  # pylint: disable=no-member
            self.prob_curve.length = (  # pylint: disable=no-member
                end_time - start_time
            )

        for notes in score.notes_by_onset_between(start_time, end_time):
            onset = notes[0].onset
            if exemptions and self.beat_exempt(onset):
                continue
            notes_to_process = [note for note in notes if self.condition(note)]
            if not notes_to_process:
                continue
            filter_time = onset - start_time
            func_result = (
                self.prob_curve.calculate(  # pylint: disable=no-member
                    filter_time, random.random(), 0
                )
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
            self.prob_curve.reset()
        except AttributeError:
            pass

        if self.by_voice:  # pylint: disable=no-member
            self._apply_by_voice(score)

        else:
            self._apply_by_score(score)


class Mediator(AttributeAdder):
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
            self.mediating_func = (
                getattr(  # pylint: disable=attribute-defined-outside-init
                    prob_curves, self.func_str  # pylint: disable=no-member
                )
            )
            # vars(prob_curves)[
            #     self.func_str
            # ]
            return True
        except KeyError:
            return False

    def mediate(self, voice_i, unmediated_val, original_val, onset):
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
            if start_time > onset or end_time <= onset:
                return unmediated_val

        adjust = self.mediating_func(
            onset + offset,
            0,
            1,
            period,
            decreasing=self.med_decreasing,  # pylint: disable=no-member
        )
        return unmediated_val + (original_val - unmediated_val) * adjust
