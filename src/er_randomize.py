import numbers
import random
import os
import typing

from fractions import Fraction

import numpy as np

import src.er_constants as er_constants

# TODO Warnings to address:
# Notice: 'parallel_voice_leading' is not compatible with checking voice-leadings
# for consonance. Ignoring 'vl_maintain_consonance'


class BaseRandomizer:
    def __init__(self, multiple_values=0, conditions=None, actions=None):
        self.multiple_values = multiple_values
        self.conditions = conditions
        self.actions = actions
        self._actions_taken = []

    def _eval_bool(self, attr):
        value = getattr(self, attr)
        if not isinstance(value, numbers.Number):
            value = 0.5
        return random.random() < value

    def _check_conditions(self, er):
        """If any condition evaluates to True, returns the associated value.

        Doesn't evaluate subsequent conditions after evaluating a condition
        to True.
        """
        if self.conditions is None:
            return

        def _do_action(obj_name, action_name, action_args):
            if action_name == "setattr":
                setattr(self, obj_name, action_args)
            else:
                obj = getattr(self, obj_name)
                action = getattr(obj, action_name)
                action(action_args)

        for lhs, op, rhs, action_indices in self.conditions:
            lhs = getattr(er, lhs)
            if isinstance(rhs, str):
                try:
                    rhs = getattr(er, rhs)
                except AttributeError:
                    # rhs is not an attribute but a literal to compare to
                    pass
            op = getattr(lhs, op)
            if op(rhs):
                for action_i in action_indices:
                    if action_i in self._actions_taken:
                        continue
                    _do_action(*self.actions[action_i])
                    self._actions_taken.append(action_i)


class StrRandomizer(BaseRandomizer):
    def __init__(self, mapping, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mapping = mapping

    def __call__(self, er):
        self._check_conditions(er)
        choices = []
        for word, weight in self.mapping.items():
            choices += [word for i in range(int(weight * 100))]
        return random.choice(choices)


class RandomSelecter(BaseRandomizer):
    def __init__(self, choices, multiple_values=0, max_multiple_values=4):
        super().__init__(multiple_values=multiple_values)
        self.choices = choices
        self.max_multiple_values = max_multiple_values

    def __call__(self, er):
        self._check_conditions(er)
        if self._eval_bool("multiple_values"):
            num_values = random.randrange(1, self.max_multiple_values + 1)
            return [random.choice(self.choices) for _ in range(num_values)]
        return random.choice(self.choices)


class BoolRandomizer(BaseRandomizer):
    def __init__(self, toggle, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.toggle = toggle

    def _fetch_value(self):
        return self._eval_bool("toggle")

    def __call__(self, er):
        self._check_conditions(er)
        if self._eval_bool("multiple_values"):
            return [self._fetch_value() for _ in range(er.num_voices)]
        return self._fetch_value()


class Randomizer(BoolRandomizer):
    """
        conditions: a sequence of tuples of form (lhs, op, rhs, action_indices),
            where
                - lhs is an attribute of the ERSettings object
                - rhs is an attribute of the ERSettings or a literal value
                    (although note that if rhs is a string, it can't have the
                    name of an attribute of ERSettings or it will evaluate
                    to that attribute)
                - op is the name of a comparison operator (e.g., "__eq__")
                - action_indices: a tuple of indices into the sequence passed as the
                    `actions` argument. The reason for passing indices rather
                    than the actions directly is so that multiple conditions
                    can trigger the same actions, without the actions
                    being taken multiple times (which, e.g., would lead to
                    an error if an attribute is deleted twice).
        actions: a sequence of tuples of form (obj_name, action_name,
            action_args), where
                - obj_name is an attribute of the Randomizer
                - action_name is either the name of a method of lhs (e.g.,
                    "__delitem__"), or "setattr" (in which case
                    setattr(self, obj_name, action_args) is called)
                - action_args is the argument to action_name
    """

    def __init__(
        self,
        min_,
        max_,
        step=1,
        toggle=1,
        multiple_values=0,
        spread=None,
        same_as=None,
        illegal_values=None,
    ):
        super().__init__(toggle, multiple_values=multiple_values)
        if not min_ <= max_:
            max_, min_ = (min_, max_)
        self.min_ = min_
        self.max_ = max_
        self.step = step
        self.spread = spread
        self.same_as = same_as
        self.illegal_values = illegal_values

    def _fetch_value(self):
        return self._choose_within_range(
            self.min_, self.max_, self.step, illegal_values=self.illegal_values
        )

    def __call__(self, er):
        self._check_conditions(er)
        if not self._eval_bool("toggle"):
            return False
        if self.same_as is not None:
            prob, param = self.same_as
            if random.random() < prob:
                return vars(er)[param]
        if self._eval_bool("multiple_values"):
            min_ = self.min_
            max_ = self.max_
            if self.spread is not None:
                spread = self._choose_within_range(*self.spread, self.step)
            out = []
            for _ in range(er.num_voices):
                try:
                    min_ = max((min_, max(out) - spread))
                except (ValueError, UnboundLocalError):
                    pass
                try:
                    max_ = min((max_, min(out) + spread))
                except (ValueError, UnboundLocalError):
                    pass
                out.append(self._choose_within_range(min_, max_, self.step))
            return out

        return self._fetch_value()

    @staticmethod
    def _choose_within_range(min_, max_, step, illegal_values=None):
        bottom = int(min_ / step)
        top = int(max_ / step)
        choices = list(range(bottom, top + 1))
        while choices:
            choice = random.choice(choices)
            if step == 1:
                out = choice
            else:
                out = choice * step
            if illegal_values and out in illegal_values:
                choices.remove(choice)
            else:
                return out

        class NoLegalValuesError(Exception):
            pass

        raise NoLegalValuesError("Unable to choose any legal values")


# LONGTERM allow randomizers to have side-effects
#   e.g., if cont_rhythms randomizes to "all" or "grid", reduce
#   min_dur if necessary
class ERRandomize:
    def __init__(self, er):
        self.num_voices = Randomizer(2, 5)
        self.pattern_len = Randomizer(2, 8, step=0.5, multiple_values=0.25)
        self.rhythm_len = Randomizer(
            1, 8, step=0.5, multiple_values=0.25, same_as=(0.5, "pattern_len")
        )
        self.pitch_loop = Randomizer(2, 4, toggle=0.25)
        self.harmony_len = Randomizer(
            1, 8, step=0.5, multiple_values=0.2, same_as=(0.5, "pattern_len")
        )
        self.truncate_patterns = BoolRandomizer(0.7)
        self.voice_order_str = StrRandomizer({"reverse": 0.25, "usual": 0.75})
        self.interval_cycle = RandomSelecter(
            list(range(er.tet)), multiple_values=0.5, max_multiple_values=8,
        )
        self.chords = RandomSelecter(
            [
                er_constants.I * er_constants.MAJOR_TRIAD,
                er_constants.II * er_constants.MINOR_TRIAD,
                er_constants.III * er_constants.MINOR_TRIAD,
                er_constants.IV * er_constants.MAJOR_TRIAD,
                er_constants.V * er_constants.MAJOR_TRIAD,
                er_constants.VI * er_constants.MINOR_TRIAD,
            ],
            multiple_values=0.4,
            max_multiple_values=4,
        )
        self.parallel_voice_leading = BoolRandomizer(0.1)
        self.voice_lead_chord_tones = BoolRandomizer(0.65)
        self.preserve_root_in_bass = StrRandomizer(
            {"lowest": 0.35, "none": 0.5, "all": 0.15}
        )
        self.chord_tone_and_root_disable = BoolRandomizer(0.1)
        self.chord_tone_selection = BoolRandomizer(0.75)
        self.force_chord_tone = StrRandomizer(
            {
                "global_first_beat": 0.2,
                "global_first_note": 0.2,
                "first_beat": 0.2,
                "first_note": 0.2,
                "none": 0.2,
            }
        )
        self.chord_tones_sync_attack_in_all_voices = BoolRandomizer(0.2)
        self.force_root_in_bass = StrRandomizer(
            {
                "global_first_beat": 0.2,
                "global_first_note": 0.2,
                "first_beat": 0.2,
                "first_note": 0.2,
                "none": 0.2,
            }
        )
        self.prefer_small_melodic_intervals = BoolRandomizer(0.7)
        self.force_repeated_notes = BoolRandomizer(0.1)
        self.force_parallel_motion = BoolRandomizer(0.2)
        self.consonance_treatment = StrRandomizer(
            {"all_attacks": 0.5, "all_durs": 0.25, "none": 0.25}
        )
        self.cont_rhythms = StrRandomizer(
            {"none": 0.6, "all": 0.2, "grid": 0.2,},
            conditions=(
                ("pattern_len", "__ne__", "rhythm_len", (0, 1),),
                ("pattern_len", "__ne__", 1, (0, 1),),
            ),
            actions=(
                ("mapping", "__delitem__", "all"),
                ("mapping", "__delitem__", "grid"),
            ),
        )
        self.vary_rhythm_consistently = BoolRandomizer(
            0.7,
            conditions=(("cont_rhythms", "__eq__", "none", (0,)),),
            actions=(("toggle", "setattr", 0),),
        )
        # LONGTERM allow generation of tuples of voices for following properties
        self.rhythmic_unison = BoolRandomizer(0.3)
        self.rhythmic_quasi_unison = BoolRandomizer(0.3)
        self.hocketing = BoolRandomizer(0.4)
        self.attack_density = Randomizer(
            0.05, 1, step=0.05, multiple_values=1, spread=(0, 1)
        )
        self.dur_density = Randomizer(
            0.05, 1, step=0.05, multiple_values=0.7, spread=(0, 1)
        )
        self.attack_subdivision = RandomSelecter(
            [
                Fraction(1, 1),
                Fraction(1, 2),
                Fraction(1, 3),
                Fraction(1, 4),
                Fraction(1, 6),
            ],
            multiple_values=0.25,
            max_multiple_values=er.num_voices,
        )
        self.randomly_distribute_between_choirs = BoolRandomizer(0.7)
        self.length_choir_segments = Randomizer(
            -0.5, 2, step=0.25, illegal_values=[0,]
        )
        self.tempo = Randomizer(96, 160)

    @staticmethod
    def _print_setting(attr, val):
        # Originally I wrote this function because I wanted to format floats
        # nicely for printing. But then I got rid of the float formatting
        # because it caused issues when copying the settings for re-use with
        # the script. It still makes numpy arrays print like tuples which is
        # nice though.
        def _format_item(item):
            if isinstance(item, bool):
                if item:
                    return "True"
                return "False"
            if isinstance(item, Fraction):
                return f"{float(item)}"
            if isinstance(item, numbers.Number):
                return f"{item:g}"
            if isinstance(item, str):
                return f'"{item}"'
            if isinstance(item, (typing.Sequence, np.ndarray)):
                return _tuplify(item)
            return f"{item}"

        def _tuplify(item):
            if isinstance(
                item, (typing.Sequence, np.ndarray)
            ) and not isinstance(item, str):
                return (
                    "("
                    + ", ".join(_format_item(sub_item) for sub_item in item)
                    + ")"
                )
            return _format_item(item)

        print(f'"{attr}": {_format_item(val)},')

    def apply(self, er):
        width = os.get_terminal_size().columns
        print("#" * width)
        print("Randomized settings:")
        for attr, randomizer in vars(self).items():
            if attr in er.exclude_from_randomization:
                continue
            val = randomizer(er)
            setattr(er, attr, val)
            self._print_setting(attr, val)
        print("#" * width)
