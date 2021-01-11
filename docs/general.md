## General functioning

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
