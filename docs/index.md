## Introduction

`efficient_rhythms` is a tool for musical composition. You can find it
on Github at <https://github.com/malcolmsailor/efficient_rhythms>. There
is also an [alpha web app version of this
script](http://malcolmsailor.pythonanywhere.com) you are welcome to try.

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
  - sortedcontainers

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

To quickly try the script out, you can run it with the default
settings:\[^This command needs to be run from the root directory of the
repository.\]

`python3 -m efficient_rhythms`

You can also try running it with randomized settings, although be warned
that the results are sometimes strange:

`python3 -m efficient_rhythms`

There are many configurable settings that shape the output. Full
documentation is available in \[`settings.html`\](docs/settings.md). But
a gentler introduction is provided in the next section.

In general, custom settings are applied by putting them into a Python
dictionary, saving them in a file, and then passing that file as an
argument to the script with the `--settings` flag. For examples, see
`docs/examples`. (A long-term goal for this project would be to provide
a GUI or other more user-friendly interface.)

## How it works

The basic settings that control the script are

  - \[`rhythm_len`\](docs/settings.md\#rhythm\_len): the length of the
    basic rhythm
  - \[`pattern_len`\](docs/settings.md\#pattern\_len): the length of the
    initial pattern
  - \[`harmony_len`\](docs/settings.md\#harmony\_len): the length of
    each harmony (i.e., chord)

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
audio\](docs/resources/m4as/example1.m4a) [Click to open this example in
the web
app](http://malcolmsailor.pythonanywhere.com/?seed=2&num_voices=2&foot_pcs=0&interval_cycle=3&prohibit_parallels=0&overwrite=y&max_repeated_notes=0&num_harmonies=4&output_path=EFFRHY%2Fdocs%2Fexamples%2Fmidi%2F&max_interval=4&force_foot_in_bass=global_first_beat&force_chord_tone=global_first_note&forbidden_interval_classes=0&randomly_distribute_between_choirs=n&tempo=120&onset_density=0.7&dur_density=1.0&max_consec_seg_from_same_choir=0&length_choir_segments=1&preserve_foot_in_bass=none&scales=DIATONIC_SCALE&chords=MAJOR_TRIAD&voice_lead_chord_tones=y&pattern_len=2&harmony_len=4&consonance_treatment=all_onsets&hocketing=y)

(By the way, I made the piano-roll figures throughout this documentation
with [midani](https://github.com/malcolmsailor/midani).)

Whenever \[`rhythm_len`\](docs/settings.md\#rhythm\_len) is not set
explicitly, it is implicitly assigned the value of
\[`pattern_len`\](docs/settings.md\#pattern\_len). So in the example
above, \[`rhythm_len`\](docs/settings.md\#rhythm\_len) was implicitly
assigned `2`. In <a href="#example2">`docs/examples/example2.py`</a>, in
contrast, we set `pattern_len = 4`, but `rhythm_len = 2`. Thus, if you
look and/or listen carefully, you’ll find that the same rhythm repeats
twice on each harmony, but with different notes each time—the entire
pattern of pitches takes four beats to repeat, and by the time it does,
its pitches are somewhat different, having been adjusted to the new
harmony.\[2\]

<span id="example2">**Example:**
`docs/examples/example2.py`</span><br>\[&#1;
notation\](docs/resources/svgs/example2.svg){class=“notation”} \[&#1;
piano
roll\](docs/resources/pngs/example2\_00001.png){class=“piano\_roll”
style=“max-height: 300px”} \[&#1;
audio\](docs/resources/m4as/example2.m4a) [Click to open this example in
the web
app](http://malcolmsailor.pythonanywhere.com/?seed=2&num_voices=2&foot_pcs=0&interval_cycle=3&prohibit_parallels=0&overwrite=y&max_repeated_notes=0&num_harmonies=4&output_path=EFFRHY%2Fdocs%2Fexamples%2Fmidi%2F&max_interval=4&force_foot_in_bass=global_first_beat&force_chord_tone=global_first_note&forbidden_interval_classes=0&randomly_distribute_between_choirs=n&tempo=120&onset_density=0.7&dur_density=1.0&max_consec_seg_from_same_choir=0&length_choir_segments=1&preserve_foot_in_bass=none&scales=DIATONIC_SCALE&chords=MAJOR_TRIAD&voice_lead_chord_tones=n&pattern_len=4&rhythm_len=2&harmony_len=4&consonance_treatment=all_onsets)

We aren’t constrained to have
\[`pattern_len`\](docs/settings.md\#pattern\_len) be a whole multiple of
\[`rhythm_len`\](docs/settings.md\#rhythm\_len). In
<a href="#example3">`docs/examples/example3.py`</a>,
\[`pattern_len`\](docs/settings.md\#pattern\_len) is still `4`, but
`rhythm_len = 1.5`, so now every third time the rhythm occurs, it is
truncated (a bit like a 3–3–2 *tresillo* pattern).

<span id="example3">**Example:**
`docs/examples/example3.py`</span><br>\[&#1;
notation\](docs/resources/svgs/example3.svg){class=“notation”} \[&#1;
piano
roll\](docs/resources/pngs/example3\_00001.png){class=“piano\_roll”
style=“max-height: 300px”} \[&#1;
audio\](docs/resources/m4as/example3.m4a) [Click to open this example in
the web
app](http://malcolmsailor.pythonanywhere.com/?seed=2&num_voices=2&foot_pcs=0&interval_cycle=3&prohibit_parallels=0&overwrite=y&max_repeated_notes=0&num_harmonies=4&output_path=EFFRHY%2Fdocs%2Fexamples%2Fmidi%2F&max_interval=4&force_foot_in_bass=global_first_beat&force_chord_tone=global_first_note&forbidden_interval_classes=0&randomly_distribute_between_choirs=n&tempo=120&onset_density=0.7%2C+0.85&dur_density=1.0&max_consec_seg_from_same_choir=0&length_choir_segments=1&preserve_foot_in_bass=none&scales=DIATONIC_SCALE&chords=MAJOR_TRIAD&voice_lead_chord_tones=n&pattern_len=4&rhythm_len=1.5&harmony_len=4&consonance_treatment=all_onsets)

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
audio\](docs/resources/m4as/example4.m4a) [Click to open this example in
the web
app](http://malcolmsailor.pythonanywhere.com/?seed=2&num_voices=2&foot_pcs=0&interval_cycle=3&prohibit_parallels=0&overwrite=y&max_repeated_notes=0&num_harmonies=4&output_path=EFFRHY%2Fdocs%2Fexamples%2Fmidi%2F&max_interval=4&force_foot_in_bass=global_first_beat&force_chord_tone=global_first_note&forbidden_interval_classes=0&randomly_distribute_between_choirs=n&tempo=120&onset_density=0.7%2C+0.85&dur_density=1.0&max_consec_seg_from_same_choir=0&length_choir_segments=1&preserve_foot_in_bass=none&scales=DIATONIC_SCALE&chords=MAJOR_TRIAD&voice_lead_chord_tones=n&pattern_len=4&rhythm_len=1.5%2C+2&harmony_len=4&consonance_treatment=all_onsets)

We can also have different values of
\[`pattern_len`\](docs/settings.md\#pattern\_len) in each voice, as in
<a href="#example5">`docs/examples/example5.py`</a>. However, if we do
so, the script has to work quite a bit harder to find a solution. To
help it do so, I made its task a little easier by changing
\[`consonance_treatment`\](docs/settings.md\#consonance\_treatment) from
`"all_onsets"` to `"none"`. Thus whereas in the previous examples, the
simultaneously onset notes all formed intervals like 3rds and fifths, in
<a href="#example5">`docs/examples/example5.py`</a>, there are also
dissonances like 7ths and 9ths.

<span id="example5">**Example:**
`docs/examples/example5.py`</span><br>\[&#1;
notation\](docs/resources/svgs/example5.svg){class=“notation”} \[&#1;
piano
roll\](docs/resources/pngs/example5\_00001.png){class=“piano\_roll”
style=“max-height: 300px”} \[&#1;
audio\](docs/resources/m4as/example5.m4a) [Click to open this example in
the web
app](http://malcolmsailor.pythonanywhere.com/?seed=2&num_voices=2&foot_pcs=0&interval_cycle=3&prohibit_parallels=0&overwrite=y&max_repeated_notes=0&num_harmonies=4&output_path=EFFRHY%2Fdocs%2Fexamples%2Fmidi%2F&max_interval=4&force_foot_in_bass=global_first_beat&force_chord_tone=global_first_note&forbidden_interval_classes=0&randomly_distribute_between_choirs=n&tempo=120&onset_density=0.7&dur_density=1.0&max_consec_seg_from_same_choir=0&length_choir_segments=1&preserve_foot_in_bass=none&scales=DIATONIC_SCALE&chords=MAJOR_TRIAD&voice_lead_chord_tones=n&pattern_len=1.5%2C+4&truncate_patterns=y&harmony_len=4&consonance_treatment=none&hocketing=y&overlap=n)

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
audio\](docs/resources/m4as/example6.m4a) [Click to open this example in
the web
app](http://malcolmsailor.pythonanywhere.com/?seed=2&num_voices=2&foot_pcs=0&interval_cycle=3&prohibit_parallels=0&overwrite=y&max_repeated_notes=0&num_harmonies=4&output_path=EFFRHY%2Fdocs%2Fexamples%2Fmidi%2F&max_interval=4&force_foot_in_bass=global_first_beat&force_chord_tone=global_first_note&forbidden_interval_classes=0&randomly_distribute_between_choirs=n&tempo=120&onset_density=0.7&dur_density=1.0&max_consec_seg_from_same_choir=0&length_choir_segments=1&preserve_foot_in_bass=none&scales=DIATONIC_SCALE&chords=MAJOR_TRIAD&voice_lead_chord_tones=n&pattern_len=1.5%2C+4&truncate_patterns=n&harmony_len=4&consonance_treatment=none&hocketing=y&overlap=n)

Another feature of all the examples up to now is that
\[`harmony_len`\](docs/settings.md\#harmony\_len) has always been at
least as long as \[`pattern_len`\](docs/settings.md\#pattern\_len). But
there’s no reason why this has to be so. In
<a href="#example7">`docs/examples/example7.py`</a>, I’ve set
`harmony_len = 2` but `pattern_len = 4` so that each pattern covers two
harmonies.

<span id="example7">**Example:**
`docs/examples/example7.py`</span><br>\[&#1;
notation\](docs/resources/svgs/example7.svg){class=“notation”} \[&#1;
piano
roll\](docs/resources/pngs/example7\_00001.png){class=“piano\_roll”
style=“max-height: 300px”} \[&#1;
audio\](docs/resources/m4as/example7.m4a) [Click to open this example in
the web
app](http://malcolmsailor.pythonanywhere.com/?seed=2&num_voices=2&foot_pcs=0&interval_cycle=3&prohibit_parallels=0&overwrite=y&max_repeated_notes=0&num_harmonies=4&output_path=EFFRHY%2Fdocs%2Fexamples%2Fmidi%2F&max_interval=4&force_foot_in_bass=first_beat&force_chord_tone=global_first_note&forbidden_interval_classes=0&randomly_distribute_between_choirs=n&tempo=120&onset_density=0.7&dur_density=1.0&max_consec_seg_from_same_choir=0&length_choir_segments=1&preserve_foot_in_bass=none&scales=DIATONIC_SCALE&chords=MAJOR_TRIAD&voice_lead_chord_tones=y&pattern_len=4&harmony_len=2&obligatory_onsets=%5B0%5D%2C+%5B%5D&obligatory_onsets_modulo=2&voice_ranges=%2848%2C+60%29%2C+%2860%2C+72%29&extend_bass_range_for_foots=6&consonance_treatment=all_onsets&hocketing=y&num_reps_super_pattern=4)

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
audio\](docs/resources/m4as/harmony\_example1.m4a) [Click to open this
example in the web
app](http://malcolmsailor.pythonanywhere.com/?seed=2&pattern_len=4&consonance_treatment=none&harmony_len=4&output_path=EFFRHY%2Fdocs%2Fexamples%2Fmidi%2F&overwrite=y&force_foot_in_bass=first_beat&extend_bass_range_for_foots=7&voice_lead_chord_tones=y&onset_density=0.7&dur_density=0.7&unison_weighted_as=SECOND&randomly_distribute_between_choirs=y&length_choir_segments=0.25&tempo=132&choirs_separate_tracks=n&max_consec_seg_from_same_choir=0&preserve_foot_in_bass=none&scales=MAJOR_SCALE%2C+MIXOLYDIAN%2C+AEOLIAN%2C+LYDIAN&chords=MAJOR_TRIAD%2C+MAJOR_TRIAD%2C+MINOR_TRIAD%2C+MAJOR_TRIAD&foot_pcs=C%2C+G%2C+A%2C+F)

There’s a lot to explain here:

1.  Strings like `"C"` and `"MAJOR_TRIAD"` name constants that are
    defined in `src\er_constants.py` and documented
    \[here\](docs/constants.md). If you know any music theory, the
    meaning of the constants above shouldn’t require any further
    explanation for now.
2.  In this script, we call the main bass pitch of each chord its
    “foot”. The main bass pitch is a little like the “root” of a
    chord, except that the main bass pitch doesn’t have to be the root
    of a chord (as in the case of inverted chords).
3.  Each foot is associated with the chord and the scale in the same
    serial position. Both the chord and the scale will be transposed so
    that they begin on the foot. Thus, there is a one-to-one
    correspondence between chords and scales (much like the
    “chord-scale” approach sometimes used in jazz pedagogy).

We can easily put the progression into another key by changing
\[`foot_pcs`\](docs/settings.md\#foot\_pcs). For instance, here it is in
E major:

    "foot_pcs": ("E", "B", "C#", "A"),
    "chords": ("MAJOR_TRIAD", "MAJOR_TRIAD", "MINOR_TRIAD", "MAJOR_TRIAD"),
    "scales": ("MAJOR_SCALE", "MIXOLYDIAN", "AEOLIAN", "LYDIAN"),

There are no constraints on \[`foot_pcs`\](docs/settings.md\#foot\_pcs),
so we can get a different progression by changing
\[`foot_pcs`\](docs/settings.md\#foot\_pcs) arbitrarily. For example, in
<a href="#harmony_example2">`docs/examples/harmony_example2.py`</a> I’ve
changed the middle two members of
\[`foot_pcs`\](docs/settings.md\#foot\_pcs) to create a more chromatic
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
audio\](docs/resources/m4as/harmony\_example2.m4a) [Click to open this
example in the web
app](http://malcolmsailor.pythonanywhere.com/?seed=2&pattern_len=4&consonance_treatment=none&harmony_len=4&output_path=EFFRHY%2Fdocs%2Fexamples%2Fmidi%2F&overwrite=y&force_foot_in_bass=first_beat&extend_bass_range_for_foots=7&voice_lead_chord_tones=y&onset_density=0.7&dur_density=0.7&unison_weighted_as=SECOND&randomly_distribute_between_choirs=y&length_choir_segments=0.25&tempo=132&choirs_separate_tracks=n&max_consec_seg_from_same_choir=0&preserve_foot_in_bass=none&scales=MAJOR_SCALE%2C+MIXOLYDIAN%2C+AEOLIAN%2C+LYDIAN&chords=MAJOR_TRIAD%2C+MAJOR_TRIAD%2C+MINOR_TRIAD%2C+MAJOR_TRIAD&foot_pcs=E%2C+G%2C+D%2C+A)

There are, however, two important constraints on
\[`chords`\](docs/settings.md\#chords) and
\[`scales`\](docs/settings.md\#scales).

1.  All the items of \[`chords`\](docs/settings.md\#chords) must have
    the same number of pitch-classes, and all the items of
    \[`scales`\](docs/settings.md\#scales) must as well. This means, for
    example, you can’t go from a major triad to a seventh chord, or from
    a major scale to a whole-tone scale. (You can, however, use scales
    or chords with any number of pitch-classes you like—as long as that
    number remains the same.)\[4\]
2.  Every scale must be a superset of the associated chord. So, for
    example
      - `"MAJOR_TRIAD"` will work with `"MAJOR_SCALE"`, `"MIXOLYDIAN"`,
        or any other scale that contains a major triad beginning on its
        first pitch
      - `"MAJOR_TRIAD"` will *not* work with `"AEOLIAN"`, `"DORIAN"`,
        etc., because these scales contain a minor triad beginning on
        their first pitch

Both \[`chords`\](docs/settings.md\#chords) and
\[`scales`\](docs/settings.md\#scales) will be looped through if they
are shorter than \[`foot_pcs`\](docs/settings.md\#foot\_pcs).
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
audio\](docs/resources/m4as/harmony\_example3.m4a) [Click to open this
example in the web
app](http://malcolmsailor.pythonanywhere.com/?seed=2&pattern_len=4&consonance_treatment=none&harmony_len=4&output_path=EFFRHY%2Fdocs%2Fexamples%2Fmidi%2F&overwrite=y&force_foot_in_bass=first_beat&extend_bass_range_for_foots=7&voice_lead_chord_tones=y&onset_density=0.7&dur_density=0.7&unison_weighted_as=SECOND&randomly_distribute_between_choirs=y&length_choir_segments=0.25&tempo=132&choirs_separate_tracks=n&max_consec_seg_from_same_choir=0&preserve_foot_in_bass=none&scales=MIXOLYDIAN%2C&chords=MAJOR_TRIAD%2C&foot_pcs=E%2C+G&num_reps_super_pattern=4)

The sequences \[`chords`\](docs/settings.md\#chords) and
\[`scales`\](docs/settings.md\#scales) do not have to have the same
number of items, as
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
audio\](docs/resources/m4as/harmony\_example4.m4a) [Click to open this
example in the web
app](http://malcolmsailor.pythonanywhere.com/?seed=2&pattern_len=4&consonance_treatment=none&harmony_len=4&output_path=EFFRHY%2Fdocs%2Fexamples%2Fmidi%2F&overwrite=y&force_foot_in_bass=first_beat&extend_bass_range_for_foots=7&voice_lead_chord_tones=y&onset_density=0.7&dur_density=0.7&unison_weighted_as=SECOND&randomly_distribute_between_choirs=y&length_choir_segments=0.25&tempo=132&choirs_separate_tracks=n&max_consec_seg_from_same_choir=0&preserve_foot_in_bass=none&scales=MIXOLYDIAN%2C+LYDIAN&chords=MAJOR_TRIAD%2C&foot_pcs=E%2C+G%2C+E%2C+C)

So far, the length of the progression has always been taken implicitly
from the length of \[`foot_pcs`\](docs/settings.md\#foot\_pcs). But it
is also possible to set the length of the progression explicitly, using
\[`num_harmonies`\](docs/settings.md\#num\_harmonies), as in
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
audio\](docs/resources/m4as/harmony\_example5.m4a) [Click to open this
example in the web
app](http://malcolmsailor.pythonanywhere.com/?seed=2&pattern_len=4&consonance_treatment=none&harmony_len=4&output_path=EFFRHY%2Fdocs%2Fexamples%2Fmidi%2F&overwrite=y&force_foot_in_bass=first_beat&extend_bass_range_for_foots=7&voice_lead_chord_tones=y&onset_density=0.7&dur_density=0.7&unison_weighted_as=SECOND&randomly_distribute_between_choirs=y&length_choir_segments=0.25&tempo=132&choirs_separate_tracks=n&max_consec_seg_from_same_choir=0&preserve_foot_in_bass=none&scales=MAJOR_SCALE%2C+MIXOLYDIAN%2C+MIXOLYDIAN%2C+AEOLIAN&chords=MAJOR_7TH_NO5%2C+DOMINANT_7TH_NO3%2C+MAJOR_64%2C+MAJOR_63&num_harmonies=4&foot_pcs=D%2C)

Another useful setting for creating harmonic progressions is
\[`interval_cycle`\](docs/settings.md\#interval\_cycle). If we pass
\[`interval_cycle`\](docs/settings.md\#interval\_cycle) to the script,
then any values of \[`foot_pcs`\](docs/settings.md\#foot\_pcs) beyond
the first are ignored. Instead, the progression of
\[`foot_pcs`\](docs/settings.md\#foot\_pcs) is created by repeatedly
progressing upwards by
\[`interval_cycle`\](docs/settings.md\#interval\_cycle). See
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
audio\](docs/resources/m4as/harmony\_example6.m4a) [Click to open this
example in the web
app](http://malcolmsailor.pythonanywhere.com/?seed=2&pattern_len=4&consonance_treatment=none&harmony_len=4&output_path=EFFRHY%2Fdocs%2Fexamples%2Fmidi%2F&overwrite=y&force_foot_in_bass=first_beat&extend_bass_range_for_foots=7&voice_lead_chord_tones=y&onset_density=0.7&dur_density=0.7&unison_weighted_as=SECOND&randomly_distribute_between_choirs=y&length_choir_segments=0.25&tempo=132&choirs_separate_tracks=n&max_consec_seg_from_same_choir=0&preserve_foot_in_bass=none&scales=MAJOR_SCALE%2C&chords=MAJOR_TRIAD%2C&num_harmonies=4&interval_cycle=PERFECT_4TH&foot_pcs=Eb%2C)

\[`interval_cycle`\](docs/settings.md\#interval\_cycle) can also consist
of more than one interval, as in
<a href="#harmony_example7">`docs/examples/harmony_example7.py`</a>.
(Note that, since the intervals in
\[`interval_cycle`\](docs/settings.md\#interval\_cycle) are always
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
audio\](docs/resources/m4as/harmony\_example7.m4a) [Click to open this
example in the web
app](http://malcolmsailor.pythonanywhere.com/?seed=2&pattern_len=4&consonance_treatment=none&harmony_len=4&output_path=EFFRHY%2Fdocs%2Fexamples%2Fmidi%2F&overwrite=y&force_foot_in_bass=first_beat&extend_bass_range_for_foots=7&voice_lead_chord_tones=y&onset_density=0.7&dur_density=0.7&unison_weighted_as=SECOND&randomly_distribute_between_choirs=y&length_choir_segments=0.25&tempo=132&choirs_separate_tracks=n&max_consec_seg_from_same_choir=0&preserve_foot_in_bass=none&scales=MAJOR_SCALE%2C&chords=MAJOR_TRIAD%2C&num_harmonies=4&interval_cycle=PERFECT_4TH%2C+MINOR_6TH&foot_pcs=Eb%2C)

Before concluding this introduction to specifying harmonies, I should
add a few words about what the script actually does with
\[`chords`\](docs/settings.md\#chords) and
\[`scales`\](docs/settings.md\#scales).

  - \[`scales`\](docs/settings.md\#scales) are used unconditionally:
    during each harmony, pitches are drawn exclusively from the
    associated scale. When a pattern is voice-led from one harmony to
    another, a bijective mapping is effected between the associated
    scales.
  - the use of \[`chords`\](docs/settings.md\#chords) is more
    contingent. The most important relevant settings are
      - if
        \[`chord_tone_selection`\](docs/settings.md\#chord\_tone\_selection)
        is `True`, then when constructing the initial pattern, the
        script probabilistically decides whether each note should be a
        chord-tone (according to \[parameters that you
        specify\](docs/settings.md\#chord-tone-settings)).
      - if
        \[`voice_lead_chord_tones`\](docs/settings.md\#voice\_lead\_chord\_tones)
        is `True`, then when voice-leading the pattern over subsequent
        harmonies, the script will ensure that chord-tones are mapped to
        chord-tones (and non-chord-tones to non-chord-tones).

In the preceding examples of this section both
\[`chord_tone_selection`\](docs/settings.md\#chord\_tone\_selection) and
\[`voice_lead_chord_tones`\](docs/settings.md\#voice\_lead\_chord\_tones)
have been `True`. As a contrasting illustration,
<a href="#harmony_example8">`docs/examples/harmony_example8.py`</a>
repeats the settings of
<a href="#harmony_example6">`docs/examples/harmony_example6.py`</a>,
with the sole difference that
\[`voice_lead_chord_tones`\](docs/settings.md\#voice\_lead\_chord\_tones)
is now set to `False`. (Note, however, that the settings
`force_foot_in_bass = True` and `extend_bass_range_for_foots = 7` in
`examples/harmony_example_base.py` are still causing the foot of each
scale/chord to sound on beat one of each harmony.)

<span id="harmony_example8">**Example:**
`docs/examples/harmony_example8.py`</span><br>\[&#1;
notation\](docs/resources/svgs/harmony\_example8.svg){class=“notation”}
\[&#1; piano
roll\](docs/resources/pngs/harmony\_example8\_00001.png){class=“piano\_roll”
style=“max-height: 300px”} \[&#1;
audio\](docs/resources/m4as/harmony\_example8.m4a) [Click to open this
example in the web
app](http://malcolmsailor.pythonanywhere.com/?seed=2&pattern_len=4&consonance_treatment=none&harmony_len=4&output_path=EFFRHY%2Fdocs%2Fexamples%2Fmidi%2F&overwrite=y&force_foot_in_bass=first_beat&extend_bass_range_for_foots=7&voice_lead_chord_tones=n&onset_density=0.7&dur_density=0.7&unison_weighted_as=SECOND&randomly_distribute_between_choirs=y&length_choir_segments=0.25&tempo=132&choirs_separate_tracks=n&max_consec_seg_from_same_choir=0&preserve_foot_in_bass=none&scales=MAJOR_SCALE%2C&chords=MAJOR_TRIAD%2C&num_harmonies=4&interval_cycle=PERFECT_4TH&foot_pcs=Eb%2C)

<a href="#harmony_example9">`docs/examples/harmony_example9.py`</a> is
similar, but with `chord_tone_selection = False` as well.

<span id="harmony_example9">**Example:**
`docs/examples/harmony_example9.py`</span><br>\[&#1;
notation\](docs/resources/svgs/harmony\_example9.svg){class=“notation”}
\[&#1; piano
roll\](docs/resources/pngs/harmony\_example9\_00001.png){class=“piano\_roll”
style=“max-height: 300px”} \[&#1;
audio\](docs/resources/m4as/harmony\_example9.m4a) [Click to open this
example in the web
app](http://malcolmsailor.pythonanywhere.com/?seed=2&pattern_len=4&consonance_treatment=none&harmony_len=4&output_path=EFFRHY%2Fdocs%2Fexamples%2Fmidi%2F&overwrite=y&force_foot_in_bass=first_beat&extend_bass_range_for_foots=7&voice_lead_chord_tones=n&onset_density=0.7&dur_density=0.7&unison_weighted_as=SECOND&randomly_distribute_between_choirs=y&length_choir_segments=0.25&tempo=132&choirs_separate_tracks=n&max_consec_seg_from_same_choir=0&preserve_foot_in_bass=none&scales=MAJOR_SCALE%2C&chords=MAJOR_TRIAD%2C&num_harmonies=4&interval_cycle=PERFECT_4TH&foot_pcs=Eb%2C&chord_tone_selection=n)

### Specifying rhythms

Besides setting \[`rhythm_len`\](docs/settings.md\#rhythm\_len) as we
did [above](#how-it-works), there are many other ways of controlling the
rhythms that are produced.\[5\]

To begin with, we have
\[`onset_subdivision`\](docs/settings.md\#onset\_subdivision) and
\[`onset_density`\](docs/settings.md\#onset\_density):

  - \[`onset_subdivision`\](docs/settings.md\#onset\_subdivision)
    indicates the basic “grid” on which note onsets can take place,
    measured in quarter notes.
  - \[`onset_density`\](docs/settings.md\#onset\_density) indicates the
    proportion of grid points that should have an onset.

So for example, in
<a href="#rhythm_example1">`docs/examples/rhythm_example1.py`</a>,
`"onset_subdivision" = 1/4` indicates a sixteenth-note grid, and
`"onset_density" = 1.0` indicates that every point in the grid should
have an onset, creating a *moto perpetuo* texture. (For clarity/brevity,
this example has only one voice.)

    {
    "num_voices": 1,
    "onset_density": 0.5,
    "onset_subdivision": 1/4,
    }

<span id="rhythm_example1">**Example:**
`docs/examples/rhythm_example1.py`</span><br>\[&#1;
notation\](docs/resources/svgs/rhythm\_example1.svg){class=“notation”}
\[&#1; piano
roll\](docs/resources/pngs/rhythm\_example1\_00001.png){class=“piano\_roll”
style=“max-height: 300px”} \[&#1;
audio\](docs/resources/m4as/rhythm\_example1.m4a) [Click to open this
example in the web
app](http://malcolmsailor.pythonanywhere.com/?seed=0&pattern_len=4&num_harmonies=3&harmony_len=4%2C+2%2C+2&num_reps_super_pattern=4&foot_pcs=6&interval_cycle=4&voice_ranges=AUTHENTIC_OCTAVES+%2A+D+%2A+OCTAVE3&scales=PENTATONIC_SCALE&force_foot_in_bass=global_first_note&max_repeated_notes=0&forbidden_intervals=0%2C&output_path=EFFRHY%2Fdocs%2Fexamples%2Fmidi%2F&overwrite=y&randomly_distribute_between_choirs=n&tempo=120&onset_density=1.0&dur_density=1.0&max_consec_seg_from_same_choir=0&length_choir_segments=1&preserve_foot_in_bass=none&chords=MAJOR_TRIAD&voice_lead_chord_tones=n&num_voices=1&onset_subdivision=0.25)

If we reduce \[`onset_density`\](docs/settings.md\#onset\_density), as
in <a href="#rhythm_example2">`docs/examples/rhythm_example2.py`</a>,
the proportion of the sixteenth-grid that is filled with onsets will be
correspondingly reduced.

    {
        "num_voices": 1,
        "onset_density": 0.5,
        "onset_subdivision": 1 / 4,
    }

<span id="rhythm_example2">**Example:**
`docs/examples/rhythm_example2.py`</span><br>\[&#1;
notation\](docs/resources/svgs/rhythm\_example2.svg){class=“notation”}
\[&#1; piano
roll\](docs/resources/pngs/rhythm\_example2\_00001.png){class=“piano\_roll”
style=“max-height: 300px”} \[&#1;
audio\](docs/resources/m4as/rhythm\_example2.m4a) [Click to open this
example in the web
app](http://malcolmsailor.pythonanywhere.com/?seed=0&pattern_len=4&num_harmonies=3&harmony_len=4%2C+2%2C+2&num_reps_super_pattern=4&foot_pcs=6&interval_cycle=4&voice_ranges=AUTHENTIC_OCTAVES+%2A+D+%2A+OCTAVE3&scales=PENTATONIC_SCALE&force_foot_in_bass=global_first_note&max_repeated_notes=0&forbidden_intervals=0%2C&output_path=EFFRHY%2Fdocs%2Fexamples%2Fmidi%2F&overwrite=y&randomly_distribute_between_choirs=n&tempo=120&onset_density=0.5&dur_density=1.0&max_consec_seg_from_same_choir=0&length_choir_segments=1&preserve_foot_in_bass=none&chords=MAJOR_TRIAD&voice_lead_chord_tones=n&num_voices=1&onset_subdivision=0.25)

Another important rhythmic parameter is
\[`dur_density`\](docs/settings.md\#dur\_density). It specifies the
proportion of time that should be filled by note durations, irrespective
of how many onsets there are. So far we have left
\[`dur_density`\](docs/settings.md\#dur\_density) at the default value
of `1.0`, which means that all notes last until the next onset in that
voice. (In musical terms, all notes are *legato*.) If we decrease it to
0.75, as in
<a href="#rhythm_example3">`docs/examples/rhythm_example3.py`</a>, some
of the notes will become shorter, so that 75% of the total time of the
rhythm is filled by sounding notes.

    {
        "num_voices": 1,
        "onset_density": 0.5,
        "dur_density": 0.75,
        "onset_subdivision": 1 / 4,
    }}

<span id="rhythm_example3">**Example:**
`docs/examples/rhythm_example3.py`</span><br>\[&#1;
notation\](docs/resources/svgs/rhythm\_example3.svg){class=“notation”}
\[&#1; piano
roll\](docs/resources/pngs/rhythm\_example3\_00001.png){class=“piano\_roll”
style=“max-height: 300px”} \[&#1;
audio\](docs/resources/m4as/rhythm\_example3.m4a) [Click to open this
example in the web
app](http://malcolmsailor.pythonanywhere.com/?seed=0&pattern_len=4&num_harmonies=3&harmony_len=4%2C+2%2C+2&num_reps_super_pattern=4&foot_pcs=6&interval_cycle=4&voice_ranges=AUTHENTIC_OCTAVES+%2A+D+%2A+OCTAVE3&scales=PENTATONIC_SCALE&force_foot_in_bass=global_first_note&max_repeated_notes=0&forbidden_intervals=0%2C&output_path=EFFRHY%2Fdocs%2Fexamples%2Fmidi%2F&overwrite=y&randomly_distribute_between_choirs=n&tempo=120&onset_density=0.5&dur_density=0.75&max_consec_seg_from_same_choir=0&length_choir_segments=1&preserve_foot_in_bass=none&chords=MAJOR_TRIAD&voice_lead_chord_tones=n&num_voices=1&onset_subdivision=0.25)

To obtain a *staccato* effect, we can make
\[`dur_density`\](docs/settings.md\#dur\_density) still shorter, but to
obtain *really* short notes, we may have to adjust
\[`min_dur`\](docs/settings.md\#min\_dur) as well, which sets the
minimum duration of each pitch as well.

    {
        "num_voices": 1,
        "onset_density": 0.5,
        "dur_density": 0.25,
        "min_dur": 1/8,
        "onset_subdivision": 1 / 4,
    }

<span id="rhythm_example4">**Example:**
`docs/examples/rhythm_example4.py`</span><br>\[&#1;
notation\](docs/resources/svgs/rhythm\_example4.svg){class=“notation”}
\[&#1; piano
roll\](docs/resources/pngs/rhythm\_example4\_00001.png){class=“piano\_roll”
style=“max-height: 300px”} \[&#1;
audio\](docs/resources/m4as/rhythm\_example4.m4a) [Click to open this
example in the web
app](http://malcolmsailor.pythonanywhere.com/?seed=0&pattern_len=4&num_harmonies=3&harmony_len=4%2C+2%2C+2&num_reps_super_pattern=4&foot_pcs=6&interval_cycle=4&voice_ranges=AUTHENTIC_OCTAVES+%2A+D+%2A+OCTAVE3&scales=PENTATONIC_SCALE&force_foot_in_bass=global_first_note&max_repeated_notes=0&forbidden_intervals=0%2C&output_path=EFFRHY%2Fdocs%2Fexamples%2Fmidi%2F&overwrite=y&randomly_distribute_between_choirs=n&tempo=120&onset_density=0.5&dur_density=0.25&max_consec_seg_from_same_choir=0&length_choir_segments=1&preserve_foot_in_bass=none&chords=MAJOR_TRIAD&voice_lead_chord_tones=n&num_voices=1&min_dur=0.125&onset_subdivision=0.25)

We can change `"onset_subdivision"` as well. For example, to have a grid
of eighth-note triplets, we would set `"onset_subdivision" = 1/3`. And
since computers have no problem with precise, strange rhythms, we could
also set it to unusual values like `5/13` or `math.pi / 12`.\[6\]

    {
        "num_voices": 1,
        "onset_density": 0.75,
        "dur_density": 0.25,
        "min_dur": 1/8,
        "onset_subdivision": 3/ 13,
    }

<span id="rhythm_example5">**Example:**
`docs/examples/rhythm_example5.py`</span><br>\[&#1; piano
roll\](docs/resources/pngs/rhythm\_example5\_00001.png){class=“piano\_roll”
style=“max-height: 300px”} \[&#1;
audio\](docs/resources/m4as/rhythm\_example5.m4a) [Click to open this
example in the web
app](http://malcolmsailor.pythonanywhere.com/?seed=0&pattern_len=4&num_harmonies=3&harmony_len=4%2C+2%2C+2&num_reps_super_pattern=4&foot_pcs=6&interval_cycle=4&voice_ranges=AUTHENTIC_OCTAVES+%2A+D+%2A+OCTAVE3&scales=PENTATONIC_SCALE&force_foot_in_bass=global_first_note&max_repeated_notes=0&forbidden_intervals=0%2C&output_path=EFFRHY%2Fdocs%2Fexamples%2Fmidi%2F&overwrite=y&randomly_distribute_between_choirs=n&tempo=120&onset_density=0.75&dur_density=0.25&max_consec_seg_from_same_choir=0&length_choir_segments=1&preserve_foot_in_bass=none&chords=MAJOR_TRIAD&voice_lead_chord_tones=n&num_voices=1&min_dur=0.125&onset_subdivision=0.23076923076923078)

All of the settings we have been looking at so far are “per-voice”,
meaning that they can be set to a different value in each voice. If we
set \[`onset_subdivision`\](docs/settings.md\#onset\_subdivision) to a
different unusual value in each voice, we get a particularly chaotic
effect. (I find that the chaos can be reined in a bit by setting
\[`rhythm_len`\](docs/settings.md\#rhythm\_len) to a short value,
creating a brief rhythmic loop.)

    {
        "rhythm_len": 1,
        "num_voices": 3,
        "onset_density": [0.25, 0.5, 0.75],
        "dur_density": [0.25, 0.5, 0.25],
        "min_dur": [0.25, 0.25, 1/8],
        "onset_subdivision": [3/ 13, 5/12, 6/11],
    }

<span id="rhythm_example6">**Example:**
`docs/examples/rhythm_example6.py`</span><br>\[&#1; piano
roll\](docs/resources/pngs/rhythm\_example6\_00001.png){class=“piano\_roll”
style=“max-height: 300px”} \[&#1;
audio\](docs/resources/m4as/rhythm\_example6.m4a) [Click to open this
example in the web
app](http://malcolmsailor.pythonanywhere.com/?seed=0&pattern_len=4&num_harmonies=3&harmony_len=4%2C+2%2C+2&num_reps_super_pattern=4&foot_pcs=6&interval_cycle=4&voice_ranges=AUTHENTIC_OCTAVES+%2A+D+%2A+OCTAVE3&scales=PENTATONIC_SCALE&force_foot_in_bass=global_first_note&max_repeated_notes=0&forbidden_intervals=0%2C&output_path=EFFRHY%2Fdocs%2Fexamples%2Fmidi%2F&overwrite=y&randomly_distribute_between_choirs=n&tempo=120&onset_density=0.4%2C+0.5%2C+0.75&dur_density=0.4%2C+0.5%2C+0.25&max_consec_seg_from_same_choir=0&length_choir_segments=1&preserve_foot_in_bass=none&chords=MAJOR_TRIAD&voice_lead_chord_tones=n&num_voices=3&min_dur=0.25%2C+0.25%2C+0.125&onset_subdivision=0.23076923076923078%2C+0.4166666666666667%2C+0.5454545454545454)

There are also a few settings that govern the relation between different
voices. If \[`hocketing`\](docs/settings.md\#hocketing) is `True`, then,
to the extent possible, the onsets of each voice will occur when there
is no onset in any other voice. (In textures with many voices, it is
also possible to assign specific pairs of voices to hocket with one
another.)

    {
        "num_voices": 2,
        "onset_density": 0.4,
        "dur_density": 0.4,
        "min_dur": 0.25,
        "onset_subdivision": 0.25,
        "hocketing": True,
    }

<span id="rhythm_example7">**Example:**
`docs/examples/rhythm_example7.py`</span><br>\[&#1;
notation\](docs/resources/svgs/rhythm\_example7.svg){class=“notation”}
\[&#1; piano
roll\](docs/resources/pngs/rhythm\_example7\_00001.png){class=“piano\_roll”
style=“max-height: 300px”} \[&#1;
audio\](docs/resources/m4as/rhythm\_example7.m4a) [Click to open this
example in the web
app](http://malcolmsailor.pythonanywhere.com/?seed=0&pattern_len=4&num_harmonies=3&harmony_len=4%2C+2%2C+2&num_reps_super_pattern=4&foot_pcs=6&interval_cycle=4&voice_ranges=AUTHENTIC_OCTAVES+%2A+D+%2A+OCTAVE3&scales=PENTATONIC_SCALE&force_foot_in_bass=global_first_note&max_repeated_notes=0&forbidden_intervals=0%2C&output_path=EFFRHY%2Fdocs%2Fexamples%2Fmidi%2F&overwrite=y&randomly_distribute_between_choirs=n&tempo=120&onset_density=0.4&dur_density=0.4&max_consec_seg_from_same_choir=0&length_choir_segments=1&preserve_foot_in_bass=none&chords=MAJOR_TRIAD&voice_lead_chord_tones=n&num_voices=2&min_dur=0.25&onset_subdivision=0.25&hocketing=y)

Another setting that governs the rhythmic relation between voices is
\[`rhythmic_unison`\](docs/settings.md\#rhythmic\_unison), which causes
voices to have exactly the same rhythm. (Like
\[`hocketing`\](docs/settings.md\#hocketing), it can be provided a
boolean, or a list of tuples of voices; see the settings documentation
for more details.)

    {
        "num_voices": 3,
        "rhythmic_unison": True,
        "onset_density": .7,
        "dur_density": 0.6,
        "min_dur": 0.25,
        "onset_subdivision": 1/4,
    }

<span id="rhythm_example8">**Example:**
`docs/examples/rhythm_example8.py`</span><br>\[&#1;
notation\](docs/resources/svgs/rhythm\_example8.svg){class=“notation”}
\[&#1; piano
roll\](docs/resources/pngs/rhythm\_example8\_00001.png){class=“piano\_roll”
style=“max-height: 300px”} \[&#1;
audio\](docs/resources/m4as/rhythm\_example8.m4a) [Click to open this
example in the web
app](http://malcolmsailor.pythonanywhere.com/?seed=0&pattern_len=4&num_harmonies=3&harmony_len=4%2C+2%2C+2&num_reps_super_pattern=4&foot_pcs=6&interval_cycle=4&voice_ranges=AUTHENTIC_OCTAVES+%2A+D+%2A+OCTAVE3&scales=PENTATONIC_SCALE&force_foot_in_bass=global_first_note&max_repeated_notes=0&forbidden_intervals=0%2C&output_path=EFFRHY%2Fdocs%2Fexamples%2Fmidi%2F&overwrite=y&randomly_distribute_between_choirs=n&tempo=120&onset_density=0.7&dur_density=0.6&max_consec_seg_from_same_choir=0&length_choir_segments=1&preserve_foot_in_bass=none&chords=MAJOR_TRIAD&voice_lead_chord_tones=n&num_voices=3&rhythmic_unison=y&min_dur=0.25&onset_subdivision=0.25)

When \[`rhythmic_unison`\](docs/settings.md\#rhythmic\_unison) is
applied, rhythmic settings like
\[`onset_density`\](docs/settings.md\#onset\_density) only have any
effect in the “leader” voice, whose rhythm is simply copied into the
other voices. If we wanted to specify a different
\[`onset_density`\](docs/settings.md\#onset\_density) in a “follower”
voice, it would be ignored. This situation would call for the related
setting
\[`rhythmic_quasi_unison`\](docs/settings.md\#rhythmic\_quasi\_unison).
When
\[`rhythmic_quasi_unison`\](docs/settings.md\#rhythmic\_quasi\_unison)
applies, then, instead of copying the “leader” rhythm into the
“follower” voices, the onsets of the “follower” voices are
constrained so far as possible to coincide with those of the “leader.”
In <a href="#rhythm_example9">`docs/examples/rhythm_example9.py`</a>,
the leader is the bass voice (midi guitar). The middle voice (midi
piano) has a *lower*
\[`onset_density`\](docs/settings.md\#onset\_density), and the top voice
(midi electric piano) has a *higher*
\[`onset_density`\](docs/settings.md\#onset\_density).

    {
        "num_voices": 3,
        "rhythmic_quasi_unison": True,
        "onset_density": [0.5, 0.4, 0.6],
        "dur_density": [0.5, 0.4, 0.6],
        "min_dur": 0.25,
        "onset_subdivision": 1 / 4,
    }

<span id="rhythm_example9">**Example:**
`docs/examples/rhythm_example9.py`</span><br>\[&#1;
notation\](docs/resources/svgs/rhythm\_example9.svg){class=“notation”}
\[&#1; piano
roll\](docs/resources/pngs/rhythm\_example9\_00001.png){class=“piano\_roll”
style=“max-height: 300px”} \[&#1;
audio\](docs/resources/m4as/rhythm\_example9.m4a) [Click to open this
example in the web
app](http://malcolmsailor.pythonanywhere.com/?seed=0&pattern_len=4&num_harmonies=3&harmony_len=4%2C+2%2C+2&num_reps_super_pattern=4&foot_pcs=6&interval_cycle=4&voice_ranges=AUTHENTIC_OCTAVES+%2A+D+%2A+OCTAVE3&scales=PENTATONIC_SCALE&force_foot_in_bass=global_first_note&max_repeated_notes=0&forbidden_intervals=0%2C&output_path=EFFRHY%2Fdocs%2Fexamples%2Fmidi%2F&overwrite=y&randomly_distribute_between_choirs=n&tempo=120&onset_density=0.5%2C+0.4%2C+0.6&dur_density=0.5%2C+0.4%2C+0.6&max_consec_seg_from_same_choir=0&length_choir_segments=1&preserve_foot_in_bass=none&chords=MAJOR_TRIAD&voice_lead_chord_tones=n&num_voices=3&rhythmic_quasi_unison=y&min_dur=0.25&onset_subdivision=0.25)

We can obtain more explicit control of the rhythms through the
\[`obligatory_onsets`\](docs/settings.md\#obligatory\_onsets) setting,
which specifies a sequence of times at which the rhythms will be
“obliged” to have a note onset. It’s also necessary to specify
\[`obligatory_onsets_modulo`\](docs/settings.md\#obligatory\_onsets\_modulo)
in order to specify when these onsets should repeat (e.g., every two
beats).

For example, in
<a href="#rhythm_example10">`docs/examples/rhythm_example10.py`</a>,
I’ve set \[`obligatory_onsets`\](docs/settings.md\#obligatory\_onsets)
to `[0, 0.75, 1.5]` and
\[`obligatory_onsets_modulo`\](docs/settings.md\#obligatory\_onsets\_modulo)
to `2` in order to specify a *tresillo* 3–3–2 rhythm. Since the value of
\[`onset_density`\](docs/settings.md\#onset\_density) implies more than
three onsets every two beats, additional onsets are added to the
underlying scaffold supplied by the values in
\[`obligatory_onsets`\](docs/settings.md\#obligatory\_onsets).

    {
        "num_voices": 3,
        "obligatory_onsets": [0, 0.75, 1.5],
        "obligatory_onsets_modulo": 2,
        "onset_density": 0.5,
        "dur_density": 0.5,
        "min_dur": 0.25,
        "onset_subdivision": 0.25,
    }

<span id="rhythm_example10">**Example:**
`docs/examples/rhythm_example10.py`</span><br>\[&#1;
notation\](docs/resources/svgs/rhythm\_example10.svg){class=“notation”}
\[&#1; piano
roll\](docs/resources/pngs/rhythm\_example10\_00001.png){class=“piano\_roll”
style=“max-height: 300px”} \[&#1;
audio\](docs/resources/m4as/rhythm\_example10.m4a) [Click to open this
example in the web
app](http://malcolmsailor.pythonanywhere.com/?seed=0&pattern_len=4&num_harmonies=3&harmony_len=4%2C+2%2C+2&num_reps_super_pattern=4&foot_pcs=6&interval_cycle=4&voice_ranges=AUTHENTIC_OCTAVES+%2A+D+%2A+OCTAVE3&scales=PENTATONIC_SCALE&force_foot_in_bass=global_first_note&max_repeated_notes=0&forbidden_intervals=0%2C&output_path=EFFRHY%2Fdocs%2Fexamples%2Fmidi%2F&overwrite=y&randomly_distribute_between_choirs=n&tempo=120&onset_density=0.5&dur_density=0.5&max_consec_seg_from_same_choir=0&length_choir_segments=1&preserve_foot_in_bass=none&chords=MAJOR_TRIAD&voice_lead_chord_tones=n&num_voices=3&obligatory_onsets=0%2C+0.75%2C+1.5&obligatory_onsets_modulo=2&min_dur=0.25&onset_subdivision=0.25)

It is possible to specify an irregular grid upon which note onsets will
take place using
\[`sub_subdivisions`\](docs/settings.md\#sub\_subdivisions). This
setting takes a sequence of integers and subdivides the grid specified
by \[`onset_subdivision`\](docs/settings.md\#onset\_subdivision) into
parts defined by the ratio of these integers. For example, in
<a href="#rhythm_example11">`docs/examples/rhythm_example11.py`</a>
below, \[`sub_subdivisions`\](docs/settings.md\#sub\_subdivisions) is
`[4,3]`, which creates an uneven “swing” feel where every first note is
4/3rds as long as every second note.\[^To keep the number of total
onsets consistent, you’ll probably want to increase
\[`onset_subdivision`\](docs/settings.md\#onset\_subdivision) by taking
the value you otherwise would have chosen and multiplying it by the
length of \[`sub_subdivisions`\](docs/settings.md\#sub\_subdivisions).\]
You’ll notice that
<a href="#rhythm_example11">`docs/examples/rhythm_example11.py`</a> is
precisely the same as
<a href="#rhythm_example1">`docs/examples/rhythm_example1.py`</a>,
except for the uneven rhythms.

    {
        "num_voices": 1,
        "onset_density": 1.0,
        "onset_subdivision": 0.5,
        "sub_subdivisions": [4, 3],
    }

<span id="rhythm_example11">**Example:**
`docs/examples/rhythm_example11.py`</span><br>\[&#1; piano
roll\](docs/resources/pngs/rhythm\_example11\_00001.png){class=“piano\_roll”
style=“max-height: 300px”} \[&#1;
audio\](docs/resources/m4as/rhythm\_example11.m4a) [Click to open this
example in the web
app](http://malcolmsailor.pythonanywhere.com/?seed=0&pattern_len=4&num_harmonies=3&harmony_len=4%2C+2%2C+2&num_reps_super_pattern=4&foot_pcs=6&interval_cycle=4&voice_ranges=AUTHENTIC_OCTAVES+%2A+D+%2A+OCTAVE3&scales=PENTATONIC_SCALE&force_foot_in_bass=global_first_note&max_repeated_notes=0&forbidden_intervals=0%2C&output_path=EFFRHY%2Fdocs%2Fexamples%2Fmidi%2F&overwrite=y&randomly_distribute_between_choirs=n&tempo=120&onset_density=1.0&dur_density=1.0&max_consec_seg_from_same_choir=0&length_choir_segments=1&preserve_foot_in_bass=none&chords=MAJOR_TRIAD&voice_lead_chord_tones=n&num_voices=1&onset_subdivision=0.5&sub_subdivisions=4%2C+3)

I think, however, that it is more interesting to experiment with values
of \[`sub_subdivisions`\](docs/settings.md\#sub\_subdivisions) that are
further from what a human would be likely to produce, as I have tried to
do in
<a href="#rhythm_example12">`docs/examples/rhythm_example12.py`</a>.

    {
        "num_voices": 3,
        "onset_density": 0.4,
        "onset_subdivision": 2,
        "sub_subdivisions": [12, 13, 11, 15, 17, 10],
        "obligatory_onsets": 0,
        "obligatory_onsets_modulo": 2,
        "hocketing": True,
    }

<span id="rhythm_example12">**Example:**
`docs/examples/rhythm_example12.py`</span><br>\[&#1; piano
roll\](docs/resources/pngs/rhythm\_example12\_00001.png){class=“piano\_roll”
style=“max-height: 300px”} \[&#1;
audio\](docs/resources/m4as/rhythm\_example12.m4a) [Click to open this
example in the web
app](http://malcolmsailor.pythonanywhere.com/?seed=0&pattern_len=4&num_harmonies=3&harmony_len=4%2C+2%2C+2&num_reps_super_pattern=4&foot_pcs=6&interval_cycle=4&voice_ranges=AUTHENTIC_OCTAVES+%2A+D+%2A+OCTAVE3&scales=PENTATONIC_SCALE&force_foot_in_bass=global_first_note&max_repeated_notes=0&forbidden_intervals=0%2C&output_path=EFFRHY%2Fdocs%2Fexamples%2Fmidi%2F&overwrite=y&randomly_distribute_between_choirs=n&tempo=120&onset_density=0.4&dur_density=1.0&max_consec_seg_from_same_choir=0&length_choir_segments=1&preserve_foot_in_bass=none&chords=MAJOR_TRIAD&voice_lead_chord_tones=n&num_voices=3&onset_subdivision=2&sub_subdivisions=12%2C+13%2C+11%2C+15%2C+17%2C+10&obligatory_onsets=0&obligatory_onsets_modulo=2&hocketing=y)

## Filters and transformers

`TODO`

1.  You can find the settings files that generated all the examples in
    this section in the `docs/examples` folder.
    `docs/examples/example_base.py` is shared among each example. So you
    can build the first example with the command `python3 -m
    efficient_rhythms --settings docs/examples/example_base.py
    docs/examples/example1.py`; for subsequent examples, just replace
    `example1.py` with the appropriate file.

2.  The music-theoretically fastidious among you may have observed that
    these examples contain plentiful parallel fifths (for example, the
    first two sixteenth-notes in
    <a href="#example2">`docs/examples/example2.py`</a>). If desired,
    parallel fifths could be avoided by including `7` (i.e., the number
    of semitones in a perfect fifth) in the sequence provided to the
    setting
    \[`prohibit_parallels`\](docs/settings.md\#prohibit\_parallels).

3.  The settings files that generated the examples in this section all
    begin with `harmony_example` and are found in the `docs/examples`
    folder. `docs/examples/harmony_example_base.py` is shared among each
    example. So you can build the first example with the command
    `python3 -m efficient_rhythms --settings
    docs/examples/harmony_example_base.py
    docs/examples/harmony_example1.py`.

4.  There is a technical reason for this constraint, (namely, that the
    script works by finding bijective voice-leadings between chords and
    scales), but in the longterm, I would very much like to remove it.

5.  The settings files that generated the examples in this section all
    begin with `rhythm_example` and are found in the `docs/examples`
    folder. `docs/examples/rhythm_example_base.py` is shared among each
    example. So you can build the first example with the command
    `python3 -m efficient_rhythms --settings
    docs/examples/rhythm_example_base.py
    docs/examples/rhythm_example1.py`.

6.  However, we’ll have to give up on representing these in conventional
    music notation. In fact, for the time being only duple note-values
    (i.e., eighth-notes, quarter-notes, and the like) can be exported to
    notation.
