import types
import typing
from numbers import Number
from typing import NewType, Optional, Sequence, Tuple, TypeVar, Union

import numpy as np

from .. import er_misc_funcs

from .type_check import _check_type


T = TypeVar("T")

JustPitch = NewType("JustPitch", float)
TemperedPitch = NewType("TemperedPitch", int)
Pitch = NewType("Pitch", Union[JustPitch, TemperedPitch])

JustPitchClass = NewType("JustPitchClass", float)
TemperedPitchClass = NewType("TemperedPitchClass", int)
PitchClass = NewType("PitchClass", Union[JustPitchClass, TemperedPitchClass])

GenericInterval = NewType("GenericInterval", int)
SpecificInterval = NewType("SpecificInterval", int)
Interval = NewType("Interval", Union[GenericInterval, SpecificInterval])

# class PitchSeq(Sequence[Pitch]):
#     pass

# class PitchSuperSeq(Sequence[PitchSeq]):
class SuperSequence(Sequence[Sequence[T]]):
    @staticmethod
    def process(x, er):
        if x is None:
            return None
        if not isinstance(x, Sequence) or isinstance(x, str):
            x = [x]
        if not isinstance(x[0], (Sequence, np.ndarray)):
            x = [x]
        return tuple(x)


# TODO eventually I would like to make the type of TimePoint more
#   constrained and harmonize it across the whole script
Metron = NewType("Metron", Number)

Tempo = Number

Voice = int


# VoiceRelations "should" derive from Union[bool, Sequence[Sequence[int]]], but
# we can't derive from Union. This will cause problems if I implement type-
# checking, so I'll have to figure out a solution for that.
# class VoiceRelations(Sequence[Sequence[int]], bool):
#     @staticmethod
#     def process(x, er):
#         if isinstance(x, bool):
#             if x:
#                 return (tuple(range(er.num_voices)),)
#             return ()
#         # else should be a sequence of sequences

#         x = list(x)
#         x = er_misc_funcs.remove_non_existing_voices(x, er.num_voices)
#         accounted_for_voices = [False for _ in range(er.num_voices)]
#         for voice_group in x:
#             for voice_i in voice_group:
#                 # TODO If we don't remove non-existing voices, we should do
#                 #   bounds-checking here
#                 accounted_for_voices[voice_i] = True
#         for voice_i, bool_ in enumerate(accounted_for_voices):
#             if not bool_:
#                 x.append((voice_i,))
#         return tuple(x)


Density = NewType("Density", float)
Quantity = NewType("Quantity", int)
DensityOrQuantity = NewType("DensityOrQuantity", Union[Density, Quantity])


# class ItemOrSeqMeta(type):
#     def _get_args(self):
#         pass

#     def __instancecheck__(self, instance: Any) -> bool:
#         return super().__instancecheck__(instance)


class ItemOrSeqBase:
    @staticmethod
    def process(x, er):
        if not isinstance(x, Sequence) or isinstance(x, str):
            return [x]
        return x

    @staticmethod
    def fill_none(er):
        return ()


class ItemOrSequence(ItemOrSeqBase, Sequence[T]):
    pass


class OptItemOrSequence(ItemOrSeqBase, Sequence[T]):
    pass


# I can't get deriving from this to work yet so for the moment
# I'm just copying the process method to each would-be derived class.
# The reason it doesn't work is because of a metaclass conflict. However,
# I do not understand why there should be such a conflict since PerVoiceBase
# derives from object
# The above comment seems to be out-of-date since I *am* deriving from
# PerVoiceBase now. But leaving it for the time being just in case there is any
# useful info in it.
class PerVoiceBase:
    @staticmethod
    def process(x, er):
        if not isinstance(x, Sequence) or isinstance(x, str):
            x = [x]
        return tuple(x[i % len(x)] for i in range(er.num_voices))

    @staticmethod
    def validate(t, x):
        if isinstance(x, Sequence) and not isinstance(x, str):
            for item in x:
                t.validate(t, item)
            return
        # The PerVoice idiom is that we want to allow either an item, or a
        # sequence of items. Later, we will wrap items in lists.
        args = typing.get_args(t)
        for arg in args:
            try:
                _check_type(arg, x)
            except TypeError:
                pass
            else:
                return
        # clean up NewType's
        args = [
            arg.__supertype__ if isinstance(arg, types.FunctionType) else arg
            for arg in args
        ]
        if len(args) == 1:
            msg = f"{x} is not of type {args[0]}"
        else:
            msg = f"type of {x} is not in {args}"
        raise TypeError(msg)


class PerVoiceSequence(PerVoiceBase, Sequence[T]):
    pass


class OptPerVoiceSequence(PerVoiceBase, Sequence[T]):
    # We can't subclass typing.Union. So instead, I just create this class
    # and I'll make a special condition to type-check for it in er_web # TODO
    pass


class PerVoiceSuperBase:
    @staticmethod
    def process(x, er):
        if x is None:
            return None
        if not isinstance(x, Sequence) or isinstance(x, str):
            x = [x]
        if not isinstance(x[0], Sequence) or isinstance(x[0], str):
            x = [x]
        return tuple(x[i % len(x)] for i in range(er.num_voices))

    @staticmethod
    def fill_none(er):
        return tuple(() for _ in range(er.num_voices))

    @staticmethod
    def sort(x, sort_kwargs):
        # we assume that x and its contents are tuples.
        x = list(x)
        for i, t in enumerate(x):
            l = list(t)
            l.sort(**sort_kwargs)
            x[i] = tuple(l)
        return x


class PerVoiceSuperSequence(PerVoiceSuperBase, Sequence[Sequence[T]]):
    pass


class OptPerVoiceSuperSequence(PerVoiceSuperBase, Sequence[Sequence[T]]):
    pass


# TODO is there a way we can also allow np arrays of the appropriate shape?
# TODO or maybe we should get rid of np arrays in preprocessing?
VoiceRange = Tuple[Pitch, Pitch]
VoiceRanges = Sequence[VoiceRange]
