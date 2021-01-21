import numpy as np

import src.er_exceptions as er_exceptions


class VoiceLeadingOrderItem:
    def __init__(
        self,
        voice_i,
        start_time,
        end_time,
        start_rhythm_i=None,
        end_rhythm_i=None,
        prev_item=None,
    ):
        self.voice_i = voice_i
        self.start_time = start_time
        self.end_time = end_time
        self.start_rhythm_i = start_rhythm_i
        self.end_rhythm_i = end_rhythm_i
        # prev_item should point to the item from which the present
        # item should be voice-led, or, if it is at the beginning,
        # to None
        self.prev_item = prev_item

    def __repr__(self):
        return (
            f"{self.__class__.__name__}(voice_i={self.voice_i}, "
            f"start_time={self.start_time}, end_time={self.end_time}, "
            f"start_rhythm_i={self.start_rhythm_i}, "
            f"end_rhythm_i={self.end_rhythm_i}, prev_item="
            + (
                "None)"
                if self.prev_item is None
                else f"<starts at {self.prev_item.start_time}>)"
            )
        )

    @property
    def prev_start_rhythm_i(self):
        # Will raise an exception if prev_item is None
        return self.prev_item.start_rhythm_i

    @property
    def prev_end_rhythm_i(self):
        # Will raise an exception if prev_item is None
        return (
            self.prev_item.start_rhythm_i
            + self.end_rhythm_i
            - self.start_rhythm_i
        )


def parallel_voice_leading(
    source_pc_scale,
    dest_pc_scale,
    scale_roots,
    source_pc_chord,
    dest_pc_chord,
    chord_tones,
    parallel_direction,
    tet=12,
):

    # if chord_tones, then the "root" of each harmony is the root of the chord
    # (which we can think of as a roman numeral), measured from the root of the
    # scale

    scale_len = len(source_pc_scale)

    if chord_tones:
        source_chord_root = source_pc_chord[0]
        source_scale_root_i = source_pc_scale.index(source_chord_root)
        dest_chord_root = dest_pc_chord[0]
        dest_scale_root_i = dest_pc_scale.index(dest_chord_root)

    # else the "root" of each harmony is the root of the scale
    else:
        source_scale_root = scale_roots[0]
        source_scale_root_i = source_pc_scale.index(source_scale_root)
        dest_scale_root = scale_roots[1]
        dest_scale_root_i = dest_pc_scale.index(dest_scale_root)

    adjust_i = (dest_scale_root_i - source_scale_root_i) % scale_len

    voice_leading_intervals = []

    for i in range(scale_len):
        source_pitch_class = source_pc_scale[i % scale_len]
        dest_pitch_class = dest_pc_scale[(i + adjust_i) % scale_len]
        interval = (dest_pitch_class - source_pitch_class) % tet
        voice_leading_intervals.append(interval)

    if parallel_direction == 0:
        avg_interval = sum(voice_leading_intervals) / scale_len
        if avg_interval > 6:
            parallel_direction = -1
        else:
            parallel_direction = 1

    if parallel_direction < 0:
        voice_leading_intervals = [
            interval - tet for interval in voice_leading_intervals
        ]

    displacement = sum([abs(interval) for interval in voice_leading_intervals])

    return [voice_leading_intervals,], displacement


def _get_chord_pcs_and_non_chord_pcs(pc_scale, pc_chord):
    chord_pcs = []
    non_chord_pcs = []
    for pc in pc_scale:
        if pc in pc_chord:
            chord_pcs.append(pc)
        else:
            non_chord_pcs.append(pc)

    return chord_pcs, non_chord_pcs


def _get_chord_and_non_chord_is(pc_scale, pc_chord):
    chord_is = []
    non_chord_is = []
    for i, pc in enumerate(pc_scale):
        if pc in pc_chord:
            chord_is.append(i)
        else:
            non_chord_is.append(i)
    return chord_is, non_chord_is


def efficient_voice_leading(
    chord1, chord2, tet=12, displacement_more_than=-1, exclude_motions=None
):
    def _voice_leading_sub(in_indices, out_indices, current_sum):
        """This is a recursive function for calculating most efficient
        voice leadings.

        The idea is that a bijective voice-leading between two
        ordered chords can be represented by a single set of indexes,
        where the first index *x* maps the first note of the first chord
        on to the *x*th note of the second chord, and so on.

        Should be initially called as follows:
            _voice_leading_sub(list(range(cardinality of chords)),
                               [],
                               0)

        The following variables are found in the enclosing scope:
            chord1
            chord2
            best_sum
            best_vl_indices
            tet
            displacement_more_than

        I believe that this function should work just fine on pitch
        multisets (that is, chords with more than one of a given
        pitch-class, rather than Python multisets). But I haven't
        yet tried it.
        """
        # LONGTERM try multisets somehow?
        nonlocal best_sum
        nonlocal best_vl_indices
        if not in_indices:
            if current_sum > displacement_more_than:
                if best_sum > current_sum:
                    best_sum = current_sum
                    best_vl_indices = [out_indices]
                elif best_sum == current_sum:
                    best_vl_indices.append(out_indices)
        else:
            chord1_index = len(out_indices)
            chord1_pc = chord1[chord1_index]
            for i, chord2_index in enumerate(in_indices):
                chord2_pc = chord2[chord2_index]
                displacement = abs(chord2_pc - chord1_pc)
                if displacement in exclude_motions[chord1_index]:
                    #      MAYBE expand to include combinations of
                    #       multiple voice leading motions
                    continue
                if displacement > tet // 2:
                    displacement = tet - displacement
                present_sum = current_sum + displacement
                if present_sum > best_sum:
                    continue
                _voice_leading_sub(
                    in_indices[:i] + in_indices[i + 1 :],
                    out_indices + [chord2_index,],
                    present_sum,
                )

    def _indices_to_voice_leading(indices):
        voice_leading = []
        for i, j in enumerate(indices):
            chord1_pc = chord1[i]
            chord2_pc = chord2[j]
            interval = chord2_pc - chord1_pc
            if abs(interval) <= tet // 2:
                voice_leading.append(interval)
            elif interval > 0:
                voice_leading.append(interval - tet)
            else:
                voice_leading.append(interval + tet)
        return tuple(voice_leading)

    card = len(chord1)
    if card != len(chord2):

        class CardinalityError(Exception):
            pass

        raise CardinalityError(
            f"Cardinality of {chord1} and {chord2} does not agree."
        )

    if exclude_motions is None:
        exclude_motions = {}
    for i in range(card):
        if i not in exclude_motions:
            exclude_motions[i] = []

    best_sum = starting_sum = tet ** 8
    best_vl_indices = []

    _voice_leading_sub(list(range(card)), [], 0)

    # If best_sum hasn't changed, then we haven't found any
    # voice-leadings.
    if best_sum == starting_sum:
        raise er_exceptions.NoMoreVoiceLeadingsError

    voice_leading_intervals = set()

    for indices in best_vl_indices:
        intervals = _indices_to_voice_leading(indices)
        voice_leading_intervals.add(intervals)

    voice_leading_intervals = list(voice_leading_intervals)

    if len(voice_leading_intervals) != 1:
        # voice_leading_intervals.sort(key=lambda x: np.std(x))
        # voice_leading_intervals.sort(key=lambda x: max(x))
        voice_leading_intervals.sort(key=np.std)
        voice_leading_intervals.sort(key=max)

    return voice_leading_intervals, best_sum


def _zip_voice_leadings(
    chord_intervals,
    chord_displacement,
    non_chord_intervals,
    non_chord_displacement,
    pc_scale,
    pc_chord,
):

    total_displacement = chord_displacement + non_chord_displacement

    zipped_intervals = []

    # This won't try every combination of chord and non-chord voice-leadings.
    # That might lead to a combinatorial explosion...

    if len(chord_intervals) != len(non_chord_intervals):
        short_list = (
            chord_intervals
            if len(chord_intervals) < len(non_chord_intervals)
            else non_chord_intervals
        )
        long_list = (
            chord_intervals
            if len(chord_intervals) > len(non_chord_intervals)
            else non_chord_intervals
        )
        i = 0
        while len(short_list) < len(long_list):
            short_list.append(short_list[i])
            i += 1

    for chord_voice_leading, non_chord_voice_leading in zip(
        chord_intervals, non_chord_intervals
    ):
        chord_vl_i = non_chord_vl_i = 0
        zipped_voice_leading = []
        for pc in pc_scale:
            if pc in pc_chord:
                zipped_voice_leading.append(chord_voice_leading[chord_vl_i])
                chord_vl_i += 1
            else:
                zipped_voice_leading.append(
                    non_chord_voice_leading[non_chord_vl_i]
                )
                non_chord_vl_i += 1
        zipped_intervals.append(zipped_voice_leading)

    return zipped_intervals, total_displacement


class VoiceLeader:
    """A class for getting voice-leadings between two harmonies.

    Each time the get_next_voice_leading() method is called, returns
    the next most efficient voice-leading. If there are no more
    possible voice-leadings, returns a NoMoreVoiceLeadingsError.

    Voice-leadings are sorted by total displacement. If there is more
    than one voice-leading of equivalent displacement, these are sorted
    by:
        1) the least maximum displacement of any individual voice
           (so [0, 0, 0, 2, 2, 2] ahead of [0, 0, 0, 0, 0, 6]).
        2) the voice-leading motion spread most evenly between the
           different voices (so [0, 0, 1, 2, 2, 1] ahead of
           [0, 0, 0, 2, 2, 2]. (This is measured by taking the standard
           deviation of the absolute intervals. In fact, I think that
           sorting by standard deviation sorts by both of these at once,
           although I'm not certain.)

    Arguments:
        er: the settings object.
        source_harmony_i
        dest_harmony_i
    """

    def __init__(self, er, source_harmony_i, dest_harmony_i):
        self.tet = er.tet
        self.source_harmony_i = source_harmony_i
        self.dest_harmony_i = dest_harmony_i
        self.source_pc_scale, self.source_pc_chord = er.get(
            source_harmony_i, "pc_scales", "pc_chords"
        )
        self.dest_pc_scale, self.dest_pc_chord = er.get(
            dest_harmony_i, "pc_scales", "pc_chords"
        )
        self.chord_is, self.non_chord_is = _get_chord_and_non_chord_is(
            self.source_pc_scale, self.source_pc_chord
        )
        self.scale_roots = (
            er.get(source_harmony_i, "foot_pcs"),
            er.get(dest_harmony_i, "foot_pcs"),
        )
        self.parallel_voice_leading = er.parallel_voice_leading
        self.parallel_direction = er.parallel_direction
        self.voice_lead_chord_tones = er.voice_lead_chord_tones
        self.voice_leading_i = -1
        # self.last_updated is for updating chord-tone voice leadings.
        # It can take three values: "chord," "non-chord," and, to initialize
        # "none"
        self.last_updated = "none"
        self.displacement = -1
        self.excluded_voice_leading_motions = {
            i: [] for i in range(len(self.source_pc_scale))
        }
        self.excluded_chord_motions = {
            i: [] for i in range(len(self.source_pc_chord))
        }
        self.excluded_non_chord_motions = {
            i: []
            for i in range(
                len(self.source_pc_scale) - len(self.source_pc_chord)
            )
        }
        self._update_voice_leadings()

    def _update_voice_leadings(self):
        if self.parallel_voice_leading:
            self.intervals, self.displacement = parallel_voice_leading(
                self.source_pc_scale,
                self.dest_pc_scale,
                self.scale_roots,
                self.source_pc_chord,
                self.dest_pc_chord,
                self.voice_lead_chord_tones,
                self.parallel_direction,
                tet=self.tet,
            )

        elif self.voice_lead_chord_tones:
            (
                self.dest_chord_pcs,
                self.dest_non_chord_pcs,
            ) = _get_chord_pcs_and_non_chord_pcs(
                self.dest_pc_scale, self.dest_pc_chord
            )
            (
                self.source_chord_pcs,
                self.source_non_chord_pcs,
            ) = _get_chord_pcs_and_non_chord_pcs(
                self.source_pc_scale, self.source_pc_chord
            )

            if self.last_updated == "non-chord":
                (
                    self.chord_intervals,
                    self.chord_displacement,
                ) = efficient_voice_leading(
                    self.source_chord_pcs,
                    self.dest_chord_pcs,
                    tet=self.tet,
                    displacement_more_than=self.chord_displacement,
                    exclude_motions=self.excluded_chord_motions,
                )
                # LONGTERM should I uncomment this block and the similar one
                #      below? If so, it will find the most efficient voice-
                #      leading, rather than re-using the previously
                #      found one.
                # self.non_chord_intervals = efficient_voice_leading(
                #     self.source_non_chord_pcs, self.dest_non_chord_pcs,
                #     tet=self.tet)[INTERVALS]
                self.last_updated = "chord"
            elif self.last_updated == "chord":
                # self.chord_intervals = efficient_voice_leading(
                #     self.source_chord_pcs, self.dest_chord_pcs,
                #     tet=self.tet)[INTERVALS]
                (
                    self.non_chord_intervals,
                    self.non_chord_displacement,
                ) = efficient_voice_leading(
                    self.source_non_chord_pcs,
                    self.dest_non_chord_pcs,
                    tet=self.tet,
                    displacement_more_than=self.non_chord_displacement,
                    exclude_motions=self.excluded_non_chord_motions,
                )
                self.last_updated = "non-chord"
            elif self.last_updated == "none":
                (
                    self.chord_intervals,
                    self.chord_displacement,
                ) = efficient_voice_leading(
                    self.source_chord_pcs,
                    self.dest_chord_pcs,
                    tet=self.tet,
                    exclude_motions=self.excluded_chord_motions,
                )
                (
                    self.non_chord_intervals,
                    self.non_chord_displacement,
                ) = efficient_voice_leading(
                    self.source_non_chord_pcs,
                    self.dest_non_chord_pcs,
                    tet=self.tet,
                    exclude_motions=self.excluded_non_chord_motions,
                )
                # Set self.last_updated to "chord" so it will change
                # the non-chord voice leading first:
                self.last_updated = "chord"

            self.intervals, self.displacement = _zip_voice_leadings(
                self.chord_intervals,
                self.chord_displacement,
                self.non_chord_intervals,
                self.non_chord_displacement,
                self.source_pc_scale,
                self.source_pc_chord,
            )
        else:
            self.intervals, self.displacement = efficient_voice_leading(
                self.source_pc_scale,
                self.dest_pc_scale,
                tet=self.tet,
                displacement_more_than=self.displacement,
                exclude_motions=self.excluded_voice_leading_motions,
            )

    def exclude_voice_leading_motion(self, interval_i, interval):
        self.excluded_voice_leading_motions[interval_i].append(interval)
        self.excluded_chord_motions = {}
        for i, chord_i in enumerate(self.chord_is):
            self.excluded_chord_motions[
                i
            ] = self.excluded_voice_leading_motions[chord_i]
        self.excluded_non_chord_motions = {}
        for i, non_chord_i in enumerate(self.non_chord_is):
            self.excluded_non_chord_motions[
                i
            ] = self.excluded_voice_leading_motions[non_chord_i]

    def get_next_voice_leading(self):
        self.voice_leading_i += 1
        while True:
            break_out = True
            try:
                voice_leading = self.intervals[self.voice_leading_i]
            except IndexError:
                if self.voice_lead_chord_tones:
                    self._update_voice_leadings()
                else:
                    self._update_voice_leadings()
                self.voice_leading_i = 0
                voice_leading = self.intervals[self.voice_leading_i]
            for interval_i, interval in enumerate(voice_leading):
                if interval in self.excluded_voice_leading_motions[interval_i]:
                    self.voice_leading_i += 1
                    break_out = False
                    break
            if break_out:
                break

        return voice_leading


# Constants for accessing voice-leadings
INTERVALS = 0

if __name__ == "__main__":
    while True:
        c1 = eval(input("c1: "))
        c2 = eval(input("c2: "))
        print(
            efficient_voice_leading(
                c1, c2, tet=12, displacement_more_than=-1, exclude_motions=None
            )
        )
