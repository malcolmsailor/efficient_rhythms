import sys
import threading

sys.stdout = open("/dev/null", "w")
import pygame  # pylint: disable=wrong-import-position

sys.stdout.close()
sys.stdout = sys.__stdout__


import src.er_midi as er_midi  # pylint: disable=wrong-import-position

SOUND_FONT = "/Users/Malcolm/Music/SoundFonts/GeneralUser GS 1.471/GeneralUser_GS_v1.471.sf2"


def init_and_return_midi_player(shell=False):
    """Selects the midi player.

    If shell is false, plays midi to virtual midi port for use with a DAW such
    as Logic.

    Formerly, if shell was True, the midiplayer would be set to fluidsynth
    if tet != 12, since I found it gave somewhat better results with unusual
    temperaments. For now, this has been de-implemented.

    Returns name of midi player.
    """
    # LONGTERM allow user to choose midiplayer?
    # LONGTERM implement fluidsynth or other?
    if shell:
        # if tet != 12:
        #     return "fluidsynth"
        pygame.mixer.init()
        return "pygame"
    # TODO debug, add python-rtmidi to requirements
    return "self"


def playback_midi(midi_player, breaker, midi_path):
    """Plays a midi file.
    """
    if midi_player == "pygame":
        pygame.mixer.music.load(midi_path)
        pygame.mixer.music.play()
    # elif midi_player == "fluidsynth":
    #     subprocess.run(["fluidsynth", SOUND_FONT, midi_path], check=False)
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
