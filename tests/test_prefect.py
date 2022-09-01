import pytest

from bikeshare.model import flow_deploy


@pytest.mark.prefect
def test_flow_deploy(tmp_path):
    assert flow_deploy.build('local', str(tmp_path / 'prefect_block'))
