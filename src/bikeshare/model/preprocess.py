import argparse
import pickle
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split


def read_df(path: str):
    # can accept local and S3 filepath
    df = pd.read_csv(path)
    return df


def dump_pickle(obj, filename):
    with open(filename, "wb") as f_out:
        pickle.dump(obj, f_out)


def preprocess(df_bikes: pd.DataFrame):
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


def run(raw_data_path: str, dest_path: str):
    Path.mkdir(dest_path, exist_ok=True)
    df = read_df(raw_data_path)
    df_bikes = preprocess(df)
    train, test = train_test_split(
        df_bikes,
        test_size=0.3,
        stratify=df_bikes["target"],
    )

    dump_pickle(train, Path(dest_path / "train.pkl"))
    dump_pickle(test, Path(dest_path / "test.pkl"))


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--raw_data_path",
        type=Path,
        help="the location where the raw NYC taxi trip data was saved",
    )
    parser.add_argument(
        "--dest_path",
        type=Path,
        help="the location where the resulting files will be saved.",
    )
    args = parser.parse_args()

    run(args.raw_data_path, args.dest_path)
