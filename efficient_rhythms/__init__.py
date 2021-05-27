import os

PACKAGE_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..")

from .er_preprocess import preprocess_settings
from .er_make import make_super_pattern
