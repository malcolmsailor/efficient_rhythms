---
title: Efficient rhythms documentation
---
<!-- This file is in pandoc's markdown because that's what I'm familiar with. Then I convert it (with pandoc) to github-flavored markdown (since that displays better on github) and put the result in docs/general.md. -->

## Introduction

`efficient_rhythms` is a tool for musical composition. You can find it on Github at [`https://github.com/malcolmsailor/efficient_rhythms`](https://github.com/malcolmsailor/efficient_rhythms)

Here are a few examples of things I have made using it:

<iframe width="560" height="315" src="https://www.youtube.com/embed/YgAUskvRWPM" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>

`TODO add more videos here`

The gist of how the script works goes as follows:

- first it makes an initial **rhythmic** pattern.
- then it fills the rhythm with pitches.
- finally, it repeats the pattern, adjusting it **efficiently** to fit any chord changes (hence the name "efficient rhythms").

You can then hear the results as a midi file. See [How it works](#how-it-works) for a fuller explanation, with many examples. The script also provides a few tools (see [Filters and Transformers](#filters-and-transformers)) for reshaping the results.

## Installation

The script requires Python >= 3.8 and has the following Python dependencies:

- mido
- numpy
- pygame
- python-rtmidi
- sortedcontainers

These can be installed by running `pip3 install -r requirements.txt` in the script directory.

As far as installing the script itself goes, you can just clone the Github repository.

### Dependencies for music notation

If you want the script to output music notation, then the following must be in your path:

- convert (part of [ImageMagick](https://www.imagemagick.org/))
- [img2pdf](https://gitlab.mister-muffin.de/josch/img2pdf)
- [verovio](https://www.verovio.org/)

The first two can be installed as follows:

```
brew install imagemagick # replace "brew" with your system package manager if not on macOS
pip3 install img2pdf
```

Verovio installation instructions are [here](https://github.com/rism-ch/verovio/wiki/Building-instructions#command-line-tool).

## Quick start

To quickly try the script out, you can run it with the default settings:

`python3 efficient_rhythms.py`

You can also try running it with randomized settings, although be warned that the results are sometimes strange:

`python3 efficient_rhythms.py --random`

There are many configurable settings that shape the output. Full documentation is available in [`settings.html`](settings.html). But a gentler introduction is provided in the next section.

In general, custom settings are applied by putting them into a Python dictionary, saving them in a file, and then passing that file as an argument to the script with the `--settings` flag. For examples, see `docs/examples`. (A long-term goal for this project would be to provide a GUI or other more user-friendly interface.)

## How it works

The basic settings that control the script are

- `rhythm_len`: the length of the basic rhythm
- `pattern_len`: the length of the initial pattern
- `harmony_len`: the length of each harmony (i.e., chord)

For instance, in REF:example1, the initial pattern is two beats long (i.e., `pattern_len = 2`). Each harmony, however, is four beats (`harmony_len = 4`). Thus you can see that the pattern repeats twice on each harmony, and is then adjusted to fit the next harmony.[^example_settings]

[^example_settings]: You can find the settings files that generated all the examples in this section in the `docs/examples` folder. `docs/examples/example_base.py` is shared among each example. So you can build the first example with the command `python3 efficient_rhythms.py --settings docs/examples/example_base.py docs/examples/example1.py`; for subsequent examples, just replace `example1.py` with the appropriate file.

EXAMPLE:example1

(By the way, I made the piano-roll figures throughout this documentation with [midani](https://github.com/malcolmsailor/midani).)

Whenever `rhythm_len` is not set explicitly, it is implicitly assigned the value of `pattern_len`. So in the example above, `rhythm_len`  was implicitly assigned `2`. In REF:example2, in contrast, we set `pattern_len = 4`, but `rhythm_len = 2`. Thus, if you look and/or listen carefully, you'll find that the same rhythm repeats twice on each harmony, but with different notes each time---the entire pattern of pitches takes four beats to repeat, and by the time it does, its pitches are somewhat different, having been adjusted to the new harmony.[^parallel_fifths]

[^parallel_fifths]: The music-theoretically fastidious among you may have observed that these examples contain plentiful parallel fifths (for example, the first two sixteenth-notes in REF:example2). If desired, parallel fifths could be avoided by including `7` (i.e., the number of semitones in a perfect fifth) in the sequence provided to the setting `prohibit_parallels`.

EXAMPLE:example2

We aren't constrained to have `pattern_len` be a whole multiple of `rhythm_len`. In REF:example3, `pattern_len` is still `4`, but `rhythm_len = 1.5`, so now every third time the rhythm occurs, it is truncated (a bit like a 3--3--2 *tresillo* pattern).

EXAMPLE:example3

Up to now, we've always specified the same settings in both voices. But we need not do so! In REF:example4, the bottom voice again has `rhythm_len = 1.5`, but the top voice now has `rhythm_len = 2`.

EXAMPLE:example4

We can also have different values of `pattern_len` in each voice, as in REF:example5. However, if we do so, the script has to work quite a bit harder to find a solution. To help it do so, I made its task a little easier by changing  `consonance_treatment` from `"all_onsets"` to `"none"`. Thus whereas in the previous examples, the simultaneously onset notes all formed intervals like 3rds and fifths, in REF:example5, there are also dissonances like 7ths and 9ths.


EXAMPLE:example5

Up until now, whenever one pattern or rhythm didn't line up with the other, we have truncated the shorter one, so that subsequent repetitions began together in both voices. But the script doesn't require this. In REF:example6, I have changed `truncate_patterns` to `False`. Now the 1.5-beat pattern in the lower part isn't truncated after 4 beats. Instead, it is displaced relative to both the 4-beat pattern in the upper part, as well as the 4-beat harmony changes. (The two patterns finally come into sync after 12 beats, the least-common-multiple of 1.5 and 4.)

EXAMPLE:example6

Another feature of all the examples up to now is that `harmony_len` has always been at least as long as `pattern_len`. But there's no reason why this has to be so. In REF:example7, I've set `harmony_len = 2` but `pattern_len = 4` so that each pattern covers two harmonies.

EXAMPLE:example7

### Harmony

In the preceding sections, we looked at how to adjust the lengths of patterns, rhythms and harmonies. Now we'll see how to specify chords and scales to create harmonic progressions.[^harmony_example_settings]

[^harmony_example_settings]: The settings files that generated the examples in this section all begin with `harmony_example` and are found in the `docs/examples` folder. `docs/examples/harmony_example_base.py` is shared among each example. So you can build the first example with the command `python3 efficient_rhythms.py --settings docs/examples/harmony_example_base.py docs/examples/harmony_example1.py`.

The most straightforward way is to specify all chords and scales explicitly. As a first example, I've specified [one of the most (over?-)used chord progressions](https://youtu.be/5pidokakU4I) in pop music, the I-V-vi-IV progression, in C major. The results are in REF:harmony_example1. The relevant lines in `harmony_example1.py` are

```
"foot_pcs": ("C", "G", "A", "F"),
"chords": ("MAJOR_TRIAD", "MAJOR_TRIAD", "MINOR_TRIAD", "MAJOR_TRIAD"),
"scales": ("MAJOR_SCALE", "MIXOLYDIAN", "AEOLIAN", "LYDIAN"),
```

EXAMPLE:harmony_example1

There's a lot to explain here:

1. Strings like `"C"` and `"MAJOR_TRIAD"` name constants that are defined in `src\er_constants.py` and documented [here](constants.html). If you know any music theory, the meaning of the constants above shouldn't require any further explanation for now.
2. In this script, we call the main bass pitch of each chord its "foot". The main bass pitch is a little like the "root" of a chord, except that the main bass pitch doesn't have to be the root of a chord (as in the case of inverted chords).
3. Each foot is associated with the chord and the scale in the same serial position. Both the chord and the scale will be transposed so that they begin on the foot. Thus, there is a one-to-one correspondence between chords and scales (much like the "chord-scale" approach sometimes used in jazz pedagogy).

We can easily put the progression into another key by changing `foot_pcs`. For instance, here it is in E major:

```
"foot_pcs": ("E", "B", "C#", "A"),
"chords": ("MAJOR_TRIAD", "MAJOR_TRIAD", "MINOR_TRIAD", "MAJOR_TRIAD"),
"scales": ("MAJOR_SCALE", "MIXOLYDIAN", "AEOLIAN", "LYDIAN"),
```

There are no constraints on `foot_pcs`, so we can get a different progression by changing `foot_pcs` arbitrarily. For example, in REF:harmony_example2 I've changed the middle two members of `foot_pcs` to create a more chromatic progression:

```
"foot_pcs": ("E", "G", "D", "A"), # was ("E", "B", "C#", "A")
"chords": ("MAJOR_TRIAD", "MAJOR_TRIAD", "MINOR_TRIAD", "MAJOR_TRIAD"),
"scales": ("MAJOR_SCALE", "MIXOLYDIAN", "AEOLIAN", "LYDIAN"),
```

EXAMPLE:harmony_example2

There are, however, two important constraints on `chords` and `scales`.

1. All the items of `chords` must have the same number of pitch-classes, and all the items of `scales` must as well. This means, for example, you can't go from a major triad to a seventh chord, or from a major scale to a whole-tone scale. (You can, however, use scales or chords with any number of pitch-classes you like---as long as that number remains the same.)[^bijective]
2. Every scale must be a superset of the associated chord. So, for example
    - `"MAJOR_TRIAD"` will work with `"MAJOR_SCALE"`, `"MIXOLYDIAN"`, or any other scale that contains a major triad beginning on its first pitch
    - `"MAJOR_TRIAD"` will *not* work with `"AEOLIAN"`, `"DORIAN"`, etc., because these scales contain a minor triad beginning on their first pitch


[^bijective]: There is a technical reason for this constraint, (namely, that the script works by finding bijective voice-leadings between chords and scales), but in the longterm, I would very much like to remove it.

Both `chords` and `scales` will be looped through if they are shorter than `foot_pcs`. REF:harmony_example3 illustrates with the following short loop:

```
    "foot_pcs": ("E", "G"),
    "chords": ("MAJOR_TRIAD",), # the trailing commas before the parentheses
    "scales": ("MIXOLYDIAN",),  #   are necessary!
```

EXAMPLE:harmony_example3

`chords` and `scales` do not have to be the same length as REF:harmony_example4 demonstrates:

```
    "foot_pcs": ("E", "G", "E", "C"),
    "chords": ("MAJOR_TRIAD",),
    "scales": ("MIXOLYDIAN", "LYDIAN"),
```

EXAMPLE:harmony_example4

So far, the length of the progression has always been taken implicitly from the length of `foot_pcs`. But it is also possible to set the length of the progression explicitly, using `num_harmonies`, as in REF:harmony_example5. Doing so allows us to create "pedal points" on a repeated bass note:

```
    "num_harmonies": 4,
    "foot_pcs": ("D",),
    # This example also illustrates a strategy for simulating mixing seventh
    #   chords with triads, using incomplete seventh chords.
    "chords": ("MAJOR_7TH_NO5", "DOMINANT_7TH_NO3", "MAJOR_64", "MAJOR_63"),
    "scales": ("MAJOR_SCALE", "MIXOLYDIAN", "DORIAN", "AEOLIAN"),
```

EXAMPLE:harmony_example5

Another useful setting for creating harmonic progressions is `interval_cycle`. If we pass `interval_cycle` to the script, then any values of `foot_pcs` beyond the first are ignored. Instead, the progression of `foot_pcs` is created by repeatedly progressing upwards by `interval_cycle`. See REF:harmony_example6:

```
    "num_harmonies": 4,
    "interval_cycle": "PERFECT_4TH",
    "foot_pcs": ("Eb",),
    # The preceding three lines are equivalent to:
    #   `"foot_pcs": ("Eb", "Ab", "Db", "Gb")`
    "chords": ("MAJOR_TRIAD",),
    "scales": ("MAJOR_SCALE",),
```

EXAMPLE:harmony_example6

`interval_cycle` can also consist of more than one interval, as in REF:harmony_example7. (Note that, since the intervals in `interval_cycle` are always understood *upwards*, `"MINOR_6TH"` in this example is equivalent to a descending major third.)

```
{
    "num_harmonies": 4,
    "interval_cycle": ("PERFECT_4TH", "MINOR_6TH"),
    "foot_pcs": ("Eb",),
    # The preceding three lines are equivalent to:
    #   `"foot_pcs": ("Eb", "Ab", "E", "A")`
    "chords": ("MAJOR_TRIAD",),
    "scales": ("MAJOR_SCALE",),
}
```

EXAMPLE:harmony_example7

Before concluding this introduction to specifying harmonies, I should add a few words about what the script actually does with `chords` and `scales`.

- `scales` are used unconditionally: during each harmony, pitches are drawn exclusively from the associated scale. When a pattern is voice-led from one harmony to another, a bijective mapping is effected between the associated scales.
- the use of `chords` is more contingent. The most important relevant settings are
    - if `chord_tone_selection` is `True`, then when constructing the initial pattern, the script probabilistically decides whether each note should be a chord-tone (according to [parameters that you specify](settings.html#chord-tone-settings)).
    - if `voice_lead_chord_tones` is `True`, then when voice-leading the pattern over subsequent harmonies, the script will ensure that chord-tones are mapped to chord-tones (and non-chord-tones to non-chord-tones).

In the preceding examples of this section both `chord_tone_selection` and `voice_lead_chord_tones` have been `True`. As a contrasting illustration, REF:harmony_example8 repeats the settings of REF:harmony_example6, with the sole difference that `voice_lead_chord_tones` is now set to `False`. (Note, however, that the settings `force_foot_in_bass = True` and `extend_bass_range_for_foots = 7` in `examples/harmony_example_base.py` are still causing the foot of each scale/chord to sound on beat one of each harmony.)

EXAMPLE:harmony_example8

REF:harmony_example9 is similar, but with `chord_tone_selection = False` as well.

EXAMPLE:harmony_example9

### Specifying rhythms

Besides setting `rhythm_len` as we did [above](#how-it-works), there are many other ways of controlling the rhythms that are produced.[^rhythm_example_settings]

[^rhythm_example_settings]: The settings files that generated the examples in this section all begin with `rhythm_example` and are found in the `docs/examples` folder. `docs/examples/rhythm_example_base.py` is shared among each example. So you can build the first example with the command `python3 efficient_rhythms.py --settings docs/examples/rhythm_example_base.py docs/examples/rhythm_example1.py`.


To begin with, we have `onset_subdivision` and `onset_density`:

- `onset_subdivision` indicates the basic "grid" on which note onsets can take place, measured in quarter notes.
- `onset_density` indicates the proportion of grid points that should have an onset.

So for example, in REF:rhythm_example1, `"onset_subdivision" = 1/4` indicates a sixteenth-note grid, and `"onset_density" = 1.0` indicates that every point in the grid should have an onset, creating a *moto perpetuo* texture. (For clarity/brevity, this example has only one voice.)

```
{
"num_voices": 1,
"onset_density": 0.5,
"onset_subdivision": 1/4,
}
```

EXAMPLE:rhythm_example1

If we reduce `onset_density`, as in REF:rhythm_example2, the proportion of the sixteenth-grid that is filled with onsets will be correspondingly reduced.

```
{
    "num_voices": 1,
    "onset_density": 0.5,
    "onset_subdivision": 1 / 4,
}
```

EXAMPLE:rhythm_example2

Another important rhythmic parameter is `dur_density`. It specifies the proportion of time that should be filled by note durations, irrespective of how many onsets there are. So far we have left `dur_density` at the default value of `1.0`, which means that all notes last until the next onset in that voice. (In musical terms, all notes are *legato*.) If we decrease it to 0.75, as in REF:rhythm_example3, some of the notes will become shorter, so that 75% of the total time of the rhythm is filled by sounding notes.
```
{
    "num_voices": 1,
    "onset_density": 0.5,
    "dur_density": 0.75,
    "onset_subdivision": 1 / 4,
}}
```

EXAMPLE:rhythm_example3

To obtain a *staccato* effect, we can make `dur_density` still shorter, but to obtain *really* short notes, we may have to adjust `min_dur` as well, which sets the minimum duration of each pitch as well.
```
{
    "num_voices": 1,
    "onset_density": 0.5,
    "dur_density": 0.25,
    "min_dur": 1/8,
    "onset_subdivision": 1 / 4,
}
```

EXAMPLE:rhythm_example4

We can change `"onset_subdivision"` as well. For example, to have a grid of eighth-note triplets, we would set `"onset_subdivision" = 1/3`. And since computers have no problem with precise, strange rhythms, we could also set it to unusual values like `5/13` or `math.pi / 12`.[^Notation]

[^Notation]: However, we'll have to give up on representing these in conventional music notation. In fact, for the time being only duple note-values (i.e., eighth-notes, quarter-notes, and the like) can be exported to notation.

```
{
    "num_voices": 1,
    "onset_density": 0.75,
    "dur_density": 0.25,
    "min_dur": 1/8,
    "onset_subdivision": 3/ 13,
}
```

EXAMPLE:rhythm_example5

All of the settings we have been looking at so far are "per-voice", meaning that they can be set to a different value in each voice. If we set `onset_subdivision` to a different unusual value in each voice, we get a particularly chaotic effect. (I find that the chaos can be reined in a bit by setting `rhythm_len` to a short value, creating a brief rhythmic loop.)
```
{
    "rhythm_len": 1,
    "num_voices": 3,
    "onset_density": [0.25, 0.5, 0.75],
    "dur_density": [0.25, 0.5, 0.25],
    "min_dur": [0.25, 0.25, 1/8],
    "onset_subdivision": [3/ 13, 5/12, 6/11],
}
```

EXAMPLE:rhythm_example6

There are also a few settings that govern the relation between different voices. If `hocketing` is `True`, then, to the extent possible, the onsets of each voice will occur when there is no onset in any other voice. (In textures with many voices, it is also possible to assign specific pairs of voices to hocket with one another.)
```
{
    "num_voices": 2,
    "onset_density": 0.4,
    "dur_density": 0.4,
    "min_dur": 0.25,
    "onset_subdivision": 0.25,
    "hocketing": True,
}
```

EXAMPLE:rhythm_example7

Another setting that governs the rhythmic relation between voices is `rhythmic_unison`, which causes voices to have exactly the same rhythm. (Like `hocketing`, it can be provided a boolean, or a list of tuples of voices; see the settings documentation for more details.)
```
{
    "num_voices": 3,
    "rhythmic_unison": True,
    "onset_density": .7,
    "dur_density": 0.6,
    "min_dur": 0.25,
    "onset_subdivision": 1/4,
}
```

EXAMPLE:rhythm_example8

When `rhythmic_unison` is applied, rhythmic settings like `onset_density` only have any effect in the "leader" voice, whose rhythm is simply copied into the other voices. If we wanted to specify a different `onset_density` in a "follower" voice, it would be ignored. This situation would call for the related setting `rhythmic_quasi_unison`. When `rhythmic_quasi_unison` applies, then, instead of copying the "leader" rhythm into the "follower" voices, the onsets of the "follower" voices are constrained so far as possible to coincide with those of the "leader." In REF:rhythm_example9, the leader is the bass voice (midi guitar). The middle voice (midi piano) has a *lower* `onset_density`, and the top voice (midi electric piano) has a *higher* `onset_density`.

```
{
    "num_voices": 3,
    "rhythmic_quasi_unison": True,
    "onset_density": [0.5, 0.4, 0.6],
    "dur_density": [0.5, 0.4, 0.6],
    "min_dur": 0.25,
    "onset_subdivision": 1 / 4,
}
```

EXAMPLE:rhythm_example9

We can obtain more explicit control of the rhythms through the `obligatory_onsets` setting, which specifies a sequence of times at which the rhythms will be "obliged" to have a note onset. It's also necessary to specify `obligatory_onsets_modulo` in order to specify when these onsets should repeat (e.g., every two beats).

For example, in REF:rhythm_example10, I've set `obligatory_onsets` to `[0, 0.75, 1.5]` and `obligatory_onsets_modulo` to `2` in order to specify a *tresillo* 3--3--2 rhythm. Since the value of `onset_density` implies more than three onsets every two beats, additional onsets are added to the underlying scaffold supplied by the values in `obligatory_onsets`.

```
{
    "num_voices": 3,
    "obligatory_onsets": [0, 0.75, 1.5],
    "obligatory_onsets_modulo": 2,
    "onset_density": 0.5,
    "dur_density": 0.5,
    "min_dur": 0.25,
    "onset_subdivision": 0.25,
}
```

EXAMPLE:rhythm_example10

It is possible to specify an irregular grid upon which note onsets will take place using `sub_subdivisions`. This setting takes a sequence of integers and subdivides the grid specified by `onset_subdivision` into parts defined by the ratio of these integers. For example, in REF:rhythm_example11 below, `sub_subdivisions` is `[4,3]`, which creates an uneven "swing" feel where every first note is 4/3rds as long as every second note.[^To keep the number of total onsets consistent, you'll probably want to increase `onset_subdivision` by taking the value you otherwise would have chosen and multiplying it by the length of `sub_subdivisions`.] You'll notice that REF:rhythm_example11 is precisely the same as REF:rhythm_example1, except for the uneven rhythms.

```
{
    "num_voices": 1,
    "onset_density": 1.0,
    "onset_subdivision": 0.5,
    "sub_subdivisions": [4, 3],
}
```

EXAMPLE:rhythm_example11

I think, however, that it is more interesting to experiment with values of `sub_subdivisions` that are further from what a human would be likely to produce, as I have tried to do in REF:rhythm_example12.
```
{
    "num_voices": 3,
    "onset_density": 0.4,
    "onset_subdivision": 2,
    "sub_subdivisions": [12, 13, 11, 15, 17, 10],
    "obligatory_onsets": 0,
    "obligatory_onsets_modulo": 2,
    "hocketing": True,
}
```

EXAMPLE:rhythm_example12

<!-- If you're interested in exploring the script further, some next steps could be:

- tinkering with the example settings in `examples/`
- running the script with `--random`
- checking out the documentation in [`settings.html`](settings.html) -->



## Filters and transformers

`TODO`

<!--
## Randomization

If the script is invoked with the "--random" or "-r" flag, then many settings will be randomly varied. The randomized settings will then be printed out so you can inspect them.

The parameters of the randomization (i.e., the possible values that each setting can receive and their respective probabilities) are hard-coded into the script. A longterm to-do is to allow the user to specify the parameters of randomization in the same way that other settings are specified. There is, however, a setting available to exclude specific settings from randomization: `exclude_from_randomization`.

These are the settings that by default are randomized:

`TODO update this list dynamically, store in settings.html`

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
preserve_foot_in_bass
chord_tone_and_foot_disable
chord_tone_selection
force_chord_tone
chord_tones_sync_onset_in_all_voices
force_foot_in_bass
prefer_small_melodic_intervals
force_repeated_notes
force_parallel_motion
consonance_treatment
cont_rhythms
vary_rhythm_consistently
rhythmic_unison
rhythmic_quasi_unison
hocketing
onset_density
dur_density
onset_subdivision
randomly_distribute_between_choirs
length_choir_segments
tempo
```

These are the settings that are not randomized (although note that it is possible to specify that some of these settings, such as `foot_pcs`, be individually randomized):

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
foot_pcs
scales
voices_separate_tracks
choirs_separate_tracks
choirs_separate_channels
write_program_changes
humanize
humanize_onset
humanize_dur
humanize_velocity
humanize_tuning
logic_type_pitch_bend
num_channels_pitch_bend_loop
pitch_bend_time_prop
integers_in_12_tet
parallel_direction
extend_bass_range_for_foots
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
obligatory_onsets
obligatory_onsets_modulo
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
vl_maintain_limit_intervals = "across_harmonies" or (more permissive still) "none"
vl_maintain_forbidden_intervals = False
```
TODO -->

<!-- TODO document fact that voice-leading is applied to individual voices -->

<!-- TODO ? (It isn't really intended to produce stand-alone compositions all by itself.) -->

<!-- cuts
- first, the script generates an initial rhythm
- next, the script creates an "initial pattern" by filling the first occurrence of this rhythm with pitches
- finally, the script repeats the initial pattern over any subsequent harmonies, transforming (or "voice-leading", in musical parlance) the pattern as necessary to fit the new harmonies. The voice-leading is "efficient", in the sense of moving the voices as little as possible. -->