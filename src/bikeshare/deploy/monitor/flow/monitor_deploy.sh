#! /usr/bin/env sh
prefect deployment build ./batch_monitor.py:batch_analyze \
	--name to-bikes-clf-monitor-s3 \
	--version v0 \
	--tag to-bikes \
	--work-queue TO-bikes-clf-monitor \
	--storage-block s3/to-bikes-flows \
	--cron "0 0 1 * *" \
	--output to-bikes-clf-monitor-s3-deployment.yaml \
	--path to-bikes-clf-monitor/
	
