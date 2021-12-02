from efficient_rhythms import er_exceptions
from efficient_rhythms import er_settings
from efficient_rhythms import er_make_handler


def test_timeout():
    settingsdict = {
        "num_voices": 6,
        "num_harmonies": 2,
        "harmony_len": 100,
        "timeout": 0.2,
    }
    er = er_settings.get_settings(settingsdict)
    try:
        er_make_handler.make_super_pattern(er, debug=False)
    except er_exceptions.ErTimeoutError:
        pass
    else:
        raise AssertionError("There should have been a timeout")
    settingsdict = {
        "num_voices": 1,
        "num_harmonies": 2,
        "timeout": 10,
    }
    er = er_settings.get_settings(settingsdict)
    # We don't expect timeout
    er_make_handler.make_super_pattern(er, debug=False)


if __name__ == "__main__":
    test_timeout()
