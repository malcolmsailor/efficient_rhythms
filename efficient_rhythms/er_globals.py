import os

import numpy as np

# TODO document DEBUG
try:
    DEBUG = os.environ["EFFICIENT_RHYTHMS_DEBUG"]
except KeyError:
    DEBUG = False


RNG = np.random.default_rng()


def set_np_seed(seed):
    global RNG
    RNG = np.random.default_rng(seed=seed)
