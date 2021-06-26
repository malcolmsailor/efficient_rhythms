"""Rhythm functions for efficient_rhythms2.py.
"""
import fractions
import random
import warnings


import numpy as np

from .. import er_globals
from .. import er_midi

from .utils import get_iois
from .rhythm import Rhythm
from .cont_rhythm import ContRhythm
from .grid import Grid


def _obligatory_onsets(er, voice_i):
    oblig_onsets, oblig_mod, rhythm_len = er.get(
        voice_i, "obligatory_onsets", "obligatory_onsets_modulo", "rhythm_len"
    )
    if not oblig_onsets:
        return ()
    out = []
    i = 0
    while True:
        rep_i, onset_i = divmod(i, len(oblig_onsets))
        onset = rep_i * oblig_mod + oblig_onsets[onset_i]
        if onset >= rhythm_len:
            break
        out.append(onset)
        i += 1
    return tuple(out)


def _obligatory_onset_indices(er, voice_i, onset_positions):
    out = []
    if voice_i == 0 and er.force_foot_in_bass in (
        "first_beat",
        "global_first_beat",
    ):
        out.append(0)
        i = 1
    else:
        i = 0
    for onset in _obligatory_onsets(er, voice_i):
        while onset_positions[i] < onset:
            i += 1
        # If we enforce elsewhere that obligatory onsets must be possible
        # onsets, we can remove the following check
        if onset_positions[i] == onset:
            out.append(i)
    return tuple(out)


def _filter_indices(
    leaders, condition, conjunction, onset_positions, oblig_indices
):
    bool_mask = condition(leaders[0])
    for i in range(1, len(leaders)):
        bool_mask = conjunction(condition(leaders[i]), bool_mask)
    indices = np.flatnonzero(bool_mask)
    if oblig_indices:
        indices = indices[np.isin(indices, oblig_indices, invert=True)]
    return set(indices)


def _hocketing_indices(
    er, voice_i, onset_positions, prev_rhythms, oblig_indices
):
    leaders = (
        prev_rhythms[leader_i % len(prev_rhythms)]
        for leader_i in er.hocketing_followers[voice_i]
    )
    # cast to set first to remove duplicate references to rhythms, if any:
    leaders = [r.onsets for r in set(leaders)]
    condition = lambda x: np.isin(onset_positions, x, invert=True)
    conjunction = np.logical_and
    return _filter_indices(
        leaders, condition, conjunction, onset_positions, oblig_indices
    )


def _quasi_unison_constrained_indices(
    er, voice_i, onset_positions, prev_rhythms, oblig_indices
):
    # returns a tuple: "at_onset" (onset positions that occur simultaneously
    #   to the leader voice)
    #   "during": (onset positions that occur during the durations of the leader
    #   voice)
    def _oblig_generator():
        oblig_indices_iter = iter(oblig_indices)
        while True:
            try:
                yield next(oblig_indices_iter)
            except StopIteration:
                yield None

    # I don't think this does what I want insofar as I think *first* all
    #   unison onsets should be filled, then those that occur during the
    #   durations of the leader (otherwise we could get a case where onsets
    #   occur only during the held long notes of the leader)
    leader_i = er.rhythmic_quasi_unison_followers[voice_i]
    leader = prev_rhythms[leader_i % len(prev_rhythms)]

    leader_iter = iter(leader)
    onset_position_iter = iter(enumerate(onset_positions))
    oblig_gen = _oblig_generator()
    at_onset = set()
    during = set()
    try:
        next_leader_onset, next_leader_dur = next(leader_iter)
    except StopIteration:
        return at_onset, during
    next_leader_release = next_leader_onset + next_leader_dur
    oblig_i = next(oblig_gen)
    while True:
        try:
            i, onset = next(onset_position_iter)
            if oblig_i is not None and i == oblig_i:
                # We do *not* include obligatory indices because
                # those are handled separately
                oblig_i = next(oblig_gen)
                continue
            while onset >= next_leader_release:
                next_leader_onset, next_leader_dur = next(leader_iter)
                next_leader_release = next_leader_onset + next_leader_dur
            if next_leader_onset == onset:
                at_onset.add(i)
            elif next_leader_onset < onset:
                during.add(i)
        except StopIteration:
            break
    return at_onset, during


def _quasi_unison_indices(
    er, voice_i, onset_positions, prev_rhythms, oblig_indices
):
    if er.rhythmic_quasi_unison_constrain:
        return _quasi_unison_constrained_indices(
            er, voice_i, onset_positions, prev_rhythms, oblig_indices
        )
    # leaders = list(
    #     {
    #         prev_rhythms[leader_i % len(prev_rhythms)].onsets
    #         for leader_i in er.rhythmic_quasi_unison_followers[voice_i]
    #     }
    # )
    # I believe there can only be one "leader" (contrary to hocketing)
    leader_i = er.rhythmic_quasi_unison_followers[voice_i]
    leaders = [prev_rhythms[leader_i % len(prev_rhythms)].onsets]
    condition = lambda x: np.isin(onset_positions, x)
    # conjunction = np.logical_or
    conjunction = None
    out = _filter_indices(
        leaders, condition, conjunction, onset_positions, oblig_indices
    )
    return out, {}


def _add_comma(er, voice_i, onset_positions, comma):
    # TODO add comma to *onset positions* rather than to *onsets*
    # modifies onsets in-place
    if not comma or er.cont_rhythms != "none":
        return
    comma_position = er.comma_position[voice_i]
    if comma_position == "end":
        return

    # LONGTERM verify that this is working with complex subdivisions

    if isinstance(comma_position, int):
        comma_i = comma_position
        if comma_i > len(onset_positions):
            warnings.warn(
                f"Comma position for voice {voice_i} greater "
                "than number of onset positions in rhythm. Choosing a "
                "random comma position."
            )
            comma_i = random.randrange(len(onset_positions))
    else:
        if comma_position == "beginning":
            comma_i = 0
        elif comma_position == "middle":
            comma_i = random.randrange(1, len(onset_positions))
        else:
            comma_i = random.randrange(len(onset_positions) + 1)

    onset_positions[comma_i:] += comma


# def _sub_subdivision_proportions(sub_subdivisions):
#     # TODO datatype
#     return np.cumsum(sub_subdivisions, dtype=np.float32) / np.sum(
#         sub_subdivisions, dtype=np.float32
#     )


def _onset_positions(er, voice_i):
    """Returns an np array of possible onset times."""

    if er.cont_rhythms == "grid":
        return er.grid.initial_onset_positions

    # TODO I believe I can remove all calls to "er.get" in this module
    rhythm_len, onset_subdivision, proportions = er.get(
        voice_i, "rhythm_len", "onset_subdivision", "sub_subdiv_props"
    )
    n_onsets, comma = divmod(rhythm_len, onset_subdivision)
    indices = np.arange(n_onsets)
    onset_positions = indices * onset_subdivision
    if proportions is not None:
        normalized_proportions = proportions * onset_subdivision
        onset_positions = np.repeat(onset_positions, len(proportions))
        onset_positions += np.tile(normalized_proportions, n_onsets)
    _add_comma(er, voice_i, onset_positions, comma)
    return onset_positions


def _swap_indices(indices, to_swap, start_i):
    if start_i == 0:
        i = -1
        for i, j in enumerate(to_swap):
            indices[[i, j]] = indices[[j, i]]
        return i + 1
    stop_i = start_i + len(to_swap)
    for j, i in enumerate(indices[start_i:], start=start_i):
        if i in to_swap:
            indices[[start_i, j]] = indices[[j, start_i]]
            start_i += 1
            if start_i == stop_i:
                break
    return start_i


def _indices_handler(er, voice_i, prev_rhythms, onset_positions):
    indices = np.arange(len(onset_positions))

    oblig_indices = _obligatory_onset_indices(er, voice_i, onset_positions)
    oblig_i_end = _swap_indices(indices, oblig_indices, 0)
    # hocketing and quasi_unison indices are complements of one another
    #   eventually I should refactor this to take more advantage of that fact!
    if voice_i in er.rhythmic_quasi_unison_followers:
        unison_indices, constrain_indices = _quasi_unison_indices(
            er, voice_i, onset_positions, prev_rhythms, oblig_indices
        )
        unison_i_end = _swap_indices(indices, unison_indices, oblig_i_end)
        constrain_i_end = _swap_indices(
            indices, constrain_indices, unison_i_end
        )
    else:
        unison_i_end = oblig_i_end
        constrain_i_end = oblig_i_end
    if voice_i in er.hocketing_followers:
        if voice_i in er.rhythmic_quasi_unison_followers:
            hocketing_i_end = len(indices)
        else:
            hocketing_indices = _hocketing_indices(
                er, voice_i, onset_positions, prev_rhythms, oblig_indices
            )

            hocketing_i_end = _swap_indices(
                indices, hocketing_indices, constrain_i_end
            )
    else:
        hocketing_i_end = constrain_i_end

    return indices, [
        oblig_i_end,
        unison_i_end,
        constrain_i_end,
        hocketing_i_end,
    ]


def get_onsets(er, voice_i, prev_rhythms):
    # TODO: don't use fractions, convert to fractions later
    onset_positions = _onset_positions(er, voice_i)
    indices, i_bounds = _indices_handler(
        er, voice_i, prev_rhythms, onset_positions
    )

    num_notes = er.get(voice_i, "num_notes")
    # can num_notes ever be greater than len(onset_positions)? I should
    # enforce no and then remove the call to min()

    num_remaining = min(num_notes, len(onset_positions))
    num_remaining -= i_bounds[0]  # oblig_i_end

    for start_i, end_i in zip(i_bounds, i_bounds[1:] + [len(onset_positions)]):
        if num_remaining <= 0:
            # we don't need to shuffle portions of the array that we will
            #   not use
            break
        er_globals.RNG.shuffle(indices[start_i:end_i])
        num_remaining -= end_i - start_i

    if num_notes > len(onset_positions) / 2:
        bool_mask = np.ones(len(onset_positions), dtype=bool)
        for i in indices[num_notes:]:
            bool_mask[i] = False
    else:
        bool_mask = np.zeros(len(onset_positions), dtype=bool)
        for i in indices[:num_notes]:
            bool_mask[i] = True
    onsets = onset_positions[bool_mask]
    return onsets


def get_iois_from_er(er, voice_i, onsets):
    return get_iois(onsets, er.rhythm_len[voice_i], er.overlap)


def _yield_onset_and_consecutive_release(rhythm):
    i = 0
    try:
        while True:
            onset, dur = rhythm._data.peekitem(i)
            first_onset = onset
            while (
                i + 1 < len(rhythm.onsets)
                and onset + dur == rhythm.onsets[i + 1]
            ):
                i += 1
                onset, dur = rhythm._data.peekitem(i)
            yield first_onset, onset + dur
            i += 1
    except IndexError:
        pass


def _within_leader_durs(er, voice_i, iois, onsets, leader_rhythm):
    leader_gen = _yield_onset_and_consecutive_release(leader_rhythm)
    out = np.minimum(iois, er.min_dur[voice_i])
    try:
        next_leader_onset, next_leader_release = next(leader_gen)
    except StopIteration:
        return out
    onset_iter = iter(enumerate(onsets))
    while True:
        try:
            i, onset = next(onset_iter)
            while onset >= next_leader_release:
                next_leader_onset, next_leader_release = next(leader_gen)
            if onset >= next_leader_onset:
                out[i] = min(iois[i], next_leader_release - onset)
        except StopIteration:
            break
    return out


def _durs_handler(er, voice_i, durs, within):

    dur_subdivision = er.dur_subdivision[voice_i]

    remaining = within - durs
    total_remaining = (
        er.dur_density[voice_i] * er.rhythm_len[voice_i] - durs.sum()
    )
    available_durs = {i: r for (i, r) in enumerate(remaining) if within[i] != r}
    available_indices = list(available_durs)
    n_indices = len(available_indices)

    # Our stopping point is rounded to the nearest dur_subdivision
    stopping_threshold = dur_subdivision / 2
    # In the case where er.overlap is False and the rhythm begins with a rest,
    #   we may not be able to reach the stopping threshold, so we also need to
    #   check whether there are any available durations to fill
    while total_remaining > stopping_threshold and n_indices:
        # to my surprise, random.choice(dict) returns values, not keys,
        #   which is why we need another solution here
        j = random.randrange(n_indices)
        i = available_indices[j]
        r = available_durs[i]
        if r <= dur_subdivision:
            increment = r
            n_indices -= 1
            if j != n_indices:
                available_indices[j], available_indices[n_indices] = (
                    available_indices[n_indices],
                    available_indices[j],
                )
        else:
            increment = dur_subdivision
            available_durs[i] -= increment
        durs[i] += increment
        total_remaining -= increment

    return total_remaining <= stopping_threshold


def get_durs(er, voice_i, iois, onsets, prev_rhythms):
    # MAYBE if onset_density > .5, *remove* duration?
    durs = np.minimum(iois, er.min_dur[voice_i])
    if (
        voice_i in er.rhythmic_quasi_unison_followers
        and er.rhythmic_quasi_unison_constrain
    ):
        leader_i = er.rhythmic_quasi_unison_followers[voice_i]
        leader = prev_rhythms[leader_i % len(prev_rhythms)]
        within_leader_durs = _within_leader_durs(
            er, voice_i, iois, onsets, leader
        )
        done = _durs_handler(er, voice_i, durs, within_leader_durs)
        if done:
            return durs
    _durs_handler(er, voice_i, durs, iois)
    return durs


def generate_rhythm(er, voice_i, prev_rhythms=()):
    if voice_i in er.rhythmic_unison_followers:
        return

    if er.cont_rhythms == "all":
        # methods from the previous version that I have not yet implemented (and
        # I'm not sure that I need to implement):
        #    rhythm.truncate_or_extend()
        #    rhythm.round()
        er.rhythms[voice_i].generate()
        return

    onsets = get_onsets(er, voice_i, prev_rhythms)
    er.check_time()
    iois = get_iois_from_er(er, voice_i, onsets)
    er.check_time()
    if er.cont_rhythms == "grid":
        durs = er.grid.get_durs(er, voice_i, onsets, prev_rhythms)
    else:
        durs = get_durs(er, voice_i, iois, onsets, prev_rhythms)
    er.check_time()
    if er.cont_rhythms == "grid":
        onsets, durs = er.grid.vary(onsets, durs)
    # rhythm = Rhythm.from_er_settings(er, voice_i)
    er.rhythms[voice_i].set_onsets_and_durs(onsets, durs)


def update_pattern_vl_order(er):
    rhythms = er.rhythms
    start_indices = [0 for _ in rhythms]
    for vl_item in er.pattern_vl_order:
        voice_i = vl_item.voice_i
        end_i = rhythms[voice_i].get_i_at_or_after(vl_item.end_time)
        first_onset, _ = rhythms[voice_i].at_or_after(vl_item.start_time)
        vl_item.set_indices(start_indices[voice_i], end_i, first_onset)
        start_indices[voice_i] = end_i


def rhythms_handler(er):
    """According to the parameters in er, return rhythms."""

    if er.rhythms_specified_in_midi:
        return

    for voice_i in range(er.num_voices):
        generate_rhythm(er, voice_i, prev_rhythms=er.rhythms[:voice_i])

    if not any(er.rhythms):

        class EmptyRhythmsError(Exception):
            pass

        raise EmptyRhythmsError(
            "No notes in any rhythms! This is a bug in the script."
        )

    update_pattern_vl_order(er)


def init_rhythms(er):
    if er.rhythms_specified_in_midi:
        er.rhythms = er_midi.get_rhythms_from_midi(er)
        return
    if er.cont_rhythms == "grid":
        er.grid = Grid.from_er_settings(er)
        er.grid.generate()

    if er.cont_rhythms == "all":
        r_class = ContRhythm
    else:
        r_class = Rhythm
    er.rhythms = []
    for voice_i in range(er.num_voices):
        if voice_i in er.rhythmic_unison_followers:
            leader_i = er.rhythmic_unison_followers[voice_i]
            er.rhythms.append(er.rhythms[leader_i])
        else:
            er.rhythms.append(r_class.from_er_settings(er, voice_i))


def get_onset_order(er):
    # TODO revise this function?

    end_time = max(er.pattern_len)

    class NoMoreAttacksError(Exception):
        pass

    def _get_next_onset():
        next_onset = end_time ** 2
        increment_i = -1
        for i in er.voice_order:
            try:
                next_onset_in_voice = onsets[i][voice_is[i]]
            except IndexError:
                continue
            if next_onset_in_voice < next_onset:
                next_onset = next_onset_in_voice
                increment_i = i
        if next_onset == end_time ** 2:
            raise NoMoreAttacksError()
        voice_is[increment_i] += 1
        return next_onset, increment_i

    onsets = [
        rhythm.onsets_between(0, pattern_len)
        for (rhythm, pattern_len) in zip(er.rhythms, er.pattern_len)
    ]
    voice_is = [0 for i in range(er.num_voices)]
    ordered_onsets = []
    while True:
        try:
            next_onset, voice_i = _get_next_onset()
        except NoMoreAttacksError:
            break
        if next_onset >= end_time:
            break
        # TODO remove this cast?
        ordered_onsets.append((voice_i, fractions.Fraction(next_onset)))
    return ordered_onsets
