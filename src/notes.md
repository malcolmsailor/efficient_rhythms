<!-- These are notes for the developer -->

LONGTERM
- consider shorter values of pattern_len as part of the initial pattern so that the voice-leading of these sections isn't so difficult, addressing:

    We can also have different values of `pattern_len` in each voice, as in REF:example5. However, if we do so, the script has to work quite a bit harder to find a solution.[^smarter] To help it do so, I made its task a little easier by changing  [`consonance_treatment`](settings.html#consonance_treatment) from `"all_onsets"` to `"none"`. (Thus whereas in the previous examples, the simultaneously onseted notes all formed intervals like 3rds and fifths, in example 5, there are also dissonances like 7ths and 9ths.)

    [^smarter]: If the algorithm were a little smarter, it wouldn't have to work nearly so hard to cope with voices of different `pattern_len`. So this is a longterm to-do.


Wishlist:
- freeze
    - "generic pattern", changing harmony but leaving generic intervals
     and rhythms intact
    - "initial pattern"
    - rhythms
    - super_pattern
    - complete_pattern
- Boolean to allow checking voice ranges against each other to find
    portion of range that is compatible with passing material between
    voices and a given interval, and, related:
- Invertible counterpoint, canons.
- Consonance settings only apply on certain beats.
- Motives: either rhythmic, melodic or both.
- Setting to force notes that extend more than a certain duration into
    the next harmony to be common tones.
- "Hard" and "soft" voice ranges
    - the latter apply to the basic pattern; the former are applied
      to voice-leading, etc.
- Boolean per voice to break durations that cross harmony changes.
- _get_onset_array can use weighted choices to generate rhythm.
- Maximum bound on parallel_voice_leading.
- Truncate patterns by harmonies
- Consonance treatment on notes that overlap with repetition of super
    pattern.
- Define melodic shapes by means of curves.
    - The curves can be functions over a given interval: the first
        pitch is (an approximation of) the function's value at the
        start of the interval, and the last pitch at the end. The
        high pitch has the function's maximum over the interval
        and low pitch its minimum. Perhaps different amounts of
        noise in the function can lead to smoother or more jagged
        melodic curves.
- Allow multi-set chords.
- Allow chords of different cardinality.
- Don't distribute out-of-range notes to choirs.
