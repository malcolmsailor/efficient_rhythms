import itertools
import numbers
import random
import os

from fractions import Fraction

import er_constants


class BaseRandomizer:
    def __init__(self, multiple_values=0):
        self.multiple_values = multiple_values

    def _eval_bool(self, attr):
        value = getattr(self, attr)
        if isinstance(value, numbers.Number):
            no = list(itertools.repeat(0, round(100 * (1 - value))))
            yes = list(itertools.repeat(1, round(100 * value)))
            choices = no + yes
        else:
            choices = (0, 1)
        if random.choice(choices):
            return True
        return False


class StrRandomizer:
    def __init__(self, mapping):
        self.mapping = mapping

    def __call__(self, er):
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
        if self._eval_bool("multiple_values"):
            num_values = random.randrange(1, self.max_multiple_values + 1)
            out = []
            for _ in range(num_values):
                out.append(random.choice(self.choices))
            return out
        return random.choice(self.choices)


class BoolRandomizer(BaseRandomizer):
    def __init__(self, toggle, multiple_values=0):
        super().__init__(multiple_values=multiple_values)
        self.toggle = toggle

    def _fetch_value(self):
        if not self._eval_bool("toggle"):
            return False
        return True

    def __call__(self, er):
        if self._eval_bool("multiple_values"):
            out = []
            for _ in range(er.num_voices):
                out.append(self._fetch_value())
            return out

        return self._fetch_value()


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


class Randomizer(BoolRandomizer):
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
        conditions=None,
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
        self.conditions = conditions

    def _fetch_value(self):
        # bottom = self.min_ * int(1 / self.step)
        # top = self.max_ * int(1 / self.step)
        # choice = random.randrange(bottom, top + 1)
        # if self.step == 1:
        #     return choice
        # return choice * self.step
        return _choose_within_range(
            self.min_, self.max_, self.step, illegal_values=self.illegal_values
        )

    # TODO check conditions
    # def _check_conditions(self, er):
    #     """This is a null function because there's no general procedure that
    #     works for all types of Randomizers; it should be overridden in
    #     subclasses."""

    def __call__(self, er):
        # TODO check conditions
        if self.conditions is not None:
            raise NotImplementedError
            # self._check_conditions(er)
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
                spread = _choose_within_range(*self.spread, self.step)
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
                out.append(_choose_within_range(min_, max_, self.step))
            return out

        return self._fetch_value()


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
        self.force_parallel_motion = StrRandomizer(
            {"within_harmonies": 0.25, "false": 0.75}
        )
        self.consonance_treatment = StrRandomizer(
            {"all_attacks": 0.5, "all_durs": 0.25, "none": 0.25}
        )
        self.cont_rhythms = StrRandomizer(
            {"none": 0.6, "all": 0.2, "grid": 0.2}
        )
        self.vary_rhythm_consistently = BoolRandomizer(0.7)
        # TODO allow generation of tuples of voices for following properties
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

    def apply(self, er):
        width = os.get_terminal_size().columns
        print("#" * width)
        print("Randomized settings:")
        for var, randomizer in vars(self).items():
            if var in er.exclude_from_randomization:
                continue
            vars(er)[var] = randomizer(er)
            print(var + ": ", vars(er)[var])
        print("#" * width)
