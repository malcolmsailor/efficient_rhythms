import copy
import operator

# constants for writing notes
DEFAULT_VELOCITY = 96
DEFAULT_CHOIR = 0


class Note:
    """Stores a note.

    For sorting, notes can be compared with the standard comparison operators
    like <, >=, etc. They are compared on the following attributes, in this
    order: attack_time, dur, pitch, finetune, velocity

    Attributes:
        pitch: an integer.
        attack_time: a fraction.
        dur: a fraction.
        velocity: an integer 0-127.
        choir: an integer.
        voice: an integer, or None. A place to store the voice that
            a note belongs to.
        finetune: a number, indicates arbitrary tuning in cents (i.e., 100ths
            of a semitone)
    """

    def __init__(
        self,
        pitch,
        attack_time,
        dur,
        velocity=DEFAULT_VELOCITY,
        choir=DEFAULT_CHOIR,
        voice=None,
        finetune=0,
    ):
        self.pitch = pitch
        self.attack_time = attack_time
        self.dur = dur
        self.velocity = velocity
        self.choir = choir
        self.voice = voice
        self.finetune = finetune
        self._spelling = None

    def __repr__(self):
        # not sure what my motivation for printing attack and dur as floats was
        out = (
            "<Note pitch={} attack={:f} dur={:f} vel={} choir={} "
            "voice={}>\n".format(
                self.pitch,
                float(self.attack_time),
                float(self.dur),
                self.velocity,
                self.choir,
                self.voice,
            )
        )
        return out

    @property
    def spelling(self):
        """Returns None if spelling has not been explicitly set first."""
        return self._spelling

    @spelling.setter
    def spelling(self, value):
        self._spelling = value

    def _comparison_sequence(self, other, op):
        def _compare_attr(attr):
            self_attr = getattr(self, attr)
            other_attr = getattr(other, attr)
            if self_attr == other_attr:
                return None
            return op(self_attr, other_attr)

        if not isinstance(other, Note):
            raise ValueError

        for attr in ("attack_time", "dur", "pitch", "finetune", "velocity"):
            result = _compare_attr(attr)
            if result is not None:
                return result
        if result is None and op in (operator.eq, operator.le, operator.ge):
            return True
        return False

    def copy(self):
        # note should not have any data that requires deep copy
        return copy.copy(self)

    def __lt__(self, other):
        return self._comparison_sequence(other, operator.lt)

    def __le__(self, other):
        return self._comparison_sequence(other, operator.le)

    def __eq__(self, other):
        return self._comparison_sequence(other, operator.eq)

    def __ne__(self, other):
        return self._comparison_sequence(other, operator.ne)

    def __ge__(self, other):
        return self._comparison_sequence(other, operator.ge)

    def __gt__(self, other):
        return self._comparison_sequence(other, operator.gt)

    def partial_equality(
        self,
        other,
        pitch=True,
        attack_time=True,
        dur=True,
        velocity=True,
        choir=True,
        voice=True,
        finetune=True,
    ):
        if pitch and not self.pitch == other.pitch:
            return False
        if attack_time and not self.attack_time == other.attack_time:
            return False
        if dur and not self.dur == other.dur:
            return False
        if velocity and not self.velocity == other.velocity:
            return False
        if choir and not self.choir == other.choir:
            return False
        if voice and not self.voice == other.voice:
            return False
        if finetune and not self.finetune == other.finetune:
            return False
        return True
