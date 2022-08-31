from pathlib import Path

from prefect import flow, get_run_logger, task

from ..model.preprocess import preprocess, read_df


@task
def read_data(path: Path):
    return read_df(path)


@task
def prep(df_bikes):
    return preprocess(df_bikes)


@flow
def flow(path: Path):
    logger = get_run_logger()
    logger.info("reading data")
    df = read_data(path)
    logger.info("prepping data")
    # df_bikes = prep(df)
    # logger.info(f'loaded {len(df_bikes)} rows of data')


if __name__ == "__main__":
    flow("/home/kohada/to-bikes/data/bikeshare-2017-q1.csv")
