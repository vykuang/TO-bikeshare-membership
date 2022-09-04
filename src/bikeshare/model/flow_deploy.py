#!usr/bin/env python

"""
To run:
cd ~/to-bikes
python -m src.bikeshare.model.flow_deploy -f s3
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Union

from dotenv import load_dotenv
from prefect.deployments import Deployment
from prefect.filesystems import S3, LocalFileSystem
from prefect.orion.schemas.schedules import CronSchedule

from .flow import to_bikes_flow

dotenv_path = Path(__file__).parent.resolve() / ".env"
load_dotenv(dotenv_path)
logging.debug(f"Loaded env vars from {dotenv_path}")

# outputs to CLI STDOUT
logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

S3_BLOCK_NAME = os.getenv("S3_BLOCK_NAME")
PREFECT_S3_BUCKET = os.getenv("PREFECT_S3_BUCKET")
PREFECT_WORK_QUEUE = os.getenv("PREFECT_WORK_QUEUE", "TO-bikes-clf")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "foo")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "bar")


def make_s3_block(overwrite: bool = False):
    logging.info(f"Making Prefect S3 block in {PREFECT_S3_BUCKET} bucket")
    s3_block = S3(
        bucket_path=PREFECT_S3_BUCKET,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )
    try:
        s3_block.save(S3_BLOCK_NAME, overwrite=overwrite)
    except ValueError:
        logging.warning("S3 block already exists")

    return S3.load(S3_BLOCK_NAME)


def make_local_block(
    name: str = "local",
    basepath: str = "./prefect_block",
    overwrite: bool = False,
):
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
    flow_params,
    storage: Union[S3, LocalFileSystem],
    deploy_name: str = "to_bikes_flow",
    work_queue_name: str = PREFECT_WORK_QUEUE,
    apply: bool = True,
):
    deployment = Deployment.build_from_flow(
        flow=to_bikes_flow,
        parameters=flow_params,
        name=deploy_name,
        version="1",
        tags=["demo"],
        schedule=CronSchedule(
            cron="0 0 1 * *",
            timezone="America/New_York",
        ),
        work_queue_name=work_queue_name,
        storage=storage,
        apply=apply,
    )
    return deployment


def deploy(
    filesystem: str,
    flow_params: Union[dict, None],
    deploy_name: str = "to-bikes-clf-train",
    local_block_path: str = "./prefect_block",
    overwrite: bool = False,
    apply: bool = True,
):
    # flow_params default
    if not flow_params:
        flow_params = {
            "data_path": "s3://to-bikeshare-data/source/2017/q1.csv",
            # "dest_path": "./output/",
            "num_trials": 10,
        }
    logging.info(f"Accepted flow_params: \n{flow_params}")

    if filesystem == "s3":
        storage = make_s3_block(overwrite=overwrite)
    elif filesystem == "local":
        storage = make_local_block(basepath=local_block_path)
    else:
        raise ValueError("`local` or `s3` for filesystem type")
    logging.info(f"Storage type: {type(storage)}")
    deployment = build(
        storage=storage,
        deploy_name=deploy_name,
        flow_params=flow_params,
        apply=apply,
    )
    logging.info(f"Deployment {deployment.name} uploaded.")
    return True


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--filesystem",
        "-f",
        type=str,
        default="local",
        choices=["local", "s3"],
        help="`local` or `s3` for prefect flow remote storage",
    )
    parser.add_argument(
        "--flow_params",
        "-p",
        default=None,
        type=json.loads,
        help="""flow_params to pass to my_flow, in '{"key": "value"}' format""",
    )
    args = parser.parse_args()
    deploy(filesystem=args.filesystem, flow_params=args.flow_params)
