import typing

from .types_ import (
    Density,
    DensityOrQuantity,
    GenericInterval,
    PitchClass,
    JustPitchClass,
    TemperedPitchClass,
    Metron,
    Pitch,
    JustPitch,
    TemperedPitch,
)


def _has(obj, types):
    try:
        if obj in types:
            return True
    except AttributeError:
        pass
    for arg in typing.get_args(obj):
        if _has(arg, types):
            return True
    return False


def has_pitches(obj):
    return _has(
        obj,
        (
            Pitch,
            JustPitch,
            TemperedPitch,
            PitchClass,
            JustPitchClass,
            TemperedPitchClass,
        ),
    )


def has_pitch_classes(obj):
    return _has(obj, (PitchClass, JustPitchClass, TemperedPitchClass))


def has_metron(obj):
    return _has(obj, (Metron,))


def has_density(obj):
    return _has(obj, (Density, DensityOrQuantity))


def has_interval(obj):
    return _has(obj, (GenericInterval,))
