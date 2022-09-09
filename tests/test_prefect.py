import pytest
from prefect import flow, task
from pathlib import Path

from bikeshare.model.flow import preprocess_task

from prefect.testing.utilities import prefect_test_harness

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

# @pytest.mark.prefect
# def test_make_block(tmp_prefect_block, local_block_name, tmp_block_path):
#     basepath = tmp_block_path / local_block_name    
#     assert type(tmp_prefect_block) == \
#         type(flow_deploy.make_local_block(
#             name=local_block_name,
#             basepath=basepath,
#             overwrite=True,
#             ))

# @pytest.mark.prefect
@pytest.fixture(autouse=True, scope="session")
def prefect_test_fixture():
    with prefect_test_harness():
        yield

@task
def my_favorite_task():
    return 42

@flow
def my_favorite_flow():
    val = my_favorite_task()
    return val

    # def test_my_favorite_task():
    #     assert my_favorite_task.fn() == 42


@pytest.mark.prefect
class TestPrefect:
    """
    All prefect tests are grouped under this class
    """
    def test_my_favorite_flow(self):
        """
        Sample test. 
        
        self must be defined as one of the arg since it is constructed 
        within the class; self is passed regardless and so we must
        make room for it
        """
        # with prefect_test_harness():
        assert my_favorite_flow() == 42

    # def test_flow_local(tmp_path):
    #     data_path = '/home/kohada/to-bikes/data/test-2017.csv'
    #     dest_path = Path(tmp_path / 'output')
    #     flow.my_flow(
    #         data_path=data_path,
    #         dest_path=dest_path,
    #     )
    #     # pkl_list = Path(tmp_path).glob('*.pkl')
    #     checklist = [dest_path / 'train.pkl', dest_path / 'test.pkl']
    #     present = [f.exists() for f in checklist]
    #     assert all(present)  