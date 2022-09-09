import pytest

from bikeshare.deploy import predict

@pytest.mark.deploy
def test_retrieve():
    model = predict.retrieve()
    assert True

