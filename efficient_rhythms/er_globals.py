import os

import numpy as np

GITHUB_URL = "https://github.com/malcolmsailor/efficient_rhythms"

try:
    DEBUG = os.environ["EFFICIENT_RHYTHMS_DEBUG"]
except KeyError:
    DEBUG = False


RNG = np.random.default_rng()


def set_np_seed(seed):
    global RNG  # pylint: disable=global-statement
    RNG = np.random.default_rng(seed=seed)
