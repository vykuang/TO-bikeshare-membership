"""
Retrieves and runs the latest version of the registered model
"""
import logging
import os
import sys
from datetime import datetime

import mlflow.pyfunc
import pandas as pd
from flask import Flask, jsonify, request
from mlflow.tracking import MlflowClient
from pymongo import MongoClient

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://127.0.0.1:27017")
mongo_client = MongoClient(MONGODB_URI)
db = mongo_client.get_database("prediction_service")
collection = db.get_collection("data")
logging.info("MongoDB connection established")


def preprocess_json(ride: dict) -> dict:
    """Preprocess the json input as dict"""
    logging.info("Preprocessing request")

    features = {}
    date_fmt = """%d/%m/%Y %H:%M"""
    dt_start = datetime.strptime(ride["trip_start_time"], date_fmt)
    dt_end = datetime.strptime(ride["trip_stop_time"], date_fmt)
    features["day_of_week"] = dt_start.weekday()
    features["start_hour"] = dt_start.hour
    features["end_hour"] = dt_end.hour
    features["target"] = ride["user_type"] == "Member"
    features["from_station_id"] = ride["from_station_id"]
    features["to_station_id"] = ride["to_station_id"]
    features["trip_duration_seconds"] = ride["trip_duration_seconds"]

    logging.debug(f"Num features returned: {len(features)}")
    return features


def json_to_df(ride: dict) -> pd.DataFrame:
    # appending dict to row allows pd.DataFrame.from_dict(orient='columns')
    rows = []
    rows.append(ride)
    # I should .set_index('trip_id'), but the trained model pipeline left it in
    # and so I need to here as well, lest ValueError Missing column be raised
    df_bike = pd.DataFrame.from_dict(rows, orient="columns")
    return df_bike


def preprocess(df_bikes: pd.DataFrame) -> pd.DataFrame:
    """Preprocesses the bikeshare data

    Converts the datetimes from str obj to datetime objects, and extracts
    the time of day to convert into hour floats

    This step is prior to feeding the arrays into the pipeline.
    """
    df_bikes["dt_start"] = pd.to_datetime(
        df_bikes["trip_start_time"],
        infer_datetime_format=True,
    )
    df_bikes["dt_end"] = pd.to_datetime(
        df_bikes["trip_stop_time"],
        infer_datetime_format=True,
    )
    # get day of week
    df_bikes["day_of_week"] = df_bikes.apply(
        lambda x: x["dt_start"].day_of_week, axis=1
    )
    # get hours
    df_bikes["start_hour"] = df_bikes.apply(
        lambda x: x["dt_start"].hour + x["dt_start"].minute / 60,
        axis=1,
    )
    df_bikes["end_hour"] = df_bikes.apply(
        lambda x: x["dt_end"].hour + x["dt_end"].minute / 60,
        axis=1,
    )
    df_bikes["target"] = df_bikes["user_type"].apply(lambda type: type == "Member")
    drops = [
        "trip_id",
        "trip_start_time",
        "trip_stop_time",
        "from_station_name",
        "to_station_name",
        "dt_start",
        "dt_end",
        "user_type",
    ]
    df_bikes = df_bikes.drop(drops, axis=1)
    return df_bikes


def retrieve() -> mlflow.pyfunc.PyFuncModel:
    """Retrieves and returns the latest version of the registered model"""
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    logging.debug(__name__)
    # defaults to ./mlruns if empty
    MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "")
    MLFLOW_REGISTERED_MODEL = os.getenv("MLFLOW_REGISTERED_MODEL", "TO-bikeshare-clf")

    client = MlflowClient(tracking_uri=MLFLOW_TRACKING_URI)
    # search string requires quotation marks around everything
    # only one search expression in 1.26
    mv_search = client.search_model_versions(f"name='{MLFLOW_REGISTERED_MODEL}'")
    logging.info("MLflow client created")

    for mv in mv_search:
        # pprint(dict(mv), indent=4)
        logging.info(
            f"version: {mv.version}\nStage: {mv.current_stage}\nSource: {mv.source}"
        )

    model_uris = [mv.source for mv in mv_search if mv.current_stage == "Production"]
    logging.info(model_uris)

    # alternatively model_uri could also be direct path to s3 bucket:
    # s3://{MLFLOW_ARTIFACT_STORE}/<exp_id>/<run_id>/artifacts/models
    # the models:/model_name/Production uri is only useable if MLflow server is up
    model = mlflow.pyfunc.load_model(
        # model_uri=f'models:/{MLFLOW_REGISTERED_MODEL}/Production'
        model_uri=model_uris[0]
    )
    return model


def predict(model: mlflow.pyfunc.PyFuncModel, features: pd.DataFrame) -> bool:
    """Given model and bikeshare trip data, return the predicted membership,
    as well as the associated probability
    """
    pred = model.predict(features)
    return bool(pred)


def save_to_db(result: dict) -> None:
    """Save prediction metadata to a DB for batch monitoring"""
    collection.insert_one(result)


def send_to_evidently(result: dict) -> None:
    """Send online prediction metadata to Evidently for realtime monitoring"""

    pass


# retrieve model only if first run?
AWS_PROFILE = os.getenv("AWS_PROFILE", "default")
logging.info(f"AWS_PROFILE set to: {AWS_PROFILE}")
model = retrieve()
logging.info("Model retrieved from artifact store")

app = Flask("bikeshare-membership-prediction")


@app.route("/predict", methods=["PUT"])
def predict_endpoint():
    """Joining the above funcs into one invocation triggered
    by an HTTP POST request
    POST because client needs to provide the required features
    for web service to make the prediction
    """
    # from the POST request
    ride = request.get_json()
    logging.info("Received PUT request")

    df_bike = json_to_df(ride)
    logging.info("Converted json to dataframe")

    features = preprocess(df_bike)
    logging.info("Preprocessed input data")

    # retrieve only on server startup, not every time a request is made
    # to minimize load on S3 and reduce response time
    # model = retrieve()

    # model is global var.
    # casting as python native bool allows serialization (to json)
    pred = predict(model, features)
    result = {
        "predicted_membership": pred,
        "input_data": ride,
        # need custom pyfunc wrapper to include predict_proba
        # "probability": proba,
        # without .to_json(), jsonify will raise non serializable error
        "model_meta": model.metadata.to_json(),
    }
    logging.info("Returning result")

    save_to_db(result.copy())
    send_to_evidently(result.copy())

    return jsonify(result)


if __name__ == "__main__":
    app.run(
        debug=True,
        host="0.0.0.0",
        port=9393,
    )
