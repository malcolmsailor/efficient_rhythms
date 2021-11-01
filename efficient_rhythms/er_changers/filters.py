import fractions
import inspect

from .. import er_classes
from .. import er_misc_funcs

from . import prob_curves
from .changers import Changer


class Filter(Changer):
    pretty_name = "Pitch filter"
    description = pretty_name + " removes notes of any pitch"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_attribute(
            "adjust_dur",
            "None",
            "Adjust durations",
            str,
            attr_val_kwargs={
                "possible_values": [
                    "None",
                    "Extend_previous_notes",
                    "Subtract_duration",
                ]
            },
            unique=True,
        )
        self.add_attribute(
            "adjust_dur_comma",
            0.25,
            "Adjust durations comma",
            float,
            attr_val_kwargs={"min_value": 0, "max_value": -1},
            unique=True,
            display_if={"adjust_dur": "Extend_previous_notes"},
        )
        self.add_attribute(
            "subtract_dur_modulo",
            0,
            "Subtract durations within length",
            fractions.Fraction,
            attr_val_kwargs={"min_value": 0.001, "max_value": -1},
            unique=True,
            display_if={"adjust_dur": "Subtract_duration"},
        )
        self.dur_adjust_durs = self.dur_adjust_onsets = None

    def _process_all_voices(self, notes_by_voices):
        if (
            self.adjust_dur != "Subtract_duration"  # pylint: disable=no-member
            or self.by_voice  # pylint: disable=no-member
        ):
            return
        self.dur_adjust_onsets = []
        self.dur_adjust_durs = []
        dur_adjust_dict = {}
        for notes in notes_by_voices.values():
            for note in notes:
                if note.onset in dur_adjust_dict:
                    dur_adjust_dict[note.onset] = min(
                        note.dur, dur_adjust_dict[note.onset]
                    )
                else:
                    dur_adjust_dict[note.onset] = note.dur

        dur_adjustment = 0
        last_mod_onset = 0
        for onset in sorted(dur_adjust_dict.keys()):
            if self.subtract_dur_modulo:  # pylint: disable=no-member
                mod_onset = (
                    onset
                    % self.subtract_dur_modulo  # pylint: disable=no-member
                )
                if mod_onset < last_mod_onset:
                    dur_adjustment = -mod_onset
                last_mod_onset = mod_onset
            dur_adjustment -= dur_adjust_dict[onset]
            self.dur_adjust_onsets.append(onset)
            self.dur_adjust_durs.append(dur_adjustment)

    def change_func(self, voice, notes_to_change):

        if (
            self.adjust_dur != "None"  # pylint: disable=no-member
            and voice.is_polyphonic
        ):
            print(
                er_misc_funcs.add_line_breaks(
                    f"Notice: adjust durations in polyphonic voice {voice.voice_i} "
                    "may produce unexpected results.",
                    indent_width=8,
                    indent_type="all",
                )
            )

        voice.filtered_notes = er_classes.Voice(
            voice_i=voice.voice_i, tet=voice.tet, voice_range=voice.range
        )

        if (
            self.adjust_dur == "Subtract_duration"  # pylint: disable=no-member
            and self.by_voice  # pylint: disable=no-member
        ):
            dur_adjustment = 0
            self.dur_adjust_onsets = []
            self.dur_adjust_durs = []
            last_mod_onset = 0
        for note in notes_to_change:
            if (
                self.adjust_dur  # pylint: disable=no-member
                == "Extend_previous_notes"
            ):
                prev_note = voice.get_prev_note(note.onset)
                if prev_note and (
                    note.onset - prev_note.onset - prev_note.dur
                    < self.adjust_dur_comma  # pylint: disable=no-member
                ):
                    prev_note.dur = note.onset + note.dur - prev_note.onset
            if (
                self.adjust_dur  # pylint: disable=no-member
                == "Subtract_duration"
                and self.by_voice  # pylint: disable=no-member
            ):
                if self.subtract_dur_modulo:  # pylint: disable=no-member
                    mod_onset = (
                        note.onset
                        % self.subtract_dur_modulo  # pylint: disable=no-member
                    )
                    if mod_onset < last_mod_onset:
                        dur_adjustment = -mod_onset
                    last_mod_onset = mod_onset
                dur_adjustment -= note.dur
                self.dur_adjust_onsets.append(note.onset)
                self.dur_adjust_durs.append(dur_adjustment)
            voice.filtered_notes.add_note(note.copy())
            voice.remove_note(note)
        # voice.filtered_notes.update_sort()
        if self.adjust_dur == "Subtract_duration":  # pylint: disable=no-member
            i = -1
            notes_to_move = []
            dur_adjustment = 0
            for note in voice:
                try:
                    while note.onset >= self.dur_adjust_onsets[i + 1]:
                        i += 1
                        dur_adjustment = self.dur_adjust_durs[i]
                except IndexError:
                    pass
                notes_to_move.append((note, note.onset + dur_adjustment))
            for note, new_onset in notes_to_move:
                voice.move_note(note, new_onset)


class PitchFilter(Filter):
    # alias for Filter
    pass


class RangeFilter(Filter):
    pretty_name = "Range filter"
    description = (
        pretty_name
        + " removes notes whose pitches lie outside the specified range(s)"
    )

    def __init__(self, *args, filter_range=((0, 127),), **kwargs):
        def pitch_in_range(note_object):
            for range_tuple in self.filter_range:  # pylint: disable=no-member
                if range_tuple[0] <= note_object.pitch <= range_tuple[1]:
                    return False
            return True

        super().__init__(*args, **kwargs)
        self.add_attribute(
            "filter_range",
            filter_range,
            "Range(s) to pass through filter",
            int,
            attr_val_kwargs={"min_value": 0, "max_value": -1, "tuple_of": -2},
            unique=True,  # CHANGER_TODO not sure this should be unique
        )
        self.condition = pitch_in_range


class OscillatingRangeFilter(Filter):
    pretty_name = "Oscillating range filter"
    description = (
        pretty_name
        + " removes notes whose pitches lie outside of a range whose bounds "
        "oscillate according to parameters that you control."
    )

    def pitch_in_osc_range(self, note_object):
        range_width = (
            self.bottom_range[1]  # pylint: disable=no-member
            - self.bottom_range[0]  # pylint: disable=no-member
        )
        l_bound = round(
            prob_curves.linear_osc(
                note_object.onset
                + self.osc_offset,  # pylint: disable=no-member
                self.bottom_range[0],  # pylint: disable=no-member
                self.bottom_range[0]  # pylint: disable=no-member
                + self.range_size,  # pylint: disable=no-member
                self.osc_period,  # pylint: disable=no-member
            )
        )
        if l_bound <= note_object.pitch <= l_bound + range_width:
            return False
        return True

    def __init__(
        self,
        *args,
        bottom_range=(0, 127),
        range_size=36,
        osc_period=8,
        osc_offset=0,
        **kwargs,
    ):

        super().__init__(*args, **kwargs)
        self.add_attribute(
            "bottom_range",
            bottom_range,
            "Range at bottom of oscillation",
            int,
            attr_val_kwargs={"min_value": 0, "max_value": -1, "tuple_of": 2},
            unique=True,
        )
        self.add_attribute(
            "range_size",
            range_size,
            "Size in pitches of oscillation",
            int,
            attr_val_kwargs={"min_value": 0, "max_value": -1},
            unique=True,
        )
        self.add_attribute(
            "osc_period",
            osc_period,
            "Oscillation period",
            int,
            attr_val_kwargs={"min_value": 0.01, "max_value": -1},
            unique=True,
        )
        self.add_attribute(
            "osc_offset",
            osc_offset,
            "Oscillation period offset",
            int,
            attr_val_kwargs={"min_value": 0, "max_value": -1},
            unique=True,
        )
        self.condition = self.pitch_in_osc_range


class OddPitchFilter(Filter):
    pretty_name = "Odd pitch filter"
    description = pretty_name + " removes notes of odd pitch"

    def __init__(self, *args, **kwargs):
        def odd_pitch(note_object):
            if note_object.pitch % 2 == 1:
                return True
            return False

        super().__init__(*args, **kwargs)
        self.condition = odd_pitch


class EvenPitchFilter(Filter):
    pretty_name = "Even pitch filter"
    description = pretty_name + " removes notes of even pitch"

    def __init__(self, *args, **kwargs):
        def even_pitch(note_object):
            if note_object.pitch % 2 == 0:
                return True
            return False

        super().__init__(*args, **kwargs)
        self.condition = even_pitch


class FilterSelectedPCs(Filter):
    pretty_name = "Selected pitch-class filter"
    description = pretty_name + " removes notes of the selected pitch-classes"

    def __init__(self, *args, selected_pcs=(), **kwargs):
        super().__init__(*args, **kwargs)
        self.condition = self.pitch_in_selected_pcs
        self.add_attribute(
            "selected_pcs",
            selected_pcs,
            "Pitch-classes to filter",
            int,
            attr_val_kwargs={"min_value": 0, "max_value": self.tet - 1},
            attr_hint=("TET", self.tet),
        )

    def pitch_in_selected_pcs(self, note_object):
        if (
            note_object.pitch % self.tet
            in self.selected_pcs  # pylint: disable=no-member
        ):
            return True
        return False


class FilterUnselectedPCs(Filter):
    pretty_name = "Unselected pitch-class filter"
    description = (
        pretty_name + " removes notes that do *not* belong to the "
        " selected pitch-classes"
    )

    def __init__(self, *args, selected_pcs=(), **kwargs):
        super().__init__(*args, **kwargs)
        self.condition = self.pitch_not_in_selected_pcs
        self.add_attribute(
            "selected_pcs",
            selected_pcs,
            "Pitch-classes not to filter",
            int,
            attr_val_kwargs={"min_value": 0, "max_value": self.tet - 1},
            attr_hint=("TET", self.tet),
        )

    def pitch_not_in_selected_pcs(self, note_object):
        if (
            note_object.pitch % self.tet
            in self.selected_pcs  # pylint: disable=no-member
        ):
            return False
        return True


FILTERS = tuple(
    name
    for name, cls in locals().items()
    if inspect.isclass(cls) and issubclass(cls, Filter) and cls not in (Filter,)
)
