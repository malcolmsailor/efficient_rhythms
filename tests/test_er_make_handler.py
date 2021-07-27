import efficient_rhythms.er_exceptions as er_exceptions
import efficient_rhythms.er_settings as er_settings
import efficient_rhythms.er_make_handler as er_make_handler


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
    except er_exceptions.TimeoutError:
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
