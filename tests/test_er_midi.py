import itertools
import os
import sys
import traceback

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)
import src.er_choirs as er_choirs  # pylint: disable=wrong-import-position
import src.er_make as er_make  # pylint: disable=wrong-import-position
import src.er_midi as er_midi  # pylint: disable=wrong-import-position
import src.er_preprocess as er_preprocess  # pylint: disable=wrong-import-position


def assay_write_track_names(
    er,
    super_pattern,
):
    # This test seems to be incomplete!
    mf = er_midi.init_midi(er, super_pattern)
    er_midi.write_track_names(er, mf)
    try:
        for track in mf.tracks:
            assert track.name != "", 'track.name == ""'
    except:  # pylint: disable=bare-except
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(
            exc_type, exc_value, exc_traceback, file=sys.stdout
        )
        breakpoint()


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
        er = er_preprocess.preprocess_settings(base_settings | more_settings)
        super_pattern = er_make.make_super_pattern(er)
        er_make.complete_pattern(er, super_pattern)
        er_choirs.assign_choirs(er, super_pattern)
        assay_write_track_names(er, super_pattern)
        er_midi.write_er_midi(er, super_pattern, er.output_path, return_mf=True)


if __name__ == "__main__":
    test_er_midi()
