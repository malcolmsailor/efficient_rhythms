import collections
import types
import typing
from typing import Optional, Union
from numbers import Number

from efficient_rhythms.er_types import *

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
        elif typing.get_origin(type_hint) is Union:
            t_args = typing.get_args(type_hint)
            for i, base in enumerate(t_args):
                try:
                    _check_type(base, val)
                except TypeError:
                    if i == len(t_args) - 1:
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
        t_args = typing.get_args(type_hint)
        if typing.get_origin(type_hint) is Union:
            # Get underlying type from Optional types
            if len(t_args) == 2 and type(None) in t_args:
                real_type = t_args[0] if t_args[1] is type(None) else t_args[1]
                t_args = typing.get_args(real_type)
        # we expect t_args to only have at most one member
        assert len(t_args) <= 1
        if t_args:
            sub_type_hint = t_args[0]
            for sub_val in val:
                _check_type(sub_type_hint, sub_val)


def test_types():
    succeed = (
        (JustPitch, 1.0),
        (TemperedPitch, 11),
        (Pitch, 1.0),
        (Pitch, 11),
        (Metron, 1.0),
        (PerVoiceSequence, [1, 2, 3]),
        (typing.List[JustPitch], [1.0, 2.0]),
        (PerVoiceSequence[JustPitch], [1.0, 2.0]),
        (Density, 0.1),
        (Quantity, 1),
        (DensityOrQuantity, 0.1),
        (DensityOrQuantity, 1),
        (Optional[PerVoiceSequence[DensityOrQuantity]], [0.1, 1]),
    )
    fail = (
        (PerVoiceSequence[JustPitch], [1, 2, 3]),
        (JustPitch, 1),
        (TemperedPitch, 11.0),
        (Metron, "foobar"),
        (PerVoiceSequence, 1),
        (Density, [0.1]),
        (Quantity, 0.1),
        (DensityOrQuantity, "foobar"),
        (Optional[PerVoiceSequence[DensityOrQuantity]], [0.1, 1, "foobar"]),
    )
    for type_hint, val in succeed:
        _check_type(type_hint, val)
    for type_hint, val in fail:
        try:
            _check_type(type_hint, val)
        except TypeError:
            pass
        else:
            raise TypeError("type check should have failed")


def test_per_voice_validate():
    pvs = PerVoiceSequence[Pitch]
    succeed = [
        1.0,
        1,
        (1.0, 2.5),
        [1, 2, 3],
    ]
    fail = [
        "foobar",
        ("foo", "bar"),
    ]
    for val in succeed:
        pvs.validate(pvs, val)
    for val in fail:
        try:
            pvs.validate(pvs, val)
        except TypeError as exc:
            print(exc)
        else:
            raise TypeError(f"{val} should have raised a TypeError")


def test_has():
    have_pitches = (
        SuperSequence[Pitch],
        PerVoiceSequence[Pitch],
        JustPitch,
        Optional[ItemOrSequence[TemperedPitch]],
    )
    no_pitches = (Metron, PerVoiceSequence[int], DensityOrQuantity)
    for t in have_pitches:
        assert has_pitches(t)
    for t in no_pitches:
        assert not has_pitches(t)
    have_metrons = (
        PerVoiceSequence[Metron],
        Metron,
        Optional[ItemOrSequence[Metron]],
    )
    no_metrons = (
        float,
        PerVoiceSequence[int],
        DensityOrQuantity,
        Number,
        list[Number],
    )
    for t in have_metrons:
        assert has_metron(t)
    for t in no_metrons:
        assert not has_metron(t)
