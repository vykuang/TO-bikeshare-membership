"""
Prefect flow to batch analyze our web service model
"""
import json
import os
import pickle
from typing import Tuple

import pandas as pd
from evidently import ColumnMapping
from evidently.dashboard import Dashboard
from evidently.dashboard.tabs import ClassificationPerformanceTab, DataDriftTab
from evidently.model_profile import Profile
from evidently.model_profile.sections import (
    ClassificationPerformanceProfileSection,
    DataDriftProfileSection,
)
from prefect import flow, get_run_logger, task
from pymongo import MongoClient

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://127.0.0.1:27017")


@task
def upload_target(filename: str) -> None:
    """
    Not needed for to-bikeshare data
    """
    mongo_client = MongoClient(MONGODB_URI)
    db = mongo_client.get_database("prediction_service")
    collection = db.get_collection("data")
    with open(filename) as f_target:
        for line in f_target.readlines():
            row = line.split(",")
            collection.update_one({"id": row[0]}, {"$set": {"target": float(row[1])}})
    mongo_client.close()


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


@task
def load_reference_data(ref_file: str) -> pd.DataFrame:
    """
    Loads and preprocesses the raw reference csv for eval metrics
    Adds the prediction column as well
    """
    # read from local or s3
    reference_data = pd.read_csv(ref_file)

    # load model from local
    with open("model.pkl", "rb") as f_in:
        model = pickle.load(f_in)

    # Create features
    features = preprocess(reference_data)

    # include prediction
    features["prediction"] = model.predict(features.drop("target", axis=1))
    return features


@task
def fetch_data() -> pd.DataFrame:

    log = get_run_logger()

    mongo_client = MongoClient(MONGODB_URI)
    db = mongo_client.get_database("prediction_service")
    data = db.get_collection("data").find()
    df = pd.DataFrame(list(data))
    log.info(f"{len(df)} records loaded from mongo db")
    mongo_client.close()
    return df


@task
def run_evidently(ref_data: pd.DataFrame, data: pd.DataFrame) -> Tuple[dict, Dashboard]:
    num_features = [
        "trip_duration_seconds",
        "start_hour",
        "end_hour",
    ]
    ctg_features = [
        "from_station_id",
        "to_station_id",
        "day_of_week",
    ]
    profile = Profile(
        sections=[DataDriftProfileSection(), ClassificationPerformanceProfileSection()]
    )
    mapping = ColumnMapping(
        prediction="prediction",
        numerical_features=num_features,
        categorical_features=ctg_features,
        datetime_features=[],
    )
    profile.calculate(ref_data, data, mapping)

    dashboard = Dashboard(
        tabs=[DataDriftTab(), ClassificationPerformanceTab(verbose_level=0)]
    )
    dashboard.calculate(ref_data, data, mapping)
    return json.loads(profile.json()), dashboard


@task
def save_report(profile) -> None:
    mongo_client = MongoClient(MONGODB_URI)
    db = mongo_client.get_database("prediction_service")
    db.get_collection("report").insert_one(profile)
    mongo_client.close()


@task
def save_html_report(dashboard) -> None:
    dashboard.save("evidently_report_example.html")


@flow
def batch_analyze():
    # input data already contains target
    # upload_target("target.csv")
    ref_data = load_reference_data("s3://to-bikeshare-data/source/2017/q1.csv")
    data = fetch_data()
    profile, dashboard = run_evidently(ref_data, data)
    save_report(profile)
    save_html_report(dashboard)


if __name__ == "__main__":
    batch_analyze()
