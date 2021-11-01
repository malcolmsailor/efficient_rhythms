import warnings

from .. import er_rhythm
from .. import er_misc_funcs


def notify_user_of_unusual_settings(er, silent=False):
    def print_(text):
        if silent:
            return
        print(er_misc_funcs.add_line_breaks(text))

    if er.cont_rhythms == "grid":
        er_rhythm.Grid.validate_er_settings(er, silent=silent)
    elif er.cont_rhythms == "all":
        er_rhythm.ContRhythm.validate_er_settings(er, silent=silent)

    # if er.len_to_force_chord_tone == 0 and er.scale_chord_tone_prob_by_dur:
    #     raise er_exceptions.ErSettingsError(
    #         "If 'scale_chord_tone_prob_by_dur' is True, then "
    #         "'len_to_force_chord_tone' must be non-zero."
    #     )
    # if len(er.voice_ranges) < er.num_voices:
    #     raise er_exceptions.ErSettingsError("len(voice_ranges) < num_voices")
    if er.scale_short_chord_tones_down and er.try_to_force_non_chord_tones:
        print_(
            "Warning: 'scale_short_chord_tones_down' and "
            "'try_to_force_non_chord_tones' are both true. Strange results may occur, "
            "particularly if there are many short notes."
        )
    if (
        er.chord_tones_sync_onset_in_all_voices
        and er.scale_chord_tone_prob_by_dur
    ):
        print(
            "Notice: 'chord_tones_sync_onset_in_all_voices' and "
            "'scale_chord_tone_prob_by_dur' are both true. Long notes in some "
            "voices may be non chord tones."
        )
    if er.chord_tone_selection != er.voice_lead_chord_tones:
        print_(
            f"Notice: 'chord_tone_selection' is {er.chord_tone_selection} "
            f"and 'voice_lead_chord_tones' is {er.voice_lead_chord_tones}"
        )

    if er.logic_type_pitch_bend:
        if er.tet == 12:
            print("Notice: 'logic_type_pitch_bend' is True and 12-tet.")
        else:
            if not er.voices_separate_tracks and er.num_voices > 1:
                warnings.warn(
                    "'logic_type_pitch_bend' and "
                    "not 'voices_separate_tracks'"
                )
            if not er.choirs_separate_tracks and er.num_choirs > 1:
                warnings.warn(
                    "'logic_type_pitch_bend' and "
                    "not 'choirs_separate_tracks'"
                )
            if er.choirs_separate_channels and er.num_choirs > 1:
                warnings.warn(
                    "'logic_type_pitch_bend' and "
                    "'choirs_separate_channels'\n"
                    "   Ignoring 'choirs_separate_channels'..."
                )

    if er.parallel_voice_leading and er.vl_maintain_consonance:
        print_(
            "Notice: 'parallel_voice_leading' is not compatible with "
            "checking voice-leadings for consonance. Ignoring "
            "'vl_maintain_consonance'"
        )

    soft_loop_max_alt_conflicts = []
    for voice_i in range(er.num_voices):
        if (
            er.get(voice_i, "pitch_loop")
            and not er.get(voice_i, "hard_pitch_loop")
            and (er.get(voice_i, "max_alternations") > 0)
        ):
            soft_loop_max_alt_conflicts.append(voice_i)
    if soft_loop_max_alt_conflicts:
        print_(
            "Notice: in {} {}, soft pitch loops are enabled and "
            "max_alternations is set as well. This "
            "may lead to shorter loops than expected in {}."
            "".format(
                "voice" if len(soft_loop_max_alt_conflicts) == 1 else "voices",
                soft_loop_max_alt_conflicts,
                "this voice"
                if len(soft_loop_max_alt_conflicts) == 1
                else "these voices",
            )
        )

    for limit_interval in ("max_interval", "min_interval"):
        soft_loop_limit_interval_conflicts = []
        for voice_i in range(er.num_voices):
            if (
                er.get(voice_i, "pitch_loop")
                and not er.get(voice_i, "hard_pitch_loop")
                and er.get(voice_i, limit_interval + "_for_non_chord_tones")
                and (
                    er.get(voice_i, limit_interval + "_for_non_chord_tones")
                    != er.get(voice_i, limit_interval)
                )
            ):
                soft_loop_limit_interval_conflicts.append(voice_i)
        if soft_loop_limit_interval_conflicts:
            voice_str = (
                "voice"
                if len(soft_loop_limit_interval_conflicts) == 1
                else "voices"
            )
            this_str = (
                "this voice"
                if len(soft_loop_limit_interval_conflicts) == 1
                else "these voices"
            )
            print_(
                f"Notice: in {voice_str} {soft_loop_limit_interval_conflicts}, "
                "soft pitch loops are enabled and "
                f"{limit_interval}_for_non_chord_tones is not equal to "
                f"{limit_interval}. Since chord tones can "
                "proceed by different intervals than non chord tones in "
                f"{this_str}, this may lead to shorter loops than expected."
            )

    if 1 in er.max_interval and er.chord_tone_selection:
        warnings.warn(
            er_misc_funcs.add_line_breaks(
                "Max interval of 1 (i.e., a 2nd) in at least "
                "one voice and 'chord_tone_selection' is true. "
                "This is likely to lead to excess repeated notes."
            )
        )

    for i, (l_bound, u_bound) in enumerate(er.hard_bounds):
        if u_bound - l_bound < er.tet:
            warnings.warn(
                er_misc_funcs.add_line_breaks(
                    f"Hard bounds at index {i} are less than an octave "
                    f"(tet={er.tet}); it is recommended they be at least an "
                    "octave."
                )
            )
