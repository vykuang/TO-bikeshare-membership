import os
import sys

from prefect.deployments import Deployment
from prefect.filesystems import S3, LocalFileSystem
from prefect.orion.schemas.schedules import CronSchedule

from .flow import flow

S3_BLOCK_NAME = os.getenv("S3_BLOCK_NAME")
PREFECT_S3_BUCKET = os.getenv('PREFECT_S3_BUCKET')
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID', 'foo')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY', 'bar')

def make_s3_block():
    s3_block = S3(
        bucket_path=PREFECT_S3_BUCKET,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )
    try:
        s3_block.save(S3_BLOCK_NAME, overwrite=False)
    except ValueError:
        print("S3 block already exists")

    return S3.load(S3_BLOCK_NAME)

def make_local_block(name: str = "local", basepath: str = "./prefect_block"):
    local_block = LocalFileSystem(
        name=name,
        basepath=basepath,
    )
    try:     
        local_block.save(name)
    except ValueError:
        print("Local block already exists")

    return LocalFileSystem.load(name)

def build(filesystem: str, path: str):
    if filesystem == 's3':
        storage = make_s3_block(S3_BLOCK_NAME, path)
    elif filesystem == 'local':
        storage = make_local_block(basepath=path)
    else:
        raise ValueError("`local` or `s3` for filesystem type")

    deployment = Deployment.build_from_flow(
        flow=flow,
        name="preprocess",
        version="1",
        tags=["demo"],
        schedule=CronSchedule(
            cron="0 0 1 * *",
            timezone="America/New_York",
        ),
        work_queue_name='to-bikes',
        storage=storage,
    )

    deployment.apply()
    return True

if __name__ == '__main__':
    filesystem = sys.argv[0]
    path = sys.argv[1]
    build(filesystem, path)