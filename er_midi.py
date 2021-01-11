"""Midi writing and reading functions for efficient_rhythms2.py
"""

import collections
import fractions
import math
import os
import random
import warnings
from multiprocessing.dummy import Pool as ThreadPool

import midiutil
import mido
import pygame

import er_choirs
import er_midi_settings
import er_notes
import er_tuning

# midi macros
META_TRACK = 0
CLOCKS_PER_TICK = 24
DEFAULT_CHANNEL = 0
DEFAULT_TRACK = 0
DEFAULT_VELOCITY = er_notes.DEFAULT_VELOCITY
NUM_CHANNELS = 16

# pitch_bend_tuple macros
MIDI_NUM = 0
PITCH_BEND = 1


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
            attack_time = note.attack_time
            if attack_time > rhythm_len:
                break
            rhythm[attack_time] = note.dur
        max_attack = max(rhythm)
        min_attack = min(rhythm)
        if er.overlap:
            overlap = min_attack - (
                max_attack + rhythm[max_attack] - rhythm_len
            )
        else:
            overlap = max_attack + rhythm[max_attack] - rhythm_len
        if overlap > 0:
            rhythm[max_attack] -= overlap
        rhythms.append(rhythm)

    return rhythms


def get_scales_and_chords_from_midi(midif, tet=12, time_sig=4):
    """Infer scales, chords, and roots from a midi file.

    Expects a midi file formatted as follows:
    1) Time signature is 4, although this can be changed with
    "time_sig" (needs to be an integer, however, for now at least)
    2) Contains two tracks, where each measure contains a complete pcset
       (i.e., as a chord of whole notes)
            A) track one has scales
            B) track two has chords

    Roots are inferred from the lowest pitch of each chord.

    Returns:
        A tuple of scales, chords, and roots (as pcsets).
    """

    score = read_midi_to_internal_data(midif, tet=tet)
    scales = [[]]
    chords = [[]]
    roots = []

    for i, pcset_type, pcsets in ((0, "scales", scales), (1, "chords", chords)):
        if pcset_type == "chords":
            lowest_pitch = tet * 100
        for note in score.voices[i]:
            attack = note.attack_time
            pitch = note.pitch
            if round(attack / time_sig) > len(pcsets) - 1:
                pcsets.append([])
                if pcset_type == "chords":
                    roots.append(lowest_pitch % tet)
                    lowest_pitch = tet * 100
            if pcset_type == "chords":
                if pitch < lowest_pitch:
                    lowest_pitch = pitch
            if pitch % tet not in pcsets[-1]:
                pcsets[-1].append(pitch % tet)
        if pcset_type == "chords":
            roots.append(lowest_pitch % tet)

    for i, root in enumerate(roots):
        scales[i] = [(pitch - root) % tet for pitch in scales[i]]
        scales[i].sort()
        chords[i] = [(pitch - root) % tet for pitch in chords[i]]

    return (scales, chords, roots)


def init_and_return_midi_player(tet, shell=False):
    """Selects the midi player.

    If shell is false, plays midi to virtual midi port for use with a DAW such
    as Logic.

    If shell is True, then the midi player is either pygame or fluidsynth. If
    tet == 12, selects pygame as midi player and initializes it. Else
    selects fluidsynth. Returns name of midi player.
    """

    if shell:
        if tet != 12:
            return "fluidsynth"

        pygame.mixer.init()
        return "pygame"
    raise NotImplementedError  # INTERNET_TODO
    return "self"  # pylint: disable=unreachable


def get_midi_time_sig(time_sig):
    """Takes a usual time signature, returns a midi time signature.

    The only change is to take the log base 2 of the denominator.
    """
    numer, denom = time_sig
    denom = int(math.log(denom, 2))
    return numer, denom


def _return_track_name_base(midi_fname, abbr=True):
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
            return voice_i + existing_voices_offset
        if er.choirs_separate_tracks and not er.voices_separate_tracks:
            return choir_i + existing_voices_offset
        if er.voices_separate_tracks and er.choirs_separate_tracks:
            return (
                voice_i * er.num_choir_programs
                + choir_i
                + existing_voices_offset
            )
        return 0 + existing_voices_offset

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

    for voice_i in range(score_num_voices):
        for choir_i in range(er.num_choir_programs):
            er.track_dict[(voice_i, choir_i)] = _get_track_number(
                voice_i, choir_i
            )

    return num_tracks, existing_voices_offset


def add_note_and_pitch_bend(
    mf,
    pitch_bend_tuple,
    time,
    dur,
    track=DEFAULT_TRACK,
    channel=DEFAULT_CHANNEL,
    velocity=DEFAULT_VELOCITY,
):
    """Adds simultaneous note and pitchwheel event."""
    mf.addPitchWheelEvent(track, channel, time, pitch_bend_tuple[PITCH_BEND])
    mf.addNote(track, channel, pitch_bend_tuple[MIDI_NUM], time, dur, velocity)


def add_note_and_pitch_bend_separately(
    mf,
    pitch_bend_tuple,
    note_time,
    note_dur,
    pitch_bend_time,
    track=DEFAULT_TRACK,
    channel=DEFAULT_CHANNEL,
    velocity=DEFAULT_VELOCITY,
):
    """Adds a note and pitchwheel events at independent times.
    """
    mf.addPitchWheelEvent(
        track, channel, pitch_bend_time, pitch_bend_tuple[PITCH_BEND]
    )
    mf.addNote(
        track,
        channel,
        pitch_bend_tuple[MIDI_NUM],
        note_time,
        note_dur,
        velocity,
    )


def humanize(er, attack, dur, velocity, tuning=None):
    def _get_value(humanize_amount):
        return random.random() * (humanize_amount) * 2 + 1 - humanize_amount

    attack = max(0, attack - 1 + _get_value(er.humanize_attack))
    dur = dur - 1 + _get_value(er.humanize_dur)
    velocity = round(velocity * _get_value(er.humanize_velocity))
    if tuning is None:
        return attack, dur, velocity, 0
    tuning = round(
        tuning
        - er_tuning.SIZE_OF_SEMITONE
        + _get_value(er.humanize_tuning) * er_tuning.SIZE_OF_SEMITONE
    )
    return attack, dur, velocity, tuning


def add_er_voice(er, voice_i, voice, mf, force_choir=None):
    """Adds a Voice object to the midi file object.
    """
    for note in voice:
        attack_time = note.attack_time
        pitch = note.pitch
        dur = note.dur
        if force_choir is not None:
            choir_i = force_choir
        else:
            choir_i = note.choir
        choir_program_i = er_choirs.get_choir_prog(er.choirs, choir_i, pitch)
        track = er.track_dict[(voice_i, choir_program_i)]
        if er.logic_type_pitch_bend and er.tet != 12:
            channel = er.note_counter[track] % er.num_channels_pitch_bend_loop
            note_count = er.note_counter[track]
            er.note_counter[track] += 1
        else:
            channel = choir_program_i if er.choirs_separate_channels else 0
        velocity = note.velocity
        if note.finetune != 0:
            raise NotImplementedError("note.finetune not yet implemented")
        if er.tet == 12:
            if er.humanize:
                attack_time, dur, velocity, _ = humanize(
                    er, attack_time, dur, velocity
                )
            mf.addNote(track, channel, pitch, attack_time, dur, velocity)
            continue

        midi_num, pitch_bend = er.pitch_bend_tuple_dict[pitch]
        if er.humanize:
            attack_time, dur, velocity, pitch_bend = humanize(
                er, attack_time, dur, velocity, tuning=pitch_bend,
            )
        pitch_bend_tuple = (midi_num, pitch_bend)
        if not er.logic_type_pitch_bend or er.tet == 12:
            # er.tet == 12 seems to be an unnecessary condition here!
            add_note_and_pitch_bend(
                mf,
                pitch_bend_tuple,
                attack_time,
                dur,
                track,
                channel,
                velocity,
                # note.finetune, # what is this? It seems to be unimplemented
            )
        else:
            prev_time_on_channel = er.pitch_bend_time_dict[track][
                note_count % er.num_channels_pitch_bend_loop
            ]
            er.pitch_bend_time_dict[track][
                note_count % er.num_channels_pitch_bend_loop
            ] = attack_time
            if prev_time_on_channel == 0:
                pitch_bend_time = 0
            else:
                pitch_bend_time = (
                    prev_time_on_channel
                    + er.pitch_bend_time_prop
                    * (attack_time - prev_time_on_channel)
                )
            add_note_and_pitch_bend_separately(
                mf,
                pitch_bend_tuple,
                attack_time,
                dur,
                pitch_bend_time,
                track,
                channel,
                velocity,
            )


def write_track_names(
    settings_obj, mf, midi_fname, zero_origin=False, abbr_track_names=True
):
    """Writes track names to the midi file object."""

    def _add_track_name(track_i, track_name):
        time = 0
        mf.addTrackName(track_i, time, track_name)

    track_name_base = _return_track_name_base(midi_fname, abbr=abbr_track_names)
    adjust = 0 if zero_origin else 1

    if isinstance(settings_obj, er_midi_settings.MidiSettings):
        for track_i in range(settings_obj.num_tracks):
            track_name = track_name_base + f"_voice{track_i + adjust}"
            _add_track_name(track_i, track_name)
        return

    for track_i in range(settings_obj.num_existing_tracks):
        track_name = track_name_base + f"_existing_voice{track_i + adjust}"
        _add_track_name(track_i, track_name)

    if (
        settings_obj.voices_separate_tracks
        and not settings_obj.choirs_separate_tracks
    ):
        for track_i in range(settings_obj.num_new_tracks):
            track_name = track_name_base + f"_voice{track_i + adjust}"
            _add_track_name(
                track_i + settings_obj.num_existing_tracks, track_name
            )
    elif (
        settings_obj.choirs_separate_tracks
        and not settings_obj.voices_separate_tracks
    ):
        for track_i in range(settings_obj.num_new_tracks):
            track_name = track_name_base + f"_choir{track_i + adjust}"
            _add_track_name(
                track_i + settings_obj.num_existing_tracks, track_name
            )
    elif (
        settings_obj.voices_separate_tracks
        and settings_obj.choirs_separate_tracks
    ):
        for track_i in range(settings_obj.num_new_tracks):
            voice_i = track_i // settings_obj.num_choirs
            choir_i = track_i % settings_obj.num_choirs
            track_name = track_name_base + (
                f"_voice{voice_i + adjust}_choir{choir_i + adjust}"
            )
            _add_track_name(
                track_i + settings_obj.num_existing_tracks, track_name
            )


def write_program_changes(er, mf, time=0):
    """Writes program changes to the midi file object."""
    for choir_i in range(er.num_choir_programs):
        program = er.get(choir_i, "choir_programs")
        for voice_i in range(er.num_voices):
            track = er.track_dict[(voice_i, choir_i)]
            if not er.logic_type_pitch_bend or er.tet == 12:
                channel = choir_i if er.choirs_separate_channels else 0
                mf.addProgramChange(track, channel, time, program)
            else:
                for channel in range(er.num_channels_pitch_bend_loop):
                    mf.addProgramChange(track, channel, time, program)


def write_tempi(er, mf, total_len):
    if er.tempo_len[0] == 0:
        mf.addTempo(META_TRACK, 0, er.tempo[0])
        return
    tempo_i = 0
    time = 0
    while time < total_len:
        if er.tempo:
            tempo = er.get(tempo_i, "tempo")
        else:
            tempo = random.randrange(*er.tempo_bounds)
        mf.addTempo(META_TRACK, time, tempo)
        time += er.get(tempo_i, "tempo_len")
        tempo_i += 1


def write_er_midi(er, super_pattern, midi_fname, reverse_tracks=True):
    """Write a midi file with an ERSettings class.
    """
    time = 0

    er.num_new_tracks, er.num_existing_tracks = _build_track_dict(
        er, super_pattern.num_voices
    )

    if er.logic_type_pitch_bend and er.tet != 12:
        er.note_counter = collections.Counter()
        er.pitch_bend_time_dict = {
            track_i: [0 for i in range(er.num_channels_pitch_bend_loop)]
            for track_i in range(er.num_new_tracks + er.num_existing_tracks)
        }

    mf = midiutil.MidiFile.MIDIFile(
        er.num_new_tracks + er.num_existing_tracks,
        adjust_origin=True,
        # ticks_per_quarternote needs to be high enough that no note_on and note_off
        # events will end up on the same tick, because midiutil doesn't sort them
        # properly and throws an error if the note_off comes before the note_on
        # LONGTERM infer ticks_per_quarternote intelligently from min_dur?
        ticks_per_quarternote=3200,
    )

    write_track_names(er, mf, midi_fname)

    write_tempi(er, mf, er.total_len)

    numerator, denominator = get_midi_time_sig(er.time_sig)
    mf.addTimeSignature(
        META_TRACK, time, numerator, denominator, CLOCKS_PER_TICK
    )

    if er.write_program_changes:
        write_program_changes(er, mf)

    if reverse_tracks:
        for voice_i, voice in enumerate(reversed(super_pattern.voices)):
            add_er_voice(er, voice_i, voice, mf)
        for existing_voice_i, existing_voice in enumerate(
            reversed(super_pattern.existing_voices)
        ):
            add_er_voice(
                er,
                existing_voice_i + er.num_voices + 1,
                existing_voice,
                mf,
                force_choir=0,
            )
    else:
        for voice_i, voice in enumerate(super_pattern.voices):
            add_er_voice(er, voice_i, voice, mf)
        for existing_voice_i, existing_voice in enumerate(
            super_pattern.existing_voices
        ):
            add_er_voice(
                er,
                existing_voice_i + er.num_voices + 1,
                existing_voice,
                mf,
                force_choir=0,
            )

    with open(midi_fname, "wb") as outf:
        try:
            mf.writeFile(outf)
        except:
            breakpoint()


def write_meta_messages(super_pattern, mf):
    for msg in super_pattern.meta_messages:
        if msg.type == "set_tempo":
            mf.addTempo(0, msg.time, mido.tempo2bpm(msg.tempo))
        elif msg.type == "time_signature":
            mf.addTimeSignature(
                0,
                msg.time,
                msg.numerator,
                msg.denominator,
                msg.clocks_per_click,
            )
        elif msg.type in (
            "end_of_track",
            "key_signature",
            "smpte_offset",
            "marker",
            "copyright",
        ):
            continue
        else:
            print(f"Message of type {msg.type} not written to file.")


def add_track(track_i, track, midi_settings, mf):
    for msg in track.other_messages:
        if msg.type in ("track_name", "end_of_track", "instrument_name"):
            continue
        if msg.type == "program_change":
            mf.addProgramChange(track_i, msg.channel, msg.time, msg.program)
        else:
            print(f"Message of type {msg.type} not written to file.")

    no_finetuning = all([note.finetune == 0 for note in track])
    # if not no_finetuning:
    #     try:
    #         midi_settings.pitch_bend_tuple_dict
    #     except AttributeError:
    #         midi_settings.pitch_bend_tuple_dict = (
    #             er_tuning.return_pitch_bend_tuple_dict(midi_settings.tet))

    for note in track:
        if midi_settings.tet == 12 and no_finetuning:
            mf.addNote(
                track_i,
                note.choir,
                note.pitch,
                note.attack_time,
                note.dur,
                note.velocity,
            )
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
            ] = note.attack_time
            if prev_time_on_channel == 0:
                pitch_bend_time = 0
            else:
                pitch_bend_time = (
                    prev_time_on_channel
                    + midi_settings.pitch_bend_time_prop
                    * (note.attack_time - prev_time_on_channel)
                )
            add_note_and_pitch_bend_separately(
                mf,
                (midi_num, pitch_bend),
                note.attack_time,
                note.dur,
                pitch_bend_time,
                track_i,
                channel,
                note.velocity,
            )


def write_midi(super_pattern, midi_fname, midi_settings, abbr_track_names=True):
    """Write a midi file, without an associated ERSettings class (e.g.,
    if processing an external midi file).
    """

    mf = midiutil.MidiFile.MIDIFile(
        midi_settings.num_tracks, adjust_origin=True
    )

    write_track_names(
        midi_settings, mf, midi_fname, abbr_track_names=abbr_track_names
    )

    write_meta_messages(super_pattern, mf)

    for track_i, track in enumerate(super_pattern.voices):
        add_track(track_i, track, midi_settings, mf)

    with open(midi_fname, "wb") as outf:
        mf.writeFile(outf)


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
    tick_attack = note_on_msg.time

    tick_dur = tick_release - tick_attack
    attack = fractions.Fraction(tick_attack, ticks_per_beat).limit_denominator(
        max_denominator=max_denominator
    )
    dur = fractions.Fraction(tick_dur, ticks_per_beat).limit_denominator(
        max_denominator=max_denominator
    )

    note_object = er_notes.Note(
        pitch, attack, dur, velocity=velocity, choir=channel
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

        # out[-1].sort(key=lambda msg: _sorter_string(msg))
        out[-1].sort(key=_sorter_string)
        out[-1].sort(key=lambda msg: msg.time)

    return out


def read_midi_to_internal_data(
    in_midi_fname,
    tet=12,
    first_note_at_0=None,
    time_sig=None,
    offset=0,
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
    # I am leaving this unused variable here because I have the feeling
    #   I may want to implement it at some point
    tick_offset = offset * ticks_per_beat  # pylint: disable=unused-variable

    if max_denominator == 0:
        max_denominator = 8192

    internal_data = er_notes.Score(
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
                internal_data.add_note_object(
                    track_i - 1, note_object, update_sort=False
                )
            else:
                msg.time = fractions.Fraction(msg.time, ticks_per_beat)
                if track_i == 0:
                    internal_data.add_meta_message(msg)
                else:
                    internal_data.add_other_message(track_i - 1, msg)
        if track_i != 0:
            internal_data.voices[track_i - 1].update_sort()

    internal_data.remove_empty_voices()

    if first_note_at_0 is False:
        return internal_data

    first_attack = internal_data.get_total_len()
    for voice in internal_data.voices:
        first_attack_in_voice = min(voice.data.keys())
        if first_attack_in_voice < first_attack:
            first_attack = first_attack_in_voice

    # If the first attack is smaller than min_attack_to_adjust, don't
    # displace the score.
    min_attack_to_adjust = 4
    if first_note_at_0 is None and first_attack < min_attack_to_adjust:
        return internal_data

    if first_attack > 0:
        internal_data.attacks_adjusted_by = -first_attack
        internal_data.displace_passage(-first_attack)

    return internal_data


class Breaker:
    """Used to break the midi playback thread.
    """

    def __init__(self):
        self.break_ = False
        self.on_count = 0

    def reset(self):
        """Call to interrupt playback.
        """
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
