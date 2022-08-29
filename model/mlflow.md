# MLFlow

Goal is to setup a framework to conveniently train and re-train the model given new data on a batch basis, and logging the trials and best model onto MLFlow. Remote server and remote artifact store will be used for storage and retrieval.

## Framework

What I'm having issues with is the interface between `preprocess` and `trials`. In the tutorials, the approach was basic to get the course going - train/validate with data from two months prior, and test/predict the current month.

In the context of my bikeshare data, a similar concept could work. If we want to predict 2019 Q2, we test/validate with 2017/8 Q2 data.

But let's frame it this way. Say we have all this data available from 2017 to 2019, we should use all of it to train the best possible model and use that to predict future data, say 2020 onwards.

Is there a way to use train-test-split? Seems crude to split it this way, especially given the size discrepancy between the years (2019 has many more records).

If we combine I'd have to add a `year` column? That data is already in the datetime so it's not much hassle to extract.

Let's keep the scope smaller first. Train/val/test only on 2017. `preprocess` will perform train-test-split, and pickle the dataframes for `trials`.

Side note maybe I don't need binarizer. Just map it in a apply/lambda within `preprocess`

## Setup

Initialize MLflow backend. We already have a backend server on AWS EC2.
Can set as env var `MLFLOW_TRACKING_URI`

```python
import mlflow
from hyperopt import STATUS_OK, Trials, fmin, hp, tpe
from hyperopt.pyll import scope

from sklearn.ensemble import Random
from sklearn.linear_model import Logistic
from sklearn.metrics import f1_score, roc_auc_score

# remote server URI to record runs
mlflow.set_tracking_uri("sqlite:///mlflow.db")
# replace with http://<external_ip>:5000

mlflow.set_experiment('TO-bikeshare-membership')

def run(data_path, num_trials):

    X_train, y_train = ...
    X_valid, y_valid = ...
    # define objective fn for hyperopt

    def objective(params):
        # train within mlflow context
        with mlflow.start_run():
            mlflow.set_tag('developer', 'vk')
            mlflow.log_params(params)

            rf = RandomForestClassifier(**params)
            rf.fit(X_train, y_train)
            y_pred = rf.predict(X_valid)
            f1 = f1_score()
            roc = roc_auc_score()
            
            mlflow.log_metric('f1', f1)
            mlflow.log_metric('roc_auc', roc)	

        return {'loss': 1 - roc, 'status': STATUS_OK}

        search_space = {
            'param1': scope.int(hp.quniform('param1', start, end, step)),
            ...
        }

    rstate = np.random.default_rng(42)
    fmin = (
        fn=objective,
        space=search_space,
        algo=tpe.suggest,
        max_evals=num_trials,
        trials=Trials(),
        rstate=rstate,
    )
```

Perhaps initiate a local run before pushing to remote?

No just go straight to remote.