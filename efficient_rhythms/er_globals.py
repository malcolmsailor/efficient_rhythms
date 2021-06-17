import numpy as np

RNG = np.random.default_rng()


def set_np_seed(seed):
    global RNG
    RNG = np.random.default_rng(seed=seed)
