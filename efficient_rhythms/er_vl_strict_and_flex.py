from . import er_exceptions
from . import er_classes
from . import er_voice_leadings

from . import er_apply_vl


def _get_htimes_end_i(rhythm, htimes, vl_item_end_i):
    # vl_item_end_i is needed as a backup in case htimes.end_time is None
    if htimes.end_time is not None:
        return rhythm.get_i_at_or_after(htimes.end_time)
    else:
        return vl_item_end_i


def flex_vl_loop(er, score, voice_lead_error, voice, vl_item):
    er.check_time()
    rhythm = er.rhythms[vl_item.voice_i]
    new_notes = er_classes.Voice()

    first_note = True
    new_note_i = vl_item.start_i
    prev_note_i = vl_item.prev_start_i

    # Dummy values so that harmony will update on first loop
    new_htimes_end_i = vl_item.start_i
    prev_htimes_end_i = vl_item.prev_start_i

    for prev_note_i, new_note_i in zip(
        range(vl_item.prev_start_i, vl_item.prev_end_i),
        range(vl_item.start_i, vl_item.end_i),
    ):
        prev_note = voice.get_notes_by_i(prev_note_i)[0]
        new_onset, new_dur = rhythm.get_onset_and_dur(new_note_i)

        # update new harmony if necessary
        if new_note_i == new_htimes_end_i:
            new_htimes = score.get_harmony_times_from_onset(new_onset)
            new_htimes_end_i = _get_htimes_end_i(
                rhythm, new_htimes, vl_item.end_i
            )
            update_voice_leadings = True

        # update prev harmony if necessary
        if prev_note_i == prev_htimes_end_i:
            prev_htimes = score.get_harmony_times_from_onset(prev_note.onset)
            prev_htimes_end_i = _get_htimes_end_i(
                rhythm, prev_htimes, vl_item.prev_end_i
            )
            update_voice_leadings = True

        if update_voice_leadings:
            voice_leader = er_voice_leadings.VoiceLeader(
                er, prev_htimes.i, new_htimes.i
            )
            voice_leading = voice_leader()
            prev_pc_scale = er.get(prev_htimes.i, "pc_scales")
            update_voice_leadings = False

        while True:
            new_note, vl_motion_tup = er_apply_vl.apply_voice_leading(
                er,
                score,
                prev_note,
                first_note,
                new_onset,
                new_dur,
                vl_item.voice_i,
                new_htimes.i,
                prev_htimes.i,
                prev_pc_scale,
                voice_leading,
                new_notes,
                voice_lead_error,
            )
            if new_note:
                new_notes.add_note(new_note)
                first_note = False
                break
            try:
                voice_leading = voice_leader(exclude_vl_tup=vl_motion_tup)
            except er_exceptions.NoMoreVoiceLeadingsError:
                voice_lead_error.total_failures += 1
                voice_lead_error.harmony_counter[
                    (prev_htimes.i, new_htimes.i)
                ] += 1
                return None

    for note in new_notes:
        voice.add_note(note)

    return new_notes


def voice_lead_pattern_flexibly(er, score, vl_error, pattern_vl_i=0):
    """This voice-leading algorithm will change voice-leading in
    the middle of a pattern if it runs into a problem.
    """

    vl_error.status()

    try:
        vl_item = er.pattern_vl_order[pattern_vl_i]
    except IndexError:
        # if we reach the end of the list, then we've effected all the
        # voice-leadings.
        return True

    voice = score.voices[vl_item.voice_i]
    new_notes = flex_vl_loop(er, score, vl_error, voice, vl_item)
    if new_notes is None:
        return False

    if er.allow_strict_voice_leading and voice_lead_pattern_strictly(
        er, score, vl_error, pattern_vl_i=pattern_vl_i + 1
    ):
        return True

    if voice_lead_pattern_flexibly(
        er, score, vl_error, pattern_vl_i=pattern_vl_i + 1
    ):
        return True

    for note in new_notes:
        voice.remove_note(note)

    return False


def strict_voice_leading_loop(er, score, voice_lead_error, voice, vl_item):
    er.check_time()
    rhythm = er.rhythms[vl_item.voice_i]
    new_notes = er_classes.Voice()

    new_onset = vl_item.first_onset
    new_note_i = vl_item.start_i
    prev_onset = vl_item.prev_first_onset
    prev_note_i = vl_item.prev_start_i

    new_htimes = score.get_harmony_times_from_onset(new_onset)
    new_htimes_end_i = _get_htimes_end_i(rhythm, new_htimes, vl_item.end_i)
    prev_htimes = score.get_harmony_times_from_onset(prev_onset)
    prev_htimes_end_i = _get_htimes_end_i(
        rhythm, prev_htimes, vl_item.prev_end_i
    )

    voice_leader = er_voice_leadings.VoiceLeader(
        er, prev_htimes.i, new_htimes.i
    )
    voice_leading = voice_leader()
    prev_pc_scale = er.get(prev_htimes.i, "pc_scales")

    while True:
        # This loop attempts to apply each voice leading in turn on the
        #   present harmony
        new_sub_notes = er_classes.Voice()
        first_note = True
        success = True
        prev_note_end_i = min(vl_item.prev_end_i, prev_htimes_end_i)
        for prev_note_j, new_note_j in zip(
            range(prev_note_i, prev_note_end_i),
            range(new_note_i, new_htimes_end_i),
        ):
            # This loop will only work if the voice is monophonic (because
            # it expects indices of onsets to be in one-to-one
            # correspondance with notes). Which it
            # should be. We could enforce this with a check but it seems
            # like that would create a lot of overhead.
            prev_note = voice.get_notes_by_i(prev_note_j)[0]
            new_onset, new_dur = rhythm.get_onset_and_dur(new_note_j)
            new_note, vl_motion_tup, = er_apply_vl.apply_voice_leading(
                er,
                score,
                prev_note,
                first_note,
                new_onset,
                new_dur,
                vl_item.voice_i,
                new_htimes.i,
                prev_htimes.i,
                prev_pc_scale,
                voice_leading,
                new_sub_notes,
                voice_lead_error,
            )
            if new_note:
                new_sub_notes.add_note(new_note)
                first_note = False
            else:
                success = False
                break

        if not success:
            try:
                voice_leading = voice_leader(exclude_vl_tup=vl_motion_tup)
            except er_exceptions.NoMoreVoiceLeadingsError:
                voice_lead_error.total_failures += 1
                voice_lead_error.harmony_counter[
                    (prev_htimes.i, new_htimes.i)
                ] += 1
                return None

        else:  # success == True
            new_notes.append(new_sub_notes)
            new_note_i = new_note_j + 1
            if new_note_i == vl_item.end_i:
                break
            prev_note_i = prev_note_j + 1
            prev_onset = voice.get_notes_by_i(prev_note_i)[0].onset
            new_onset, new_dur = rhythm.get_onset_and_dur(new_note_i)
            # update new harmony if necessary
            if new_note_i == new_htimes_end_i:
                new_htimes = score.get_harmony_times_from_onset(new_onset)
                new_htimes_end_i = _get_htimes_end_i(
                    rhythm, new_htimes, vl_item.end_i
                )

            # update prev harmony if necessary
            if prev_note_i == prev_htimes_end_i:
                prev_htimes = score.get_harmony_times_from_onset(prev_onset)
                prev_htimes_end_i = _get_htimes_end_i(
                    rhythm, prev_htimes, vl_item.prev_end_i
                )

            voice_leader = er_voice_leadings.VoiceLeader(
                er, prev_htimes.i, new_htimes.i
            )
            voice_leading = voice_leader()
            prev_pc_scale = er.get(prev_htimes.i, "pc_scales")

    voice.append(new_notes)
    return new_notes


def voice_lead_pattern_strictly(er, score, vl_error, pattern_vl_i=0):
    vl_error.status()

    try:
        vl_item = er.pattern_vl_order[pattern_vl_i]
    except IndexError:
        # if we reach the end of the list, then we've effected all the
        # voice-leadings.
        return True

    voice = score.voices[vl_item.voice_i]

    # I think I may be removing empty voices elsewhere in which case this
    #   check could be skipped
    # In the event that the voice is empty, skip loop.
    # Also skip loop if vl_item is empty. (We don't want to delete the vl_item
    # because we reuse them on re-generating the rhythm, after which the vl_item
    # may no longer be empty.)
    if voice and vl_item:
        new_notes = strict_voice_leading_loop(
            er, score, vl_error, voice, vl_item
        )
        if new_notes is None:
            return False

    if voice_lead_pattern_strictly(
        er, score, vl_error, pattern_vl_i=pattern_vl_i + 1
    ):
        return True

    if er.allow_flexible_voice_leading and voice_lead_pattern_flexibly(
        er, score, vl_error, pattern_vl_i=pattern_vl_i + 1
    ):
        return True

    for note in new_notes:
        voice.remove_note(note)

    return False
