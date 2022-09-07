"""
Retrieves and runs the latest version of the registered model
"""
import logging
import os
import sys

import mlflow.pyfunc
from flask import Flask, jsonify, request
from mlflow.tracking import MlflowClient

MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db")
MLFLOW_EXP_NAME = os.getenv("MLFLOW_EXP_NAME", "TO-bikeshare-classifier")
MLFLOW_REGISTERED_MODEL = os.getenv("MLFLOW_REGISTERED_MODEL", "TO-bikeshare-clf")

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

def preprocess(ride):
    """Preprocess the json input"""
    logging.info("Preprocessing request")
    features = {}
    return features


def retrieve():
    """Retrieves and returns the latest version of the registered model"""
    client = MlflowClient(tracking_uri=MLFLOW_TRACKING_URI)
    # search string requires quotation marks around everything
    # only one search expression in 1.26
    mv_search = client.search_model_versions(f"name='{MLFLOW_REGISTERED_MODEL}'")
    for mv in mv_search:
        # pprint(dict(mv), indent=4)
        logging.debug(f"version: {mv.version}\nStage: {mv.current_stage}\nSource: {mv.source}")

    model_uris = [mv.source for mv in mv_search if mv.current_stage == "Production"]
    logging.debug(model_uris)

    # alternatively model_uri could also be direct path to s3 bucket:
    # s3://{MLFLOW_ARTIFACT_STORE}/<exp_id>/<run_id>/artifacts/models
    # the models:/model_name/Production uri is only useable if MLflow server is up
    model = mlflow.pyfunc.load_model(
        # model_uri=f'models:/{MLFLOW_REGISTERED_MODEL}/Production'
        model_uri=model_uris[0]
    )
    return model


def predict(model, features):
    """Given model and bikeshare trip data, return the predicted membership,
    as well as the associated probability
    """
    pred = model.predict(features)
    proba = model.predict_proba(features)
    return float(pred), float(proba)


app = Flask("bikeshare-membership-prediction")


@app.route("/predict", methods=["POST"])
def predict_endpoint():
    """Joining the above funcs into one invocation triggered
    by an HTTP POST request
    POST because client needs to provide the required features
    for web service to make the prediction
    """
    # from the POST request
    ride = request.get_json()
    logging.info("Received POST request")

    features = preprocess(ride)
    logging.info("Preprocessed input data")

    model = retrieve()
    logging.info("Model retrieved from artifact store")

    pred, proba = predict(model, features)
    result = {
        "predicted_membership": pred,
        "probability": proba,
        "model_version": {},
    }
    logging.info("Returning result")

    return jsonify(result)
