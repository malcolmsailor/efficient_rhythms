import os
import sys
import traceback

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

import efficient_rhythms.er_settings as er_settings  # pylint: disable=wrong-import-position


def test_categories():
    cats = er_settings.CATEGORIES
    try:
        for f, a in er_settings.ERSettings.__dataclass_fields__.items():
            c = a.metadata["category"]
            assert c in cats
    except:  # pylint: disable=bare-except

        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(
            exc_type, exc_value, exc_traceback, file=sys.stdout
        )
        breakpoint()


if __name__ == "__main__":
    test_categories()
