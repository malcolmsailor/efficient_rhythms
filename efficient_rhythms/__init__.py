import os

# PACKAGE_DIR needs to be defined before the below imports
PACKAGE_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..")

from .er_constant_groups import (  # pylint: disable=wrong-import-position
    CONSTANT_GROUPS,
    CONSTANTS_BY_NAME,
)
from .er_exceptions import (  # pylint: disable=wrong-import-position
    ErSettingsError,
    ErMakeError,
    ErTimeoutError,
)

from .er_make_handler import (  # pylint: disable=wrong-import-position
    make_super_pattern,
)
from .er_settings import (  # pylint: disable=wrong-import-position
    ERSettings,
    CATEGORIES,
    get_settings,
)
from .er_midi import write_er_midi  # pylint: disable=wrong-import-position
