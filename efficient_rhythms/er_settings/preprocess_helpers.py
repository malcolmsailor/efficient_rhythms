import random

from .defaults import (
    DEFAULT_NUM_HARMONIES,
    MAX_SUPER_PATTERN_LEN,
    MAX_SUPER_PATTERN_LEN_RANDOM,
)


def get_max_super_pattern_len(er):
    if er.randomized:
        return MAX_SUPER_PATTERN_LEN_RANDOM
    return MAX_SUPER_PATTERN_LEN


def len_all_harmonies(er):
    try:
        return sum(er.harmony_len) / len(er.harmony_len) * er.num_harmonies
    except TypeError:  # er.harmony_len is not iterable
        return er.harmony_len * er.num_harmonies


def get_num_harmonies(er):
    if er.foot_pcs is not None:
        return len(er.foot_pcs)
    return DEFAULT_NUM_HARMONIES


def random_foot_pcs(er):
    # TODO integrate interval_cycle here?
    return tuple(random.randrange(0, er.tet) for _ in range(er.num_harmonies))


def counting_order(er):
    return tuple(i for i in range(er.num_voices))


def random_tempi(er):
    if not er.tempo_len:
        n = 1
    else:
        n = len(er.tempo_len)
    return tuple(random.randrange(*er.tempo_bounds) for _ in range(n))


def guess_time_sig(er):
    temp_time_signature = max(
        er.pattern_len
        + [
            sum(er.harmony_len),
        ]
    )
    i = 0
    numer = temp_time_signature
    while numer % 1 != 0:
        i += 1
        numer = temp_time_signature * 2 ** i
        if i == 8:

            class TimeSigError(Exception):
                pass

            raise TimeSigError(
                f"No time signature denominator below {4 * 2**i}"
            )

    denom = 4 * 2 ** i

    for i in range(2, int(numer) + 1):
        if numer % i == 0:
            numer = i
            break

    return (numer, denom)
