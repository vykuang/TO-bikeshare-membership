#! /usr/bin/env sh
prefect deployment build ./flow.py:to_bikes_flow \
	--name to-bikes-clf-train-s3 \
	--version v0 \
	--tag to-bikes \
	--work-queue TO-bikes-clf \
	--storage-block s3/to-bikes-flows \
	--cron "0 0 1 * *" \
	--output to-bikes-clf-train-s3-deployment.yaml \
	--path to-bikes-clf-train/
	
