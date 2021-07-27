"""Provides tuning and spelling functions for efficient_rhythms2.py."""

ALPHABET = "fcgdaeb"

# for EastWest, SIZE_OF_SEMITONE should be 4096
# for Vienna, SIZE_OF_SEMITONE should be 8192

SIZE_OF_SEMITONE = 4096


def finetune_pitch_bend_tuple(
    pitch_bend_tuple, fine_tune, size_of_semitone=SIZE_OF_SEMITONE
):
    new_midi_num = pitch_bend_tuple[0]
    new_pitch_bend = round(
        pitch_bend_tuple[1] + fine_tune / 100 * size_of_semitone
    )
    while abs(new_pitch_bend) > size_of_semitone / 2:
        if new_pitch_bend > 0:
            new_midi_num += 1
            new_pitch_bend = new_pitch_bend - size_of_semitone
        else:
            new_midi_num -= 1
            new_pitch_bend = new_pitch_bend + size_of_semitone

    return new_midi_num, new_pitch_bend


def twelve_tet_midi_num_to_pitch_bend_tuple(
    midi_num, size_of_semitone=SIZE_OF_SEMITONE
):

    closest_whole_number = round(midi_num)
    pitch_bend = int((midi_num - closest_whole_number) * size_of_semitone)

    # I don't know if the next lines are really necessary
    while abs(
        midi_num - closest_whole_number - (pitch_bend + 1) / size_of_semitone
    ) < abs(midi_num - closest_whole_number - (pitch_bend) / size_of_semitone):
        pitch_bend += 1
    while abs(
        midi_num - closest_whole_number - (pitch_bend - 1) / size_of_semitone
    ) < abs(midi_num - closest_whole_number - (pitch_bend) / size_of_semitone):
        pitch_bend -= 1

    return (closest_whole_number, pitch_bend)


def return_pitch_bend_tuple_dict(
    tet, origin=0, size_of_semitone=SIZE_OF_SEMITONE
):
    """Returns a dictionary of form
            (pitch_number: (12-tet midinum, pitch_bend))

    Keyword args:
        - origin: the 12 - tet pitch class from which the relevant pitches
            will be calculated. (Should probably always be 0 (C).)
    """

    def _12_tet_pitch_classes(tet, origin=0):
        # origin = 0 builds scale from C as starting PC.
        step_size = 12 / tet
        pitch_classes = [(i * step_size) + origin for i in range(tet)]
        return pitch_classes

    def _12_tet_midi_nums(tet, origin=0):
        pitch_classes = _12_tet_pitch_classes(tet, origin % 12)
        pitches = []
        for octave in range(11):
            pitches += [
                pitch_class + (octave * 12) for pitch_class in pitch_classes
            ]
        return pitches

    twelve_tet_midi_nums = _12_tet_midi_nums(tet, origin)

    pitch_bend_tuple_dict = {}
    for pitch in range(tet * 11):
        pitch_bend_tuple_dict[pitch] = twelve_tet_midi_num_to_pitch_bend_tuple(
            twelve_tet_midi_nums[pitch], size_of_semitone=size_of_semitone
        )

    return pitch_bend_tuple_dict


def approximate_just_interval(rational, tet):
    """Approximates given rational in given equal temperament.
    """

    if rational < 0:
        sign = -1
        rational = -rational
    else:
        sign = 1
    if rational < 1:
        lower_power_of_two = 0
        while 2 ** lower_power_of_two > rational:
            lower_power_of_two -= 1
        upper_power_of_two = lower_power_of_two + 1

    else:
        upper_power_of_two = 0
        while 2 ** upper_power_of_two < rational:
            upper_power_of_two += 1
        lower_power_of_two = upper_power_of_two - 1

    lower_power = lower_power_of_two * tet
    upper_power = upper_power_of_two * tet

    comma = 2 ** (1 / (tet * 2))

    while True:

        if upper_power - lower_power == 1:
            upper_interval = 2 ** (upper_power / tet)
            if (
                max(rational, upper_interval) / min(rational, upper_interval)
            ) < comma:
                return sign * upper_power
            return sign * lower_power

        middle = (upper_power + lower_power) // 2
        middle_interval = 2 ** (middle / tet)
        if (
            max(rational, middle_interval) / min(rational, middle_interval)
        ) < comma:
            return sign * middle

        if rational > middle_interval:
            lower_power = middle
        else:
            upper_power = middle


def approximate_12_tet_pitch(pitch, tet):
    """Approximates a 12-tet pitch in the specified temperament.
    """
    octave = pitch // 12
    pc = pitch % 12
    new_p = octave * tet + round((pc / 12) * tet)
    return new_p


def temper_pitch_materials(item, tet, integers_in_12_tet=False):
    # None values are passed through as is
    if item is None:
        return None
    try:
        iter(item)
        iterable = True
    except TypeError:
        iterable = False
    if iterable:
        out = []
        for sub_item in item:
            sub_item = temper_pitch_materials(
                sub_item, tet, integers_in_12_tet=integers_in_12_tet
            )
            out.append(sub_item)
        return out

    if isinstance(item, int):
        if integers_in_12_tet:
            pitch = approximate_12_tet_pitch(item, tet)
        else:
            pitch = item
        return pitch

    new_pitch = approximate_just_interval(item, tet=tet)
    return new_pitch


def temper_pitch_materials_in_place(item, tet, integers_in_12_tet=False):
    try:
        iter(item)
        iterable = True
    except TypeError:
        iterable = False
    if iterable:
        if not isinstance(item, list):
            raise TypeError(
                "All iterables passed to "
                "temper_pitch_materials_in_place must be lists."
            )
        copy_of_item = item.copy()
        item.clear()
        for sub_item in copy_of_item:
            sub_item = temper_pitch_materials(
                sub_item, tet, integers_in_12_tet=integers_in_12_tet
            )
            item.append(sub_item)
        return None

    if isinstance(item, int):
        if integers_in_12_tet:
            pitch = approximate_12_tet_pitch(item, tet)
        else:
            pitch = item
        return pitch

    new_pitch = approximate_just_interval(item, tet=tet)
    return new_pitch
