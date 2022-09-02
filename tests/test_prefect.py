import pytest


from bikeshare.model import flow_deploy


@pytest.mark.prefect
def test_flow_deploy(tmp_prefect_deploy, tmp_prefect_block):
    assert type(tmp_prefect_deploy) == \
        type(flow_deploy.build(
            storage=tmp_prefect_block,
            name='local',
            work_queue_name='test',))

@pytest.mark.prefect
def test_make_block(tmp_prefect_block, local_block_name, tmp_block_path):
    basepath = tmp_block_path / local_block_name    
    assert type(tmp_prefect_block) == \
        type(flow_deploy.make_local_block(
            name=local_block_name,
            basepath=basepath,
            overwrite=True,))

