  - [Pitch-class constants](#pitch-class-constants)
      - [Just pitch-class constants](#just-pitch-class-constants)
  - [Interval constants](#interval-constants)
  - [Chord constants](#chord-constants)
  - [Scale constants](#scale-constants)
  - [Voice range constants](#voice-range-constants)
  - [Octave constants](#octave-constants)
  - [Consonances constants](#consonances-constants)
  - [General-midi program constants](#general-midi-program-constants)

When specifying pitch materials like chords, scales, and intervals, as
well as when specifying general-midi instruments, the constants defined
in `src/er_constants.py` can be used. For ease of reference, these
constants are also listed below.

In settings files, these constants can be indicated in either of the
following ways:

1.  As Python identifiers, e.g., `C * MAJOR_SCALE`
2.  As strings, e.g., `"C * MAJOR_SCALE"`

The only advantage of using strings is that you can use the `#`
character to indicate sharps. So `"C# * MAJOR_SCALE"` or `"C## *
MAJOR_SCALE"` will work as expected, but `C# * MAJOR_SCALE` won’t work
because `#` is not a legal character in Python identifiers. (Everything
after `#` will be understood as a comment.)

TODO document just and tempered pitch constants.

# Pitch-class constants

## Just pitch-class constants

Natural pitch-class constants.

    C = 1.0
    D = 9 / 8
    E = 5 / 4
    F = 4 / 3
    G = 3 / 2
    A = 10 / 6
    B = 15 / 8

Flats and sharps are here defined as the difference between a just major
and a just minor third.

    FLAT = 24 / 25
    SHARP = 25 / 24

Flat and sharp pitch-class constants. (In user settings, “\#” only works
in strings, where it will be replaced by ‘\_SHARP’, since ‘\#’ isn’t a
valid character in Python identifiers)

    Cb = C * FLAT
    Db = D * FLAT
    Eb = E * FLAT
    Fb = F * FLAT
    Gb = G * FLAT
    Ab = A * FLAT
    Bb = B * FLAT
    C# = C_SHARP = C * SHARP
    D# = D_SHARP = D * SHARP
    E# = E_SHARP = E * SHARP
    F# = F_SHARP = F * SHARP
    G# = G_SHARP = G * SHARP
    A# = A_SHARP = A * SHARP
    B# = B_SHARP = B * SHARP

Double-flat and double-sharp pitch-class constants.

    Cbb = C * FLAT * FLAT
    Dbb = D * FLAT * FLAT
    Ebb = E * FLAT * FLAT
    Fbb = F * FLAT * FLAT
    Gbb = G * FLAT * FLAT
    Abb = A * FLAT * FLAT
    Bbb = B * FLAT * FLAT
    C## = C_SHARP_SHARP = C * SHARP * SHARP
    D## = D_SHARP_SHARP = D * SHARP * SHARP
    E## = E_SHARP_SHARP = E * SHARP * SHARP
    F## = F_SHARP_SHARP = F * SHARP * SHARP
    G## = G_SHARP_SHARP = G * SHARP * SHARP
    A## = A_SHARP_SHARP = A * SHARP * SHARP
    B## = B_SHARP_SHARP = B * SHARP * SHARP

# Interval constants

Just-interval constants

    UNISON = PERFECT_UNISON = 1.0
    MINOR_2ND = MINOR_SECOND = 16 / 15
    MAJOR_2ND = MAJOR_SECOND = 9 / 8
    MINOR_3RD = MINOR_THIRD = 6 / 5
    MAJOR_3RD = MAJOR_THIRD = 5 / 4
    PERFECT_4TH = PERFECT_FOURTH = 4 / 3
    DIMINISHED_5TH = DIMINISHED_FIFTH = 4096 / 2916
    PERFECT_5TH = PERFECT_FIFTH = 3 / 2
    MINOR_6TH = MINOR_SIXTH = 8 / 5
    MAJOR_6TH = MAJOR_SIXTH = 10 / 6
    MINOR_7TH = MINOR_SEVENTH = 16 / 9
    MAJOR_7TH = MAJOR_SEVENTH = 15 / 8
    OCTAVE = PERFECT_OCTAVE = 2.0
    MINOR_9TH = MINOR_NINTH = 32 / 15
    MAJOR_9TH = MAJOR_NINTH = 9 / 4
    MINOR_10TH = MINOR_TENTH = 12 / 5
    MAJOR_10TH = MAJOR_TENTH = 5 / 2

Generic-interval constants

    GENERIC_UNISON = 0
    SECOND = GENERIC_SECOND = 1
    THIRD = GENERIC_THIRD = 2
    FOURTH = GENERIC_FOURTH = 3
    FIFTH = GENERIC_FIFTH = 4
    SIXTH = GENERIC_SIXTH = 5
    SEVENTH = GENERIC_SEVENTH = 6
    GENERIC_OCTAVE = 7

Roman-numeral constants. These are defined relative to the major scale,
the way jazz musicians sometimes use them.

    I = UNISON
    bII = MINOR_2ND
    II = MAJOR_2ND
    bIII = MINOR_3RD
    III = MAJOR_3RD
    IV = PERFECT_4TH
    bV = DIMINISHED_5TH
    V = PERFECT_5TH
    bVI = MINOR_6TH
    VI = MAJOR_6TH
    bVII = MINOR_7TH
    VII = MAJOR_7TH

# Chord constants

Triad constants

    MAJOR_TRIAD = np.array([1.0, 5 / 4, 3 / 2])
    MINOR_TRIAD = np.array([1.0, 6 / 5, 3 / 2])
    DIMINISHED_TRIAD = np.array([1.0, 6 / 5, (6 / 5) ** 2])
    AUGMENTED_TRIAD = np.array([1.0, 5 / 4, (5 / 4) ** 2])

Seventh-chord constants

    HALF_DIMINISHED_CHORD = np.array([UNISON, MINOR_3RD, DIMINISHED_5TH, MINOR_7TH])
    DOMINANT_7TH_CHORD = np.array([UNISON, MAJOR_3RD, PERFECT_5TH, MINOR_7TH])
    MAJOR_7TH_CHORD = np.array([UNISON, MAJOR_3RD, PERFECT_5TH, MAJOR_7TH])
    MINOR_7TH_CHORD = np.array([UNISON, MINOR_3RD, PERFECT_5TH, MINOR_7TH])

Incomplete seventh-chord constants

    HALF_DIMINISHED_NO5 = np.array([UNISON, MINOR_3RD, MINOR_7TH])
    HALF_DIMINISHED_NO3 = np.array([UNISON, DIMINISHED_5TH, MINOR_7TH])
    DOMINANT_7TH_NO5 = np.array([UNISON, MAJOR_3RD, MINOR_7TH])
    DOMINANT_7TH_NO3 = np.array([UNISON, PERFECT_5TH, MINOR_7TH])
    MAJOR_7TH_NO5 = np.array([UNISON, MAJOR_3RD, MAJOR_7TH])
    MAJOR_7TH_NO3 = np.array([UNISON, PERFECT_5TH, MAJOR_7TH])
    MINOR_7TH_NO5 = np.array([UNISON, MINOR_3RD, MINOR_7TH])
    MINOR_7TH_NO3 = np.array([UNISON, PERFECT_5TH, MINOR_7TH])

Inverted triad constants

    MAJOR_63 = np.array([1.0, 6 / 5, 8 / 5])
    MINOR_63 = np.array([1.0, 5 / 4, 5 / 3])
    MAJOR_64 = np.array([1.0, 4 / 3, 5 / 3])
    MINOR_64 = np.array([1.0, 4 / 3, 8 / 5])
    MAJOR_53_OPEN = np.array([1.0, 3 / 2, 5 / 2])
    MAJOR_63_OPEN = np.array([1.0, 8 / 5, 12 / 5])
    MAJOR_64_OPEN = np.array([1.0, 5 / 3, 8 / 3])
    MINOR_53_OPEN = np.array([1.0, 3 / 2, 12 / 5])
    MINOR_63_OPEN = np.array([1.0, 5 / 3, 5 / 2])
    MINOR_64_OPEN = np.array([1.0, 8 / 5, 8 / 3])

Triad group constants

    CONSONANT_TRIADS = [MAJOR_TRIAD, MAJOR_63, MAJOR_64, MINOR_TRIAD, MINOR_63, MINOR_64]
    CONSONANT_TRIADS_NO_64 = [MAJOR_TRIAD, MAJOR_63, MINOR_TRIAD, MINOR_63]
    CONSONANT_TRIADS_OPEN = [MAJOR_53_OPEN, MAJOR_63_OPEN, MAJOR_64_OPEN, MINOR_53_OPEN, MINOR_63_OPEN, MINOR_64_OPEN]
    CONSONANT_TRIADS_OPEN_NO_64 = [MAJOR_53_OPEN, MAJOR_63_OPEN, MINOR_53_OPEN, MINOR_63_OPEN]

# Scale constants

Just scale constants

    PENTATONIC_SCALE = np.array([C, G, D, A, E])
    DIATONIC_SCALE = np.array([F, C, G, D, A, E, B])
    HEXACHORD_MAJOR = np.array([F, C, G, D, A, E])
    HEXACHORD_MINOR = np.array([F, C, G, D, A, E * FLAT])
    MAJOR_SCALE = DIATONIC_SCALE
    NATURAL_MINOR_SCALE = DIATONIC_SCALE * E * FLAT

Diatonic modes

    IONIAN = DIATONIC_SCALE
    DORIAN = DIATONIC_SCALE * B * FLAT
    PHRYGIAN = DIATONIC_SCALE * A * FLAT
    LYDIAN = DIATONIC_SCALE * G
    MIXOLYDIAN = DIATONIC_SCALE * F
    AEOLIAN = DIATONIC_SCALE * E * FLAT
    LOCRIAN = DIATONIC_SCALE * D * FLAT

12-tone equal tempered symmetric-scale constants

    WHOLE_TONE = np.array([0, 2, 4, 6, 8, 10])
    OCTATONIC = OCTATONIC01 = np.array([0, 1, 3, 4, 6, 7, 9, 10])
    OCTATONIC02 = np.array([0, 2, 3, 5, 6, 8, 9, 11])
    HEXATONIC = HEXATONIC01 = np.array([0, 1, 4, 5, 8, 9])
    HEXATONIC03 = np.array([0, 3, 4, 7, 8, 11])
    ENNEATONIC = ENNEATONIC012 = np.array([0, 1, 2, 4, 5, 6, 8, 9, 10])
    ENNEATONIC013 = np.array([0, 1, 3, 4, 5, 7, 8, 9, 11])
    ENNEATONIC023 = np.array([0, 2, 3, 4, 6, 7, 8, 10, 11])

# Voice range constants

    CONTIGUOUS_OCTAVES = np.array([[2.0 ** i, 2.0 ** (i + 1)] for i in range(7)])
    CONTIGUOUS_4THS = np.array([[(4 / 3) ** i, (4 / 3) ** (i + 1)] for i in range(7)])
    CONTIGUOUS_5THS = np.array([[(3 / 2) ** i, (3 / 2) ** (i + 1)] for i in range(7)])
    CONTIGUOUS_12THS = np.array([[(3 / 1) ** i, (3 / 1) ** (i + 1)] for i in range(7)])
    CONTIGUOUS_15THS = np.array([[(4 / 1) ** i, (4 / 1) ** (i + 1)] for i in range(7)])
    AUTHENTIC_OCTAVES = np.append(CONTIGUOUS_OCTAVES, CONTIGUOUS_OCTAVES * (3 / 2), axis=0)
    AUTHENTIC_5THS = np.append(CONTIGUOUS_5THS, CONTIGUOUS_5THS * (3 / 2), axis=0)
    AUTHENTIC_12THS = np.append(CONTIGUOUS_12THS, CONTIGUOUS_12THS * (3 / 2), axis=0)
    AUTHENTIC_15THS = np.append(CONTIGUOUS_15THS, CONTIGUOUS_15THS * (3 / 2), axis=0)
    PLAGAL_OCTAVES = np.append(CONTIGUOUS_OCTAVES, CONTIGUOUS_OCTAVES * (4 / 3), axis=0)
    PLAGAL_5THS = np.append(CONTIGUOUS_5THS, CONTIGUOUS_5THS * (4 / 3), axis=0)

# Octave constants

    OCTAVE0 = 2.0 ** 1
    OCTAVE1 = 2.0 ** 2
    OCTAVE2 = 2.0 ** 3
    OCTAVE3 = 2.0 ** 4
    OCTAVE4 = 2.0 ** 5
    OCTAVE5 = 2.0 ** 6
    OCTAVE6 = 2.0 ** 7
    OCTAVE7 = 2.0 ** 8
    OCTAVE8 = 2.0 ** 9

# Consonances constants

    CONSONANCES = (1.0, 3 / 2, 4 / 3, 5 / 4, 6 / 5, 8 / 5, 10 / 6)
    PERFECT_CONSONANCES = (1.0, 3 / 2, 4 / 3)
    IMPERFECT_CONSONANCES = (5 / 4, 6 / 5, 8 / 5, 10 / 6)

# General-midi program constants

    PIANO = 0
    ACOUSTIC_GRAND_PIANO = 0
    BRIGHT_ACOUSTIC_PIANO = 1
    ELECTRIC_GRAND_PIANO = 2
    HONKY_TONK_PIANO = 3
    ELECTRIC_PIANO = 4
    ELECTRIC_PIANO_1 = 4
    ELECTRIC_PIANO_2 = 5
    HARPSICHORD = 6
    CLAVI = 7
    CELESTA = 8
    GLOCKENSPIEL = 9
    MUSIC_BOX = 10
    VIBRAPHONE = 11
    MARIMBA = 12
    XYLOPHONE = 13
    TUBULAR_BELLS = 14
    DULCIMER = 15
    DRAWBAR_ORGAN = 16
    PERCUSSIVE_ORGAN = 17
    ROCK_ORGAN = 18
    CHURCH_ORGAN = 19
    REED_ORGAN = 20
    ACCORDION = 21
    HARMONICA = 22
    TANGO_ACCORDION = 23
    GUITAR = 24
    ACOUSTIC_GUITAR_NYLON = 24
    ACOUSTIC_GUITAR_STEEL = 25
    ELECTRIC_GUITAR_JAZZ = 26
    ELECTRIC_GUITAR_CLEAN = 27
    ELECTRIC_GUITAR_MUTED = 28
    OVERDRIVEN_GUITAR = 29
    DISTORTION_GUITAR = 30
    GUITAR_HARMONICS = 31
    ACOUSTIC_BASS = 32
    ELECTRIC_BASS_FINGER = 33
    ELECTRIC_BASS_PICK = 34
    FRETLESS_BASS = 35
    SLAP_BASS_1 = 36
    SLAP_BASS_2 = 37
    SYNTH_BASS_1 = 38
    SYNTH_BASS_2 = 39
    VIOLIN = 40
    VIOLA = 41
    CELLO = 42
    CONTRABASS = 43
    TREMOLO_STRINGS = 44
    PIZZ_STRINGS = 45
    PIZZICATO_STRINGS = 45
    HARP = 46
    ORCHESTRAL_HARP = 46
    TIMPANI = 47
    STRING_ENSEMBLE_1 = 48
    STRING_ENSEMBLE_2 = 49
    SYNTHSTRINGS_1 = 50
    SYNTHSTRINGS_2 = 51
    CHOIR_AAHS = 52
    VOICE_OOHS = 53
    SYNTH_VOICE = 54
    ORCHESTRA_HIT = 55
    TRUMPET = 56
    TROMBONE = 57
    TUBA = 58
    MUTED_TRUMPET = 59
    FRENCH_HORN = 60
    BRASS_SECTION = 61
    SYNTHBRASS_1 = 62
    SYNTHBRASS_2 = 63
    SOPRANO_SAX = 64
    ALTO_SAX = 65
    TENOR_SAX = 66
    BARITONE_SAX = 67
    OBOE = 68
    ENGLISH_HORN = 69
    BASSOON = 70
    CLARINET = 71
    PICCOLO = 72
    FLUTE = 73
    RECORDER = 74
    PAN_FLUTE = 75
    BLOWN_BOTTLE = 76
    SHAKUHACHI = 77
    WHISTLE = 78
    OCARINA = 79
    LEAD_1_SQUARE = 80
    LEAD_2_SAWTOOTH = 81
    LEAD_3_CALLIOPE = 82
    LEAD_4_CHIFF = 83
    LEAD_5_CHARANG = 84
    LEAD_6_VOICE = 85
    LEAD_7_FIFTHS = 86
    LEAD_8_BASS_AND_LEAD = 87
    PAD_1_NEW_AGE = 88
    PAD_2_WARM = 89
    PAD_3_POLYSYNTH = 90
    PAD_4_CHOIR = 91
    PAD_5_BOWED = 92
    PAD_6_METALLIC = 93
    PAD_7_HALO = 94
    PAD_8_SWEEP = 95
    FX_1_RAIN = 96
    FX_2_SOUNDTRACK = 97
    FX_3_CRYSTAL = 98
    FX_4_ATMOSPHERE = 99
    FX_5_BRIGHTNESS = 100
    FX_6_GOBLINS = 101
    FX_7_ECHOES = 102
    FX_8_SCI_FI = 103
    SITAR = 104
    BANJO = 105
    SHAMISEN = 106
    KOTO = 107
    KALIMBA = 108
    BAG_PIPE = 109
    FIDDLE = 110
    SHANAI = 111
    TINKLE_BELL = 112
    AGOGO = 113
    STEEL_DRUMS = 114
    WOODBLOCK = 115
    TAIKO_DRUM = 116
    MELODIC_TOM = 117
    SYNTH_DRUM = 118
    REVERSE_CYMBAL = 119
    GUITAR_FRET_NOISE = 120
    BREATH_NOISE = 121
    SEASHORE = 122
    BIRD_TWEET = 123
    TELEPHONE_RING = 124
    HELICOPTER = 125
    APPLAUSE = 126
    GUNSHOT = 127
