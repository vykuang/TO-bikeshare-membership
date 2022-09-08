"""
Retrieves and runs the latest version of the registered model
"""
import logging
import os
import sys
from datetime import datetime
import mlflow.pyfunc
from flask import Flask, jsonify, request
from mlflow.tracking import MlflowClient
from dotenv import load_dotenv

MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db")
MLFLOW_EXP_NAME = os.getenv("MLFLOW_EXP_NAME", "TO-bikeshare-classifier")
MLFLOW_REGISTERED_MODEL = os.getenv("MLFLOW_REGISTERED_MODEL", "TO-bikeshare-clf")

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

def preprocess(ride):
    """Preprocess the json input"""
    logging.info("Preprocessing request")
    
    features = {}
    date_fmt = """%d/%m/%Y %H:%M"""
    dt_start = datetime.strptime(ride['trip_start_time'], date_fmt)
    dt_end = datetime.strptime(ride['trip_stop_time'], date_fmt)
    features['day_of_week'] = dt_start.weekday()
    features['start_hour'] = dt_start.hour
    features['end_hour'] = dt_end.hour
    features['target'] = ride['user_type'] == "Member"
    features['from_station_id'] = ride['from_station_id']
    features['to_station_id'] = ride['to_station_id']
    features['trip_duration_seconds'] = ride['trip_duration_seconds']
    logging.debug(f'Num features returned: {len(features)}')
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

    features = preprocess(ride)
    logging.info("Preprocessed input data")

    model = retrieve()
    logging.info("Model retrieved from artifact store")

    pred, proba = predict(model, features)
    result = {
        "predicted_membership": pred,
        "probability": proba,
        "model_version": model.metadata,
    }
    logging.info("Returning result")

    return jsonify(result)

if __name__ == "__main__":
    load_dotenv()
    app.run(
        debug=True,
        host="0.0.0.0",
        port=9393,
    )

