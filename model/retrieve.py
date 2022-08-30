"""
Retrieves and runs thee latest version of the registered model
"""
import os
from pathlib import Path
from pprint import pprint

import mlflow.pyfunc
from dotenv import load_dotenv
from mlflow.tracking import MlflowClient

dotenv_path = Path.cwd() / ".env"
load_dotenv(dotenv_path)

MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db")
MLFLOW_EXP_NAME = os.getenv("MLFLOW_EXP_NAME", "TO-bikeshare-classifier")
MLFLOW_REGISTERED_MODEL = os.getenv("MLFLOW_REGISTERED_MODEL", "TO-bikeshare-clf")

client = MlflowClient(tracking_uri=MLFLOW_TRACKING_URI)

# search string requires quotation marks around everything
# only one search expression in 1.26
mv_search = client.search_model_versions(f"name='{MLFLOW_REGISTERED_MODEL}'")
for mv in mv_search:
    # pprint(dict(mv), indent=4)
    print(f"version: {mv.version}\nStage: {mv.current_stage}\nSource: {mv.source}")

model_uris = [mv.source for mv in mv_search if mv.current_stage == "Production"]
print(model_uris)
# for mv in client.search_registered_models(f"name='{MLFLOW_REGISTERED_MODEL}'"):
#     pprint(dict(mv), indent=4)

# alternatively model_uri could also be direct path to s3 bucket:
# s3://{MLFLOW_ARTIFACT_STORE}/<exp_id>/<run_id>/artifacts/models
# the models:/model_name/Production uri is only useable if MLflow server is up
model = mlflow.pyfunc.load_model(
    # model_uri=f'models:/{MLFLOW_REGISTERED_MODEL}/Production'
    # model_uri='s3://mlflow-artifacts-remote-1212/4/fcf666f0460b4ad8b6b6ab2bfe14a902/artifacts/models'
    model_uri=model_uris[0]
)
