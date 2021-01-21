import fractions
import math
import numbers
import random

import src.er_misc_funcs as er_misc_funcs


def ensure_list(obj, attr_str):
    """If given attributes of object are not inside a list,
    places them inside a list.
    """
    attribute = vars(obj)[attr_str]
    # special case for empty tuple:
    if attribute == ():
        return
    if not isinstance(attribute, (list)):
        vars(obj)[attr_str] = [
            attribute,
        ]


class AttributeAdder:
    """Used as a bass class for Changer and ProbFunc classes.

    """

    def __init__(self):
        super().__init__()
        self.hint_dict = {}
        self.interface_dict = {}
        self.validation_dict = {}
        self.display_if = {}
        self.desc_dict = {}

    def add_attribute(
        self,
        attr_name,
        attr_value,
        attr_pretty_name,
        attr_type,
        attr_val_kwargs=None,
        attr_hint=None,
        unique=False,
        display_if=None,
        description=None,
    ):
        """
        Arguments:
            attr_name: attribute name
            attr_value: attribute value
            attr_pretty_name: Attribute name as it should appear in user
                interface.
            attr_type: data type of attribute value.
        Keyword arguments:
            attr_val_kwargs: Dict. Keyword arguments for attribute validator.
                (See AttributeValidator class.) Default: None.
            attr_hint: String. Brief explanatory text to appear in user
                interface, on the right margin at the attribute selection
                screen.
                Default: None.
            unique: Boolean. If false, attribute value will be placed in a list
                if not already an iterable. CHANGER_TODO I think this is placing
                    tuples etc. in lists too.
            display_if: CHANGER_TODO
            description: String. Longer explanatory text to appear under the
                header when adjusting the attribute.
        """
        setattr(self, attr_name, attr_value)
        self.interface_dict[attr_name] = attr_pretty_name
        if attr_val_kwargs is None:
            attr_val_kwargs = {}
        self.validation_dict[attr_name] = AttributeValidator(
            attr_type, **attr_val_kwargs, unique=unique
        )
        if attr_hint:
            self.hint_dict[attr_name] = attr_hint
        if not unique:
            ensure_list(self, attr_name)
        self.display_if[attr_name] = display_if
        self.desc_dict[attr_name] = description

    def get(self, voice_i, *params):
        out = []
        for param in params:
            try:
                out.append(vars(self)[param][voice_i % len(vars(self)[param])])
            except TypeError:  # CHANGER_TODO delete this try/except?
                breakpoint()
        if len(out) == 1:
            out = out[0]
        return out

    def display(self, attr_name):
        if self.display_if[attr_name] is None:
            return True
        for attr, val in self.display_if[attr_name].items():
            actual_attr_val = getattr(self, attr)
            if val == "true":
                if actual_attr_val:
                    if (
                        isinstance(actual_attr_val, (list, tuple))
                        and len(set(actual_attr_val)) == 1
                        and not actual_attr_val[0]
                    ):
                        return False
                    return True
                return False
            if val == "non_empty":
                return not er_misc_funcs.empty_nested(actual_attr_val)
            if isinstance(val, (tuple, list)) and actual_attr_val in val:
                return True
            if actual_attr_val != val:
                return False
        return True


class AttributeValidator:
    """Validates instance attributes for the classes ProbFunc and
    er_changers.Changer.

    Attributes:
        type_: the type of the attribute, or if the attribute is a tuple or
            list, the type of its members.
        min_value: the minimum value for numeric attributes.
        max_value: the maximum value for numeric attributes. If < 0, then
            there is no maximum value.
        possible_values: a list or tuple of possible values to check the
            attribute against. (Pass an empty list to disable.)
        unique: bool. Indicates that an attribute should not be placed into
            a list.
        tuple_of: required number of elements in a tuple. If a negative int,
            then the number of elements must divide that number evenly,
            and the elements will be grouped into sub-tuples of that size.
            (E.g., if -2, then there must be an even number of elements, and
            they will be returned as a tuple of 2-tuples.)
    Methods:
        possible_values_str(): returns a string containing the possible values,
            for help in the shell.
        validate(): validates and casts the input data. Returns None if
            validation fails, otherwise returns the cast input.
    """

    def __init__(
        self,
        type_,
        min_value=0,
        max_value=1,
        possible_values=(),
        unique=False,
        tuple_of=0,
        iter_of_iters=False,
        empty_ok=False,
        sort=False,
    ):
        self.type_ = type_
        self.min_value = min_value
        self.max_value = max_value
        if type_ == bool:
            self.possible_values = ("True", "False")
        else:
            self.possible_values = possible_values
            for possible_value in possible_values:
                if " " in possible_value:
                    raise ValueError(
                        "Possible values cannot contain spaces. "
                        f"Change possible value '{possible_value}'"
                    )
        self.unique = unique
        self.tuple_of = tuple_of
        self.iter_of_iters = iter_of_iters
        self.empty_ok = empty_ok
        self.sort = sort

    def validate(self, answer):
        """Validates and casts the input data.

        Takes a string. Returns None if validation fails, otherwise
        returns the cast input.
        """

        def _sub_validate(bit):
            # breakpoint()
            if isinstance(bit, (list, tuple)):
                if self.tuple_of > 0:
                    if (
                        not isinstance(bit[0], (list, tuple))
                        and len(bit) != self.tuple_of
                    ):
                        return None
                elif self.tuple_of < 0:
                    if len(bit) == 0:
                        if self.empty_ok:
                            return bit
                        return False
                    if (
                        not isinstance(bit[0], (list, tuple))
                        and len(bit) % (self.tuple_of * -1) != 0
                    ):
                        return None

                out = []
                for piece in bit:
                    # breakpoint()
                    new_piece = _sub_validate(piece)
                    if new_piece is None:
                        return None
                    out.append(new_piece)
                if self.sort:
                    out.sort()
                return out

            if not isinstance(bit, self.type_):
                try:
                    if self.type_ == fractions.Fraction:
                        bit = self.type_(bit).limit_denominator(
                            max_denominator=er_misc_funcs.MAX_DENOMINATOR
                        )
                    else:
                        bit = self.type_(bit)
                except ValueError:
                    try:
                        bit = self.type_(f"'{bit}'")
                    except ValueError:
                        return None

            if self.possible_values and bit not in self.possible_values:
                return None

            if isinstance(bit, numbers.Number):
                if bit < self.min_value:
                    return None
                if self.max_value >= 0 and bit > self.max_value:
                    return None

            return bit

        def enquote(answer, unique):
            """If self.type_ is str, places the items of the answer in quotes
            if the user did not do so.

            Doesn't cope with nested lists.
            """
            if unique:
                return f"'{answer}'"
            if answer.count("[") + answer.count("(") > 1:
                print(
                    "Warning: can't parse nested lists properly unless\n"
                    "    all strings are enclosed in quotes."
                )
            bits = (
                answer.replace(" ", "")
                .replace("[", "")
                .replace("]", "")
                .replace("(", "")
                .replace(")", "")
                .split(",")
            )
            enquoted = []
            for bit in bits:
                enquoted.append(f"'{bit}'")
            joined = ", ".join(enquoted)
            listed = f"[{joined}]"
            answer = eval(listed)

            return answer

        if self.type_ == str:
            if "'" not in answer and '"' not in answer:
                answer = str(enquote(answer, self.unique))
        try:
            answer = eval(answer)
        except SyntaxError:
            return None
        except NameError:
            return None

        if not self.unique:
            if not isinstance(answer, (list, tuple)):
                answer = [
                    answer,
                ]
            if self.tuple_of < 0:
                sub_tuple = self.tuple_of * -1
                new_list = []
                for j in range(math.ceil(len(answer) / sub_tuple)):
                    new_list.append(answer[j * sub_tuple : (j + 1) * sub_tuple])
                answer = new_list

        # if _sub_validate(answer) is None:
        #     return None
        print(answer)
        answer = _sub_validate(answer)

        if answer is None:
            return None

        if self.unique:
            if isinstance(answer, (list, tuple)):
                return answer[0]

        if self.iter_of_iters:
            try:
                iter(answer[0])
                return answer
            except TypeError:
                return [
                    answer,
                ]

        return answer

    def possible_values_str(self):
        """Returns a string explaining the possible values for the attribute.
        """
        if self.type_ in (float, int):
            if self.max_value < 0:
                return f"Enter a number >= {self.min_value}: "
            return (
                f"Enter a number between {self.min_value} and "
                f"{self.max_value}: "
            )
        if self.type_ == str:
            return f"Possible values: {self.possible_values}: "
        if self.type_ == bool:
            return "Possible values: 'True' or 'False'"
        # CHANGER_TODO look for a help string?
        return "Sorry, possible values for this attribute not implemented yet!"


class NullProbFunc(AttributeAdder):
    def __init__(self, **kwargs):  # pylint: disable=unused-argument
        super().__init__()
        self.pretty_name = "Null (Always on)"

    def _get_seg_len(  # pylint: disable=unused-argument,no-self-use
        self, *args
    ):
        return 1

    def calculate(  # pylint: disable=unused-argument,no-self-use
        self, *args, **kwargs
    ):
        return True


class ProbFunc(NullProbFunc):
    """Base class for probability function classes.

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
            of the probability function, where 1 is a quarter note.
            If the grain is, e.g., 0.5, then the function will
            only decrement self.seg_len_range at each new 8th note
            (although it will only decrement once for notes longer
            than an 8th note). This could, for instance, chop up
            a stream of 16th notes into 8th-note length segments.
        self.grain_offset: (list of) numbers. The offset (from 0)
            at which granularity is calculated (so, e.g., with a
            granularity of 1 and a grain_offset of 0.25, the
            probability function will apply to groups of 4 16ths
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
                self.prob_func(  # pylint: disable=no-member
                    x, rand, voice_i=voice_i
                )
            )
            self._on_dict[voice_i] = result
            return result

        if self._on_dict[voice_i]:
            return True
        return False


class Static(ProbFunc):
    """Static probability function class.
    """

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

    def prob_func(self, x, rand, voice_i=0):  # pylint: disable=unused-argument
        if self.prob[voice_i % len(self.prob)] > rand:
            return True
        return False


class NonStaticFunc(ProbFunc):
    """Base class for non-static probability function classes.
    """

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


class Linear(NonStaticFunc):
    """Linear probability function class.
    """

    def __init__(self, min_prob=0, max_prob=1, length=0, decreasing=False):
        super().__init__(
            min_prob=min_prob,
            max_prob=max_prob,
            length=length,
            decreasing=decreasing,
        )
        self.pretty_name = "Linear"

    def prob_func(self, x, rand, voice_i=0):
        decreasing, min_prob, max_prob = self.get(
            voice_i, "decreasing", "min_prob", "max_prob"
        )
        result = linear(
            x, min_prob, max_prob, self.length, decreasing=decreasing
        )
        if result > rand:
            return True
        return False


class Quadratic(NonStaticFunc):
    """Quadratic probability function class."""

    def __init__(self, min_prob=0, max_prob=1, length=0, decreasing=False):
        super().__init__(
            min_prob=min_prob,
            max_prob=max_prob,
            length=length,
            decreasing=decreasing,
        )
        self.pretty_name = "Quadratic"

    def prob_func(self, x, rand, voice_i=0):
        decreasing, min_prob, max_prob = self.get(
            voice_i, "decreasing", "min_prob", "max_prob"
        )
        result = quadratic(
            x, min_prob, max_prob, self.length, decreasing=decreasing
        )
        if result > rand:
            return True
        return False


class OscFunc(NonStaticFunc):
    """Base class for oscillating non-static probability functions.
    """

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


class LinearOsc(OscFunc):
    """Linear oscillating probability function class.
    """

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

    def prob_func(self, x, rand, voice_i=0):
        decreasing, min_prob, max_prob, period, offset = self.get(
            voice_i, "decreasing", "min_prob", "max_prob", "period", "offset"
        )
        result = linear_osc(
            offset + x, min_prob, max_prob, period, decreasing=decreasing
        )
        if result > rand:
            return True
        return False


class Saw(OscFunc):
    """Saw oscillating probability function class.
    """

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

    def prob_func(self, x, rand, voice_i=0):
        decreasing, min_prob, max_prob, period, offset = self.get(
            voice_i, "decreasing", "min_prob", "max_prob", "period", "offset"
        )
        result = saw(
            offset + x, min_prob, max_prob, period, decreasing=decreasing
        )
        if result > rand:
            return True
        return False


class Sine(OscFunc):
    """Sine oscillating probability function class.
    """

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

    def prob_func(self, x, rand, voice_i=0):
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
    """Accumulating probability function class.
    """

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

    def prob_func(self, x, rand, voice_i=0):
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
# class Accumulating2(ProbFunc):
#     """Accumulating probability function class.
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
#             "sub_prob_type", sub_prob_type, "Sub-probability function:")
#         self.accumulated = {}
#
#     def reset(self):
#         self.accumulated = {}
#
#     def prob_func(self, x, rand, voice_i=0):
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


class RandomToggle(ProbFunc):
    """Random toggle probability function class.
    """

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

    def prob_func(self, x, rand, voice_i=0):  # pylint: disable=unused-argument
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


if __name__ == "__main__":
    for i in range(48):
        print(linear(i, 0, 1, 48))
