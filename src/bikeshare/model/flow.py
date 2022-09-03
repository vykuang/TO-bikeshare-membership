from pathlib import Path

from prefect import flow, get_run_logger, task
from sklearn.model_selection import train_test_split

from .preprocess import dump_pickle, preprocess, read_df


@task
def read_data(path: str):
    return read_df(path)


@task
def prep(df_bikes):
    return preprocess(df_bikes)


@task
def dump_pickle_task(obj, filename):
    dump_pickle(obj, filename)


@flow
def my_flow(data_path: str, dest_path: Path):
    """Deployment flow for re-training the TO-bikeshare-classifier

    Taken from preprocess.run(), with prefect logger added
    """
    logger = get_run_logger()

    Path.mkdir(dest_path, exist_ok=True)
    logger.debug(f"absolute dest_path: {dest_path.resolve()}")

    logger.info(f"reading data from {data_path}")
    df = read_data(data_path)

    logger.info("prepping data")
    df_bikes = prep(df)
    logger.info(f"loaded {len(df_bikes)} rows of data")

    train, test = train_test_split(
        df_bikes,
        test_size=0.3,
        stratify=df_bikes["target"],
    )
    logger.info(f"Train size: {len(train)}\tTest size: {len(test)}")

    dump_pickle(train, Path(dest_path / "train.pkl"))
    dump_pickle(test, Path(dest_path / "test.pkl"))
    logger.info(f"Saved train.pkl and test.pkl in {dest_path}")


if __name__ == "__main__":
    # for testing
    my_flow(
        data_path="/home/kohada/to-bikes/data/bikeshare-2017-q1.csv",
        dest_path="/home/kohada/to-bikes/data/output/",
    )
