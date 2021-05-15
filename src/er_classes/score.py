import copy

import src.er_classes as er_classes
import src.er_spelling as er_spelling


class HarmonyTimes:
    def __init__(self, start, end):
        self.start_time = start
        self.end_time = end

    def __repr__(self):
        return (
            f"{self.__class__.__name__}(start_time={self.start_time}, "
            f"end_time={self.end_time})"
        )


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
                        "Attack:{:>10.3}  Pitch:{:>6}  Duration:{:>10.3}"
                        "".format(
                            float(note.attack_time),
                            self.speller(note.pitch),
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
                er_classes.Voice(
                    voice_i=voice_i, tet=self.tet, voice_range=voice_range
                )
            )
        self.num_voices += 1
        return self.voices[self.num_voices - 1]

    def remove_empty_voices(self):
        """Removes any voices that contain no notes."""

        non_empty_voices = list(range(self.num_voices))
        for voice_i, voice in enumerate(self.voices):
            if not voice:
                non_empty_voices.remove(voice_i)

        new_voices = er_classes.VoiceList()
        for non_empty_voice_i in non_empty_voices:
            new_voices.append(self.voices[non_empty_voice_i])
        self.voices = new_voices

    def add_note(
        self,
        voice_i,
        pitch,
        attack_time,
        dur,
        velocity=er_classes.DEFAULT_VELOCITY,
        choir=er_classes.DEFAULT_CHOIR,
    ):
        """Adds a note to the specified voice."""
        self.voices[voice_i].add_note(
            pitch, attack_time, dur, velocity=velocity, choir=choir
        )

    def add_note_object(self, voice_i, note_object, update_sort=True):
        """Adds a note object to the specified voice."""
        self.voices[voice_i].add_note_object(
            note_object, update_sort=update_sort
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
            temp_voice = er_classes.Voice(
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

    def get_passage(self, passage_start_time, passage_end_time, make_copy=True):
        """Returns all voices of a given passage as a Score object.

        Passage includes notes attacked during the given time interval,
        but not notes sounding but attacked earlier. Passage is inclusive
        of passage_start_time and exclusive of passage_end_time.

        Keyword args:
            make_copy: if True, returns a copy of the notes in the passage. If
                False, returns the original notes (so they can be altered in
                place).
        """
        passage = Score(
            tet=self.tet, harmony_times_dict=self.harmony_times_dict
        )
        for voice in self.voices:
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
        return self.harmony_times_dict[harmony_i]

    @property
    def harmony_times(self):
        return self._harmony_times

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
        """Returns last n pitches (including pitch attacked at time)."""
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
        harmony_times_list = []
        harmony_i = 0
        start_time = 0
        end_time = 0
        while True:
            end_time += harmony_len[harmony_i % len(harmony_len)]
            self.harmony_times_dict[harmony_i] = HarmonyTimes(
                start_time, end_time
            )
            harmony_times_list.append((start_time, end_time))
            # self.harmony_times_dict[harmony_i] = (start_time, end_time)
            start_time = end_time
            harmony_i += 1
            if end_time > total_len:
                break
        self._harmony_times = tuple(harmony_times_list)

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
        try:
            self.speller = er_spelling.Speller(tet, pitches=True)
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
        self.attacks_adjusted_by = 0

        for i in range(num_voices):
            self.add_voice(voice_range=ranges[i % len(ranges)])
