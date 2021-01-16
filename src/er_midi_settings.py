import collections
import dataclasses
import numbers
import os
import typing

import src.er_misc_funcs as er_misc_funcs
import src.er_tuning as er_tuning

# User probably won't need to access these settings
@dataclasses.dataclass
class MidiSettings:

    num_tracks: int = None  # Not to be set by user, will be overwritten later
    _output_path: str = None  # Not to be set by user, will be overwritten later
    _original_path: str = None  # Not to be set by user, will be overwritten later
    output_dir: str = None  #
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

    @property
    def original_path(self):
        return self._original_path

    @original_path.setter
    def original_path(self, original_path):
        self._original_path = original_path
        if self.output_dir is None:
            self.output_dir = os.path.dirname(original_path)

    @property
    def output_path(self):
        if self._output_path is None or os.path.exists(self._output_path):
            self._output_path = er_misc_funcs.get_changed_midi_path(
                os.path.join(
                    self.output_dir, (os.path.basename(self._original_path)),
                )
            )
        return self._output_path
