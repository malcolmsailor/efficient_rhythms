import itertools

from efficient_rhythms import er_choirs
from efficient_rhythms import er_make
from efficient_rhythms import er_midi
from efficient_rhythms import er_settings
from efficient_rhythms import er_classes


def assay_write_track_names(
    er,
    super_pattern,
):
    # This test seems to be incomplete!
    mf = er_midi.init_midi(er, super_pattern)
    er_midi.write_track_names(er, mf)
    for track in mf.tracks:
        assert track.name != "", 'track.name == ""'


def test_voices_to_tracks():
    base_settings = {
        "randomly_distribute_between_choirs": False,
        "num_voices": 3,
    }
    er = er_settings.get_settings(base_settings)
    # voice, pitch, onset, dur
    notes = [
        (0, 60, 0, 1),
        (1, 65, 0, 1),
        (2, 67, 0, 1),
    ]
    score = er_classes.Score(num_voices=er.num_voices, tet=er.tet)
    for (v, p, a, d) in notes:
        score.add_note(v, p, a, d)
    er_choirs.assign_choirs(er, score)
    # note that by default reverse_tracks would be False, which would mean that
    # the choir assignments would be reversed (e.g., with three voices, track
    # 0 would become track 2). To avoid that hassle, we pass
    # reverse_tracks=False
    mf = er_midi.write_er_midi(
        er, score, "test_voices_to_tracks", reverse_tracks=False, return_mf=True
    )
    for track_i, track in enumerate(mf.tracks):
        for msg in track:
            if msg.type in ("note_on", "note_off", "program_change"):
                # the meta track is track 0, so we need to subtract 1
                #   to get the right element from er.choir_assignments
                assert msg.channel == er.choir_assignments[track_i - 1]


def test_er_midi():
    base_settings = {
        "output_path": "test_track_names.mid",
        "seed": 1,
        "pattern_len": 1,
        "num_harmonies": 1,
        "onset_density": 1 / 4,
        "length_choir_segments": 1 / 4,
        "randomly_distribute_between_choirs": True,
    }
    bools = True, False
    for voices_separate_tracks, choirs_separate_tracks in itertools.product(
        bools, bools
    ):
        more_settings = {
            "voices_separate_tracks": voices_separate_tracks,
            "choirs_separate_tracks": choirs_separate_tracks,
        }
        print(more_settings)
        # er = er_settings.get_settings(base_settings | more_settings)
        # | is only implemented in python 3.9
        merged_settings = base_settings.copy()
        for k, v in more_settings.items():
            merged_settings[k] = v
        er = er_settings.get_settings(merged_settings)
        super_pattern = er_make.make_super_pattern(er)
        er_make.complete_pattern(er, super_pattern)
        er_choirs.assign_choirs(er, super_pattern)
        assay_write_track_names(er, super_pattern)
        er_midi.write_er_midi(er, super_pattern, er.output_path, return_mf=True)


if __name__ == "__main__":
    test_voices_to_tracks()
    test_er_midi()
