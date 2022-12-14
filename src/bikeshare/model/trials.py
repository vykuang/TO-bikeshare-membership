import argparse
import os
import pickle
from pathlib import Path

import mlflow
import numpy as np
from dotenv import load_dotenv
from hyperopt import STATUS_OK, Trials, fmin, hp, tpe
from hyperopt.pyll import scope
from sklearn.compose import make_column_transformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder


def load_pickle(path: Path):
    with open(path, "rb") as f_in:
        return pickle.load(f_in)


def model_search(train, test, num_trials):

    dotenv_path = Path.cwd() / ".env"
    load_dotenv(dotenv_path)

    MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db")
    MLFLOW_EXP_NAME = os.getenv("MLFLOW_EXP_NAME", "TO-bikeshare-clf")
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment(MLFLOW_EXP_NAME)

    # train = load_pickle(Path(data_path) / "train.pkl")
    # test = load_pickle(Path(data_path) / "test.pkl")

    X_train = train.drop("target", axis=1)
    y_train = train["target"].values

    X_test = test.drop("target", axis=1)
    y_test = test["target"].values

    def objective(params):
        with mlflow.start_run():
            mlflow.set_tag("model", "to-bikeshare-clf")
            # log only the hyperparameters passed
            mlflow.log_params(params)

            ct = make_column_transformer(
                (OneHotEncoder(), ["from_station_id"]),
                (OneHotEncoder(), ["to_station_id"]),
                # remainder='drop',
                remainder="passthrough",
            )
            clf = make_pipeline(ct, RandomForestClassifier(**params))
            clf.fit(X_train, y_train)

            cv = StratifiedKFold()
            scores_train = cross_val_score(
                clf,
                X_train,
                y_train,
                cv=cv,
                scoring="roc_auc",
                n_jobs=-1,
            )
            roc_auc_train = np.average(scores_train)
            mlflow.log_metric("roc_auc_train", roc_auc_train)

            y_preds = clf.predict_log_proba(X_test)[:, 1]
            roc_auc = np.average(roc_auc_score(y_test, y_preds))

            mlflow.log_metric("roc_auc", roc_auc)
            mlflow.sklearn.log_model(clf, artifact_path="models")

            inv_roc_auc = 1 / roc_auc

        return {"loss": inv_roc_auc, "status": STATUS_OK}

    search_space = {
        "n_estimators": scope.int(hp.quniform("n_estimators", 10, 100, 1)),
        "max_depth": scope.int(hp.quniform("max_depth", 1, 20, 1)),
        "min_samples_split": scope.int(hp.quniform("min_samples_split", 2, 10, 1)),
        "min_samples_leaf": scope.int(hp.quniform("min_samples_leaf", 1, 4, 1)),
        "class_weight": hp.choice("class_weight", ["balanced", "balanced_subsample"]),
        "random_state": 42,
    }

    rstate = np.random.default_rng(42)  # for reproducible results
    trials = Trials()
    fmin(
        fn=objective,
        space=search_space,
        algo=tpe.suggest,
        max_evals=num_trials,
        trials=trials,
        rstate=rstate,
        return_argmin=True,
    )
    return trials


def _run(data_path, max_evals):
    train = load_pickle(data_path / "train.pkl")
    test = load_pickle(data_path / "test.pkl")
    model_search(train=train, test=test, num_trials=max_evals)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data_path",
        type=Path,
        default="../data/output",
        help="the location where the processed TO bikeshare data was saved.",
    )
    parser.add_argument(
        "--max_evals",
        type=int,
        default=10,
        help="the number of parameter evaluations for the optimizer to explore.",
    )
    args = parser.parse_args()

    _run(args.data_path, args.max_evals)
