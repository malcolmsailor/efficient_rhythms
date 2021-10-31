import copy

import sortedcontainers

import mspell

from .. import er_classes


class HarmonyTimes:
    def __init__(self, start, end, i):
        self.start_time = start
        self.end_time = end
        self.i = i

    def __repr__(self):
        return (
            f"{self.__class__.__name__}(start_time={self.start_time}, "
            f"end_time={self.end_time}, i={self.i})"
        )


class Score:
    """Contains the notes, as well as many methods for working with them.

    Keyword arguments:
        num_voices
        test
        harmony_len: Used to construct attribute "harmony_times_dict"
            and associated methods (unless harmony_times_dict is also passed,
            in which case this argument has no effect). If passed, pass
            "total_len" as well.
        harmony_times_dict: can be passed in directly when copying an
            existing Score object. Otherwise use harmony_len.
        total_len: Total length of the music that will be stored. Only used
            in calculation of "harmony_times_dict", so you can add notes
            beyond this time without consequence.

    Attributes:
        harmony_times
        all_voice_idxs
        total_dur
        first_onset_and_notes

    Methods:
        head

        add_voice
        remove_empty_voices
        add_note
        add_other_message
        add_meta_message
        onset
        fill_with_rests
        displace_passage
        remove_passage
        repeat_passage
        transpose
        get_passage
        get_harmony_times
        get_harmony_i
        get_harmony_times_from_onset
        get_sounding_voices
        get_sounding_pitches
        get_simultaneously_onset_ps
        get_all_ps_onset_in_dur
        get_all_ps_sounding_in_dur
        get_prev_n_pitches
        get_prev_pitch
        get_last_n_pitches


    """

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
        try:
            self.speller = mspell.Speller(tet, pitches=True)
        except ValueError:
            self.speller = lambda x: x
        self.existing_voices = []
        if existing_score:
            for voice in existing_score.voices:
                self.existing_voices.append(voice)
            self.voices = er_classes.VoiceList(
                existing_voices=self.existing_voices
            )
        else:
            self.voices = er_classes.VoiceList()  # num_new_voices=num_voices)
        self.meta_messages = []
        self.n_since_chord_tone_list = []
        self.num_voices = 0
        self.time_sig = time_sig
        self.onsets_adjusted_by = 0

        for i in range(num_voices):
            self.add_voice(voice_range=ranges[i % len(ranges)])

    def __str__(self, head=-1):
        strings = []
        for voice_type, voice_list in (
            ("EXISTING VOICE", self.existing_voices),
            ("VOICE", self.voices),
        ):
            for voice_i, voice in enumerate(voice_list):
                strings.append("#" * 52)
                strings.append(f"{voice_type} {voice_i}")
                strings.append("#" * 52)
                n = 0
                for note in voice:
                    if head > 0:
                        if n > head:
                            break
                        n += 1
                    strings.append(
                        "Attack:{:>10.5}  Pitch:{:>6}  Duration:{:>10.5}"
                        "".format(
                            float(note.onset),
                            self.speller(note.pitch),
                            float(note.dur),
                        )
                    )
                strings.append("\n")
        return "\n".join(strings)[:-2]

    def head(self, head=15):
        return self.__str__(head=head)

    # LONGTERM implement "score note iterator?"
    def __iter__(self):
        for voice_i in self.all_voice_idxs:
            yield self.voices[voice_i]

    def between(self, start_time=None, end_time=None):
        # voice.between() should be preferred to score.between() wherever
        # possible.
        def _sort_next_notes():
            next_notes.sort(key=lambda t: t[1].onset, reverse=True)

        voice_gens = [
            voice.between(start_time, end_time) for voice in self.voices
        ]
        next_notes = []
        for voice_i, voice_gen in enumerate(voice_gens):
            try:
                next_notes.append((voice_i, next(voice_gen)))
            except StopIteration:
                pass

        _sort_next_notes()
        while next_notes:
            voice_i, next_note = next_notes[-1]
            yield next_note
            try:
                next_notes[-1] = (voice_i, next(voice_gens[voice_i]))
            except StopIteration:
                next_notes.pop()
            else:
                _sort_next_notes()

    def notes_by_onset_between(self, start_time=None, end_time=None):
        def _sort_next_notes():
            next_notes.sort(key=lambda t: t[1].onset)

        voice_gens = [
            voice.between(start_time, end_time) for voice in self.voices
        ]
        next_notes = []
        for voice_i, voice_gen in enumerate(voice_gens):
            try:
                next_notes.append((voice_i, next(voice_gen)))
            except StopIteration:
                pass
        _sort_next_notes()

        while next_notes:
            out = []
            to_pop = []
            onset = next_notes[0][1].onset
            for i in range(len(next_notes)):
                voice_i, next_note = next_notes[i]
                if next_note.onset != onset:
                    break
                while next_note.onset == onset:
                    out.append(next_note)
                    try:
                        next_note = next(voice_gens[voice_i])
                    except StopIteration:
                        to_pop.append(i)
                        break
                next_notes[i] = (voice_i, next_note)
            yield out
            to_pop.sort(reverse=True)
            for i in to_pop:
                next_notes.pop(i)
            _sort_next_notes()

    @property
    def total_dur(self):
        """Returns the length of the super pattern from 0 to the final note
        release.
        """
        releases = []
        for voice in self:
            try:
                releases.append(voice.last_release_and_notes[0])
            except IndexError:
                pass
        if not releases:
            return 0
        return max(releases)

    def add_voice(self, voice=None, voice_i=None, voice_range=None):
        """Adds a voice."""
        if voice:
            self.voices.append(voice)
            # this allows the new voice to have a value for voice_i that
            # doesn't conform to its index position in self.voices. What is
            # the use of that? Shouldn't we automatically assign the appropriate
            # index?
            if voice_i is not None:
                self.voices[-1].voice_i = voice_i
        else:
            if voice_i is None:
                voice_i = self.num_voices
            self.voices.append(
                er_classes.Voice(
                    voice_i=voice_i, tet=self.tet, voice_range=voice_range
                )
            )
        self.num_voices += 1
        return self.voices[self.num_voices - 1]

    def remove_empty_voices(self, update_indices=False):
        """Removes any voices that contain no notes."""

        non_empty_voices = list(range(self.num_voices))
        for voice_i, voice in enumerate(self.voices):
            if voice.is_empty():
                non_empty_voices.remove(voice_i)

        new_voices = er_classes.VoiceList()
        for new_voice_i, non_empty_voice_i in enumerate(non_empty_voices):
            if update_indices:
                self.voices[non_empty_voice_i] = new_voice_i
            new_voices.append(self.voices[non_empty_voice_i])
        self.voices = new_voices

    def add_note(
        self,
        voice_i,
        note_obj_or_pitch,
        onset=None,
        dur=None,
        velocity=er_classes.DEFAULT_VELOCITY,
        choir=er_classes.DEFAULT_CHOIR,
    ):
        """Adds a note to the specified voice."""
        self.voices[voice_i].add_note(
            note_obj_or_pitch, onset, dur, velocity=velocity, choir=choir
        )

    def add_other_message(self, voice_i, message):
        self.voices[voice_i].add_other_message(message)

    def add_meta_message(self, message):
        try:
            if message.type == "time_signature":
                if self.time_sig is None:
                    self.time_sig = (message.numerator, message.denominator)
                else:
                    print(
                        "Warning: midi file has more than one time signature. "
                        "Only the first is supported."
                    )
        except AttributeError:
            pass
        self.meta_messages.append(message)

    def onset(self, onset, voice_i):
        """Check if an onset occurs in the given voice
        at the specified time."""
        return onset in self.voices[voice_i]

    def fill_with_rests(self, end_time):
        """Fills all silences with "rests" (Note classes with pitch,
        choir, and velocity all None).

        end_time must be passed (in order to fill the end of the last measure
        with rests).

        For now this is only used for writing kern files.
        """
        for voice in self:
            voice.fill_with_rests(end_time)

    def displace_passage(
        self,
        displacement,
        start_time=None,
        end_time=None,
        apply_to_existing_voices=False,
    ):
        """Moves a passage forward or backward in time.

        Any notes whose onset times are moved before 0 will be deleted.

        Any meta messages whose onset times that would be displaced below
        time 0 are placed at time 0.

        If start_time is not specified, passage moved starts from beginning
        of score. If end_time is not specified, passage moved continues to
        end of score. If neither are specified, entire score is moved.
        """
        # LONGTERM add parameter to overwrite existing music when displacing
        if displacement == 0:
            return

        for voice in self.voices:
            voice.displace_passage(displacement, start_time, end_time)
        if apply_to_existing_voices:
            for voice in self.existing_voices:
                voice.displace_passage(displacement, start_time, end_time)

        for msg in self.meta_messages:
            # LONGTERM don't move tempo changes past beginning of passage
            if start_time and msg.time < start_time:
                continue
            if end_time and msg.time >= end_time:
                continue
            msg.time = max(msg.time + displacement, 0)

    def remove_passage(
        self, start_time=None, end_time=None, apply_to_existing_voices=False
    ):
        """Removes from the specified start time until the specified end time."""
        # LONGTERM what to do about overlapping durations?
        for voice in self.voices:
            voice.remove_passage(start_time=start_time, end_time=end_time)
        if apply_to_existing_voices:
            for voice in self.existing_voices:
                voice.remove_passage(start_time=start_time, end_time=end_time)

    def repeat_passage(
        self,
        original_start_time,
        original_end_time,
        repeat_start_time,
        apply_to_existing_voices=False,
    ):
        """Repeats a passage."""
        for voice in self.voices:
            voice.repeat_passage(
                original_start_time, original_end_time, repeat_start_time
            )
        if apply_to_existing_voices:
            for voice in self.existing_voices:
                voice.repeat_passage(
                    original_start_time, original_end_time, repeat_start_time
                )
        # LONGTERM handle meta messages?

    def transpose(
        self,
        interval,
        er=None,  # triggers generic transposition if passed
        max_interval=None,  # ignored unless generic transposition
        finetune=0,
        start_time=None,
        end_time=None,
        apply_to_existing_voices=False,
    ):
        for voice in self.voices:
            voice.transpose(
                interval,
                er=er,
                score=self if er is not None else None,
                max_interval=max_interval,
                finetune=finetune,
                start_time=start_time,
                end_time=end_time,
            )
        if apply_to_existing_voices:
            for voice in self.existing_voices:
                voice.transpose(
                    interval,
                    er=er,
                    score=self if er is not None else None,
                    max_interval=max_interval,
                    finetune=finetune,
                    start_time=start_time,
                    end_time=end_time,
                )

    def get_passage(self, passage_start_time, passage_end_time, make_copy=True):
        """Returns all voices of a given passage as a Score object.

        Passage includes notes with onsets during the given time interval,
        but not notes sounding but with earlier onsets. Passage is inclusive
        of passage_start_time and exclusive of passage_end_time.

        Keyword args:
            make_copy: if True, returns a copy of the notes in the passage. If
                False, returns the original notes (so they can be altered in
                place).
        """
        try:
            harmony_times_dict = self.harmony_times_dict.copy()
        except AttributeError:
            harmony_times_dict = None
        passage = Score(tet=self.tet, harmony_times_dict=harmony_times_dict)
        for voice in self:
            new_voice = voice.get_passage(
                passage_start_time, passage_end_time, make_copy=make_copy
            )
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
            passage.add_meta_message(copy.deepcopy(msg) if make_copy else msg)
        if (
            first_tempo_msg_after_passage_start is None
            or first_tempo_msg_after_passage_start.time > passage_start_time
        ):
            try:
                tempo_msg = (
                    copy.deepcopy(last_tempo_msg_before_passage_start)
                    if make_copy
                    else last_tempo_msg_before_passage_start
                )
                tempo_msg.time = passage_start_time
                passage.add_meta_message(tempo_msg)
            except NameError:
                pass

        return passage

    def get_harmony_times(self, harmony_i):
        return self._harmony_idx_to_time[harmony_i]

    def get_harmony_times_from_onset(self, onset):
        return self._harmony_idx_to_time[self.get_harmony_i(onset)]

    @property
    def harmony_times(self):
        return list(self._harmony_idx_to_time.values())

    def get_harmony_i(self, onset):
        """If passed an onset time beyond the end of the harmonies, will
        return the last harmony.
        """
        return self._harmony_time_to_idx.bisect_right(onset) - 1

    def get_sounding_voices(self, onset, dur=0, min_onset=0, min_dur=0):
        """Get voices sounding at onset (if dur==0) or between
        onset and onset + dur.
        """
        out = []
        for voice_i in self.all_voice_idxs:
            if self.voices[voice_i].get_sounding_pitches(
                onset,
                end_time=onset + dur,
                min_onset=min_onset,
                min_dur=min_dur,
            ):
                out.append(voice_i)
        return out

    def get_sounding_pitches(
        self,
        onset,
        end_time=None,
        voices=None,
        min_onset=0,
        min_dur=0,
    ):
        sounding_pitches = set()

        if voices is None:
            voices = self.all_voice_idxs

        for voice_i in voices:
            voice = self.voices[voice_i]
            sounding_pitches.update(
                voice.get_sounding_pitches(
                    onset,
                    end_time=end_time,
                    min_onset=min_onset,
                    min_dur=min_dur,
                )
            )

        return list(sorted(sounding_pitches))

    def get_simultaneously_onset_ps(self, onset, voices=None, min_dur=0):
        return self.get_sounding_pitches(
            onset,
            voices=voices,
            min_onset=onset,
            min_dur=min_dur,
        )

    def get_all_ps_onset_in_dur(self, onset, dur, voices=None):
        return self.get_sounding_pitches(
            onset,
            end_time=onset + dur,
            voices=voices,
            min_onset=onset,
        )

    def get_all_ps_sounding_in_dur(self, onset, dur, voices=None, min_dur=0):

        return self.get_sounding_pitches(
            onset,
            end_time=onset + dur,
            voices=voices,
            min_dur=min_dur,
        )

    def get_prev_n_pitches(
        self, n, time, voice_i, min_onset=0, stop_at_rest=False
    ):
        """Returns previous n pitches (with onset before time).

        If pitches are onset earlier than min_onset, -1 will be
        returned instead.
        """
        return self.voices[voice_i].get_prev_n_pitches(
            n, time, min_onset=min_onset, stop_at_rest=stop_at_rest
        )

    def get_prev_pitch(self, time, voice_i, min_onset=0, stop_at_rest=False):
        """Returns previous pitch from voice."""
        return self.voices[voice_i].get_prev_n_pitches(
            1, time, min_onset=min_onset, stop_at_rest=stop_at_rest
        )[0]

    def get_last_n_pitches(
        self, n, time, voice_i, min_onset=0, stop_at_rest=False
    ):
        """Returns last n pitches (including pitch with onset at time)."""
        return self.voices[voice_i].get_prev_n_pitches(
            n,
            time,
            min_onset=min_onset,
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
        self._harmony_idx_to_time = {}
        self._harmony_time_to_idx = sortedcontainers.SortedDict()
        harmony_i = start_time = end_time = 0
        while end_time < total_len:
            end_time += harmony_len[harmony_i % len(harmony_len)]
            harmony_times = HarmonyTimes(start_time, end_time, harmony_i)
            self._harmony_idx_to_time[harmony_i] = harmony_times
            self._harmony_time_to_idx[start_time] = harmony_times
            start_time = end_time
            harmony_i += 1
        # We want the final harmony_time to extend to the end of the score,
        # even if there are stray notes overlapping where the last harmony
        # "should" have ended. So we set it to None.
        harmony_times.end_time = None

    @property
    def all_voice_idxs(self):
        return list(range(self.voices.num_new_voices)) + [
            i + self.voices.num_new_voices + 1
            for i in range(self.voices.num_existing_voices)
        ]

    @property
    def first_onset_and_notes(self):
        first_onset = self.total_dur
        first_notes = None
        for voice in self:
            (
                first_onset_in_voice,
                first_note_in_voice,
            ) = voice.first_onset_and_notes
            if first_onset_in_voice < first_onset:
                first_onset, first_notes = (
                    first_onset_in_voice,
                    first_note_in_voice,
                )
        return first_onset, first_notes

    def copy(self):
        return copy.deepcopy(self)
