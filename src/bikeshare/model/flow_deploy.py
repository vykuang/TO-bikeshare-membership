import os
import logging
from typing import Union

from prefect.deployments import Deployment
from prefect.filesystems import S3, LocalFileSystem
from prefect.orion.schemas.schedules import CronSchedule

from .flow import my_flow

S3_BLOCK_NAME = os.getenv("S3_BLOCK_NAME")
PREFECT_S3_BUCKET = os.getenv("PREFECT_S3_BUCKET")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "foo")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "bar")


def make_s3_block(overwrite: bool = False):
    s3_block = S3(
        bucket_path=PREFECT_S3_BUCKET,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )
    try:
        s3_block.save(S3_BLOCK_NAME, overwrite=overwrite)
    except ValueError:
        print("S3 block already exists")

    return S3.load(S3_BLOCK_NAME)


def make_local_block(
    name: str = "local", 
    basepath: str = "./prefect_block", 
    overwrite: bool = False):
    local_block = LocalFileSystem(
        name=name,
        basepath=basepath,
    )
    try:
        local_block.save(name, overwrite=overwrite)
    except ValueError:
        logging.warning("Local block already exists")

    return LocalFileSystem.load(name)

def build(
    storage: Union[S3, LocalFileSystem],
    name: str = 'my_flow', 
    work_queue_name: str = 'to-bikes',
    ):
    deployment = Deployment.build_from_flow(
        flow=my_flow,
        name=name,
        version="1",
        tags=["demo"],
        schedule=CronSchedule(
            cron="0 0 1 * *",
            timezone="America/New_York",
        ),
        work_queue_name=work_queue_name,
        storage=storage,
    )
    return deployment

def deploy(
    filesystem: str, 
    name: str = 'to-bikes-clf-train',
    path: str = './prefect_block', 
    overwrite: bool = False,
    ):
    
    if filesystem == "s3":
        storage = make_s3_block(overwrite=overwrite)
    elif filesystem == "local":
        storage = make_local_block(basepath=path)
        
    else:
        raise ValueError("`local` or `s3` for filesystem type")
    logging.info(type(storage))
    deployment = build(
        storage, 
        name=name,
        )

    deployment.apply()
    return True
