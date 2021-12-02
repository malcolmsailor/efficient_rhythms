import collections
import types
import typing

# Type checking code based on https://stackoverflow.com/a/50622643/10155119


def _find_type_origin(type_hint):
    if isinstance(type_hint, typing._SpecialForm):
        # case of typing.Any, typing.ClassVar, typing.Final, typing.Literal,
        # typing.NoReturn, typing.Optional, or typing.Union without parameters
        return

    actual_type = (
        typing.get_origin(type_hint) or type_hint
    )  # requires Python 3.8
    if isinstance(actual_type, typing._SpecialForm):
        # case of typing.Union[…] or typing.ClassVar[…] or …
        for origins in map(_find_type_origin, typing.get_args(type_hint)):
            # yield from origins
            for origin in origins:
                if isinstance(origin, types.FunctionType):
                    # type_hint is from a call to NewType
                    yield origin.__supertype__
                else:
                    yield origin

    else:
        yield actual_type


def _check_type(type_hint, val):
    if isinstance(type_hint, types.FunctionType):
        # type_hint is from a call to NewType
        type_hint = type_hint.__supertype__
    if isinstance(type_hint, typing.TypeVar):
        constraints = type_hint.__constraints__
        if not constraints:
            return True
        for constraint in constraints:
            try:
                _check_type(constraint, val)
            except TypeError:
                pass
            else:
                return True
            raise TypeError("constraints not satisfied")

    actual_types = tuple(_find_type_origin(type_hint))
    if actual_types and not isinstance(val, actual_types):
        if hasattr(type_hint, "__orig_bases__"):
            for i, base in enumerate(type_hint.__orig_bases__):
                try:
                    _check_type(base, val)
                except TypeError:
                    if i == len(type_hint.__orig_bases__) - 1:
                        raise
                else:
                    break
        else:
            raise TypeError(
                f"Expected type '{type_hint}'"
                f" but received type '{type(val)}' instead"
            )
    if isinstance(val, typing.Dict):
        k_ty, v_ty = typing.get_args(type_hint)
        for k, v in val.items():
            _check_type(k_ty, k)
            _check_type(v_ty, v)
    elif isinstance(val, typing.Tuple):
        sub_type_hint_tup = typing.get_args(type_hint)
        for sub_type_hint, sub_val in zip(sub_type_hint_tup, val):
            _check_type(sub_type_hint, sub_val)
    elif isinstance(val, collections.abc.Sequence) and not isinstance(val, str):
        # max_len(val)
        sub_type_hint_tup = typing.get_args(type_hint)
        # we expect this to only have at most one member
        assert len(sub_type_hint_tup) <= 1
        if sub_type_hint_tup:
            sub_type_hint = sub_type_hint_tup[0]
            for sub_val in val:
                _check_type(sub_type_hint, sub_val)
    return None
