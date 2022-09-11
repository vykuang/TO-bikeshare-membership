import pytest

from bikeshare.deploy.predict_service import predict

@pytest.mark.timeout(30)
@pytest.mark.deploy
def test_retrieve():
    model = predict.retrieve()
    assert True

