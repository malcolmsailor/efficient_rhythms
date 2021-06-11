import collections

from . import er_misc_funcs


class TimeoutError(Exception):
    pass


class ErSettingsError(Exception):
    pass


class ErMakeException(Exception):
    pass


class UnableToChoosePitchError(ErMakeException):
    def __init__(self):
        super().__init__()
        self.too_many_alternations = 0
        self.too_many_repeated_notes = 0
        self.pitch_loop_just_one_pitch = 0

    def __str__(self):
        return (
            "Unable to choose from available pitches in constructing "
            "basic pattern.\n"
            "Number of times exceeding max_alternations:   {}.\n"
            "Number of times exceeding max_repeated_notes: {}.\n"
            "Number of times pitch loop just one pitch:    {}."
            "".format(
                self.too_many_alternations,
                self.too_many_repeated_notes,
                self.pitch_loop_just_one_pitch,
            )
        )


class AvailablePitchMaterialsError(ErMakeException):
    """Error will be raised if at any stage of _attempt_harmony_pattern
    there are no available pitch-classes or pitches."""

    def __init__(self, er):
        super().__init__()
        self._init_total_counts()
        self.reset_inner_counts()

        self.forbidden_parallels_str = (
            f"prohibit_parallels: {er.prohibit_parallels}"
        )
        self._max_count = er.max_available_pitch_materials_deadends
        self.num_attempts = er.initial_pattern_attempts
        self.printer = er.build_status_printer

    def reset_inner_counts(self):
        self._no_available_pcs = 0
        self._no_available_pitches = 0
        self._exceeding_max_interval = 0
        self._forbidden_parallels = 0
        self._unable_to_choose_pitch = 0
        self._excess_alternations = 0
        self._excess_repeated_notes = 0
        self._pitch_loop_just_one_pitch = 0
        self._all_count = 0

    def _init_total_counts(self):
        self._total_no_available_pcs = 0
        self._total_no_available_pitches = 0
        self._total_exceeding_max_interval = 0
        self._total_forbidden_parallels = 0
        self._total_unable_to_choose_pitch = 0
        self._total_excess_alternations = 0
        self._total_excess_repeated_notes = 0
        self._total_pitch_loop_just_one_pitch = 0

    def _update_count(self):
        self._all_count += 1
        self.status()
        if self._all_count >= self._max_count:
            raise self

    def no_available_pcs(self):
        self._no_available_pcs += 1
        self._total_no_available_pcs += 1
        self._update_count()

    def no_available_pitches(self):
        self._no_available_pitches += 1
        self._total_no_available_pitches += 1
        self._update_count()

    def exceeding_max_interval(self):
        self._exceeding_max_interval += 1
        self._total_exceeding_max_interval += 1
        self._update_count()

    def forbidden_parallels(self):
        self._forbidden_parallels += 1
        self._total_forbidden_parallels += 1
        self._update_count()

    def unable_to_choose_pitch(self):
        self._unable_to_choose_pitch += 1
        self._total_unable_to_choose_pitch += 1
        self._update_count()

    def excess_alternations(self, count=1):
        self._excess_alternations += count
        self._total_excess_alternations += count

    def excess_repeated_notes(self, count=1):
        self._excess_repeated_notes += count
        self._total_excess_repeated_notes += count

    def pitch_loop_just_one_pitch(self, count=1):
        self._pitch_loop_just_one_pitch += count
        self._total_pitch_loop_just_one_pitch += count

    def __str__(self):

        return (
            "\nUnable to find available pitches while making basic pattern "
            "after {} attempts\n"
            "Number of times no available pitch-classes:              {:3}\n"
            "Number of times no available pitches:                    {:3}\n"
            "Number of times no pitches within max interval:          {:3}\n"
            # "        ({})\n"
            "Number of times forbidden parallels:                     {:3}\n"
            "        ({})\n"
            "Number of times unable to choose from available pitches: {:3}\n"
            "        Excess alternations:           {:3}\n"
            "        Excess repeated notes:         {:3}\n"
            "        Pitch loop just one pitch:     {:3}\n"
            "".format(
                self.num_attempts,
                self._total_no_available_pcs,
                self._total_no_available_pitches,
                self._total_exceeding_max_interval,
                # self.max_interval_str,
                self._total_forbidden_parallels,
                self.forbidden_parallels_str,
                self._total_unable_to_choose_pitch,
                self._total_excess_alternations,
                self._total_excess_repeated_notes,
                self._total_pitch_loop_just_one_pitch,
            )
        )

    @property
    def counts(self):
        return (
            (self._no_available_pcs, self._total_no_available_pcs),
            (self._no_available_pitches, self._total_no_available_pitches),
            (self._exceeding_max_interval, self._total_exceeding_max_interval),
            (self._forbidden_parallels, self._total_forbidden_parallels),
            (self._excess_alternations, self._total_excess_alternations),
            (self._excess_repeated_notes, self._total_excess_repeated_notes),
            (
                self._pitch_loop_just_one_pitch,
                self._total_pitch_loop_just_one_pitch,
            ),
        )

    def status(self):
        self.printer.initial_pattern_status(*self.counts)


class NoMoreVoiceLeadingsError(ErMakeException):
    """Raised if cannot find voice-leading of necessary displacement."""


class VoiceLeadingError(ErMakeException):
    def out_of_range(self):
        self._out_of_range += 1
        self._total_out_of_range += 1

    def check_intervals(self):
        self._check_intervals += 1
        self._total_check_intervals += 1

    def check_consonance(self):
        self._check_consonance += 1
        self._total_check_consonance += 1

    def limit_intervals(self):
        self._limit_intervals += 1
        self._total_limit_intervals += 1

    def parallel_intervals(self):
        self._parallel_intervals += 1
        self._total_parallel_intervals += 1

    def __init__(self, er=None):
        super().__init__()
        self.total_failures = 0
        self.harmony_counter = collections.Counter()
        self._init_total_counts()
        self.reset_inner_counts()
        # This class should always be created with er non-None. But this
        # check allows the instances to be copied for debugging purposes.
        if er is not None:
            self.num_attempts = er.voice_leading_attempts
            self.printer = er.build_status_printer

    def reset_inner_counts(self):
        self._out_of_range = 0
        self._check_consonance = 0
        self._check_intervals = 0
        self._limit_intervals = 0
        self._parallel_intervals = 0

    def _init_total_counts(self):
        self._total_out_of_range = 0
        self._total_check_consonance = 0
        self._total_check_intervals = 0
        self._total_limit_intervals = 0
        self._total_parallel_intervals = 0

    @property
    def counts(self):
        return (
            (self._out_of_range, self._total_out_of_range),
            (self._check_intervals, self._total_check_intervals),
            (self._check_consonance, self._total_check_consonance),
            (self._limit_intervals, self._total_limit_intervals),
            (self._parallel_intervals, self._total_parallel_intervals),
        )

    def status(self):
        self.printer.voice_leading_status(*self.counts)

    def __str__(self):
        counter_strs = []
        within = False
        max_count = 0
        for (
            (prev_harmony_i, harmony_i),
            count,
        ) in self.harmony_counter.items():
            if prev_harmony_i == harmony_i:
                if count > max_count:
                    within = True
                    max_count = count
                counter_strs.append(
                    er_misc_funcs.add_line_breaks(
                        f"{count:3} failures within harmony {prev_harmony_i:2}",
                        indent_type="all",
                    )
                )
            else:
                if count > max_count:
                    within = False
                    max_count = count
                counter_strs.append(
                    er_misc_funcs.add_line_breaks(
                        f"{count:3} failures between harmony "
                        f"{prev_harmony_i:2} and harmony {harmony_i:2}",
                        indent_type="all",
                    )
                )
        if within:
            counter_strs.append(
                er_misc_funcs.add_line_breaks(
                    "Voice-leading failures within harmonies usually occur "
                    "in conjunction with the use of different values of "
                    "`pattern_len` "
                    "in different voices. You might try more permissive "
                    "settings, like `consonance_treatment = 'none'` or "
                    "`voice_lead_chord_tones = False`",
                    indent_type="none",
                )
            )
        counter_str = "\n".join(counter_strs)
        return (
            f"\nUnable to voice-lead {self.num_attempts} attempts at "
            "initial pattern.\n"
            f"{counter_str}"
        )
