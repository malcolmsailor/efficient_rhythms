import dataclasses
from dataclasses import field as fld
import re
import numbers
import typing
from fractions import Fraction

import numpy as np

# from . import er_type_check

DEFAULT_NUM_HARMONIES = 4

# The user can override MAX_SUPER_PATTERN_LEN
# We use a lower default when script is invoked with --random to make success
# somewhat more likely
MAX_SUPER_PATTERN_LEN = 128
MAX_SUPER_PATTERN_LEN_RANDOM = 64

CATEGORIES = (
    "global",
    "midi",
    "scale_and_chord",
    "tuning",
    "voice_leading",
    "chord_tones",
    "melody",
    "consonance",
    "rhythm",
    "choir",
    "transpose",
    "tempo",
    "shell_only",
    "randomization",
)


# TODO use this type annotation for sequences that can be ndarrays as well
# Note that Seq_or_arr will match strings
# Seq_or_arr = typing.Union[typing.Sequence, np.ndarray]

# TODO setting to give notes different velocities depending on their
#   subdivision

# @er_type_check.enforce_types
@dataclasses.dataclass
class ERSettings:
    """Stores the settings that control the script's behavior.

    Hyperlinked, formatted markdown and HTML versions automatically generated
    from the following  docstring are available in `docs/settings.md` and
    `docs/settings.html`.  For most usage cases it is probably better to consult
    the documentation there.

    The many settings below control the behavior of this script. The recommended
    way of using the script is to store the desired settings as a Python
    dictionary in a file and then pass the file into the script with the
    `--settings` flag. For examples, see the files in the `docs/examples/`
    directory.  For a high-level overview of the script, see
    `docs/general.html`

    Note on "per-voice sequences" and other "looping sequences"
    ===========================================================

    Many arguments below can take "per-voice sequences" as arguments. These are
    sequences (e.g., tuples or lists) that assign a different setting to each
    voice. Importantly, however, it is possible to provide a sequence that is
    shorter than the number of voices. In this case, the sequence will be
    looped through as many times as is necessary. For example,
    if `num_voices == 5`, but `len(pattern_len) == 2`, voices 0, 2, and 4 will
    be assigned the first value in `pattern_len`, while voices 1 and 3 will be
    assigned the second value. (The voices are zero-indexed.)

    There are also a number of arguments that take sequences that, if necessary,
    will be looped through in a similar manner, but where the items of the
    sequence are not applied to voices, but to something else. An example is
    `harmony_len`. I refer to these as "looping sequences".

    Note on specifying pitches and intervals
    ========================================

    For most use cases, it will be most convenient to specify pitch materials
    using strings denoting constants which are provided in `efficient_rhythms/er_constants.py`
    and documented in `docs/constants.md` and `docs/constants.html`. A few
    examples: `"PERFECT_4TH"`, `"C# * OCTAVE4"`, `"F * PHRYGIAN"`, etc.

    Otherwise, pitch materials can be specified either as integers, or as other
    numeric types (e.g., floats). **If you don't care about tuning or
    temperament, just specify all intervals and pitches as integers** (e.g., one
    semitone = `1`, "middle C" = `60`). Otherwise, read on:

    - integers specify equal-tempered intervals. For example, in 12-tet (the
    usual temperament employed in Western music), an interval of `7`
    corresponds to a perfect fifth. How exactly integers function in
    other temperaments depends on the setting `integers_in_12_tet`;
    see its documentation below for details.

    - other numeric types are interpreted as just intervals, and
    then approximated in the specified equal-division-of-the-octave
    temperament (the default being 12). Thus an interval of 1.5 (which
    in tuning theory is more often specified as a ratio of 3:2)
    corresponds to a perfect fifth. If `tet = 12`, this will be approximated
    as 7 semitones (7/12ths of an octave). If `tet = 31`, on the other
    hand, this will be approximated as 18/31sts of an octave.

    "Generic" and "specific" intervals
    ==================================

    In the settings below, I sometimes use the terms "generic" or "specific" in
    reference to intervals. These terms come from academic music theory (e.g.,
    Clough and Myerson 1985).

    A "generic" interval defines an interval with respect to some reference
    scale, by counting the number of scale steps the interval contains.  They
    might also be called "scalar" intervals (using "scalar" in a completely
    different sense from its linear algebra meaning).  "Specific" intervals
    define intervals "absolutely", by simply counting the number of semitones
    the interval comprises, irrespective of any reference scale.

    In typical musical usage, "thirds", "fifths", and the like refer to generic
    intervals: a third is the distance between any pitch in a scale and the
    pitch two steps above or below it. (It would be more practical to call a
    "third" a "second" but, unfortunately, this usage has now been established
    for many centuries!) Depending on the structure of the scale, and the
    location of the interval within it, the exact pitch distance connoted by one
    and the same generic interval may vary. For instance, in the C major scale,
    the third from C to E is 4 semitones, but the third from D to F is 3
    semitones. To distinguish these cases, music theory has developed an armory
    of interval "qualities" like "major", "minor", "diminished", and so on.  A
    generic interval together with a quality, like "minor third", is somewhat
    like a specific interval, but it is not quite the same thing, because there
    can be more than one generic interval + quality that correspond to one
    specific interval. For example, both "minor thirds" and "augmented seconds"
    comprise 3 semitones. (Thus, the mapping from generic intervals with
    qualities to specific intervals is onto but not one-to-one.)

    Keyword args:

        General settings
        ================

        Less often used general settings are under "Miscellaneous settings"
        below.

        seed: int. Seed for random number generation.
        output_path: str. Path for output midi file. If a relative path, will
            be created relative to the current directory, unless the path begins
            with the string "EFFRHY/", in which case "EFFRHY/" will be replaced
            with the directory of the efficient_rhythms script.  If any folder
            in the path does not exist, it will be created.  If the path is a
            directory (ending with `"/"`), a midi file will be created within
            that directory with the same basename as the last settings file, but
            with the extension `.mid`. (If there are no settings files, the
            basename will be `effrhy.mid`.)

            See also `overwrite`.
            Default: "EFFRHY/output_midi/effrhy.mid"
        tet: int. Specifies equal division of the octave.
            Default: 12
        num_voices: int. The number of "voices" (or "parts") to be created.
            If `existing_voices` below is passed, then `num_voices` specifies
            the number of *new* voices to be added, and doesn't include the
            `existing_voices` taken from the provided midi file.
            Default: 3
        num_reps_super_pattern: int. Number of times to repeat the complete
            "super pattern".
            Default: 2
        pattern_len: a number, or a per-voice sequence of numbers. Indicates the
            length of the "basic pattern" in beats. If a single number, all
            voices have the same length; if a sequence, sets the length for each
            voice individually.  If `pattern_len` is 0 or negative, it will be
            assigned the length of the complete harmonic progression (determined
            by `harmony_len` and `num_harmonies`).

            If `cont_rhythms != "none"`, then this argument must consist of
            a single number.
            Default: 0
        truncate_patterns: bool. If True, then repetitions of any values in
            `pattern_len` which are not factors of the maximum value in
            `pattern_len` will be truncated at the maximum value. For example,
            if voice 0 has `pattern_len = 3` and voice 1 has `pattern_len = 5`,
            every second repetition of the pattern in voice 0 will be truncated
            after two beats.
            Default: False
        rhythm_len: a number, or a per-voice sequence of numbers. Indicates the
            length of the rhythmic pattern to be generated. If not passed, then
            will be assigned the value of `pattern_len`. If a single number, all
            voices have the same length; if a sequence, sets the length for each
            voice individually.  The use of `rhythm_len` is to make repeated
            rhythmic patterns that are shorter than `pattern_len`. If
            `rhythm_len` does not divide `pattern_len` evenly (e.g., if
            `rhythm_len == 3` and `pattern_len == 8`), then the final repetition
            of `rhythm_len` will be truncated. Similarly, if `rhythm_len` is
            longer than `pattern_len`, it will be truncated; in this case, one
            may as well not pass any value of `rhythm_len`, since in the absence
            of a value, `rhythm_len` is assigned the value of `pattern_len`.

            If `cont_rhythms != "none"`, then this argument must consist of
            a single number, which must be the same as the value of
            `pattern_len`.
        num_harmonies: int. The number of harmonies in the pattern. If
            not passed, the length of `foot_pcs` will be assigned to this
            setting. If `foot_pcs` is not passed either, will be set to a
            default value of 4.
        harmony_len: a number, or a looping sequence of numbers (see above).
            If a sequence of numbers, the harmonies will cycle through the
            sequence until `num_harmonies` is reached. That is, the first
            harmony will have the length of the first number in the sequence,
            the second harmony of the second, and so on. (Unlike `pattern_len`
            or `rhythm_len`, there is no way of assigning different
            harmony_lengths to different voices.)
            Default: 4
        voice_ranges: a sequence of 2-tuples. Each tuple is of form
            (lowest_note, highest_note). `er_constants.py` provides a number of
            useful values for this purpose. The sequence must be at least
            `num_voices` length. (If it is longer, excess items will be
            ignored.) It is not enforced that the sequence be in ascending order
            but I haven't extensively tested what happens if it is not.  Note
            that if `constrain_voice_leading_to_ranges` is False, than these
            ranges will only be enforced for the initial pattern. See also
            `hard_bounds`.

            For a list of pre-defined constants that can be used with this
            setting, see docs/constants.html. See also the note above on
            specifying pitches and intervals.

            Default: "CONTIGUOUS_OCTAVES * OCTAVE3 * C"



        Scale and chord settings
        ========================

        scales_and_chords_specified_in_midi: string. If passed, specifies a
            midi file in a specific format, described below, from which the
            settings `foot_pcs`, `scales`, and `chords` below should be inferred
            (in which case any explicit values for these settings are ignored).

            The midi file should consist of two tracks. `scales` are inferred
            from the first track, and `chords` and `foot_pcs` are inferred
            from the second track (`foot_pcs` are simply the lowest sounding
            pitch of each chord). Each track should consist entirely of
            simultaneous whole notes (i.e., semibreves) constituting the
            intended scales or chords, respectively. For an example, see
            `docs/examples/scales_and_chords_specified_in_midi_example.mid`.
            Note that the rhythm of the harmonic changes is set through the
            `harmony_len` parameter above.

            You must ensure that chords and scales are consistent (that is,
            that the chords do not contain pitch-classes that do not belong to
            the  scales; i.e., that the scales are supersets of the chords),
            or an `InconsistentChordsAndScalesError` will be raised.
        foot_pcs: sequence of numbers. In this script, we call the main bass
            pitch of each chord its "foot". The main bass pitch is a little like
            the "root" of a chord, except that the main bass pitch doesn't have
            to be the root of a chord (as in the case of inverted chords).
            `foot_pcs` specifies the "foots" of each harmony. These are the
            pitch-classes that will correspond to `0` in each item of
            `scales` and `chords`.

            For example, if `foot_pcs == [2, 4]` and `chords == [[0, 4, 7], [0,
            3, 8]]`, then the actually realized chords will have pitch-classes
            `[2, 6, 9]` and `[4, 7, 0]`, respectively (assuming `tet == 12`).
            (In music-theoretic terms, the chords will be a D major triad
            followed by a first- inversion C major triad.)

            If `foot_pcs` is shorter than `num_harmonies`, it is looped through
            until the necessary length is obtained.

            If not passed, or passed an empty sequence, `num_harmonies` foots
            will be generated randomly.

            Note that if `interval_cycle` below is non-empty, all items in this
            sequence past the first are ignored.

            (See the note above on specifying pitches and intervals.)
        interval_cycle: number, or sequence of numbers. Specifies a foot-pc
            interval cycle beginning on the first pitch-class of `foot_pcs` (or
            on a randomly chosen pitch-class, if `foot_pcs` is not passed).
            For example, if `foot_pcs == [0]`, and
                - `interval_cycle == 3`, the foot pitch-classes will be 0, 3,
                    6...
                - `interval_cycle == [3, -2]`, the foot pitch-classes will be
                    0, 3, 1, 4, 2...
            (See the note above on specifying pitches and intervals.)
        scales: a sequence of sequences of numbers. Each subsequence specifies
            a scale. Scales should always be specified starting from pitch-class
            0; they will then be transposed to the appropriate pitch-classes
            according to the settings `foot_pcs` or `interval_cycle`.

            If `foot_pcs` has fewer items than `scales`, then the excess items
            in `scales` will be ignored.

            If `foot_pcs` has more items than `scales`, then `scales` will be
            looped through.

            For a list of pre-defined constants that can be used with this
            setting, see docs/constants.html. See also the note above on
            specifying pitches and intervals.

            Default: ["DIATONIC_SCALE"]
        chords: a sequence of sequences of numbers. Each subsequence specifies
            a chord. Scales should always be specified starting from pitch-class
            0; they will then be transposed to the appropriate pitch-classes
            according to the settings `foot_pcs` or `interval_cycle`.

            If `foot_pcs` has fewer items than `chords`, then the excess items
            in `chords` will be ignored.

            If `foot_pcs` has more items than `chords`, then `chords` will be
            looped through.

            For a list of pre-defined constants that can be used with this
            setting, see docs/constants.html. See also the note above on
            specifying pitches and intervals.

            Default: ["MAJOR_TRIAD"]

        Midi settings
        =============

        voices_separate_tracks: bool. If True, different "voices" in the score
            are written to separate tracks in the output midi file.
            Default: True
        choirs_separate_tracks: bool. If True, different "choirs" in the score
            are written to separate tracks in the output midi file.
            Default: True
        choirs_separate_channels: bool. If True, different "choirs" in the score
            are assigned to separate channels in the output midi file (up to
            the maximum of 16 channels).
            Default: True
        write_program_changes: bool. If True, General Midi program changes are
            written to the output midi file. Depending on the intended use,
            this may or may not be desired.
            Default: True
        humanize: bool. Whether to apply "humanization" to various parameters
            according to the various "humanize" settings below.
            Default: True
        humanize_onset: float. Randomly varies onset times within +- this
            amount, in quarter notes.
            Default: 0.0
        humanize_dur: float.  Randomly varies duration times within +- this
            amount, in quarter notes.
            Default: 0.0
        humanize_velocity: float between 0 and 1.  Scales velocities
            by 1 +- a random amount between 0 and this amount.
            Default: 0.1
        humanize_tuning: float. Only implemented when `tet != 12`. Randomly
            varies tuning within +- this amount.
            Default: 0.0

        Tuning settings
        ===============

        integers_in_12_tet: bool. If `True`, then any pitch materials (e.g.,
            in `max_interval` or `scales`) that are indicated by integers
            (rather than floats etc.) will be interpreted as 12-tet intervals
            that will be approximated in the given temperament (if `tet != 12`).
            Thus, if True for example, if `tet == 31`, then an interval of `7`
            (7/12ths of an octave, the nearest 12-tet approximation to a just
            fifth) will converted to `18`, the nearest 31-tet approximation to
            7/12ths of an octave.
            Default: False
        logic_type_pitch_bend: bool. If True, turns on a midi-writing scheme
            that I devised in order to make non-12-tet files work in Logic
            Pro. That is, in order to avoide pitch-bend latency problems, as
            well as to avoid audible bends during the release tails of notes,
            the notes (and their associated pitch-bend events) of each voice
            loop through a number of different channels (set by
            `num_channels_pitch_bend_loop`).

            I have not used these midi files with any other DAWs so I don't
            know whether this setting is helpful with e.g., ProTools.
            Default: False
        num_channels_pitch_bend_loop: int. Defines number of channels to loop
            through if `logic_type_pitch_bend` is True.
            Default: 9
        pitch_bend_time_prop: number between 0 and 1. If `logic_type_pitch_bend`
            is True, then this parameter defines how long between the release
            of the last note on a channel and the onset of the next note
            on that same channel the associated pitch-bend message should
            be written. The value should probably be more than half to avoid
            an audible bend during the release of the previous pitch.
            Default: 0.75

        Voice-leading settings
        ======================

        parallel_voice_leading: bool. If `True`, then the voice-leading between
            harmonies is conducted in pure (generic) parallel motion.
            Default: False
        parallel_direction: int. Only has an effect if `parallel_voice_leading`
            is True. Governs the direction of the parallel voice-leading:
                - if positive, the motion is always upwards
                - if negative, the motion is always downwards
                - if 0, then the motion is either upwards or downwards,
                    depending on which is shorter.
            Default: 0
        voice_lead_chord_tones: bool. If True, then chord-tones on each harmony
            are voice-led to chord-tones on the next harmony, and
            non-chord-tones to non-chord-tones. So, if moving from a C major
            chord to an F major chord, the pitch-class C will be mapped to one
            of the pitch-classes (F, A, C), the pitch-class E will be mapped to
            one of the two remaining pitch-classes of the F major chord, and the
            pitch-class G will be mapped to the remaining pitch-class of the F
            major chord. A similar mapping will be made among the non-chord
            tones of the scale.

            Setting this parameter to True will greatly reduce the script's
            ability to find voice-leading solutions (especially in combination
            with `allow_flexible_voice_leading == False`). Note also that it
            will often lead to at least some relatively large voice-leading
            motions.

            Default: False
        preserve_foot_in_bass: string. Controls whether the occurrences
            of the foot in the bass are "preserved" when voice-leading the
            initial pattern to subsequent harmonies. For example, if the first
            two harmonies are C major followed by F major, should a C in the
            bass on the first chord be voice-led to an F in the bass on the
            second chord, preserving the foot, or should it be voice-led to a C
            (which would be more efficient, in the sense of moving a smaller
            interval, a unison, rather than a fourth or fifth).

            Note that if this settings is not "none", otherwise forbidden
            intervals may occur.

            Possible values:
                "lowest": only the lowest sounding occurrences of
                    the foot on each harmony are preserved (so if, e.g.,
                    C2 and C3 both occur, only C2 will
                    be preserved when voice-led to the next chord, while
                    C3 will proceed by efficient voice-leading like all
                    other pitches).
                "all": all occurrences of the foot of each harmony
                    are preserved.
                "none": the foot is voice-led like any other pitch.
            Default: "none"
        extend_bass_range_for_foots: number. If non-zero, permits transposition
            of the foot lower than the normal range of the bass voice, in order
            to maintain the foot as the lowest sounding pitch during a given
            harmony. Specifically, if the lowest sounding occurrences
            of the foot during a given harmony are not the lowest sounding pitch
            during that harmony, then they will be transposed an octave
            downwards, provided that this transposition lies within this
            extended range.
            Default: 0
        constrain_voice_leading_to_ranges: bool. If False, then after the
            initial pattern is complete, the voices may exceed their ranges, if
            the most efficient voice-leading requires it. (For example, if
            the highest pitch of a voice's range is G, but a subsequent
            efficient voice-leading requires G-sharp, the voice will be allowed
            to ascend to G-sharp, rather than enforcing a less-efficient
            voice-leading).
            Default: False
        allow_flexible_voice_leading: bool. If True, then the voice-leading
            (i.e., the mapping of pitches from one harmony to the next) will
            be allowed to change mid-harmony. (So that, for example, the pitch
            C5 might at first be mapped to D5 by the initial voice-leading, but
            after the script reaches an impasse, a new voice-leading will
            be chosen, which might map C5 to B4.) Setting to True will greatly
            expand the script's ability to find voice-leading solutions;
            however, it may tend to destroy the audible sense of "pattern".
            Default: False
        vl_maintain_consonance: bool. If False, then after the initial pattern
            is complete, voice-leadings will not be checked for consonance.
            (See the settings under "Consonance and dissonance settings" below.)
            Default: True
        vl_maintain_limit_intervals: string. Determines when and whether, after
            the initial pattern is complete, voice-leadings will be allowed to
            exceed limit intervals.  (See settings `max_interval`,
            `max_interval_for_non_chord_tones`, `min_interval`,
            `min_interval_for_non_chord_tones`.)

            Possible values:
                "all": limit intervals are always maintained.
                "across_harmonies": limit intervals are maintained when voice-
                    leading from one harmony to another, but not when voice-
                    leading within a single harmony. (Maintaining the limit
                    intervals within a single harmony when a pattern is
                    repeated on that harmony can lead the script to switch
                    to a different voice-leading abruptly for the repetition,
                    which may not be desired.)
                "none": limit intervals are never maintained.
            Default: "across_harmonies"
        vl_maintain_forbidden_intervals: bool. If False, then after the initial
            pattern is complete, voice-leadings will be permitted to contain
            forbidden intervals.  (See `forbidden_interval_classes`,
            `forbidden_interval_modulo`.)
            Default: True
        vl_maintain_prohibit_parallels: bool. If False, then after the initial
            pattern is complete, voice-leadings will be permitted to contain
            prohibited parallel intervals. (See `prohibit_parallels`.)
            Default: True

        Chord-tone settings
        ===================

        Most chord tone settings only have an effect if `chord_tone_selection`
        is `True`. Only `force_chord_tone` applies irrespective of
        `chord_tone_selection`.

        chord_tone_and_foot_disable: bool. If True, disables all chord-tone and
            foot specific behavior. Specifically, disables
            `chord_tone_selection`, `chord_tones_no_diss_treatment`,
            `force_chord_tone`, `force_foot_in_bass`,
            `max_interval_for_non_chord_tones`,
            `min_interval_for_non_chord_tones`, `voice_lead_chord_tones`,
            `preserve_foot_in_bass`, `extend_bass_range_for_foots`
            Default: False
        chord_tone_selection: boolean. If True, then the script will select
            whether each note should be assigned a chord-tone according to a
            probabilistic function (some of whose parameters can be set below).
            Note that even if this setting is True, however, and a particular
            note is assigned to be a chord-tone, if all chord-tones fail to
            satisfy the various conditions (e.g., `max_interval`, etc.), the
            algorithm will try to find a non-chord-tone that works.
                - Note that not all chord tone behavior is controlled
                    by this setting, however. Some settings (such as those
                    that begin "force_chord_tone") apply regardless. To disable
                    all chord tone behavior entirely, use
                    `chord_tone_and_foot_disable`.
            Default: True
        chord_tone_prob_func: string. If `chord_tone_selection` is True, then
            the probability of the next note being a nonchord tone falls
            following each nonchord tone. This parameter controls how it falls.
            It can take the following values:
                "quadratic"
                "linear"
            Default: "linear"
        max_n_between_chord_tones: int. Controls after how many non-chord tones
            the probability of the following note being a chord tone rises to 1.
            For example, if `chord_tone_prob_func` is `"linear"`,
            `min_prob_chord_tone` is 0.5, and
            `max_n_between_chord_tones` is 2,
                - after a chord tone, the probability of a chord tone will be
                    0.5
                - after one non-chord tone, the probability of a chord tone will
                    be 0.75
                - after two non-chord tones, the probability of a chord tone
                    will be 1
            Default: 4
        min_prob_chord_tone: float. Sets the probability of a chord tone
            immediately following another chord tone. See
            `max_n_between_chord_tones` for an example.
            Default: 0.25
        try_to_force_non_chord_tones: boolean. If True, then if the chord-tone
            probability function returns false, the script will try to force
            the pitch to be a non-chord tone. If False, then it is selected from
            the entire scale (chord tones and non-chord tones).
            Even if True, however, if all non-chord tones fail, the
            algorithm will try to find a chord-tone that works.
            Default: False
        len_to_force_chord_tone: int. If `chord_tone_selection` is True,
            then notes of this value or longer will be forced to be chord
            tones. To disable, set to 0.
            Default: 1
        scale_chord_tone_prob_by_dur: bool. If True, and `chord_tone_selection`
            is True, then the probability of a note being a chord-tone is scaled
            by the duration of that note, so that longer notes are more likely
            to be chord-tones.  Specifically, the probability of a note being a
            chord tone is linearly interpolated between what it would have been
            otherwise and 1, according to where the duration lies in the range
            set by `scale_chord_tone_neutral_dur` and `len_to_force_chord_tone`.
            (Whether the probability of notes shorter than
            `scale_chord_tone_neutral_dur` is reduced depends upon
            `scale_short_chord_tones_down`.) Thus if this setting is True, then
            `len_to_force_chord_tone` must have a non-zero value.
            Default: True
        scale_chord_tone_neutral_dur: number. If `scale_chord_tone_prob_by_dur`
            is True, then this setting determines the note duration where
            chord-tone probability is left unchanged; notes of duration
            longer than this will have their chord-tone probability increased,
            and notes shorter will have their chord-tone probability decreased
            if `scale_short_chord_tones_down` is True.
            Default: 0.5
        scale_short_chord_tones_down: bool. See `scale_chord_tone_prob_by_dur`
            and `scale_chord_tone_neutral_dur`.
            Default: False
        chord_tone_before_rests: a number, or a per-voice sequence of numbers.
            If chord_tone_selection is true, then rests of this length or
            greater will always be preceded by a chord tone. To disable, assign
            a value of 0.
            Default: 0.26
        chord_tones_no_diss_treatment: boolean, or a per-voice sequence of
            booleans. If true, then chord tones are exempted from the conditions
            of dissonance treatment. (However, dissonances sounding *against*
            these chord tones are still subject to the rules of dissonance
            treatment.)
            Default: False
        force_chord_tone: string. Possible values:
                "global_first_beat": forces chord tone on onsets on the global
                    first beat (i.e., the first beat of the entire piece). Note,
                    however, that this does not ensure that there will be an
                    onset on the global first beat, and this parameter has no
                    effect on notes that sound *after* the first beat. (Compare
                    "global_first_note".)
                "global_first_note": forces chord tones on the first note to
                    sound in each voice.
                "first_beat": forces chord tones on onsets on the first beat
                    of each harmony of the initial pattern. Note, however, that
                    this does not ensure that there will be an onset on the
                    first beat of each harmony, and this parameter has no effect
                    on notes that sound *after* the first beat of each harmony.
                    (Compare "first_note".)
                "first_note": forces chord tones on the first note of each
                    harmony in each voice.
                "none": does not force any chord tones.
            Default: "none"
        chord_tones_sync_onset_in_all_voices: bool. If True, then chord-tone
            selection will be synchronized between all simultaneously onset
            voices.
            Default: False
        force_foot_in_bass: string. Possible values are listed below; they work
            in the same way as for `force_chord_string` above.
                "first_beat"
                "first_note"
                "global_first_beat"
                "global_first_note"
                "none"
            Default: "none"

        Melody settings
        ===============

        prefer_small_melodic_intervals: bool. If true, smaller intervals
              will be more probable than larger intervals within the range
              of each voice.
              LONGTERM how, exactly? Make documentation more explicit?
            Default: True
        prefer_small_melodic_intervals_coefficient: number. If
            `prefer_small_melodic_intervals` is true, then
            `prefer_small_melodic_intervals_coefficient` adjusts how strong the
            weighting towards smaller intervals is. It can take any value > 0;
            greater values mean larger intervals are relatively more likely. A
            good range of values is 0 - 10.
            Default: 1
        unison_weighted_as: int. If prefer_small_melodic_intervals is true, then
            we have to tell the algorithm how to weight melodic unisons, because
            we usually don't want them to be the most common melodic interval.
            Unisons will be weighted the same as whichever generic interval this
            variable is assigned to.

            (If you *DO* want unisons to be the most common melodic interval,
            set to "GENERIC_UNISON" -- you can't use "UNISON" because that's a just
            interval constant.)

            For a list of pre-defined constants that can be used with this
            setting, see docs/constants.html.

            Default: "FIFTH"
        max_interval: number, or a per-voice sequence of numbers. If `None`, does
            not apply.  If positive, indicates a generic interval. Otherwise,
            indicates a specific interval (in which case it can be a float to
            indicate a just interval which will be tempered in
            pre-processing---see the note above on specifying pitches and
            intervals).

            `max_interval` sets an inclusive bound (so if `max_interval == -5`,
            an interval of 5 semitones is allowed, but 6 is not).
            `max_interval`, like the other similar settings below, applies
            across rests.
            Default: "-OCTAVE"
        max_interval_for_non_chord_tones: number, or a per-voice sequence of
            numbers.  Works in the same way as max_interval, but only applies to
            non-chord tones. If given a value of 1, can be used to apply a sort
            of primitive dissonance treatment. It can, however, also be given a
            value *larger* than max_interval, for unusual effects.  min_interval
            sets an inclusive bound (so if `min_interval == -3`, an interval of
            3 semitones is allowed, but 2 is not).  If not passed, is assigned
            the value of `max_interval`.
        min_interval: number, or a per-voice sequence of numbers. Works like
            `max_interval`, but specifies a minimum, rather than a maximum,
            interval.
            Default: None
        min_interval_for_non_chord_tones: number, or a per-voice sequence of
            numbers. Works like `max_interval_for_non_chord_tones`, but
            specifies a minimum, rather than a maximum, interval.  If not
            passed, is assigned the value of `min_interval`.
        force_repeated_notes: bool. If True, then within each harmony, each
            note is forced to repeat the pitch of the previous note.
            Default: False
        max_repeated_notes: integer. Sets the maximum allowed number of repeated
            pitches in a single voice. If `force_repeated_notes` is True, this
            parameter is ignored. "One repeated note" means two notes with the
            same pitch in a row. To disable, set to a negative value.

            Warning: for now, only applies to the initial pattern, not to
            the subsequent voice-leading

            Default: -1
        max_alternations: integer, or a per-voice sequence of integers.
            Specifies the maximum allowed number of consecutive alternations of
            two pitches in a voice.  "One alternation" is two pitches (e.g., A,
            B), and "two alternations" is four pitches (e.g., A, B, A, B). If
            set to two, then the sequence "A, B, A, B, A" is allowed, just not
            "A, B, A, B, A, B" (or longer).  To disable, set to 0.
            Default: 2
        pitch_loop: int, or a sequence of ints. If passed, in each voice,
            pitches will be repeated in a loop of the specified length.
            (However, at each harmony change, the loop will be adjusted to fit
            the new harmony.)
        hard_pitch_loop: boolean. If True, then after the initial loop of each
            voice is constructed, pitch constraint parameters such as
            `consonances` and `max_interval` will be ignored and the pitches
            will continue to be looped "no matter what." If False, then a "soft"
            pitch loop is constructed, where a new pitch is chosen each time a
            pitch fails to pass the pitch constraint parameters.
            Default: False
        prohibit_parallels: sequence of numbers. The numbers will be treated as
            octave-equivalent intervals (so, e.g., an octave equals a unison).
            Parallel motion by these intervals will be forbidden. The obvious
            use is to prohibit parallel octaves, but can be used however one
            wishes. (See the note above on specifying pitches and intervals.)
            Default: (OCTAVE,)
        antiparallels: bool. If True, then "antiparallel" versions of the
            intervals in `prohibit_parallels` will also be prohibited. (E.g.,
            if parallel octaves are forbidden, then an octave followed by a
            unison or a fifteenth will also be forbidden, and vice versa.)
            Default: True
        force_parallel_motion: bool, or a dictionary where keys are tuples of
            ints (indicating voice indices) and values are bools.  If True,
            then voices will be constrained to move in (generic) parallel
            motion. The parallel motion is only enforced within harmonies;
            across the boundaries between harmonies, voices may move freely.
            When this parameter is True between voices that do not have the same
            onsets, it works as follows: it takes the *last* melodic interval
            in the leader voice, and adds the same melodic interval in the
            follower voice.

            If True, `prohibit_parallels` is nevertheless respected
            (specifically, the harmonic interval that would result from forcing
            parallel motion is checked for membership in `prohibit_parallels`).
            If moving in parallel with the leader would cause the follower voice
            to exceed the lowest pitch of its range, it will be moved up an
            octave; conversely, if it would exceed the highest pitch of its
            range, it will be moved down an octave. (Either operation may
            violate `max_interval` or `max_interval_for_non_chord_tones`.) Note
            that strange effects may result if the voice's range is less than an
            octave.

            Note that if the follower has a longer `pattern_len` than the
            leader, the parallel motion will only last until the conclusion
            of the leader pattern.

            Default: False


        Consonance and dissonance settings
        ==================================

        consonance_treatment: string. Controls among which notes consonance
            is evaluated. Possible values:
                "all_onsets": each pitch is evaluated for consonance with all
                    other simulatenously onset pitches.
                "all_durs": each pitch is evaluated for consonance with
                    all other pitches sounding during its duration.
                "none": no consonance treatment.
            Default: "all_onsets"
        consonance_type: string. Controls how notes are evaluated for
            consonance/dissonance. Possible values:
                "pairwise": all pairs of sounding voices are checked against
                    the sequence in `consonances`
                "chordwise": all voices are checked as a group
                    to see if they belong to one of the chords in
                    `consonant_chords`
            Default: "pairwise"
        consonance_modulo: number, or a sequence of numbers, or a
            per-voice sequence of sequences of numbers.

            If a number, only onset times that are 0 modulo this number will
            have consonance settings applied. For example, if
            `consonance_modulo == 1`, then every quarter-note beat will have
            consonance settings applied, but pitches *between* these beats
            will not.

            If a sequence of numbers, the sequence of numbers defines a loop
            of onset times at which consonance settings will be applied. The
            largest number in the sequence defines the loop length.
            For example, if `consonance_modulo == [1, 1.5, 2]`, then consonance
            settings will be applied at beats 0, 1, 1.5, 2, 3, 3.5, 4, 5, etc.

            If a sequence of sequences of numbers, each sub-sequence works as
            defined above, and they are applied to individual voices in a
            looping per-voice manner as described above.
        min_dur_for_cons_treatment: number. Notes with durations shorter than
            this value will not be evaluated for consonance.
            Default: 0
        forbidden_intervals: a sequence of numbers. The harmonic intervals
            specified by this sequence will be  avoided. Octave-equivalent
            intervals are NOT avoided. The main expected use is to avoid
            unisons. Whether this setting persists after the initial pattern
            depends on the value of `vl_maintain_consonance`. (See the note
            above on specifying pitches and intervals.)
            Default: ()
        forbidden_interval_classes: a sequence of numbers. The harmonic interval
            classes specified by this sequence will be  avoided. will be
            entirely avoided, regardless of consonance settings, at least in the
            initial pattern.  Whether this setting persists after the initial
            pattern depends on the value of `vl_maintain_consonance`. (See the
            note above on specifying pitches and intervals.)
            Default: ()
        forbidden_interval_modulo: number, or a sequence of number, or a
            sequence of sequence of numbers. Optionally defines onset times
            at which `forbidden_interval_classes` will be enforced. Works
            similarly to and is specified in the same manner as
            `consonance_modulo`.
        exclude_augmented_triad: boolean. Because all the pairwise intervals of
            the 12-tet augmented triad are consonant, if we want to avoid it, we
            need to explicitly exclude it. Only has any effect if
            consonance_type is "pairwise".
            Default: True
        consonances: a sequence of numbers. The sequence items specify the
            intervals that will be treated as consonances if `consonance_type`
            is `"pairwise"`. (But see `invert_consonances` below.) Since it's
            just a sequence of numbers, you can specify any intervals you
            like---it does not have to conform to the usual set of consonances.

            For a list of pre-defined constants that can be used with this
            setting, see docs/constants.html. See also the note above on
            specifying pitches and intervals.

            Default: `"CONSONANCES"`
        invert_consonances: bool. If True, then the contents of `consonances`
            are replaced by their setwise complement. (E.g., if `tet` is 12,
            then `[0, 3, 4, 5, 7, 8, 9]` will be replaced by `[1, 2, 6, 10,
            11]`.) This permits an easy way of specifying so-called "dissonant
            counterpoint". Has no effect if `consonance_type` is `"chordwise"`.
            Default: False
        consonant_chords: a sequence of sequences of numbers. Each sub-sequence
            specifies a chord to be understood as consonant if `consonance_type`
            is `"chordwise"`.

            For a list of pre-defined constants that can be used with this
            setting, see docs/constants.html. See also the note above on
            specifying pitches and intervals.

            Default: `("MAJOR_TRIAD", "MINOR_TRIAD")`
        chord_octave_equi_type: string. If `consonance_type` is `"chordwise"`,
            controls how the items in `consonant_chords` are interpreted
            regarding octave equivalence and octave permutations. Possible
            values:
                "all": all octave-equivalent and octave-permuted voicings are
                    allowed. Thus (C4, E4, G4), (C4, G4, E5), and (G3, E4, C4)
                    are all equivalent (as are many other voicings of a
                    C major chord).
                "bass": all octave-equivalent and octave-permuted voicings are
                    allowed, except that the bass pitch (the lowest pitch of the
                    chord) must be preserved. Thus (C4, E4, G4) and (C4, G4, E5)
                    are equivalent, but (G3, E4, C4) is not, because the lowest
                    pitch has changed.
                "order": octave equivalence is allowed but pitches must be in
                    the order listed. Thus (C4, E4, G4) is equivalent to
                    (C4, E4, G5) but not to (C4, G4, E5).
                "none": no octave equivalence or octave permutations of
                    voicings. Thus (C3, E4, G4) is not equivalent to
                    (C4, E4, G4).

            Note that transpositional equivalence always applies, so (C4, E4,
            G4) will always match (F4, A4, C5), and also (C3, E3, G3), even if
            `"none"`.

            Note on voice crossings: in all of these settings,
            "order" refers to order by pitch height, and not by voice number. So
            if voice 0 has E3 and voice 1 has C3, the order is (C3, E3), because
            C3 is lower in pitch than E3, and not (E3, C3), because voice 0 is
            lower than voice 1.
            Default: "all"
        chord_permit_doublings: string. If `consonance_type` is `"chordwise"`,
            controls when octave doublings of chord members are permitted.
            Possible values:
                "all": any and all doublings are permitted.
                "complete": doublings are only permitted once the chord is
                    complete. E.g., if the allowed chord is a major triad, then
                    after (C4, E4), the doubling E5 will not be permitted
                    because the chord is incomplete. However, after
                    (C4, E4, G4), E5 will be permitted, because the chord is
                    now complete.
                "none": all doublings are prohibited.
            Default: "all"

        Rhythm settings
        ===============

        All rhythm settings use `rhythm_len` above.

        rhythms_specified_in_midi: string. If passed, specifies a midi file
            whose rhythms will be used for the output file. In this case, all
            rhythm settings below are ignored, with the sole exception of
            `overlap`. However, `rhythm_len` and `pattern_len` must still be set
            explicitly above. If `num_voices` is greater than the number of
            tracks in the input midi file, then the rhythms will loops through
            the tracks. If the number of tracks in the input midi file is
            greater than `num_voices`, the excess tracks will be ignored.
        rhythms_in_midi_reverse_voices: boolean. The convention in this
            program is for the bass voice to be track 0. On the other hand, in
            scores (e.g., those made with Sibelius), the convention is for the
            bass to be the lowest displayed (e.g., highest-numbered) track. If
            the input file was made with this latter score-order convention, set
            this boolean to true.
            Default: False
        onset_density: a float from 0.0 to 1.0, or an int, or a per-voice
            sequence of floats and/or ints.

            Floats represent a proportion of the available onsets to be
            filled. E.g., if `onset_density == 0.5` and there are 4 possible
            onset times, there will be 2 onsets. (Possible onset times are
            determined by `onset_subdivision`, `sub_subdivisions`, and
            `comma` below).

            Integers represent a literal number of onsets. E.g., if
            `onset_density == 3`, there will be 3 onsets.

            Any negative values will be replaced by a random float between
            0.0 and 1.0.

            Note that there will always be at least one onset in each rhythm,
            regardless of how low `onset_density` is set.
            Default: 0.5
        dur_density: a float from 0.0 to 1.0, or a per-voice sequence of floats.
            Indicates a proportion of the duration of `rhythm_len` that should
            be filled. Any negative values will be replaced by a random float
            between 0.0 and 1.0.
            Default: 1.0
        onset_subdivision: a number, or a per-voice sequence of numbers.
            Indicates the basic "grid" on which onsets can take place, measured
            in quarter notes. For example, if `onset_subdivision == 1/4`, then
            onsets can occur on every sixteenth note subdivision. (But see also
            `sub_subdivision` below.) If `cont_rhythms == "all"` or
            `cont_rhythms == "grid"`, then this parameter no longer indicates
            the grid on which onsets can take place, but it is still used to
            calculate how many onset positions there should be. Thus, in the
            case of continuous rhythms, this parameter can be thought of as
            indicating the average grid duration, rather than the exact grid
            duration.
            Default: Fraction(1, 4)
        sub_subdivisions: a sequence of ints, or a per-voice sequence of
            sequences of ints.  Further subdivides `onset_subdivision`, into
            parts defined by the ratio of the integers in the sequence. This can
            be used to apply "swing" or any other irregular subdivision you
            like. For instance, if passed a value of `(3, 4, 2)`, each unit of
            length `onset_subdivision` will be subdivided into a portion of
            3/9, a portion of 4/9, and a portion of 2/9. If a sequence of
            sequences, each sub-sequence applies to an individual voice,
            interpreted in the looping per-voice manner described above.

            Note that this parameter is ignored if `cont_rhythms != "none"`.
        dur_subdivision: a number, or a per-voice sequence of numbers.
            Indicates the "grid" on which note durations are extended (and thus
            on which releases take place), which will be measured from the
            note onset. Values of 0 will be assigned the corresponding value of
            onset_subdivision. Note that, regardless of this value, all notes
            will be given a duration of at least `min_dur`, so it is possible
            that the total duration will exceed the value implied by
            `dur_subdivision` somewhat.
            Default: 0
        min_dur: a number, or a per-voice sequence of numbers. Indicates the
            minimum duration of a note. Values <= 0 will be assigned the
            corresponding value of `onset_subdivision`.
            Default: 0
        obligatory_onsets: a sequence of numbers, or a per-voice sequence of
            sequences of numbers. Numbers specify obligatory
            onset times to include in the rhythm. Zero-indexed, so beat "1"
            (in musical terms) is `0`. Thus a value of `[0, 2, 3]`, with
            an `obligatory_onsets` value of `4` would enforce onsets on beats
            0, 2, and 3, repeating every 4 beats; in musical terms, we could
            think of this as onsets on the first, third, and fourth beats of
            every measure of 4/4.

            If `obligatory_onsets` specifies more onsets than would be
            implied by `onset_density`, `obligatory_onsets` takes precedence.

            Default: ()
        obligatory_onsets_modulo: a number, or a sequence of numbers.
            Specifies which times (if any) should be understood as equivalent
            to the values in `obligatory_onsets`. Thus, if `obligatory_onsets`
            is `(0,)`, and `obligatory_onsets_modulo` is passed a value of
            `2`, then times of 2, 4, 6, ... will be equivalent to 0. Has no
            effect if `obligatory_onsets` is empty.
            Default: 4
        # TODO how to handle possible values can be string *or* int
        comma_position: string, int, or sequence of strings and/or ints.  If
            the `rhythm_len` is not divisible by `onset_subdivision`
            (e.g., `rhythm_len == 3` and `onset_subdivision == 2/3`), then
            there will be a "comma" left over that the onsets do not fill. This
            setting controls the placement of any such comma. Possible values:
              - "end": comma is placed at the end of the rhythm.
              - "anywhere": the comma is placed randomly anywhere before,
                  after, or during the rhythm.
              - "beginning": comma is placed at the beginning of the rhythm,
                  before any notes.
              - "middle": comma is placed randomly in the middle of the
                  rhythm.
              - int: specify the index at which to place the comma.
            Default: "end"
        overlap: bool. If `True`, then the final durations of each pattern
            repetition can overlap with the first durations of the next. If
            `False`, pattern overlaps are avoided.
            Default: True
        rhythmic_unison: bool, or a sequence of tuples of ints. Controls
            whether to apply "rhythmic unison" (i.e., simultaneous onsets
            and releases) to some or all voices.

            If True, all voices are in rhythmic unison. In this case, the
            rhythm settings that will apply to all voices are those of the
            bass voice (i.e., voice 0).

            If False, no voices are in rhythmic unison.

            If a sequence of tuples of ints, specifies combinations of voices
            that are in rhythmic unison. For example, `[(0, 1), (2, 3)]` would
            indicate that voices 0 and 1 would be in rhythmic unison with one
            another, while voices 2 and 3 would also be in rhythmic unison with
            one another, but neither of voices 0 and 1 are in rhythmic unison
            with either of voices 2 and 3. Voices that are not specified will
            have an independent rhythm, not in rhythmic unison with any other
            part. Thus, with four voices, `[(0, 2)]` would cause voices 0 and
            2 to be in rhythmic unison with one another, while voices 1 and 3
            would each have independent rhythms. Note that each tuple should
            be in ascending order. The rhythmic parameters that will be used
            in the construction of each rhythm are those of the first-listed
            voice.

            Note that, when using tuples of rhythmic unison voices, it is
            sometimes necessary to provide "dummy" rhythmic parameters. If, for
            instance, the `rhythmic_unison` tuples are `[(0, 1), (2, 3)]` and a
            parameter such as `onset_density` is `[0.5, 0.3]`, the second value
            of `onset_density` will never be used, because the first voices of
            the `rhythmic_unison` tuples are 0 and 2 (and 2, modulo the length
            of `onset_density`, is 0). In this situation it is necessary to
            insert a dummy value into `onset_density` (e.g., [0.5, 0.0, 0.3])
            in order to apply the parameter 0.3 to the second `rhythmic_unison`
            tuple.
            Default: False
        rhythmic_quasi_unison: bool, or a sequence of tuples of ints. This
            parameter is specified in the same way as `rhythmic_unison` above.
            However, whereas `rhythmic_unison` causes voices to have precisely
            the same rhythms, this parameter works differently. It does not
            override the rhythmic settings (such as `onset_density`) that apply
            to each voice, but it constrains the onsets of "follower" voices to
            occur at the same time as the onsets of "leader" voices, as far as
            is possible. If the follower has a greater `onset_density` than the
            leader, then the follower will have onsets simultaneous with all
            those of the leader, as well as extra onsets to satisfy its
            `onset_density` value. If the follower has a lesser
            `onset_density` than the leader, then all of the followers onsets
            will occur simultaneous with onsets in the leader, but it will have
            fewer onsets than the leader. The effect on other rhythmic
            parameters like `dur_density` is similar.  See also
            `rhythmic_quasi_unison_constrain` below.
            Default: False
        rhythmic_quasi_unison_constrain: boolean. If `rhythmic_quasi_unison`
            is False, has no effect. If True, and `rhythmic_quasi_unison` is
            True, then
                - if the follower voice has a smaller onset density than the
                leader, it will be constrained not to contain any durations
                that lie outside the durations of the leader.
                - if the follower has a greater onset density than the leader,
                it will be constrained to have all its onsets occur during the
                durations of the leader, if possible.
            Default: False
        hocketing: bool, or a sequence of tuples of ints.  This parameter is
            specified in the same way as `rhythmic_unison` above.  Its effect is
            to lead combinations of voices to be "hocketed" ---i.e., for, when
            possible, the onsets of one voice to be placed during the pauses of
            another, and vice versa.

            Tuples of the form (0, 1, 2) will cause voice 1 to be constructed
            in hocket with voice 0, and then voice 2 to be constructed in hocket
            with voice 1.

            Tuples of the form (0, 1) and (1, 2), in contrast, will cause
            voice 1 to be constructed in hocket with voice 0 (as before), but
            voice 2 to be constructed in hocket with voice 1 *but not* with
            voice 0.
            Default: False
        cont_rhythms: string. Specifies whether and how to use "continuous"
            rhythms. Usually, rhythms in music are understood in a discrete
            manner, as rational subdivisions or combinations of unit values like
            quarter-notes or thirty-second-notes. (Of course, in live
            performance, this is an idealization, since humans are not
            metronomes.) In contrast, this script allows for the construction of
            "continuous" rhythms, where the rhythmic values are drawn
            arbitrarily from the real number line.

            `cont_rhythms` can take the following values:
                "none": continuous rhythms are not used.
                "all": all voices have unique continuous rhythm.
                "grid": all voices share a continuous-rhythm "grid", so that
                    their rhythmic onsets (  and releases?) will be
                    on a common grid.

            If `cont_rhythms` is not `None`, then `rhythm_len` must equal
            `pattern_len` and both must have only a single value.
            Default: "none"
        num_cont_rhythm_vars: int, or sequence of ints. If
            `cont_rhythms != "none"`, then, optionally, the rhythms can be
            varied when they recur by perturbing them randomly. This parameter
            determines the number of such variations.  Setting it to `1` has the
            effect of disabling it. Setting it to a negative value will cause
            the rhythmic variations to continue throughout the super pattern, or
            throughout the entire output, depending on the value of
            `super_pattern_reps_cont_var`. See also `vary_rhythm_consistently`
            and `cont_var_increment`.
            Default: 1
        vary_rhythm_consistently: bool. If True, and `num_cont_rhythm_vars !=
            1`, then the perturbations applied to the rhythm will be the same
            from one variation until the next---at least until `min_dur` is
            reached in one or more of the notes of the rhythm.
            Default: True
        cont_var_increment: number. If `num_cont_rhythm_vars != 1`, determines
            how much rhythmic perturbation is applied to each variation. Larger
            values lead to larger perturbations.
            Default: 0.1
        super_pattern_reps_cont_var: bool. If True, any variations of the
            rhythm implied by `num_cont_rhythm_vars` will be allowed to continue
            into repetitions of the super pattern.
            Default: True


        Choir settings
        ==============

        choirs: sequence of ints and/or strings.

            Ints specify the program number of a GM midi instrument.

            Strings specify integer constants defining GM midi instruments
            defined in `er_constants.py`.

            For a list of pre-defined constants that can be used with this
            setting, see docs/constants.html.

            Default: ("GUITAR", "ELECTRIC_PIANO", "PIANO", "XYLOPHONE")
        choir_assignments: sequence of ints. Assigns voices to the given index
            in `choirs`. Will be looped through if necessary. For example, if
            `choir_assignments == [1, 0]`, voice 0 will be assigned to
            `choirs[1]`, voice 1 will be assigned to `choirs[0]`, voice 2 (if it
            exists) will be assigned to `choirs[1]`, and so on.  By default, or
            if passed an empty sequence, voices are assigned to choirs in
            counting order (i.e., voice 0 is assigned to choir 0, voice 1 to
            choir 1, etc.), except that if there are more voices than choirs,
            the choirs are looped through.

            If `randomly_distribute_between_choirs` is True, then this
            setting is ignored.
        randomly_distribute_between_choirs: bool. If True, then voices are
            randomly assigned to items from `choirs`. The precise way in which
            this occurs is controlled by the settings below.
            Default: False
        length_choir_segments: number. Only has an effect if
            `randomly_distribute_between_choirs` is True. Sets the duration of
            each random choir assignment in quarter notes. If 0 or negative,
            each voice is permanently assigned to a choir at random.
            Default: 1
        length_choir_loop: number. Only has an effect if
            `randomly_distribute_between_choirs` is True. If positive, sets the
            duration of a loop for the random choir assignments. Shorter values
            will be readily audible loops; longer values are likely to be less
            apparent as loops. If 0 or negative, then no loop.  Note that
            depending on the combination of settings applied, it may not be
            possible to construct a loop of sufficient length. In this case, a
            warning will be emitted, but the script will otherwise continue.
            Default: 0
        choir_segments_dovetail: bool. Only has an effect if
            `randomly_distribute_between_choirs` is True. If True, then choir
            assignments will be extended by one note, so that they overlap with
            the following choir assignment. (This can make this sort of thing
            easier for humans to play.)
            Default: False
        max_consec_seg_from_same_choir: int. Only has an effect if
            `randomly_distribute_between_choirs` is True. If positive, then no
            voice will be assigned to the same choir for more than the specified
            number of segments in a row.
            Default: 0
        all_voices_from_different_choirs: bool. Only has an effect if
            `randomly_distribute_between_choirs` is True. If True, then at each
            new choir assignment, it will be ensured that no two voices are
            assigned to the same choir.  An error will be raised if this setting
            is True and `num_voices` is greater than `len(choirs)`.
            Default: False
        each_choir_combination_only_once: bool.  Only has an effect if
            `randomly_distribute_between_choirs` is True. If True, then
            each combination of choir assignments will occur only once before
            all others are heard, or before `length_choir_loop` is reached, if
            possible.
            Default: False

        Tempo settings
        ==============

        tempo: a number or a sequence of numbers. Specifies a tempo or tempi in
            quarter-note beats-per-minute. If a sequence, the length of each
            tempo segment is set with `tempo_len`. If a sequence, will be looped
            through if necessary. If an empty sequence, a tempo or tempi will
            be randomly generated.
            Default: 120
        tempo_len: a number or a sequence of numbers. Specifies the duration of
            each tempo in `tempo` in quarter-note beats. If a sequence, will be
            looped through as necessary. Has no effect if `tempo` is a single
            number.  If 0, then the first tempo in `tempo` applies to the whole
            file.
            Default: 0
        tempo_bounds: a tuple of form (number, number). If `tempo` is an empty
            sequence, then tempi are randomly generated within the (inclusive)
            bounds set by this tuple.
            Default: (80, 144)

        Transposition settings
        ======================

        transpose: bool. Toggles transposition of segments according to the
            following settings. Note that the limits imposed by `voice_ranges`
            are not followed by the transposition settings.
            Default: False
        transpose_type: string. For explanation of the possible values, see the
            discussion of "generic" and "specific" transposition above.
            Possible values:
                "generic"
                "specific"
            Default: "specific"
        transpose_len: number, or sequence of numbers. The length of the
            segments to be transposed. If a single number, all segments have the
            same length. If a sequence of numbers, will be looped through.
            Default: 4
        transpose_intervals: number, or sequence of numbers. The interval
            or intervals by which to transpose segments. If a single number,
            all segments will be transposed by the same amount. If a sequence
            of numbers, will be looped through. The transposition is cumulative,
            so, for example, if `transpose_intervals` is `3`, then the first
            segment will be transposed by `3`, the second by `6`, etc.
            (See also `cumulative_max_transpose_interval`.)
            If an empty sequence, segments will be transposed at random.
            Default: ()
        cumulative_max_transpose_interval: a number. Sets an absolute maximum
            bound for cumulative transposition, after which segments will be
            transposed up or down an octave. The bound is inclusive. To disable,
            set to 0.  Thus, if `cumulative_max_transpose_interval == 6` and
            `transpose_intervals == 3`, segments will be transposed by 3, 6, -3,
            0, 3, ... semitones. (If, on the other hand,
            `cumulative_max_transpose_interval == 0`, segments will be
            transposed by 3, 6, 9, 12, 15, ...)
        transpose_before_repeat: boolean. If True, then any transpositions are
            applied to the completed "super pattern" *before* repeating it;
            thus, the super pattern will have the same sequence of
            transpositions on all repetitions. If False, then any transpositions
            are applied *after* repeating the super pattern. Thus, unless the
            sequence of transpositions happen to return to their starting point
            at exactly the beginning of the repetitions of the super pattern,
            each super pattern will feature a new sequence of transpositions.

        Existing voices settings
        ========================

        existing_voices: string. The path to a midi file that contains some
            pre-existing music to which new voices should be added. Settings
            such as `scales` or `chords` are not inferred from the midi file and
            must be set explicitly by the user.
        existing_voices_offset: number. Used to set the beat at which the
            voices in `existing_voices` should begin. Has no effect if
            `existing_voices` is not passed.
            Default: 0
        bass_in_existing_voice: boolean. If True, then all bass-specific
            parameters (like `preserve_foot_in_bass`) will have no effect.
            Default: False
        existing_voices_repeat: boolean. If True, then any existing voices
            will be truncated at the end of the super pattern, and then repeated
            together with the new voices.
            Default: True
        existing_voices_transpose: boolean. If True, then any existing voices
            will be transposed according to the "transposition settings" below.
            Default: True
        existing_voices_max_denominator: integer. In order to avoid rounding
            errors and the like, the rhythms in `existing_voices` are converted
            to Python's Fraction type. This parameter sets the maximum
            denominator allowed in the conversion.
            Default: 8192

        Miscellaneous settings
        ======================

        overwrite: bool. If False, if a file with the name specified by
            `output_path` already exists, the name will be incremented with
            a numeric suffix before the extension until it does not exist. E.g.,
            if `output_path == 'effrhy.mid'` but `effrhy.mid` already exists,
            `effrhy_001.mid` will be created; if `effrhy_001.mid` already
            exists, `effrhy_002.mid` will be created.
            Default: False
        max_super_pattern_len: number. If positive, the super pattern will be
            truncated if it reaches this length.
            Default: 128
        hard_bounds: a per-voice sequence of 2-tuples.  Each tuple is of form
            (lowest_note, highest_note). (See the note above on specifying
            pitches and intervals.) This setting determines a lower and upper
            bound that will be enforced regardless of the setting of
            `constrain_voice_leading_to_ranges`. The default values are the
            lowest and highest notes of an 88-key piano, respectively. See also
            `voice_ranges`.
            Default: (("OCTAVE0 * A", "OCTAVE8 * C"))
        voice_order_str: string. If "reverse", voices will be generated from
            highest to lowest. Otherwise, they are generated from lowest to
            highest.
            Default: "usual"
        allow_voice_crossings: bool, or a per-voice sequence of bools. This
            could be used, for example, to forbid voice-crossings in the bass
            voice, but not in the other voices.
            Default: True
        time_sig: an optional tuple of form (int, int). The integers are the
            numerator and denominator of a time signature, respectively. The
            time signature will be written to the midi output file and used
            if exporting notation with Verovio. If no time signature is passed,
            the script will do its best to infer an appropriate time signature
            from the other settings.
            Default: None
        initial_pattern_attempts: integer. Number of attempts to make at
            constructing initial pattern before giving up or asking whether
            to make more attempts.
            Default: 50
        exclude_from_randomization: sequence of strings. A list of
            attribute names of this class. Only has an effect when the script is
            invoked with "-r" or "--random", in which case any attribute names
            found in this list will be excluded from randomization. (Although
            note that not all attributes are randomized in any case; see the
            documentation for more info.)
            Default: ()
        voice_leading_attempts: integer. Number of attempts to make at
            constructing voice-leading pattern before giving up or asking
            whether to make more attempts.
            Default: 50
        ask_for_more_attempts: bool. If True, if `initial_pattern_attempts` or
            `voice_leading_attempts` are made without success, script will
            prompt user whether to try again.
            Default: False
        max_available_pitch_materials_deadends: integer. Sets the maximum number
            of "deadends" the recursive algorithm for building the initial
            pattern can reach before it will be aborted.
            Default: 1000

    """

    def get(self, i, *params):
        out = []
        for param in params:
            attr = getattr(self, param)
            try:
                out.append(attr[i % len(attr)])
            except TypeError:
                # If there's a type error, it should be because
                #   the param is not a list, and so we simply
                #   return the whole param.
                out.append(attr)
        if len(out) == 1:
            out = out[0]
        return out

    ###################################################################
    # Global settings

    # I retrieve the "doc" attribute of the dataclass fields dynamically, from
    # the docstring of this class. But the metadata dict is wrapped in
    # MappingProxyType() which does not support assignment. Thus, in order to
    # support assignment, I add a "mutable_attrs" dict to metadata.

    # I also tried getting parsing the docstring into per-field docs immediately
    # after defining it in the class body. But if I do that, I can't see a way
    # of programmatically retrieving the correct docstring fragment (i.e.,
    # the fragment that describes "seed" when assigning the field for `seed`)
    # and I don't want to have to hard-code all of these.
    seed: typing.Union[int, None] = fld(
        default=None,
        metadata={
            "mutable_attrs": {},
            "category": "global",
            "priority": 1,
        },
    )
    output_path: str = fld(
        default="EFFRHY/output_midi/effrhy.mid",
        metadata={
            "mutable_attrs": {},
            "category": "global",
            "shell_only": True,
            "priority": 0,
        },
    )
    overwrite: bool = fld(
        default=False,
        metadata={
            "mutable_attrs": {},
            "category": "global",
            "shell_only": True,
            "priority": 0,
        },
    )

    tet: int = fld(
        default=12,
        metadata={
            "mutable_attrs": {},
            "category": "global",
            "priority": 2,
            "val_dict": {"min_": (1,), "max_": (1200,)},
        },
    )

    # num_voices: int. If existing_voices is employed, num_voices
    #   specifies the number of voices that will be added, not the total
    #   number including the existing voices.

    num_voices: int = fld(
        default=3,
        metadata={
            "mutable_attrs": {},
            "category": "global",
            "priority": 1,
        },
    )
    num_reps_super_pattern: int = fld(
        default=2,
        metadata={
            "mutable_attrs": {},
            "category": "global",
            "priority": 3,
        },
    )

    # existing_voices: string. The path to a midi file that contains
    #   some pre-existing music to be added to. The chord/scale parameters
    #   below must be set by the user to match (if desired).
    #   To disable, set to an empty string.
    # existing_voices_offset: numb Offset for existing voices.
    # bass_in_existing_voice: boolean. If true, then bass-only parameters
    #   will not apply to voice 0 of the new voices.
    # existing_voices_repeat: boolean. If true, then the portion of
    #   the existing voices that occurs during the new super_pattern
    #   will be repeated together with the new voices.
    # existing_voices_transpose: boolean. If true, then the
    #   existing voices will be transposed along with the new voices,
    #   according to the transposition settings below. Whether this happens
    #   before or after repeat depends on transpose_before_repeat.
    # existing_voices_erase_choirs: boolean.
    # existing_voices_max_denominator: int. If 0 or false, set to 8192.

    existing_voices: str = fld(
        default="",
        metadata={
            "mutable_attrs": {},
            "category": "global",
            "shell_only": True,
            "priority": 0,
        },
    )
    existing_voices_offset: numbers.Number = fld(
        default=0,
        metadata={
            "mutable_attrs": {},
            "category": "global",
            "shell_only": True,
            "priority": 0,
        },
    )
    bass_in_existing_voice: bool = fld(
        default=False,
        metadata={
            "mutable_attrs": {},
            "category": "global",
            "shell_only": True,
            "priority": 0,
        },
    )
    existing_voices_repeat: bool = fld(
        default=True,
        metadata={
            "mutable_attrs": {},
            "category": "global",
            "shell_only": True,
            "priority": 0,
        },
    )
    existing_voices_transpose: bool = fld(
        default=True,
        metadata={
            "mutable_attrs": {},
            "category": "global",
            "shell_only": True,
            "priority": 0,
        },
    )
    existing_voices_erase_choirs: bool = fld(
        default=True,
        metadata={
            "mutable_attrs": {},
            "category": "global",
            "shell_only": True,
            "priority": 0,
        },
    )  # LONGTERM implement False
    existing_voices_max_denominator: int = fld(
        default=8192,
        metadata={
            "mutable_attrs": {},
            "category": "global",
            "shell_only": True,
            "priority": 0,
        },
    )

    # LONGTERM make continuous rhythms work with non-identical pattern_len/rhythm_len
    # TODO Document conditions specific to continuous rhythms
    pattern_len: typing.Union[
        numbers.Number, typing.Sequence[numbers.Number]
    ] = fld(
        default=0,
        metadata={
            "mutable_attrs": {},
            "category": "global",
            "priority": 1,
        },
    )
    rhythm_len: typing.Union[
        numbers.Number, typing.Sequence[numbers.Number], None
    ] = fld(
        default=None,
        metadata={
            "mutable_attrs": {},
            "category": "global",
            "priority": 1,
        },
    )
    num_harmonies: typing.Union[int, None] = fld(
        default=None,
        metadata={
            "mutable_attrs": {},
            "category": "global",
            "priority": 1,
        },
    )
    time_sig: typing.Union[None, typing.Tuple[int, int]] = fld(
        default=None,
        metadata={
            "mutable_attrs": {},
            "category": "global",
            "priority": 3,
        },
    )
    harmony_len: typing.Union[
        numbers.Number, typing.Sequence[numbers.Number]
    ] = fld(
        default=4,
        metadata={
            "mutable_attrs": {},
            "category": "global",
            "priority": 1,
        },
    )
    truncate_patterns: bool = fld(
        default=False,
        metadata={
            "mutable_attrs": {},
            "category": "global",
            "priority": 2,
        },
    )
    max_super_pattern_len: typing.Union[None, numbers.Number] = fld(
        default=None,
        metadata={
            "mutable_attrs": {},
            "category": "global",
            "priority": 3,
        },
    )
    voice_ranges: typing.Union[
        typing.Sequence[typing.Tuple[numbers.Number, numbers.Number]],
        np.ndarray,
    ] = fld(
        default="CONTIGUOUS_OCTAVES * OCTAVE3 * C",
        metadata={
            "mutable_attrs": {},
            "category": "global",
            "priority": 2,
        },
    )
    hard_bounds: typing.Sequence[
        # typing.Tuple[
        #     typing.Union[str, numbers.Number], typing.Union[str, numbers.Number]
        # ]
        typing.Tuple[numbers.Number, numbers.Number]
    ] = fld(
        default=(
            (
                "OCTAVE0 * A",
                "OCTAVE8 * C",
            ),
        ),
        metadata={
            "mutable_attrs": {},
            "category": "global",
            "priority": 3,
        },
    )
    # MAYBE add other possible voice orders, e.g., (melody, bass, inner voices)
    voice_order_str: str = fld(
        default="usual",
        metadata={
            "mutable_attrs": {},
            "category": "global",
            "priority": 4,
            # TODO possible values
        },
    )
    allow_voice_crossings: typing.Union[bool, typing.Sequence[bool]] = fld(
        default=True,
        metadata={
            "mutable_attrs": {},
            "category": "global",
            "priority": 3,
        },
    )

    ###################################################################
    # Scale and chord settings
    scales_and_chords_specified_in_midi: str = fld(
        default=None,
        metadata={
            "mutable_attrs": {},
            "category": "scale_and_chord",
            "shell_only": True,
            "priority": 0,
        },
    )
    foot_pcs: typing.Union[None, typing.Sequence[numbers.Number]] = fld(
        default=None,
        metadata={
            "mutable_attrs": {},
            "category": "scale_and_chord",
            "priority": 1,
        },
    )
    interval_cycle: typing.Union[
        None, numbers.Number, typing.Sequence[numbers.Number]
    ] = fld(
        default=None,
        metadata={
            "mutable_attrs": {},
            "category": "scale_and_chord",
            "priority": 2,
        },
    )
    scales: typing.Sequence[
        typing.Union[np.ndarray, typing.Sequence[numbers.Number]]
    ] = fld(
        default_factory=lambda: ["DIATONIC_SCALE"],
        metadata={
            "mutable_attrs": {},
            "category": "scale_and_chord",
            "priority": 1,
        },
    )
    # QUESTION is there a way to implement octave equivalence settings for
    #   chords here as well as for consonant_chords?
    chords: typing.Sequence[
        typing.Union[np.ndarray, typing.Sequence[numbers.Number]]
    ] = fld(
        default_factory=lambda: ["MAJOR_TRIAD"],
        metadata={
            "mutable_attrs": {},
            "category": "scale_and_chord",
            "priority": 1,
        },
    )

    ###################################################################
    # Midi settings

    voices_separate_tracks: bool = fld(
        default=True,
        metadata={
            "mutable_attrs": {},
            "category": "midi",
            "priority": 0,
        },
    )
    choirs_separate_tracks: bool = fld(
        default=True,
        metadata={
            "mutable_attrs": {},
            "category": "midi",
            "priority": 0,
        },
    )
    choirs_separate_channels: bool = fld(
        default=True,
        metadata={
            "mutable_attrs": {},
            "category": "midi",
            "priority": 0,
        },
    )
    write_program_changes: bool = fld(
        default=True,
        metadata={
            "mutable_attrs": {},
            "category": "midi",
            "priority": 0,
        },
    )
    humanize: bool = fld(
        default=True,
        metadata={
            "mutable_attrs": {},
            "category": "midi",
            "priority": 0,
        },
    )
    humanize_onset: float = fld(
        default=0.0,
        metadata={
            "mutable_attrs": {},
            "category": "midi",
            "priority": 0,
        },
    )
    humanize_dur: float = fld(
        default=0.0,
        metadata={
            "mutable_attrs": {},
            "category": "midi",
            "priority": 0,
        },
    )
    humanize_velocity: float = fld(
        default=0.1,
        metadata={
            "mutable_attrs": {},
            "category": "midi",
            "priority": 0,
        },
    )
    humanize_tuning: float = fld(
        default=0.0,
        metadata={
            "mutable_attrs": {},
            "category": "midi",
            "priority": 0,
        },
    )
    logic_type_pitch_bend: bool = fld(
        default=False,
        metadata={
            "mutable_attrs": {},
            "category": "midi",
            "priority": 0,
        },
    )
    num_channels_pitch_bend_loop: int = fld(
        default=9,
        metadata={
            "mutable_attrs": {},
            "category": "midi",
            "priority": 0,
        },
    )
    pitch_bend_time_prop: numbers.Number = fld(
        default=0.75,
        metadata={
            "mutable_attrs": {},
            "category": "midi",
            "priority": 0,
        },
    )

    ###################################################################
    # Tuning settings

    integers_in_12_tet: bool = fld(
        default=False,
        metadata={
            "mutable_attrs": {},
            "category": "tuning",
            "priority": 0,
        },
    )

    ###################################################################
    # Voice-leading settings
    # LONGTERM setting that allows voice-leading to be applied to entire
    #   score segment at once, rather than just to individual voices
    #   (so that each pitch-class will have same voice-leading in all
    #   parts)
    #
    #       These settings govern how the initial pattern is voice-led
    #       through subsequent harmonies.

    parallel_voice_leading: bool = fld(
        default=False,
        metadata={
            "mutable_attrs": {},
            "category": "voice_leading",
            "priority": 2,
        },
    )
    parallel_direction: int = fld(
        default=0,
        metadata={
            "mutable_attrs": {},
            "category": "voice_leading",
            "priority": 2,
        },
    )

    voice_lead_chord_tones: bool = fld(
        default=False,
        metadata={
            "mutable_attrs": {},
            "category": "voice_leading",
            "priority": 1,
        },
    )

    # LONGTERM address fact that otherwise forbidden intervals can occur
    #   if this setting is not "none"

    preserve_foot_in_bass: str = fld(
        default="none",
        metadata={
            "mutable_attrs": {},
            "category": "voice_leading",
            "priority": 1,
            "possible_values": ("lowest", "all", "none"),
        },
    )

    # LONGTERM allow transposition by multiple octaves if necessary.

    extend_bass_range_for_foots: numbers.Number = fld(
        default=0,
        metadata={
            "mutable_attrs": {},
            "category": "voice_leading",
            "priority": 2,
        },
    )
    constrain_voice_leading_to_ranges: bool = fld(
        default=False,
        metadata={
            "mutable_attrs": {},
            "category": "voice_leading",
            "priority": 3,
        },
    )
    allow_flexible_voice_leading: bool = fld(
        default=False,
        metadata={
            "mutable_attrs": {},
            "category": "voice_leading",
            "priority": 3,
        },
    )
    vl_maintain_consonance: bool = fld(
        default=True,
        metadata={
            "mutable_attrs": {},
            "category": "voice_leading",
            "priority": 2,
        },
    )
    vl_maintain_limit_intervals: str = fld(
        default="across_harmonies",
        metadata={
            "mutable_attrs": {},
            "category": "voice_leading",
            "priority": 2,
            "possible_values": ("all", "across_harmonies", "none"),
        },
    )
    # LONGTERM maintain max_repeated_notes
    vl_maintain_forbidden_intervals: bool = fld(
        default=True,
        metadata={
            "mutable_attrs": {},
            "category": "voice_leading",
            "priority": 2,
        },
    )
    vl_maintain_prohibit_parallels: bool = fld(
        default=True,
        metadata={
            "mutable_attrs": {},
            "category": "voice_leading",
            "priority": 2,
        },
    )

    ###################################################################
    # Chord tones settings

    chord_tone_and_foot_disable: bool = fld(
        default=False,
        metadata={
            "mutable_attrs": {},
            "category": "chord_tones",
            "priority": 1,
        },
    )
    chord_tone_selection: bool = fld(
        default=True,
        metadata={
            "mutable_attrs": {},
            "category": "chord_tones",
            "priority": 1,
        },
    )
    chord_tone_prob_func: str = fld(
        default="linear",
        metadata={
            "mutable_attrs": {},
            "category": "chord_tones",
            "priority": 4,
        },
    )
    max_n_between_chord_tones: int = fld(
        default=4,
        metadata={
            "mutable_attrs": {},
            "category": "chord_tones",
            "priority": 2,
        },
    )
    min_prob_chord_tone: float = fld(
        default=0.25,
        metadata={
            "mutable_attrs": {},
            "category": "chord_tones",
            "priority": 2,
        },
    )
    try_to_force_non_chord_tones: bool = fld(
        default=False,
        metadata={
            "mutable_attrs": {},
            "category": "chord_tones",
            "priority": 3,
        },
    )
    len_to_force_chord_tone: int = fld(
        default=1,
        metadata={
            "mutable_attrs": {},
            "category": "chord_tones",
            "priority": 3,
        },
    )
    scale_chord_tone_prob_by_dur: bool = fld(
        default=True,
        metadata={
            "mutable_attrs": {},
            "category": "chord_tones",
            "priority": 2,
        },
    )
    scale_chord_tone_neutral_dur: numbers.Number = fld(
        default=0.5,
        metadata={
            "mutable_attrs": {},
            "category": "chord_tones",
            "priority": 4,
        },
    )
    scale_short_chord_tones_down: bool = fld(
        default=False,
        metadata={
            "mutable_attrs": {},
            "category": "chord_tones",
            "priority": 3,
        },
    )
    # LONGTERM what about chord tone *after* rests?
    chord_tone_before_rests: typing.Union[
        numbers.Number, typing.Sequence[numbers.Number]
    ] = fld(
        default=0.26,
        metadata={
            "mutable_attrs": {},
            "category": "chord_tones",
            "priority": 2,
        },
    )
    chord_tones_no_diss_treatment: typing.Union[
        bool, typing.Sequence[bool]
    ] = fld(
        default=False,
        metadata={
            "mutable_attrs": {},
            "category": "chord_tones",
            "priority": 2,
        },
    )
    force_chord_tone: str = fld(
        default="none",
        metadata={
            "mutable_attrs": {},
            "category": "chord_tones",
            "priority": 2,
            "possible_values": (
                "global_first_beat",
                "global_first_note",
                "first_beat",
                "first_note",
                "none",
            ),
        },
    )
    chord_tones_sync_onset_in_all_voices: bool = fld(
        default=False,
        metadata={
            "mutable_attrs": {},
            "category": "chord_tones",
            "priority": 2,
        },
    )
    force_foot_in_bass: str = fld(
        default="none",
        metadata={
            "mutable_attrs": {},
            "category": "chord_tones",
            "priority": 1,
            "possible_values": (
                "global_first_beat",
                "global_first_note",
                "first_beat",
                "first_note",
                "none",
            ),
        },
    )

    ###################################################################
    # Melody settings

    prefer_small_melodic_intervals: bool = fld(
        default=True,
        metadata={
            "mutable_attrs": {},
            "category": "melody",
            "priority": 1,
        },
    )
    prefer_small_melodic_intervals_coefficient: numbers.Number = fld(
        default=1,
        metadata={
            "mutable_attrs": {},
            "category": "melody",
            "priority": 4,
        },
    )
    unison_weighted_as: int = fld(
        default="FIFTH",
        metadata={
            "mutable_attrs": {},
            "category": "melody",
            "priority": 3,
        },
    )

    # LONGTERM min rest value across which limit intervals do not apply
    # LONGTERM avoid enforcing limit intervals with voice-led foot

    max_interval: typing.Union[
        numbers.Number, typing.Sequence[numbers.Number]
    ] = fld(
        default="-OCTAVE",
        metadata={
            "mutable_attrs": {},
            "category": "melody",
            "priority": 2,
        },
    )
    max_interval_for_non_chord_tones: typing.Union[
        numbers.Number, typing.Sequence[numbers.Number]
    ] = fld(
        default="take_from_max_interval",  # TODO document this!
        metadata={
            "mutable_attrs": {},
            "category": "melody",
            "priority": 2,
        },
    )
    min_interval: typing.Union[
        None,
        numbers.Number,
        typing.Sequence[numbers.Number],
    ] = fld(
        default=None,
        metadata={
            "mutable_attrs": {},
            "category": "melody",
            "priority": 2,
        },
    )
    min_interval_for_non_chord_tones: typing.Union[
        numbers.Number, typing.Sequence[numbers.Number]
    ] = fld(
        default="take_from_min_interval",
        metadata={
            "mutable_attrs": {},
            "category": "melody",
            "priority": 2,
        },
    )

    # LONGTERM apply on a per-voice basis
    force_repeated_notes: bool = fld(
        default=False,
        metadata={
            "mutable_attrs": {},
            "category": "melody",
            "priority": 2,
        },
    )
    # max_repeated_notes only applies to the initial pattern, not to
    # the subsequent voice-leading (LONGTERM: fix)
    max_repeated_notes: int = fld(
        default=1,
        metadata={
            "mutable_attrs": {},
            "category": "melody",
            "priority": 2,
        },
    )
    max_alternations: typing.Union[int, typing.Sequence[int]] = fld(
        default=2,
        metadata={
            "mutable_attrs": {},
            "category": "melody",
            "priority": 2,
        },
    )
    pitch_loop: typing.Union[int, typing.Sequence[int]] = fld(
        default=(),
        metadata={
            "mutable_attrs": {},
            "category": "melody",
            "priority": 2,
        },
    )
    hard_pitch_loop: bool = fld(
        default=False,
        metadata={
            "mutable_attrs": {},
            "category": "melody",
            "priority": 3,
        },
    )
    # LONGTERM: prefer_alternations bool
    prohibit_parallels: typing.Sequence[numbers.Number] = fld(
        default=("OCTAVE",),
        metadata={
            "mutable_attrs": {},
            "category": "melody",
            "priority": 2,
        },
    )
    antiparallels: bool = fld(
        default=True,
        metadata={
            "mutable_attrs": {},
            "category": "melody",
            "priority": 3,
        },
    )

    # MAYBE think about other types of parallel motion (e.g.,
    #   choosing a generic harmonic interval and maintaining it)
    # MAYBE make force_parallel_motion interact with consonance settings better
    force_parallel_motion: typing.Union[
        bool, typing.Dict[typing.Sequence[int], bool]
    ] = fld(
        default=False,
        metadata={
            "mutable_attrs": {},
            "category": "melody",
            "priority": 2,
        },
    )

    ###################################################################
    # Consonance and dissonance settings

    consonance_type: str = fld(
        default="pairwise",
        metadata={
            "mutable_attrs": {},
            "category": "consonance",
            "priority": 2,
            "possible_values": (
                "pairwise",
                "chordwise",
            ),
        },
    )
    consonance_treatment: str = fld(
        default="all_onsets",
        metadata={
            "mutable_attrs": {},
            "category": "consonance",
            "priority": 1,
            "possible_values": ("all_onsets", "all_durs", "none"),
        },
    )
    # MAYBE all modulos have boolean to be truncated by initial_pattern_len?
    consonance_modulo: typing.Union[
        numbers.Number,
        typing.Sequence[numbers.Number],
        typing.Sequence[typing.Sequence[numbers.Number]],
    ] = fld(
        default=3,
        metadata={
            "mutable_attrs": {},
            "category": "consonance",
            "priority": 0,
        },
    )
    min_dur_for_cons_treatment: numbers.Number = fld(
        default=2,
        metadata={
            "mutable_attrs": {},
            "category": "consonance",
            "priority": 0,
        },
    )
    forbidden_intervals: typing.Sequence[numbers.Number] = fld(
        default=(),
        metadata={
            "mutable_attrs": {},
            "category": "consonance",
            "priority": 2,
        },
    )
    forbidden_interval_classes: typing.Sequence[numbers.Number] = fld(
        default=(),
        metadata={
            "mutable_attrs": {},
            "category": "consonance",
            "priority": 2,
        },
    )
    forbidden_interval_modulo: typing.Union[
        numbers.Number,
        typing.Sequence[numbers.Number],
        typing.Sequence[typing.Sequence[numbers.Number]],
    ] = fld(
        default=0,
        metadata={
            "mutable_attrs": {},
            "category": "consonance",
            "priority": 3,
        },
    )
    exclude_augmented_triad: bool = fld(
        default=True,
        metadata={
            "mutable_attrs": {},
            "category": "consonance",
            "priority": 2,
        },
    )
    consonances: typing.Sequence[numbers.Number] = fld(
        default="CONSONANCES",
        metadata={
            "mutable_attrs": {},
            "category": "consonance",
            "priority": 1,
        },
    )
    invert_consonances: bool = fld(
        default=False,
        metadata={
            "mutable_attrs": {},
            "category": "consonance",
            "priority": 4,
        },
    )
    consonant_chords: typing.Sequence[typing.Sequence[numbers.Number]] = fld(
        default=(
            "MAJOR_TRIAD",
            "MINOR_TRIAD",
        ),
        metadata={
            "mutable_attrs": {},
            "category": "consonance",
            "priority": 2,
        },
    )
    chord_octave_equi_type: str = fld(
        default="all",
        metadata={
            "mutable_attrs": {},
            "category": "consonance",
            "priority": 3,
        },
    )
    chord_permit_doublings: str = fld(
        default="all",
        metadata={
            "mutable_attrs": {},
            "category": "consonance",
            "priority": 3,
            "possible_values": ("all", "complete", "none"),
        },
    )

    ###################################################################
    # Rhythm settings.

    rhythmic_unison: typing.Union[
        bool, typing.Sequence[typing.Sequence[int]]
    ] = fld(
        default=False,
        metadata={
            "mutable_attrs": {},
            "category": "rhythm",
            "priority": 2,
        },
    )
    rhythmic_quasi_unison: typing.Union[
        bool, typing.Sequence[typing.Sequence[int]]
    ] = fld(
        default=False,
        metadata={
            "mutable_attrs": {},
            "category": "rhythm",
            "priority": 2,
        },
    )  # not implemented for cont_rhythms
    hocketing: typing.Union[bool, typing.Sequence[typing.Sequence[int]]] = fld(
        default=False,
        metadata={
            "mutable_attrs": {},
            "category": "rhythm",
            "priority": 2,
        },
    )
    rhythmic_quasi_unison_constrain: bool = fld(
        default=False,
        metadata={
            "mutable_attrs": {},
            "category": "rhythm",
            "priority": 2,
        },
    )
    cont_rhythms: str = fld(
        default="none",
        metadata={
            "mutable_attrs": {},
            "category": "rhythm",
            "priority": 0,
        },
    )
    # LONGTERM add obligatory_onsets to grid
    num_cont_rhythm_vars: typing.Union[int, typing.Sequence[int]] = fld(
        default=1,
        metadata={
            "mutable_attrs": {},
            "category": "rhythm",
            "priority": 0,
        },
    )
    vary_rhythm_consistently: bool = fld(
        default=True,
        metadata={
            "mutable_attrs": {},
            "category": "rhythm",
            "priority": 0,
        },
    )
    cont_var_increment: numbers.Number = fld(
        default=0.1,
        metadata={
            "mutable_attrs": {},
            "category": "rhythm",
            "priority": 0,
        },
    )
    super_pattern_reps_cont_var: bool = fld(
        default=True,
        metadata={
            "mutable_attrs": {},
            "category": "rhythm",
            "priority": 0,
        },
    )
    rhythms_specified_in_midi: str = fld(
        default="",
        metadata={
            "mutable_attrs": {},
            "category": "rhythm",
            "shell_only": True,
            "priority": 0,
        },
    )
    rhythms_in_midi_reverse_voices: bool = fld(
        default=False,
        metadata={
            "mutable_attrs": {},
            "category": "rhythm",
            "shell_only": True,
            "priority": 0,
        },
    )
    onset_density: typing.Union[
        typing.Union[float, int], typing.Sequence[typing.Union[float, int]]
    ] = fld(
        default=0.5,
        metadata={
            "mutable_attrs": {},
            "category": "rhythm",
            "priority": 1,
        },
    )
    dur_density: typing.Union[float, typing.Sequence[float]] = fld(
        default=1.0,
        metadata={
            "mutable_attrs": {},
            "category": "rhythm",
            "priority": 1,
        },
    )
    onset_subdivision: typing.Union[
        numbers.Number, typing.Sequence[numbers.Number]
    ] = fld(
        default=Fraction(1, 4),
        metadata={
            "mutable_attrs": {},
            "category": "rhythm",
            "priority": 1,
        },
    )
    sub_subdivisions: typing.Union[
        int,
        typing.Sequence[typing.Union[int, typing.Sequence[int]]],
    ] = fld(
        default=1,
        metadata={
            "mutable_attrs": {},
            "category": "rhythm",
            "priority": 3,
        },
    )
    dur_subdivision: typing.Union[
        numbers.Number, typing.Sequence[numbers.Number]
    ] = fld(
        default=0,
        metadata={
            "mutable_attrs": {},
            "category": "rhythm",
            "priority": 1,
        },
    )
    # MAYBE raise error if min_dur is empty,
    #    or other settings that cannot be empty are empty?
    min_dur: typing.Union[
        numbers.Number, typing.Sequence[numbers.Number]
    ] = fld(
        default=0,
        metadata={
            "mutable_attrs": {},
            "category": "rhythm",
            "priority": 2,
        },
    )
    obligatory_onsets: typing.Union[
        typing.Sequence[numbers.Number],
        typing.Sequence[typing.Sequence[numbers.Number]],
    ] = fld(
        default=(),
        metadata={
            "mutable_attrs": {},
            "category": "rhythm",
            "priority": 2,
        },
    )
    obligatory_onsets_modulo: typing.Union[
        numbers.Number, typing.Sequence[numbers.Number]
    ] = fld(
        default=4,
        metadata={
            "mutable_attrs": {},
            "category": "rhythm",
            "priority": 2,
        },
    )
    comma_position: typing.Union[
        str, int, typing.Sequence[typing.Union[str, int]]
    ] = fld(
        default="end",
        metadata={
            "mutable_attrs": {},
            "category": "rhythm",
            "priority": 4,
        },
    )
    overlap: bool = fld(
        default=True,
        metadata={
            "mutable_attrs": {},
            "category": "rhythm",
            "priority": 4,
        },
    )

    ###################################################################
    # Choir settings

    choirs: typing.Sequence[
        int,
        # typing.Tuple[
        #     typing.Sequence[int], typing.Union[int, typing.Sequence[int]]
        # ],
    ] = fld(
        default=(
            "GUITAR",
            "ELECTRIC_PIANO",
            "PIANO",
            "XYLOPHONE",
        ),
        metadata={
            "mutable_attrs": {},
            "category": "choir",
            "priority": 0,
        },
    )
    choir_assignments: typing.Union[None, typing.Sequence[int]] = fld(
        default=None,
        metadata={
            "mutable_attrs": {},
            "category": "choir",
            "priority": 0,
        },
    )
    randomly_distribute_between_choirs: bool = fld(
        default=False,
        metadata={
            "mutable_attrs": {},
            "category": "choir",
            "priority": 0,
        },
    )
    length_choir_segments: numbers.Number = fld(
        default=1,
        metadata={
            "mutable_attrs": {},
            "category": "choir",
            "priority": 0,
        },
    )
    length_choir_loop: numbers.Number = fld(
        default=0,
        metadata={
            "mutable_attrs": {},
            "category": "choir",
            "priority": 0,
        },
    )
    choir_segments_dovetail: bool = fld(
        default=False,
        metadata={
            "mutable_attrs": {},
            "category": "choir",
            "priority": 0,
        },
    )
    max_consec_seg_from_same_choir: int = fld(
        default=0,
        metadata={
            "mutable_attrs": {},
            "category": "choir",
            "priority": 0,
        },
    )
    all_voices_from_different_choirs: bool = fld(
        default=False,
        metadata={
            "mutable_attrs": {},
            "category": "choir",
            "priority": 0,
        },
    )
    each_choir_combination_only_once: bool = fld(
        default=False,
        metadata={
            "mutable_attrs": {},
            "category": "choir",
            "priority": 0,
        },
    )

    ###################################################################
    # Transpose settings

    transpose: bool = fld(
        default=False,
        metadata={
            "mutable_attrs": {},
            "category": "transpose",
            "priority": 2,
        },
    )
    transpose_type: str = fld(
        default="specific",
        metadata={
            "mutable_attrs": {},
            "category": "transpose",
            "priority": 2,
            "possible_values": ("generic", "specific"),
        },
    )
    transpose_len: typing.Union[
        numbers.Number, typing.Sequence[numbers.Number]
    ] = fld(
        default=4,
        metadata={
            "mutable_attrs": {},
            "category": "transpose",
            "priority": 2,
        },
    )
    transpose_intervals: typing.Union[
        numbers.Number, typing.Sequence[numbers.Number]
    ] = fld(
        default=(),
        metadata={
            "mutable_attrs": {},
            "category": "transpose",
            "priority": 2,
        },
    )
    cumulative_max_transpose_interval: numbers.Number = fld(
        default=5,
        metadata={
            "mutable_attrs": {},
            "category": "transpose",
            "priority": 3,
        },
    )
    transpose_before_repeat: bool = fld(
        default=False,
        metadata={
            "mutable_attrs": {},
            "category": "transpose",
            "priority": 3,
        },
    )

    ###################################################################
    # Tempo settings

    # LONGTERM debug tempos
    tempo: typing.Union[numbers.Number, typing.Sequence[numbers.Number]] = fld(
        default=120,
        metadata={
            "mutable_attrs": {},
            "category": "tempo",
            "priority": 1,
        },
    )
    tempo_len: typing.Union[
        numbers.Number, typing.Sequence[numbers.Number]
    ] = fld(
        default=0,
        metadata={
            "mutable_attrs": {},
            "category": "tempo",
            "priority": 2,
        },
    )
    tempo_bounds: typing.Tuple[numbers.Number, numbers.Number] = fld(
        default=(
            80,
            144,
        ),
        metadata={
            "mutable_attrs": {},
            "category": "tempo",
            "priority": 3,
        },
    )

    # LONGTERM implement, also update to effect a voice leading from
    # harmony_n of the harmonies
    # in the first pattern (which isn't necessarily 0))
    #       (use a dict)

    # reset_to_original_voicing: typing.Sequence[int] = ()

    initial_pattern_attempts: int = fld(
        default=50,
        metadata={
            "mutable_attrs": {},
            "category": "global",
            "shell_only": True,
            "priority": 0,
        },
    )
    voice_leading_attempts: int = fld(
        default=50,
        metadata={
            "mutable_attrs": {},
            "category": "global",
            "shell_only": True,
            "priority": 0,
        },
    )
    ask_for_more_attempts: bool = fld(
        default=False,
        metadata={
            "mutable_attrs": {},
            "category": "global",
            "shell_only": True,
            "priority": 0,
        },
    )
    max_available_pitch_materials_deadends: int = fld(
        default=1000,
        metadata={
            "mutable_attrs": {},
            "category": "global",
            "shell_only": True,
            "priority": 0,
        },
    )

    ###################################################################
    # Randomization settings

    exclude_from_randomization: typing.Sequence[str] = fld(
        default=(),
        metadata={
            "mutable_attrs": {},
            "category": "randomization",
            "priority": 4,
        },
    )


heading_pattern = re.compile(r"\n {8}[^\n]+\n {8}=+\n", re.MULTILINE)
default_pattern = re.compile(r"\n {12}Default.*", re.MULTILINE)
line_break_pattern = re.compile(r"(.)\n {12}(\S)", re.MULTILINE)
indent_pattern = re.compile(r"\n {12}(\S)", re.MULTILINE)


def _reformat_setting_doc(setting_doc):
    setting_doc = re.sub(default_pattern, "", setting_doc)
    setting_doc = re.sub(heading_pattern, "", setting_doc)
    setting_doc = re.sub(line_break_pattern, r"\1 \2", setting_doc)
    setting_doc = re.sub(indent_pattern, r"\n\1", setting_doc)
    return setting_doc


# I don't use __post_init__ for this function because I want to add the docs
# to the class rather than to its instances
def add_metadata_docs():
    ds = ERSettings.__doc__
    bits = re.split(r"\n {8}(\w+): ", ds)[1:]
    for setting_name, setting_doc in zip(*([iter(bits)] * 2)):
        reformatted = _reformat_setting_doc(setting_doc)
        dataclass_field = ERSettings.__dataclass_fields__[setting_name]
        mutable_attrs = dataclass_field.metadata["mutable_attrs"]
        mutable_attrs["doc"] = reformatted


add_metadata_docs()
