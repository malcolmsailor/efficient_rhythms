import collections
import copy


# TODO how does sortedcontainers compare to just using bisect from the
#   standard library?
import sortedcontainers

from .. import er_classes
from .. import er_spelling


class DumbSortedList(list):
    """A list that stays sorted.

    The purpose of this class is to store notes that share a given onset
    time. I expect that most often there will only be a single note at each
    onset time, and rarely more than 2. For this reason, any extra overhead
    from using a binary tree or the like seems not worth it. For any usage
    where these assumptions don't hold, consider replacing with
    sortedcontainers.SortedList
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sort()

    def __setitem__(self, *args, **kwargs):
        raise NotImplementedError

    def __setslice__(self, *args, **kwargs):
        raise NotImplementedError

    def append(self, *args, **kwargs):
        raise NotImplementedError("use 'add()' instead")

    def extend(self, *args, **kwargs):
        raise NotImplementedError("use 'add()' instead")

    def insert(self, *args, **kwargs):
        raise NotImplementedError("use 'add()' instead")

    def add(self, *args, **kwargs):
        super().append(*args, **kwargs)
        self.sort()

    def __copy__(self):
        new = DumbSortedList()
        super(DumbSortedList, new).extend(self)
        return new

    def copy(self):
        return self.__copy__()

    def __deepcopy__(self, memo):
        new = DumbSortedList()
        for item in self:
            super(DumbSortedList, new).append(copy.deepcopy(item, memo))
        return new


class BreakWhile(Exception):
    pass


class Voice:
    """A dictionary of lists of Note objects, together with methods for
    working with them.

    Can be iterated over (e.g., for note in voice [where "voice" is a
    Voice object]) and reversed (e.g., reversed(voice)). This will
    give the note objects sorted by onset time and secondarily by
    durations.

    Attributes:
    # TODO update this list
        data: a dictionary. Keys are onsets (fractions), values are
            lists of Note objects, sorted by duration.
        other_messages: a list in which other midi messages are stored
            when constructing the voice from a midi file.
        voice_i: int. The index number of the voice, if stored in a
            Score object.
        tet: int.
        range: Nonetype, or tuple of two ints. Used in certain
            transformers.

    Methods:
        is_polyphonic # TODO convert this to a (cached?) property
        get_notes_by_i
        add_note
        move_note
        remove_note
        remove_onset
        add_rest
        add_other_message
        append
        get_sounding_pitches
        get_all_ps_onset_in_dur
        get_prev_n_pitches
        get_prev_pitch
        get_last_n_pitches
        get_i_at_or_before
        get_i_before
        get_i_at_or_after
        get_prev_n_notes
        get_prev_note
        get_last_n_notes
        get_passage
        remove_passage
        repeat_passage
        transpose
        displace_passage
        fill_with_rests
        copy



    """

    def __init__(self, voice_i=None, tet=12, voice_range=None):
        self._data = sortedcontainers.SortedDict()
        self._releases = sortedcontainers.SortedDict()
        self.other_messages = []
        self.voice_i = voice_i
        self.tet = tet
        try:
            self.speller = er_spelling.Speller(tet, pitches=True)
        except ValueError:
            self.speller = lambda x: x
        self.range = voice_range

    def __len__(self):
        # returns the number of onsets (each of which potentially has more than
        # one note)
        return len(self._data)

    def peekitem(self, key):
        return self._data.peekitem(key)

    def __iter__(self):
        for onset in self._data:
            for note in self._data[onset]:
                yield note

    def __reversed__(self):
        for onset in reversed(self._data):
            for note in reversed(self._data[onset]):
                yield note

    def __str__(self):
        strings = []
        strings.append("#" * 52)
        for note in self:
            strings.append(
                "Attack:{:>10.3}  Pitch:{:>6}  Duration:{:>10.3}"
                "".format(
                    float(note.onset),
                    self.speller(note.pitch),
                    float(note.dur),
                )
            )
        strings.append("\n")
        return "\n".join(strings)[:-2]

    def __contains__(self, *args, **kwargs):
        return self._data.__contains__(*args, **kwargs)

    def __getitem__(self, *args, **kwargs):
        return self._data.__getitem__(*args, **kwargs)

    def __delitem__(self, onset):
        self.remove_onset(onset)

    def is_empty(self):  # TODO convert to property, document
        return len(self._data) == 0

    def is_polyphonic(self):
        for onset in self._data:
            if len(self._data[onset]) > 1:
                return True
        return False

    @property
    def first_onset_and_notes(self):
        return self._data.peekitem(0)

    @property
    def last_onset_and_notes(self):
        """Raises an IndexError if the voice is empty."""
        return self._data.peekitem()

    @property
    def last_release_and_notes(self):
        return self._releases.peekitem()

    def get_notes_by_i(self, i):
        return self._data.peekitem(i)[1]

    def add_note(
        self,
        note_obj_or_pitch,
        onset=None,
        dur=None,
        velocity=er_classes.DEFAULT_VELOCITY,
        choir=er_classes.DEFAULT_CHOIR,
    ):
        if isinstance(note_obj_or_pitch, er_classes.Note):
            note_obj = note_obj_or_pitch
            note_obj.voice = self.voice_i
        else:
            # is it worth asserting that onset and dur are not None here?
            note_obj = er_classes.Note(
                note_obj_or_pitch,
                onset,
                dur,
                velocity=velocity,
                choir=choir,
                voice=self.voice_i,
            )
        if note_obj.onset not in self._data:
            self._data[note_obj.onset] = DumbSortedList([note_obj])
        else:
            self._data[note_obj.onset].add(note_obj)
        if (release := note_obj.onset + note_obj.dur) not in self._releases:
            self._releases[release] = DumbSortedList([note_obj])
        else:
            self._releases[release].add(note_obj)

    def move_note(self, note_object, new_onset):
        """Moves a note object to a new onset time."""
        self.remove_note(note_object)
        note_object.onset = new_onset
        self.add_note(note_object)

    def remove_note(self, note_obj):
        """Removes given note object from self."""
        notes = self._data[note_obj.onset]
        notes.remove(note_obj)  # what kind of exception does this raise?
        if not notes:
            del self._data[note_obj.onset]
        release = note_obj.onset + note_obj.dur
        notes = self._releases[release]
        notes.remove(note_obj)
        if not notes:
            del self._releases[release]

    def remove_onset(self, onset):
        """Unconditionally removes and returns all notes at `onset`.

        `del voice[onset] calls this function`
        """
        # because self.remove_note alters self._data[onset], we need
        # to save a list of the notes to iterate
        notes = list(self._data[onset])
        for note in notes:
            self.remove_note(note)
        return notes

    def add_rest(self, onset, dur):
        self.add_note(None, onset, dur)

    def add_other_message(self, message):
        self.other_messages.append(message)

    def append(self, other_voice_or_sequence, offset=0, make_copy=True):
        """Appends the notes of another Voice object."""
        # I would like to rename this as "extend" or "concatenate"
        # but since list.append is called so often it is hard to search
        # the project for references to this method in order to change
        # them!
        for note in other_voice_or_sequence:
            if make_copy:
                note = note.copy()
            note.onset += offset
            self.add_note(note)

    def get_sounding_pitches(
        self,
        onset,
        end_time=None,
        min_onset=0,
        min_dur=0,
        sort_out=True,
    ):
        sounding_pitches = set()
        # end_time = onset + dur
        if end_time is None:
            end_time = onset
        # Unfortunately, we seem to need to iterate over all onsets that occur
        # before
        # the end of the interval (starting from 0), because there is no
        # constraint on how long
        # a note can be. So even if we are now at time 10000, there is no
        # guarantee that a note was not struck at time 0 with length 10001.
        # This inefficiency can be reduced somewhat by use of min_onset.
        # If this proves to be a bottleneck there is probably a more clever
        # way of performing the search that would be worth looking into.

        ## TODO Maybe this can be refactored using _releases?
        onsets_during_interval = self._data.irange(
            min_onset, end_time, inclusive=(True, onset == end_time)
        )
        for prev_onset in onsets_during_interval:
            for note in self._data[prev_onset]:
                if note.onset + note.dur <= onset:
                    continue
                if note.dur >= min_dur:
                    sounding_pitches.add(note.pitch)
        if sort_out:
            return list(sorted(sounding_pitches))
        return list(sounding_pitches)

    def get_all_ps_onset_in_dur(self, onset, dur):
        return self.get_sounding_pitches(
            onset, end_time=onset + dur, min_onset=onset
        )

    def get_all_ps_onset_between(self, start_time, end_time):
        if start_time is None:
            start_time = 0
        if end_time is None:
            end_time = self._releases.peekitem(-1)[0]
        return self.get_sounding_pitches(
            start_time, end_time, min_onset=start_time
        )

    def get_prev_n_pitches(
        self,
        n,
        time,
        min_onset=0,
        stop_at_rest=False,
        include_start_time=False,
    ):
        """Returns previous n pitches (onset before time).

        If pitches are onset earlier than min_onset, -1 will be
        returned instead. Or, if stop_at_rest is True, then instead of any
        pitches earlier than the first rest, -1 will be returned in place.
        """
        return [
            note.pitch if note is not None else -1
            for note in self.get_prev_n_notes(
                n,
                time,
                min_onset=min_onset,
                stop_at_rest=stop_at_rest,
                include_start_time=include_start_time,
            )
        ]

    def get_prev_pitch(self, time, min_onset=0, stop_at_rest=False):
        """Returns previous pitch from voice."""
        return self.get_prev_n_pitches(
            1, time, min_onset=min_onset, stop_at_rest=stop_at_rest
        )[0]

    def get_last_n_pitches(self, n, time, min_onset=0, stop_at_rest=False):
        """Returns last n pitches (including pitch onset at time)."""
        return self.get_prev_n_pitches(
            n,
            time,
            min_onset=min_onset,
            stop_at_rest=stop_at_rest,
            include_start_time=True,
        )

    def get_i_at_or_before(self, time):
        return self._data.bisect_right(time) - 1

    def get_i_before(self, time):
        # raises an Exception if called when self._data is empty
        # does this need to be fixed?
        i = self._data.bisect_right(time) - 1
        if time == self._data.peekitem(i)[0]:
            i -= 1
        return i

    def get_i_at_or_after(self, time):
        return self._data.bisect_left(time)

    def between(self, start_time=None, end_time=None):
        start_i = (
            self.get_i_at_or_after(start_time) if start_time is not None else 0
        )
        end_i = (
            self.get_i_at_or_after(end_time)
            if end_time is not None
            else len(self)
        )
        for i in range(start_i, end_i):
            notes = self.get_notes_by_i(i)
            for note in notes:
                yield note

    # I am not using this method
    # def increment_onset(self, prev_onset_time):
    #     """Get the first onset time *after* prev_onset_time.

    #     It is assumed that the prev_onset_time is in the voice.
    #     """
    #     i = self._data.bisect_left(prev_onset_time)
    #     return self._data.peekitem(i + 1)[0]

    def get_prev_n_notes(
        self,
        n,
        time,
        min_onset=0,
        stop_at_rest=False,
        include_start_time=False,
    ):

        if not self._data:
            return [None for _ in range(n)]

        if include_start_time:
            start_i = self.get_i_at_or_before(time)
        else:
            start_i = self.get_i_before(time)

        out_notes = []
        last_onset = time
        i_iter = iter(range(start_i, -1, -1))
        try:
            while n > 0:
                i = next(i_iter)
                onset, notes = self._data.peekitem(i)
                if onset < min_onset:
                    break
                for note in reversed(notes):
                    if stop_at_rest and note.onset + note.dur < last_onset:
                        raise BreakWhile
                    out_notes.append(note)
                    n -= 1
                    if n == 0:
                        break
                    last_onset = onset
        except (StopIteration, BreakWhile):
            pass

        if n:
            out_notes.extend([None for _ in range(n)])

        out_notes.reverse()
        return out_notes

    def get_prev_note(self, time, min_onset=0, stop_at_rest=False):
        """Returns previous Note from voice."""
        return self.get_prev_n_notes(
            1, time, min_onset=min_onset, stop_at_rest=stop_at_rest
        )[0]

    def get_last_n_notes(self, n, time, min_onset=0, stop_at_rest=False):
        """Returns last n pitches (including pitch onset at time)."""
        return self.get_prev_n_notes(
            n,
            time,
            min_onset=min_onset,
            stop_at_rest=stop_at_rest,
            include_start_time=True,
        )

    def get_passage(self, start_time, end_time, make_copy=True):

        """Returns a single voice of a given passage.

        Passage includes notes onset during the given time interval,
        but not notes sounding but onset earlier. Passage is inclusive
        of start_time and exclusive of end_time.

        Doesn't change the "voice" attributes of the notes.

        Keyword args:
            make_copy: if True, returns a copy of the notes in the passage. If
                False, returns the original notes (so they can be altered in
                place).
        """

        new_voice = Voice(tet=self.tet, voice_range=self.range)
        onsets = self._data.irange(
            start_time, end_time, inclusive=(True, False)
        )
        for onset in onsets:
            new_voice._data[onset] = [  # pylint: disable=protected-access
                note.copy() if make_copy else note for note in self._data[onset]
            ]
        return new_voice

    def remove_passage(self, start_time=None, end_time=None):
        """Like get_passage, but removes the returned passage from the voice.
        If either of start_time or end_time are not passed,
        removes to the start or end of the voice, respectively."""
        new_voice = Voice(tet=self.tet, voice_range=self.range)
        # We must cast the return value to a tuple because otherwise, it is
        # lazily evaluated and this causes problems because we are changing
        # the underlying data as we iterate through onsets
        onsets = tuple(
            self._data.irange(start_time, end_time, inclusive=(True, False))
        )
        for onset in onsets:
            new_voice._data[onset] = self.remove_onset(onset)
        return new_voice

    def repeat_passage(
        self, original_start_time, original_end_time, repeat_start_time
    ):
        """Repeats a voice."""
        original_onsets = self._data.irange(
            original_start_time, original_end_time, inclusive=(True, False)
        )
        for onset in original_onsets:
            for note in self._data[onset]:
                repeat_note = note.copy()
                repeat_note.onset = (
                    repeat_start_time + onset - original_start_time
                )
                self.add_note(repeat_note)

    def transpose(
        self,
        interval,
        er=None,  # triggers generic transposition if passed
        score=None,  # ignored unless generic transposition
        max_interval=None,  # ignored unless generic transposition
        finetune=0,
        start_time=None,
        end_time=None,
    ):
        """Transposes a passage."""
        onsets = self._data.irange(
            start_time, end_time, inclusive=(True, False)
        )
        if er is None:  # specific transpose
            for onset in onsets:
                for note in self._data[onset]:
                    note.pitch += interval
                    note.finetune += finetune
            return
        # generic transpose
        harmony_i = harmony_times = scale = adjusted_interval = None

        def _update_harmony_times():
            nonlocal harmony_i, harmony_times, scale, adjusted_interval
            if harmony_i is None:
                harmony_i = score.get_harmony_i(
                    start_time if start_time is not None else 0
                )
            else:
                harmony_i += 1
            harmony_times = score.get_harmony_times(harmony_i)
            scale = er.get(harmony_i, "gamut_scales")
            adjusted_interval = interval
            while adjusted_interval > abs(max_interval):
                adjusted_interval -= len(er.get(harmony_i, "pc_scales"))
            while adjusted_interval < -abs(max_interval):
                adjusted_interval += len(er.get(harmony_i, "pc_scales"))

        _update_harmony_times()
        for onset in onsets:
            if (
                harmony_times.end_time is not None
                and onset >= harmony_times.end_time
            ):
                _update_harmony_times()
            for note in self._data[onset]:
                orig_sd = scale.index(note.pitch)
                note.pitch = scale[orig_sd + adjusted_interval]

    def displace_passage(self, displacement, start_time=None, end_time=None):
        if displacement == 0:
            return

        if start_time is None:
            start_time = 0

        if -displacement > start_time:
            self.remove_passage(start_time, -displacement)
            start_time = -displacement
        if end_time is not None and start_time >= end_time:
            return

        passage = self.remove_passage(start_time, end_time)
        for note in passage:
            note.onset += displacement
            self.add_note(note)

    def fill_with_rests(self, until):
        prev_release = 0
        rests = []
        for onset, notes in self._data.items():
            if prev_release >= until:
                break
            if onset > prev_release:
                rests.append((prev_release, onset - prev_release))
            for note in notes:
                if onset + note.dur > prev_release:
                    prev_release = onset + note.dur

        if until > prev_release:
            rests.append((prev_release, until - prev_release))

        for onset, dur in rests:
            self.add_rest(onset, dur)

    def copy(self):

        return copy.deepcopy(self)


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
            return self.data[key]
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
