import collections
import dataclasses
import numbers
import typing

import er_tuning


@dataclasses.dataclass
class MidiSettings:

    num_tracks: int = None  # Not to be set by user, will be overwritten later
    tet: int = 12
    time_sig: typing.Tuple[int, int] = None
    max_denominator: int = 8192
    num_channels_pitch_bend_loop: int = 9
    pitch_bend_time_prop: numbers.Number = 0.75

    def __post_init__(self):
        self.note_counter: collections.Counter()
        # If the file is in 12 tet and features no finetuning then these steps are
        # not necessary but for the moment it seems like more effort than it's
        # worth to check:
        self.pitch_bend_time_dict: {
            track_i: [0 for i in range(self.num_channels_pitch_bend_loop)]
            for track_i in range(self.num_tracks)
        }
        self.pitch_bend_tuple_dict: er_tuning.return_pitch_bend_tuple_dict(
            self.tet
        )

    def num_tracks_from(self, score):
        self.num_tracks = score.num_voices
