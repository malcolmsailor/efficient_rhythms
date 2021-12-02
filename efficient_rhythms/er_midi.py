"""Midi writing and reading functions for efficient_rhythms2.py
"""

import collections
import fractions
import os
import random
import warnings
from multiprocessing.dummy import Pool as ThreadPool

import mido

from . import er_choirs
from . import er_midi_settings
from . import er_classes
from . import er_tuning

# midi constants
META_TRACK = 0
CLOCKS_PER_TICK = 24
DEFAULT_CHANNEL = 0
DEFAULT_TRACK = 0
DEFAULT_VELOCITY = er_classes.DEFAULT_VELOCITY
NUM_CHANNELS = 16

# pitch_bend_tuple constants
MIDI_NUM = 0
PITCH_BEND = 1

# LONGTERM transpose notes up an octave as they voice-lead out of range

TIME_PRECISION = 12


def abs_to_delta_times(mf, skip=()):
    for track_i, track in enumerate(mf.tracks):
        if track_i in skip:
            continue
        # it's important that note-offs don't go after note-ons that should be
        #   at the same instant. Numerical error with floats sometimes leads to
        #   that happening, so we round to TIME_PRECISION when sorting here.
        track.sort(key=lambda x: round(x.time, TIME_PRECISION))
        current_tick_time = 0  # unrounded
        for msg in track:
            abs_tick_time = mf.ticks_per_beat * msg.time
            delta_tick_time = abs_tick_time - current_tick_time
            msg.time = round(delta_tick_time)
            current_tick_time = abs_tick_time


def get_rhythms_from_midi(er):
    midif = er.rhythms_specified_in_midi
    score = read_midi_to_internal_data(midif)
    if er.rhythms_in_midi_reverse_voices:
        score.voices = list(reversed(score.voices))
    rhythms = []
    for voice_i in range(er.num_voices):
        rhythm = {}
        rhythm_len = er.get(voice_i, "rhythm_len")
        voice = score.voices[voice_i % len(score.voices)]
        for note in voice:
            onset = note.onset
            if onset > rhythm_len:
                break
            rhythm[onset] = note.dur
        max_onset = max(rhythm)
        min_onset = min(rhythm)
        if er.overlap:
            overlap = min_onset - (max_onset + rhythm[max_onset] - rhythm_len)
        else:
            overlap = max_onset + rhythm[max_onset] - rhythm_len
        if overlap > 0:
            rhythm[max_onset] -= overlap
        rhythms.append(rhythm)

    return rhythms


def get_scales_and_chords_from_midi(midif, tet=12, time_sig=4):
    """Infer scales, chords, and foots from a midi file.

    Expects a midi file formatted as follows:
    1) Time signature is 4, although this can be changed with
    "time_sig" (needs to be an integer, however, for now at least)
    2) Contains two tracks, where each measure contains a complete pcset
       (i.e., as a chord of whole notes)
            A) track one has scales
            B) track two has chords

    Roots are inferred from the lowest pitch of each chord.

    Returns:
        A tuple of scales, chords, and foots (as pcsets).
    """

    score = read_midi_to_internal_data(midif, tet=tet)
    scales = [[]]
    chords = [[]]
    foots = []

    for i, pcset_type, pcsets in ((0, "scales", scales), (1, "chords", chords)):
        if pcset_type == "chords":
            lowest_pitch = tet * 100
        for note in score.voices[i]:
            onset = note.onset
            pitch = note.pitch
            if round(onset / time_sig) > len(pcsets) - 1:
                pcsets.append([])
                if pcset_type == "chords":
                    foots.append(lowest_pitch % tet)
                    lowest_pitch = tet * 100
            if pcset_type == "chords":
                if pitch < lowest_pitch:
                    lowest_pitch = pitch
            if pitch % tet not in pcsets[-1]:
                pcsets[-1].append(pitch % tet)
        if pcset_type == "chords":
            foots.append(lowest_pitch % tet)

    for i, foot in enumerate(foots):
        scales[i] = [(pitch - foot) % tet for pitch in scales[i]]
        scales[i].sort()
        chords[i] = [(pitch - foot) % tet for pitch in chords[i]]

    return (scales, chords, foots)


# this function is deprecated since switch to mido since mido takes human
# readable time signatures already.
# def get_midi_time_sig(time_sig):
#     """Takes a usual time signature, returns a midi time signature.
#
#     The only change is to take the log base 2 of the denominator.
#     """
#     numer, denom = time_sig
#     denom = int(math.log(denom, 2))
#     return numer, denom


def return_track_name_base(midi_fname, abbr=True):
    """Returns an abbreviated version of the file name to be used to name
    the tracks.
    """
    basename = os.path.basename(midi_fname).replace(".mid", "")
    if not abbr:
        return basename
    chars = []
    for i in range(len(basename) - 1, 0, -1):
        char = basename[i]
        if not char.isdigit() and char != "_":
            break
        chars.insert(0, char)

    if chars and chars[0] == "_":
        chars.pop(0)

    bits = basename[: i + 1].split("_")
    for bit in reversed(bits):
        chars.insert(0, bit[0])
    out = "".join(chars)

    return out


def _build_track_dict(er, score_num_voices):
    def _get_track_number(voice_i, choir_i):
        if er.voices_separate_tracks and not er.choirs_separate_tracks:
            return voice_i + offset
        if er.choirs_separate_tracks and not er.voices_separate_tracks:
            return choir_i + offset
        if er.voices_separate_tracks and er.choirs_separate_tracks:
            return voice_i * er.num_choir_programs + choir_i + offset
        return 0 + offset

    if er.voices_separate_tracks and not er.choirs_separate_tracks:
        num_tracks = score_num_voices
    elif er.choirs_separate_tracks and not er.voices_separate_tracks:
        num_tracks = er.num_choir_programs
    elif er.voices_separate_tracks and er.choirs_separate_tracks:
        num_tracks = score_num_voices * er.num_choir_programs
    else:
        num_tracks = 1

    er.track_dict = {}

    existing_voices_offset = 0

    if er.existing_voices:
        if er.existing_voices_erase_choirs:
            existing_voices_choirs = [
                0,
            ]
            for voice_i in range(er.existing_score.num_voices):
                for choir_i in existing_voices_choirs:
                    er.track_dict[
                        (voice_i + 1 + score_num_voices, choir_i)
                    ] = existing_voices_offset
                    existing_voices_offset += 1

        else:
            raise NotImplementedError(
                "Among other things, I need to remove "
                "'gaps' from the existing choirs (e.g., "
                "where choirs 0, 1, and 3, but not 2, "
                "are used)"
            )
            # existing_voices_choirs = set()
            # for voice in er.existing_score:
            #     for note_obj in voice:
            #         existing_voices_choirs.add(note_obj.choir)

    # we start from 1 for track "0", the "meta-track" with tempo changes etc.
    offset = 1 + existing_voices_offset

    for voice_i in range(score_num_voices):
        for choir_i in range(er.num_choir_programs):
            er.track_dict[(voice_i, choir_i)] = _get_track_number(
                voice_i, choir_i
            )

    return num_tracks, existing_voices_offset


def add_note_and_pitch_bend(
    mido_track,
    pitch_bend_tuple,
    note,
    channel,
    pitch_bend_time=None,
):
    if 0 <= pitch_bend_tuple[MIDI_NUM] <= 127:
        mido_track.append(
            mido.Message(
                "pitchwheel",
                channel=channel,
                pitch=pitch_bend_tuple[PITCH_BEND],
                time=pitch_bend_time
                if pitch_bend_time is not None
                else note.onset,
            )
        )
        add_note(
            mido_track,
            note,
            pitch=pitch_bend_tuple[MIDI_NUM],
            channel=channel,
        )


def humanize(er, note=None, tuning=None):
    # Takes *either* note or tuning as kwarg and returns a humanized version
    #   thereof... I should probably refactor!
    def _get_value(humanize_amount):
        return random.random() * (humanize_amount) * 2 + 1 - humanize_amount

    if note is not None:
        new_note = note.copy()
        new_note.onset = max(0, note.onset - 1 + _get_value(er.humanize_onset))
        new_note.dur = note.dur - 1 + _get_value(er.humanize_dur)
        new_note.velocity = round(
            note.velocity * _get_value(er.humanize_velocity)
        )
        return new_note
    tuning = round(
        tuning
        - er_tuning.SIZE_OF_SEMITONE
        + _get_value(er.humanize_tuning) * er_tuning.SIZE_OF_SEMITONE
    )
    return tuning


def add_er_voice(er, voice_i, voice, mf, force_choir=None):
    """Adds a Voice object to the midi file object."""
    empty = True
    for note in voice:
        if force_choir is not None:
            choir_i = force_choir
        else:
            choir_i = note.choir
        choir_program_i = er_choirs.get_choir_prog(
            er.choirs, choir_i, note.pitch
        )
        # I used to add 1 because meta track is track 0 but now I've moved that
        # operation into the construction of er.track_dict above
        track_i = er.track_dict[(voice_i, choir_program_i)]
        if er.logic_type_pitch_bend and er.tet != 12:
            channel = er.note_counter[track_i] % er.num_channels_pitch_bend_loop
            note_count = er.note_counter[track_i]
            er.note_counter[track_i] += 1
        else:
            channel = choir_program_i if er.choirs_separate_channels else 0
        if note.finetune != 0:
            raise NotImplementedError("note.finetune not yet implemented")
        if er.humanize:
            note = humanize(er, note=note)
        if er.tet == 12:
            if 0 <= note.pitch <= 127:
                add_note(mf.tracks[track_i], note)
                empty = False
            else:
                raise ValueError(
                    f"Note pitch {note.pitch} is not in range "
                    "[0-127]; this is probably a bug in this script"
                )
            continue

        midi_num, pitch_bend = er.pitch_bend_tuple_dict[note.pitch]
        if er.humanize:
            pitch_bend = humanize(
                er,
                tuning=pitch_bend,
            )
        if not er.logic_type_pitch_bend or er.tet == 12:
            # er.tet == 12 seems to be an unnecessary condition here!
            add_note_and_pitch_bend(
                mf.tracks[track_i],
                (midi_num, pitch_bend),
                note,
                channel,
                # note.finetune, # what is this? It seems to be unimplemented
            )
            empty = False
        else:
            prev_time_on_channel = er.pitch_bend_time_dict[track_i][
                note_count % er.num_channels_pitch_bend_loop
            ]
            er.pitch_bend_time_dict[track_i][
                note_count % er.num_channels_pitch_bend_loop
            ] = note.onset
            if prev_time_on_channel == 0:
                pitch_bend_time = 0
            else:
                pitch_bend_time = (
                    prev_time_on_channel
                    + er.pitch_bend_time_prop
                    * (note.onset - prev_time_on_channel)
                )
            add_note_and_pitch_bend(
                mf.tracks[track_i],
                (midi_num, pitch_bend),
                note,
                channel,
                pitch_bend_time=pitch_bend_time,
            )
            empty = False
    return empty


def write_track_names(settings_obj, mf, abbr_track_names=True):
    """Writes track names to the midi file object."""

    def _add_track_name(track_i, track_name):
        mf.tracks[track_i].append(
            mido.MetaMessage("track_name", name=track_name, time=0)
        )

    midi_fname = settings_obj.output_path
    track_name_base = return_track_name_base(midi_fname, abbr=abbr_track_names)

    # Add meta track
    _add_track_name(0, os.path.splitext(os.path.basename(midi_fname))[0])

    if isinstance(settings_obj, er_midi_settings.MidiSettings):
        for track_i in range(settings_obj.num_tracks):
            track_name = track_name_base + f"_voice{track_i + 1}"
            _add_track_name(track_i + 1, track_name)
        return

    for track_i in range(settings_obj.num_existing_tracks):
        track_name = track_name_base + f"_existing_voice{track_i + 1}"
        _add_track_name(track_i + 1, track_name)

    if (
        settings_obj.voices_separate_tracks
        and not settings_obj.choirs_separate_tracks
    ):
        for track_i in range(settings_obj.num_new_tracks):
            track_name = track_name_base + f"_voice{track_i + 1}"
            _add_track_name(
                track_i + settings_obj.num_existing_tracks + 1, track_name
            )
    elif (
        settings_obj.choirs_separate_tracks
        and not settings_obj.voices_separate_tracks
    ):
        for track_i in range(settings_obj.num_new_tracks):
            track_name = track_name_base + f"_choir{track_i + 1}"
            _add_track_name(
                track_i + settings_obj.num_existing_tracks + 1, track_name
            )
    elif (
        settings_obj.voices_separate_tracks
        and settings_obj.choirs_separate_tracks
    ):
        for track_i in range(settings_obj.num_new_tracks):
            voice_i = track_i // settings_obj.num_choirs
            choir_i = track_i % settings_obj.num_choirs
            track_name = track_name_base + (
                f"_voice{voice_i + 1}_choir{choir_i + 1}"
            )
            _add_track_name(
                track_i + settings_obj.num_existing_tracks + 1, track_name
            )
    else:
        _add_track_name(1, track_name_base + "_all")


def write_program_changes(er, mf, time=0):
    """Writes program changes to the midi file object."""
    for choir_i in range(er.num_choir_programs):
        program = er.get(choir_i, "choir_programs")
        for voice_i in range(er.num_voices):
            track_i = er.track_dict[(voice_i, choir_i)]
            track = mf.tracks[track_i]
            if not er.logic_type_pitch_bend or er.tet == 12:
                channel = choir_i if er.choirs_separate_channels else 0
                track.append(
                    mido.Message(
                        "program_change",
                        channel=channel,
                        program=program,
                        time=time,
                    )
                )
            else:
                for channel in range(er.num_channels_pitch_bend_loop):
                    track.append(
                        mido.Message(
                            "program_change",
                            channel=channel,
                            program=program,
                            time=time,
                        )
                    )


def write_tempi(er, mf, total_len):
    tempo_i = 0
    time = 0
    while time < total_len:
        if er.tempo:
            tempo = er.get(tempo_i, "tempo")
        else:
            # ideally I should adapt this to preprocessing
            tempo = random.randrange(*er.tempo_bounds)
        mf.tracks[META_TRACK].append(
            mido.MetaMessage(
                "set_tempo", tempo=mido.bpm2tempo(tempo), time=time
            )
        )
        if not er.tempo_len:
            break
        time += er.get(tempo_i, "tempo_len")
        tempo_i += 1


def init_midi(er, super_pattern):

    # LONGTERM not really crazy about these side-effects
    er.num_new_tracks, er.num_existing_tracks = _build_track_dict(
        er, super_pattern.num_voices
    )
    # When I was using midiutil, ticks_per_quarternote needed to be high enough
    # that no note_on and note_off
    # events ended up on the same tick, because midiutil doesn't sort them
    # properly and throws an error if the note_off comes before the note_on.
    # Not sure if mido has any similar issues but leaving ticks_per_beat at
    # a high value for now.
    mf = mido.MidiFile(ticks_per_beat=3200)
    # Add one for META_TRACK, which will be track 0
    for _ in range(er.num_new_tracks + er.num_existing_tracks + 1):
        mf.add_track()

    return mf


def write_er_midi(
    er,
    super_pattern,
    midi_fname,
    reverse_tracks=True,
    return_mf=False,
    dont_write_empty=True,
):
    """Write a midi file with an ERSettings class.

    Doesn't write the midi file if it contains no notes.

    Returns a boolean indicating whether there are any notes in the midi file.

    If return_mf is True, returns the mido MidiFile object. I added this flag
    for testing purposes.
    """

    if er.logic_type_pitch_bend and er.tet != 12:
        er.note_counter = collections.Counter()
        er.pitch_bend_time_dict = {
            track_i: [0 for i in range(er.num_channels_pitch_bend_loop)]
            for track_i in range(er.num_new_tracks + er.num_existing_tracks)
        }

    mf = init_midi(er, super_pattern)

    write_track_names(er, mf)

    write_tempi(er, mf, er.total_len)

    mf.tracks[META_TRACK].append(
        mido.MetaMessage(
            "time_signature",
            numerator=er.time_sig[0],
            denominator=er.time_sig[1],
            clocks_per_click=CLOCKS_PER_TICK,
        )
    )

    if er.write_program_changes:
        write_program_changes(er, mf)
    # non_empty = False
    empty_voices = []
    for voice_i, voice in enumerate(
        super_pattern.voices
        if not reverse_tracks
        else reversed(super_pattern.voices)
    ):
        empty = add_er_voice(er, voice_i, voice, mf)
        empty_voices.append(empty)
        # if not empty:
        #     non_empty = True
    for existing_voice_i, existing_voice in enumerate(
        super_pattern.existing_voices
        if not reverse_tracks
        else reversed(super_pattern.existing_voices)
    ):
        empty = add_er_voice(
            er,
            existing_voice_i + er.num_voices,
            # I add 1 inside add_er_voice so I don't think adding 1 is necessary
            # here
            # existing_voice_i + er.num_voices + 1,
            existing_voice,
            mf,
            force_choir=0,
        )
        # if not empty:
        #     non_empty = True
        empty_voices.append(empty)

    non_empty = not all(empty_voices)

    if non_empty:
        abs_to_delta_times(mf)
        if dont_write_empty:
            for i in range(len(mf.tracks) - 1, 0, -1):
                if not any(msg.type == "note_on" for msg in mf.tracks[i]):
                    mf.tracks.pop(i)
        if return_mf:
            return mf
        mf.save(filename=midi_fname)
    return non_empty


def write_meta_messages(super_pattern, mf):
    for msg in super_pattern.meta_messages:
        mf.tracks[META_TRACK].append(msg)


def add_note(mido_track, note, pitch=None, channel=None):
    channel = note.choir if channel is None else channel
    pitch = note.pitch if pitch is None else pitch
    mido_track.append(
        mido.Message(
            "note_on",
            channel=channel,
            note=pitch,
            velocity=note.velocity,
            time=note.onset,
        )
    )
    mido_track.append(
        mido.Message(
            "note_off",
            channel=channel,
            note=pitch,
            velocity=note.velocity,
            time=note.onset + note.dur,
        )
    )


def add_track(track_i, track, midi_settings, mf):
    for msg in track.other_messages:
        if msg.type in ("track_name", "end_of_track", "instrument_name"):
            continue
        if msg.type == "program_change":
            mf.tracks[track_i].append(msg)
        else:
            print(f"Message of type {msg.type} not written to file.")

    no_finetuning = all(note.finetune == 0 for note in track)
    # if not no_finetuning:
    #     try:
    #         midi_settings.pitch_bend_tuple_dict
    #     except AttributeError:
    #         midi_settings.pitch_bend_tuple_dict = (
    #             er_tuning.return_pitch_bend_tuple_dict(midi_settings.tet))
    empty = True
    for note in track:
        if midi_settings.tet == 12 and no_finetuning:
            if 0 <= note.pitch <= 127:
                add_note(mf.tracks[track_i], note)
                empty = False
        else:
            channel = (
                midi_settings.note_counter[track_i]
                % midi_settings.num_channels_pitch_bend_loop
            )
            note_count = midi_settings.note_counter[track_i]
            midi_settings.note_counter[track_i] += 1
            midi_num, pitch_bend = midi_settings.pitch_bend_tuple_dict[
                note.pitch
            ]
            if note.finetune:
                midi_num, pitch_bend = er_tuning.finetune_pitch_bend_tuple(
                    (midi_num, pitch_bend), note.finetune
                )
            prev_time_on_channel = midi_settings.pitch_bend_time_dict[track_i][
                note_count % midi_settings.num_channels_pitch_bend_loop
            ]
            midi_settings.pitch_bend_time_dict[track_i][
                note_count % midi_settings.num_channels_pitch_bend_loop
            ] = note.onset
            if prev_time_on_channel == 0:
                pitch_bend_time = 0
            else:
                pitch_bend_time = (
                    prev_time_on_channel
                    + midi_settings.pitch_bend_time_prop
                    * (note.onset - prev_time_on_channel)
                )
            add_note_and_pitch_bend(
                track,
                (midi_num, pitch_bend),
                note,
                channel,
                pitch_bend_time=pitch_bend_time,
            )
            empty = False
    return empty


def write_midi(super_pattern, midi_settings, abbr_track_names=True):
    """Write a midi file, without an associated ERSettings class (e.g.,
    if processing an external midi file).

    Doesn't write the midi file if it contains no notes.

    Returns a boolean indicating whether there are any notes in the midi file.
    """
    midi_fname = midi_settings.output_path
    mf = mido.MidiFile()
    for _ in range(midi_settings.num_tracks + 1):
        mf.add_track()

    write_track_names(midi_settings, mf, abbr_track_names=abbr_track_names)

    write_meta_messages(super_pattern, mf)
    non_empty = False
    for track_i, track in enumerate(super_pattern.voices):
        empty = add_track(track_i, track, midi_settings, mf)
        if not empty:
            non_empty = True

    if non_empty:
        abs_to_delta_times(mf, skip=(META_TRACK,))
        mf.save(filename=midi_fname)
    return non_empty


def _pitch_bend_handler(pitch_bend_dict, track_i, msg):
    pitch_bend_dict[track_i][msg.channel] = msg.pitch


def _note_on_handler(
    note_on_dict, pitch_bend_dict, inverse_pb_tup_dict, track_i, msg, tet=12
):

    channel = msg.channel
    midinum = msg.note

    if tet != 12:
        pitch_bend = pitch_bend_dict[track_i][channel]
        pitch = inverse_pb_tup_dict[(midinum, pitch_bend)]

    else:
        pitch = midinum

    note_on_dict[track_i][channel][midinum] = (msg, pitch)


def _note_off_handler(
    note_on_dict, track_i, msg, ticks_per_beat, max_denominator=8192
):

    channel = msg.channel
    midinum = msg.note
    tick_release = msg.time

    note_on_msg, pitch = note_on_dict[track_i][channel][midinum]
    velocity = note_on_msg.velocity
    tick_onset = note_on_msg.time

    tick_dur = tick_release - tick_onset
    onset = fractions.Fraction(tick_onset, ticks_per_beat).limit_denominator(
        max_denominator=max_denominator
    )
    dur = fractions.Fraction(tick_dur, ticks_per_beat).limit_denominator(
        max_denominator=max_denominator
    )

    note_object = er_classes.note.Note(
        pitch, onset, dur, velocity=velocity, choir=channel
    )

    return note_object


class AbsoluteMidiMsg(mido.Message):
    """A child class of the Message class from the mido library. The only
    change is that the time is specified in absolute ticks.

    Call with AbsoluteMidiMsg(msg, tick_time) where "msg" is a mido Message
    and tick_time is the time in ticks.

    Use with caution since the mido methods may rely on relative tick_times.
    """

    # def __init__(self, msg, tick_time):
    #     self_vars = vars(self)
    #     msg_vars = vars(msg)
    #     for msg_attribute, value in msg_vars.items():
    #         self_vars[msg_attribute] = value
    #     self.time = tick_time

    def __init__(self, msg, tick_time):
        super().__init__(msg.type)
        for msg_attribute, value in vars(msg).items():
            if msg_attribute == "type":
                continue
            setattr(self, msg_attribute, value)
        self.time = tick_time

    # def __str__(self):
    #     return (f"type: {self.type:<20} time: {float(self.time):>10}")
    #
    # def __repr__(self):
    #     return (f"type: {self.type}; time: {float(self.time)}")


class AbsoluteMetaMidiMsg(mido.MetaMessage):
    """A child class of the MetaMessage class from the mido library. The only
    change is that the time is specified in absolute ticks.

    Call with AbsoluteMetaMidiMsg(msg, tick_time) where "msg" is a mido
    MetaMessage and tick_time is the time in ticks.

    Use with caution since the mido methods may rely on relative tick_times.
    """

    def __init__(self, msg, tick_time):
        super().__init__(msg.type)
        for msg_attribute, value in vars(msg).items():
            if msg_attribute == "type":
                continue
            setattr(self, msg_attribute, value)
        self.time = tick_time


def _return_sorted_midi_tracks(in_mid):
    def _sorter_string(msg):
        if msg.type == "pitchwheel":
            return "aaaa"
        return msg.type

    out = []
    for track in in_mid.tracks:
        out.append([])
        tick_time = 0
        for msg in track:
            tick_time += msg.time
            if isinstance(msg, mido.midifiles.meta.MetaMessage):
                out[-1].append(AbsoluteMetaMidiMsg(msg, tick_time))
            else:
                out[-1].append(AbsoluteMidiMsg(msg, tick_time))
        out[-1].sort(key=_sorter_string)
        out[-1].sort(key=lambda msg: msg.time)

    return out


def read_midi_to_internal_data(
    in_midi_fname,
    tet=12,
    first_note_at_0=None,
    time_sig=None,
    track_num_offset=0,
    max_denominator=8192,
):

    in_mid = mido.MidiFile(in_midi_fname)
    num_tracks = len(in_mid.tracks)
    if num_tracks == 1:
        warnings.warn(
            "Midi files of just one track exported from Logic "
            "don't put meta messages on a separate track. Support "
            "for these is not yet implemented and there is likely to "
            "be a crash very soon..."
        )

    ticks_per_beat = in_mid.ticks_per_beat
    # # I am leaving this unused variable here because I have the feeling
    # #   I may want to implement it at some point
    # tick_offset = offset * ticks_per_beat  # pylint: disable=unused-variable

    if max_denominator == 0:
        max_denominator = 8192

    internal_data = er_classes.Score(
        tet=tet, num_voices=num_tracks - 1, time_sig=time_sig
    )
    if track_num_offset:
        for voice in internal_data.voices:
            voice.voice_i += track_num_offset

    # Sorting the tracks avoids orphan note or pitchwheel events.
    sorted_tracks = _return_sorted_midi_tracks(in_mid)

    pitch_bend_tuple_dict = er_tuning.return_pitch_bend_tuple_dict(tet)

    inverse_pb_tup_dict = {}
    for pitch, pb_tup in pitch_bend_tuple_dict.items():
        inverse_pb_tup_dict[pb_tup] = pitch

    pitch_bend_dict = {
        i: {j: {} for j in range(NUM_CHANNELS)} for i in range(num_tracks)
    }
    note_on_dict = {
        i: {j: {} for j in range(NUM_CHANNELS)} for i in range(num_tracks)
    }

    for track_i, track in enumerate(sorted_tracks):
        for msg in track:
            if msg.type == "pitchwheel":
                _pitch_bend_handler(pitch_bend_dict, track_i, msg)
            elif msg.type == "note_on" and msg.velocity > 0:
                _note_on_handler(
                    note_on_dict,
                    pitch_bend_dict,
                    inverse_pb_tup_dict,
                    track_i,
                    msg,
                    tet=tet,
                )
            elif msg.type == "note_off" or (
                msg.type == "note_on" and msg.velocity == 0
            ):
                note_object = _note_off_handler(
                    note_on_dict,
                    track_i,
                    msg,
                    ticks_per_beat,
                    max_denominator=max_denominator,
                )
                internal_data.add_note(track_i - 1, note_object)
            else:
                msg.time = fractions.Fraction(msg.time, ticks_per_beat)
                if track_i == 0:
                    internal_data.add_meta_message(msg)
                else:
                    internal_data.add_other_message(track_i - 1, msg)
        # if track_i != 0:
        #     internal_data.voices[track_i - 1].update_sort()

    internal_data.remove_empty_voices()

    if first_note_at_0 is False:
        return internal_data

    # first_onset = internal_data.total_dur
    # for voice in internal_data.voices:
    #     first_onset_in_voice = min(voice.data.keys())
    #     if first_onset_in_voice < first_onset:
    #         first_onset = first_onset_in_voice
    first_onset, _ = internal_data.first_onset_and_notes

    # If the first onset is smaller than min_onset_to_adjust, don't
    # displace the score.
    min_onset_to_adjust = 4
    if first_note_at_0 is None and first_onset < min_onset_to_adjust:
        return internal_data

    if first_onset > 0:
        internal_data.onsets_adjusted_by = -first_onset
        internal_data.displace_passage(-first_onset)

    return internal_data


class Breaker:
    """Used to break the midi playback thread."""

    def __init__(self):
        self.break_ = False
        self.on_count = 0

    def reset(self):
        """Call to interrupt playback."""
        self.break_ = True
        while self.on_count > 0:
            pass
        self.break_ = False


def all_notes_off(output):
    """For whatever reason, mido's "panic" and "reset" functions don't
    seem to work with Logic. Use this instead.
    """
    for channel in range(16):
        for pitch in range(1, 128):
            output.send(mido.Message("note_off", note=pitch, channel=channel))


def _playback_mid(mid, breaker, output):
    # LONGTERM is breaker a good solution?
    breaker.on_count += 1
    for message in mid.play(meta_messages=True):
        if breaker.break_:
            breaker.on_count -= 1
            return
        if isinstance(message, mido.Message):
            output.send(message)
    breaker.on_count -= 1


def playback(in_midi_fname, breaker, multi_output=False):
    in_mid = mido.MidiFile(in_midi_fname)
    num_tracks = len(in_mid.tracks)
    if not multi_output or num_tracks == 1:
        output = mido.open_output(  # pylint: disable=no-member
            name=str(0), virtual=True, autoreset=True
        )
        _playback_mid(in_mid, breaker, output)
        all_notes_off(output)
    # The following code might be useful with a DAW that allows
    # assigning different midi ports to different tracks. Unfortunately,
    # Logic doesn't do so.
    else:
        divided_mid = []
        breakers = []
        output_dict = []
        for track_i in range(1, num_tracks):
            out_mid = mido.MidiFile()
            out_mid.tracks.append(in_mid.tracks[0])
            out_mid.tracks.append(in_mid.tracks[track_i])
            divided_mid.append(out_mid)
            breakers.append(breaker)
            output = mido.open_output(  # pylint: disable=no-member
                name=str(track_i), virtual=True
            )
            output_dict.append(output)

        pool = ThreadPool(num_tracks - 1)
        pool.starmap(_playback_mid, zip(divided_mid, breakers, output_dict))
        pool.close()
        pool.join()


if __name__ == "__main__":
    pass
