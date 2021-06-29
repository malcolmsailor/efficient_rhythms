import inspect

from .. import er_misc_funcs

from .attribute_val import AttributeValidator


def ensure_list(obj, attr_str):
    """If given attributes of object are not inside a list,
    places them inside a list.
    """
    attribute = vars(obj)[attr_str]
    # special case for empty tuple:
    if attribute == ():
        return
    # TODO sometimes we would like to process tuples, other times not
    # TODO really we should use type annotations to validate more intelligently
    if not isinstance(attribute, (list)):
        vars(obj)[attr_str] = [
            attribute,
        ]


# TODO can't get "Range(s) to pass through filter" to work


class AttributeAdder:
    """Used as a bass class for Changer and ProbCurve classes."""

    description = ""

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
        for param_name in params:
            param_list = getattr(self, param_name)
            voice_param = param_list[voice_i % len(param_list)]
            out.append(voice_param)
            # out.append(vars(self)[param][voice_i % len(vars(self)[param])])
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
