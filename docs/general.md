# Efficient rhythms

I wrote this script for use as a tool in musical composition. The basic way that it works goes as follows:

- first, the script generates an initial rhythm
- next, the script creates an "initial pattern" by filling the first occurrence of this rhythm with pitches
- finally, the script repeats the initial pattern over any subsequent harmonies, transforming (or "voice-leading", in musical parlance) the pattern as necessary to fit the new harmonies. The voice-leading is "efficient", in the sense of moving the voices as little as possible.

There are many parameters governing each step in this process. The name of the script comes from the fact that it begins with a **rhythm** and then voice-leads it **efficiently**.

Here are some examples of things I have made using this script:

<!-- TODO -->

(It isn't really intended to produce stand-alone compositions all by itself.)

## How it works (a longer explanation)

I will illustrate with the aid of a few examples.

Here, the initial pattern is two beats long---i.e., `pattern_len = 2`. Each harmony, however, is four beats (`harmony_len = 4`). Thus you can see that the pattern repeats twice on each harmony before being adjusted to fit the next harmony.

<!-- TODO notation; annotate -->
![pngs/example100001.png](Example 1 piano roll)

We can also set the length of the rhythm separately from the length of the pattern. Thus in the above example, `rhythm_len = 2` but `pattern_len = 4`. Thus, if you look and/or listen carefully, you'll hear that the same rhythm repeats twice on each harmony, but with different notes each time.

![pngs/example200001.png](Example 2 piano roll)

We aren't constrained, however, to have `pattern_len` be a whole multiple of `rhythm_len`. In the next example, `pattern_len` is still `4`, but `rhythm_len = 1.5`, so now every third time the rhythm occurs, it is truncated (this is a bit like the 3--3--2 *tresillo* pattern).

![pngs/example300001.png](Example 3 piano roll)

So far, we've always had the same settings in both voices. But we don't have to. In the next example, the bottom voice again has a `rhythm_len` of 1.5, but the top voice now has `rhythm_len = 2`.

![pngs/example400001.png](Example 4 piano roll)

We can also have different values of `pattern_len` in each voice, like in the following example. However, if we do so, the script has to work quite a bit harder...
<!-- TODO why? -->

![pngs/example500001.png](Example 5 piano roll)

Above, when one pattern didn't line up with the other, we truncated it... <!-- TODO finish -->

![pngs/example600001.png](Example 6 piano roll)

Also, note that up until now, `harmony_len` has always been at least as long as `pattern_len`. But there's no constraint that that has to be the case.

![pngs/example700001.png](Example 7 piano roll)

The script works as follows:
- an "initial_pattern" is created.
    - the length of the initial_pattern is pattern_len in each voice (it is
        not necessarily the same length in each voice)

## Music-theoretic considerations

### "Generic" and "specific" intervals

In the settings below, I sometimes use the terms "generic" or "specific"
in reference to intervals. These terms come from academic music theory
(e.g., Clough and Myerson 1985).

A "generic" interval defines an interval with respect to some reference
scale, by counting the number of scale steps the interval contains.
They might also be called "scalar" intervals (using "scalar" in
a completely different sense from its linear algebra meaning).
"Specific" intervals define intervals "absolutely", by simply counting
the number of semitones the interval comprises, irrespective of
any reference scale.

In typical musical usage, "thirds", "fifths", and the like
refer to generic intervals: a third is the distance between any pitch
in a scale and the pitch two steps above or below it. (It would be
more practical to call a "third" a "second" but, unfortunately, this
usage has now been established for many centuries!) Depending on the
structure of the scale, and the location of the interval within it,
the exact pitch distance connoted by one and the same generic
interval may vary. For instance, in the C major scale, the third from
C to E is 4 semitones, but the third from D to F is 3 semitones. To
distinguish these cases, music theory has developed an armory of
interval "qualities" like "major", "minor", "diminished", and so on.
A generic interval together with a quality, like "minor third", is
somewhat like a specific interval, but it is not quite the same thing,
because there can be more than one generic interval + quality that
correspond to one specific interval. For example, both "minor thirds"
and "augmented seconds" comprise 3 semitones. (Thus, the mapping from
generic intervals with qualities to specific intervals is onto but not
one-to-one.)

### Specifying pitch materials

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


# Randomization

If the script is invoked with the "--random" or "-r" flag, then many settings will be randomly varied. The randomized settings will then be printed out so you can inspect them.

The parameters of the randomization (i.e., the possible values that each setting can receive and their respective probabilities) are hard-coded into the script. A longterm to-do is to allow the user to specify the parameters of randomization in the same way that other settings are specified. There is, however, a setting available to exclude specific settings from randomization: `exclude_from_randomization`.

These are the settings that by default are randomized:

<!-- Update dynamically? -->

```
num_voices
pattern_len
rhythm_len
pitch_loop
harmony_len
truncate_patterns
voice_order_str
interval_cycle
chords
parallel_voice_leading
voice_lead_chord_tones
preserve_root_in_bass
chord_tone_and_root_disable
chord_tone_selection
force_chord_tone
chord_tones_sync_attack_in_all_voices
force_root_in_bass
prefer_small_melodic_intervals
force_repeated_notes
force_parallel_motion
consonance_treatment
cont_rhythms
vary_rhythm_consistently
rhythmic_unison
rhythmic_quasi_unison
hocketing
attack_density
dur_density
attack_subdivision
randomly_distribute_between_choirs
length_choir_segments
tempo
```

These are the settings that are not randomized (although note that it is possible to specify that some of these settings, such as `root_pcs`, be individually randomized):

```
tet
num_reps_super_pattern
existing_voices
existing_voices_offset
bass_in_existing_voice
existing_voices_repeat
existing_voices_transpose
existing_voices_erase_choirs
existing_voices_max_denominator
num_harmonies
hard_pitch_loop
time_sig
max_super_pattern_len
voice_ranges
allow_voice_crossings
scales_and_chords_specified_in_midi
root_pcs
scales
voices_separate_tracks
choirs_separate_tracks
choirs_separate_channels
write_program_changes
humanize
humanize_attack
humanize_dur
humanize_velocity
humanize_tuning
logic_type_pitch_bend
num_channels_pitch_bend_loop
pitch_bend_time_prop
integers_in_12_tet
parallel_direction
extend_bass_range_for_roots
constrain_voice_leading_to_ranges
allow_flexible_voice_leading
vl_maintain_consonance
vl_maintain_limit_intervals
vl_maintain_forbidden_intervals
chord_tone_prob_func
max_n_between_chord_tones
min_prob_chord_tone
try_to_force_non_chord_tones
len_to_force_chord_tone
scale_chord_tone_prob_by_dur
scale_chord_tone_neutral_dur
scale_short_chord_tones_down
chord_tone_before_rests
chord_tones_no_diss_treatment
prefer_small_melodic_intervals_coefficient
unison_weighted_as
max_interval
max_interval_for_non_chord_tones
min_interval
min_interval_for_non_chord_tones
max_repeated_notes
max_alternations
prohibit_parallels
antiparallels
consonance_type
consonance_modulo
min_dur_for_cons_treatment
forbidden_interval_classes
forbidden_interval_modulo
exclude_augmented_triad
consonances
invert_consonances
consonant_chords
chord_octave_equi_type
chord_permit_doublings
rhythmic_quasi_unison_constrain
num_cont_rhythm_vars
cont_var_increment
super_pattern_reps_cont_var
rhythms_specified_in_midi
rhythms_in_midi_reverse_voices
sub_subdivisions
dur_subdivision
min_dur
obligatory_attacks
obligatory_attacks_modulo
comma_position
overlap
choirs
choir_assignments
length_choir_loop
choir_segments_dovetail
max_consec_seg_from_same_choir
all_voices_from_different_choirs
each_choir_combination_only_once
transpose
transpose_type
transpose_len
transpose_intervals
cumulative_max_transpose_interval
transpose_before_repeat
tempo_len
tempo_bounds
initial_pattern_attempts
voice_leading_attempts
ask_for_more_attempts
max_available_pitch_materials_deadends
exclude_from_randomization
```

# Help, my script is failing!

A list of "permissive" settings.

If the script is failing with your supplied settings, consider applying
some of the following settings to increase the size of the search space:

```
constrain_voice_leading_to_ranges = False
allow_flexible_voice_leading = True
vl_maintain_consonance = False
vl_maintain_limit_intervals = False
vl_maintain_forbidden_intervals = False
```
TODO
