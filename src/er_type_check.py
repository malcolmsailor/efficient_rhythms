# """The code in this module is directly taken from
# https://stackoverflow.com/a/50622643/10155119
# The intended difference (not yet implemented) is that if the type check fails,
# we will check if it is a string reference to er_constants
# """

# # LONGTERM implement

# import inspect
# import typing
# from functools import wraps


# class PitchConstantError(Exception):
#     pass

# def process_er_constant_str(pitch_str):
#     pitch_str = pitch_str.replace("#", "_SHARP")
#     bits = pitch_str.split()
#     val = 1
#     next_op, rnext_op = "__mul__", "__rmul__"
#     for bit in bits:
#         if next_op is None:
#             try:
#                 next_op, rnext_op = PITCH_CONSTANT_OP_MAP[bit]
#             except KeyError:
#                 raise PitchConstantError(  # pylint: disable=raise-missing-from
#                     f"{bit} is not an implemented operation on pitch "
#                     "constants. Implemented pitch constant operations are "
#                     f"{tuple(PITCH_CONSTANT_OP_MAP.keys())}."
#                     # TODO see documentation for more help
#                 )
#         else:
#             try:
#                 constant = getattr(er_constants, bit)
#             except AttributeError:
#                 raise PitchConstantError(  # pylint: disable=raise-missing-from
#                     f"{bit} is not an implemented pitch constant."
#                 )
#                 # TODO see documentation for more help
#             next_val = getattr(val, next_op)(constant)
#             if next_val is NotImplemented:
#                 val = getattr(constant, rnext_op)(val)
#             else:
#                 val = next_val
#             next_op = None
#     if next_op is not None:
#         raise PitchConstantError(
#             f"Trailing operation in pitch constant {pitch_str}"
#         )
#     return val

# def _find_type_origin(type_hint):
#     if isinstance(type_hint, typing._SpecialForm):
#         # case of typing.Any, typing.ClassVar, typing.Final, typing.Literal,
#         # typing.NoReturn, typing.Optional, or typing.Union without parameters
#         yield typing.Any
#         return

#     actual_type = typing.get_origin(type_hint) or type_hint  # requires Python 3.8
#     if isinstance(actual_type, typing._SpecialForm):
#         # case of typing.Union[…] or typing.ClassVar[…] or …
#         for origins in map(_find_type_origin, typing.get_args(type_hint)):
#             yield from origins
#     else:
#         yield actual_type


# def _check_types(parameters, hints):
#     for name, value in parameters.items():
#         type_hint = hints.get(name, typing.Any)
#         actual_types = tuple(
#                 origin
#                 for origin in _find_type_origin(type_hint)
#                 if origin is not typing.Any
#         )
#         if actual_types and not isinstance(value, actual_types):
#             raise TypeError(
#                     f"Expected type '{type_hint}' for argument '{name}'"
#                     f" but received type '{type(value)}' instead"
#             )


# def enforce_types(callable):
#     def decorate(func):
#         hints = typing.get_type_hints(func)
#         signature = inspect.signature(func)

#         @wraps(func)
#         def wrapper(*args, **kwargs):
#             parameters = dict(zip(signature.parameters, args))
#             parameters.update(kwargs)
#             _check_types(parameters, hints)

#             return func(*args, **kwargs)
#         return wrapper

#     if inspect.isclass(callable):
#         callable.__init__ = decorate(callable.__init__)
#         return callable

#     return decorate(callable)


# def enforce_strict_types(callable):
#     def decorate(func):
#         hints = typing.get_type_hints(func)
#         signature = inspect.signature(func)

#         @wraps(func)
#         def wrapper(*args, **kwargs):
#             bound = signature.bind(*args, **kwargs)
#             bound.apply_defaults()
#             parameters = dict(zip(signature.parameters, bound.args))
#             parameters.update(bound.kwargs)
#             _check_types(parameters, hints)

#             return func(*args, **kwargs)
#         return wrapper

#     if inspect.isclass(callable):
#         callable.__init__ = decorate(callable.__init__)
#         return callable

#     return decorate(callable)
