import pytest
from prefect import flow, task
from pathlib import Path
from bikeshare.model import flow_deploy

from bikeshare.model import flow


# @pytest.mark.prefect
# def test_flow_deploy(tmp_prefect_deploy, tmp_prefect_block):
#     flow_params = {
#         'data_path': '/home/kohada/to-bikes/data/test-2017.csv',
#         'dest_path': './output/'
#         }
#     assert type(tmp_prefect_deploy) == \
#         type(flow_deploy.build(
#             flow_params=flow_params,
#             storage=tmp_prefect_block,
#             deploy_name='local',
#             work_queue_name='test',
#             ))

@pytest.mark.prefect
def test_make_block(tmp_prefect_block, local_block_name, tmp_block_path):
    basepath = tmp_block_path / local_block_name    
    assert type(tmp_prefect_block) == \
        type(flow_deploy.make_local_block(
            name=local_block_name,
            basepath=basepath,
            overwrite=True,
            ))

@pytest.mark.prefect
def test_flow_local(tmp_path):
    data_path = '/home/kohada/to-bikes/data/test-2017.csv'
    dest_path = Path(tmp_path / 'output')
    flow.my_flow(
        data_path=data_path,
        dest_path=dest_path,
    )
    # pkl_list = Path(tmp_path).glob('*.pkl')
    checklist = [dest_path / 'train.pkl', dest_path / 'test.pkl']
    present = [f.exists() for f in checklist]
    assert all(present)

@task
def my_favorite_task():
    return 42

@flow
def my_favorite_flow():
    val = my_favorite_task()
    return val

def test_my_favorite_task():
    assert my_favorite_task.fn() == 42