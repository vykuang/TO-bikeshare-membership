import pytest
import subprocess

from prefect.filesystems import LocalFileSystem 
from prefect.deployments import Deployment

from bikeshare.model import flow_deploy


@pytest.fixture(scope="session")
def local_block_name():
    # alphanumeric and dashes only, no underscore
    return "local-test"

@pytest.fixture(scope="session")
def tmp_block_path(tmp_path_factory):
    return tmp_path_factory.mktemp("blocks")

@pytest.fixture(scope="session")
def tmp_prefect_block(tmp_block_path, local_block_name):
    test_name = 'test1'
    test_path = tmp_block_path / test_name
    test_block = LocalFileSystem(
        name=test_name, 
        basepath=test_path,
        )
    test_block.save(name=test_name, overwrite=True)
    test_block = LocalFileSystem.load(name=test_name)
    yield test_block

    # must resort to CLI to programmatically delete the blocks.
    subprocess.run(
        ["prefect", "block", "delete", f"local-file-system/{test_name}"],
        check=True, text=True,
    )
    # subprocess.run(["prefect block delete", f"local-file-system/{test_name}"])
    subprocess.run(
        ["prefect", "block", "delete", f"local-file-system/{local_block_name}"],
        check=True, text=True,
    )

@pytest.fixture(scope="session")
def tmp_prefect_deploy(tmp_prefect_block):
    yield Deployment.build_from_flow(
        flow=flow_deploy.my_flow,
        name='test2',
        work_queue_name='test2',
        storage=tmp_prefect_block,
    )
    