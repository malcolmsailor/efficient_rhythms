import functools

import numpy as np

from . import er_exceptions


class ParallelMotionInfo:
    def __init__(self, leader_i, motion_type):
        self.leader_i = leader_i
        # LONGTERM implement "global" parallel motion
        # (that's why this translation to a string is here, so eventually
        # force_parallel_motion in ERSettings can be specified by a
        # string with minimum fuss)
        self.motion_type = "within_harmonies" if motion_type else "false"


class VLOrderItem:
    def __init__(self, voice_i, start_time, end_time, prev):
        self.voice_i = voice_i
        self.start_time = start_time
        self.end_time = end_time
        self._prev = prev
        # The following fields are expected to be initialized later by calling
        #   the `set_indices()` method
        self._start_i = None
        self._end_i = None
        self._len = None
        self._first_onset = None

    def __repr__(self):
        prev_str = (
            "None)"
            if self._prev is None
            else f"<starts at {self._prev.start_time}>"
        )
        return (
            f"{self.__class__.__name__}("
            f"voice_i={self.voice_i}, "
            f"start_time={self.start_time}, end_time={self.end_time}, "
            f"start_i={self.start_i}, "
            f"end_i={self.end_i}, "
            f"first_onset={self.first_onset}, "
            f"prev={prev_str})"
        )

    def set_indices(self, start_i, end_i, first_onset):
        self._start_i = start_i
        self._end_i = end_i
        self._len = end_i - start_i
        self._first_onset = first_onset

    def __len__(self):
        # We define this method so that "empty" vl-items (where start_i == end_i
        # evaluate to False).
        return self._len

    @property
    def prev(self):
        return self._prev

    @property
    def prev_start_time(self):
        return self._prev.start_time

    @property
    def prev_start_i(self):
        # Will raise an exception if prev is None
        return self._prev.start_i

    @property
    def prev_first_onset(self):
        return self._prev.first_onset

    @property
    def prev_end_i(self):
        """Note that the previous item may be *longer* than the current one
        (if the current one is truncated).
        This returns the index to the end of the portion of the previous item
        from which this will be voice-led, rather than the full length.
        """
        # Will raise an exception if prev is None (or set_indices hasn't been
        #   called)
        return self._prev.start_i + self._len

    @property
    def start_i(self):
        return self._start_i

    @property
    def end_i(self):
        return self._end_i

    @property
    def first_onset(self):
        return self._first_onset


def indices_to_vl(indices, chord1, chord2, tet):
    voice_leading = []
    for i, j in enumerate(indices):
        interval = chord2[j] - chord1[i]
        if abs(interval) <= tet // 2:
            voice_leading.append(interval)
        elif interval > 0:
            voice_leading.append(interval - tet)
        else:
            voice_leading.append(interval + tet)
    return tuple(voice_leading)


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
            halftet
            tet
            displacement_more_than

        I believe that this function should work just fine on pitch
        multisets (that is, chords with more than one of a given
        pitch-class, rather than Python multisets). But I haven't
        yet tried it.
        """
        # LONGTERM try multisets somehow?
        nonlocal best_sum, best_vl_indices
        if not in_indices:
            if current_sum > displacement_more_than:
                if best_sum > current_sum:
                    best_sum = current_sum
                    best_vl_indices = [out_indices]
                elif best_sum == current_sum:
                    best_vl_indices.append(out_indices)
        else:
            chord1_i = len(out_indices)
            for i, chord2_i in enumerate(in_indices):
                displacement = abs(chord2[chord2_i] - chord1[chord1_i])
                if chord1_i in exclude_motions:
                    if displacement in exclude_motions[chord1_i]:
                        #      MAYBE expand to include combinations of
                        #       multiple voice leading motions
                        continue
                if displacement > halftet:
                    displacement = tet - displacement
                present_sum = current_sum + displacement
                if present_sum > best_sum:
                    continue
                _voice_leading_sub(
                    in_indices[:i] + in_indices[i + 1 :],
                    out_indices + [chord2_i],
                    present_sum,
                )

    card = len(chord1)
    if card != len(chord2):
        raise ValueError(f"{chord1} and {chord2} have different lengths.")

    if exclude_motions is None:
        exclude_motions = {}

    best_sum = starting_sum = tet ** 8
    best_vl_indices = []
    halftet = tet // 2

    _voice_leading_sub(list(range(card)), [], 0)

    # If best_sum hasn't changed, then we haven't found any
    # voice-leadings.
    if best_sum == starting_sum:
        raise er_exceptions.NoMoreVoiceLeadingsError

    # My original code here created voice_leading_intervals as a set and then
    # cast to a list afterwards. The only reason I can see for doing this
    # would be if there could be duplicate items in the list otherwise, but
    # it doesn't seem to me that this is possible, and fairly extensive testing
    # didn't turn up any cases. So I removed the set but leaving this note
    # just in case any future problems turn up as a result.

    voice_leading_intervals = [
        indices_to_vl(indices, chord1, chord2, tet)
        for indices in best_vl_indices
    ]

    if len(voice_leading_intervals) > 1:
        voice_leading_intervals.sort(key=np.var)

    return voice_leading_intervals, best_sum


class VoiceLeader:
    """A class for getting voice-leadings between two harmonies.

    Each time the instance is called (i.e., with __call__), returns
    the next most efficient voice-leading. If there are no more
    possible voice-leadings, returns a NoMoreVoiceLeadingsError.

    Voice-leadings are sorted by total displacement. If there is more
    than one voice-leading of equivalent displacement, these are sorted
    by the following two condiitions (the second condition in fact
    enforces the first as well):
        1) the least maximum displacement of any individual voice
           (so [0, 0, 0, 2, 2, 2] ahead of [0, 0, 0, 0, 0, 6]).
        2) the voice-leading motion spread most evenly between the
           different voices (so [0, 0, 1, 2, 2, 1] ahead of
           [0, 0, 0, 2, 2, 2]. (This is measured by taking the standard
           deviation of the intervals.)

    Arguments:
        er: the settings object.
        src_harmony_i
        dest_harmony_i
    """

    def __init__(self, er, src_harmony_i, dest_harmony_i):
        self.er = er
        self.tet = er.tet
        self.src_harmony_i = src_harmony_i
        self.dest_harmony_i = dest_harmony_i
        self.src_pc_scale, self.src_pc_chord = er.get(
            src_harmony_i, "pc_scales", "pc_chords"
        )
        self.dest_pc_scale, self.dest_pc_chord = er.get(
            dest_harmony_i, "pc_scales", "pc_chords"
        )
        self.scale_foots = (
            er.get(src_harmony_i, "foot_pcs"),
            er.get(dest_harmony_i, "foot_pcs"),
        )
        self.parallel_voice_leading = er.parallel_voice_leading
        if self.parallel_voice_leading:
            self.parallel_str = er.parallel_direction
            # the commented-out attempted implementation of "alternate" below
            # does not work because
            # the VoiceLeader only applies to two chords, then a new instance
            # is created.
            if self.parallel_str == "alternate":
                raise NotImplementedError
            elif self.parallel_str == "up":
                self.parallel_dir = 1
            elif self.parallel_str == "down":
                self.parallel_dir = -1

        self.voice_lead_chord_tones = er.voice_lead_chord_tones
        self.voice_leading_i = -1
        # self._chords_last_updated is for updating chord-tone voice leadings.
        # It should be None on initialization and True/False afterwards
        self._chords_last_updated = None
        self.displacement = self.c_displacement = self.nc_displacement = -1
        self._init_excluded_motions()

        self._update_voice_leadings()

    def _init_excluded_motions(self):
        self.excluded_vl_motions = {
            i: [] for i in range(len(self.src_pc_scale))
        }
        if self.voice_lead_chord_tones:
            # The values of both of the following dicts are the same lists
            # as self.excluded_vl_motions. Thus we don't have to explicitly
            # maintain these dicts when updating the excluded vl motions.
            self.excluded_chord_motions = {
                chord_i: self.excluded_vl_motions[scale_i]
                for chord_i, scale_i in self.chord_indices.items()
            }
            self.excluded_nonchord_motions = {
                nonchord_i: self.excluded_vl_motions[scale_i]
                for nonchord_i, scale_i in self.nonchord_indices.items()
            }

    def _parallel_voice_leading(self):

        # both src and dest scales must have same length
        scale_len = len(self.src_pc_scale)

        if self.voice_lead_chord_tones:
            # if chord_tones, then the "foot" of each harmony is the foot of the
            # chord (which we can think of as a roman numeral), measured from
            # the foot of the scale
            src_foot, dest_foot = self.src_pc_chord[0], self.dest_pc_chord[0]
            # src_scale_foot_i = self.src_pc_scale.index(src_chord_foot)
            # dest_scale_foot_i = self.dest_pc_scale.index(dest_chord_foot)

        else:
            # else the "foot" of each harmony is the foot of the scale
            src_foot, dest_foot = self.scale_foots

        src_scale_foot_i = self.src_pc_scale.index(src_foot)
        dest_scale_foot_i = self.dest_pc_scale.index(dest_foot)

        foot_interval = (dest_scale_foot_i - src_scale_foot_i) % scale_len

        vl_intervals = []

        for i in range(scale_len):
            src_pc = self.src_pc_scale[i % scale_len]
            dest_pc = self.dest_pc_scale[(i + foot_interval) % scale_len]
            interval = (dest_pc - src_pc) % self.tet
            vl_intervals.append(interval)

        if all(i == 0 for i in vl_intervals):
            return [vl_intervals], 0

        if self.parallel_str == "closest":
            #      or (
            #     self.parallel_str == "alternate" and self.parallel_dir is None
            # ):
            avg_interval = sum(vl_intervals) / scale_len
            if avg_interval > 6:
                self.parallel_dir = -1
            else:
                self.parallel_dir = 1
        # elif self.parallel_str == "alternate":
        #     self.parallel_dir *= -1

        if self.parallel_dir < 0:
            vl_intervals = [interval - self.tet for interval in vl_intervals]

        displacement = sum([abs(interval) for interval in vl_intervals])

        return [vl_intervals], displacement

    @functools.cached_property
    def chord_indices(self):
        return self.er.chord_indices_at_harmony_i(self.src_harmony_i)

    @functools.cached_property
    def nonchord_indices(self):
        return self.er.nonchord_indices_at_harmony_i(self.src_harmony_i)

    @functools.cached_property
    def src_chord_pcs(self):
        return self.er.chord_pcs_at_harmony_i(self.src_harmony_i)

    @functools.cached_property
    def src_nonchord_pcs(self):
        return self.er.nonchord_pcs_at_harmony_i(self.src_harmony_i)

    @functools.cached_property
    def dest_chord_pcs(self):
        return self.er.chord_pcs_at_harmony_i(self.dest_harmony_i)

    @functools.cached_property
    def dest_nonchord_pcs(self):
        return self.er.nonchord_pcs_at_harmony_i(self.dest_harmony_i)

    def _update_chord_vls(self):
        self.chord_intervals, self.c_displacement = efficient_voice_leading(
            self.src_chord_pcs,
            self.dest_chord_pcs,
            tet=self.tet,
            exclude_motions=self.excluded_chord_motions,
            displacement_more_than=self.c_displacement,
        )
        self._chords_last_updated = True

    def _update_nonchord_vls(self):
        self.nonchord_intervals, self.nc_displacement = efficient_voice_leading(
            self.src_nonchord_pcs,
            self.dest_nonchord_pcs,
            tet=self.tet,
            exclude_motions=self.excluded_nonchord_motions,
            displacement_more_than=self.nc_displacement,
        )
        self._chords_last_updated = False

    def _update_voice_leadings(self):
        if self.parallel_voice_leading:
            self.intervals, self.displacement = self._parallel_voice_leading()

        elif self.voice_lead_chord_tones:
            if self._chords_last_updated is None:
                # We put _update_chord_vls() second so self._chords_last_updated
                # will be True and on the subsequent call the non-chord
                # voice-leading will be updated first:
                self._update_nonchord_vls()
                self._update_chord_vls()
            elif self._chords_last_updated:
                self._update_nonchord_vls()
            else:
                self._update_chord_vls()
            self.zip_voice_leadings()
        else:
            self.intervals, self.displacement = efficient_voice_leading(
                self.src_pc_scale,
                self.dest_pc_scale,
                tet=self.tet,
                displacement_more_than=self.displacement,
                exclude_motions=self.excluded_vl_motions,
            )

    def zip_voice_leadings(self):

        self.displacement = self.c_displacement + self.nc_displacement

        self.intervals = []

        # This won't try every combination of chord and non-chord voice-leadings.
        # That could lead to a combinatorial explosion...

        if len(self.chord_intervals) != len(self.nonchord_intervals):
            short_list = (
                self.chord_intervals
                if len(self.chord_intervals) < len(self.nonchord_intervals)
                else self.nonchord_intervals
            )
            long_list = (
                self.chord_intervals
                if len(self.chord_intervals) > len(self.nonchord_intervals)
                else self.nonchord_intervals
            )
            i = 0
            while len(short_list) < len(long_list):
                short_list.append(short_list[i])
                i += 1

        for chord_voice_leading, nonchord_voice_leading in zip(
            self.chord_intervals, self.nonchord_intervals
        ):
            chord_vl_i = nonchord_vl_i = 0
            zipped_voice_leading = []
            for pc in self.src_pc_scale:
                if pc in self.src_pc_chord:
                    zipped_voice_leading.append(chord_voice_leading[chord_vl_i])
                    chord_vl_i += 1
                else:
                    zipped_voice_leading.append(
                        nonchord_voice_leading[nonchord_vl_i]
                    )
                    nonchord_vl_i += 1
            self.intervals.append(zipped_voice_leading)

    def __call__(self, exclude_vl_tup=None):
        if exclude_vl_tup is not None:
            # exclude_vl_tup[0] is interval_i
            # exclude_vl_tup[1] is interval
            self.excluded_vl_motions[exclude_vl_tup[0]].append(
                exclude_vl_tup[1]
            )
        self.voice_leading_i += 1
        while True:
            break_out = True
            try:
                voice_leading = self.intervals[self.voice_leading_i]
            except IndexError:
                if self.parallel_voice_leading:
                    # there is only *one* parallel voice-leading, so if we are
                    # here, the voice-leading has failed
                    raise er_exceptions.NoMoreVoiceLeadingsError
                self._update_voice_leadings()
                self.voice_leading_i = 0
                voice_leading = self.intervals[self.voice_leading_i]
            for interval_i, interval in enumerate(voice_leading):
                if interval in self.excluded_vl_motions[interval_i]:
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
