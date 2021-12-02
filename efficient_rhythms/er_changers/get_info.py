"""A hack to get info about changers and prob curves for documentation.
"""

from . import prob_curves

# Prob curves and changers will subclass this class
class InfoGetter:
    def __init__(self):
        self.display_if = self.hint_dict = None
        self.validation_dict = None

    def _display_if_info(self, name):
        if (
            name
            in self.display_if  # pylint: disable=unsupported-membership-test
            and self.display_if[name] is not None
        ):
            out = []
            for k, v in self.display_if[name].items():
                if isinstance(v, (tuple, list)):
                    out.append(f"{k} in {v}")
                else:
                    if isinstance(v, str):
                        v = f"'{v}'"
                    out.append(f"{k} == {v}")
            return "Only has effect if " + ", ".join(out)
        return None

    @staticmethod
    def _format_attr_info(
        name, pretty_name, hint, display_if, default, val_info
    ):
        pretty_text = (
            "Description: "
            + pretty_name
            + "."
            + (" " + hint if hint is not None else "")
        )

        indented_l = [pretty_text]
        if display_if is not None:
            indented_l.append(display_if)
        indented_l.append(f"Default: {default}")
        indented_l.extend(val_info)
        indented_s = "\n".join("- " + line for line in indented_l) + "\n"
        return f"### {name}\n\n" + indented_s

    def _get_attr_info(self, name):
        pretty_name = self.interface_dict[name]  # pylint: disable=no-member
        hint = (
            self.hint_dict[name]
            if name
            in self.hint_dict  # pylint: disable=unsupported-membership-test
            else None
        )
        # It seems that I was also using hints to display relevant info
        # about the current midi file in the interface. So, for example,
        # for end_time, the hint is a tuple that tells the user what the
        # total length of the current file is. Here, though, we are trying to
        # export info for general help docs so info about any specific midi file
        # is clearly not useful.
        # In the long run I should revise this code so that hints are used
        # more consistently.
        if isinstance(hint, tuple):
            hint = None
        display_if = self._display_if_info(name)
        val_info = self.validation_dict[name].info()
        # This is obviously not necessarily the default value, but merely the
        # current value of the attribute. Here, we are trusting that this
        # function is only going to be called before changing any of the
        # instance's attributes. (I'm only calling it from
        # docs/resources/scripts/get_changers.py). But obviously it would be
        # better to rewrite the changers in a more sensible way (using
        # dataclasses?)
        default = getattr(self, name)
        if isinstance(default, prob_curves.NullProbCurve):
            default = default.__class__.__name__

        return self._format_attr_info(
            name, pretty_name, hint, display_if, default, val_info
        )

    def get_info(self):
        header = f"## {self.__class__.__name__}\n"
        pretty_text = (
            f"{self.pretty_name}."  # pylint: disable=no-member
            + (
                f" {self.description}."  # pylint: disable=no-member
                if self.description  # pylint: disable=no-member
                else ""
            )
        ) + "\n"
        out = [header, pretty_text]
        for name in self.interface_dict:  # pylint: disable=no-member
            out.append(self._get_attr_info(name))
        return "\n".join(out)
