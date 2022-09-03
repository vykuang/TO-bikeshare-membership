import os
from pathlib import Path

from dotenv import load_dotenv

dotenv_path = Path.cwd() / ".env"
load_dotenv(dotenv_path)
print(dotenv_path)

MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db")
MLFLOW_EXP_NAME = os.getenv("MLFLOW_EXP_NAME", "TO-bikeshare-clf")
# mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
# mlflow.set_experiment(MLFLOW_EXP_NAME)
print(MLFLOW_TRACKING_URI)
print(MLFLOW_EXP_NAME)
