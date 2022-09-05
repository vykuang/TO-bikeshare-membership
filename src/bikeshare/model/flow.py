from prefect import flow, get_run_logger, task
from sklearn.model_selection import train_test_split

from .preprocess import dump_pickle, preprocess, read_df
from .registry import register_model
from .trials import model_search


@task
def read_data_task(path: str):
    return read_df(path)


@task
def preprocess_task(df_bikes):
    return preprocess(df_bikes)


@task
def dump_pickle_task(obj, filename):
    dump_pickle(obj, filename)


@task
def model_search_task(train, test, num_trials: int):
    logger = get_run_logger()
    # logger.info(f"Looking for train and test.pkl in {Path(dest_path).resolve()}")
    logger.info(f"Beginning model_search with {num_trials} trials")
    return model_search(train=train, test=test, num_trials=num_trials)


@task
def register_model_task():
    return register_model()


@flow()
def to_bikes_flow(data_path: str, num_trials: int):
    """Deployment flow for re-training the TO-bikeshare-classifier

    Taken from preprocess.run(), with prefect logger added
    """
    logger = get_run_logger()

    # Path.mkdir(dest_path, exist_ok=True)
    # logger.debug(f"absolute dest_path: {dest_path.resolve()}")

    logger.info(f"reading data from {data_path}")
    df = read_data_task(data_path)

    logger.info("prepping data")
    df_bikes = preprocess_task(df)
    logger.info(f"loaded {len(df_bikes)} rows of data")

    train, test = train_test_split(
        df_bikes,
        test_size=0.3,
        stratify=df_bikes["target"],
    )
    logger.info(f"Train size: {len(train)}\tTest size: {len(test)}")

    # dump_pickle_task(train, Path(dest_path / "train.pkl"))
    # dump_pickle_task(test, Path(dest_path / "test.pkl"))
    # logger.info(f"Saved train.pkl and test.pkl in {dest_path}")

    trials = model_search_task(train=train, test=test, num_trials=num_trials)
    if trials:
        for trial in trials:
            logger.debug(f"Trial {trial['tid']}: {trial['result']}")
        latest_vers = register_model_task()
        logger.info(f"best model run ID: {latest_vers.run_id}")
        logger.info(f"source: {latest_vers.source}")
    else:
        logger.error("No successful trials")


if __name__ == "__main__":
    # for testing
    to_bikes_flow(
        data_path="/home/kohada/to-bikes/data/bikeshare-2017-q1.csv",
        # dest_path="/home/kohada/to-bikes/data/output/",
        num_trials=5,
    )
