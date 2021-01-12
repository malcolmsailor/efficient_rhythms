import collections


class UnableToChoosePitchError(Exception):
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


class AvailablePitchMaterialsError(Exception):
    """Error will be raised if at any stage of _attempt_harmony_pattern
    there are no available pitch-classes or pitches."""

    def __init__(self, er):
        super().__init__()
        self._no_available_pcs = 0
        self._no_available_pitches = 0

        self._exceeding_max_interval = 0
        # max_interval_type = "generic" if er.max_interval > 0 else "specific"
        # self.max_interval_str = (
        #     f"Max {max_interval_type} interval = {er.max_interval}")

        self._forbidden_parallels = 0
        self.forbidden_parallels_str = (
            f"Forbidden parallels: {er.prohibit_parallels}"
        )

        self._unable_to_choose_pitch = 0
        self._excess_alternations = 0
        self._excess_repeated_notes = 0
        self._pitch_loop_just_one_pitch = 0
        self._total_count = 0
        self._max_count = er.max_available_pitch_materials_deadends
        self.num_attempts = er.initial_pattern_attempts

    def _update_count(self):
        self._total_count += 1
        if self._total_count >= self._max_count:
            raise self

    def no_available_pcs(self):
        self._no_available_pcs += 1
        self._update_count()

    def no_available_pitches(self):
        self._no_available_pitches += 1
        self._update_count()

    def exceeding_max_interval(self):
        self._exceeding_max_interval += 1
        self._update_count()

    def forbidden_parallels(self):
        self._forbidden_parallels += 1
        self._update_count()

    def unable_to_choose_pitch(self):
        self._unable_to_choose_pitch += 1
        self._update_count()

    def excess_alternations(self, count=1):
        self._excess_alternations += count

    def excess_repeated_notes(self, count=1):
        self._excess_repeated_notes += count

    def pitch_loop_just_one_pitch(self, count=1):
        self._pitch_loop_just_one_pitch += count

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
                self._no_available_pcs,
                self._no_available_pitches,
                self._exceeding_max_interval,
                # self.max_interval_str,
                self._forbidden_parallels,
                self.forbidden_parallels_str,
                self._unable_to_choose_pitch,
                self._excess_alternations,
                self._excess_repeated_notes,
                self._pitch_loop_just_one_pitch,
            )
        )

    def status(self):
        out = (
            "No PCs:{:<3} No Ps:{:<3} Max int:{:<3} = ints:{:<3} Alts:{:<3} "
            "Reps:{:<3} Loop:{:<3}"
            "".format(
                self._no_available_pcs,
                self._no_available_pitches,
                self._exceeding_max_interval,
                self._forbidden_parallels,
                self._excess_alternations,
                self._excess_repeated_notes,
                self._pitch_loop_just_one_pitch,
            )
        )
        return out


class NoMoreVoiceLeadingsError(Exception):
    """Raised if cannot find voice-leading of necessary displacement."""


class VoiceLeadFailureCounter:
    def __init__(self):
        self.out_of_range = 0
        self.check_intervals = 0
        self.check_consonance = 0
        self.limit_intervals = 0

    def __str__(self):
        out = (
            "Out of range:{:<4} Harm. ints:{:<4} "
            "Not consonant:{:<4} Mel. ints:{:<4}"
            "".format(
                self.out_of_range,
                self.check_intervals,
                self.check_consonance,
                self.limit_intervals,
            )
        )
        return out


class VoiceLeadingError(Exception):
    def __init__(self, er):
        super().__init__()
        self.total_failures = 0
        self.harmony_counter = collections.Counter()
        self.temp_failure_counter = VoiceLeadFailureCounter()
        self.total_failure_counter = VoiceLeadFailureCounter()
        self.num_attempts = er.voice_leading_attempts

    def reset_temp_counter(self):
        total_vars = vars(self.total_failure_counter)
        temp_vars = vars(self.temp_failure_counter)
        for var in total_vars:
            total_vars[var] += temp_vars[var]
        self.temp_failure_counter = VoiceLeadFailureCounter()

    def __str__(self):
        self.reset_temp_counter()
        counter_strs = []
        for (prev_harmony_i, harmony_i), count in self.harmony_counter.items():
            counter_strs.append(
                f"   {count:3} failures between harmony {prev_harmony_i:2} "
                f"and harmony {harmony_i:2}"
            )
        counter_str = "\n".join(counter_strs)
        return (
            "\nUnable to voice-lead {} attempts at initial_pattern.\n"
            "Total voice-leading failures: {}\n"
            "{}\n"
            "{}".format(
                self.num_attempts,
                self.total_failures,
                str(self.total_failure_counter),
                counter_str,
            )
        )
