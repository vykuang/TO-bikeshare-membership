"""
Searches the MLflow database for the best performing model and register to production stage
"""
import logging
import os
from pathlib import Path

import mlflow
from dotenv import load_dotenv
from mlflow.entities import ViewType
from mlflow.tracking import MlflowClient


def register_model():
    dotenv_path = Path.cwd() / ".env"
    load_dotenv(dotenv_path)

    MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db")
    MLFLOW_EXP_NAME = os.getenv("MLFLOW_EXP_NAME", "TO-bikeshare-classifier")
    MLFLOW_REGISTERED_MODEL = os.getenv("MLFLOW_REGISTERED_MODEL", "TO-bikeshare-clf")

    client = MlflowClient(tracking_uri=MLFLOW_TRACKING_URI)
    exp = client.get_experiment_by_name(MLFLOW_EXP_NAME)
    best_runs = client.search_runs(
        experiment_ids=exp.experiment_id,
        run_view_type=ViewType.ACTIVE_ONLY,
        max_results=3,
        order_by=["metrics.roc_auc DESC"],
    )
    for run in best_runs:
        logging.debug(run.info.run_id)
    # Register
    # get runs_ID and assign registry name
    run_ID = best_runs[0].info.run_id
    model_uri = f"runs:/{run_ID}/models"
    model_vers = mlflow.register_model(
        model_uri,
        MLFLOW_REGISTERED_MODEL,
    )

    # Promote to production stage
    # how to retrieve latest version?
    latest_vers = client.get_latest_versions(name=MLFLOW_REGISTERED_MODEL)
    logging.info(latest_vers)
    client.transition_model_version_stage(
        name=MLFLOW_REGISTERED_MODEL,
        version=latest_vers[-1].version,
        stage="Production",
        archive_existing_versions=True,
    )
    # for rm in client.list_registered_models():
    #     pprint(dict(rm), indent=4)
    return latest_vers[-1]


if __name__ == "__main__":
    register_model()
