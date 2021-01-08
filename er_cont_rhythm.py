"""For producing continuously varied rhythms
"""
import math

import numpy as np

import er_notes

RANDOM_CARD = 200
COMMA = 10 ** -5


def apply_min_dur_to_rel_attacks(rel_attacks, rhythm):
    while True:
        remaining = 0
        indices = np.ones(rhythm.num_notes)
        for i, rel_attack in enumerate(rel_attacks):
            if rel_attack >= rhythm.min_dur:
                continue
            indices[i] = 0
            remaining += rel_attack - rhythm.min_dur
            rel_attacks[i] = rhythm.min_dur
        if not remaining:
            break
        adjust = np.where(
            indices == 1, np.random.randint(0, RANDOM_CARD, rhythm.num_notes), 0
        )
        if adjust.sum():
            adjust = adjust / adjust.sum() * remaining
        rel_attacks = rel_attacks + adjust
    return rel_attacks


def generate_continuous_attacks(rhythm):
    rand_array = np.random.randint(0, RANDOM_CARD, rhythm.num_notes)
    attacks = rand_array / rand_array.sum() * rhythm.rhythm_len
    rhythm.rel_attacks[0] = apply_min_dur_to_rel_attacks(attacks, rhythm)


def fill_continuous_durs(rhythm):
    target_total_dur = min(
        (rhythm.dur_density * rhythm.rhythm_len, rhythm.rhythm_len)
    )
    actual_total_dur = rhythm.durs[0].sum()
    available_durs = rhythm.rel_attacks[0] - rhythm.durs[0]
    if not available_durs.sum():
        return
    available_durs_prop = available_durs / available_durs.sum()
    missing_dur = target_total_dur - actual_total_dur

    while missing_dur > 0:
        weights = np.where(
            available_durs > 0,
            np.random.randint(0, RANDOM_CARD, rhythm.num_notes),
            0,
        )
        weights_2 = weights / weights.sum()
        weights_3 = weights_2 - weights_2[available_durs > 0].mean() + 1
        deltas = (weights_3) * (missing_dur * available_durs_prop)
        rhythm.durs[0] += deltas
        overlaps = np.where(
            rhythm.durs[0] - rhythm.rel_attacks[0] > 0,
            rhythm.durs[0] - rhythm.rel_attacks[0],
            0,
        )
        rhythm.durs[0] -= overlaps
        actual_total_dur = rhythm.durs[0].sum()
        available_durs = rhythm.rel_attacks[0] - rhythm.durs[0]
        if available_durs.sum():
            available_durs_prop = available_durs / available_durs.sum()
            missing_dur = target_total_dur - actual_total_dur
        else:
            # this delete statement is in place for safety, so if it the
            # loop runs again when there are no available durations, it
            # will throw an error
            missing_dur = 0
            del available_durs_prop


def vary_continuous_attacks(rhythm, apply_to_durs=True):

    # def _vary_continuous_attacks_randomly(rhythm, i, apply_to_durs=True):
    def _vary_continuous_attacks_randomly(rhythm, i):  # TODO apply_to_durs?
        deltas = np.random.randint(0, RANDOM_CARD, rhythm.num_notes)
        deltas = deltas / deltas.sum() * rhythm.increment
        deltas = deltas - deltas.mean()
        attacks = rhythm.rel_attacks[i] + deltas
        rhythm.rel_attacks[i + 1] = apply_min_dur_to_rel_attacks(
            attacks, rhythm
        )
        # TODO vary durations

    def _vary_continuous_attacks_consistently(rhythm, i, apply_to_durs=True):
        def _update_deltas():
            deltas = np.random.randint(1, RANDOM_CARD, rhythm.num_notes)
            deltas2 = deltas / deltas.sum()
            deltas3 = deltas2 - deltas2.mean()
            if abs(deltas3).sum() == 0:
                breakpoint()
                # TODO investigate and fix whatever it is that results in
                #   this condition. Returning 0 is a kludge.
                rhythm.deltas = np.zeros(rhythm.num_notes)
                return
            deltas4 = deltas3 / (abs(deltas3).sum() / rhythm.increment)
            indices = np.array([True for i in range(rhythm.num_notes)])

            while True:
                if np.all(
                    rhythm.rel_attacks[i] + deltas4 >= rhythm.min_dur - COMMA
                ):
                    rhythm.deltas = deltas4
                    return
                if np.all(
                    rhythm.rel_attacks[i] + deltas4 * -1
                    >= rhythm.min_dur - COMMA
                ):
                    rhythm.deltas = deltas4 * -1
                    return
                indices = np.array(
                    [
                        rhythm.rel_attacks[i][j] + deltas4[j]
                        >= rhythm.min_dur - COMMA
                        and indices[j]
                        for j in range(rhythm.num_notes)
                    ]
                )

                deltas = np.where(indices, deltas, 0)
                deltas2 = deltas / deltas.sum()
                deltas3 = np.where(
                    indices, deltas2 - deltas2[indices].mean(), 0
                )
                if abs(deltas3).sum() == 0:
                    # TODO investigate and fix whatever it is that results in
                    #   this condition. Returning 0 is a kludge.
                    rhythm.deltas = np.zeros(rhythm.num_notes)
                    return
                deltas4 = deltas3 / (abs(deltas3).sum() / rhythm.increment)

        if rhythm.deltas is None:
            _update_deltas()
        elif np.any(rhythm.rel_attacks[i] + rhythm.deltas < rhythm.min_dur):
            _update_deltas()

        rhythm.rel_attacks[i + 1] = rhythm.rel_attacks[i] + rhythm.deltas

        if apply_to_durs:
            rhythm.durs[i + 1] = rhythm.durs[i]
            remaining_durs = rhythm.rel_attacks[i + 1] - rhythm.durs[i + 1]
            while np.any(remaining_durs < 0):
                negative_durs = np.where(remaining_durs < 0, remaining_durs, 0)
                rhythm.durs[i + 1] += negative_durs
                available_durs = np.where(remaining_durs > 0, remaining_durs, 0)
                dur_to_add = np.abs(negative_durs).sum()
                deltas = np.where(
                    available_durs > 0,
                    np.random.randint(1, RANDOM_CARD, rhythm.num_notes),
                    0,
                )
                deltas2 = deltas / deltas.sum() * dur_to_add
                rhythm.durs[i + 1] += deltas2
                remaining_durs = rhythm.rel_attacks[i + 1] - rhythm.durs[i + 1]

    for i in range(rhythm.num_vars - 1):
        if rhythm.full:
            rhythm.rel_attacks[i + 1] = rhythm.rel_attacks[i]
        elif rhythm.vary_rhythm_consistently:
            _vary_continuous_attacks_consistently(
                rhythm, i, apply_to_durs=apply_to_durs
            )
        else:
            _vary_continuous_attacks_randomly(rhythm, i)


def truncate_or_extend(rhythm):
    if (
        rhythm.rhythm_len < rhythm.pattern_len
        and rhythm.pattern_len % rhythm.rhythm_len != 0
    ):
        min_j = (
            math.ceil(rhythm.pattern_len / rhythm.rhythm_len) * rhythm.num_notes
        )
        temp_rel_attacks = np.zeros((rhythm.num_vars, min_j))
        temp_durs = np.zeros((rhythm.num_vars, min_j))
        for var_i, var in enumerate(rhythm.rel_attacks):
            temp_rel_attacks[var_i, : rhythm.num_notes] = var
            temp_durs[var_i, : rhythm.num_notes] = rhythm.durs[var_i]
            time = rhythm.rhythm_len
            j = rhythm.num_notes
            while time < rhythm.pattern_len:
                attack_dur = var[j % rhythm.num_notes]
                dur = rhythm.durs[var_i][j % rhythm.num_notes]
                temp_rel_attacks[var_i, j] = min(
                    (attack_dur, rhythm.pattern_len - time)
                )
                temp_durs[var_i, j] = min((dur, rhythm.pattern_len - time))
                time += attack_dur
                j += 1
            if j < min_j:
                min_j = j
        # If each repetition of the rhythm doesn't have the same number of
        # notes, the algorithm won't work. For now we just address this
        # by truncating to the minumum length.
        rhythm.rel_attacks = temp_rel_attacks[:, :min_j]
        rhythm.durs = temp_durs[:, :min_j]
        # If we truncated one (or conceivably more) attacks from some
        # rhythms, we need to add the extra duration back on to the attacks.
        # Thus doesn't effect rhythm.durs, however.
        for var_i, var in enumerate(rhythm.rel_attacks):
            var[min_j - 1] += rhythm.pattern_len - var.sum()


def get_rhythm(er, voice_i):
    rhythm = er_notes.ContinuousRhythm(er, voice_i)
    if rhythm.num_notes == 0:
        print(f"Notice: voice {voice_i} is empty.")
        return rhythm
    generate_continuous_attacks(rhythm)
    fill_continuous_durs(rhythm)
    vary_continuous_attacks(rhythm)
    truncate_or_extend(rhythm)
    rhythm.round()
    rhythm.rel_attacks_to_rhythm()
    return rhythm


if __name__ == "__main__":
    pass
