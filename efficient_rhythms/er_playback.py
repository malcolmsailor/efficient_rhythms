import os
import subprocess
import sys
import threading

with open("/dev/null", "w") as sys.stdout:
    import pygame  # pylint: disable=wrong-import-position

sys.stdout = sys.__stdout__

from . import er_midi  # pylint: disable=wrong-import-position


def init_and_return_midi_player(shell=False):
    """Selects the midi player.

    If shell is false, plays midi to virtual midi port for use with a DAW such
    as Logic.

    Formerly, if shell was True, the midiplayer would be set to fluidsynth
    if tet != 12, since I found it gave somewhat better results with unusual
    temperaments. For now, this has been de-implemented.

    Returns name of midi player.
    """
    if shell:
        # If EFFRHY_MIDI_PLAYER environment variable is defined, we understand
        #   it to be an executable we will call to playback midi files
        if "EFFRHY_MIDI_PLAYER" in os.environ:
            print(
                f"Using `{os.environ['EFFRHY_MIDI_PLAYER']}` for midi playback"
            )
            return "environment"
        pygame.mixer.init()
        print("Using pygame for midi playback")
        return "pygame"
    print("Using python-rtmidi for midi playback")
    return "self"


def playback_midi(midi_player, breaker, midi_path):
    """Plays a midi file."""
    if midi_player == "environment":
        midi_exec = os.environ["EFFRHY_MIDI_PLAYER"]
        command = midi_exec + " '" + midi_path + "'"
        print(f"\nRunning `{command}`")
        subprocess.run(command, shell=True, check=True)
    if midi_player == "pygame":
        pygame.mixer.music.load(midi_path)
        pygame.mixer.music.play()
    elif midi_player == "self":
        playback_thread = threading.Thread(
            target=er_midi.playback,
            args=[midi_path, breaker],
            kwargs={"multi_output": False},
        )
        playback_thread.start()


def stop_playback_midi(midi_player, breaker):
    if midi_player == "pygame":
        pygame.mixer.music.stop()
    elif midi_player == "self":
        breaker.break_ = True
        breaker.reset()
