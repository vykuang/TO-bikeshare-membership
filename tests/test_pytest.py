import pytest

from bikeshare import foo
from bikeshare.model import preprocess
from bikeshare.orchestrate import flow


def test_always_passes():
    assert True


@pytest.mark.xfail(reason="because of the way it is")
def test_always_fails():
    assert False


def test_foo():
    assert foo.add_num(4) == 5
