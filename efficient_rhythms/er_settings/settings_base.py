import typing

from .. import er_constants
from .. import er_exceptions
from .. import er_misc_funcs
from .. import er_randomize
from .. import er_tuning
from .. import er_types


def _process_str(pitch_str):
    pitch_str = pitch_str.replace("#", "_SHARP")
    return eval(pitch_str, vars(er_constants))  # pylint: disable=eval-used


def replace_pitch_constants(pitch_material):
    if isinstance(pitch_material, str):
        return _process_str(pitch_material)
    if isinstance(pitch_material, typing.Sequence):
        return tuple(replace_pitch_constants(item) for item in pitch_material)
    return pitch_material


def temper_pitches(pitches, er):
    return er_tuning.temper_pitch_materials(
        pitches, er.tet, er.integers_in_12_tet
    )


def ensure_pitch_classes(pcs, er):
    if isinstance(pcs, typing.Sequence):
        return tuple(ensure_pitch_classes(pc, er) for pc in pcs)
    return pcs % er.tet


def get_base_type(field_type):
    # we want to strip "Optional" from types
    if typing.get_origin(field_type) is typing.Union:
        type_args = typing.get_args(field_type)
        if len(type_args) == 2 and type(None) in type_args:
            return type_args[0] if type_args[1] is type(None) else type_args[1]
    return field_type


class SettingsBase:
    _silent = _randomized = None
    # when creating a dataclass that derives from another class, we still need
    # to apply the @dataclass decorator. For that reason there doesn't seem to
    # be any purpose in applying it to SettingsBase.
    def __post_init__(self):
        self._set_seed()
        if self.randomized:
            self.randomize()
        self._process_fields()
        self._timeout_event = None

    def _set_seed(self):
        self.seed = er_misc_funcs.set_seed(
            self.seed, print_out=not self._silent
        )

    def check_time(self):
        if self._timeout_event is None:
            return
        if self._timeout_event.is_set():
            raise er_exceptions.ErTimeoutError

    def add_timeout_event(self, timeout_event):
        self._timeout_event = timeout_event

    def randomize(self):
        randomizer = er_randomize.ERRandomize(self)
        randomizer.apply(self)
        # we re-set the seed in the hopes that the music will be reproducible
        er_misc_funcs.set_seed(self.seed, print_out=False)

    @property
    def randomized(self):  # pylint: disable=missing-docstring
        return self._randomized

    # def _init_private_fields(self):
    #     for field_name, field_args in self._fields:
    #         if (
    #             field_name[:2] != "h_"
    #             or "postprocess" not in field_args.metadata
    #         ):
    #             continue
    #         postprocess = field_args.metadata["postprocess"]
    #         if "args" in field_args.metadata:
    #             args = [
    #                 getattr(self, attr_name)
    #                 for attr_name in field_args.metadata["args"]
    #             ]
    #         else:
    #             args = []
    #         setattr(self, field_name, postprocess(self, *args))

    def _process_fields(self):
        for field_name, field_args in self._fields:
            field_type = get_base_type(field_args.type)
            self._fill_none_or_falsy(field_name, field_args, field_type)
            self._process_per_voice_seqs(field_name, field_type)
            self._sort(field_name, field_type, field_args)
            self._process_pitch_materials(field_name, field_type)
            self._process_intervals(field_name, field_type)
            self._process_rhythm_materials(field_name, field_type)

    def _process_pitch_materials(self, field_name, field_type):
        if not er_types.has_pitches(field_type):
            return
        raw_val = getattr(self, field_name)
        new_val = replace_pitch_constants(raw_val)
        new_val = temper_pitches(new_val, self)
        if er_types.has_pitch_classes(field_type):
            new_val = ensure_pitch_classes(new_val, self)
        setattr(self, field_name, new_val)

    def _process_intervals(self, field_name, field_type):
        if not er_types.has_interval(field_type):
            return
        raw_val = getattr(self, field_name)
        new_val = replace_pitch_constants(raw_val)
        setattr(self, field_name, new_val)

    def _process_rhythm_materials(self, field_name, field_type):
        if not er_types.has_metron(field_type):
            return
        raw_val = getattr(self, field_name)
        if raw_val is None:
            return
        # TODO think about whether we really want to convert to fractions,
        #   or maybe some other type?
        #   Maybe it depends on cont_rhythms?
        new_val = er_misc_funcs.convert_to_fractions(raw_val)
        setattr(self, field_name, new_val)

    def _fill_none_or_falsy(self, field_name, field_args, field_type):
        raw_val = getattr(self, field_name)
        metadata = field_args.metadata
        if not raw_val and "if_falsy" in metadata:
            new_val = metadata["if_falsy"](self)
            setattr(self, field_name, new_val)
            return
        if raw_val is not None:
            return
        if "if_none" in metadata:
            new_val = metadata["if_none"](self)
            setattr(self, field_name, new_val)
        elif "from_if_none" in metadata:
            new_val = getattr(self, metadata["from_if_none"])
            setattr(self, field_name, new_val)
        elif hasattr(field_type, "fill_none"):
            new_val = field_type.fill_none(self)
            setattr(self, field_name, new_val)

    def _sort(self, field_name, field_type, field_args):
        if "sort" in field_args.metadata:
            sorted_ = field_type.sort(
                getattr(self, field_name), field_args.metadata["sort"]
            )
            setattr(self, field_name, sorted_)

    @property
    def _fields(self):
        return self.__dataclass_fields__.items()  # pylint: disable=no-member

    def _process_per_voice_seqs(self, field_name, field_type):
        raw_val = getattr(self, field_name)
        if not hasattr(field_type, "process"):
            return
        processed_val = field_type.process(raw_val, self)
        setattr(self, field_name, processed_val)
