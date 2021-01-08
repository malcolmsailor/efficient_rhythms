import dataclasses
import numbers
import typing
from fractions import Fraction

import er_constants


@dataclasses.dataclass
class ERSettings:
    """summary

    The script works as follows:
    - an "initial_pattern" is created.
        - the length of the initial_pattern is pattern_len in each voice (it is
            not necessarily the same length in each voice)

    Note on "modular" lists:
    Many lists are understood in a modular manner. An example is `pattern_len`:
    if there are four voices, but `len(pattern_len) == 2`, voices 1 and 3 will
    be assigned the first value in `pattern_len`, while voices 2 and 4 will be
    assigned the second value.

    TODO explain "generic" and "specific" motion

    TODO "root" below doesn't necessarily strictly mean root, in the sense of
        a root position chord. Perhaps I should find a better word.

    TODO define initial pattern

    TODO document more "permissive" settings like vl_maintain_consonance that
    can be changed to help find solutions.

    A note on specifying pitch materials (i.e., pitches, intervals, etc.):
        In general, pitches can be specified either as integers, or as other
        numeric types (e.g., floats). If you don't care about tuning or
        temperament, the easiest thing to do is just specify all intervals as
        integers. Otherwise, read on:
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


    Keyword args:
        seed: int. Seed to pass to random number generators.
        tet: int. Specifies equal division of the octave.
            Default: 12.
        freeze: TODO
        num_voices: int. The number of "voices" (or "parts") to be created.
            If `existing_voices` below is
            passed, then `num_voices` specifies the number of new voices to be
            added, not the total number of voices (including those found
            in the provided midi file).
            Default: 3.
        num_reps_super_pattern: int. TODO.
            Default: 2
        pattern_len: a number, or a list of numbers. Indicates the length of the
            "basic pattern" in beats. If a single number, all voices have the same
            length; if a list, sets the length for each voice individually. The list
            is understood in a modular manner.
            If `pattern_len` is 0 or negative, it will be assigned the length of
            the complete harmonic progression (determined by `harmony_len` and
            `num_harmonies`)
            Default: 0
        truncate_patterns: bool. If True, then any values in `pattern_len` which
            are not factors of the maximum value in `pattern_len` will be
            truncated at the maximum value.
            Default: False
        rhythm_len: a number, or a list of numbers. Indicates the length of the
            rhythmic pattern to be generated. If not passed, then will be
            assigned the value of `pattern_len`. If a single number, all voices
            have the same
            length; if a list, sets the length for each voice individually. The list
            is understood in a modular manner.
            The use of `rhythm_len` is to make repeated rhythmic patterns that are
            shorter than `pattern_len`. If `rhythm_len` does not divide
            `pattern_len` evenly (e.g., if `rhythm_len = 3` and `pattern_len = 8`),
            then the final repetition of `rhythm_len` will be truncated. Similarly,
            if `rhythm_len` is longer than `pattern_len`, it will be truncated; in
            this case, one may as well not pass any value of `rhythm_len`, since in
            the absence of a value, `rhythm_len` is assigned the value of
            `pattern_len`.
            Technical detail: if `continuously varying rhythms == True`, and
                `rhythm_len` is shorter than `pattern_len` and does not divide it
                evenly, the repetition and truncation of `rhythm_len` happens
                *before* the variation.
        num_harmonies: int. The number of harmonies in the pattern. If passed a
            non-positive value,
            then will be assigned the length of `root_pcs`.
            Default: 4
        harmony_len: a number, or a list of numbers. If a list of numbers, the
            harmonies will cycle through the list until `num_harmonies` is
            reached. So, for instance, the first harmony will have the length
            of the first number in the list, the second harmony of the second,
            and so on. The list is interpreted in a modular manner. (Unlike
            `pattern_len` or `rhythm_len`, there is no way of assigning
            different harmony_lengths to different voices.)
            Default: 4
        max_super_pattern_len: number. If positive, the super pattern will be
            truncated if it reaches this length.
            Default: 128
        voice_ranges: a sequence of 2-tuples. Each tuple is of form (lowest_note, highest_note).
            (See the note above on specifying pitches.) er_constants.py provides
            a number of useful values for this purpose.
            TODO What if this list is not in order?
            TODO what if this list is too short?
            Default: AUTHENTIC_OCTAVES * OCTAVE3 * F
        voice_order_str: string. If "reverse", voices will be generated from
            highest to lowest. Otherwise, they are generated from lowest to
            highest.
            Default: "usual"
        allow_voice_crossings: bool, or a sequence of bools. If a sequence,
            applies to individual voices in a modular manner. This could be
            used, for example, to forbid voice-crossings in the bass voice,
            but not in the other voices.
            Default: True
        time_sig: an optional tuple of form (int, int). The integers are the
            numerator and denominator of a time signature, respectively. The
            time signature will be written to the midi output file and used
            if exporting notation with Verovio. If no time signature is passed,
            the script will do its best to infer an appropriate time signature
            from the other settings.
            Default: None
        existing_voices: string. The path to a midi file that contains some
            pre-existing music to which new voices should be added. Settings such
            as `scales` or `chords` are not inferred from the midi file and must
            be set explicitly by the user.
        existing_voices_offset: number. Used to set the beat at which the
            voices in `existing_voices` should begin. Has no effect if
            `existing_voices` is not passed.
            Default: 0
        bass_in_existing_voice: boolean. If True, then all bass-specific
            parameters (like `preserve_root_in_bass`) will have no effect.
            Default: False
        existing_voices_repeat: boolean. If True, then any existing voices
            will be truncated at the end of the super pattern, and then repeated
            together with the new voices.
            Default: True
        existing_voices_transpose: boolean. If True, then any existing voices
            will be transposed according to the transposition settings below,
            according to the transposition settings below.
            Default: True
        existing_voices_max_denominator: integer. In order to avoid rounding
            errors and the like, the rhythms in `existing_voices` are converted
            to Python's Fraction type. This parameter sets the maximum
            denominator allowed in the conversion.
            Default: 8192

        Scale and chord settings
        ========================

        scales_and_chords_specified_in_midi: string. If passed, specifies a
            midi file in a specific format, described below, from which the
            settings `root_pcs`, `scales`, and `chords` below should be inferred (in which case any explicit
            values for these settings are ignored).
            The midi file should consist of two tracks. `scales` are inferred
            from the first track, and `chords` and `root_pcs` are inferred
            from the second track (`root_pcs` are simply the lowest sounding
            pitch of each chord). Each track should consist entirely of
            simultaneous whole notes (i.e., semibreves) constituting the
            intended scales or chords, respectively. For an example, see
            `examples/scales_and_chords_specified_in_midi_example.mid`.
            Note that the rhythm of the harmonic changes is set through the
            `harmony_len` parameter above.
            You must ensure that chords and scales are consistent (that is,
            that the chords do not contain pitch-classes that do not belong to
            the  scales; i.e., that the scales are supersets of the chords),
            or an `InconsistentChordsAndScalesError` will be raised.
        root_pcs: sequence of numbers. Specifies the pitch-classes that
            will correspond to `0` in each item of `scales` and `chords`.
            Note that for chords that are not in root position, this will not
            correspond to the root in a music-theoretic sense.
            For example,
            if `root_pcs = [2, 4]` and `chords = [[0, 4, 7], [0, 3, 8]]`, then
            the actually realized chords will have pitch-classes `[2, 6, 9]` and
            `[4, 7, 0]`, respectively (assuming `tet = 12`). (In music-theoretic
            terms, the chords will be a D major triad followed by a first-
            inversion C major triad.)
            # TODO what if shorter than num_harmonies
            If not passed or an empty list, `num_harmonies` roots will be
            generated randomly.
            Note that if `interval_cycle` below is non-empty, all items in this
            list past the first are ignored.
        interval_cycle: number, or list of numbers.
            # TODO what exactly does this do?
        scales: a sequence of sequences of numbers. Each subsequence specifies
            a scale. Scales should always be specified starting from pitch-class
            0; they will then be transposed to the appropriate pitch-classes
            according to the settings `root_pcs` or `interval_cycle`.
            If `root_pcs` has fewer items than `scales`, then the excess items
            in `scales` will be ignored.
            If `root_pcs` has more items than `scales`, then `scales` will be
            looped through.
            Default: [er_constants.DIATONIC_SCALE]
        chords: a sequence of sequences of numbers. Each subsequence specifies
            a chord. Scales should always be specified starting from pitch-class
            0; they will then be transposed to the appropriate pitch-classes
            according to the settings `root_pcs` or `interval_cycle`.
            If `root_pcs` has fewer items than `chords`, then the excess items
            in `chords` will be ignored.
            If `root_pcs` has more items than `chords`, then `chords` will be
            looped through.
            Default: [er_constants.MAJOR_TRIAD]

        Midi settings
        =============

        voices_separate_tracks: bool. If True, different "voices" in the
            are written to separate tracks in the output midi file.
            Default: True
        choirs_separate_tracks: bool. If True, different "choirs" in the
            are written to separate tracks in the output midi file.
            Default: True
        choirs_separate_channels: bool. If True, different "choirs" in the
            are assigned to separate channels in the output midi file (up to
            the maximum of 16 channels).
            Default: True
        write_program_changes: bool. If True, General Midi program changes are
            written to the output midi file. Depending on the intended use,
            this may or may not be desired.
            Default: True
        humanize: bool. Whether to apply "humanization" to various parameters
            according to the various "humanize" settings below.
            Default: True.
        humanize_attack: float. Randomly varies attack times within +- this
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

        Voice-leading settings
        ======================

        prohibit_parallels: list-like of numbers. The numbers will be treated as
            octave-equivalent intervals (so, e.g., an octave equals a unison).
            Parallel motion by these intervals will be forbidden. The obvious
            use is to prohibit parallel octaves, but can be used however one
            wishes.
            TODO floats/ints?
            Default: (OCTAVE,)
        antiparallels: bool. If True, then "antiparallel" versions of the
            intervals in `prohibit_parallels` will also be prohibited. (E.g.,
            if parallel octaves are forbidden, then an octave followed by a
            unison or a fifteenth will also be forbidden, and vice versa.)
            Default: True
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

        voice_lead_chord_tones: bool. TODO what does this do?
            Default: True

        preserve_root_in_bass: string. Controls whether the occurrences
            of the root in the bass are "preserved" when voice-leading the
            initial pattern to subsequent harmonies. For example, if the first
            two harmonies are C major followed by F major, should a C in the
            bass on the first chord be voice-led to an F in the bass on the
            second chord, preserving the root, or should it be voice-led to a C
            (which would be more efficient, in the sense of moving a smaller
            interval, a unison, rather than a fourth or fifth).
            Possible values:
                - "lowest": only the lowest sounding occurrences of
                    the root on each harmony are preserved (so if, e.g.,
                    C2 and C3 both occur, only C2 will
                    be preserved when voice-led to the next chord, while
                    C3 will proceed by efficient voice-leading like all
                    other pitches).
                - "all": all occurrences of the root of each harmony
                    are preserved.
                - "none": the root is voice-led like any other pitch.
            Default: "lowest"
        extend_bass_range_for_roots: number. If non-zero, permits transposition
            of the root lower than the normal range of the bass voice, in order
            to maintain the root as the lowest sounding pitch during a given
            harmony. Specifically, if the lowest sounding occurrences
            of the root during a given harmony are not the lowest sounding pitch
            during that harmony, then they will be transposed an octave
            downwards, provided that this transposition lies within this
            extended range. TODO allow transposition by multiple octaves if
            necessary.
            Default: 0.
        constrain_voice_leading_to_ranges: bool. If False, then after the
            initial pattern is complete, the voices may exceed their ranges, if
            the most efficient voice-leading requires it. (For example, if
            the highest pitch of a voice's range is G, but a subsequent
            efficient voice-leading requires G-sharp, the voice will be allowed
            to ascend to G-sharp, rather than enforcing a less-efficient
            voice-leading).
            Default: False
        allow_flexible_voice_leading: bool. TODO document better
            Default: True
        vl_maintain_consonance: bool. If False, then after the initial pattern
            is complete, voice-leadings will not be checked for consonance.
            TODO refer to appropriate settings
            Default: True
        vl_maintain_limit_intervals: bool. If False, then after the initial pattern
            is complete, voice-leadings will be allowed to exceed limit intervals.
            TODO refer to appropriate settings
            Default: True
        vl_maintain_forbidden_intervals: bool. If False, then after the initial pattern
            is complete, voice-leadings will be permitted to contain forbidden intervals.
            TODO refer to appropriate settings
            Default: True

        Chord-tone settings
        ===================

        chord_tone_and_root_disable: bool. If True, disables all chord-tone and root
            specific behaviour.
            Default: False
        chord_tone_selection: boolean. If True, then the script will select whether
            each note should be assigned a chord-tone according to some probabilistic
            function (some of whose parameters can be set below).
                - Note that not all chord tone behaviour is controlled
                    by this setting, however. Some settings (such as those
                    that begin "force_chord_tone") apply regardless. To disable
                    all chord tone behaviour, use chord_tone_and_root_disable.
                    # TODO clarify this note?
            Default: True
        chord_tone_prob_func: string. If chord_tone_selection is True, then the
            probability of the next note being a nonchord tone falls following
            each nonchord tone. This parameter controls how it falls. It can take
            the following values:
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
                - after one non-chord tone, the probability of a chord tone will be 0.75
                - after two non-chord tones, the probability of a chord tone will be 1
            Default: 4.
        min_prob_chord_tone: float. Sets the probability of a chord tone
            immediately following another chord tone.
            See `max_n_between_chord_tones` for an example.
            Default: 0.25
        force_non_chord_tones: boolean. If True, then if the chord-tone
            probability function returns false, the pitch is forced to be
            a non-chord tone. Otherwise it is selected from the entire scale
            (chord tones and non-chord tones).
            Default: False
              - Note that the actual probabilities realized in the music
                will likely vary somewhat. This is because the algorithm
                will backtrack if it fails to find any pitches that works,
                and once it has exhausted the chord tones (if it has
                selected a chord tone) it will turn to the non-chord tones,
                and vice versa.
                TODO move this note to a better spot?

        len_to_force_chord_tone: int. Default: 2 TODO
        scale_chord_tone_prob_by_dur: bool. Default: True TODO
        scale_chord_tone_neutral_dur: number. Default: 0.5 TODO
        scale_short_chord_tones_down: bool. Default: True TODO
        chord_tone_before_rests: number, or list of numbers. If chord_tone_selection is true,
            then rests of this length or greater will always be preceded by a
            chord tone. To disable, assign a value of 0.
            If a list, is interpreted as applying to voices in a modular manner.
            Default: 0.26
        chord_tones_no_diss_treatment: boolean, or list of booleans. If
            true, then chord tones are exempted from the conditions of dissonance
            treatment. (However, dissonances sounding *against* these chord
            tones are still subject to the rules of dissonance treatment.)
            If a list, is interpreted as applying to voices in a modular manner.
            Default: True
        force_chord_tone: string. Possible values:
            "global_first_beat": forces chord tone on attacks on the global
               first beat (i.e., the first beat of the entire piece). Note,
               however, that this does not ensure that there will be an attack
               on the global first beat, and this parameter has no effect on
               notes that sound *after* the first beat. (Compare "global_first_note".)
            "global_first_note": forces chord tones on the first note to
              sound in each voice.
            "first_beat": forces chord tones on attacks on the first beat
              of each harmony of the initial pattern. Note, however, that this
              does not ensure that there will be an attack on the first beat of
              each harmony, and this parameter has no effect on notes that sound
              *after* the first beat of each harmony. (Compare "first_note".)
            "first_note": forces chord tones on the first note of each harmony
              in each voice.
            "none": does not force any chord tones.
            Default: "none"
        chord_tones_sync_attack_in_all_voices: bool. TODO
            Default: False
        force_root_in_bass: string. Possible values are listed below; they work
            in the same way as for `force_chord_string` above.
                  - "first_beat"
                  - "first_note"
                  - "global_first_beat"
                  - "global_first_note"
                  - "none"
            Default: "none"

        Melody settings
        ===============

        control_melodic_intervals: bool. If true, smaller intervals
              will be more probable than larger intervals within the range
              of each voice. TODO rename this variable?
              TODO how, exactly? Make documentation more explicit?
            Default: True
        control_coefficient: number. If control_melodic_intervals is true,
          then control_coefficient adjusts how strong the weighting
          towards smaller intervals is. It can take any value > 0; greater
          values mean larger intervals are relatively more likely. A good
          range of values is 0 - 10.
          Default: 1
        unison_weighted_as: int. If control_melodic_intervals is true, then
          we have to tell the algorithm how to weight melodic unisons,
          because we usually don't want them to be the most common melodic
          interval. Unisons will be weighted the same as whichever generic
          interval this variable is assigned to.
          (If you *DO* want unisons to be the most common melodic interval,
          set to GENERIC_UNISON -- you can't use UNISON because that's
          a just interval constant.) TODO specify from er_constants
          Default: FIFTH
        max_interval: number, or list of numbers.  (See note on "modular" lists.) If zero, does not apply.
          If positive, indicates a generic interval. If
          negative, indicates a specific interval (in which case it can be a
          float to indicate a just interval which will be tempered in
          pre-processing).
          Default: -OCTAVE
        max_interval_for_non_chord_tones: number, or list of numbers. (See note on "modular" lists.)
          Works in the same way as max_interval, but only applies to
          non-chord tones. If given a value of 1, can be used to apply a
          sort of primitive dissonance treatment. It can, however, also
          be given a value *larger* than max_interval, for unusual effects.
          Default: -OCTAVE
        min_interval: number, or list of numbers. (See note on "modular" lists.) Works like max_interval, but
            specifies a minimum, rather than a maximum, interval.
            Default: 0
        min_interval_for_non_chord_tones: number, or list of numbers. (See note on "modular" lists.) Works like max_interval_for_non_chord_tones, but
            specifies a minimum, rather than a maximum, interval.
            Default: 0
        force_repeated_notes: bool. TODO
            Default: False
        max_repeated_notes: integer. Sets the maximum allowed number of repeated
            pitches in a single voice. If `force_repeated_notes` is True, this
            parameter is ignored.
            Default: 1
        max_alternations: integer, or sequence of integers (understood in a modular
            manner). Specifies the
            maximum allowed number of consecutive alternations of two pitches
            in a voice.  "One alternation" is two pitches (e.g., A, B), and
            "two alternations"
            is four pitches (e.g., A, B, A, B). If set to two, then the sequence
            "A, B, A, B, A" is allowed, just not "A, B, A, B, A, B" (or longer).
            To disable, set to 0.
            Default: 2
        pitch_loop: int, or list of ints. If passed, in each voice, pitches will be
            repeated in a loop of the specified length. (However, at each harmony change, the loop
            will be adjusted to fit the new harmony.)
        hard_pitch_loop: boolean. If True, then after the initial loop of each voice
            is constructed, pitch constraint parameters such as `consonance` (TODO is this actually a
            parameter) and `max_interval` will be ignored and the pitches will
            continue to be looped "no matter what." If False, then a "soft" pitch
            loop is constructed, where a new pitch is chosen each time a pitch fails
            to pass the pitch constraint parameters.
            Default: False

        Consonance and dissonance settings
        ==================================

        consonance_treatment: string. Controls among which notes consonance
            is evaluated. Possible values:
                "all_attacks": each pitch is evaluated for consonance with all
                    other simulatenously attacked pitches.
                "all_durs": each pitch is evaluated for consonance with
                    all other pitches sounding during its duration.
                "none": no consonance treatment.
                Default: "all_attacks"
        consonance_type: string. Controls how notes are evaluated for
            consonance/dissonance. Possible values:
                "pairwise": all pairs of sounding voices are checked against
                    the list in `consonances`
                "chordwise": all voices are checked as a group
                    to see if they belong to one of the chords in
                    `consonant_chords`
                Default: "pairwise"
        consonance_modulo: TODO
        min_dur_for_cons_treatment: number. Notes with durations shorter than
            this value will not be evaluated for consonance.
            Default: 0
        forbidden_interval_classes: a list of numbers. The intervals in
          this list (interpreted as harmonic intervals) will be entirely avoided,
          regardless of consonance settings, at least in the initial pattern.
          Whether this setting persists after the initial pattern depends on
          the value of `vl_maintain_consonance`
        forbidden_interval_modulo: TODO
        exclude_augmented_triad: boolean. Because all the pairwise intervals of
          the 12-tet augmented triad are consonant, if we want to avoid it, we
          need to explicitly
          exclude it. Only has any effect if consonance_type is "pairwise".
          Default: True
        consonances: a list of numbers. The list items specify the intervals
            that will be treated as consonances if `consonance_type` is
            `"pairwise"`. (But see `invert_consonances` below.) Since it's just a list of numbers, you can specify
            any intervals you like---it does not have to conform to the usual
            set of consonances.
            Default: CONSONANCES # TODO
        invert_consonances: bool. If True, then the contents of `consonances`
            are replaced by their setwise complement. (E.g., if `tet` is 12, then
            `[0, 3, 4, 5, 7, 8, 9]` will be replaced by `[1, 2, 6, 10, 11]`.)
            This permits an easy way of specifying so-called "dissonant
            counterpoint". Has no effect if `consonance_type` is `"chordwise"`.
            Default: False
        consonant_chords: a list of sequences of numbers. Each sub-sequence specifies a
            chord to be understood as consonant if `consonance_type` is
            `"chordwise"`.
            Default: (MAJOR_TRIAD, MINOR_TRIAD)
        chord_octave_equi_type: string. If `consonance_type` is `"chordwise"`,
            controls how the items in
            `consonant_chords` are interpreted regarding octave equivalence and
            octave permutations. Possible
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
                "none": no octave equivalence or octave permutations of voicings.
                    Thus (C3, E4, G4) is not equivalent to (C4, E4, G4).
            Note that transpositional equivalence always applies, so (C4, E4, G4)
            will always match (F4, A4, C5), and also (C3, E3, G3), even if `"none"`.
            Note on voice crossings: in all of these settings, "order" refers to order by
            pitch height, and not by voice number. So if voice 0 has E3 and
            voice 1 has C3, the order is (C3, E3), because C3 is lower in pitch
            than E3, and not (E3, C3), because voice 0 is lower than voice 1.
            Default: "all"
        chord_permit_doublings: string. If `consonance_type` is `"chordwise"`,
            controls when octave doublings of chord members are permitted.
            Possible values:
                "all": any and all doublings are permitted.
                "complete": doublings are only permitted once the chord is
                    complete. E.g., if the allowed chord is a major triad, then
                    after (C4, E4), the doubling E5 will not be permitted
                    because the chord is incomplete. However, after (C4, E4, G4),
                    E5 will be permitted, because the chord is now complete.
                "none": all doublings are prohibited.
            Default: "all"
            TODO is it possible to specify doublings in voicings? E.g.,
                something like [0, 3, 7, 12]?

        Rhythm settings
        ===============

        All rhythm settings use `rhythm_len` above.

        rhythms_specified_in_midi: string. If passed, specifies a
            midi file whose rhythms will be used for the output file. In this
            case, all rhythm settings below are ignored, with the sole
            exception of `overlap`. However, `rhythm_len`
            and `pattern_len` must still be set explicitly above. If
            `num_voices` is greater than the number of tracks in the input midi
            file, then the rhythms will loops through the tracks. If the number
            of tracks in the input midi file is greater than `num_voices`,
            the excess tracks will be ignored.
        rhythms_in_midi_reverse_voices: boolean. The convention in this
            program is for the bass voice to be track 0. On the other hand, in
            scores (e.g., those made with Sibelius), the convention is for the bass
            to be the lowest displayed (e.g., highest-numbered) track. If the input file
            was made with this latter score-order convention, set this
            boolean to true.
            Default: False
        attack_density: a float from 0.0 to 1.0, or an int, or a list of
            floats and/or ints (interpreted in a modular manner).
            Floats represent a proportion of the available attacks to be
            filled. E.g., if `attack_density = 0.5` and there are 4 possible
            attack times, there will be 2 attacks. # TODO how is the possible attack times determined?
            Integers represent a literal number of attacks. E.g., if
            `attack_density = 3`, there will be 3 attacks.
            Any negative values will be replaced by a random float between
            0.0 and 1.0.
            TODO how does attack_density work with continuous rhythms?
            Default: 0.5
        dur_density: a float from 0.0 to 1.0, or a (modular) sequence of floats.
            Indicates a proportion of the duration of `rhythm_len` that should
            be filled. Any negative values will be replaced by a random float between
            0.0 and 1.0.
            Default: 1.0
        attack_subdivision: a number, or a (modular) sequence of numbers.
            Indicates the basic "grid" on which attacks can take place,
            measured in quarter notes. For example, if
            `attack_subdivision = 1/4`, then attacks can occur on every
            sixteenth note subdivision. (But see also `sub_subdivision` below.)
            Default: Fraction(1, 4)
        sub_subdivisions: a sequence of ints, or a sequence of sequence of ints.
            Further subdivides `attack_subdivision`, into parts defined by the
            ratio of the integers in the list. This can be used to apply "swing"
            or any other irregular subdivision you like. For instance, if passed
            a value of `(3, 4, 2)`, each unit of length `attack_subdivision`
            will be subdivided into a portion of 3/9, a portion of 4/9, and a
            portion of 2/9. If a sequence of sequences, each sub-sequence
            applies to an individual voice, interpreted in a modular manner.
        dur_subdivision: a number, or a (modular) sequence of numbers.
            Indicates the "grid" on which note durations are extended (and thus
            on which releases take place), which will be measured from the
            note attack. Values of 0 will be assigned the corresponding value of
            attack_subdivision.
            NB If extending the note by dur_subdivision would lead to
            the total duration of the notes of the rhythm being larger than
            the target set by `dur_density`, then the note will be extended
            by less than this. (TODO Do I like this behavior? Perhaps change?)
            Default: 0
        min_dur: a number, or a (modular) sequence of numbers. Indicates the
            minimum duration of a note. Values of 0 will be assigned the
            corresponding value of attack_subdivision.
            NB it is possible for notes to be shorter than this (I think) if
            extending them would exceed the target set by `dur_density`
            TODO change this!
            Default: 0
        obligatory_attacks: a sequence of numbers, or a sequence of sequence
            of numbers (interpreted modularly). Numbers specify obligatory
            attack times to include in the rhythm. Zero-indexed, so beat "1"
            (in musical terms) is `0`. Thus a value of `[0, 2, 3]`, with
            an `obligatory_attacks` value of `4` would enforce attacks on beats
            0, 2, and 3, repeating every 4 beats; in musical terms, we could
            think of this as attacks on the first, third, and fourth beats of
            every measure of 4/4.
            Default: ()
        obligatory_attacks_modulo: a number, or a sequence of numbers.
            Specifies which times (if any) should be understood as equivalent
            to the values in `obligatory_attacks`. Thus, if `obligatory_attacks`
            is `(0,)`, and `obligatory_attacks_modulo` is passed a value of
            `2`, then times of 2, 4, 6, ... will be equivalent to 0. Has no
            effect if `obligatory_attacks` is empty.
            Default: 4
        comma_position: string, int, or sequence of strings and/or ints.  If
            the `rhythm_len` is not divisible by `attack_subdivision`
            (e.g., `rhythm_len = 3` and `attack_subdivision = 2/3`), then
            there will be a "comma" left over that the attacks do not fill. This
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
            whether to apply "rhythmic unison" (i.e., simultaneous attacks
            and releases) to some or all voices.
            If True, all voices are in rhythmic unison. In this case, the
            rhythm settings that will apply to all voices are those of the
            bass voice (i.e., voice 0). TODO verify!
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
            would each have independent rhythms.
            Note that, when using tuples of rhythmic unison voices, it is
            sometimes necessary to provide "dummy" rhythmic parameters. If, for
            instance, the `rhythmic_unison` tuples are
                  `[(0, 1), (2, 3)]` and a parameter such as
                  `attack_density` is `[0.5, 0.3]`, the second
                  value of `attack_density` will never be used,
                  because the first voices of the `rhythmic_unison`
                  tuples are 0 and 2 (and 2, modulo the length of
                  `attack_density`, is 0). In this situation it
                  is necessary to insert a dummy value into `attack_density` (e.g.,
                  [0.5, 0.0, 0.3]) in order to apply the parameter 0.3 to
                  the second `rhythmic_unison` tuple.
            TODO Each tuple should be in ascending order---why? Perhaps sort.
            TODO double check comment-docs below
            Default: False
        rhythmic_quasi_unison: bool, or a sequence of tuples of ints. This
            parameter is specified in the same way as `rhythmic_unison` above,
            but ... TODO how exactly does this work?
        hocketing: bool, or a sequence of tuples of ints.  This
            parameter is specified in the same way as `rhythmic_unison` above.
            Its effect is to lead combinations of voices to be "hocketed"
            ---i.e., for, when possible, the attacks of one voice to be placed
            during the pauses of another, and vice versa.
            Tuples of the form (0, 1, 2) will cause voice 1 to be constructed
            in hocket with voice 0, and then voice 2 to be constructed in hocket
            with voice 1.
            Tuples of the form (0, 1) and (1, 2), in contrast, will cause
            voice 1 to be constructed in hocket with voice 0 (as before), but
            voice 2 to be constructed in hocket with voice 1 *but not* with
            voice 0.
        rhythmic_quasi_unison_constrain: boolean. If `rhythmic_quasi_unison`
            is False, has no effect. If True, and `rhythmic_quasi_unison` is
            True, then
                - if the follower voice has a smaller attack density than the
                leader, it will be constrained not to contain any durations
                that lie outside the durations of the leader.
                - if the follower has a greater attack density than the leader,
                it will be constrained to have all its attacks occur during the
                durations of the leader, if possible.
        cont_rhythms: string. Specifies whether and how to use "continuous"
            rhythms. Usually, rhythms in music are understood in a discrete
            manner, as rational subdivisions or combinations of unit values
            like quarter-notes or thirty-second-notes. (Of course, in
            live performance, this is
            an idealization, since humans are not metronomes.) In contrast,
            this script allows for the construction of "continuous" rhythms,
            where the rhythmic values are
            drawn arbitrarily from the real number line (to whatever precision
            Python allows).
            `cont_rhythms` can take the following values:
                "none": continuous rhythms are not used.
                "all": all voices have unique continuous rhythm.
                "grid": all voices share a continuous-rhythm "grid", so that
                    their rhythmic attacks (TODO and releases?) will be
                    on a common grid.
            Default: "none"

        Choir settings
        ==============

        choirs: a sequence of ints or tuples.
            Integers specify
            the program numbers of GM midi instruments. Constants defining
            these can be found in `er_constants.py`.
            Tuples can be used to combine multiple instruments (e.g., violins
            and cellos) into a single "choir". They should consist of two items:
                - a sequence of GM midi instruments, listed from low to high
                - an integer or sequence of integers, specifying a split point
                or split points, that is, the pitches at which the instruments
                should be switched between.
            Default: (er_constants.MARIMBA, er_constants.VIBRAPHONE, er_constants.ELECTRIC_PIANO, er_constants.GUITAR,)
        choir_assignments: sequence of ints. Assigns voices to the given index
            in `choirs`. Will be looped through if necessary. For example, if
            `choir_assignments = [1, 0]`, voice 0 will be assigned to
            `choirs[1]`, voice 1 will be assigned to `choirs[0]`, voice 2 (if
            it exists) will be assigned to `choirs[1]`, and so on.
            By default, or if passed an empty list, all voices are assigned to
            choir 0.
            If `randomly_distribute_between_choirs` is True, then this
            setting is ignored.
        randomly_distribute_between_choirs: bool. If True, then voices are
            randomly assigned to items from `choirs`. The precise way in which
            this occurs is controlled by the settings below.
            Default: False
        length_choir_segments: number. Only has an effect if
            `randomly_distribute_between_choirs` is True. Sets the duration
            of each random choir
            assignment in quarter notes. If 0 or negative, each voice is
            permanently assigned to a choir at random.
            Default: 1
        length_choir_loop: number. Only has an effect if
            `randomly_distribute_between_choirs` is True. If positive, sets
            the duration of a loop for the random choir assignments. Shorter
            values will be readily audible loops; longer values are likely
            to be less apparent as loops. If 0 or negative, then no loop.
            Note that depending on the combination of settings applied,
            it may not be possible to construct a loop of sufficient
            length. In this case, a warning will be emitted, but the script
            will otherwise continue.
            Default: 0
        choir_segments_dovetail: bool. Only has an effect if
            `randomly_distribute_between_choirs` is True. If True, then
            choir assignments will be extended by one note, so that they overlap
            with the following choir assignment. (This can make this sort
            of thing easier for humans to play.)
            Default: False
        max_consec_seg_from_same_choir: int. Only has an effect if
            `randomly_distribute_between_choirs` is True. If positive, then
            no voice will be assigned to the same choir for more than the
            specified number of segments in a row.
            Default: 0
        all_voices_from_different_choirs: bool. Only has an effect if
            `randomly_distribute_between_choirs` is True. If True, then at each
            new choir assignment, it will be ensured that no two voices are
            assigned to the same choir.
            An error will be raised if this setting is True and `num_voices`
            is greater than `len(choirs)`.
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
        tempo_len: a number or a sequence of numbers. Specifies the duration of each
            tempo in `tempo` in quarter-note beats. If a sequence, will be looped
            through as necessary. Has no effect if `tempo` is a single number.
            If 0, then the first tempo in `tempo` applies to the whole file.
            Default: 0
        tempo_bounds: a tuple of form (number, number). If `tempo` is an empty
            sequence, then tempi are randomly generated within the (inclusive)
            bounds set by this tuple.
            Default: (80, 144)


    Attributes:
        attribute_name: attribute_description

    Methods:
        method_name: method_description
    """

    # TODO document get
    # TODO rename get? integrate with built-in attribute access somehow?
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

    # TODO fix 2420!!!
    # TODO why does max_repeated_notes fail? (e.g., 2471)
    # TODO why does 2558 not work?

    ###################################################################
    # Global settings

    # TODO type checking? (is there a library that will perform this automatically?)
    # TODO documentation
    seed: int = None

    tet: int = 12

    # freeze: string.
    #       - "rhythms"
    #       - "initial_pattern"
    #       - "super_pattern"
    #       - "complete_pattern"
    # TODO delete, I think
    freeze: str = ""

    # num_voices: int. If existing_voices is employed, num_voices
    #   specifies the number of voices that will be added, not the total
    #   number including the existing voices.

    num_voices: int = 3
    num_reps_super_pattern: int = 2

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

    existing_voices: str = ""
    existing_voices_offset = 0
    bass_in_existing_voice = False
    existing_voices_repeat = True
    existing_voices_transpose = True
    existing_voices_erase_choirs = True  # LONGTERM implement False
    existing_voices_max_denominator = 8192

    # pattern_len: number or list of numbers (to indicate different
    #   lengths) for each voice. Negative numbers will be assigned the
    #   value of (harmony_len * num_harmonies). (I.e., the pattern will
    #   be the length of the complete harmonic progression.)
    # rhythm_len: number or list of numbers. If an empty list,
    #   pattern_len will be used instead. If rhythm_len does not divide
    #   pattern_len evenly, it will be truncated.
    #       If continuously varying rhythms, and rhythm_len is shorter
    #   than pattern_len and does not divide it evenly, the repetition and
    #   truncation of rhythm_len happens *before* the variation.
    # MAYBE make different rhythm/pattern lengths work with
    #   cont_rhythm == True
    # num_harmonies: if negative, will be assigned the length of
    #   root_pcs, defined below.
    # pitch_loop: an int, or a list of ints. Indicates the number of
    #   pitches to loop in each voice (these loops will be adjusted to
    #   each harmony change). To disable, just use 0.
    #   consonance, max_interval, and other such parameters will be
    #   ignored after the initial number of pitches in the loop are
    #   constructed. If false, then a "soft" pitch loop is constructed,
    #   so that a new pitch will be chosen each time the consonance etc.
    #   checks fail on a pitch from the loop.

    # TODO make continuous rhythms work with non-identical pattern_len/rhythm_len
    pattern_len: typing.Union[
        numbers.Number, typing.Sequence[numbers.Number]
    ] = 0
    rhythm_len: typing.Union[
        numbers.Number, typing.Sequence[numbers.Number]
    ] = None
    num_harmonies: int = 4
    pitch_loop: typing.Union[int, typing.Sequence[int]] = ()
    hard_pitch_loop: bool = False

    # time_sig: a tuple of ints, or None. The tuple should be the
    #   numerator and denominator of the time signature. A time signature
    #   will be inferred from the other settings but if desired
    #   it can be set explicitly here.

    time_sig: typing.Tuple[int, int] = None

    # harmony_len: number, or list of numbers. If a list of numbers,
    #   the harmonies will cycle through these lengths. (There's no way
    #   of assigning different harmony lengths to different voices.)

    harmony_len: typing.Union[
        numbers.Number, typing.Sequence[numbers.Number]
    ] = 4

    # truncate_patterns: if True, then any values in pattern_len
    #   which are not factors of the maximum value will be truncated at
    #   the maximum value.

    truncate_patterns: bool = False

    # max_super_pattern_len: if non-zero, the super pattern will
    #   be truncated if it reaches this length

    max_super_pattern_len: numbers.Number = 128

    # voice_ranges: a list of tuples of form (lowest_note, highest_note).
    #   It is most usefully indicated by constants by means of the constants
    #   defined in er_constants.py. The specified ranges are inclusive of the
    #   boundary pitches.

    voice_ranges: typing.Sequence[
        typing.Tuple[numbers.Number, numbers.Number]
    ] = er_constants.AUTHENTIC_OCTAVES * er_constants.OCTAVE3 * er_constants.F

    # voice_order_str: if "reverse", then the voices will be generated
    #   from highest to lowest. Otherwise, they are generated from
    #   lowest to highest.
    # MAYBE add other possibilities, e.g., (melody, bass, inner voices)

    voice_order_str: str = "usual"

    # allow_voice_crossings: bool, or list of bools.

    allow_voice_crossings: typing.Union[bool, typing.Sequence[bool]] = True

    ###################################################################
    # Scale and chord settings

    # scales_and_chords_specified_in_midi: if None, then
    #    root_pcs, scales and chords are used from below.

    scales_and_chords_specified_in_midi: str = None

    # root_pcs: list. If an empty list, roots
    #   will be generated randomly. Floats will be treated as just
    #   intervals, and ints as tempered intervals.
    # interval_cycle: int, float, or list thereof. Creates an
    #   interval cycle beginning on the first key note of root_pcs
    #   (in which case any remaining items in root_pcs are ignored).
    #   If an empty list, has no effect.

    root_pcs: typing.Sequence[numbers.Number] = None
    interval_cycle: typing.Union[
        numbers.Number, typing.Sequence[numbers.Number]
    ] = None

    scales: typing.Sequence[
        typing.Sequence[numbers.Number]
    ] = dataclasses.field(default_factory=lambda: [er_constants.DIATONIC_SCALE])
    # QUESTION is there a way to implement octave equivalence settings for
    #   chords here as well as for consonant_chords?
    # TODO if chords is empty then skip all chord-related behavior?
    chords: typing.Sequence[
        typing.Sequence[numbers.Number]
    ] = dataclasses.field(default_factory=lambda: [er_constants.MAJOR_TRIAD])

    ###################################################################
    # Midi settings

    voices_separate_tracks: bool = True
    choirs_separate_tracks: bool = True
    choirs_separate_channels: bool = True
    write_program_changes: bool = True

    # humanize: boolean.
    # humanize_parameters: dict where each value should be a
    #   number between 0 and 1, where 0 is no humanization and 1
    #   is "extreme" humanization (which will likely not sound especially "human").
    #       dict keys:
    #           - "attack": note attack position, where 1 is a quarter-note.
    #           - "dur": note dur position, where 1 is a quarter-note.
    #           - "velocity": scale the velocity by 1 +- this amount.
    #           - "tuning": tuning, only implemented for non-12-tet.
    #               Semitone is 1.

    humanize: bool = True
    humanize_attack: float = 0.0
    humanize_dur: float = 0.0
    humanize_velocity: float = 0.1
    humanize_tuning: float = 0.0

    # logic_type_pitch_bend: if True, writes pitch bend messages
    #   according to a scheme that aims to make files that I can use in
    #   Logic. In order to avoid pitch-bend latency problems, as well as
    #   audible bends during the release tails of notes, the notes (and
    #   associated pitch-bend events) loop through a number of channels
    #   (set with num_channels_pitch_bend_loop).
    # pitch_bend_time_prop: if logic_type_pitch_bend is true, the
    #   proportion of the time since the last note on this channel to
    #   place the pitch bend message. Should probably be more than half
    #   to avoid bending the release of the previous pitch.

    logic_type_pitch_bend: bool = True  # TODO doc this and following params
    num_channels_pitch_bend_loop: int = 9
    pitch_bend_time_prop: numbers.Number = 2 / 3

    ###################################################################
    # Tuning settings

    # integers_in_12_tet: if True, then any pitch materials
    #   indicated as integers (e.g., max_interval, scales...)
    #   will be intrepreted as 12-tet intervals which will be
    #   approximated in the given temperament (if not 12-tet).

    integers_in_12_tet: bool = False

    ###################################################################
    # Voice-leading settings
    #
    #       These settings govern how the initial pattern is voice-led
    #       through subsequent harmonies.

    # parallel_voice_leading: boolean. If true, each harmony is
    #   voice-led in pure (generic) parallel motion.
    # parallel_direction: integ Governs parallel_voice_leading.
    #   If positive, then the parallel voice-leading will be upwards.
    #   If negative, the voice-leading will be downwards. If 0, then
    #   the voice-leading will be upwards or downwards, whichever is
    #   a smaller interval.

    parallel_voice_leading: bool = False
    parallel_direction: int = 0

    voice_lead_chord_tones: bool = True

    # preserve_root_in_bass: string. Controls whether the appearances
    #   of the root in the bass are preserved when voice-leading the
    #   initial pattern to subsequent harmonies. Possible values:
    #       - "lowest": only the lowest sounding occurrences of
    #           the root on each harmony are preserved (so if, e.g.,
    #           C2 and C3 both occur, only the note that was C2 will
    #           be preserved when voice-led to the next chord, while
    #           C3 will proceed by efficient voice-leading like all
    #           other pitches).
    #       - "all": all occurrences of the root of each harmony
    #           are preserved.
    #       - "none": the root is voice-led like any other pitch.

    preserve_root_in_bass: str = "lowest"

    # extend_bass_range_for_roots: numb If the lowest octave of the
    #   root sounding in the bass voice is not the lowest pitch during
    #   that harmony, it will be transposed an octave downwards, if this
    #   octave transposition lies within this extended range. To disable
    #   this behaviour set to 0.

    extend_bass_range_for_roots: numbers.Number = 0

    # constrain_voice_leading_to_ranges: True. If False, then
    #   voice-leadings may exceed the given voice ranges after the
    #   initial pattern is complete.
    # vl_maintain_all: bool. If True, then other parameters
    #   beginning "vl_maintain" are all set to true.
    # vl_maintain_consonance: if false, then
    #   voice-leadings after the initial pattern will not be checked for
    #   consonance.
    # allow_flexible_voice_leading: if true, then the voice-leading
    #   of harmonies after the initial pattern will be allowed to change
    #   in the middle of the harmony.

    constrain_voice_leading_to_ranges: bool = False
    allow_flexible_voice_leading: bool = True
    vl_maintain_consonance: bool = True
    vl_maintain_limit_intervals: bool = True
    # TODO warning if vl_maintain_limit_intervals and polyphonic voice
    vl_maintain_forbidden_intervals: bool = True

    ###################################################################
    # Chord tones settings
    #
    # Parameters that begin "force_chord_tone" (though not
    #   "force_non_chord_tone") apply regardless of whether chord_tone_selection
    #   is true. Other chord_tone settings modify the behaviour activated
    #   by chord_tone_selection.

    # chord_tone_and_root_disable: disables all chord-tone and root
    #   specific behaviour in the script.
    # chord_tone_selection: boolean. If true, then the script will use
    #   a probability function (some of whose parameters can be set below)
    #   to select whether each pitch should be a chord tone.
    #       - Note that not all chord tone behaviour is controlled
    #         by this setting, howev Some settings (such as those
    #         that begin "force_chord_tone") apply regardless. To disable
    #         all chord tone behaviour, use chord_tone_and_root_disable.

    chord_tone_and_root_disable: bool = False
    chord_tone_selection: bool = True

    # chord_tone_prob_func can take the following values:
    #       - "quadratic": probability of a non-chord tone falls
    #           quadratically
    #       - "linear": probability of a non-chord tone falls
    #           linearly
    # max_n_between_chord_tones: int. Sets the number of non-chord
    #   tones after which the probability of a chord-tone is 1.
    # min_prob_chord_tone: float. Sets the probability of a chord-tone
    #   immediately following another chord-tone.
    # force_non_chord_tones: boolean. If true, then if the chord-tone
    #   probability function returns false, the pitch is forced to be
    #   a non-chord tone. Otherwise it is selected from the entire scale
    #   (chord tones and non-chord tones).
    #       - Note that the actual probabilities realized in the music
    #         will likely vary somewhat. This is because the algorithm
    #         will backtrack if it fails to find any pitches that works,
    #         and once it has exhausted the chord tones (if it has
    #         selected a chord tone) it will turn to the non-chord tones,
    #         and vice versa.

    chord_tone_prob_func: str = "linear"
    max_n_between_chord_tones: int = 4
    min_prob_chord_tone: float = 0.25
    force_non_chord_tones: bool = False

    # scale_chord_tone_prob_by_dur: boolean. If true,
    #   len_to_force_chord_tone must be set to a non-zero value.
    # len_to_force_chord_tone: note values this long or longer will be
    #   forced to be chord tones
    # scale_short_chord_tones_down: boolean. If true, then the chord
    #   tone probability of notes shorter than scale_chord_tone_neutral_dur
    #   will be reduced. If false, they are left untouched. (Strange results
    #   may occur if this parameter is true and so is force_non_chord_tones.)
    #

    len_to_force_chord_tone: int = 2
    scale_chord_tone_prob_by_dur: bool = True
    scale_chord_tone_neutral_dur: numbers.Number = 0.5
    scale_short_chord_tones_down: bool = True

    # chord_tone_before_rests: numb If chord_tone_selection is true,
    #   then rests of this length or greater will always be preceded by a
    #   chord tone.

    chord_tone_before_rests: typing.Union[
        numbers.Number, typing.Sequence[numbers.Number]
    ] = 0.26

    # TODO what about chord tone *after* rests?

    # chord_tones_no_diss_treatment: boolean, or list of booleans. If
    #   true, then chord tones are exempted from the conditions of dissonance
    #   treatment. (However, dissonances sounding *against* these chord
    #   tones are still subject to the rules of dissonance treatment.)

    chord_tones_no_diss_treatment: typing.Union[
        bool, typing.Sequence[bool]
    ] = True

    # force_chord_tone: string. Possible values:
    #       "global_first_beat": forces chord tone on attacks on the global
    #            first beat (but does not force an attack on the global
    #            first beat).
    #       "global_first_note": forces chord tones on the first note to
    #           sound in each voice.
    #       "first_beat": forces chord tones on attacks on the first beat
    #           of each harmony of the initial pattern (but does not force
    #           attacks on the first beat of each harmony).
    #       "first_note": forces chord tones on the first note of each harmony
    #           in each voice.
    #       "none": does not force any chord tones.

    force_chord_tone: str = "none"

    chord_tones_sync_attack_in_all_voices: bool = False

    # force_root_in_bass: string. Possible values are below, they
    #   work the same way as for force_chord_string above.
    #       - "first_beat"
    #       - "first_note"
    #       - "global_first_beat"
    #       - "global_first_note"
    #       - "none"

    force_root_in_bass: str = "none"

    ###################################################################
    # Melody settings

    # control_melodic_intervals: boolean. If true, smaller intervals
    #   will be more probable than larger intervals within the range
    #   of each voice.

    control_melodic_intervals: bool = True

    # control_coefficient: if control_melodic_intervals is true,
    #   then control_coefficient adjusts how strong the weighting
    #   towards smaller intervals is. It can take any value > 0; greater
    #   values mean larger intervals are relatively more likely. A good
    #   range of values is 0 - 10.

    control_coefficient: numbers.Number = 1

    # unison_weighted_as: if control_melodic_intervals is true, then
    #   we have to tell the algorithm how to weight melodic unisons,
    #   because we usually don't want them to be the most common melodic
    #   interval. Unisons will be weighted the same as whichever generic
    #   interval this variable is assigned to.
    #   (If you *DO* want unisons to be the most common melodic interval,
    #   set to GENERIC_UNISON -- you can't use UNISON because that's
    #   a just interval constant.)

    unison_weighted_as: int = er_constants.FIFTH

    # max_interval: int or float, or list thereof. If zero, does not apply.
    #   If positive, indicates a scalar (i.e., generic) interval. If
    #   negative, indicates a specific interval (in which case it can be a
    #   float to indicate a just interval which will be tempered in
    #   pre-processing).
    # max_interval_for_non_chord_tones: int or float, or list thereof.
    #   Works in the same way as max_interval, but only applies to
    #   non-chord tones. If given a value of 1, can be used to apply a
    #   sort of primitive dissonance treatment. It can, however, also
    #   be given a value *larger* than max_interval.
    # min_interval: int or float, or list thereof.
    # min_interval_for_non_chord_tones: int or float, or list thereof.
    #       - the minimum interval settings work in the same sort of way as
    #           the maximum interval settings.

    # LONGTERM min rest value across which limit intervals do not apply
    # LONGTERM avoid enforcing limit intervals with voice-led root

    max_interval: typing.Union[
        numbers.Number, typing.Sequence[numbers.Number]
    ] = -er_constants.OCTAVE
    max_interval_for_non_chord_tones: typing.Union[
        numbers.Number, typing.Sequence[numbers.Number]
    ] = -er_constants.OCTAVE
    min_interval: typing.Union[
        numbers.Number, typing.Sequence[numbers.Number]
    ] = 0
    min_interval_for_non_chord_tones: typing.Union[
        numbers.Number, typing.Sequence[numbers.Number]
    ] = 0

    # force_repeated_notes: boolean.
    # max_repeated_notes: integ If force_repeated_notes is true,
    #   this parameter is ignored.

    force_repeated_notes: bool = False
    max_repeated_notes: int = 1

    # max_alternations: int, or a list of ints. Sets the maximum number
    #   of alternations (repetitions of two pitches) in each voice. "One
    #   alternation" is two pitches (e.g., A, B), and "two alternations"
    #   is four pitches (e.g., A, B, A, B). If set to two, then the sequence
    #   "A, B, A, B, A" is allowed, just not "A, B, A, B, A, B" (or longer).
    #   To disable, set to 0.

    max_alternations: typing.Union[int, typing.Sequence[int]] = 2

    # prohibit_parallels: list of numbers. Will be treated as octave-
    #   equivalent intervals. The obvious use is to prohibit parallel octaves,
    #   but you can put any kind of interval you like.

    prohibit_parallels: typing.Sequence[numbers.Number] = (er_constants.OCTAVE,)

    # antiparallels: boolean. If true, then antiparallel versions of the
    #   the intervals in prohibit_parallels are forbidden as well. (E.g.,
    #   octave to unison or octave to fifteenth.)

    antiparallels: bool = True

    # force_parallel_motion: a string, or a dictionary of tuples of ints
    #   (indicating voices) and strings.
    #       - "within_harmonies"
    #       - "global" (not implemented yet)
    #       - "false"
    #    ** The functioning of the parallel motion is a bit specific.
    #       It looks at the last melodic interval in the leader voice,
    #       and adds the same melodic interval in the follower voice.
    #       There may have been other notes in the follower voice since
    #       the previous note in the leader voice, in which case the
    #       parallel harmonic intervals will be the interval formed by
    #       the last note in the follower voice.
    #       MAYBE think about other types of parallel motion (e.g.,
    #       choosing a generic harmonic interval and maintaining it)
    # MAYBE implement forbidden parallel intervals
    # MAYBE make this interact with consonance settings better

    force_parallel_motion = "false"  # TODO doc etc.
    avoid_octaves_between_parallel_voices = True  # not implemented

    ###################################################################
    # Consonance and dissonance settings

    # consonance_type takes the following two values:
    #       "pairwise": all pairs of voices are checked against
    #           the list in consonances
    #       "chordwise": all voices are checked to see if they
    #           belong to one of the chords in consonant_chords

    consonance_type: str = "pairwise"

    # consonance_treatment can take the following three values:
    #     "all_attacks": all simultaneously attacked pitches
    #           are consonant with one anoth
    #     "all_durs": each pitch is consonant with all other
    #           pitches sounding during its duration.
    #     "none": no consonance treatment.
    # consonance_modulo: number, or list of numbers, or list of list of
    #   numbers. If 0, does not apply. Otherwise, only attack_times that are
    #   0 modulo this setting will have
    #   consonance settings applied. If a list, then the modulo is
    #   "cumulative" (see elsewhere # TODO explain this). If a list of
    #   lists, each list applies to an individual voice.
    consonance_treatment: str = "all_attacks"
    # MAYBE all modulos have boolean to be truncated by initial_pattern_len?
    consonance_modulo: typing.Union[
        numbers.Number,
        typing.Sequence[numbers.Number],
        typing.Sequence[typing.Sequence[numbers.Number]],
    ] = 0
    min_dur_for_cons_treatment: numbers.Number = 0

    # forbidden_interval_classes: a list. The (harmonic) intervals in
    #   this list will be entirely avoided, regardless of consonance
    #   settings. (At least in the initial pattern. Whether this setting
    #   persists afterwards depends on
    #   vl_maintain_consonance)
    # forbidden_interval_modulo: works same as consonance_modulo.

    forbidden_interval_classes: typing.Sequence[numbers.Number] = (0,)
    forbidden_interval_modulo = [2]

    # exclude_augmented_triad: because all the pairwise intervals of
    #   the 12-tet augmented triad are consonant, we need to explicitly
    #   exclude it. Only has any effect if consonance_type is "pairwise".

    exclude_augmented_triad: bool = True

    # consonances: a list, for pairwise consonance treatment.
    #   Strictly speaking, just provides a list of the allowed intervals,
    #   which don't actually have to be (conventionally) consonant.
    # consonant_chords: a list, for "chordwise" consonance treatment.
    # invert_consonances: if true, inverts the list in consonances.
    #   This permits "dissonant counterpoint", etc. Only has an effect in
    #   pairwise consonance treatment.

    consonances: typing.Sequence[numbers.Number] = er_constants.CONSONANCES
    invert_consonances: bool = False
    consonant_chords: typing.Sequence[typing.Sequence[numbers.Number]] = (
        er_constants.MAJOR_TRIAD,
        er_constants.MINOR_TRIAD,
    )
    # chord_octave_equi_type: string. Governs the interpretation of
    #   the chords in consonant_chords. Can take the following values:
    #
    #   "all": The usual setting. All octave equivalence and octave
    #       permutations are allowed.
    #   "bass": all octave equivalence and octave permutations are allowed
    #       except that the bass note is preserved.
    #   "order": octave equivalence is allowed but notes must be in the
    #       order listed. (Where "order" means octave order, not voice
    #       ord)
    #   "none": no octave equivalence, in thse sense that (C3, E4, G4) is
    #       not considered the same as (C4, E4, G4) because of the tenth/
    #       third. Nevertheless, transpositional equivalence still applies,
    #       including when the interval of transposition is an octave,
    #       so (C3, E3, G3) will match (C4, E4, G4). The relevant order is
    #       octave order, not voice order, so (C4, G4, E4) will also match
    #       (C3, E3, G3).

    chord_octave_equi_type: str = "all"

    # chord_permit_doublings:
    #   "all": permit any and all doublings.
    #   "complete": doublings only permitted after the chord is complete.
    #   "none": no doublings permitted.

    chord_permit_doublings: str = "all"

    ###################################################################
    # Rhythm settings.
    # Possible values for rhythmic_unison:
    #       - True: all voices in rhythmic unison
    #       - False: no rhythmic unison
    #       - list of tuples: voices in each list will be in rhythmic
    #           unison. Any voices not present in the list will be
    #           constructed as usual. Each tuple should be in
    #           ascending order, regardless of voice_ord
    #           The rhythmic parameters used for constructing the rhythm
    #           will be those of the first listed voice. If the bass
    #           (voice 0) is in any of these tuples, it should be listed
    #           first.
    #           ** This behaviour can have the following consequence:
    #               if, for instance, the rhythmic_unison tuples are
    #               [(0, 1), (2, 3)] and a parameter such as
    #               attack_density is [0.5, 0.3], the second
    #               value of attack_density will never be used,
    #               because the first voices of the rhythmic_unison
    #               tuples are 0 and 2 (which, % the length of
    #               attack_density, is 0). In this situation it
    #               is necessary to insert a dummy value (e.g.,
    #               [0.5, 0.5, 0.3]) in order to apply a parameter to
    #               the second rhythmic_unison tuple.
    # rhythmic_quasi_unison: a boolean, or a list of tuples. If a pair of
    #   voices are in rhythmic unison then their value for rhythmic quasi-
    #   unison is ignored.
    # hocketing: a boolean, or a list of tuples. Tuples of the form
    #   (0, 1, 2) mean that voice 1 will be constructed in hocket with voice
    #   0, and voice 2 in hocket with voice 0 and 1. Tuples of the form
    #   (0, 1), and (1, 2), in contrast, mean that voice 1 will be constructed
    #   in hocket with voice 0 but voice 2 will be constructed in hocket
    #   with voice 1 (and not voice 0).

    rhythmic_unison: typing.Union[
        bool, typing.Sequence[typing.Sequence[int]]
    ] = False
    rhythmic_quasi_unison: typing.Union[
        bool, typing.Sequence[typing.Sequence[int]]
    ] = False  # not implemented for cont_rhythms
    hocketing: typing.Union[bool, typing.Sequence[typing.Sequence[int]]] = False

    # rhythmic_quasi_unison_constrain: boolean. If true and
    #   rhythmic_quasi_unison is true, then:
    #       - if the follower voice has a smaller attack density
    #           than the leader, it will be constrained to not contain
    #           any durations that lie outside of the durations of
    #           the lead
    #       - if the follower has a greater attack density
    #           than the leader, it will be constrained to have
    #           all its attacks occur during the durations of the
    #           leader, if possible.

    rhythmic_quasi_unison_constrain: bool = False

    # cont_rhythms: string. Can take the following values:
    #       "all": all voices have an (individually generated)
    #           continuous rhythm.
    #       "grid": all voices share a continuous-rhythm grid.
    #       "none": continuous rhythms off.
    # num_vars: int, or list of ints. Number of variations (where 1 is the
    #   the "theme") for continuous rhythm (or grid) to undergo. If negative,
    #   will be set to fill the complete score.

    cont_rhythms: str = "none"
    # TODO add obligatory_beats to grid
    num_vars: typing.Union[int, typing.Sequence[int]] = 1  # TODO doc
    vary_rhythm_consistently: bool = True  # TODO doc
    # cont_var_increment is multiplied by the number of beats
    cont_var_increment: numbers.Number = 0.1  # TODO doc
    super_pattern_reps_cont_var: bool = True  # TODO doc

    # rhythms_specified_in_midi: string. Specifies the path to a
    #   a midi file which will be used to construct the rhythms
    #   for the output. rhythm_len and/or pattern_len must
    #   still be set explicitly above. If num_voices is greater
    #   than the number of tracks in the input midi file, then
    #   the rhythms will loop through the tracks. If the number of
    #   tracks in the input midi file is greater than num_voices,
    #   the excess tracks will be ignored.
    #   To disable, use an empty string. If enabled, all other rhythm
    #   settings are ignored, except for overlap.
    # rhythms_in_midi_reverse_voices: boolean. The convention in this
    #   program is for the bass voice to be track 0. On the other hand, in
    #   scores (e.g., made with Sibelius), the convention is for the bass
    #   to be the lowest (e.g., highest-numbered) track. If the input file
    #   was made with this latter score-order convention, set this
    #   boolean to true.

    rhythms_specified_in_midi: str = ""
    rhythms_in_midi_reverse_voices: bool = False

    # All the following rhythmic parameters can either be a number or a
    #   list of numbers. A single number applies to all voices; a list
    #   applies to each voice individually, modulo the length of the list.
    # attack_density: a float from 0 to 1.0, or an int, or a list of
    #   floats and/or ints. Floats represent a proportion of the available
    #   attacks to be filled; integers represent a literal number of attacks.
    #   Any negative values will be replaced with random values.
    # dur_density: a float from 0 to 1.0, or a list of floats.
    #   Any negative values will be replaced with random values.
    # attack_subdivision, dur_subdivision, and min_dur should
    #   be numbers, or a list of numbers. If either of the latter are
    #   0, they wil be set to the value of attack_subdivision.
    # min_dur: if a fraction or float, then specifies a proportion of
    #   a quarter note. If an int, specifies a duration in milliseconds
    #   (which is converted to a note value according to the first tempo in
    #   tempo). If 0, will be set to the value of attack_subdivision.
    # obligatory_attacks: a list, or a list of lists. Zero-indexed.
    # obligatory_attacks_modulo: an number, or list thereof.

    attack_density: typing.Union[
        typing.Union[float, int], typing.Sequence[typing.Union[float, int]]
    ] = 0.5
    dur_density: typing.Union[float, typing.Sequence[float]] = 1.0
    attack_subdivision: typing.Union[
        numbers.Number, typing.Sequence[numbers.Number]
    ] = Fraction(1, 4)
    sub_subdivisions: typing.Union[
        int, typing.Sequence[typing.Union[int, typing.Sequence[int]]],
    ] = 1
    dur_subdivision: typing.Union[
        numbers.Number, typing.Sequence[numbers.Number]
    ] = 0
    min_dur: typing.Union[
        numbers.Number, typing.Sequence[numbers.Number]
    ] = 0  # TODO raise error if min_dur is empty,
    # or other settings that cannot be empty are empty?
    obligatory_attacks: typing.Union[
        typing.Sequence[numbers.Number],
        typing.Sequence[typing.Sequence[numbers.Number]],
    ] = ()
    obligatory_attacks_modulo: typing.Union[
        numbers.Number, typing.Sequence[numbers.Number]
    ] = 4

    # comma_position: string, int, or list of strings and/or ints. If
    #   the length of a rhythm is not divisible by the attack subdivision
    #   (e.g., rhythm length of 3 and an attack subdivision of 2/3), then
    #   there will be a "comma" left over that the attacks do not fill. This
    #   setting controls the position of any such comma. Possible values:
    #       - "end": comma is placed at the end of the rhythm. (Default.
    #           If an empty list or string, it will be assigned this value.)
    #       - "anywhere": the comma is placed randomly anywhere before,
    #           after, or during the rhythm.
    #       - "beginning": comma is placed at the beginning of the rhythm,
    #           before any notes.
    #       - "middle": comma is placed randomly in the middle of the
    #           rhythm.
    #       - int: specify the index at which to place the comma.

    comma_position: typing.Union[
        str, int, typing.Sequence[typing.Union[str, int]]
    ] = "end"

    # overlap: boolean. If true, then the final durations of each
    #   pattern repetition can overlap with the first durations of
    #   the next. If false, then no pattern overlaps.

    overlap: bool = True

    ###################################################################
    # Choir settings

    # choirs: a list, populated with:
    #       - ints corresponding to GM midi instruments.
    #           - or -
    #       - a tuple of:
    #           - a list of GM midi instruments (from low to high)
    #           - a split point (or list thereof) to switch between
    #               these (so one can e.g., combine cellos and violins)
    #   To indicate GM programs, one can use constants provided at end of file.
    # choir_assignments: a tuple of ints assigning each voice to
    #   the given index in choir_programs. Ignored if
    #   randomly_distribute_between_choirs is true.

    choirs: typing.Sequence[
        typing.Union[
            int,
            typing.Tuple[
                typing.Sequence[int], typing.Union[int, typing.Sequence[int]]
            ],
        ]
    ] = (
        er_constants.MARIMBA,
        er_constants.VIBRAPHONE,
        er_constants.ELECTRIC_PIANO,
        er_constants.GUITAR,
    )
    choir_assignments: typing.Sequence[int] = None
    randomly_distribute_between_choirs: bool = False  # TODO doc

    # length_choir_segments: sets the duration for each random choir
    #   assignment. If negative, each voice is permanently assigned to
    #   a choir. (Ignored if randomly_distribute_between choirs is
    #   false.)
    # length_choir_loop: sets the length of the loop of choir assignments.
    #   Short values will be audible loops, while longer values are likely
    #   to be inaudible as loops. If negative, then no loop.

    length_choir_segments: numbers.Number = 1
    length_choir_loop: numbers.Number = 0
    choir_segments_dovetail: bool = False

    # max_consec_seg_from_same_choir: int.
    # all_voices_from_different_choirs : boolean.
    # each_choir_combination_only_once: boolean.

    max_consec_seg_from_same_choir: int = 0
    all_voices_from_different_choirs: bool = False
    each_choir_combination_only_once: bool = False

    ###################################################################
    # Transpose settings

    # transpose: boolean. Toggles transposition.
    # transpose_type: str.
    #       "generic"
    #       "specific"
    # transpose_len: a number, or a list of numbers to be cycled through.
    # transpose_intervals: a single number, or a list. If an empty list,
    #   a transpose interval is chosen at random. If transpose_type is
    #   "generic", then must be an int. If "specific", a float is a just
    #   interval while an int is a tempered interval.
    # cumulative_max_transpose_interval: a numb Inclusive of the given
    #   interval.
    # transpose_before_repeat: boolean. If true, the transposition will be
    #   applied to the super_pattern before repeating it. If false, the
    #   transposition will be applied to the complete output, after repeating
    #   the super pattern.

    transpose: bool = False  # TODO doc
    transpose_type: str = "generic"  # TODO doc
    transpose_len: typing.Union[
        numbers.Number, typing.Sequence[numbers.Number]
    ] = 2  # TODO doc
    transpose_intervals: typing.Union[
        numbers.Number, typing.Sequence[numbers.Number]
    ] = 3  # TODO doc
    cumulative_max_transpose_interval: numbers.Number = 5  # TODO doc
    transpose_before_repeat: bool = False  # TODO doc

    ###################################################################
    # Tempo settings

    # tempo: number, or list of numbers. List of tempos. Will be looped
    #   through if necessary. If an empty list, tempos will be randomly
    #   generated.
    # tempo_len: number, or list of numbers. The length of each tempo
    #   segment. Will be looped through if necessary. If 0, then the
    #   first tempo in tempo applies to the whole file.
    # tempo_bounds: provides the (inclusive) upper and lower bounds
    #   for randomly generated tempi.
    # TODO debug tempos
    tempo: typing.Union[numbers.Number, typing.Sequence[numbers.Number]] = 120
    tempo_len: typing.Union[numbers.Number, typing.Sequence[numbers.Number]] = 0
    tempo_bounds: typing.Tuple[numbers.Number, numbers.Number] = (
        80,
        144,
    )

    # the following list gives the indexes of harmonies at which to rest
    # to the original spacing of the chord (this effects a parallel voice
    # leading from harmony 0 to the harmony in question;).

    # TODO update to effect a voice leading from harmony_n of the harmonies
    # in the first pattern (which isn't necessarily 0))
    #       (use a dict)

    reset_to_original_voicing: typing.Sequence[int] = ()  # TODO doc

    ###################################################################
    # Randomization settings

    exclude_from_randomization = [
        "pattern_len",
        "harmony_len",
        # "interval_cycle",
        "truncate_patterns",
        # "chords",
        "tempo",
    ]  # TODO doc ?

    ###################################################################
    # Default settings

    # TODO add below to above definitions, then delete
    # # json_defaults: if a parameter is not found in a JSON file,
    # #   look in this dictionary for the default value. If it is not
    # #   found, the value set above will be used.
    # #   Ideally, I should keep this dictionary updated with sensible
    # #   values each time I introduce new parameters.
    # json_defaults = {
    #     "hard_pitch_loop": False,
    #     "time_sig": None,
    #     "max_super_pattern_len": 128,
    #     "allow_voice_crossings": True,
    #     "interval_cycle": [],
    #     "constrain_voice_leading_to_ranges": False,
    #     "vl_maintain_all": False,
    #     "vl_maintain_consonance": False,
    #     "vl_maintain_limit_intervals": False,
    #     "vl_maintain_forbidden_intervals": False,
    #     "chord_tone_and_root_disable": False,
    #     "scale_chord_tone_prob_by_dur": False,
    #     "len_to_force_chord_tone": 2,
    #     "scale_chord_tone_neutral_dur": 0.5,
    #     "scale_short_chord_tones_down": False,
    #     "chord_tones_no_diss_treatment": False,
    #     "max_interval_for_non_chord_tones": 5, # Ideally, get from max_interval
    #     "min_interval": 0,
    #     "min_interval_for_non_chord_tones": 0,
    #     "min_dur_for_cons_treatment": 0,
    #     "chord_octave_equi_type": "all",
    #     "chord_permit_doublings": "all",
    #     "cont_rhythms": "none",
    #     "num_vars": 8,
    #     "vary_rhythm_consistently": True,
    #     "cont_var_increment": 0.15,
    #     "super_pattern_reps_cont_var": True,
    #     "rhythms_in_midi_reverse_voices": True,
    #     "sub_subdivisions": (1,),
    #     "choir_segments_dovetail": False,
    #     "max_consec_seg_from_same_choir": 2,
    #     "transpose_type": "specific",
    #     "tempo_len": 0,
    #     "consonance_modulo": 0,
    #     "forbidden_interval_modulo": 0,
    # }

    # End of settings
    ###################################################################
