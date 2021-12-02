import fractions
import inspect
import math
import random

from .attribute_adder import AttributeAdder
from .get_info import InfoGetter


class NullProbCurve(AttributeAdder, InfoGetter):
    pretty_name = "Always on"

    def __init__(self, **kwargs):  # pylint: disable=unused-argument
        super().__init__()

    def _get_seg_len(
        self, *args
    ):  # pylint: disable=unused-argument,no-self-use
        return 1

    def calculate(
        self, *args, **kwargs
    ):  # pylint: disable=unused-argument,no-self-use
        return True


class AlwaysOn(NullProbCurve):
    # alias for NullProbCurve
    pass


class ProbCurve(NullProbCurve):
    """Base class for probability curve classes.

    Attributes:
        self.seg_len_range: (list of) 2-tuples of ints. Defines an
            (inclusive) range of possible "segment lengths" that
            will be chosen from. The function will only return a
            new value after the segment length has expired (e.g.,
            if the segment length is 2, it will only return a
            new value on every 2nd occasion it is called). The
            segment count is decremented at each note, or at each
            new "grain" (see below), whichever is longer.
        self.granularity: (list of) numbers. Defines the "grain"
            of the probability curve, where 1 is a quarter note.
            If the grain is, e.g., 0.5, then the function will
            only decrement self.seg_len_range at each new 8th note
            (although it will only decrement once for notes longer
            than an 8th note). This could, for instance, chop up
            a stream of 16th notes into 8th-note length segments.
        self.grain_offset: (list of) numbers. The offset (from 0)
            at which granularity is calculated (so, e.g., with a
            granularity of 1 and a grain_offset of 0.25, the
            probability curve will apply to groups of 4 16ths
            ending on each beat).

    Methods:
        calculate(x, voice_i): calculates the result for
    """

    def __init__(self, seg_len_range=(1, 1), granularity=(0), grain_offset=0):
        super().__init__()
        self.seg_len_range = None
        self.add_attribute(
            "seg_len_range",
            seg_len_range,
            "Segment length range",
            int,
            attr_val_kwargs={
                "min_value": 1,
                "max_value": -1,
                "tuple_of": 2,
                "iter_of_iters": True,
            },
        )
        self.add_attribute(
            "granularity",
            granularity,
            "Rhythmic granularity",
            fractions.Fraction,
            attr_val_kwargs={"min_value": 0, "max_value": -1},
        )
        self.add_attribute(
            "grain_offset",
            grain_offset,
            "Granularity offset",
            fractions.Fraction,
            attr_val_kwargs={"min_value": 0, "max_value": -1},
            display_if={"granularity": "true"},
        )
        self._on_dict = {}
        self._count_dict = {}
        self._grain_dict = {}

    def _get_seg_len(self, voice_i):  # pylint: disable=arguments-differ
        lower_b, upper_b = self.seg_len_range[voice_i % len(self.seg_len_range)]
        return random.randrange(lower_b, upper_b + 1)

    def _new_grain(self, x, voice_i):
        granularity, grain_offset = self.get(
            voice_i, "granularity", "grain_offset"
        )

        if granularity == 0:
            return True

        # if voice_i not in self._grain_dict:
        #     self._grain_dict[voice_i] = x
        #     return False

        try:
            last_x = self._grain_dict[voice_i]
        except KeyError:
            self._grain_dict[voice_i] = x
            return False

        self._grain_dict[voice_i] = x
        remaining = granularity - ((last_x + grain_offset) % granularity)
        if x - last_x >= remaining:
            return True
        return False

    def calculate(self, x, rand, voice_i=0):  # pylint: disable=arguments-differ
        if self._new_grain(x, voice_i):
            try:
                self._count_dict[voice_i] -= 1
            except KeyError:
                if self.get(voice_i, "granularity") == 0:
                    pass
                else:
                    raise  # We should never get here unless there is a bug

        if voice_i not in self._count_dict or not self._count_dict[voice_i]:
            self._count_dict[voice_i] = self._get_seg_len(voice_i)
            result = bool(
                self.prob_curve(  # pylint: disable=no-member
                    x, rand, voice_i=voice_i
                )
            )
            self._on_dict[voice_i] = result
            return result

        if self._on_dict[voice_i]:
            return True
        return False


class Static(ProbCurve):
    """Static probability curve class."""

    def __init__(  # pylint: disable=unused-argument
        self, prob=0.5, seg_len_range=(1, 1), **extra_args
    ):
        super().__init__(seg_len_range=seg_len_range)
        self.prob = None
        self.add_attribute(
            "prob",
            prob,
            "Static probability",
            float,
            attr_val_kwargs={"min_value": 0, "max_value": 1},
        )
        self.pretty_name = "Static"

    def prob_curve(self, x, rand, voice_i=0):  # pylint: disable=unused-argument
        if self.prob[voice_i % len(self.prob)] > rand:
            return True
        return False


class NonStaticCurve(ProbCurve):
    """Base class for non-static probability curve classes."""

    def __init__(
        self,
        min_prob=0,
        max_prob=1,
        length=0,
        decreasing=False,
        seg_len_range=(1, 1),
    ):
        super().__init__(seg_len_range=seg_len_range)
        self.length = length
        self.add_attribute(
            "min_prob",
            min_prob,
            "Minimum probability",
            float,
            attr_val_kwargs={"min_value": 0, "max_value": 1},
        )
        self.add_attribute(
            "max_prob",
            max_prob,
            "Maximum probability",
            float,
            attr_val_kwargs={"min_value": 0, "max_value": 1},
        )
        self.add_attribute("decreasing", decreasing, "Decreasing", bool)


class Linear(NonStaticCurve):
    """Linear probability curve class."""

    def __init__(self, min_prob=0, max_prob=1, length=0, decreasing=False):
        super().__init__(
            min_prob=min_prob,
            max_prob=max_prob,
            length=length,
            decreasing=decreasing,
        )
        self.pretty_name = "Linear"

    def prob_curve(self, x, rand, voice_i=0):
        decreasing, min_prob, max_prob = self.get(
            voice_i, "decreasing", "min_prob", "max_prob"
        )
        result = linear(
            x, min_prob, max_prob, self.length, decreasing=decreasing
        )
        if result > rand:
            return True
        return False


class Quadratic(NonStaticCurve):
    """Quadratic probability curve class."""

    def __init__(self, min_prob=0, max_prob=1, length=0, decreasing=False):
        super().__init__(
            min_prob=min_prob,
            max_prob=max_prob,
            length=length,
            decreasing=decreasing,
        )
        self.pretty_name = "Quadratic"

    def prob_curve(self, x, rand, voice_i=0):
        decreasing, min_prob, max_prob = self.get(
            voice_i, "decreasing", "min_prob", "max_prob"
        )
        result = quadratic(
            x, min_prob, max_prob, self.length, decreasing=decreasing
        )
        if result > rand:
            return True
        return False


class OscCurve(NonStaticCurve):
    """Base class for oscillating non-static probability curves."""

    def __init__(
        self, min_prob=0, max_prob=1, period=4, length=0, decreasing=False
    ):
        super().__init__(
            min_prob=min_prob,
            max_prob=max_prob,
            length=length,
            decreasing=decreasing,
        )
        self.add_attribute(
            "period",
            period,
            "Oscillation period",
            fractions.Fraction,
            attr_val_kwargs={"min_value": 0, "max_value": -1},
        )
        self.add_attribute(
            "offset",
            0,
            "Oscillation offset",
            fractions.Fraction,
            attr_val_kwargs={"min_value": 0, "max_value": -1},
        )


class LinearOsc(OscCurve):
    """Linear oscillating probability curve class."""

    def __init__(
        self, min_prob=0, max_prob=1, period=4, length=0, decreasing=False
    ):
        super().__init__(
            min_prob=min_prob,
            max_prob=max_prob,
            length=length,
            decreasing=decreasing,
        )
        self.pretty_name = "Linear oscillating"

    def prob_curve(self, x, rand, voice_i=0):
        decreasing, min_prob, max_prob, period, offset = self.get(
            voice_i, "decreasing", "min_prob", "max_prob", "period", "offset"
        )
        result = linear_osc(
            offset + x, min_prob, max_prob, period, decreasing=decreasing
        )
        if result > rand:
            return True
        return False


class Saw(OscCurve):
    """Saw oscillating probability curve class."""

    def __init__(
        self, min_prob=0, max_prob=1, period=4, length=0, decreasing=False
    ):
        super().__init__(
            min_prob=min_prob,
            max_prob=max_prob,
            length=length,
            decreasing=decreasing,
        )
        self.pretty_name = "Saw wave"

    def prob_curve(self, x, rand, voice_i=0):
        decreasing, min_prob, max_prob, period, offset = self.get(
            voice_i, "decreasing", "min_prob", "max_prob", "period", "offset"
        )
        result = saw(
            offset + x, min_prob, max_prob, period, decreasing=decreasing
        )
        if result > rand:
            return True
        return False


class Sine(OscCurve):
    """Sine oscillating probability curve class."""

    def __init__(
        self, min_prob=0, max_prob=1, period=4, length=0, decreasing=False
    ):
        super().__init__(
            min_prob=min_prob,
            max_prob=max_prob,
            length=length,
            decreasing=decreasing,
        )
        self.pretty_name = "Sine wave"

    def prob_curve(self, x, rand, voice_i=0):
        decreasing, min_prob, max_prob, period, offset = self.get(
            voice_i, "decreasing", "min_prob", "max_prob", "period", "offset"
        )
        result = cosine(
            offset + x, min_prob, max_prob, period, decreasing=decreasing
        )
        if result > rand:
            return True
        return False


class Accumulating(Static):
    """Accumulating probability curve class."""

    # LONGTERM: accommodate this to continuously varying rhythms somehow?
    def __init__(self, prob=0.05, decreasing=True, acc_modulo=8):
        super().__init__(prob=prob)
        self.pretty_name = "Accumulating"
        self.add_attribute(
            "acc_modulo",
            acc_modulo,
            "Accumulation modulo",
            int,
            attr_val_kwargs={"min_value": 0, "max_value": -1},
        )
        self.decreasing = None
        self.add_attribute(
            "decreasing", decreasing, "Decreasing", bool, unique=True
        )
        self.accumulated = {}

    def reset(self):
        self.accumulated = {}

    def prob_curve(self, x, rand, voice_i=0):
        # if voice_i not in self.accumulated:
        #     self.accumulated[voice_i] = []
        try:
            accumulated = self.accumulated[voice_i]
        except KeyError:
            accumulated = []
            self.accumulated[voice_i] = accumulated
        acc_modulo = self.get(voice_i, "acc_modulo")
        x_modulo = x % acc_modulo

        if x_modulo in accumulated and not self.decreasing:
            return True

        result = self.prob[voice_i % len(self.prob)]
        if result > rand:
            accumulated.append(x_modulo)
            if self.decreasing:
                return False
            return True

        if x_modulo not in accumulated and self.decreasing:
            return True

        return False


# MAYBE make accumulating function that can take a non-static probability?
# class Accumulating2(ProbCurve):
#     """Accumulating probability curve class.
#     """
#     def __init__(self, prob=0.05, sub_prob_type="static", decreasing=True,
#                  acc_modulo=8):
#         super().__init__(prob=prob)
#         self.pretty_name = "Accumulating2"
#         self.add_attribute(
#             "acc_modulo", acc_modulo, "Accumulation modulo",
#             int, attr_val_kwargs={"min_value": 0, "max_value": -1})
#         self.add_attribute(
#             "decreasing", decreasing, "Decreasing", bool, unique=True)
#         self.add_attribute(
#             "sub_prob_type", sub_prob_type, "Sub-probability curve:")
#         self.accumulated = {}
#
#     def reset(self):
#         self.accumulated = {}
#
#     def prob_curve(self, x, rand, voice_i=0):
#         if voice_i not in self.accumulated:
#             self.accumulated[voice_i] = []
#         accumulated = self.accumulated[voice_i]
#         acc_modulo = self.get(voice_i, "acc_modulo")
#         x_modulo = x % acc_modulo
#
#         if x_modulo in accumulated and not self.decreasing:
#             return True
#
#         result = self.prob[voice_i % len(self.prob)]
#         if result > rand:
#             accumulated.append(x_modulo)
#             if self.decreasing:
#                 return False
#             return True
#
#         if x_modulo not in accumulated and self.decreasing:
#             return True
#
#         return False


class RandomToggle(ProbCurve):
    """Random toggle probability curve class."""

    def __init__(self, on_prob=0.25, off_prob=0.25):
        super().__init__()
        self.add_attribute(
            "on_prob",
            on_prob,
            "On probability",
            float,
            attr_val_kwargs={"min_value": 0, "max_value": 1},
        )
        self.add_attribute(
            "off_prob",
            off_prob,
            "Off probability",
            float,
            attr_val_kwargs={"min_value": 0, "max_value": 1},
        )

        self.pretty_name = "Random toggle"
        self._on_dict = {}

    def reset(self):
        self._on_dict = {}

    def prob_curve(self, x, rand, voice_i=0):  # pylint: disable=unused-argument
        try:
            on_or_off = self._on_dict[voice_i]
        except KeyError:
            on_or_off = random.choice((True, False))
            self._on_dict[voice_i] = on_or_off
        if on_or_off:
            result = self.get(voice_i, "off_prob")
            if result > rand:
                self._on_dict[voice_i] = False
                return False
            return True
        # else off:
        result = self.get(voice_i, "on_prob")
        if result > rand:
            self._on_dict[voice_i] = True
            return True
        return False


def linear(x, min_prob, max_prob, length, decreasing=False):
    if decreasing:
        return (max_prob - min_prob) * ((-x) / length + 1) + min_prob
    return (max_prob - min_prob) * (x / length) + min_prob


def linear_decreasing(x, min_prob, max_prob, length):
    return linear(x, min_prob, max_prob, length, decreasing=True)


def quadratic(x, min_prob, max_prob, length, decreasing=False):
    if decreasing:
        return (max_prob - min_prob) * (-(((x) / length) ** 2) + 1) + min_prob
    return (max_prob - min_prob) * ((x / length) ** 2) + min_prob


def quadratic_decreasing(x, min_prob, max_prob, length):
    return quadratic(x, min_prob, max_prob, length, decreasing=True)


def static(prob, *args, **kwargs):  # pylint: disable=unused-argument
    return prob


def linear_osc(x, min_prob, max_prob, period, decreasing=False):
    mod_x = x % period
    slope_len = period / 2
    if decreasing:
        if mod_x > slope_len:
            return linear(mod_x - slope_len, min_prob, max_prob, slope_len)
        return linear(mod_x, min_prob, max_prob, slope_len, decreasing=True)
    if mod_x > slope_len:
        return linear(
            mod_x - slope_len, min_prob, max_prob, slope_len, decreasing=True
        )
    return linear(mod_x, min_prob, max_prob, slope_len)


def saw(x, min_prob, max_prob, period, decreasing=False):
    mod_x = x % period
    if decreasing:
        return linear(mod_x, min_prob, max_prob, period, decreasing=True)
    return linear(mod_x, min_prob, max_prob, period)


def saw_decreasing(x, min_prob, max_prob, period):
    return saw(x, min_prob, max_prob, period, decreasing=True)


def cosine(x, min_prob, max_prob, period, decreasing=False):
    result = (math.cos(math.pi * 2 * x / period) / 2 + 0.5) * (
        max_prob - min_prob
    ) + min_prob
    if decreasing:
        return result
    return -1 * result + 1


PROB_CURVES = tuple(
    name
    for name, cls in locals().items()
    if inspect.isclass(cls)
    and issubclass(cls, AttributeAdder)
    and cls
    not in (AttributeAdder, NullProbCurve, ProbCurve, NonStaticCurve, OscCurve)
)
