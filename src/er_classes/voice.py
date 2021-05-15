import collections
import copy

import src.er_classes as er_classes
import src.er_misc_funcs as er_misc_funcs
import src.er_spelling as er_spelling

# TODO is there any reason this needs to actually subclass UserDict?
# TODO maybe use defaultdict for internal data
# TODO think about the ideal data type for this class


class Voice(collections.UserDict):
    """A dictionary of lists of Note objects, together with methods for
    working with them.

    TODO I think a better structure for this data would be a list
        (or maybe a binary tree?)
        I think sortedcontainers.SortedKeyList is likely ideal
        - to get the first note at or after a given time, we can use
            binary search or built-in index (whichever is faster)
        - to get the last note of a passage, likewise
        - we can take slices as above
        - because we need to maintain numerical sort order, but also, two notes
            can occur at the same time, we need to sort on addition

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

    Methods:
        is_polyphonic # TODO convert this to a (cached?) property
        slice_keys
        update_sort
        update_attack_time
        add_note
        add_note_object # TODO combine with add_note
        move_note
        remove_note
        remove_note_object # TODO combine with remove_note
        add_rest
        add_other_message
        append # TODO rename extend or concatenate or something?
        get_sounding_pitches
        get_all_pitches_attacked_during_duration
        get_prev_n_pitches
        get_prev_pitch
        get_last_n_pitches
        get_prev_n_notes
        get_prev_note
        get_last_n_notes
        get_passage
        repeat_passage
        transpose
        displace_passage



    """

    def __init__(self, voice_i=None, tet=12, voice_range=None):
        super().__init__()
        self.other_messages = []
        # self.max_attack_time is used to check whether to sort the
        #   dictionary after adding a new note
        self.max_attack_time = 0
        self.voice_i = voice_i
        self.tet = tet
        try:
            self.speller = er_spelling.Speller(tet, pitches=True)
        except ValueError:
            self.speller = lambda x: x
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
        strings.append("#" * 52)
        for note in self:
            strings.append(
                "Attack:{:>10.3}  Pitch:{:>6}  Duration:{:>10.3}"
                "".format(
                    float(note.attack_time),
                    self.speller(note.pitch),
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
        velocity=er_classes.DEFAULT_VELOCITY,
        choir=er_classes.DEFAULT_CHOIR,
        update_sort=True,
    ):
        """Adds a note."""
        try:
            self[attack_time].append(
                er_classes.Note(
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
                er_classes.Note(
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
                er_classes.Note(
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
                er_classes.Note(
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
        """Returns last n pitches (including pitch attacked at time)."""
        return self.get_prev_n_pitches(
            n,
            time,
            min_attack_time=min_attack_time,
            stop_at_rest=stop_at_rest,
            include_start_time=True,
        )

    class BreakWhile(Exception):
        pass

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
            while n > 0:
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
                        raise self.BreakWhile
                    out_notes.insert(0, note)
                    n -= 1
                    if n <= 0:
                        raise self.BreakWhile
                    last_attack_time = note.attack_time
        except (StopIteration, self.BreakWhile):
            pass

        for _ in range(n, 0, -1):
            out_notes.insert(0, None)
        return out_notes

    def get_prev_note(self, time, min_attack_time=0, stop_at_rest=False):
        """Returns previous Note from voice."""
        return self.get_prev_n_notes(
            1, time, min_attack_time=min_attack_time, stop_at_rest=stop_at_rest
        )[0]

    def get_last_n_notes(self, n, time, min_attack_time=0, stop_at_rest=False):
        """Returns last n pitches (including pitch attacked at time)."""
        return self.get_prev_n_notes(
            n,
            time,
            min_attack_time=min_attack_time,
            stop_at_rest=stop_at_rest,
            include_start_time=True,
        )

    def get_passage(self, passage_start_time, passage_end_time, make_copy=True):

        """Returns a single voice of a given passage.

        Passage includes notes attacked during the given time interval,
        but not notes sounding but attacked earlier. Passage is inclusive
        of passage_start_time and exclusive of passage_end_time.

        Doesn't change the "voice" attributes of the notes.

        Keyword args:
            make_copy: if True, returns a copy of the notes in the passage. If
                False, returns the original notes (so they can be altered in
                place).
        """

        new_voice = Voice(tet=self.tet, voice_range=self.range)

        for note in self:
            attack_time = note.attack_time
            if attack_time < passage_start_time:
                continue
            if attack_time >= passage_end_time:
                break
            try:
                new_voice[attack_time].append(
                    copy.copy(note) if make_copy else note
                )
            except KeyError:
                new_voice[attack_time] = [
                    copy.copy(note) if make_copy else note,
                ]

        return new_voice

    def repeat_passage(
        self, original_start_time, original_end_time, repeat_start_time
    ):
        """Repeats a voice."""
        repeated_notes = []
        for note in self:
            attack_time = note.attack_time
            # TODO binary search to find first note
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
            # TODO binary search to find first note
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
