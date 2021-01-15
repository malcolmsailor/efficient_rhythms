

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
- _get_attack_array can use weighted choices to generate rhythm.
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
