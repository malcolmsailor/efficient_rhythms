import types

from .. import er_changers


def _get_changer_dict():
    i = 1
    changer_dict = {}
    for filter_ in er_changers.FILTERS:
        changer_dict[i] = getattr(er_changers, filter_)
        i += 1
    # The next dictionary entry is added to mark the boundary
    #   between filters and transformers.
    changer_dict[-1] = None
    for transformer in er_changers.TRANSFORMERS:
        changer_dict[i] = getattr(er_changers, transformer)
        i += 1

    return types.MappingProxyType(changer_dict)


CHANGER_DICT = _get_changer_dict()
