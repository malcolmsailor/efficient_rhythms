import fractions
import math
import numbers
from typing import Iterable

from .. import er_misc_funcs


class AttributeValidator:
    """Validates instance attributes for the classes ProbCurve and
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
        possible_values: Iterable[str] = (),
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

    def info(self):
        out = []
        out.append(f"Type: {self.type_.__name__}")
        if self.type_ == bool:
            pass
        elif issubclass(self.type_, numbers.Number):
            out.append(f"Min: {self.min_value}")
            if self.max_value >= 0:
                out.append(f"Max: {self.max_value}")
        elif self.possible_values:
            out.append(
                "Possible values: "
                + ", ".join(f"'{poss_val}'" for poss_val in self.possible_values)
            )
        out.append("Unique: " + ("yes" if self.unique else "no"))
        return out
        # return "    " + "\n    ".join(out)

    def validate(self, answer):
        """Validates and casts the input data.

        Takes a string. Returns None if validation fails, otherwise
        returns the cast input.
        """

        def _sub_validate(bit):
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

            if self.possible_values and str(bit) not in self.possible_values:
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
            # TODO I suspect ast.literal_eval would be just fine here and below
            answer = eval(listed)  # pylint: disable=eval-used

            return answer

        if self.type_ == str:
            if "'" not in answer and '"' not in answer:
                answer = str(enquote(answer, self.unique))
        try:
            answer = eval(answer)  # pylint: disable=eval-used
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
        """Returns a string explaining the possible values for the attribute."""
        if self.type_ in (float, int):
            if self.max_value < 0:
                return f"Enter a number >= {self.min_value}: "
            return f"Enter a number between {self.min_value} and " f"{self.max_value}: "
        if self.type_ == str:
            return f"Possible values: {self.possible_values}: "
        if self.type_ == bool:
            return "Possible values: 'True' or 'False'"
        # CHANGER_TODO look for a help string?
        return "Sorry, possible values for this attribute not implemented yet!"
