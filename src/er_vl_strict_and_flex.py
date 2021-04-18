import src.er_exceptions as er_exceptions
import src.er_notes as er_notes
import src.er_voice_leadings as er_voice_leadings

import src.er_apply_vl as er_apply_vl


def voice_lead_pattern_flexibly(
    er, super_pattern, voice_lead_error, pattern_voice_leading_i=0
):
    """This voice-leading algorithm will change voice-leading in
    the middle of a pattern if it runs into a problem.
    """

    voice_lead_error.status()

    try:
        vl_item = er.pattern_voice_leading_order[pattern_voice_leading_i]
    except IndexError:
        # if we reach the end of the list, then we've effected all the
        # voice-leadings.
        return True

    voice = super_pattern.voices[vl_item.voice_i]
    rhythm = er.rhythms[vl_item.voice_i]

    prev_harmony_end_time = new_harmony_end_time = -1

    first_note = True

    new_notes = er_notes.Voice()
    rhythm_i = vl_item.start_rhythm_i
    for prev_note_i, prev_note in enumerate(voice):
        prev_attack_time = prev_note.attack_time
        if prev_note_i < vl_item.prev_start_rhythm_i:
            continue
        if prev_attack_time >= vl_item.end_time:
            break

        new_attack_time, new_dur = rhythm.get_attack_time_and_dur(rhythm_i)

        update_voice_leadings = False

        if prev_attack_time >= prev_harmony_end_time:
            prev_harmony_i = super_pattern.get_harmony_i(prev_attack_time)
            prev_harmony_end_time = super_pattern.get_harmony_times(
                prev_harmony_i
            ).end_time
            update_voice_leadings = True

        if new_attack_time >= new_harmony_end_time:
            new_harmony_i = super_pattern.get_harmony_i(new_attack_time)
            new_harmony_end_time = super_pattern.get_harmony_times(
                new_harmony_i
            ).end_time
            update_voice_leadings = True

        if update_voice_leadings:
            voice_leader = er_voice_leadings.VoiceLeader(
                er, prev_harmony_i, new_harmony_i
            )
            voice_leading = voice_leader.get_next_voice_leading()

            prev_pc_scale = er.get(prev_harmony_i, "pc_scales")

        while True:
            (
                new_note,
                voice_leading_motion_tup,
            ) = er_apply_vl.apply_voice_leading(
                er,
                super_pattern,
                prev_note,
                first_note,
                new_attack_time,
                new_dur,
                vl_item.voice_i,
                new_harmony_i,
                prev_harmony_i,
                prev_pc_scale,
                voice_leading,
                new_notes,
                voice_lead_error,
            )
            if new_note:
                new_notes.add_note_object(new_note)
                first_note = False
                rhythm_i += 1
                break
            try:
                voice_leader.exclude_voice_leading_motion(
                    *voice_leading_motion_tup
                )
                voice_leading = voice_leader.get_next_voice_leading()
            except er_exceptions.NoMoreVoiceLeadingsError:
                # print(prev_harmony_i, new_harmony_i)
                voice_lead_error.total_failures += 1
                voice_lead_error.harmony_counter[
                    (prev_harmony_i, new_harmony_i)
                ] += 1
                return False

    for note in new_notes:
        voice.add_note_object(note)

    if voice_lead_pattern_strictly(
        er,
        super_pattern,
        voice_lead_error,
        pattern_voice_leading_i=pattern_voice_leading_i + 1,
    ):
        return True

    if voice_lead_pattern_flexibly(
        er,
        super_pattern,
        voice_lead_error,
        pattern_voice_leading_i=pattern_voice_leading_i + 1,
    ):
        return True

    for note in new_notes:
        voice.remove_note(note.pitch, note.attack_time)

    return False


# def voice_lead_pattern_strictly(
#     er, super_pattern, voice_lead_error, pattern_voice_leading_i=0
# ):
#
#     voice_lead_error.status()
#
#     try:
#         vl_item = er.pattern_voice_leading_order[pattern_voice_leading_i]
#     except IndexError:
#         # if we reach the end of the list, then we've effected all the
#         # voice-leadings.
#         return True
#
#     voice = super_pattern.voices[vl_item.voice_i]
#     rhythm = er.rhythms[vl_item.voice_i]
#
#     new_attack_time = vl_item.start_time
#
#     new_notes = er_notes.Voice()
#     success_rhythm_i = vl_item.start_rhythm_i
#
#     # In the event that the voice is empty, skip this loop.
#     if voice:
#
#         prev_attack_time = rhythm.get_attack_time_and_dur(
#             vl_item.prev_start_rhythm_i
#         )[0]
#
#         while True:
#             # This loop updates the harmony
#             new_harmony_i = super_pattern.get_harmony_i(new_attack_time)
#             new_harmony_times = super_pattern.get_harmony_times(new_harmony_i)
#
#             prev_harmony_i = super_pattern.get_harmony_i(prev_attack_time)
#             prev_harmony_times = super_pattern.get_harmony_times(prev_harmony_i)
#
#             voice_leader = er_voice_leadings.VoiceLeader(
#                 er, prev_harmony_i, new_harmony_i
#             )
#             voice_leading = voice_leader.get_next_voice_leading()
#
#             prev_pc_scale = er.get(prev_harmony_i, "pc_scales")
#
#             while True:
#                 rhythm_i = success_rhythm_i
#                 new_sub_notes = er_notes.Voice()
#                 first_note = True
#                 success = True
#
#                 for prev_note_i, prev_note in enumerate(voice):
#                     # There must be a better way of locating where to start
#                     #   than scanning linearly over the list. But in practice
#                     #   scores seem to be short enough that this isn't a big
#                     #   issue.
#                     if prev_note_i < vl_item.prev_start_rhythm_i:
#                         continue
#                     if prev_note_i >= vl_item.prev_end_rhythm_i:
#                         break
#                     prev_attack_time = prev_note.attack_time
#
#                     if prev_attack_time < prev_harmony_times.start_time:
#                         continue
#                     if prev_attack_time >= prev_harmony_times.end_time:
#                         break
#                     new_attack_time, new_dur = rhythm.get_attack_time_and_dur(
#                         rhythm_i
#                     )
#                     if new_attack_time < new_harmony_times.start_time:
#                         continue
#                     if new_attack_time >= new_harmony_times.end_time:
#                         break
#                     if rhythm_i >= vl_item.end_rhythm_i:
#                         break
#
#                     (
#                         new_note,
#                         voice_leading_motion_tup,
#                     ) = er_apply_vl.apply_voice_leading(
#                         er,
#                         super_pattern,
#                         prev_note,
#                         first_note,
#                         new_attack_time,
#                         new_dur,
#                         vl_item.voice_i,
#                         new_harmony_i,
#                         prev_harmony_i,
#                         prev_pc_scale,
#                         voice_leading,
#                         new_sub_notes,
#                         voice_lead_error,
#                     )
#
#                     if new_note:
#                         new_sub_notes.add_note_object(new_note)
#                         first_note = False
#                         rhythm_i += 1
#                     else:
#                         success = False
#                         break
#
#                 if success:
#                     new_notes.append(new_sub_notes)
#                     success_rhythm_i = rhythm_i
#                     break
#
#                 try:
#                     voice_leader.exclude_voice_leading_motion(
#                         *voice_leading_motion_tup
#                     )
#                     voice_leading = voice_leader.get_next_voice_leading()
#                 except er_exceptions.NoMoreVoiceLeadingsError:
#                     voice_lead_error.total_failures += 1
#                     voice_lead_error.harmony_counter[
#                         (prev_harmony_i, new_harmony_i)
#                     ] += 1
#                     return False
#
#             if (
#                 rhythm_i >= vl_item.end_rhythm_i
#                 or new_attack_time >= er.total_len
#                 or prev_note_i >= vl_item.prev_end_rhythm_i
#             ):
#                 break
#
#         voice.append(new_notes)
#
#     if voice_lead_pattern_strictly(
#         er,
#         super_pattern,
#         voice_lead_error,
#         pattern_voice_leading_i=pattern_voice_leading_i + 1,
#     ):
#         return True
#
#     if er.allow_flexible_voice_leading and voice_lead_pattern_flexibly(
#         er,
#         super_pattern,
#         voice_lead_error,
#         pattern_voice_leading_i=pattern_voice_leading_i + 1,
#     ):
#         return True
#
#     for note in new_notes:
#         voice.remove_note(note.pitch, note.attack_time)
#
#     return False


def voice_lead_pattern_strictly(
    er, super_pattern, voice_lead_error, pattern_voice_leading_i=0
):
    voice_lead_error.status()

    try:
        vl_item = er.pattern_voice_leading_order[pattern_voice_leading_i]
    except IndexError:
        # if we reach the end of the list, then we've effected all the
        # voice-leadings.
        return True

    voice = super_pattern.voices[vl_item.voice_i]
    rhythm = er.rhythms[vl_item.voice_i]

    new_attack_time = vl_item.start_time

    new_notes = er_notes.Voice()
    success_rhythm_i = vl_item.start_rhythm_i

    harmony_start_rhythm_i = vl_item.prev_start_rhythm_i

    # In the event that the voice is empty, skip this loop.
    if voice:

        prev_attack_time = rhythm.get_attack_time_and_dur(
            vl_item.prev_start_rhythm_i
        )[0]

        break_out = False
        while True:
            # This loop updates the harmony

            new_harmony_i = super_pattern.get_harmony_i(new_attack_time)
            new_harmony_times = super_pattern.get_harmony_times(new_harmony_i)
            prev_harmony_i = super_pattern.get_harmony_i(prev_attack_time)
            prev_harmony_times = super_pattern.get_harmony_times(prev_harmony_i)
            voice_leader = er_voice_leadings.VoiceLeader(
                er, prev_harmony_i, new_harmony_i
            )
            voice_leading = voice_leader.get_next_voice_leading()
            prev_pc_scale = er.get(prev_harmony_i, "pc_scales")

            while True:
                rhythm_i = success_rhythm_i
                new_sub_notes = er_notes.Voice()
                first_note = True
                success = True

                for prev_note_i, prev_note in enumerate(voice):
                    # There must be a better way of locating where to start
                    #   than scanning linearly over the list. But in practice
                    #   scores seem to be short enough that this isn't a big
                    #   issue.
                    # if prev_note_i < vl_item.prev_start_rhythm_i:
                    if prev_note_i < harmony_start_rhythm_i:
                        continue
                    if prev_note_i >= vl_item.prev_end_rhythm_i:
                        break_out = True
                        break
                    prev_attack_time = prev_note.attack_time

                    if prev_attack_time < prev_harmony_times.start_time:
                        continue
                    if prev_attack_time >= prev_harmony_times.end_time:
                        harmony_start_rhythm_i = prev_note_i
                        break
                    new_attack_time, new_dur = rhythm.get_attack_time_and_dur(
                        rhythm_i
                    )
                    if new_attack_time < new_harmony_times.start_time:
                        continue
                    if new_attack_time >= new_harmony_times.end_time:
                        harmony_start_rhythm_i = prev_note_i
                        break
                    if rhythm_i >= vl_item.end_rhythm_i:
                        break_out = True
                        break

                    (
                        new_note,
                        voice_leading_motion_tup,
                    ) = er_apply_vl.apply_voice_leading(
                        er,
                        super_pattern,
                        prev_note,
                        first_note,
                        new_attack_time,
                        new_dur,
                        vl_item.voice_i,
                        new_harmony_i,
                        prev_harmony_i,
                        prev_pc_scale,
                        voice_leading,
                        new_sub_notes,
                        voice_lead_error,
                    )

                    if new_note:
                        new_sub_notes.add_note_object(new_note)
                        first_note = False
                        rhythm_i += 1
                    else:
                        success = False
                        break

                if success:
                    new_notes.append(new_sub_notes)
                    success_rhythm_i = rhythm_i
                    break

                try:
                    voice_leader.exclude_voice_leading_motion(
                        *voice_leading_motion_tup
                    )
                    voice_leading = voice_leader.get_next_voice_leading()
                except er_exceptions.NoMoreVoiceLeadingsError:
                    voice_lead_error.total_failures += 1
                    voice_lead_error.harmony_counter[
                        (prev_harmony_i, new_harmony_i)
                    ] += 1
                    return False

            if (
                break_out
                # I was doing the next check but I am guessing it is not
                #   necessary based on the fact that I don't check it anywhere
                #   else (e.g., in voice_lead_pattern_flexibly)
                or new_attack_time >= er.total_len
            ):
                break

        voice.append(new_notes)

    if voice_lead_pattern_strictly(
        er,
        super_pattern,
        voice_lead_error,
        pattern_voice_leading_i=pattern_voice_leading_i + 1,
    ):
        return True

    if er.allow_flexible_voice_leading and voice_lead_pattern_flexibly(
        er,
        super_pattern,
        voice_lead_error,
        pattern_voice_leading_i=pattern_voice_leading_i + 1,
    ):
        return True

    for note in new_notes:
        voice.remove_note(note.pitch, note.attack_time)

    return False
