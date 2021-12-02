import pytest

from efficient_rhythms import er_misc_funcs


@pytest.fixture
def set_seed():
    er_misc_funcs.set_seed(0, print_out=False)
