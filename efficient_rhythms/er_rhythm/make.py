"""Rhythm functions for efficient_rhythms2.py.
"""
import fractions
import random
import warnings


import numpy as np

from .. import er_globals
from .. import er_midi

from .rhythm import Rhythm
from .cont_rhythm import ContinuousRhythm
from .grid import Grid


def _obligatory_onsets(er, voice_i):
    oblig_onsets, oblig_mod, rhythm_len = er.get(
        voice_i, "obligatory_onsets", "obligatory_onsets_modulo", "rhythm_len"
    )
    if not oblig_onsets:
        return ()
    out = []
    time = 0
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
    # cast to set first to remove duplicate references to a rhythms, if any:
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
        # TODO cast elsewhere
        return np.array(list(er.grid.keys()), dtype=np.float32)

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


# def _indices_shuffler(num_remaining, indices, start_i, end_i=None):
#     if num_remaining <= 0:
#         return num_remaining
#     RNG.shuffle(indices[start_i:end_i])
#     try:
#         return num_remaining - end_i + start_i
#     except TypeError:
#         # end_i is None
#         return 0


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


def get_iois(er, voice_i, onsets):
    # iois = inter-onset-intervals
    iois = np.empty(len(onsets), fractions.Fraction)
    iois[:-1] = onsets[1:] - onsets[:-1]
    iois[-1] = er.get(voice_i, "rhythm_len") - onsets[-1]
    if er.overlap:
        iois[-1] += onsets[0]
    return iois


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


# def new_fit_rhythm_to_pattern(er, voice_i, onsets, durs):
#     # TODO deprecate this function in favor of _pad_truncations
#     n_onsets = len(onsets)
#     if n_onsets == 0:
#         return onsets, durs
#     pattern_len = er.pattern_len[voice_i]
#     rhythm_len = er.rhythm_len[voice_i]
#     if rhythm_len >= pattern_len:
#         return onsets, durs
#     reps, remainder = divmod(pattern_len, rhythm_len)
#     remainder_i = np.searchsorted(onsets, remainder)
#     rep_onsets = np.tile(onsets, reps)
#     rep_durs = np.tile(durs, reps)
#     out_onsets = np.concatenate((rep_onsets, onsets[:remainder_i]))
#     out_durs = np.concatenate((rep_durs, durs[:remainder_i]))
#     for i in range(reps + 1):
#         out_onsets[n_onsets * i : n_onsets * (i + 1)] += i * float(rhythm_len)

#     overshoot = out_onsets[-1] + out_durs[-1] - pattern_len
#     if er.overlap:
#         overshoot -= out_onsets[0]
#     if overshoot > 0:
#         out_durs[-1] -= overshoot
#     return out_onsets, out_durs


def generate_rhythm(er, voice_i, prev_rhythms=()):
    if voice_i in er.rhythmic_unison_followers:
        leader_i = er.rhythmic_unison_followers[voice_i]
        return prev_rhythms[leader_i]

    if er.cont_rhythms == "all":
        return get_cont_rhythm(er, voice_i)

    onsets = get_onsets(er, voice_i, prev_rhythms)
    er.check_time()
    iois = get_iois(er, voice_i, onsets)
    er.check_time()
    durs = get_durs(er, voice_i, iois, onsets, prev_rhythms)
    er.check_time()
    if er.cont_rhythms == "grid":
        rhythm = er.grid.return_varied_rhythm(er, onsets, durs, voice_i)
    else:
        rhythm = Rhythm.from_er_settings(er, voice_i, onsets=onsets, durs=durs)
    return rhythm


def get_cont_rhythm(er, voice_i):
    rhythm = ContinuousRhythm(er, voice_i)
    if rhythm.num_notes == 0:
        print(f"Notice: voice {voice_i} is empty.")
        return rhythm
    rhythm.generate_continuous_onsets()
    rhythm.fill_continuous_durs()
    rhythm.vary_continuous_onsets()
    rhythm.truncate_or_extend()
    rhythm.round()
    rhythm.rel_onsets_to_rhythm()
    return rhythm


# Not sure what this was ever used for. RhythmicDict has a __str__ method.
# Perhaps this is deprecated?
# def print_rhythm(rhythm):
#     if isinstance(rhythm, list):
#         strings = []
#         strings.append("#" * 51)
#         for onset in rhythm:
#             strings.append("Attack:{:>10.3}" "".format(float(onset)))
#         strings.append("\n")
#         print("\n".join(strings)[:-2])
#     elif isinstance(rhythm, dict):
#         strings = []
#         strings.append("#" * 51)
#         for onset, dur in rhythm.items():
#             strings.append(
#                 "Attack:{:>10.3}  Duration:{:>10.3}"
#                 "".format(float(onset), float(dur))
#             )
#         strings.append("\n")
#         print("\n".join(strings)[:-2])


# def _get_onset_positions(er, voice_i):

#     if er.cont_rhythms == "grid":
#         return list(er.grid.keys())

#     rhythm_len, sub_subdiv_props = er.get(
#         voice_i, "rhythm_len", "sub_subdiv_props"
#     )
#     onset_positions = []
#     time_i = 0
#     time = fractions.Fraction(0, 1)
#     while time < rhythm_len:
#         onset_positions.append(time)
#         time += sub_subdiv_props[time_i % len(sub_subdiv_props)]
#         time_i += 1
#     return onset_positions


# def _get_available_for_hocketing(er, voice_i, prev_rhythms, onset_positions):
#     """Used for er.hocketing. Returns those subdivisions
#     that are available for to be selected. (I.e., those
#     that do not belong to the previously constructed
#     rhythms, and those that do not belong to obligatory
#     beats in other voices.)
#     """
#     out = []
#     for onset in onset_positions:
#         write = True
#         for prev_rhythm in prev_rhythms:
#             if onset in prev_rhythm:
#                 write = False
#                 break
#         if not write:
#             continue
#         for oblig_onsets_i, oblig_onsets in enumerate(er.obligatory_onsets):
#             if oblig_onsets_i != voice_i % len(er.obligatory_onsets):
#                 if onset in oblig_onsets:
#                     write = False
#                     break
#         if not write:
#             continue
#         out.append(onset)

#     return out


# def _get_available_for_quasi_unison(
#     er, voice_i, leader_rhythms, onset_positions
# ):
#     out = []
#     for onset in onset_positions:
#         go_on = False
#         for leader_rhythm in leader_rhythms:
#             if onset in leader_rhythm:
#                 out.append(onset)
#                 go_on = False
#                 break
#         if go_on:
#             continue
#         for oblig_onsets_i, oblig_onsets in enumerate(er.obligatory_onsets):
#             if oblig_onsets_i != voice_i % len(er.obligatory_onsets):
#                 if onset in oblig_onsets:
#                     out.append(onset)
#                     break

#     return out


# def _get_leader_available(er, remaining, leader_rhythm):
#     # LONGTERM make this work when the follower rhythm is a different length
#     #   (especially longer) than the leader rhythm?
#     out = []
#     for time in remaining:
#         leader_time = time

#         while leader_time >= 0 and leader_time not in leader_rhythm:
#             leader_time -= er.onset_subdivision_gcd
#         if leader_time < 0:
#             continue
#         if time <= leader_time + leader_rhythm[leader_time]:
#             out.append(time)

#     return out


# def _get_onset_list(
#     er, voice_i, onset_positions, available, leader_rhythm=None
# ):
#     def _add_onset(onset, remove_oblig=False):
#         nonlocal num_notes
#         out.append(onset)
#         num_notes -= 1
#         if onset in remaining:
#             remaining.remove(onset)
#         if onset in available:
#             available.remove(onset)
#         if remove_oblig and onset in oblig:
#             oblig.remove(onset)

#     num_notes, obligatory_onsets = er.get(
#         voice_i, "num_notes", "obligatory_onsets"
#     )
#     remaining = onset_positions.copy()
#     # I'm not sure whether it's necessary to make a copy of obligatory
#     #   onsets, but doing it to be safe, for now, at least.
#     oblig = obligatory_onsets.copy()

#     out = []
#     if voice_i == 0 and er.force_foot_in_bass in (
#         "first_beat",
#         "global_first_beat",
#     ):
#         _add_onset(fractions.Fraction(0, 1), remove_oblig=True)

#     for onset in oblig:
#         if onset in remaining:
#             _add_onset(onset)
#         else:
#             print(
#                 f"Note: obligatory onset {onset} in voice {voice_i} "
#                 "not available."
#             )

#     while num_notes and available:
#         choose = random.choice(available)
#         _add_onset(choose)

#     if num_notes and leader_rhythm:
#         available = _get_leader_available(er, remaining, leader_rhythm)
#         while num_notes and available:
#             choose = random.choice(available)
#             _add_onset(choose)

#     # Add onsets to obtain the specified number of notes.
#     for _ in range(num_notes):
#         try:
#             choose = random.choice(remaining)
#         except:
#             breakpoint()
#         _add_onset(choose)
#     out.sort()

#     return out


# def _get_onset_dict_and_durs_to_next_onset(er, voice_i, onset_list):
#     """Returns a dictionary of onsets (with minimum durations)
#     as well as a dictionary of the duration between onsets
#     """

#     min_dur, rhythm_len = er.get(voice_i, "min_dur", "rhythm_len")

#     onsets = {}
#     durs = {}

#     for onset_i, onset in enumerate(onset_list):
#         try:
#             dur = onset_list[onset_i + 1] - onset
#         except IndexError:
#             dur = rhythm_len - onset
#             if er.overlap:
#                 dur += onset_list[0]
#         durs[onset] = dur
#         onsets[onset] = min(dur, min_dur)

#     return onsets, durs


# def _fill_quasi_unison_durs(er, voice_i, onsets, leader_rhythm):
#     leader_durs_at_onsets = {}
#     rhythm_length = er.rhythm_len[voice_i]
#     time = rhythm_length
#     leader_onset = rhythm_length
#     current_dur = 0
#     while time > 0:
#         time -= er.onset_subdivision_gcd
#         if time in leader_rhythm:
#             leader_dur = leader_rhythm[time]
#             if time + leader_dur == leader_onset:
#                 current_dur += leader_dur
#             else:
#                 current_dur = leader_dur
#             if time in onsets:
#                 leader_durs_at_onsets[time] = current_dur
#             leader_onset = time

#     return leader_durs_at_onsets


# def _fill_onset_durs(
#     er, voice_i, onsets, durs, leader_i=None, leader_durs_at_onsets=()
# ):
#     """Adds to the onset durations until the specified
#     density is achieved. Doesn't return anything, just
#     alters the onset dictionary in place.
#     """

#     def _fill_onsets_sub(dur_dict, remaining_dict):
#         actual_total_dur = sum(onsets.values())
#         available = []
#         for time in onsets:
#             if time in dur_dict and onsets[time] != dur_dict[time]:
#                 available.append(time)

#         # We round dur_density to the nearest dur_subdivision
#         while (
#             target_total_dur - actual_total_dur > dur_subdivision / 2
#             and available
#         ):
#             choose = random.choice(available)
#             remaining_dur = remaining_dict[choose] - onsets[choose]
#             dur_to_add = min(dur_subdivision, remaining_dur)
#             onsets[choose] += dur_to_add
#             actual_total_dur += dur_to_add
#             if (
#                 onsets[choose] >= dur_dict[choose]
#                 or onsets[choose] >= remaining_dict[choose]
#             ):
#                 available.remove(choose)

#         return actual_total_dur

#     dur_subdivision = er.get(voice_i, "dur_subdivision")

#     target_total_dur = fractions.Fraction(
#         er.dur_density[voice_i] * er.rhythm_len[voice_i]
#     ).limit_denominator(max_denominator=8192)

#     if leader_durs_at_onsets:
#         actual_total_dur = _fill_onsets_sub(leader_durs_at_onsets, durs)
#         if (actual_total_dur >= target_total_dur) or (
#             er.rhythmic_quasi_unison_constrain
#             and er.onset_density[voice_i] < er.onset_density[leader_i]
#         ):
#             return

#     _fill_onsets_sub(durs, durs)


# def _add_comma(er, voice_i, onsets):

#     # This function shouldn't run with any sort of continuous rhythms.
#     if er.cont_rhythms != "none":
#         return

#     comma_position = er.comma_position[voice_i]
#     if comma_position == "end":
#         return

#     # LONGTERM verify that this is working with complex subdivisions
#     rhythm_length = er.rhythm_len[voice_i]
#     subdivision = er.onset_subdivision[voice_i]
#     comma = rhythm_length % subdivision

#     if isinstance(comma_position, int):
#         comma_i = comma_position
#         if comma_i > len(onsets):
#             warnings.warn(
#                 f"Comma position for voice {voice_i} greater "
#                 "than number of onsets in rhythm. Choosing a "
#                 "random comma position."
#             )
#             comma_i = random.randrange(len(onsets))
#     else:
#         if comma_position == "beginning":
#             comma_i = 0
#         elif comma_position == "middle":
#             comma_i = random.randrange(1, len(onsets))
#         else:
#             comma_i = random.randrange(len(onsets) + 1)

#     onset_list = list(onsets.keys())

#     for onset in onset_list[comma_i:]:
#         new_onset = onset + comma
#         dur = onsets[onset]
#         del onsets[onset]
#         onsets[new_onset] = dur


# def _fit_rhythm_to_pattern(er, voice_i, onsets):
#     """If the rhythm is shorter than the pattern, extend it as necessary."""

#     if not onsets:
#         return

#     rhythm_len, pattern_len, num_notes = er.get(
#         voice_i, "rhythm_len", "pattern_len", "num_notes"
#     )

#     if rhythm_len >= pattern_len:
#         return

#     onset_list = list(onsets.keys())

#     onset_i = num_notes
#     while True:
#         prev_onset = onset_list[onset_i % len(onset_list)]
#         new_onset = prev_onset + rhythm_len * (onset_i // num_notes)
#         if new_onset >= pattern_len:
#             break
#         onsets[new_onset] = onsets[prev_onset]
#         onset_i += 1

#     last_onset = max(onsets)
#     last_onset_dur = onsets[last_onset]
#     overshoot = last_onset + last_onset_dur - pattern_len
#     if er.overlap:
#         first_onset = min(onsets)
#         overshoot -= first_onset
#     if overshoot > 0:
#         onsets[last_onset] -= overshoot


# def generate_rhythm_old(er, voice_i, prev_rhythms=()):
#     """Constructs a rhythm randomly according to the arguments supplied.

#     Keyword args:
#         prev_rhythms (list of dictionaries): used in the construction of
#             hocketed rhythms.

#     Returns:
#         A dictionary of (Fraction:onset time, Fraction:duration) pairs.
#     """

#     # TODO revise this code... it gets *really* slow when the rhythms get long

#     if voice_i in er.rhythmic_unison_followers:
#         leader_i = er.rhythmic_unison_followers[voice_i]
#         return prev_rhythms[leader_i]

#     if er.cont_rhythms == "all":
#         return get_cont_rhythm(er, voice_i)

#     subdivision = er.onset_subdivision[voice_i]
#     # why am I doing this here? Shouldn't this be in preprocessing?
#     # I moved it to preprocessing
#     # if not er.min_dur[voice_i]:
#     #     er.min_dur[voice_i] = subdivision
#     # if not er.dur_subdivision[voice_i]:
#     #     er.dur_subdivision[voice_i] = subdivision

#     onset_positions = _get_onset_positions(er, voice_i)
#     er.check_time()

#     available = []
#     if voice_i in er.hocketing_followers:
#         leaders = []
#         for leader_i in er.hocketing_followers[voice_i]:
#             leaders.append(prev_rhythms[leader_i % len(prev_rhythms)])
#         available = _get_available_for_hocketing(
#             er, voice_i, leaders, onset_positions
#         )
#     elif voice_i in er.rhythmic_quasi_unison_followers:
#         leader_i = er.rhythmic_quasi_unison_followers[voice_i]
#         leader_rhythm = prev_rhythms[leader_i % len(prev_rhythms)]
#         available = _get_available_for_quasi_unison(
#             er,
#             voice_i,
#             [
#                 prev_rhythms[leader_i],
#             ],
#             onset_positions,
#         )

#         if (
#             er.onset_density[voice_i] > er.onset_density[leader_i]
#             and er.rhythmic_quasi_unison_constrain
#         ):
#             onset_list = _get_onset_list(
#                 er, voice_i, onset_positions, available, leader_rhythm
#             )
#         else:
#             onset_list = _get_onset_list(
#                 er, voice_i, onset_positions, available
#             )

#         onsets, durs = _get_onset_dict_and_durs_to_next_onset(
#             er, voice_i, onset_list
#         )

#         leader_durs_at_onsets = _fill_quasi_unison_durs(
#             er,
#             voice_i,
#             onsets,
#             prev_rhythms[leader_i],
#         )

#         _fill_onset_durs(
#             er,
#             voice_i,
#             onsets,
#             durs,
#             leader_i=leader_i,
#             leader_durs_at_onsets=leader_durs_at_onsets,
#         )
#         if er.cont_rhythms == "grid":
#             rhythm = er.grid.return_varied_rhythm(er, onsets, voice_i)
#             return rhythm
#         _add_comma(er, voice_i, onsets)

#         _fit_rhythm_to_pattern(er, voice_i, onsets)

#         rhythm = Rhythm(er, voice_i)
#         rhythm.data = onsets
#         return rhythm
#     # LONGTERM consolidate this code with above (a lot of duplication!)
#     er.check_time()
#     onset_list = _get_onset_list(er, voice_i, onset_positions, available)
#     er.check_time()
#     onsets, durs = _get_onset_dict_and_durs_to_next_onset(
#         er, voice_i, onset_list
#     )
#     er.check_time()
#     _fill_onset_durs(er, voice_i, onsets, durs)
#     er.check_time()
#     _add_comma(er, voice_i, onsets)
#     er.check_time()
#     if er.cont_rhythms == "grid":
#         rhythm = er.grid.return_varied_rhythm(er, onsets, voice_i)
#         return rhythm
#     er.check_time()
#     _fit_rhythm_to_pattern(er, voice_i, onsets)

#     rhythm = Rhythm(er, voice_i)
#     rhythm.data = onsets
#     return rhythm

# TODO clean up commented code
def update_pattern_vl_order(er, rhythms):
    # if er.cont_rhythms != "none":
    #     er.num_notes_by_pattern = [
    #         len(rhythms[voice_i].rel_onsets[0])
    #         # len(rhythms[voice_i].onsets[0])
    #         for voice_i in range(er.num_voices)
    #     ]
    #     # The next lines seem a little kludgy, it would be nice to
    #     # treat all rhythms in a more homogenous way. But for now, at least
    #     # it works.
    #     for voice_i in range(er.num_voices):
    #         pattern_len, rhythm_len = er.get(
    #             voice_i, "pattern_len", "rhythm_len"
    #         )
    #         if pattern_len % rhythm_len == 0:
    #             num_repeats_of_rhythm = pattern_len // rhythm_len
    #             er.num_notes_by_pattern[voice_i] *= num_repeats_of_rhythm

    # else:
    #     # The length of each rhythm is equal to the number of notes
    #     # per pattern because of the _fit_rhythm_to_pattern function
    #     # previously run.
    #     er.num_notes_by_pattern = [len(rhythm) for rhythm in rhythms]

    # if er.truncate_patterns:
    #     max_len = max(er.pattern_len)
    #     truncate_lens = [
    #         max_len % pattern_len for pattern_len in er.pattern_len
    #     ]
    #     er.num_notes_by_truncated_pattern = [0 for i in range(er.num_voices)]
    #     for voice_i, truncate_len in enumerate(truncate_lens):
    #         if truncate_len:
    #             for onset in rhythms[voice_i]:
    #                 if onset >= truncate_len:
    #                     break
    #                 er.num_notes_by_truncated_pattern[voice_i] += 1
    start_indices = [0 for _ in rhythms]
    for vl_item in er.pattern_vl_order:
        voice_i = vl_item.voice_i
        end_i = rhythms[voice_i].get_i_at_or_after(vl_item.end_time)
        first_onset, _ = rhythms[voice_i].at_or_after(vl_item.start_time)
        vl_item.set_indices(start_indices[voice_i], end_i, first_onset)
        start_indices[voice_i] = end_i

    # totals = [0 for rhythm in rhythms]
    # for i in range(len(er.pattern_vl_order)):
    #     vl_item = er.pattern_vl_order[i]
    #     start_rhythm_i = totals[vl_item.voice_i]
    #     if (
    #         er.truncate_patterns
    #         and (vl_item.end_time - vl_item.start_time)
    #         < er.pattern_len[vl_item.voice_i]
    #     ):
    #         # TODO I believe all references to 'truncated_pattern_num_notes'
    #         #   can now be replaced by 'len(rhythm)' (but make sure!)
    #         # totals[vl_item.voice_i] += rhythms[
    #         #     vl_item.voice_i
    #         # ].truncated_pattern_num_notes
    #         totals[vl_item.voice_i] += len(rhythms[vl_item.voice_i])
    #     else:
    #         # TODO I think "num_notes_by_pattern" may no longer be necessary
    #         totals[vl_item.voice_i] += er.num_notes_by_pattern[vl_item.voice_i]
    #     # end_rhythm_i is the first note *after* the rhythm ends
    #     end_rhythm_i = totals[vl_item.voice_i]
    #     vl_item.start_i = start_rhythm_i
    #     vl_item.end_i = end_rhythm_i
    #     vl_item.len = end_rhythm_i - start_rhythm_i


def rhythms_handler(er):
    """According to the parameters in er, return rhythms."""

    if er.rhythms_specified_in_midi:
        rhythms = er_midi.get_rhythms_from_midi(er)
    else:
        rhythms = []
        if er.cont_rhythms == "grid":
            er.grid = Grid(er)
        for voice_i in range(er.num_voices):
            rhythms.append(generate_rhythm(er, voice_i, prev_rhythms=rhythms))

    if not any(rhythms):

        class EmptyRhythmsError(Exception):
            pass

        raise EmptyRhythmsError(
            "No notes in any rhythms! This is a bug in the script."
        )

    update_pattern_vl_order(er, rhythms)

    return rhythms


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


# def rest_before_next_note(rhythm, onset, min_rest_len):
#     release = onset + rhythm[onset]
#     for next_onset in rhythm.onsets:
#         if next_onset >= release:
#             break

#     gap = next_onset - release
#     if gap >= min_rest_len:
#         return True

#     return False
