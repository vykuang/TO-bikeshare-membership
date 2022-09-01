import pytest

from bikeshare import foo
from bikeshare.model import preprocess


def test_always_passes():
    assert True

@pytest.mark.xfail(reason="because of the way it is")
def test_always_fails():
    assert False
