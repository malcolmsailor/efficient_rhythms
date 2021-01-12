"""Provides a Score class that stores Voice classes which store Note classes,
together with associated methods.
"""
import collections
import copy

import er_misc_funcs
import er_tuning

# constants for writing notes
DEFAULT_VELOCITY = 96
DEFAULT_CHOIR = 0


class Note:
    """Stores a note.

    Attributes:
        pitch: an integer.
        attack_time: a fraction.
        dur: a fraction.
        velocity: an integer 0-127.
        choir: an integer.
        voice: an integer, or None. A place to store the voice that
            a note belongs to.
    """

    def __init__(
        self,
        pitch,
        attack_time,
        dur,
        velocity=DEFAULT_VELOCITY,
        choir=DEFAULT_CHOIR,
        voice=None,
        finetune=0,
    ):
        self.pitch = pitch
        self.attack_time = attack_time
        self.dur = dur
        self.velocity = velocity
        self.choir = choir
        self.voice = voice
        # self.finetune (in cents) can be used for arbitrary tuning
        self.finetune = finetune

    def __repr__(self):
        out = (
            "<Note pitch={} attack={:f} dur={:f} vel={} choir={} "
            "voice={}>\n".format(
                self.pitch,
                float(self.attack_time),
                float(self.dur),
                self.velocity,
                self.choir,
                self.voice,
            )
        )
        return out


# class RhythmicDict(collections.UserDict):
#     def __str__(self):
#         strings = []
#         strings.append("#" * 51)
#         for attack_time, dur in self.items():
#             strings.append(
#                 "Attack:{:>10.6}  Duration:{:>10.6}"
#                 "".format(float(attack_time), float(dur))
#             )
#         strings.append("\n")
#         return "\n".join(strings)[:-2]
#
#     # def make_attack_and_dur_lists(self):
#     #     self.attack_times = list(self.keys())
#     #     self.attack_times_and_durs = list(self.items())
#
#     # LONGTERM attack_times and attack_times_and_durs assume that
#     #   the contents will no longer be changed after their first access.
#     #   Is there a way to enforce this?
#     @functools.cached_property
#     def attack_times(self):
#         return list(self.keys())
#
#     @functools.cached_property
#     def attack_times_and_durs(self):
#         return list(self.items())
#
#
# class Rhythm(RhythmicDict):
#     @functools.cached_property
#     def total_num_notes(self):
#         # LONGTERM check whether this works with truncate
#         out = self.num_notes
#         running_length = self.rhythm_len
#         while running_length < self.total_rhythm_len:
#             break_out = False
#             if running_length + self.rhythm_len <= self.total_rhythm_len:
#                 running_length += self.rhythm_len
#                 out += self.num_notes
#             else:
#                 for attack_time in self:
#                     if running_length + attack_time >= self.total_rhythm_len:
#                         break_out = True
#                         break
#                     out += 1
#             if break_out:
#                 break
#         return out
#
#     def __init__(self, er, voice_i):
#         super().__init__()
#         self.voice_i = voice_i
#         (
#             self.num_notes,
#             self.rhythm_len,
#             self.pattern_len,
#             self.min_dur,
#             self.dur_density,
#         ) = er.get(
#             voice_i,
#             "num_notes",
#             "rhythm_len",
#             "pattern_len",
#             "min_dur",
#             "dur_density",
#         )
#         self.total_rhythm_len = self.pattern_len
#         if er.truncate_patterns:
#             # max_len = max(er.pattern_len)
#             # self.truncate_len = max_len % self.pattern_len
#             self.truncate_len = max(er.pattern_len)
#             self.n_per_truncate = math.ceil(
#                 self.truncate_len / self.pattern_len
#             )
#         else:
#             self.truncate_len = 0
#         # self.total_num_notes is overwritten in ContinuousRhythm and used
#         # in get_attack_time_and_dur
#         # self.total_num_notes = self.num_notes
#
#         # self._get_offsets(er.max_super_pattern_len)
#         self._check_min_dur()
#
#     def _check_min_dur(self):
#         if self.rhythm_len < self.min_dur * self.num_notes:
#             new_min_dur = er_misc_funcs.convert_to_fractions(
#                 self.rhythm_len / self.num_notes
#             )
#             print(
#                 f"Notice: min_dur too long in voice {self.voice_i} rhythm; "
#                 f"reducing from {self.min_dur} to {new_min_dur}."
#             )
#             self.min_dur = new_min_dur
#         if self.rhythm_len <= self.min_dur * self.num_notes:
#             print(
#                 "Notice: 'cont_rhythms' will have no effect in voice "
#                 f"{self.voice_i} because "
#                 "'min_dur' is the maximum value compatible with "
#                 "'rhythm_len', 'attack_subdivision', and 'sub_subdivisions'. "
#                 "To allow 'cont_rhythms' to have an effect, reduce 'min_dur' "
#                 f"to less than {self.min_dur}"
#             )
#             self.full = True
#         else:
#             self.full = False
#
#     def get_attack_time_and_dur(self, rhythm_i):
#         offset = (rhythm_i // self.total_num_notes) * self.total_rhythm_len
#         attack_time, dur = self.attack_times_and_durs[
#             rhythm_i % self.total_num_notes
#         ]
#         return attack_time + offset, dur
#
#
# class ContinuousRhythmicObject(RhythmicDict):
#     """Used as a base for ContinuousRhythm and Grid objects."""
#
#     # def round(self, precision=4):
#     def round(self):
#         try:
#             self.pattern_len
#         except AttributeError:
#             # Grid object does not have pattern_len attribute.
#             adj_len = self.rhythm_len  # pylint: disable=no-member
#         else:
#             if (
#                 self.rhythm_len < self.pattern_len
#                 and self.pattern_len % self.rhythm_len != 0
#             ):
#                 adj_len = self.pattern_len
#             else:
#                 adj_len = self.rhythm_len
#         for var in self.rel_attacks:  # pylint: disable=no-member
#             for j, dur in enumerate(var):
#                 var[j] = round(dur, 4)
#             var[j] += adj_len - var.sum()
#         try:
#             self.durs  # pylint: disable=no-member
#         except AttributeError:
#             # Grid object does not have .durs attribute.
#             return
#         for var in self.durs:  # pylint: disable=no-member
#             for j, dur in enumerate(var):
#                 var[j] = round(dur, 4)
#
#     # def round_to_frac(self, max_denominator=10000):
#     #     # This function doesn't work because fractions are not a valid
#     #     # datatype for np arrays.
#     #     try:
#     #         self.pattern_len
#     #     except AttributeError:
#     #         # Grid object does not have .pattern_len attribute.
#     #         adj_len = self.rhythm_len
#     #     else:
#     #         if (self.rhythm_len < self.pattern_len and
#     #                 self.pattern_len % self.rhythm_len != 0):
#     #             adj_len = self.pattern_len
#     #         else:
#     #             adj_len = self.rhythm_len
#     #     for var_i, var in enumerate(self.rel_attacks):
#     #         for j, dur in enumerate(var):
#     #             var[j] = fractions.Fraction(dur).limit_denominator(
#     #                 max_denominator=max_denominator)
#     #         var[j] += adj_len - var.sum()
#     #     try:
#     #         self.durs
#     #     except AttributeError:
#     #         # Grid object does not have .durs attribute.
#     #         return
#     #     for var_i, var in enumerate(self.durs):
#     #         for j, dur in enumerate(var):
#     #             var[j] = fractions.Fraction(dur).limit_denominator(
#     #                 max_denominator=max_denominator)
#
#     def rel_attacks_to_rhythm(
#         self, offset=0, first_var_only=False, comma=fractions.Fraction(1, 5000)
#     ):
#
#         if first_var_only:
#             # For use with Grid
#             rel_attacks = self.rel_attacks[0]  # pylint: disable=no-member
#         else:
#             rel_attacks = self.rel_attacks.reshape(  # pylint: disable=no-member
#                 -1
#             )
#
#         try:
#             durs = self.durs.reshape(-1)
#         except AttributeError:
#             # Grid does not have durs attribute.
#             durs = rel_attacks
#
#         for i, rel_attack in enumerate(rel_attacks):
#             frac_rel_attack = fractions.Fraction(rel_attack).limit_denominator(
#                 max_denominator=100000
#             )
#             frac_dur = fractions.Fraction(durs[i]).limit_denominator(
#                 max_denominator=100000
#             )
#             if frac_rel_attack == 0:
#                 continue
#             self[offset] = frac_dur
#             offset += frac_rel_attack
#             # if rel_attack == 0:
#             #     continue
#             # self[offset] = durs[i]
#             # offset += rel_attack
#
#         for attack_i, attack_time in enumerate(self.attack_times[:-1]):
#             overlap = (
#                 attack_time
#                 + self[attack_time]
#                 - self.attack_times[attack_i + 1]
#             )
#             if overlap > comma:
#                 warnings.warn("Unexpectedly long overlap in rhythm")
#             if overlap > 0:
#                 self[attack_time] = (
#                     self.attack_times[attack_i + 1] - attack_time
#                 )
#
#
# class ContinuousRhythm(Rhythm, ContinuousRhythmicObject):
#     def __init__(self, er, voice_i):
#         super().__init__(er, voice_i)
#
#         (
#             self.cont_var_increment,
#             self.num_cont_rhythm_vars,
#             self.vary_rhythm_consistently,
#         ) = er.get(
#             voice_i,
#             "cont_var_increment",
#             "num_cont_rhythm_vars",
#             "vary_rhythm_consistently",
#         )
#         self.increment = self.rhythm_len * self.cont_var_increment
#         self.rel_attacks = np.zeros((self.num_cont_rhythm_vars, self.num_notes))
#         self.durs = np.full_like(self.rel_attacks, self.min_dur)
#         self.deltas = None
#         if (
#             self.rhythm_len < self.pattern_len
#             and self.pattern_len % self.rhythm_len != 0
#         ):
#             self.total_rhythm_len = self.pattern_len * self.num_cont_rhythm_vars
#         else:
#             self.total_rhythm_len = self.rhythm_len * self.num_cont_rhythm_vars
#         self.total_num_notes = self.num_notes * self.num_cont_rhythm_vars


class Voice(collections.UserDict):
    """A dictionary of lists of Note objects, together with methods for
    working with them.

    Can be iterated over (e.g., for note in voice [where "voice" is a
    Voice object]) and reversed (e.g., reversed(voice)). This will
    give the note objects sorted by attack time and secondarily by
    durations.

    Attributes:
        data: a dictionary. Keys are attack_times (fractions), values are
            lists of Note objects, sorted by duration.
        other_messages: a list in which other midi messages are stored
            when constructing the voice from a midi file.
        max_attack_time: fraction. Used to monitor whether to re-sort
            the dictionary (i.e., if a new attack time smaller than
            max_attack_time is added).
        voice_i: int. The index number of the voice, if stored in a
            Score object.
        tet: int.
        range: Nonetype, or tuple of two ints. Used in certain
            transformers.
    """

    def __init__(self, voice_i=None, tet=12, voice_range=None):
        super().__init__()
        self.other_messages = []
        # self.max_attack_time is used to check whether to sort the
        #   dictionary after adding a new note
        self.max_attack_time = 0
        self.voice_i = voice_i
        self.tet = tet
        self.speller = er_tuning.Speller(tet)
        self.range = voice_range
        self.sort_up_to_date = 0
        self.reversed_up_to_date = -1
        self.reversed_voice = None

    def __iter__(self):
        for attack_time in self.data:
            notes = sorted(self.data[attack_time], key=lambda x: x.pitch)
            notes = sorted(notes, key=lambda x: x.dur)
            for note_object in notes:
                yield note_object

    def __reversed__(self):
        if self.reversed_up_to_date != self.sort_up_to_date:
            self.reversed_voice = dict(
                sorted(self.data.items(), key=lambda x: x[0], reverse=True)
            )
            for attack_time in self.reversed_voice:
                self.reversed_voice[attack_time].sort(
                    key=lambda x: x.dur, reverse=True
                )
            self.reversed_up_to_date = self.sort_up_to_date
        for attack_time in self.reversed_voice:
            # notes = sorted(
            #     self.data[attack_time], key=lambda x: x.dur, reverse=True)
            for note_object in self.reversed_voice[attack_time]:
                yield note_object

    def __str__(self):
        strings = []
        strings.append("#" * 51)
        for note in self:
            strings.append(
                "Attack:{:>10.3}  Pitch:{:>5}  Duration:{:>10.3}"
                "".format(
                    float(note.attack_time),
                    self.speller.spell(note.pitch),
                    float(note.dur),
                )
            )
        strings.append("\n")
        return "\n".join(strings)[:-2]

    def is_polyphonic(self):
        for attack_time in self.data:
            if len(self.data[attack_time]) > 1:
                return True
        return False

    def slice_keys(self, slice_):
        if isinstance(slice_, int):
            start = slice_
            stop = None
            step = None
        else:
            start = slice_.start
            stop = slice_.stop
            step = slice_.step
        return list(self.data.keys())[start:stop:step]

    def update_sort(self):
        self.data = dict(sorted(self.data.items(), key=lambda x: x[0]))
        for attack_time in self.data:
            self.data[attack_time].sort(key=lambda x: x.dur)

    def update_attack_time(self, attack_time):
        if attack_time <= self.max_attack_time:
            # This condition means that update secondary sort will not
            # necessarily take place, but since nothing depends on the
            # secondary sort the speed gain is probably worth it.
            #
            # changed my mind and commented the condition out:
            # if attack_time not in self.data:
            self.update_sort()
        else:
            self.max_attack_time = attack_time

    def add_note(
        self,
        pitch,
        attack_time,
        dur,
        velocity=DEFAULT_VELOCITY,
        choir=DEFAULT_CHOIR,
        update_sort=True,
    ):
        """Adds a note."""
        try:
            self[attack_time].append(
                Note(
                    pitch,
                    attack_time,
                    dur,
                    velocity=velocity,
                    choir=choir,
                    voice=self.voice_i,
                )
            )
        except KeyError:
            self[attack_time] = [
                Note(
                    pitch,
                    attack_time,
                    dur,
                    velocity=velocity,
                    choir=choir,
                    voice=self.voice_i,
                ),
            ]
        if update_sort:
            self.update_attack_time(attack_time)
        self.sort_up_to_date += update_sort

    def add_note_object(self, note_object, update_sort=True):
        """Adds a note object."""
        note_object.voice = self.voice_i
        # if note_object.attack_time not in self:
        #     self[note_object.attack_time] = []
        try:
            self[note_object.attack_time].append(note_object)
        except KeyError:
            self[note_object.attack_time] = [
                note_object,
            ]
        if update_sort:
            self.update_attack_time(note_object.attack_time)
        self.sort_up_to_date += update_sort

    def move_note(self, note_object, new_attack_time, update_sort=True):
        """Moves a note object to a new attack time."""
        self.remove_note_object(note_object)
        note_object.attack_time = new_attack_time
        self.add_note_object(note_object, update_sort=update_sort)

    def remove_note(self, pitch, attack_time, dur=None):
        """Removes a note from the voice.

        Like list.remove, removes the first note that it finds
        that matches the specified criteria -- so if there is
        more than one identical note, the others will remain.
        If dur is not specified, then matches any dur.
        """

        class RemoveNoteError(Exception):
            pass

        try:
            notes = self.data[attack_time]
        except KeyError as exc:
            raise RemoveNoteError(
                f"No notes at attack time {attack_time}"
            ) from exc
        remove_i = -1
        for note_i, note in enumerate(notes):
            if note.pitch == pitch:
                if dur and note.dur != dur:
                    continue
                remove_i = note_i
                break
        if remove_i < 0:
            if dur:
                raise RemoveNoteError(
                    f"No note of pitch {pitch} and dur {dur} at attack "
                    f"time {attack_time}"
                )
            raise RemoveNoteError(
                f"No note of pitch {pitch} at attack " f"time {attack_time}"
            )
        notes.pop(remove_i)
        if not notes:
            del self.data[attack_time]

    def remove_note_object(self, note_object):
        class RemoveNoteObjectError(Exception):
            pass

        attack_time = note_object.attack_time
        try:
            notes = self.data[attack_time]
        except KeyError as exc:
            raise RemoveNoteObjectError(
                f"No attacks at {attack_time} in voice {self.voice_i}."
            ) from exc
        notes.remove(note_object)
        if not notes:
            del self.data[attack_time]

    def add_rest(self, attack_time, dur, update_sort=True):
        """Adds a 'rest'."""
        try:
            self[attack_time].append(
                Note(
                    None,
                    attack_time,
                    dur,
                    velocity=None,
                    choir=None,
                    voice=self.voice_i,
                )
            )
        except KeyError:
            self[attack_time] = [
                Note(
                    None,
                    attack_time,
                    dur,
                    velocity=None,
                    choir=None,
                    voice=self.voice_i,
                ),
            ]
        if update_sort:
            self.update_attack_time(attack_time)
        self.sort_up_to_date += update_sort

    def add_other_message(self, message):
        self.other_messages.append(message)

    def append(self, other_voice, offset=0):
        """Appends the notes of another Voice object."""
        for note_object in other_voice:
            note_copy = copy.copy(note_object)
            note_copy.attack_time += offset
            self.add_note_object(note_copy, update_sort=False)
        self.update_sort()
        self.sort_up_to_date += 1

    def get_sounding_pitches(
        self, attack_time, dur=0, min_attack_time=0, min_dur=0
    ):

        sounding_pitches = set()
        end_time = attack_time + dur
        times = list(self.data.keys())
        i = er_misc_funcs.binary_search(
            times, end_time, not_found="force_upper"
        )
        while i is not None:
            try:
                time = times[i]
            except IndexError:
                i -= 1
                continue
            i -= 1
            notes = self.data[time]
            break_out = False
            for note in reversed(notes):
                if dur > 0 and note.attack_time >= end_time:
                    continue
                if note.attack_time > end_time:
                    continue
                if note.attack_time < min_attack_time:
                    break_out = True
                    break
                if note.attack_time + note.dur <= attack_time:
                    continue
                if note.dur >= min_dur:
                    sounding_pitches.add(note.pitch)
            if i < 0 or break_out:
                break

        return list(sorted(sounding_pitches))

    def get_all_pitches_attacked_during_duration(self, attack_time, dur):
        return self.get_sounding_pitches(
            attack_time, dur=dur, min_attack_time=attack_time
        )

    def get_prev_n_pitches(
        self,
        n,
        time,
        min_attack_time=0,
        stop_at_rest=False,
        include_start_time=False,
    ):
        """Returns previous n pitches (attacked before time).

        If pitches are attacked earlier than min_attack_time, -1 will be
        returned instead. Or, if stop_at_rest is True, then instead of any
        pitches earlier than the first rest, -1 will be returned in place.
        """
        return [
            note.pitch if note is not None else -1
            for note in self.get_prev_n_notes(
                n,
                time,
                min_attack_time=min_attack_time,
                stop_at_rest=stop_at_rest,
                include_start_time=include_start_time,
            )
        ]

        # attack_times = list(self.data.keys())
        # i = er_misc_funcs.binary_search(attack_times, time)
        # pitches = []
        # if n <= 0:
        #     return pitches
        # if i is not None and include_start_time:
        #     i += 1
        # while i is not None:
        #     i -= 1
        #     if i < 0:
        #         break
        #     attack_time = attack_times[i]
        #     if attack_time == time and not include_start_time:
        #         continue
        #
        #     notes = self.data[attack_time]
        #     break_out = False
        #     last_attack_time = -1  # We want last_attack_time to be smaller
        #     # than note.attack_time + note.dur at least
        #     # once.
        #     # Later: do we actually? Don't we want it to break if there is a
        #     # rest immediately preceding the initial attack time?
        #     for note in reversed(notes):
        #         if note.attack_time < min_attack_time:
        #             break_out = True
        #             break
        #         if (
        #             stop_at_rest
        #             and note.attack_time + note.dur < last_attack_time
        #         ):
        #             break_out = True
        #             break
        #         pitches.insert(0, note.pitch)
        #         last_attack_time = note.attack_time
        #         if len(pitches) == n:
        #             break_out = True
        #             break
        #     if break_out:
        #         break
        #
        # for i in range(n - len(pitches)):
        #     pitches.insert(0, -1)
        # return pitches

    def get_prev_pitch(self, time, min_attack_time=0, stop_at_rest=False):
        """Returns previous pitch from voice."""
        return self.get_prev_n_pitches(
            1, time, min_attack_time=min_attack_time, stop_at_rest=stop_at_rest
        )[0]

    def get_last_n_pitches(
        self, n, time, min_attack_time=0, stop_at_rest=False
    ):
        """Returns last n pitches (including pitch attacked at time).
        """
        return self.get_prev_n_pitches(
            n,
            time,
            min_attack_time=min_attack_time,
            stop_at_rest=stop_at_rest,
            include_start_time=True,
        )

    def get_prev_n_notes(
        self,
        n,
        time,
        min_attack_time=0,
        stop_at_rest=False,
        include_start_time=False,
    ):
        attack_times = list(self.data.keys())
        start_i = er_misc_funcs.binary_search(
            attack_times, time, not_found="force_lower"
        )
        if start_i is None:
            return [None for _ in range(n)]

        out_notes = []
        last_attack_time = time
        i_iter = iter(range(start_i, -1, -1))
        try:
            while n:
                i = next(i_iter)
                attack_time = attack_times[i]
                if attack_time == time and not include_start_time:
                    continue
                if attack_time < min_attack_time:
                    break
                notes = self.data[attack_time]
                for note in reversed(notes):
                    if (
                        stop_at_rest
                        and note.attack_time + note.dur < last_attack_time
                    ):
                        # Is there any reason not to use the built-in
                        # StopIteration for this purpose?
                        raise StopIteration
                    out_notes.insert(0, note)
                    n -= 1
                    last_attack_time = note.attack_time
        except StopIteration:
            pass

        for _ in range(n, 0, -1):
            out_notes.insert(0, None)
        return out_notes

    # def get_prev_n_notes2(
    #     self,
    #     n,
    #     time,
    #     min_attack_time=0,
    #     stop_at_rest=False,
    #     include_start_time=False,
    # ):
    #     """Like get_prev_n_pitches, but returns Note objects.
    #
    #     If notes are attacked earlier than min_attack_time, None will be
    #     returned instead. Or, if stop_at_rest is True, then instead of any
    #     pitches earlier than the first rest, None will be returned instead.
    #     """
    #
    #     attack_times = list(self.data.keys())
    #     i = er_misc_funcs.binary_search(attack_times, time)
    #     out_notes = []
    #     if n <= 0:
    #         return out_notes
    #     if i is not None and include_start_time:
    #         i += 1
    #     while i is not None:
    #         i -= 1
    #         if i < 0:
    #             break
    #         attack_time = attack_times[i]
    #         if attack_time == time and not include_start_time:
    #             continue
    #
    #         notes = self.data[attack_time]
    #         break_out = False
    #         for note in reversed(notes):
    #             if note.attack_time < min_attack_time:
    #                 break_out = True
    #                 break
    #             if (
    #                 stop_at_rest
    #                 and note.attack_time + note.dur < last_attack_time
    #             ):
    #                 break_out = True
    #                 break
    #             out_notes.insert(0, note)
    #             last_attack_time = note.attack_time
    #             if len(out_notes) == n:
    #                 break_out = True
    #                 break
    #         if break_out:
    #             break
    #
    #     for _ in range(n - len(out_notes)):
    #         out_notes.insert(0, None)
    #     return out_notes

    def get_prev_note(self, time, min_attack_time=0, stop_at_rest=False):
        """Returns previous Note from voice."""
        return self.get_prev_n_notes(
            1, time, min_attack_time=min_attack_time, stop_at_rest=stop_at_rest
        )[0]

    def get_last_n_notes(self, n, time, min_attack_time=0, stop_at_rest=False):
        """Returns last n pitches (including pitch attacked at time).
        """
        return self.get_prev_n_notes(
            n,
            time,
            min_attack_time=min_attack_time,
            stop_at_rest=stop_at_rest,
            include_start_time=True,
        )

    def get_passage(self, passage_start_time, passage_end_time):

        """Returns a single voice of a given passage.

        Passage includes notes attacked during the given time interval,
        but not notes sounding but attacked earlier. Passage is inclusive
        of passage_start_time and exclusive of passage_end_time.

        Doesn't change the "voice" attributes of the notes.
        """

        new_voice = Voice(tet=self.tet, voice_range=self.range)

        for note in self:
            attack_time = note.attack_time
            if attack_time < passage_start_time:
                continue
            if attack_time >= passage_end_time:
                break
            try:
                new_voice[attack_time].append(copy.copy(note))
            except KeyError:
                new_voice[attack_time] = [
                    copy.copy(note),
                ]

        return new_voice

    def repeat_passage(
        self, original_start_time, original_end_time, repeat_start_time
    ):
        """Repeats a voice."""
        repeated_notes = []
        for note in self:
            attack_time = note.attack_time
            if attack_time < original_start_time:
                continue
            if attack_time >= original_end_time:
                break
            repeat_time = repeat_start_time + attack_time - original_start_time
            repeat_note = copy.copy(note)
            repeat_note.attack_time = repeat_time
            repeated_notes.append(repeat_note)

        for repeat_note in repeated_notes:
            self.add_note_object(repeat_note, update_sort=False)
        self.update_sort()
        self.sort_up_to_date += 1

    def transpose(self, interval, start_time=0, end_time=None):
        """Transposes a passage."""

        for note in self:
            attack_time = note.attack_time
            if attack_time < start_time:
                continue
            if end_time is not None and attack_time >= end_time:
                break
            note.pitch += interval

    def displace_passage(self, displacement, start_time=None, end_time=None):
        if displacement == 0:
            return
        notes_to_move = []
        for note_object in self:
            if start_time and start_time > note_object.attack_time:
                continue
            if end_time and note_object.attack_time >= end_time:
                continue
            notes_to_move.append(note_object)

        for note_object in notes_to_move:
            self.remove_note_object(note_object)
            note_object.attack_time = note_object.attack_time + displacement
            if note_object.attack_time >= 0:
                self.add_note_object(note_object, update_sort=False)

        self.update_sort()
        self.sort_up_to_date += 1


class VoiceList(collections.UserList):
    def __init__(self, iterable=(), num_new_voices=None, existing_voices=()):
        super().__init__()
        self.data = list(iterable)
        if num_new_voices is None:
            self.num_new_voices = len(iterable)
        else:
            self.num_new_voices = num_new_voices
            if iterable and len(iterable) != num_new_voices:
                print(
                    "Warning: VoiceList constructor called with an iterable "
                    "and a num_new_voices, and length of iterable does not "
                    "agree."
                )
        self.existing_voices = existing_voices
        self.num_existing_voices = len(existing_voices)

    def __getitem__(self, key):
        if 0 <= key < self.num_new_voices:
            # try:
            return self.data[key]
            # except IndexError:
            #     breakpoint()
        if (
            self.num_new_voices
            < key
            <= self.num_new_voices + self.num_existing_voices
        ):
            # An IndexError will be raised between the indices
            #   for the new voices properly in this list and the
            #   existing voices. This must be so to permit
            #   iteration over the list proper. So, for instance,
            #   if there are 3 new voices and 2 existing voices,
            #   indices 0-2 will access the new voices and 4-5 the
            #   existing voices, while 3 will raise an IndexError.
            return self.existing_voices[key - self.num_new_voices - 1]
        if key < 0:
            return self.data[self.num_new_voices + key]
        raise IndexError()

    def append(self, item):
        self.data.append(item)
        self.num_new_voices += 1

    # I don't understand pylint's objection here
    def extend(self, iterable):  # pylint: disable=arguments-differ
        self.data.extend(iterable)
        self.num_new_voices += len(iterable)

    def insert(self, i, item):
        self.data.insert(i, item)
        self.num_new_voices += 1

    def remove(self, item):
        self.data.remove(item)
        self.num_new_voices -= 1

    def pop(self, i=None):
        if i is not None:
            out = self.data.pop(i)
        else:
            out = self.data.pop()
        self.num_new_voices -= 1
        return out

    def copy(self):
        return copy.deepcopy(self)


class HarmonyTimes:
    def __init__(self, start, end):
        self.start_time = start
        self.end_time = end


class Score:
    """Contains the notes, as well as many methods for working with them.

    Arguments:
        harmony_len: Used to construct attribute "harmony_times_dict"
            and associated methods. If passed, pass "total_len" as well.
        total_len: Total length of the music that will be stored. Only used
            in calculation of "harmony_times_dict", so you can add notes
            beyond this time without consequence.

    """

    def __str__(self, head=-1):
        strings = []
        for voice_type, voice_list in (
            ("EXISTING VOICE", self.existing_voices),
            ("VOICE", self.voices),
        ):
            for voice_i, voice in enumerate(voice_list):
                strings.append("#" * 51)
                strings.append(f"{voice_type} {voice_i}")
                strings.append("#" * 51)
                n = 0
                for note in voice:
                    if head > 0:
                        if n > head:
                            break
                        n += 1
                    strings.append(
                        "Attack:{:>10.3}  Pitch:{:>5}  Duration:{:>10.3}"
                        "".format(
                            float(note.attack_time),
                            self.speller.spell(note.pitch),
                            float(note.dur),
                        )
                    )
                strings.append("\n")
        return "\n".join(strings)[:-2]

    def head(self, head=15):
        return self.__str__(head=head)

    def __iter__(self):
        # This iterates over new *and* existing voices... is there any
        # use case for doing just one over the other?
        attack_times = []
        for voice_i in self.all_voice_is:
            attack_times += self.voices[voice_i].data.keys()
        attack_times = sorted(list(set(attack_times)))
        for attack_time in attack_times:
            out = []
            for voice_i in self.all_voice_is:
                try:
                    out += self.voices[voice_i].data[attack_time]
                except KeyError:
                    pass
            yield out

    def get_total_len(self):
        """Returns the length of the super pattern from 0 to the final note
        release.
        """
        total_len = 0
        for voice in self.voices:
            try:
                max_attack = max(voice.data)
            except ValueError:
                # if a voice is empty, max will return a ValueError
                continue
            max_dur = max([note.dur for note in voice[max_attack]])
            final_release = max_attack + max_dur
            if final_release > total_len:
                total_len = final_release

        return total_len

    def add_voice(self, voice=None, voice_i=None, voice_range=None):
        """Adds a voice."""
        if voice:
            self.voices.append(voice)
            if voice_i is not None:
                self.voices[-1].voice_i = voice_i
        else:
            if voice_i is None:
                voice_i = self.num_voices
            self.voices.append(
                Voice(voice_i=voice_i, tet=self.tet, voice_range=voice_range)
            )
        self.num_voices += 1
        return self.voices[self.num_voices - 1]

    def remove_empty_voices(self):
        """Removes any voices that contain no notes."""

        non_empty_voices = list(range(self.num_voices))
        for voice_i, voice in enumerate(self.voices):
            if not voice:
                non_empty_voices.remove(voice_i)

        new_voices = VoiceList()
        for non_empty_voice_i in non_empty_voices:
            new_voices.append(self.voices[non_empty_voice_i])
        self.voices = new_voices

    def add_note(
        self,
        voice_i,
        pitch,
        attack_time,
        dur,
        velocity=DEFAULT_VELOCITY,
        choir=DEFAULT_CHOIR,
    ):
        """Adds a note to the specified voice.
        """
        self.voices[voice_i].add_note(
            pitch, attack_time, dur, velocity=velocity, choir=choir
        )

    def add_note_object(self, voice_i, note_object, update_sort=True):
        """Adds a note object to the specified voice.
        """
        self.voices[voice_i].add_note_object(
            note_object, update_sort=update_sort
        )

    def add_other_message(self, voice_i, message):
        self.voices[voice_i].add_other_message(message)

    def add_meta_message(self, message):
        self.meta_messages.append(message)

    def attack(self, attack_time, voice_i):
        """Check if an attack occurs in the given voice
        at the specified time."""
        if attack_time in self.voices[voice_i]:
            return True
        return False

    def fill_with_rests(self, end_time):
        """Fills all silences with "rests" (Note classes with pitch,
        choir, and velocity all None).

        end_time must be passed (in order to fill the end of the last measure
        with rests).

        For now this is only used for writing kern files.
        """
        for voice_i, voice in enumerate(self.voices):
            temp_voice = Voice(
                voice_i=voice.voice_i, tet=voice.tet, voice_range=voice.range
            )
            prev_release = 0
            for note in voice:
                attack_time = note.attack_time
                if attack_time > prev_release:
                    rest_attack = prev_release
                    rest_dur = attack_time - prev_release
                    temp_voice.add_rest(rest_attack, rest_dur)
                prev_release = attack_time + note.dur
                temp_voice.add_note_object(note)
            if prev_release < end_time:
                rest_attack = prev_release
                rest_dur = end_time - prev_release
                temp_voice.add_rest(rest_attack, rest_dur)

            self.voices[voice_i] = temp_voice

    def displace_passage(
        self,
        displacement,
        start_time=None,
        end_time=None,
        apply_to_existing_voices=False,
    ):
        """Moves a passage forward or backward in time.

        Any notes whose attack times are moved before 0 will be deleted.

        Any meta messages whose attack times that would be displaced below
        time 0 are placed at time 0.

        If start_time is not specified, passage moved starts from beginning
        of score. If end_time is not specified, passage moved continues to
        end of score. If neither are specified, entire score is moved.
        """
        # LONGTERM add parameter to overwrite existing music when displacing
        if displacement == 0:
            return
        if apply_to_existing_voices:
            voices = self.voices + self.existing_voices
        else:
            voices = self.voices
        for voice in voices:
            voice.displace_passage(displacement, start_time, end_time)

        for msg in self.meta_messages:
            # LONGTERM don't move tempo changes past beginning of passage
            if start_time and msg.time < start_time:
                continue
            if end_time and msg.time >= end_time:
                continue
            msg.time = max(msg.time + displacement, 0)

    def remove_passage(
        self, start_time, end_time=0, apply_to_existing_voices=False
    ):
        """Removes from the specified start time until the specified end time.

        If end time is 0, then removes until the end of the Score.
        """
        # LONGTERM what to do about overlapping durations?

        if apply_to_existing_voices:
            voice_lists = (self.voices, self.existing_voices)
        else:
            voice_lists = (self.voices,)
        for voice_list in voice_lists:
            for voice in voice_list:
                to_remove = []
                for attack in voice.data:
                    if attack < start_time:
                        continue
                    if end_time != 0 and attack >= end_time:
                        continue
                    to_remove.append(attack)
                for attack in to_remove:
                    del voice.data[attack]

    def repeat_passage(
        self,
        original_start_time,
        original_end_time,
        repeat_start_time,
        apply_to_existing_voices=False,
    ):
        """Repeats a passage."""
        if apply_to_existing_voices:
            voices = self.voices + self.existing_voices
        else:
            voices = self.voices
        for voice in voices:
            voice.repeat_passage(
                original_start_time, original_end_time, repeat_start_time
            )
        # LONGTERM handle meta messages?

    def transpose(
        self, interval, start_time, end_time, apply_to_existing_voices=False
    ):
        for voice in self.voices:
            voice.transpose(interval, start_time, end_time)
        if apply_to_existing_voices:
            for voice in self.existing_voices:
                voice.transpose(interval, start_time, end_time)

    def get_passage(self, passage_start_time, passage_end_time):
        """Returns all voices of a given passage as a Score object.

        Passage includes notes attacked during the given time interval,
        but not notes sounding but attacked earlier. Passage is inclusive
        of passage_start_time and exclusive of passage_end_time.
        """
        passage = Score(
            tet=self.tet, harmony_times_dict=self.harmony_times_dict
        )
        for voice in self.voices:
            new_voice = voice.get_passage(passage_start_time, passage_end_time)
            passage.add_voice(
                new_voice, voice_i=voice.voice_i, voice_range=voice.range
            )

        first_tempo_msg_after_passage_start = None
        for msg in self.meta_messages:
            if msg.time < passage_start_time:
                if msg.type == "set_tempo":
                    last_tempo_msg_before_passage_start = msg
                continue
            if msg.time >= passage_end_time:
                continue
            if (
                msg.type == "set_tempo"
                and first_tempo_msg_after_passage_start is None
            ):
                first_tempo_msg_after_passage_start = msg
            passage.add_meta_message(copy.deepcopy(msg))
        if (
            first_tempo_msg_after_passage_start is None
            or first_tempo_msg_after_passage_start.time > passage_start_time
        ):
            try:
                tempo_msg = copy.deepcopy(last_tempo_msg_before_passage_start)
                tempo_msg.time = passage_start_time
                passage.add_meta_message(tempo_msg)
            except NameError:
                pass

        return passage

    def get_harmony_times(self, harmony_i):
        return self.harmony_times_dict[harmony_i]

    def get_harmony_i(self, attack_time):
        """If passed an attack time beyond the end of the harmonies, will
        return the last harmony.
        """
        for harmony_i in self.harmony_times_dict:
            try:
                if (
                    self.harmony_times_dict[harmony_i + 1].start_time
                    > attack_time
                ):
                    return harmony_i
            except KeyError:
                return harmony_i
        return harmony_i

    def get_sounding_voices(
        self, attack_time, dur=0, min_attack_time=0, min_dur=0
    ):
        """Get voices sounding at attack_time (if dur==0) or between
        attack_time and attack_time + dur.
        """
        out = []
        for voice_i in self.all_voice_is:
            if self.voices[voice_i].get_sounding_pitches(
                attack_time,
                dur=dur,
                min_attack_time=min_attack_time,
                min_dur=min_dur,
            ):
                out.append(voice_i)
        return out

    def get_sounding_pitches(
        self, attack_time, dur=0, voices="all", min_attack_time=0, min_dur=0
    ):

        sounding_pitches = set()

        if voices == "all":
            voices = self.all_voice_is

        for voice_i in voices:
            voice = self.voices[voice_i]
            sounding_pitches.update(
                voice.get_sounding_pitches(
                    attack_time,
                    dur=dur,
                    min_attack_time=min_attack_time,
                    min_dur=min_dur,
                )
            )

        for existing_voice in self.existing_voices:
            # Existing voices are always retrieved.
            sounding_pitches.update(
                existing_voice.get_sounding_pitches(
                    attack_time,
                    dur=dur,
                    min_attack_time=min_attack_time,
                    min_dur=min_dur,
                )
            )

        return list(sorted(sounding_pitches))

    def get_simultaneously_attacked_pitches(
        self, attack_time, voices="all", min_dur=0
    ):
        return self.get_sounding_pitches(
            attack_time,
            voices=voices,
            min_attack_time=attack_time,
            min_dur=min_dur,
        )

    def get_all_pitches_attacked_during_duration(
        self, attack_time, dur, voices="all"
    ):
        return self.get_sounding_pitches(
            attack_time, dur=dur, voices=voices, min_attack_time=attack_time
        )

    def get_all_pitches_sounding_during_duration(
        self, attack_time, dur, voices="all", min_dur=0
    ):
        return self.get_sounding_pitches(
            attack_time, dur=dur, voices=voices, min_dur=min_dur
        )

    def get_prev_n_pitches(
        self, n, time, voice_i, min_attack_time=0, stop_at_rest=False
    ):
        """Returns previous n pitches (attacked before time).

        If pitches are attacked earlier than min_attack_time, -1 will be
        returned instead.
        """
        return self.voices[voice_i].get_prev_n_pitches(
            n, time, min_attack_time=min_attack_time, stop_at_rest=stop_at_rest
        )

    def get_prev_pitch(
        self, time, voice_i, min_attack_time=0, stop_at_rest=False
    ):
        """Returns previous pitch from voice."""
        return self.voices[voice_i].get_prev_n_pitches(
            1, time, min_attack_time=min_attack_time, stop_at_rest=stop_at_rest
        )[0]

    def get_last_n_pitches(
        self, n, time, voice_i, min_attack_time=0, stop_at_rest=False
    ):
        """Returns last n pitches (including pitch attacked at time).
        """
        return self.voices[voice_i].get_prev_n_pitches(
            n,
            time,
            min_attack_time=min_attack_time,
            stop_at_rest=stop_at_rest,
            include_start_time=True,
        )

    def _build_harmony_times_dict(self, harmony_len, total_len=None):
        class HarmonyTimesDictError(Exception):
            pass

        if total_len is None:
            raise HarmonyTimesDictError(
                "Must pass total_len with harmony_len when creating "
                "Score object."
            )

        self.harmony_times_dict = {}
        harmony_i = 0
        start_time = 0
        end_time = 0
        while True:
            end_time += harmony_len[harmony_i % len(harmony_len)]
            self.harmony_times_dict[harmony_i] = HarmonyTimes(
                start_time, end_time
            )
            # self.harmony_times_dict[harmony_i] = (start_time, end_time)
            start_time = end_time
            harmony_i += 1
            if end_time > total_len:
                break

    @property
    def all_voice_is(self):
        return list(range(self.voices.num_new_voices)) + [
            i + self.voices.num_new_voices + 1
            for i in range(self.voices.num_existing_voices)
        ]

    def __init__(
        self,
        num_voices=0,
        tet=12,
        harmony_len=None,
        harmony_times_dict=None,
        total_len=None,
        ranges=(None,),
        time_sig=None,
        existing_score=None,
    ):

        if harmony_times_dict:
            self.harmony_times_dict = harmony_times_dict
        elif harmony_len:
            self._build_harmony_times_dict(harmony_len, total_len=total_len)
        else:
            self.harmony_times_dict = None
        self.tet = tet
        self.speller = er_tuning.Speller(tet)
        self.existing_voices = []
        if existing_score:
            for voice in existing_score.voices:
                self.existing_voices.append(voice)
            self.voices = VoiceList(
                # num_new_voices=num_voices,
                existing_voices=self.existing_voices
            )
        else:
            self.voices = VoiceList()  # num_new_voices=num_voices)
        self.meta_messages = []
        self.n_since_chord_tone_list = []
        self.num_voices = 0
        self.time_sig = time_sig
        self.attacks_adjusted_by = 0

        for i in range(num_voices):
            self.add_voice(voice_range=ranges[i % len(ranges)])


if __name__ == "__main__":
    v = VoiceList([1, 2, 3, 4], num_new_voices=3)
    v.append(5)
    print(v)
    print(v.num_new_voices)
