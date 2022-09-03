import argparse
from pathlib import Path

import boto3

client = boto3.client("s3")


def upload(data, bucket: str, key: str):
    put_response = client.put_object(
        Body=data,
        Bucket=bucket,
        Key=key,
    )
    return put_response


def retrieve(bucket: str, key: str):
    get_response = client.get_object(
        Bucket=bucket,
        Key=key,
    )
    obj = get_response["Body"]
    return obj


def _run(data_path, bucket, key):
    pass


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data_path",
        type=Path,
        default="../data/output",
        help="the location where the processed TO bikeshare data was saved.",
    )
    parser.add_argument(
        "--bucket",
        type=str,
        default="to-bikeshare-data",
        help="the number of parameter evaluations for the optimizer to explore.",
    )
    args = parser.parse_args()

    _run(args.data_path, args.bucket)
