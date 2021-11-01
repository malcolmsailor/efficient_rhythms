import collections
import fractions
import inspect
import random

from .. import er_misc_funcs

from .changers import Changer, ChangeFuncError, Mediator


class Transformer(Changer):
    pretty_name = "Transformer"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def mark_note(self, note):
        """Marks notes that have been transformed by appending name of
        transformer to note.transformations_ list. If note has not been
        transformed, it will not have a note.transformations_ list and
        so accessing it will raise an AttributeError.

        This function should be called for each note by the change_func()
        of each transformer.
        """
        try:
            note.transformations_.append(self.pretty_name)
        except AttributeError:
            note.transformations_ = [
                self.pretty_name,
            ]


class ForcePitchTransformer(Transformer):
    pretty_name = "Force pitch transformer"

    def __init__(self, *args, force_pitches=(), **kwargs):
        super().__init__(*args, **kwargs)
        self.add_attribute(
            "force_pitches",
            force_pitches,
            "Pitches to force",
            int,
            attr_val_kwargs={"min_value": 1, "max_value": -1},
        )

    def change_func(  # pylint: disable=unused-argument
        self, voice, notes_to_change
    ):
        for note in notes_to_change:
            pitch_to_force = random.choice(
                self.force_pitches  # pylint: disable=no-member
            )
            note.pitch = pitch_to_force
            self.mark_note(note)

    def validate(self, *args):
        super().validate(*args)
        if not er_misc_funcs.no_empty_lists(
            self.force_pitches  # pylint: disable=no-member
        ):
            raise ChangeFuncError("'Pitches to force' contains an empty list.")


class ForcePitchClassesTransformer(Transformer):
    pretty_name = "Force pitch-classes transformer"

    def __init__(self, *args, force_pcs=(), **kwargs):
        super().__init__(*args, **kwargs)
        self.add_attribute(
            "force_pcs",
            force_pcs,
            "Pitch-classes to force",
            int,
            attr_val_kwargs={
                "min_value": 0,
                "max_value": 11,
                "iter_of_iters": True,
            },
        )

    def change_func(self, voice, notes_to_change):
        voice_i = voice.voice_i
        pcs = self.get(voice_i, "force_pcs")
        for note in notes_to_change:
            sign = random.choice([1, -1])
            adjust = 0
            pitch = note.pitch
            while True:
                if (pitch + adjust * sign) % voice.tet in pcs:
                    note.pitch = pitch + adjust * sign
                    break
                if (pitch + adjust * sign * -1) % voice.tet in pcs:
                    note.pitch = pitch + adjust * sign * -1
                    break
                adjust += 1
            self.mark_note(note)

    def validate(self, *args):
        super().validate(*args)
        if not er_misc_funcs.no_empty_lists(
            self.force_pcs  # pylint: disable=no-member
        ):
            raise ChangeFuncError(
                "'Pitch-classes to force' contains an empty list."
            )


class VelocityTransformer(Transformer, Mediator):
    pretty_name = "Velocity transformer"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_attribute(
            "trans_type",
            "Scale",
            "Velocity transform type",
            str,
            attr_val_kwargs={"possible_values": ["Scale", "Fix"]},
            unique=True,
        )
        self.add_attribute(
            "scale_by",
            1,
            "Scale factor",
            float,
            attr_val_kwargs={"min_value": 0, "max_value": -1},
            display_if={"trans_type": "Scale"},
        )
        self.add_attribute(
            "fix_to",
            64,
            "Fix velocity to",
            int,
            attr_val_kwargs={"min_value": 0, "max_value": 127},
            display_if={"trans_type": "Fix"},
        )
        self.add_attribute(
            "humanize",
            6,
            "Humanize +/-",
            int,
            attr_val_kwargs={"min_value": 0, "max_value": 127},
        )

    def change_func(self, voice, notes_to_change):
        voice_i = voice.voice_i
        if self.trans_type == "Scale":  # pylint: disable=no-member
            scale_by, humanize = self.get(voice_i, "scale_by", "humanize")
            for note in notes_to_change:
                unmediated_vel = round(
                    max(0, min(127, note.velocity * scale_by))
                )
                mediated_vel = round(
                    self.mediate(
                        voice_i, unmediated_vel, note.velocity, note.onset
                    )
                )
                note.velocity = random.randrange(
                    max(mediated_vel - humanize, 0),
                    min(mediated_vel + humanize + 1, 128),
                )
                self.mark_note(note)

        elif self.trans_type == "Fix":  # pylint: disable=no-member
            fix_to, humanize = self.get(voice_i, "fix_to", "humanize")
            for note in notes_to_change:
                unmediated_vel = round(max(0, min(127, fix_to)))
                mediated_vel = round(
                    self.mediate(
                        voice_i, unmediated_vel, note.velocity, note.onset
                    )
                )
                try:
                    note.velocity = random.randrange(
                        max(mediated_vel - humanize, 0),
                        min(mediated_vel + humanize + 1, 128),
                    )
                except ValueError:
                    breakpoint()
                self.mark_note(note)


class ChangeDurationsTransformer(Transformer, Mediator):
    pretty_name = "Change durations transformer"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_attribute(
            "trans_type",
            "Scale",
            "Change durations type",
            str,
            attr_val_kwargs={"possible_values": ["Scale", "By_fixed_amount"]},
            unique=True,
        )
        self.add_attribute(
            "scale_by",
            1,
            "Scale factor",
            float,
            attr_val_kwargs={"min_value": 0, "max_value": -1},
            display_if={"trans_type": "Scale"},
        )
        self.add_attribute(
            "fix_amount",
            1,
            "Fixed amount",
            fractions.Fraction,
            attr_val_kwargs={"min_value": -4192, "max_value": -1},
            display_if={"trans_type": "By_fixed_amount"},
        )
        self.add_attribute(
            "min_dur",
            0,
            "Minimum dur",
            fractions.Fraction,
            attr_val_kwargs={"min_value": 0, "max_value": -1},
        )
        self.add_attribute(
            "min_dur_treatment",
            "Enforce_min_dur",
            "Treatment of notes below minumum dur",
            str,
            attr_val_kwargs={"possible_values": ["Enforce_min_dur", "Delete"]},
            unique=True,
        )

    def change_func(self, voice, notes_to_change):
        voice_i = voice.voice_i
        if self.trans_type == "Scale":  # pylint: disable=no-member
            scale_by = self.get(voice_i, "scale_by")
        elif self.trans_type == "By_fixed_amount":  # pylint: disable=no-member
            fix_amount = self.get(voice_i, "self.fix_amount")
        min_dur = self.get(voice_i, "min_dur")
        for note in notes_to_change:
            try:
                unmediated_dur = note.dur * scale_by
            except NameError:
                unmediated_dur = note.dur + fix_amount
            note.dur = fractions.Fraction(
                self.mediate(voice_i, unmediated_dur, note.dur, note.onset)
            ).limit_denominator(2048)
            if (
                note.dur < min_dur
                and self.min_dur_treatment  # pylint: disable=no-member
                == "Enforce_min_dur"
            ):
                note.dur = min_dur
            elif note.dur < min_dur or note.dur <= 0:
                try:
                    notes_to_remove.append(note)
                except NameError:
                    notes_to_remove = [
                        note,
                    ]
            self.mark_note(note)

        if (
            self.min_dur_treatment  # pylint: disable=no-member
            == "Enforce_min_dur"
        ):
            return

        for note in notes_to_remove:
            voice.remove_note(note)


class RandomOctaveTransformer(Transformer):
    pretty_name = "Random octave transformer"

    def __init__(self, *args, ranges=0, avoid_orig_oct=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_attribute(
            "ranges",
            ranges,
            "Voice ranges",
            int,
            attr_val_kwargs={
                "min_value": 0,
                "max_value": -1,
                "tuple_of": 2,
                "iter_of_iters": True,
            },
            attr_hint="If voice ranges are 0, they are taken from Voice "
            "objects if possible",
        )
        self.add_attribute(
            "avoid_orig_oct",
            avoid_orig_oct,
            "Avoid original octave if possible",
            bool,
            unique=True,
        )

    def change_func(self, voice, notes_to_change):
        voice_i = voice.voice_i
        voice_range = self.get(voice_i, "ranges")
        if isinstance(voice_range, tuple):
            voice_range = sorted(voice_range)
        if not voice_range:
            voice_range = voice.range
            if voice_range is None:
                print(
                    f"        No voice_range specified in voice {voice_i}, "
                    "defaulting to (36, 84)"
                )
                voice_range = (36, 84)
        low, high = voice_range
        for note in notes_to_change:
            choices = []
            new_pitch = note.pitch % voice.tet
            while new_pitch <= high:
                if new_pitch >= low:
                    choices.append(new_pitch)
                new_pitch += voice.tet
            if (
                self.avoid_orig_oct  # pylint: disable=no-member
                and note.pitch in choices
                and len(choices) > 1
            ):
                choices.remove(note.pitch)
            new_pitch = random.choice(choices)
            note.pitch = new_pitch
            self.mark_note(note)


class TransposeTransformer(Transformer):
    pretty_name = "Transpose transformer"

    def __init__(self, *args, transpose=0, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_attribute(
            "transpose",
            transpose,
            "Interval of transposition",
            int,
            attr_val_kwargs={
                "min_value": self.tet * -6,
                "max_value": self.tet * 6,
            },
        )
        self.add_attribute("preserve", False, "Preserve original note", bool)
        self.add_attribute(
            "trans_type",
            "Standard",
            "Transposition type",
            str,
            attr_val_kwargs={
                "possible_values": ["Standard", "Cumulative", "Random"]
            },
            unique=True,
        )
        self.add_attribute(
            "bound",
            0,
            "Cumulative bound",
            int,
            attr_val_kwargs={"min_value": 0, "max_value": self.tet * 6},
            attr_hint="After the cumulative transposition reaches the bound "
            "(inclusive; either up or down), it will be shifted an octave "
            "up/down",
            display_if={"trans_type": "Cumulative"},
        )
        self.add_attribute(
            "seg_dur",
            4,
            "Transposition segment duration",
            fractions.Fraction,
            attr_val_kwargs={"min_value": 0, "max_value": -1},
            attr_hint="If non-zero, then transposition segment number of "
            "notes is ignored",
            display_if={"trans_type": ("Cumulative", "Random")},
        )
        self.add_attribute(
            "seg_card",
            0,
            "Transposition segment number of notes",
            int,
            attr_val_kwargs={"min_value": 1, "max_value": -1},
            display_if={"trans_type": ("Cumulative", "Random")},
        )
        self._count_dict = collections.Counter()

    def standard(self, voice, notes_to_change):
        voice_i = voice.voice_i
        transpose, preserve = self.get(voice_i, "transpose", "preserve")
        for note in notes_to_change:
            if preserve:
                note_copy = note.copy()
                note_copy.pitch += transpose
                voice.add_note(note_copy)
                self.mark_note(note_copy)
                self.mark_note(note)
            else:
                note.pitch += transpose
                self.mark_note(note)

    def get_seg_i(self, voice_i, note):
        seg_dur, seg_card = self.get(voice_i, "seg_dur", "seg_card")
        if seg_dur:
            seg_i = int(note.onset // seg_dur)
        else:
            seg_i = self._count_dict[voice_i] // seg_card
            self._count_dict[voice_i] += 1
        return seg_i

    def cumulative(self, voice, notes_to_change):
        voice_i = voice.voice_i
        transpose, bound, preserve = self.get(
            voice_i, "transpose", "bound", "preserve"
        )

        for note in notes_to_change:
            seg_i = self.get_seg_i(voice_i, note)
            cum_trans = transpose * seg_i
            if bound:
                if cum_trans > 0:
                    while cum_trans > bound:
                        cum_trans -= voice.tet
                elif cum_trans < 0:
                    while cum_trans < -bound:
                        cum_trans += voice.tet
            # note.pitch += cum_trans
            if preserve:
                note_copy = note.copy()
                note_copy.pitch += cum_trans
                voice.add_note(note_copy)
                self.mark_note(note_copy)
                self.mark_note(note)
            else:
                note.pitch += cum_trans
                self.mark_note(note)

    def build_rand_trans(self):
        self.rand_trans = []  # pylint: disable=attribute-defined-outside-init
        length = (
            1
            if not self.by_voice  # pylint: disable=no-member
            else self.num_voices
        )
        for voice_i in range(length):
            self.rand_trans.append([])
            if (
                self.by_voice  # pylint: disable=no-member
                and voice_i not in self.voices  # pylint: disable=no-member
            ):
                continue
            transpose, seg_dur = self.get(voice_i, "transpose", "seg_dur")
            if seg_dur:
                time = 0
                while time < self.total_len:
                    self.rand_trans[-1].append(
                        random.randrange(-transpose, transpose + 1)
                    )
                    time += seg_dur
            else:
                # Thus function doesn't have access to how many
                # segments there will actually be, but we can assume
                # that no one will notice a repeating pattern of 1024!
                seg_i = 0
                while seg_i < 1024:
                    self.rand_trans[-1].append(
                        random.randrange(-transpose, transpose + 1)
                    )
                    seg_i += 1

    def random(self, voice, notes_to_change):
        try:
            self.rand_trans
        except AttributeError:
            self.build_rand_trans()
        voice_i = voice.voice_i
        rand_trans = self.rand_trans[voice_i % len(self.rand_trans)]
        preserve = self.get(voice_i, "preserve")
        for note in notes_to_change:
            seg_i = self.get_seg_i(voice_i, note)
            transpose = rand_trans[seg_i % len(rand_trans)]
            if preserve:
                note_copy = note.copy()
                note_copy.pitch += transpose
                voice.add_note(note_copy)
                self.mark_note(note_copy)
                # QUESTION should the original note be marked in this case?
                self.mark_note(note)
            else:
                note.pitch += transpose
                self.mark_note(note)

    def change_func(self, voice, notes_to_change):
        if self.trans_type == "Standard":  # pylint: disable=no-member
            self.standard(voice, notes_to_change)
        elif self.trans_type == "Cumulative":  # pylint: disable=no-member
            self.cumulative(voice, notes_to_change)
        elif self.trans_type == "Random":  # pylint: disable=no-member
            self.random(voice, notes_to_change)
        else:
            raise ChangeFuncError(
                "Unknown or non-implemented transposition type."
            )


class ChannelTransformer(Transformer):
    pretty_name = "Channel transformer"

    def __init__(self, *args, dest_channels=(), **kwargs):
        super().__init__(*args, **kwargs)
        self.add_attribute(
            "dest_channels",
            dest_channels,
            "Destination channels",
            int,
            attr_val_kwargs={
                "min_value": 0,
                "max_value": 15,
                "iter_of_iters": True,
            },
        )

    def change_func(self, voice, notes_to_change):
        voice_i = voice.voice_i
        dest_channels = self.get(voice_i, "dest_channels")
        for note in notes_to_change:
            note.choir = random.choice(dest_channels)
            self.mark_note(note)

    def validate(self, *args):
        super().validate(*args)
        if not er_misc_funcs.no_empty_lists(
            self.dest_channels  # pylint: disable=no-member
        ):
            raise ChangeFuncError(
                "'Destination channels' contains an empty list."
            )


class ChannelExchangerTransformer(Transformer):
    pretty_name = "Channel exchanger transformer"

    def __init__(self, *args, channel_pairs=(), **kwargs):
        super().__init__(*args, **kwargs)
        self.add_attribute(
            "channel_pairs",
            channel_pairs,
            "Channel source/destination pairs",
            int,
            attr_val_kwargs={"min_value": 0, "max_value": 15, "tuple_of": -2},
        )

    def change_func(  # pylint: disable=unused-argument
        self, voice, notes_to_change
    ):
        try:
            source_channels, dest_channels = zip(
                *self.channel_pairs  # pylint: disable=no-member
            )
        except ValueError as exc:
            raise ChangeFuncError(
                "Invalid value for channel source/destination pairs... "
                "perhaps they are empty?"
            ) from exc
        # voice_i = voice.voice_i
        for note in notes_to_change:
            try:
                i = source_channels.index(note.choir)
            except ValueError:
                continue
            note.choir = dest_channels[i]
            self.mark_note(note)


# # LONGTERM implement
# class ShepherdTransformer(Transformer):
#     pretty_name = "Shepherd tone transformer"

#     def __init__(self, *args, prob_curve="NullProbCurve", **kwargs):
#         super().__init__(
# *args, prob_curve=prob_curve, **kwargs
#         )
#         self.tet = score.tet
#         self.add_attribute(
#             "pitch_center",
#             5 * score.tet,
#             "Pitch center",
#             int,
#             attr_val_kwargs={"min_value": 0, "max_value": 10 * score.tet},
#         )
#         self.add_attribute(
#             "flat_peak",
#             score.tet,
#             "Size of flat peak in semitones",
#             int,
#             attr_val_kwargs={"min_value": 1, "max_value": 10 * score.tet},
#         )
#         self.add_attribute(
#             "num_octaves",
#             6,
#             "Number of octaves",
#             int,
#             attr_val_kwargs={"min_value": 0, "max_value": -1},
#         )
#         self.add_attribute(
#             "shape",
#             "quadratic",
#             "Velocity curve shape",
#             str,
#             attr_val_kwargs={"possible_values": ["quadratic", "linear"]},
#             unique=True,
#         )
#         # self.add_attribute(
#         #     "new_tracks",
#         #     True,
#         #     "Add new tracks for doubled notes",
#         #     bool,
#         #     unique=True,
#         # ) # LONGTERM
#         self.require_score = True
#         self.vel_func = self.bottom_pitch = self.top_pitch = None
#         self.bottom_flat_peak = self.top_flat_peak = None

#     def validate(self, *args):
#         super().validate(*args)

#         def _get_bottom(pitch_center, num_octaves):
#             return max(math.floor(pitch_center - num_octaves * self.tet / 2), 0)

#         def _get_top(pitch_center, num_octaves):
#             return min(
#                 math.ceil(pitch_center + num_octaves * self.tet / 2),
#                 math.floor(self.tet * 127 / 12),
#             )

#         self.bottom_pitch = []
#         self.top_pitch = []
#         self.bottom_flat_peak = []
#         self.top_flat_peak = []
#         for i in range(
#             max(
#                 len(self.pitch_center),  # pylint: disable=no-member
#                 len(self.num_octaves),  # pylint: disable=no-member
#             ),
#         ):
#             pitch_center, num_octaves, flat_peak = self.get(
#                 i, "pitch_center", "num_octaves", "flat_peak"
#             )
#             self.bottom_pitch.append(_get_bottom(pitch_center, num_octaves))
#             self.top_pitch.append(_get_top(pitch_center, num_octaves))
#             self.bottom_flat_peak.append(
#                 pitch_center - math.ceil(flat_peak / 2)
#             )
#             self.top_flat_peak.append(pitch_center + math.floor(flat_peak / 2))
#         if self.shape == "quadratic":  # pylint: disable=no-member
#             self.vel_func = prob_curves.quadratic
#         elif self.shape == "linear":  # pylint: disable=no-member
#             self.vel_func = prob_curves.linear

#     def get_vel(self, pitch, orig_vel, voice_i):
#         (
#             bottom_flat_peak,
#             top_flat_peak,
#             flat_peak,
#             num_octaves,
#             bottom_pitch,
#             top_pitch,
#         ) = self.get(
#             voice_i,
#             "bottom_flat_peak",
#             "top_flat_peak",
#             "flat_peak",
#             "num_octaves",
#             "bottom_pitch",
#             "top_pitch",
#         )
#         if pitch < bottom_flat_peak:
#             return round(
#                 orig_vel
#                 * self.vel_func(
#                     pitch - bottom_pitch,
#                     0,
#                     1,
#                     (num_octaves * self.tet - math.ceil(flat_peak / 2)) / 2,
#                 )
#             )
#         if pitch > top_flat_peak:
#             return round(
#                 orig_vel
#                 * self.vel_func(
#                     top_pitch - pitch,
#                     0,
#                     1,
#                     (num_octaves * self.tet - math.floor(flat_peak / 2)) / 2,
#                 )
#             )
#         return orig_vel

#     def change_func(self, score, voice_i, notes_to_change):
#         voice = score.voices[voice_i]
#         bottom_pitch, top_pitch = self.get(voice_i, "bottom_pitch", "top_pitch")
#         if self.new_tracks:  # pylint: disable=no-member
#             # LONGTERM
#             pass
#         for note in notes_to_change:
#             self.mark_note(note)
#             pc_int = (note.pitch - bottom_pitch) % self.tet
#             pitch = bottom_pitch + pc_int
#             while pitch <= top_pitch:
#                 new_vel = self.get_vel(pitch, note.velocity, voice_i)
#                 if pitch == note.pitch:
#                     note.velocity = new_vel
#                 elif self.new_tracks:  # pylint: disable=no-member
#                     # LONGTERM
#                     pass
#                 else:
#                     new_note = note.copy()
#                     new_note.velocity = new_vel
#                     new_note.pitch = pitch
#                     voice.add_note(new_note)
#                 # ...
#                 pitch += self.tet


class TrackExchangerTransformer(Transformer):
    pretty_name = "Track exchanger transformer"

    def __init__(self, *args, track_pairs=(), **kwargs):
        super().__init__(*args, **kwargs)
        self.add_attribute(
            "track_pairs",
            track_pairs,
            "Track source/destination pairs",
            int,
            attr_val_kwargs={"min_value": 0, "max_value": -1, "tuple_of": -2},
        )
        self.require_score = True

    def change_func(self, score, voice_i, notes_to_change):
        try:
            source_tracks, dest_tracks = zip(
                *self.track_pairs  # pylint: disable=no-member
            )
        except ValueError as exc:
            raise ChangeFuncError(
                "Invalid value for track source/destination pairs... "
                "perhaps they are empty?"
            ) from exc
        try:
            i = source_tracks.index(voice_i)
        except ValueError:
            return
        dest_voice_i = dest_tracks[i]
        while dest_voice_i > score.num_voices - 1:
            score.add_voice()

        for note in notes_to_change:
            score.voices[dest_voice_i].add_note(note)
            score.voices[voice_i].remove_note(note)
            self.mark_note(note)
        # score.voices[dest_voice_i].update_sort()


class InvertTransformer(Transformer):
    pretty_name = "Melodic inversion transformer"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_attribute(
            "axis",
            5 * self.tet,
            "Axis of inversion",
            int,
            attr_val_kwargs={"max_value": -1},
            attr_hint=("TET", self.tet),
        )

    def change_func(self, voice, notes_to_change):
        voice_i = voice.voice_i
        axis = self.get(voice_i, "axis")
        notes_to_remove = []
        for note in notes_to_change:
            new_pitch = 2 * axis - note.pitch
            if 0 < new_pitch <= self.tet * 10:
                note.pitch = new_pitch
                self.mark_note(note)
            else:
                notes_to_remove.append(note)

        if notes_to_remove:
            print("\n")
            print(
                "        Removing {} out of range notes in voice {}".format(
                    len(notes_to_remove), voice_i
                )
            )
            for note in notes_to_remove:
                voice.remove_note(note)


class TrackRandomizerTransformer(Transformer):
    pretty_name = "Track randomizer transformer"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_attribute(
            "dest_voices",
            self.voices,  # pylint: disable=no-member
            "Destination voices",
            int,
            attr_val_kwargs={"min_value": 0, "max_value": -1},
        )
        self.require_score = True

    def validate(self, score, *args):  # pylint: disable=arguments-differ
        super().validate(*args)
        for i, dest_voice_i in enumerate(
            self.dest_voices  # pylint: disable=no-member
        ):
            if dest_voice_i > score.num_voices - 1:
                self.dest_voices[  # pylint: disable=no-member
                    i
                ] = score.num_voices
                score.add_voice()

    def change_func(self, score, voice_i, notes_to_change):
        for note in notes_to_change:
            dest_voice_i = random.choice(
                self.dest_voices  # pylint: disable=no-member
            )
            score.voices[dest_voice_i].add_note(note)
            score.voices[voice_i].remove_note(note)
            self.mark_note(note)

        # for dest_voice_i in self.dest_voices:  # pylint: disable=no-member
        #     score.voices[dest_voice_i].update_sort()
        # score.voices[voice_i].update_sort()


class TrackDoublerTransformer(Transformer):
    pretty_name = "Track doubler transformer"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_attribute(
            "doubling_intervals",
            0,
            "Doubled voices transpositions",
            int,
            attr_val_kwargs={"min_value": -128, "max_value": 128},
        )
        self.require_score = True

    def change_func(  # pylint: disable=unused-argument
        self, score, voice_i, notes_to_change
    ):
        for note in notes_to_change:
            self.mark_note(note)
        for (
            doubling_interval
        ) in self.doubling_intervals:  # pylint: disable=no-member
            dest_track = score.add_voice()
            dest_track.append(notes_to_change)
            dest_track.transpose(doubling_interval)


class SubdivideTransformer(Transformer):
    pretty_name = "Subdivide transformer"
    description = (
        pretty_name + " subdivides pitches into notes of specified value"
    )

    def __init__(self, *args, subdivision=0.25, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_attribute(
            "subdivision",
            subdivision,
            "Subdivision value",
            fractions.Fraction,
            attr_val_kwargs={"min_value": 1 / 128, "max_value": 4},
        )

    def change_func(self, voice, notes_to_change):
        # add comma support
        voice_i = voice.voice_i
        subdivision = self.get(voice_i, "subdivision")
        for note in notes_to_change:
            time = note.onset
            end = time + note.dur
            to_add = min((subdivision, note.dur))
            note.dur = to_add
            time += to_add
            while time < end:
                new_note = note.copy()
                new_note.onset = time
                to_add = min((subdivision, end - time))
                if to_add == 0:
                    break
                new_note.dur = to_add
                voice.add_note(new_note)
                time += to_add
            self.mark_note(note)
        # voice.update_sort()


# LONGTERM finish implementing or delete
# class LoopTransformer(Transformer):
#     pretty_name = "Loop transformer"

#     def __init__(self, *args, loop_len=4, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.add_attribute(
#             "loop_len",
#             loop_len,
#             "Loop length",
#             fractions.Fraction,
#             attr_val_kwargs={"min_value": 0, "max_value": -1},
#         )

#     def change_func(self, voice, notes_to_change):
#         voice_i = voice.voice_i
#         loop_len = self.get(voice_i, "loop_len")
#         # What to do if the onset % loop_len does not
#         # occur in the initial loop?
#         # And what about note attributes other than pitch?
#         # (duration, choir, ...)
#         for note in notes_to_change:
#             time = note.onset
#             ref_time = time % loop_len
#             # For now, I just take the first note, arbitrarily,
#             # at the earlier time
#             try:
#                 ref_note = voice[ref_time][0]
#             except KeyError:
#                 continue
#             note.pitch = ref_note.pitch
#             self.mark_note(note)

TRANSFORMERS = tuple(
    name
    for name, cls in locals().items()
    if inspect.isclass(cls)
    and issubclass(cls, Transformer)
    and cls not in (Transformer,)
)
