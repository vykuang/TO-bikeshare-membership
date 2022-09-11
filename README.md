# TO Bikeshare Membership

## Problem Statement

End-to-end ML deployment of a model predicting whether a trip record belongs to a member or a casual rider.

Bikeshare ridership data - given these features:

* ride start datetime
* duration
* start station id
* to-station id

Can we predict whether the user is a member (annual pass) or casual (short term pass)? Is this an unbalanced dataset? Are there far more members than casual trips logged?

## Architecture

[Insert architecture diagram here]

* `scikit-learn` classifiers train on source data
* `MLFlow` tracks experiment results
* `Prefect` orchestrates the training pipeline; Prefect Cloud free tier is used as the orchestration server, and a dockerized agent executes the deployed flows
* `AWS S3` stores the source data, MLflow model artifacts, and orchestration backend database
* `AWS EC2` instance hosts the remote MLflow tracking server and dockerized prefect agent
* `AWS RDS` postgres instance hosts the remote MLflow backend store; contains the run metrics and metadata for all experiments from the tracking server

## Running this thing

### Set up

1. Use the `sample-bikeshare.csv` as our source data.
2. Set up MLflow
	* Tracking server can be local or remote server
	* Backend store can be local or remote database
	* Artifact store can be local filesystem or remote bucket
3. Set up Prefect
	* Scheduler can be local, remote, or Prefect Cloud (hosted by Prefect)
	* storage can be local or remote bucket; this is where Prefect stores the deployment flow codes to be run by the agent
	* Agent can be local instance or remote, as long as they have access to storage and prefect scheduling server
4. (Optional) Set up AWS
	* S3 for raw data storage, MLflow artifact store, and Prefect deployment code storage
	* RDS for MLflow backend store, and potentially prefect if running a remote instance not hosted by Prefect Cloud
	* EC2 to run MLflow server, web service docker, and optionally prefect server.
	* Note that MLflow also has options for third-party hosted servers with free tier usage options, e.g. Neptune.

### environment variables

These are the environment variables required by prefect deployment flows, prefect agent, and the ML deployment server

```
# MLflow
MLFLOW_TRACKING_URI=
MLFLOW_EXP_NAME='TO-bikeshare-classifier'
MLFLOW_REGISTERED_MODEL='TO-bikeshare-clf'

# profile to access MLflow remote artifact bucket
AWS_PROFILE=mlflow-storage
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=

# Prefect
PREFECT_API_URL=https://api.prefect.cloud/api/accounts/.../
PREFECT_API_KEY=pnu_...
PREFECT_S3_BUCKET=
PREFECT_WORK_QUEUE=TO-bikes-clf
S3_BLOCK_NAME='to-bikes-flows'

# profile to access Prefect S3 storage
AWS_PROFILE=prefect-storage
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
```
	
To reproduce the project, the cloud resources are not required; every component of the project can be run locally. Both MLflow and Prefect have the option to host local servers, and the backend store database can point to a lightweight SQLite `.db` file. Simply change the environment variables so that they point to a valid local resource.



## Modelling


## Experiment Tracking

## Orchestration

## Deployment

## using the service

Once set up, the deployment container will expose an URL endpoint for users to `PUT` a predict request. `PUT` was selected over `POST` since no new resource is being created, and user should receive the same result each time they request with the same input data.

Current implementation can accept one trip data per `PUT` request. The accompanying JSON keys should match the columns of the training data:

```json
input_dict = {
    "trip_id": 712382,
    "trip_start_time": "1/1/2017 0:00",
    "trip_stop_time": "1/1/2017 0:03",
    "trip_duration_seconds": 223,
    "from_station_id": 7051,
    "from_station_name": "Wellesley St E / Yonge St Green P",
    "to_station_id": 7089,
    "to_station_name": "Church St  / Wood St",
    "user_type": "Member",
}
```

Requester should receive a `json` containing the prediction and metadata about the model that made the prediction

## Future Development

* Handling datasets from different years, not just 2017, taking into account the different column names and data fields
* Adding a dummy classifier to serve as baseline comparison. I.e. If target is 95% positive, the dummy classifier should predict positive 95% of the time. Will our trained classifier perform better?
* Adding seasonality and year as features
* Complete script to include fetching data from TO open data as part of the pipeline
    * prefect-agent assumes that all source data has been neatly stored on `to-bikeshare-data` bucket in `/source/<year>/<quarter>.csv` format
    * `fetch` should pull from TO open data and push to cloud bucket in that format.
* Add multiple model types in the hyperopt search space; currently using only random forest
* When loading model via MLflow's artifact store, the default model only has `.predict()`. [According to this issues page](https://github.com/mlflow/mlflow/issues/694), a custom wrapper is required if we want `.predict_proba()` as provided by the original sklearn model.

