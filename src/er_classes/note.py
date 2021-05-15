# constants for writing notes
DEFAULT_VELOCITY = 96
DEFAULT_CHOIR = 0


class Note:
    """Stores a note.

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
