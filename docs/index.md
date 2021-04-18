## Introduction

`efficient_rhythms` is a tool for musical composition. You can find it
on Github at <https://github.com/malcolmsailor/efficient_rhythms>

Here are a few examples of things I have made using it:

<iframe width="560" height="315" src="https://www.youtube.com/embed/YgAUskvRWPM" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen>

</iframe>

`TODO add more videos here`

The gist of how the script works goes as follows:

  - first it makes an initial **rhythmic** pattern.
  - then it fills the rhythm with pitches.
  - finally, it repeats the pattern, adjusting it **efficiently** to fit
    any chord changes (hence the name “efficient rhythms”).

You can then hear the results as a midi file. See [How it
works](#how-it-works) for a fuller explanation, with many examples. The
script also provides a few tools (see [Filters and
Transformers](#filters-and-transformers)) for reshaping the results.

## Installation

The script requires Python \>= 3.8 and has the following Python
dependencies:

  - mido
  - numpy
  - pygame
  - python-rtmidi

These can be installed by running `pip3 install -r requirements.txt` in
the script directory.

As far as installing the script itself goes, you can just clone the
Github repository.

### Dependencies for music notation

If you want the script to output music notation, then the following must
be in your path:

  - convert (part of [ImageMagick](https://www.imagemagick.org/))
  - [img2pdf](https://gitlab.mister-muffin.de/josch/img2pdf)
  - [verovio](https://www.verovio.org/)

The first two can be installed as follows:

    brew install imagemagick # replace "brew" with your system package manager if not on macOS
    pip3 install img2pdf

Verovio installation instructions are
[here](https://github.com/rism-ch/verovio/wiki/Building-instructions#command-line-tool).

## Quick start

To quickly try the script out, you can run it with the default settings:

`python3 efficient_rhythms.py`

You can also try running it with randomized settings, although be warned
that the results are sometimes strange:

`python3 efficient_rhythms.py --random`

There are many configurable settings that shape the output. Full
documentation is available in \[`settings.html`\](docs/settings.md). But
a gentler introduction is provided in the next section.

## How it works

The basic settings that control the script are

  - `rhythm_len`: the length of the basic rhythm
  - `pattern_len`: the length of the initial pattern
  - `harmony_len`: the length of each harmony (i.e., chord)

For instance, in <a href="#example1">`docs/examples/example1.py`</a>,
the initial pattern is two beats long (i.e., `pattern_len = 2`). Each
harmony, however, is four beats (`harmony_len = 4`). Thus you can see
that the pattern repeats twice on each harmony, and is then adjusted to
fit the next harmony.\[1\]

<span id="example1">**Example:**
`docs/examples/example1.py`</span><br>\[&#1;
notation\](docs/resources/svgs/example1.svg){class=“notation”} \[&#1;
piano
roll\](docs/resources/pngs/example1\_00001.png){class=“piano\_roll”
style=“max-height: 300px”} \[&#1;
audio\](docs/resources/m4as/example1.m4a)

Whenever `rhythm_len` is not set explicitly, it is implicitly assigned
the value of `pattern_len`. So in the example above, `rhythm_len` was
implicitly assigned `2`. In
<a href="#example2">`docs/examples/example2.py`</a>, in contrast, we set
`pattern_len = 4`, but `rhythm_len = 2`. Thus, if you look and/or listen
carefully, you’ll find that the same rhythm repeats twice on each
harmony, but with different notes each time—the entire pattern of
pitches takes four beats to repeat, and by the time it does, its pitches
are somewhat different, having been adjusted to the new harmony.\[2\]

<span id="example2">**Example:**
`docs/examples/example2.py`</span><br>\[&#1;
notation\](docs/resources/svgs/example2.svg){class=“notation”} \[&#1;
piano
roll\](docs/resources/pngs/example2\_00001.png){class=“piano\_roll”
style=“max-height: 300px”} \[&#1;
audio\](docs/resources/m4as/example2.m4a)

We aren’t constrained to have `pattern_len` be a whole multiple of
`rhythm_len`. In <a href="#example3">`docs/examples/example3.py`</a>,
`pattern_len` is still `4`, but `rhythm_len = 1.5`, so now every third
time the rhythm occurs, it is truncated (a bit like a 3–3–2 *tresillo*
pattern).

<span id="example3">**Example:**
`docs/examples/example3.py`</span><br>\[&#1;
notation\](docs/resources/svgs/example3.svg){class=“notation”} \[&#1;
piano
roll\](docs/resources/pngs/example3\_00001.png){class=“piano\_roll”
style=“max-height: 300px”} \[&#1;
audio\](docs/resources/m4as/example3.m4a)

Up to now, we’ve always specified the same settings in both voices. But
we need not do so\! In
<a href="#example4">`docs/examples/example4.py`</a>, the bottom voice
again has `rhythm_len = 1.5`, but the top voice now has `rhythm_len
= 2`.

<span id="example4">**Example:**
`docs/examples/example4.py`</span><br>\[&#1;
notation\](docs/resources/svgs/example4.svg){class=“notation”} \[&#1;
piano
roll\](docs/resources/pngs/example4\_00001.png){class=“piano\_roll”
style=“max-height: 300px”} \[&#1;
audio\](docs/resources/m4as/example4.m4a)

We can also have different values of `pattern_len` in each voice, as in
<a href="#example5">`docs/examples/example5.py`</a>. However, if we do
so, the script has to work quite a bit harder to find a solution. To
help it do so, I made its task a little easier by changing
\[`consonance_treatment`\](docs/settings.md\#consonance\_treatment) from
`"all_attacks"` to `"none"`. Thus whereas in the previous examples, the
simultaneously attacked notes all formed intervals like 3rds and fifths,
in <a href="#example5">`docs/examples/example5.py`</a>, there are also
dissonances like 7ths and 9ths.

<span id="example5">**Example:**
`docs/examples/example5.py`</span><br>\[&#1;
notation\](docs/resources/svgs/example5.svg){class=“notation”} \[&#1;
piano
roll\](docs/resources/pngs/example5\_00001.png){class=“piano\_roll”
style=“max-height: 300px”} \[&#1;
audio\](docs/resources/m4as/example5.m4a)

Up until now, whenever one pattern or rhythm didn’t line up with the
other, we have truncated the shorter one, so that subsequent repetitions
began together in both voices. But the script doesn’t require this. In
<a href="#example6">`docs/examples/example6.py`</a>, I have changed
\[`truncate_patterns`\](docs/settings.md\#truncate\_patterns) to
`False`. Now the 1.5-beat pattern in the lower part isn’t truncated
after 4 beats. Instead, it is displaced relative to both the 4-beat
pattern in the upper part, as well as the 4-beat harmony changes. (The
two patterns finally come into sync after 12 beats, the
least-common-multiple of 1.5 and 4.)

<span id="example6">**Example:**
`docs/examples/example6.py`</span><br>\[&#1;
notation\](docs/resources/svgs/example6.svg){class=“notation”} \[&#1;
piano
roll\](docs/resources/pngs/example6\_00001.png){class=“piano\_roll”
style=“max-height: 300px”} \[&#1;
audio\](docs/resources/m4as/example6.m4a)

Another feature of all the examples up to now is that `harmony_len` has
always been at least as long as `pattern_len`. But there’s no reason why
this has to be so. In
<a href="#example7">`docs/examples/example7.py`</a>, I’ve set
`harmony_len = 2` but `pattern_len = 4` so that each pattern covers two
harmonies.

<span id="example7">**Example:**
`docs/examples/example7.py`</span><br>\[&#1;
notation\](docs/resources/svgs/example7.svg){class=“notation”} \[&#1;
piano
roll\](docs/resources/pngs/example7\_00001.png){class=“piano\_roll”
style=“max-height: 300px”} \[&#1;
audio\](docs/resources/m4as/example7.m4a)

### Harmony

In the preceding sections, we looked at how to adjust the lengths of
patterns, rhythms and harmonies. Now we’ll see how to specify chords and
scales to create harmonic progressions.\[3\]

The most straightforward way is to specify all chords and scales
explicitly. As a first example, I’ve specified [one of the most
(over?-)used chord progressions](https://youtu.be/5pidokakU4I) in pop
music, the I-V-vi-IV progression, in C major. The results are in
<a href="#harmony_example1">`docs/examples/harmony_example1.py`</a>. The
relevant lines in `harmony_example1.py` are

    "foot_pcs": ("C", "G", "A", "F"),
    "chords": ("MAJOR_TRIAD", "MAJOR_TRIAD", "MINOR_TRIAD", "MAJOR_TRIAD"),
    "scales": ("MAJOR_SCALE", "MIXOLYDIAN", "AEOLIAN", "LYDIAN"),

<span id="harmony_example1">**Example:**
`docs/examples/harmony_example1.py`</span><br>\[&#1;
notation\](docs/resources/svgs/harmony\_example1.svg){class=“notation”}
\[&#1; piano
roll\](docs/resources/pngs/harmony\_example1\_00001.png){class=“piano\_roll”
style=“max-height: 300px”} \[&#1;
audio\](docs/resources/m4as/harmony\_example1.m4a)

There’s a lot to explain here:

1.  Strings like `"C"` and `"MAJOR_TRIAD"` name constants that are
    defined in `src\er_constants.py`. If you know any music theory, the
    meaning of the constants above shouldn’t require any further
    explanation now. `TODO document er_constants and add a link to it
    here`
2.  We call the “main bass note” of each chord its “foot”. `TODO
    document "foots" and add a link here`
3.  Each foot is associated with the chord and the scale in the same
    serial position. Both the chord and the scale will be transposed so
    that they begin on the foot. Thus, there is a one-to-one
    correspondence between chords and scales (much like the
    “chord-scale” approach sometimes used in jazz pedagogy).

We can easily put the progression into another key by changing
`foot_pcs`. For instance, here it is in E major:

    "foot_pcs": ("E", "B", "C#", "A"),
    "chords": ("MAJOR_TRIAD", "MAJOR_TRIAD", "MINOR_TRIAD", "MAJOR_TRIAD"),
    "scales": ("MAJOR_SCALE", "MIXOLYDIAN", "AEOLIAN", "LYDIAN"),

There are no constraints on `foot_pcs`, so we can get a different
progression by changing `foot_pcs` arbitrarily. For example, in
<a href="#harmony_example2">`docs/examples/harmony_example2.py`</a> I’ve
changed the middle two members of `foot_pcs` to create a more chromatic
progression:

    "foot_pcs": ("E", "G", "D", "A"), # was ("E", "B", "C#", "A")
    "chords": ("MAJOR_TRIAD", "MAJOR_TRIAD", "MINOR_TRIAD", "MAJOR_TRIAD"),
    "scales": ("MAJOR_SCALE", "MIXOLYDIAN", "AEOLIAN", "LYDIAN"),

<span id="harmony_example2">**Example:**
`docs/examples/harmony_example2.py`</span><br>\[&#1;
notation\](docs/resources/svgs/harmony\_example2.svg){class=“notation”}
\[&#1; piano
roll\](docs/resources/pngs/harmony\_example2\_00001.png){class=“piano\_roll”
style=“max-height: 300px”} \[&#1;
audio\](docs/resources/m4as/harmony\_example2.m4a)

There are, however, two important constraints on `chords` and `scales`.

1.  All the items of `chords` must have the same number of
    pitch-classes, and all the items of `scales` must as well. This
    means, for example, you can’t go from a major triad to a seventh
    chord, or from a major scale to a whole-tone scale. (You can,
    however, use scales or chords with any number of pitch-classes you
    like—as long as that number remains the same.)\[4\]
2.  Every scale must be a superset of the associated chord. So, for
    example
      - `"MAJOR_TRIAD"` will work with `"MAJOR_SCALE"`, `"MIXOLYDIAN"`,
        or any other scale that contains a major triad beginning on its
        first pitch
      - `"MAJOR_TRIAD"` will *not* work with `"AEOLIAN"`, `"DORIAN"`,
        etc., because these scales contain a minor triad beginning on
        their first pitch

Both `chords` and `scales` will be looped through if they are shorter
than `foot_pcs`.
<a href="#harmony_example3">`docs/examples/harmony_example3.py`</a>
illustrates with the following short loop:

``` 
    "foot_pcs": ("E", "G"),
    "chords": ("MAJOR_TRIAD",), # the trailing commas before the parentheses
    "scales": ("MIXOLYDIAN",),  #   are necessary!
```

<span id="harmony_example3">**Example:**
`docs/examples/harmony_example3.py`</span><br>\[&#1;
notation\](docs/resources/svgs/harmony\_example3.svg){class=“notation”}
\[&#1; piano
roll\](docs/resources/pngs/harmony\_example3\_00001.png){class=“piano\_roll”
style=“max-height: 300px”} \[&#1;
audio\](docs/resources/m4as/harmony\_example3.m4a)

`chords` and `scales` do not have to be the same length as
<a href="#harmony_example4">`docs/examples/harmony_example4.py`</a>
demonstrates:

``` 
    "foot_pcs": ("E", "G", "E", "C"),
    "chords": ("MAJOR_TRIAD",),
    "scales": ("MIXOLYDIAN", "LYDIAN"),
```

<span id="harmony_example4">**Example:**
`docs/examples/harmony_example4.py`</span><br>\[&#1;
notation\](docs/resources/svgs/harmony\_example4.svg){class=“notation”}
\[&#1; piano
roll\](docs/resources/pngs/harmony\_example4\_00001.png){class=“piano\_roll”
style=“max-height: 300px”} \[&#1;
audio\](docs/resources/m4as/harmony\_example4.m4a)

So far, the length of the progression has always been taken implicitly
from the length of `foot_pcs`. But it is also possible to set the length
of the progression explicitly, using `num_harmonies`, as in
<a href="#harmony_example5">`docs/examples/harmony_example5.py`</a>.
Doing so allows us to create “pedal points” on a repeated bass note:

``` 
    "num_harmonies": 4,
    "foot_pcs": ("D",),
    # This example also illustrates a strategy for simulating mixing seventh
    #   chords with triads, using incomplete seventh chords.
    "chords": ("MAJOR_7TH_NO5", "DOMINANT_7TH_NO3", "MAJOR_64", "MAJOR_63"),
    "scales": ("MAJOR_SCALE", "MIXOLYDIAN", "DORIAN", "AEOLIAN"),
```

<span id="harmony_example5">**Example:**
`docs/examples/harmony_example5.py`</span><br>\[&#1;
notation\](docs/resources/svgs/harmony\_example5.svg){class=“notation”}
\[&#1; piano
roll\](docs/resources/pngs/harmony\_example5\_00001.png){class=“piano\_roll”
style=“max-height: 300px”} \[&#1;
audio\](docs/resources/m4as/harmony\_example5.m4a)

Another useful setting for creating harmonic progressions is
`interval_cycle`. If we pass `interval_cycle` to the script, then any
values of `foot_pcs` beyond the first are ignored. Instead, the
progression of `foot_pcs` is created by repeatedly progressing upwards
by `interval_cycle`. See
<a href="#harmony_example6">`docs/examples/harmony_example6.py`</a>:

``` 
    "num_harmonies": 4,
    "interval_cycle": "PERFECT_4TH",
    "foot_pcs": ("Eb",),
    # The preceding three lines are equivalent to:
    #   `"foot_pcs": ("Eb", "Ab", "Db", "Gb")`
    "chords": ("MAJOR_TRIAD",),
    "scales": ("MAJOR_SCALE",),
```

<span id="harmony_example6">**Example:**
`docs/examples/harmony_example6.py`</span><br>\[&#1;
notation\](docs/resources/svgs/harmony\_example6.svg){class=“notation”}
\[&#1; piano
roll\](docs/resources/pngs/harmony\_example6\_00001.png){class=“piano\_roll”
style=“max-height: 300px”} \[&#1;
audio\](docs/resources/m4as/harmony\_example6.m4a)

`interval_cycle` can also consist of more than one interval, as in
<a href="#harmony_example7">`docs/examples/harmony_example7.py`</a>.
(Note that, since the intervals in `interval_cycle` are always
understood *upwards*, `"MINOR_6TH"` in this example is equivalent to a
descending major third.)

    {
        "num_harmonies": 4,
        "interval_cycle": ("PERFECT_4TH", "MINOR_6TH"),
        "foot_pcs": ("Eb",),
        # The preceding three lines are equivalent to:
        #   `"foot_pcs": ("Eb", "Ab", "E", "A")`
        "chords": ("MAJOR_TRIAD",),
        "scales": ("MAJOR_SCALE",),
    }

<span id="harmony_example7">**Example:**
`docs/examples/harmony_example7.py`</span><br>\[&#1;
notation\](docs/resources/svgs/harmony\_example7.svg){class=“notation”}
\[&#1; piano
roll\](docs/resources/pngs/harmony\_example7\_00001.png){class=“piano\_roll”
style=“max-height: 300px”} \[&#1;
audio\](docs/resources/m4as/harmony\_example7.m4a)

Before concluding this introduction to specifying harmonies, I should
add a few words about what the script actually does with `chords` and
`scales`.

  - `scales` are used unconditionally: during each harmony, pitches are
    drawn exclusively from the associated scale. When a pattern is
    voice-led from one harmony to another, a bijective mapping is
    effected between the associated scales.
  - the use of `chords` is more contingent. The most important relevant
    settings are
      - if `chord_tone_selection` is `True`, then when constructing the
        initial pattern, the script probabilistically decides whether
        each note should be a chord-tone (according to \[parameters that
        you specify\](docs/settings.md\#chord-tone-settings)).
      - if `voice_lead_chord_tones` is `True`, then when voice-leading
        the pattern over subsequent harmonies, the script will ensure
        that chord-tones are mapped to chord-tones (and non-chord-tones
        to non-chord-tones).

In the preceding examples of this section both `chord_tone_selection`
and `voice_lead_chord_tones` have been `True`. As a contrasting
illustration,
<a href="#harmony_example8">`docs/examples/harmony_example8.py`</a>
repeats the settings of
<a href="#harmony_example6">`docs/examples/harmony_example6.py`</a>,
with the sole difference that `voice_lead_chord_tones` is now set to
`False`. (Note, however, that the settings `force_foot_in_bass = True`
and `extend_bass_range_for_foots = 7` in
`examples/harmony_example_base.py` are still causing the foot of each
scale/chord to sound on beat one of each harmony.)

<span id="harmony_example8">**Example:**
`docs/examples/harmony_example8.py`</span><br>\[&#1;
notation\](docs/resources/svgs/harmony\_example8.svg){class=“notation”}
\[&#1; piano
roll\](docs/resources/pngs/harmony\_example8\_00001.png){class=“piano\_roll”
style=“max-height: 300px”} \[&#1;
audio\](docs/resources/m4as/harmony\_example8.m4a)

<a href="#harmony_example9">`docs/examples/harmony_example9.py`</a> is
similar, but with `chord_tone_selection = False` as well.

<span id="harmony_example9">**Example:**
`docs/examples/harmony_example9.py`</span><br>\[&#1;
notation\](docs/resources/svgs/harmony\_example9.svg){class=“notation”}
\[&#1; piano
roll\](docs/resources/pngs/harmony\_example9\_00001.png){class=“piano\_roll”
style=“max-height: 300px”} \[&#1;
audio\](docs/resources/m4as/harmony\_example9.m4a)

### Specifying rhythms

Besides setting `rhythm_len` as we did [above](#how-it-works), there are
many other ways of controlling the rhythms that are produced.

To begin with, we have `attack_subdivision` and `attack_density`:

  - `attack_subdivision` indicates the basic “grid” on which note
    attacks can take place, measured in quarter notes.
  - `attack_density` indicates the proportion of grid points that should
    have an attack.

So for example, in
<a href="#rhythm_example1">`docs/examples/rhythm_example1.py`</a>,
`"attack_subdivision" = 1/4` indicates a sixteenth-note grid, and
`"attack_density" = 1.0` indicates that every point in the grid should
have an attack, creating a *moto perpetuo* texture. (For
clarity/brevity, this example has only one voice.)

    {
    "num_voices": 1,
    "attack_density": 0.5,
    "attack_subdivision": 1/4,
    }

<span id="rhythm_example1">**Example:**
`docs/examples/rhythm_example1.py`</span><br>\[&#1;
notation\](docs/resources/svgs/rhythm\_example1.svg){class=“notation”}
\[&#1; piano
roll\](docs/resources/pngs/rhythm\_example1\_00001.png){class=“piano\_roll”
style=“max-height: 300px”} \[&#1;
audio\](docs/resources/m4as/rhythm\_example1.m4a)

If we reduce `attack_density`, as in
<a href="#rhythm_example2">`docs/examples/rhythm_example2.py`</a>, the
proportion of the sixteenth-grid that is filled with attacks will be
correspondingly reduced.

    {
        "num_voices": 1,
        "attack_density": 0.5,
        "attack_subdivision": 1 / 4,
    }

<span id="rhythm_example2">**Example:**
`docs/examples/rhythm_example2.py`</span><br>\[&#1;
notation\](docs/resources/svgs/rhythm\_example2.svg){class=“notation”}
\[&#1; piano
roll\](docs/resources/pngs/rhythm\_example2\_00001.png){class=“piano\_roll”
style=“max-height: 300px”} \[&#1;
audio\](docs/resources/m4as/rhythm\_example2.m4a)

Another important rhythmic parameter is `dur_density`. It specifies the
proportion of time that should be filled by note durations, irrespective
of how many attacks there are. So far we have left `dur_density` at the
default value of `1.0`, which means that all notes last until the next
attack in that voice. (In musical terms, all notes are *legato*.) If we
decrease it to 0.75, as in
<a href="#rhythm_example3">`docs/examples/rhythm_example3.py`</a>, some
of the notes will become shorter, so that 75% of the total time of the
rhythm is filled by sounding notes.

    {
        "num_voices": 1,
        "attack_density": 0.5,
        "dur_density": 0.75,
        "attack_subdivision": 1 / 4,
    }}

<span id="rhythm_example3">**Example:**
`docs/examples/rhythm_example3.py`</span><br>\[&#1;
notation\](docs/resources/svgs/rhythm\_example3.svg){class=“notation”}
\[&#1; piano
roll\](docs/resources/pngs/rhythm\_example3\_00001.png){class=“piano\_roll”
style=“max-height: 300px”} \[&#1;
audio\](docs/resources/m4as/rhythm\_example3.m4a)

To obtain a *staccato* effect, we can make `dur_density` still shorter,
but to obtain *really* short notes, we may have to adjust `min_dur` as
well, which sets the minimum duration of each pitch as well.

    {
        "num_voices": 1,
        "attack_density": 0.5,
        "dur_density": 0.25,
        "min_dur": 1/8,
        "attack_subdivision": 1 / 4,
    }

<span id="rhythm_example4">**Example:**
`docs/examples/rhythm_example4.py`</span><br>\[&#1;
notation\](docs/resources/svgs/rhythm\_example4.svg){class=“notation”}
\[&#1; piano
roll\](docs/resources/pngs/rhythm\_example4\_00001.png){class=“piano\_roll”
style=“max-height: 300px”} \[&#1;
audio\](docs/resources/m4as/rhythm\_example4.m4a)

We can change `"attack_subdivision"` as well. For example, to have a
grid of eighth-note triplets, we would set `"attack_subdivision" = 1/3`.
And since computers have no problem with precise, strange rhythms, we
could also set it to unusual values like `5/13` or `math.pi / 12`.\[5\]

    {
        "num_voices": 1,
        "attack_density": 0.75,
        "dur_density": 0.25,
        "min_dur": 1/8,
        "attack_subdivision": 3/ 13,
    }

<span id="rhythm_example5">**Example:**
`docs/examples/rhythm_example5.py`</span><br>\[&#1; piano
roll\](docs/resources/pngs/rhythm\_example5\_00001.png){class=“piano\_roll”
style=“max-height: 300px”} \[&#1;
audio\](docs/resources/m4as/rhythm\_example5.m4a)

All of the settings we have been looking at so far are “per-voice”,
meaning that they can be set to a different value in each voice. If we
set `attack_subdivision` to a different unusual value in each voice, we
get a particularly chaotic effect. (I find that the chaos can be reined
in a bit by setting `rhythm_len` to a short value, creating a brief
rhythmic loop.)

    {
        "rhythm_len": 1,
        "num_voices": 3,
        "attack_density": [0.25, 0.5, 0.75],
        "dur_density": [0.25, 0.5, 0.25],
        "min_dur": [0.25, 0.25, 1/8],
        "attack_subdivision": [3/ 13, 5/12, 6/11],
    }

<span id="rhythm_example6">**Example:**
`docs/examples/rhythm_example6.py`</span><br>\[&#1; piano
roll\](docs/resources/pngs/rhythm\_example6\_00001.png){class=“piano\_roll”
style=“max-height: 300px”} \[&#1;
audio\](docs/resources/m4as/rhythm\_example6.m4a)

There are also a few settings that govern the relation between different
voices. If `hocketing` is `True`, then, to the extent possible, the
attacks of each voice will occur when there is no attack in any other
voice. (In textures with many voices, it is also possible to assign
specific pairs of voices to hocket with one another.)

    {
        "num_voices": 2,
        "attack_density": 0.4,
        "dur_density": 0.4,
        "min_dur": 0.25,
        "attack_subdivision": 0.25,
        "hocketing": True,
    }

<span id="rhythm_example7">**Example:**
`docs/examples/rhythm_example7.py`</span><br>\[&#1;
notation\](docs/resources/svgs/rhythm\_example7.svg){class=“notation”}
\[&#1; piano
roll\](docs/resources/pngs/rhythm\_example7\_00001.png){class=“piano\_roll”
style=“max-height: 300px”} \[&#1;
audio\](docs/resources/m4as/rhythm\_example7.m4a)

Another setting that governs the rhythmic relation between voices is
`rhythmic_unison`, which causes voices to have exactly the same rhythm.
(Like `hocketing`, it can be provided a boolean, or a list of tuples of
voices; see the settings documentation for more details.)

    {
        "num_voices": 3,
        "rhythmic_unison": True,
        "attack_density": .7,
        "dur_density": 0.6,
        "min_dur": 0.25,
        "attack_subdivision": 1/4,
    }

<span id="rhythm_example8">**Example:**
`docs/examples/rhythm_example8.py`</span><br>\[&#1;
notation\](docs/resources/svgs/rhythm\_example8.svg){class=“notation”}
\[&#1; piano
roll\](docs/resources/pngs/rhythm\_example8\_00001.png){class=“piano\_roll”
style=“max-height: 300px”} \[&#1;
audio\](docs/resources/m4as/rhythm\_example8.m4a)

When `rhythmic_unison` is applied, rhythmic settings like
`attack_density` only have any effect in the “leader” voice, whose
rhythm is simply copied into the other voices. If we wanted to specify a
different `attack_density` in a “follower” voice, it would be ignored.
This situation would call for the related setting
`rhythmic_quasi_unison`. When `rhythmic_quasi_unison` applies, then,
instead of copying the “leader” rhythm into the “follower” voices, the
attacks of the “follower” voices are constrained so far as possible to
coincide with those of the “leader.” In
<a href="#rhythm_example9">`docs/examples/rhythm_example9.py`</a>, the
leader is the bass voice (midi guitar). The middle voice (midi piano)
has a *lower* `attack_density`, and the top voice (midi electric piano)
has a *higher* `attack_density`.

    {
        "num_voices": 3,
        "rhythmic_quasi_unison": True,
        "attack_density": [0.5, 0.4, 0.6],
        "dur_density": [0.5, 0.4, 0.6],
        "min_dur": 0.25,
        "attack_subdivision": 1 / 4,
    }

<span id="rhythm_example9">**Example:**
`docs/examples/rhythm_example9.py`</span><br>\[&#1;
notation\](docs/resources/svgs/rhythm\_example9.svg){class=“notation”}
\[&#1; piano
roll\](docs/resources/pngs/rhythm\_example9\_00001.png){class=“piano\_roll”
style=“max-height: 300px”} \[&#1;
audio\](docs/resources/m4as/rhythm\_example9.m4a)

We can obtain more explicit control of the rhythms through the
`obligatory_attacks` setting, which specifies a sequence of times at
which the rhythms will be “obliged” to have a note onset. It’s also
necessary to specify `obligatory_attacks_modulo` in order to specify
when these attacks should repeat (e.g., every two beats).

For example, in
<a href="#rhythm_example10">`docs/examples/rhythm_example10.py`</a>,
I’ve set `obligatory_attacks` to `[0, 0.75, 1.5]` and
`obligatory_attacks_modulo` to `2` in order to specify a *tresillo*
3–3–2 rhythm. Since the value of `attack_density` implies more than
three attacks every two beats, additional attacks are added to the
underlying scaffold supplied by the values in `obligatory_attacks`.

    {
        "num_voices": 3,
        "obligatory_attacks": [0, 0.75, 1.5],
        "obligatory_attacks_modulo": 2,
        "attack_density": 0.5,
        "dur_density": 0.5,
        "min_dur": 0.25,
        "attack_subdivision": 0.25,
    }

<span id="rhythm_example10">**Example:**
`docs/examples/rhythm_example10.py`</span><br>\[&#1;
notation\](docs/resources/svgs/rhythm\_example10.svg){class=“notation”}
\[&#1; piano
roll\](docs/resources/pngs/rhythm\_example10\_00001.png){class=“piano\_roll”
style=“max-height: 300px”} \[&#1;
audio\](docs/resources/m4as/rhythm\_example10.m4a)

It is possible to specify an irregular grid upon which note attacks will
take place using `sub_subdivisions`. This setting takes a sequence of
integers and subdivides the grid specified by `attack_subdivision` into
parts defined by the ratio of these integers. For example, in
<a href="#rhythm_example11">`docs/examples/rhythm_example11.py`</a>
below, `sub_subdivisions` is `[4,3]`, which creates an uneven “swing”
feel where every first note is 4/3rds as long as every second note.\[^To
keep the number of total attacks consistent, you’ll probably want to
increase `attack_subdivision` by taking the value you otherwise would
have chosen and multiplying it by the length of `sub_subdivisions`.\]
You’ll notice that
<a href="#rhythm_example11">`docs/examples/rhythm_example11.py`</a> is
precisely the same as
<a href="#rhythm_example1">`docs/examples/rhythm_example1.py`</a>,
except for the uneven rhythms.

    {
        "num_voices": 1,
        "attack_density": 1.0,
        "attack_subdivision": 0.5,
        "sub_subdivisions": [4, 3],
    }

<span id="rhythm_example11">**Example:**
`docs/examples/rhythm_example11.py`</span><br>\[&#1; piano
roll\](docs/resources/pngs/rhythm\_example11\_00001.png){class=“piano\_roll”
style=“max-height: 300px”} \[&#1;
audio\](docs/resources/m4as/rhythm\_example11.m4a)

I think, however, that it is more interesting to experiment with values
of `sub_subdivisions` that are further from what a human would be likely
to produce. In
<a href="#rhythm_example12">`docs/examples/rhythm_example12.py`</a>, I
use a segment of the Fibonacci sequence in reverse.

    {
        "num_voices": 3,
        "attack_density": 0.4,
        "attack_subdivision": 1,
        "sub_subdivisions": [8, 5, 3],
        "obligatory_attacks": 0,
        "obligatory_attacks_modulo": 2,
        "hocketing": True,
    }

<span id="rhythm_example12">**Example:**
`docs/examples/rhythm_example12.py`</span><br>\[&#1; piano
roll\](docs/resources/pngs/rhythm\_example12\_00001.png){class=“piano\_roll”
style=“max-height: 300px”} \[&#1;
audio\](docs/resources/m4as/rhythm\_example12.m4a)

## Filters and transformers

`TODO`

1.  You can find the settings files that generated all the examples in
    this section in the `docs/examples` folder.
    `docs/examples/example_base.py` is shared among each example. So you
    can build the first example with the command `python3
    efficient_rhythms.py --settings docs/examples/example_base.py
    docs/examples/example1.py`; for subsequent examples, just replace
    `example1.py` with the appropriate file.

2.  The music-theoretically fastidious among you may have observed that
    these examples contain plentiful parallel fifths (for example, the
    first two sixteenth-notes in
    <a href="#example2">`docs/examples/example2.py`</a>). If desired,
    parallel fifths could be avoided by including `7` (i.e., the number
    of semitones in a perfect fifth) in the sequence provided to the
    setting `prohibit_parallels`.

3.  The settings files that generated the examples in this section all
    begin with `harmony_example` and are found in the `docs/examples`
    folder. `docs/examples/harmony_example_base.py` is shared among each
    example. So you can build the first example with the command
    `python3 efficient_rhythms.py --settings
    docs/examples/harmony_example_base.py
    docs/examples/harmony_example1.py`.

4.  There is a technical reason for this constraint, (namely, that the
    script works by finding bijective voice-leadings between chords and
    scales), but in the longterm, I would very much like to remove it.

5.  However, we’ll have to give up on representing these in conventional
    music notation. In fact, for the time being only duple note-values
    (i.e., eighth-notes, quarter-notes, and the like) can be exported to
    notation.
