# Filters

## PitchFilter

Pitch filter. Pitch filter removes notes of any pitch.

### prob_curve

- Description: Probability curve.
- Default: Static
- Type: str
- Possible values: 'AlwaysOn', 'Static', 'Linear', 'Quadratic', 'LinearOsc', 'Saw', 'Sine', 'Accumulating', 'RandomToggle'
- Unique: yes

### marked_by

- Description: Only apply to notes marked by.
- Default: 
- Type: str
- Unique: yes

### start_time

- Description: Start time.
- Default: [0]
- Type: float
- Min: 0.0
- Max: 0.0
- Unique: no

### end_time

- Description: End time.
- Default: [0.0]
- Type: float
- Min: 0.0
- Max: 0.0
- Unique: no

### by_voice

- Description: By voice.
- Default: True
- Type: bool
- Unique: yes

### voices

- Description: Voices.
- Only has effect if by_voice == 'true'
- Default: []
- Type: int
- Min: 0
- Unique: no

### exemptions

- Description: Exemptions.
- Default: off
- Type: str
- Possible values: 'off', 'metric', 'counting'
- Unique: yes

### exempt

- Description: Exempt beats.
- Only has effect if exemptions == 'metric'
- Default: ()
- Type: Fraction
- Min: 0
- Unique: no

### exempt_modulo

- Description: Exempt beats modulo.
- Only has effect if exemptions == 'metric'
- Default: 4
- Type: Fraction
- Min: 0
- Unique: yes

### exempt_n

- Description: Exempt num notes.
- Only has effect if exemptions == 'counting'
- Default: [0]
- Type: int
- Min: 0
- Unique: no

### exempt_comma

- Description: Exempt comma.
- Only has effect if exemptions == 'metric'
- Default: 1/128
- Type: Fraction
- Min: 0
- Unique: yes

### invert_exempt

- Description: Invert exempt beats.
- Only has effect if exemptions in ('metric', 'counting')
- Default: False
- Type: bool
- Unique: yes

### adjust_dur

- Description: Adjust durations.
- Default: None
- Type: str
- Possible values: 'None', 'Extend_previous_notes', 'Subtract_duration'
- Unique: yes

### adjust_dur_comma

- Description: Adjust durations comma.
- Only has effect if adjust_dur == 'Extend_previous_notes'
- Default: 0.25
- Type: float
- Min: 0
- Unique: yes

### subtract_dur_modulo

- Description: Subtract durations within length.
- Only has effect if adjust_dur == 'Subtract_duration'
- Default: 0
- Type: Fraction
- Min: 0.001
- Unique: yes


## RangeFilter

Range filter. Range filter removes notes whose pitches lie outside the specified range(s).

### prob_curve

- Description: Probability curve.
- Default: Static
- Type: str
- Possible values: 'AlwaysOn', 'Static', 'Linear', 'Quadratic', 'LinearOsc', 'Saw', 'Sine', 'Accumulating', 'RandomToggle'
- Unique: yes

### marked_by

- Description: Only apply to notes marked by.
- Default: 
- Type: str
- Unique: yes

### start_time

- Description: Start time.
- Default: [0]
- Type: float
- Min: 0.0
- Max: 0.0
- Unique: no

### end_time

- Description: End time.
- Default: [0.0]
- Type: float
- Min: 0.0
- Max: 0.0
- Unique: no

### by_voice

- Description: By voice.
- Default: True
- Type: bool
- Unique: yes

### voices

- Description: Voices.
- Only has effect if by_voice == 'true'
- Default: []
- Type: int
- Min: 0
- Unique: no

### exemptions

- Description: Exemptions.
- Default: off
- Type: str
- Possible values: 'off', 'metric', 'counting'
- Unique: yes

### exempt

- Description: Exempt beats.
- Only has effect if exemptions == 'metric'
- Default: ()
- Type: Fraction
- Min: 0
- Unique: no

### exempt_modulo

- Description: Exempt beats modulo.
- Only has effect if exemptions == 'metric'
- Default: 4
- Type: Fraction
- Min: 0
- Unique: yes

### exempt_n

- Description: Exempt num notes.
- Only has effect if exemptions == 'counting'
- Default: [0]
- Type: int
- Min: 0
- Unique: no

### exempt_comma

- Description: Exempt comma.
- Only has effect if exemptions == 'metric'
- Default: 1/128
- Type: Fraction
- Min: 0
- Unique: yes

### invert_exempt

- Description: Invert exempt beats.
- Only has effect if exemptions in ('metric', 'counting')
- Default: False
- Type: bool
- Unique: yes

### adjust_dur

- Description: Adjust durations.
- Default: None
- Type: str
- Possible values: 'None', 'Extend_previous_notes', 'Subtract_duration'
- Unique: yes

### adjust_dur_comma

- Description: Adjust durations comma.
- Only has effect if adjust_dur == 'Extend_previous_notes'
- Default: 0.25
- Type: float
- Min: 0
- Unique: yes

### subtract_dur_modulo

- Description: Subtract durations within length.
- Only has effect if adjust_dur == 'Subtract_duration'
- Default: 0
- Type: Fraction
- Min: 0.001
- Unique: yes

### filter_range

- Description: Range(s) to pass through filter.
- Default: ((0, 127),)
- Type: int
- Min: 0
- Unique: yes


## OscillatingRangeFilter

Oscillating range filter. Oscillating range filter removes notes whose pitches lie outside of a range whose bounds oscillate according to parameters that you control..

### prob_curve

- Description: Probability curve.
- Default: Static
- Type: str
- Possible values: 'AlwaysOn', 'Static', 'Linear', 'Quadratic', 'LinearOsc', 'Saw', 'Sine', 'Accumulating', 'RandomToggle'
- Unique: yes

### marked_by

- Description: Only apply to notes marked by.
- Default: 
- Type: str
- Unique: yes

### start_time

- Description: Start time.
- Default: [0]
- Type: float
- Min: 0.0
- Max: 0.0
- Unique: no

### end_time

- Description: End time.
- Default: [0.0]
- Type: float
- Min: 0.0
- Max: 0.0
- Unique: no

### by_voice

- Description: By voice.
- Default: True
- Type: bool
- Unique: yes

### voices

- Description: Voices.
- Only has effect if by_voice == 'true'
- Default: []
- Type: int
- Min: 0
- Unique: no

### exemptions

- Description: Exemptions.
- Default: off
- Type: str
- Possible values: 'off', 'metric', 'counting'
- Unique: yes

### exempt

- Description: Exempt beats.
- Only has effect if exemptions == 'metric'
- Default: ()
- Type: Fraction
- Min: 0
- Unique: no

### exempt_modulo

- Description: Exempt beats modulo.
- Only has effect if exemptions == 'metric'
- Default: 4
- Type: Fraction
- Min: 0
- Unique: yes

### exempt_n

- Description: Exempt num notes.
- Only has effect if exemptions == 'counting'
- Default: [0]
- Type: int
- Min: 0
- Unique: no

### exempt_comma

- Description: Exempt comma.
- Only has effect if exemptions == 'metric'
- Default: 1/128
- Type: Fraction
- Min: 0
- Unique: yes

### invert_exempt

- Description: Invert exempt beats.
- Only has effect if exemptions in ('metric', 'counting')
- Default: False
- Type: bool
- Unique: yes

### adjust_dur

- Description: Adjust durations.
- Default: None
- Type: str
- Possible values: 'None', 'Extend_previous_notes', 'Subtract_duration'
- Unique: yes

### adjust_dur_comma

- Description: Adjust durations comma.
- Only has effect if adjust_dur == 'Extend_previous_notes'
- Default: 0.25
- Type: float
- Min: 0
- Unique: yes

### subtract_dur_modulo

- Description: Subtract durations within length.
- Only has effect if adjust_dur == 'Subtract_duration'
- Default: 0
- Type: Fraction
- Min: 0.001
- Unique: yes

### bottom_range

- Description: Range at bottom of oscillation.
- Default: (0, 127)
- Type: int
- Min: 0
- Unique: yes

### range_size

- Description: Size in pitches of oscillation.
- Default: 36
- Type: int
- Min: 0
- Unique: yes

### osc_period

- Description: Oscillation period.
- Default: 8
- Type: int
- Min: 0.01
- Unique: yes

### osc_offset

- Description: Oscillation period offset.
- Default: 0
- Type: int
- Min: 0
- Unique: yes


## OddPitchFilter

Odd pitch filter. Odd pitch filter removes notes of odd pitch.

### prob_curve

- Description: Probability curve.
- Default: Static
- Type: str
- Possible values: 'AlwaysOn', 'Static', 'Linear', 'Quadratic', 'LinearOsc', 'Saw', 'Sine', 'Accumulating', 'RandomToggle'
- Unique: yes

### marked_by

- Description: Only apply to notes marked by.
- Default: 
- Type: str
- Unique: yes

### start_time

- Description: Start time.
- Default: [0]
- Type: float
- Min: 0.0
- Max: 0.0
- Unique: no

### end_time

- Description: End time.
- Default: [0.0]
- Type: float
- Min: 0.0
- Max: 0.0
- Unique: no

### by_voice

- Description: By voice.
- Default: True
- Type: bool
- Unique: yes

### voices

- Description: Voices.
- Only has effect if by_voice == 'true'
- Default: []
- Type: int
- Min: 0
- Unique: no

### exemptions

- Description: Exemptions.
- Default: off
- Type: str
- Possible values: 'off', 'metric', 'counting'
- Unique: yes

### exempt

- Description: Exempt beats.
- Only has effect if exemptions == 'metric'
- Default: ()
- Type: Fraction
- Min: 0
- Unique: no

### exempt_modulo

- Description: Exempt beats modulo.
- Only has effect if exemptions == 'metric'
- Default: 4
- Type: Fraction
- Min: 0
- Unique: yes

### exempt_n

- Description: Exempt num notes.
- Only has effect if exemptions == 'counting'
- Default: [0]
- Type: int
- Min: 0
- Unique: no

### exempt_comma

- Description: Exempt comma.
- Only has effect if exemptions == 'metric'
- Default: 1/128
- Type: Fraction
- Min: 0
- Unique: yes

### invert_exempt

- Description: Invert exempt beats.
- Only has effect if exemptions in ('metric', 'counting')
- Default: False
- Type: bool
- Unique: yes

### adjust_dur

- Description: Adjust durations.
- Default: None
- Type: str
- Possible values: 'None', 'Extend_previous_notes', 'Subtract_duration'
- Unique: yes

### adjust_dur_comma

- Description: Adjust durations comma.
- Only has effect if adjust_dur == 'Extend_previous_notes'
- Default: 0.25
- Type: float
- Min: 0
- Unique: yes

### subtract_dur_modulo

- Description: Subtract durations within length.
- Only has effect if adjust_dur == 'Subtract_duration'
- Default: 0
- Type: Fraction
- Min: 0.001
- Unique: yes


## EvenPitchFilter

Even pitch filter. Even pitch filter removes notes of even pitch.

### prob_curve

- Description: Probability curve.
- Default: Static
- Type: str
- Possible values: 'AlwaysOn', 'Static', 'Linear', 'Quadratic', 'LinearOsc', 'Saw', 'Sine', 'Accumulating', 'RandomToggle'
- Unique: yes

### marked_by

- Description: Only apply to notes marked by.
- Default: 
- Type: str
- Unique: yes

### start_time

- Description: Start time.
- Default: [0]
- Type: float
- Min: 0.0
- Max: 0.0
- Unique: no

### end_time

- Description: End time.
- Default: [0.0]
- Type: float
- Min: 0.0
- Max: 0.0
- Unique: no

### by_voice

- Description: By voice.
- Default: True
- Type: bool
- Unique: yes

### voices

- Description: Voices.
- Only has effect if by_voice == 'true'
- Default: []
- Type: int
- Min: 0
- Unique: no

### exemptions

- Description: Exemptions.
- Default: off
- Type: str
- Possible values: 'off', 'metric', 'counting'
- Unique: yes

### exempt

- Description: Exempt beats.
- Only has effect if exemptions == 'metric'
- Default: ()
- Type: Fraction
- Min: 0
- Unique: no

### exempt_modulo

- Description: Exempt beats modulo.
- Only has effect if exemptions == 'metric'
- Default: 4
- Type: Fraction
- Min: 0
- Unique: yes

### exempt_n

- Description: Exempt num notes.
- Only has effect if exemptions == 'counting'
- Default: [0]
- Type: int
- Min: 0
- Unique: no

### exempt_comma

- Description: Exempt comma.
- Only has effect if exemptions == 'metric'
- Default: 1/128
- Type: Fraction
- Min: 0
- Unique: yes

### invert_exempt

- Description: Invert exempt beats.
- Only has effect if exemptions in ('metric', 'counting')
- Default: False
- Type: bool
- Unique: yes

### adjust_dur

- Description: Adjust durations.
- Default: None
- Type: str
- Possible values: 'None', 'Extend_previous_notes', 'Subtract_duration'
- Unique: yes

### adjust_dur_comma

- Description: Adjust durations comma.
- Only has effect if adjust_dur == 'Extend_previous_notes'
- Default: 0.25
- Type: float
- Min: 0
- Unique: yes

### subtract_dur_modulo

- Description: Subtract durations within length.
- Only has effect if adjust_dur == 'Subtract_duration'
- Default: 0
- Type: Fraction
- Min: 0.001
- Unique: yes


## FilterSelectedPCs

Selected pitch-class filter. Selected pitch-class filter removes notes of the selected pitch-classes.

### prob_curve

- Description: Probability curve.
- Default: Static
- Type: str
- Possible values: 'AlwaysOn', 'Static', 'Linear', 'Quadratic', 'LinearOsc', 'Saw', 'Sine', 'Accumulating', 'RandomToggle'
- Unique: yes

### marked_by

- Description: Only apply to notes marked by.
- Default: 
- Type: str
- Unique: yes

### start_time

- Description: Start time.
- Default: [0]
- Type: float
- Min: 0.0
- Max: 0.0
- Unique: no

### end_time

- Description: End time.
- Default: [0.0]
- Type: float
- Min: 0.0
- Max: 0.0
- Unique: no

### by_voice

- Description: By voice.
- Default: True
- Type: bool
- Unique: yes

### voices

- Description: Voices.
- Only has effect if by_voice == 'true'
- Default: []
- Type: int
- Min: 0
- Unique: no

### exemptions

- Description: Exemptions.
- Default: off
- Type: str
- Possible values: 'off', 'metric', 'counting'
- Unique: yes

### exempt

- Description: Exempt beats.
- Only has effect if exemptions == 'metric'
- Default: ()
- Type: Fraction
- Min: 0
- Unique: no

### exempt_modulo

- Description: Exempt beats modulo.
- Only has effect if exemptions == 'metric'
- Default: 4
- Type: Fraction
- Min: 0
- Unique: yes

### exempt_n

- Description: Exempt num notes.
- Only has effect if exemptions == 'counting'
- Default: [0]
- Type: int
- Min: 0
- Unique: no

### exempt_comma

- Description: Exempt comma.
- Only has effect if exemptions == 'metric'
- Default: 1/128
- Type: Fraction
- Min: 0
- Unique: yes

### invert_exempt

- Description: Invert exempt beats.
- Only has effect if exemptions in ('metric', 'counting')
- Default: False
- Type: bool
- Unique: yes

### adjust_dur

- Description: Adjust durations.
- Default: None
- Type: str
- Possible values: 'None', 'Extend_previous_notes', 'Subtract_duration'
- Unique: yes

### adjust_dur_comma

- Description: Adjust durations comma.
- Only has effect if adjust_dur == 'Extend_previous_notes'
- Default: 0.25
- Type: float
- Min: 0
- Unique: yes

### subtract_dur_modulo

- Description: Subtract durations within length.
- Only has effect if adjust_dur == 'Subtract_duration'
- Default: 0
- Type: Fraction
- Min: 0.001
- Unique: yes

### selected_pcs

- Description: Pitch-classes to filter.
- Default: ()
- Type: int
- Min: 0
- Max: 11
- Unique: no


## FilterUnselectedPCs

Unselected pitch-class filter. Unselected pitch-class filter removes notes that do *not* belong to the  selected pitch-classes.

### prob_curve

- Description: Probability curve.
- Default: Static
- Type: str
- Possible values: 'AlwaysOn', 'Static', 'Linear', 'Quadratic', 'LinearOsc', 'Saw', 'Sine', 'Accumulating', 'RandomToggle'
- Unique: yes

### marked_by

- Description: Only apply to notes marked by.
- Default: 
- Type: str
- Unique: yes

### start_time

- Description: Start time.
- Default: [0]
- Type: float
- Min: 0.0
- Max: 0.0
- Unique: no

### end_time

- Description: End time.
- Default: [0.0]
- Type: float
- Min: 0.0
- Max: 0.0
- Unique: no

### by_voice

- Description: By voice.
- Default: True
- Type: bool
- Unique: yes

### voices

- Description: Voices.
- Only has effect if by_voice == 'true'
- Default: []
- Type: int
- Min: 0
- Unique: no

### exemptions

- Description: Exemptions.
- Default: off
- Type: str
- Possible values: 'off', 'metric', 'counting'
- Unique: yes

### exempt

- Description: Exempt beats.
- Only has effect if exemptions == 'metric'
- Default: ()
- Type: Fraction
- Min: 0
- Unique: no

### exempt_modulo

- Description: Exempt beats modulo.
- Only has effect if exemptions == 'metric'
- Default: 4
- Type: Fraction
- Min: 0
- Unique: yes

### exempt_n

- Description: Exempt num notes.
- Only has effect if exemptions == 'counting'
- Default: [0]
- Type: int
- Min: 0
- Unique: no

### exempt_comma

- Description: Exempt comma.
- Only has effect if exemptions == 'metric'
- Default: 1/128
- Type: Fraction
- Min: 0
- Unique: yes

### invert_exempt

- Description: Invert exempt beats.
- Only has effect if exemptions in ('metric', 'counting')
- Default: False
- Type: bool
- Unique: yes

### adjust_dur

- Description: Adjust durations.
- Default: None
- Type: str
- Possible values: 'None', 'Extend_previous_notes', 'Subtract_duration'
- Unique: yes

### adjust_dur_comma

- Description: Adjust durations comma.
- Only has effect if adjust_dur == 'Extend_previous_notes'
- Default: 0.25
- Type: float
- Min: 0
- Unique: yes

### subtract_dur_modulo

- Description: Subtract durations within length.
- Only has effect if adjust_dur == 'Subtract_duration'
- Default: 0
- Type: Fraction
- Min: 0.001
- Unique: yes

### selected_pcs

- Description: Pitch-classes not to filter.
- Default: ()
- Type: int
- Min: 0
- Max: 11
- Unique: no



# Transformers

## ForcePitchTransformer

Force pitch transformer.

### prob_curve

- Description: Probability curve.
- Default: Static
- Type: str
- Possible values: 'AlwaysOn', 'Static', 'Linear', 'Quadratic', 'LinearOsc', 'Saw', 'Sine', 'Accumulating', 'RandomToggle'
- Unique: yes

### marked_by

- Description: Only apply to notes marked by.
- Default: 
- Type: str
- Unique: yes

### start_time

- Description: Start time.
- Default: [0]
- Type: float
- Min: 0.0
- Max: 0.0
- Unique: no

### end_time

- Description: End time.
- Default: [0.0]
- Type: float
- Min: 0.0
- Max: 0.0
- Unique: no

### by_voice

- Description: By voice.
- Default: True
- Type: bool
- Unique: yes

### voices

- Description: Voices.
- Only has effect if by_voice == 'true'
- Default: []
- Type: int
- Min: 0
- Unique: no

### exemptions

- Description: Exemptions.
- Default: off
- Type: str
- Possible values: 'off', 'metric', 'counting'
- Unique: yes

### exempt

- Description: Exempt beats.
- Only has effect if exemptions == 'metric'
- Default: ()
- Type: Fraction
- Min: 0
- Unique: no

### exempt_modulo

- Description: Exempt beats modulo.
- Only has effect if exemptions == 'metric'
- Default: 4
- Type: Fraction
- Min: 0
- Unique: yes

### exempt_n

- Description: Exempt num notes.
- Only has effect if exemptions == 'counting'
- Default: [0]
- Type: int
- Min: 0
- Unique: no

### exempt_comma

- Description: Exempt comma.
- Only has effect if exemptions == 'metric'
- Default: 1/128
- Type: Fraction
- Min: 0
- Unique: yes

### invert_exempt

- Description: Invert exempt beats.
- Only has effect if exemptions in ('metric', 'counting')
- Default: False
- Type: bool
- Unique: yes

### force_pitches

- Description: Pitches to force.
- Default: ()
- Type: int
- Min: 1
- Unique: no


## ForcePitchClassesTransformer

Force pitch-classes transformer.

### prob_curve

- Description: Probability curve.
- Default: Static
- Type: str
- Possible values: 'AlwaysOn', 'Static', 'Linear', 'Quadratic', 'LinearOsc', 'Saw', 'Sine', 'Accumulating', 'RandomToggle'
- Unique: yes

### marked_by

- Description: Only apply to notes marked by.
- Default: 
- Type: str
- Unique: yes

### start_time

- Description: Start time.
- Default: [0]
- Type: float
- Min: 0.0
- Max: 0.0
- Unique: no

### end_time

- Description: End time.
- Default: [0.0]
- Type: float
- Min: 0.0
- Max: 0.0
- Unique: no

### by_voice

- Description: By voice.
- Default: True
- Type: bool
- Unique: yes

### voices

- Description: Voices.
- Only has effect if by_voice == 'true'
- Default: []
- Type: int
- Min: 0
- Unique: no

### exemptions

- Description: Exemptions.
- Default: off
- Type: str
- Possible values: 'off', 'metric', 'counting'
- Unique: yes

### exempt

- Description: Exempt beats.
- Only has effect if exemptions == 'metric'
- Default: ()
- Type: Fraction
- Min: 0
- Unique: no

### exempt_modulo

- Description: Exempt beats modulo.
- Only has effect if exemptions == 'metric'
- Default: 4
- Type: Fraction
- Min: 0
- Unique: yes

### exempt_n

- Description: Exempt num notes.
- Only has effect if exemptions == 'counting'
- Default: [0]
- Type: int
- Min: 0
- Unique: no

### exempt_comma

- Description: Exempt comma.
- Only has effect if exemptions == 'metric'
- Default: 1/128
- Type: Fraction
- Min: 0
- Unique: yes

### invert_exempt

- Description: Invert exempt beats.
- Only has effect if exemptions in ('metric', 'counting')
- Default: False
- Type: bool
- Unique: yes

### force_pcs

- Description: Pitch-classes to force.
- Default: ()
- Type: int
- Min: 0
- Max: 11
- Unique: no


## VelocityTransformer

Velocity transformer.

### func_str

- Description: Mediating function.
- Default: thru
- Type: str
- Possible values: 'thru', 'linear', 'quadratic', 'linear_osc', 'saw', 'cosine'
- Unique: yes

### med_start_time

- Description: Mediator start time.
- Only has effect if func_str in ['linear', 'quadratic']
- Default: [0]
- Type: Fraction
- Min: 0
- Max: 0.0
- Unique: no

### med_end_time

- Description: Mediator end time.
- Only has effect if func_str in ['linear', 'quadratic']
- Default: [0.0]
- Type: Fraction
- Min: 0
- Max: 0.0
- Unique: no

### med_period

- Description: Mediator period.
- Only has effect if func_str in ['linear_osc', 'saw', 'cosine']
- Default: [4]
- Type: Fraction
- Min: 0
- Unique: no

### med_offset

- Description: Mediator offset.
- Only has effect if func_str in ['linear_osc', 'saw', 'cosine']
- Default: [0]
- Type: Fraction
- Min: 0
- Unique: no

### med_decreasing

- Description: Mediator decreasing.
- Only has effect if func_str in ['linear_osc', 'saw', 'cosine', 'linear', 'quadratic']
- Default: False
- Type: bool
- Unique: yes

### prob_curve

- Description: Probability curve.
- Default: Static
- Type: str
- Possible values: 'AlwaysOn', 'Static', 'Linear', 'Quadratic', 'LinearOsc', 'Saw', 'Sine', 'Accumulating', 'RandomToggle'
- Unique: yes

### marked_by

- Description: Only apply to notes marked by.
- Default: 
- Type: str
- Unique: yes

### start_time

- Description: Start time.
- Default: [0]
- Type: float
- Min: 0.0
- Max: 0.0
- Unique: no

### end_time

- Description: End time.
- Default: [0.0]
- Type: float
- Min: 0.0
- Max: 0.0
- Unique: no

### by_voice

- Description: By voice.
- Default: True
- Type: bool
- Unique: yes

### voices

- Description: Voices.
- Only has effect if by_voice == 'true'
- Default: []
- Type: int
- Min: 0
- Unique: no

### exemptions

- Description: Exemptions.
- Default: off
- Type: str
- Possible values: 'off', 'metric', 'counting'
- Unique: yes

### exempt

- Description: Exempt beats.
- Only has effect if exemptions == 'metric'
- Default: ()
- Type: Fraction
- Min: 0
- Unique: no

### exempt_modulo

- Description: Exempt beats modulo.
- Only has effect if exemptions == 'metric'
- Default: 4
- Type: Fraction
- Min: 0
- Unique: yes

### exempt_n

- Description: Exempt num notes.
- Only has effect if exemptions == 'counting'
- Default: [0]
- Type: int
- Min: 0
- Unique: no

### exempt_comma

- Description: Exempt comma.
- Only has effect if exemptions == 'metric'
- Default: 1/128
- Type: Fraction
- Min: 0
- Unique: yes

### invert_exempt

- Description: Invert exempt beats.
- Only has effect if exemptions in ('metric', 'counting')
- Default: False
- Type: bool
- Unique: yes

### trans_type

- Description: Velocity transform type.
- Default: Scale
- Type: str
- Possible values: 'Scale', 'Fix'
- Unique: yes

### scale_by

- Description: Scale factor.
- Only has effect if trans_type == 'Scale'
- Default: [1]
- Type: float
- Min: 0
- Unique: no

### fix_to

- Description: Fix velocity to.
- Only has effect if trans_type == 'Fix'
- Default: [64]
- Type: int
- Min: 0
- Max: 127
- Unique: no

### humanize

- Description: Humanize +/-.
- Default: [6]
- Type: int
- Min: 0
- Max: 127
- Unique: no


## ChangeDurationsTransformer

Change durations transformer.

### func_str

- Description: Mediating function.
- Default: thru
- Type: str
- Possible values: 'thru', 'linear', 'quadratic', 'linear_osc', 'saw', 'cosine'
- Unique: yes

### med_start_time

- Description: Mediator start time.
- Only has effect if func_str in ['linear', 'quadratic']
- Default: [0]
- Type: Fraction
- Min: 0
- Max: 0.0
- Unique: no

### med_end_time

- Description: Mediator end time.
- Only has effect if func_str in ['linear', 'quadratic']
- Default: [0.0]
- Type: Fraction
- Min: 0
- Max: 0.0
- Unique: no

### med_period

- Description: Mediator period.
- Only has effect if func_str in ['linear_osc', 'saw', 'cosine']
- Default: [4]
- Type: Fraction
- Min: 0
- Unique: no

### med_offset

- Description: Mediator offset.
- Only has effect if func_str in ['linear_osc', 'saw', 'cosine']
- Default: [0]
- Type: Fraction
- Min: 0
- Unique: no

### med_decreasing

- Description: Mediator decreasing.
- Only has effect if func_str in ['linear_osc', 'saw', 'cosine', 'linear', 'quadratic']
- Default: False
- Type: bool
- Unique: yes

### prob_curve

- Description: Probability curve.
- Default: Static
- Type: str
- Possible values: 'AlwaysOn', 'Static', 'Linear', 'Quadratic', 'LinearOsc', 'Saw', 'Sine', 'Accumulating', 'RandomToggle'
- Unique: yes

### marked_by

- Description: Only apply to notes marked by.
- Default: 
- Type: str
- Unique: yes

### start_time

- Description: Start time.
- Default: [0]
- Type: float
- Min: 0.0
- Max: 0.0
- Unique: no

### end_time

- Description: End time.
- Default: [0.0]
- Type: float
- Min: 0.0
- Max: 0.0
- Unique: no

### by_voice

- Description: By voice.
- Default: True
- Type: bool
- Unique: yes

### voices

- Description: Voices.
- Only has effect if by_voice == 'true'
- Default: []
- Type: int
- Min: 0
- Unique: no

### exemptions

- Description: Exemptions.
- Default: off
- Type: str
- Possible values: 'off', 'metric', 'counting'
- Unique: yes

### exempt

- Description: Exempt beats.
- Only has effect if exemptions == 'metric'
- Default: ()
- Type: Fraction
- Min: 0
- Unique: no

### exempt_modulo

- Description: Exempt beats modulo.
- Only has effect if exemptions == 'metric'
- Default: 4
- Type: Fraction
- Min: 0
- Unique: yes

### exempt_n

- Description: Exempt num notes.
- Only has effect if exemptions == 'counting'
- Default: [0]
- Type: int
- Min: 0
- Unique: no

### exempt_comma

- Description: Exempt comma.
- Only has effect if exemptions == 'metric'
- Default: 1/128
- Type: Fraction
- Min: 0
- Unique: yes

### invert_exempt

- Description: Invert exempt beats.
- Only has effect if exemptions in ('metric', 'counting')
- Default: False
- Type: bool
- Unique: yes

### trans_type

- Description: Change durations type.
- Default: Scale
- Type: str
- Possible values: 'Scale', 'By_fixed_amount'
- Unique: yes

### scale_by

- Description: Scale factor.
- Only has effect if trans_type == 'Scale'
- Default: [1]
- Type: float
- Min: 0
- Unique: no

### fix_amount

- Description: Fixed amount.
- Only has effect if trans_type == 'By_fixed_amount'
- Default: [1]
- Type: Fraction
- Min: -4192
- Unique: no

### min_dur

- Description: Minimum dur.
- Default: [0]
- Type: Fraction
- Min: 0
- Unique: no

### min_dur_treatment

- Description: Treatment of notes below minumum dur.
- Default: Enforce_min_dur
- Type: str
- Possible values: 'Enforce_min_dur', 'Delete'
- Unique: yes


## RandomOctaveTransformer

Random octave transformer.

### prob_curve

- Description: Probability curve.
- Default: Static
- Type: str
- Possible values: 'AlwaysOn', 'Static', 'Linear', 'Quadratic', 'LinearOsc', 'Saw', 'Sine', 'Accumulating', 'RandomToggle'
- Unique: yes

### marked_by

- Description: Only apply to notes marked by.
- Default: 
- Type: str
- Unique: yes

### start_time

- Description: Start time.
- Default: [0]
- Type: float
- Min: 0.0
- Max: 0.0
- Unique: no

### end_time

- Description: End time.
- Default: [0.0]
- Type: float
- Min: 0.0
- Max: 0.0
- Unique: no

### by_voice

- Description: By voice.
- Default: True
- Type: bool
- Unique: yes

### voices

- Description: Voices.
- Only has effect if by_voice == 'true'
- Default: []
- Type: int
- Min: 0
- Unique: no

### exemptions

- Description: Exemptions.
- Default: off
- Type: str
- Possible values: 'off', 'metric', 'counting'
- Unique: yes

### exempt

- Description: Exempt beats.
- Only has effect if exemptions == 'metric'
- Default: ()
- Type: Fraction
- Min: 0
- Unique: no

### exempt_modulo

- Description: Exempt beats modulo.
- Only has effect if exemptions == 'metric'
- Default: 4
- Type: Fraction
- Min: 0
- Unique: yes

### exempt_n

- Description: Exempt num notes.
- Only has effect if exemptions == 'counting'
- Default: [0]
- Type: int
- Min: 0
- Unique: no

### exempt_comma

- Description: Exempt comma.
- Only has effect if exemptions == 'metric'
- Default: 1/128
- Type: Fraction
- Min: 0
- Unique: yes

### invert_exempt

- Description: Invert exempt beats.
- Only has effect if exemptions in ('metric', 'counting')
- Default: False
- Type: bool
- Unique: yes

### ranges

- Description: Voice ranges. If voice ranges are 0, they are taken from Voice objects if possible
- Default: [0]
- Type: int
- Min: 0
- Unique: no

### avoid_orig_oct

- Description: Avoid original octave if possible.
- Default: False
- Type: bool
- Unique: yes


## TransposeTransformer

Transpose transformer.

### prob_curve

- Description: Probability curve.
- Default: Static
- Type: str
- Possible values: 'AlwaysOn', 'Static', 'Linear', 'Quadratic', 'LinearOsc', 'Saw', 'Sine', 'Accumulating', 'RandomToggle'
- Unique: yes

### marked_by

- Description: Only apply to notes marked by.
- Default: 
- Type: str
- Unique: yes

### start_time

- Description: Start time.
- Default: [0]
- Type: float
- Min: 0.0
- Max: 0.0
- Unique: no

### end_time

- Description: End time.
- Default: [0.0]
- Type: float
- Min: 0.0
- Max: 0.0
- Unique: no

### by_voice

- Description: By voice.
- Default: True
- Type: bool
- Unique: yes

### voices

- Description: Voices.
- Only has effect if by_voice == 'true'
- Default: []
- Type: int
- Min: 0
- Unique: no

### exemptions

- Description: Exemptions.
- Default: off
- Type: str
- Possible values: 'off', 'metric', 'counting'
- Unique: yes

### exempt

- Description: Exempt beats.
- Only has effect if exemptions == 'metric'
- Default: ()
- Type: Fraction
- Min: 0
- Unique: no

### exempt_modulo

- Description: Exempt beats modulo.
- Only has effect if exemptions == 'metric'
- Default: 4
- Type: Fraction
- Min: 0
- Unique: yes

### exempt_n

- Description: Exempt num notes.
- Only has effect if exemptions == 'counting'
- Default: [0]
- Type: int
- Min: 0
- Unique: no

### exempt_comma

- Description: Exempt comma.
- Only has effect if exemptions == 'metric'
- Default: 1/128
- Type: Fraction
- Min: 0
- Unique: yes

### invert_exempt

- Description: Invert exempt beats.
- Only has effect if exemptions in ('metric', 'counting')
- Default: False
- Type: bool
- Unique: yes

### transpose

- Description: Interval of transposition.
- Default: [0]
- Type: int
- Min: -72
- Max: 72
- Unique: no

### preserve

- Description: Preserve original note.
- Default: [False]
- Type: bool
- Unique: no

### trans_type

- Description: Transposition type.
- Default: Standard
- Type: str
- Possible values: 'Standard', 'Cumulative', 'Random'
- Unique: yes

### bound

- Description: Cumulative bound. After the cumulative transposition reaches the bound (inclusive; either up or down), it will be shifted an octave up/down
- Only has effect if trans_type == 'Cumulative'
- Default: [0]
- Type: int
- Min: 0
- Max: 72
- Unique: no

### seg_dur

- Description: Transposition segment duration. If non-zero, then transposition segment number of notes is ignored
- Only has effect if trans_type in ('Cumulative', 'Random')
- Default: [4]
- Type: Fraction
- Min: 0
- Unique: no

### seg_card

- Description: Transposition segment number of notes.
- Only has effect if trans_type in ('Cumulative', 'Random')
- Default: [0]
- Type: int
- Min: 1
- Unique: no


## ChannelTransformer

Channel transformer.

### prob_curve

- Description: Probability curve.
- Default: Static
- Type: str
- Possible values: 'AlwaysOn', 'Static', 'Linear', 'Quadratic', 'LinearOsc', 'Saw', 'Sine', 'Accumulating', 'RandomToggle'
- Unique: yes

### marked_by

- Description: Only apply to notes marked by.
- Default: 
- Type: str
- Unique: yes

### start_time

- Description: Start time.
- Default: [0]
- Type: float
- Min: 0.0
- Max: 0.0
- Unique: no

### end_time

- Description: End time.
- Default: [0.0]
- Type: float
- Min: 0.0
- Max: 0.0
- Unique: no

### by_voice

- Description: By voice.
- Default: True
- Type: bool
- Unique: yes

### voices

- Description: Voices.
- Only has effect if by_voice == 'true'
- Default: []
- Type: int
- Min: 0
- Unique: no

### exemptions

- Description: Exemptions.
- Default: off
- Type: str
- Possible values: 'off', 'metric', 'counting'
- Unique: yes

### exempt

- Description: Exempt beats.
- Only has effect if exemptions == 'metric'
- Default: ()
- Type: Fraction
- Min: 0
- Unique: no

### exempt_modulo

- Description: Exempt beats modulo.
- Only has effect if exemptions == 'metric'
- Default: 4
- Type: Fraction
- Min: 0
- Unique: yes

### exempt_n

- Description: Exempt num notes.
- Only has effect if exemptions == 'counting'
- Default: [0]
- Type: int
- Min: 0
- Unique: no

### exempt_comma

- Description: Exempt comma.
- Only has effect if exemptions == 'metric'
- Default: 1/128
- Type: Fraction
- Min: 0
- Unique: yes

### invert_exempt

- Description: Invert exempt beats.
- Only has effect if exemptions in ('metric', 'counting')
- Default: False
- Type: bool
- Unique: yes

### dest_channels

- Description: Destination channels.
- Default: ()
- Type: int
- Min: 0
- Max: 15
- Unique: no


## ChannelExchangerTransformer

Channel exchanger transformer.

### prob_curve

- Description: Probability curve.
- Default: Static
- Type: str
- Possible values: 'AlwaysOn', 'Static', 'Linear', 'Quadratic', 'LinearOsc', 'Saw', 'Sine', 'Accumulating', 'RandomToggle'
- Unique: yes

### marked_by

- Description: Only apply to notes marked by.
- Default: 
- Type: str
- Unique: yes

### start_time

- Description: Start time.
- Default: [0]
- Type: float
- Min: 0.0
- Max: 0.0
- Unique: no

### end_time

- Description: End time.
- Default: [0.0]
- Type: float
- Min: 0.0
- Max: 0.0
- Unique: no

### by_voice

- Description: By voice.
- Default: True
- Type: bool
- Unique: yes

### voices

- Description: Voices.
- Only has effect if by_voice == 'true'
- Default: []
- Type: int
- Min: 0
- Unique: no

### exemptions

- Description: Exemptions.
- Default: off
- Type: str
- Possible values: 'off', 'metric', 'counting'
- Unique: yes

### exempt

- Description: Exempt beats.
- Only has effect if exemptions == 'metric'
- Default: ()
- Type: Fraction
- Min: 0
- Unique: no

### exempt_modulo

- Description: Exempt beats modulo.
- Only has effect if exemptions == 'metric'
- Default: 4
- Type: Fraction
- Min: 0
- Unique: yes

### exempt_n

- Description: Exempt num notes.
- Only has effect if exemptions == 'counting'
- Default: [0]
- Type: int
- Min: 0
- Unique: no

### exempt_comma

- Description: Exempt comma.
- Only has effect if exemptions == 'metric'
- Default: 1/128
- Type: Fraction
- Min: 0
- Unique: yes

### invert_exempt

- Description: Invert exempt beats.
- Only has effect if exemptions in ('metric', 'counting')
- Default: False
- Type: bool
- Unique: yes

### channel_pairs

- Description: Channel source/destination pairs.
- Default: ()
- Type: int
- Min: 0
- Max: 15
- Unique: no


## TrackExchangerTransformer

Track exchanger transformer.

### prob_curve

- Description: Probability curve.
- Default: Static
- Type: str
- Possible values: 'AlwaysOn', 'Static', 'Linear', 'Quadratic', 'LinearOsc', 'Saw', 'Sine', 'Accumulating', 'RandomToggle'
- Unique: yes

### marked_by

- Description: Only apply to notes marked by.
- Default: 
- Type: str
- Unique: yes

### start_time

- Description: Start time.
- Default: [0]
- Type: float
- Min: 0.0
- Max: 0.0
- Unique: no

### end_time

- Description: End time.
- Default: [0.0]
- Type: float
- Min: 0.0
- Max: 0.0
- Unique: no

### by_voice

- Description: By voice.
- Default: True
- Type: bool
- Unique: yes

### voices

- Description: Voices.
- Only has effect if by_voice == 'true'
- Default: []
- Type: int
- Min: 0
- Unique: no

### exemptions

- Description: Exemptions.
- Default: off
- Type: str
- Possible values: 'off', 'metric', 'counting'
- Unique: yes

### exempt

- Description: Exempt beats.
- Only has effect if exemptions == 'metric'
- Default: ()
- Type: Fraction
- Min: 0
- Unique: no

### exempt_modulo

- Description: Exempt beats modulo.
- Only has effect if exemptions == 'metric'
- Default: 4
- Type: Fraction
- Min: 0
- Unique: yes

### exempt_n

- Description: Exempt num notes.
- Only has effect if exemptions == 'counting'
- Default: [0]
- Type: int
- Min: 0
- Unique: no

### exempt_comma

- Description: Exempt comma.
- Only has effect if exemptions == 'metric'
- Default: 1/128
- Type: Fraction
- Min: 0
- Unique: yes

### invert_exempt

- Description: Invert exempt beats.
- Only has effect if exemptions in ('metric', 'counting')
- Default: False
- Type: bool
- Unique: yes

### track_pairs

- Description: Track source/destination pairs.
- Default: ()
- Type: int
- Min: 0
- Unique: no


## InvertTransformer

Melodic inversion transformer.

### prob_curve

- Description: Probability curve.
- Default: Static
- Type: str
- Possible values: 'AlwaysOn', 'Static', 'Linear', 'Quadratic', 'LinearOsc', 'Saw', 'Sine', 'Accumulating', 'RandomToggle'
- Unique: yes

### marked_by

- Description: Only apply to notes marked by.
- Default: 
- Type: str
- Unique: yes

### start_time

- Description: Start time.
- Default: [0]
- Type: float
- Min: 0.0
- Max: 0.0
- Unique: no

### end_time

- Description: End time.
- Default: [0.0]
- Type: float
- Min: 0.0
- Max: 0.0
- Unique: no

### by_voice

- Description: By voice.
- Default: True
- Type: bool
- Unique: yes

### voices

- Description: Voices.
- Only has effect if by_voice == 'true'
- Default: []
- Type: int
- Min: 0
- Unique: no

### exemptions

- Description: Exemptions.
- Default: off
- Type: str
- Possible values: 'off', 'metric', 'counting'
- Unique: yes

### exempt

- Description: Exempt beats.
- Only has effect if exemptions == 'metric'
- Default: ()
- Type: Fraction
- Min: 0
- Unique: no

### exempt_modulo

- Description: Exempt beats modulo.
- Only has effect if exemptions == 'metric'
- Default: 4
- Type: Fraction
- Min: 0
- Unique: yes

### exempt_n

- Description: Exempt num notes.
- Only has effect if exemptions == 'counting'
- Default: [0]
- Type: int
- Min: 0
- Unique: no

### exempt_comma

- Description: Exempt comma.
- Only has effect if exemptions == 'metric'
- Default: 1/128
- Type: Fraction
- Min: 0
- Unique: yes

### invert_exempt

- Description: Invert exempt beats.
- Only has effect if exemptions in ('metric', 'counting')
- Default: False
- Type: bool
- Unique: yes

### axis

- Description: Axis of inversion.
- Default: [60]
- Type: int
- Min: 0
- Unique: no


## TrackRandomizerTransformer

Track randomizer transformer.

### prob_curve

- Description: Probability curve.
- Default: Static
- Type: str
- Possible values: 'AlwaysOn', 'Static', 'Linear', 'Quadratic', 'LinearOsc', 'Saw', 'Sine', 'Accumulating', 'RandomToggle'
- Unique: yes

### marked_by

- Description: Only apply to notes marked by.
- Default: 
- Type: str
- Unique: yes

### start_time

- Description: Start time.
- Default: [0]
- Type: float
- Min: 0.0
- Max: 0.0
- Unique: no

### end_time

- Description: End time.
- Default: [0.0]
- Type: float
- Min: 0.0
- Max: 0.0
- Unique: no

### by_voice

- Description: By voice.
- Default: True
- Type: bool
- Unique: yes

### voices

- Description: Voices.
- Only has effect if by_voice == 'true'
- Default: []
- Type: int
- Min: 0
- Unique: no

### exemptions

- Description: Exemptions.
- Default: off
- Type: str
- Possible values: 'off', 'metric', 'counting'
- Unique: yes

### exempt

- Description: Exempt beats.
- Only has effect if exemptions == 'metric'
- Default: ()
- Type: Fraction
- Min: 0
- Unique: no

### exempt_modulo

- Description: Exempt beats modulo.
- Only has effect if exemptions == 'metric'
- Default: 4
- Type: Fraction
- Min: 0
- Unique: yes

### exempt_n

- Description: Exempt num notes.
- Only has effect if exemptions == 'counting'
- Default: [0]
- Type: int
- Min: 0
- Unique: no

### exempt_comma

- Description: Exempt comma.
- Only has effect if exemptions == 'metric'
- Default: 1/128
- Type: Fraction
- Min: 0
- Unique: yes

### invert_exempt

- Description: Invert exempt beats.
- Only has effect if exemptions in ('metric', 'counting')
- Default: False
- Type: bool
- Unique: yes

### dest_voices

- Description: Destination voices.
- Default: []
- Type: int
- Min: 0
- Unique: no


## TrackDoublerTransformer

Track doubler transformer.

### prob_curve

- Description: Probability curve.
- Default: Static
- Type: str
- Possible values: 'AlwaysOn', 'Static', 'Linear', 'Quadratic', 'LinearOsc', 'Saw', 'Sine', 'Accumulating', 'RandomToggle'
- Unique: yes

### marked_by

- Description: Only apply to notes marked by.
- Default: 
- Type: str
- Unique: yes

### start_time

- Description: Start time.
- Default: [0]
- Type: float
- Min: 0.0
- Max: 0.0
- Unique: no

### end_time

- Description: End time.
- Default: [0.0]
- Type: float
- Min: 0.0
- Max: 0.0
- Unique: no

### by_voice

- Description: By voice.
- Default: True
- Type: bool
- Unique: yes

### voices

- Description: Voices.
- Only has effect if by_voice == 'true'
- Default: []
- Type: int
- Min: 0
- Unique: no

### exemptions

- Description: Exemptions.
- Default: off
- Type: str
- Possible values: 'off', 'metric', 'counting'
- Unique: yes

### exempt

- Description: Exempt beats.
- Only has effect if exemptions == 'metric'
- Default: ()
- Type: Fraction
- Min: 0
- Unique: no

### exempt_modulo

- Description: Exempt beats modulo.
- Only has effect if exemptions == 'metric'
- Default: 4
- Type: Fraction
- Min: 0
- Unique: yes

### exempt_n

- Description: Exempt num notes.
- Only has effect if exemptions == 'counting'
- Default: [0]
- Type: int
- Min: 0
- Unique: no

### exempt_comma

- Description: Exempt comma.
- Only has effect if exemptions == 'metric'
- Default: 1/128
- Type: Fraction
- Min: 0
- Unique: yes

### invert_exempt

- Description: Invert exempt beats.
- Only has effect if exemptions in ('metric', 'counting')
- Default: False
- Type: bool
- Unique: yes

### doubling_intervals

- Description: Doubled voices transpositions.
- Default: [0]
- Type: int
- Min: -128
- Max: 128
- Unique: no


## SubdivideTransformer

Subdivide transformer. Subdivide transformer subdivides pitches into notes of specified value.

### prob_curve

- Description: Probability curve.
- Default: Static
- Type: str
- Possible values: 'AlwaysOn', 'Static', 'Linear', 'Quadratic', 'LinearOsc', 'Saw', 'Sine', 'Accumulating', 'RandomToggle'
- Unique: yes

### marked_by

- Description: Only apply to notes marked by.
- Default: 
- Type: str
- Unique: yes

### start_time

- Description: Start time.
- Default: [0]
- Type: float
- Min: 0.0
- Max: 0.0
- Unique: no

### end_time

- Description: End time.
- Default: [0.0]
- Type: float
- Min: 0.0
- Max: 0.0
- Unique: no

### by_voice

- Description: By voice.
- Default: True
- Type: bool
- Unique: yes

### voices

- Description: Voices.
- Only has effect if by_voice == 'true'
- Default: []
- Type: int
- Min: 0
- Unique: no

### exemptions

- Description: Exemptions.
- Default: off
- Type: str
- Possible values: 'off', 'metric', 'counting'
- Unique: yes

### exempt

- Description: Exempt beats.
- Only has effect if exemptions == 'metric'
- Default: ()
- Type: Fraction
- Min: 0
- Unique: no

### exempt_modulo

- Description: Exempt beats modulo.
- Only has effect if exemptions == 'metric'
- Default: 4
- Type: Fraction
- Min: 0
- Unique: yes

### exempt_n

- Description: Exempt num notes.
- Only has effect if exemptions == 'counting'
- Default: [0]
- Type: int
- Min: 0
- Unique: no

### exempt_comma

- Description: Exempt comma.
- Only has effect if exemptions == 'metric'
- Default: 1/128
- Type: Fraction
- Min: 0
- Unique: yes

### invert_exempt

- Description: Invert exempt beats.
- Only has effect if exemptions in ('metric', 'counting')
- Default: False
- Type: bool
- Unique: yes

### subdivision

- Description: Subdivision value.
- Default: [0.25]
- Type: Fraction
- Min: 0.0078125
- Max: 4
- Unique: no



# Probability curves

## AlwaysOn

Always on.


## Static

Static.

### seg_len_range

- Description: Segment length range.
- Default: [(1, 1)]
- Type: int
- Min: 1
- Unique: no

### granularity

- Description: Rhythmic granularity.
- Default: [0]
- Type: Fraction
- Min: 0
- Unique: no

### grain_offset

- Description: Granularity offset.
- Only has effect if granularity == 'true'
- Default: [0]
- Type: Fraction
- Min: 0
- Unique: no

### prob

- Description: Static probability.
- Default: [0.5]
- Type: float
- Min: 0
- Max: 1
- Unique: no


## Linear

Linear.

### seg_len_range

- Description: Segment length range.
- Default: [(1, 1)]
- Type: int
- Min: 1
- Unique: no

### granularity

- Description: Rhythmic granularity.
- Default: [0]
- Type: Fraction
- Min: 0
- Unique: no

### grain_offset

- Description: Granularity offset.
- Only has effect if granularity == 'true'
- Default: [0]
- Type: Fraction
- Min: 0
- Unique: no

### min_prob

- Description: Minimum probability.
- Default: [0]
- Type: float
- Min: 0
- Max: 1
- Unique: no

### max_prob

- Description: Maximum probability.
- Default: [1]
- Type: float
- Min: 0
- Max: 1
- Unique: no

### decreasing

- Description: Decreasing.
- Default: [False]
- Type: bool
- Unique: no


## Quadratic

Quadratic.

### seg_len_range

- Description: Segment length range.
- Default: [(1, 1)]
- Type: int
- Min: 1
- Unique: no

### granularity

- Description: Rhythmic granularity.
- Default: [0]
- Type: Fraction
- Min: 0
- Unique: no

### grain_offset

- Description: Granularity offset.
- Only has effect if granularity == 'true'
- Default: [0]
- Type: Fraction
- Min: 0
- Unique: no

### min_prob

- Description: Minimum probability.
- Default: [0]
- Type: float
- Min: 0
- Max: 1
- Unique: no

### max_prob

- Description: Maximum probability.
- Default: [1]
- Type: float
- Min: 0
- Max: 1
- Unique: no

### decreasing

- Description: Decreasing.
- Default: [False]
- Type: bool
- Unique: no


## LinearOsc

Linear oscillating.

### seg_len_range

- Description: Segment length range.
- Default: [(1, 1)]
- Type: int
- Min: 1
- Unique: no

### granularity

- Description: Rhythmic granularity.
- Default: [0]
- Type: Fraction
- Min: 0
- Unique: no

### grain_offset

- Description: Granularity offset.
- Only has effect if granularity == 'true'
- Default: [0]
- Type: Fraction
- Min: 0
- Unique: no

### min_prob

- Description: Minimum probability.
- Default: [0]
- Type: float
- Min: 0
- Max: 1
- Unique: no

### max_prob

- Description: Maximum probability.
- Default: [1]
- Type: float
- Min: 0
- Max: 1
- Unique: no

### decreasing

- Description: Decreasing.
- Default: [False]
- Type: bool
- Unique: no

### period

- Description: Oscillation period.
- Default: [4]
- Type: Fraction
- Min: 0
- Unique: no

### offset

- Description: Oscillation offset.
- Default: [0]
- Type: Fraction
- Min: 0
- Unique: no


## Saw

Saw wave.

### seg_len_range

- Description: Segment length range.
- Default: [(1, 1)]
- Type: int
- Min: 1
- Unique: no

### granularity

- Description: Rhythmic granularity.
- Default: [0]
- Type: Fraction
- Min: 0
- Unique: no

### grain_offset

- Description: Granularity offset.
- Only has effect if granularity == 'true'
- Default: [0]
- Type: Fraction
- Min: 0
- Unique: no

### min_prob

- Description: Minimum probability.
- Default: [0]
- Type: float
- Min: 0
- Max: 1
- Unique: no

### max_prob

- Description: Maximum probability.
- Default: [1]
- Type: float
- Min: 0
- Max: 1
- Unique: no

### decreasing

- Description: Decreasing.
- Default: [False]
- Type: bool
- Unique: no

### period

- Description: Oscillation period.
- Default: [4]
- Type: Fraction
- Min: 0
- Unique: no

### offset

- Description: Oscillation offset.
- Default: [0]
- Type: Fraction
- Min: 0
- Unique: no


## Sine

Sine wave.

### seg_len_range

- Description: Segment length range.
- Default: [(1, 1)]
- Type: int
- Min: 1
- Unique: no

### granularity

- Description: Rhythmic granularity.
- Default: [0]
- Type: Fraction
- Min: 0
- Unique: no

### grain_offset

- Description: Granularity offset.
- Only has effect if granularity == 'true'
- Default: [0]
- Type: Fraction
- Min: 0
- Unique: no

### min_prob

- Description: Minimum probability.
- Default: [0]
- Type: float
- Min: 0
- Max: 1
- Unique: no

### max_prob

- Description: Maximum probability.
- Default: [1]
- Type: float
- Min: 0
- Max: 1
- Unique: no

### decreasing

- Description: Decreasing.
- Default: [False]
- Type: bool
- Unique: no

### period

- Description: Oscillation period.
- Default: [4]
- Type: Fraction
- Min: 0
- Unique: no

### offset

- Description: Oscillation offset.
- Default: [0]
- Type: Fraction
- Min: 0
- Unique: no


## Accumulating

Accumulating.

### seg_len_range

- Description: Segment length range.
- Default: [(1, 1)]
- Type: int
- Min: 1
- Unique: no

### granularity

- Description: Rhythmic granularity.
- Default: [0]
- Type: Fraction
- Min: 0
- Unique: no

### grain_offset

- Description: Granularity offset.
- Only has effect if granularity == 'true'
- Default: [0]
- Type: Fraction
- Min: 0
- Unique: no

### prob

- Description: Static probability.
- Default: [0.05]
- Type: float
- Min: 0
- Max: 1
- Unique: no

### acc_modulo

- Description: Accumulation modulo.
- Default: [8]
- Type: int
- Min: 0
- Unique: no

### decreasing

- Description: Decreasing.
- Default: True
- Type: bool
- Unique: yes


## RandomToggle

Random toggle.

### seg_len_range

- Description: Segment length range.
- Default: [(1, 1)]
- Type: int
- Min: 1
- Unique: no

### granularity

- Description: Rhythmic granularity.
- Default: [0]
- Type: Fraction
- Min: 0
- Unique: no

### grain_offset

- Description: Granularity offset.
- Only has effect if granularity == 'true'
- Default: [0]
- Type: Fraction
- Min: 0
- Unique: no

### on_prob

- Description: On probability.
- Default: [0.25]
- Type: float
- Min: 0
- Max: 1
- Unique: no

### off_prob

- Description: Off probability.
- Default: [0.25]
- Type: float
- Min: 0
- Max: 1
- Unique: no
