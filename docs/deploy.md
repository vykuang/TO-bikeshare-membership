# Model Deployment

The trained ML model will be hosted as a web service. The service will expect a JSON formatted input with the same fields as the 2017 training data

## Workflow

This is a simpler mode of deployment, and fitting for this proof of concept project.

* Gunicorn instance is listening at specific port of instance's public IP
* User POSTs @ `/predict` with the json of the input data
* Web service will
    * Preprocess and prepare input data
    * Retrieve the latest registered model in Production stage
    * Predict on the input using the retrieved model,
    * Return membership prediction along with the `proba` percentage

## Set up

* Web service will run inside a docker container
* Container will contain the code to preprocess the data, retrieve the model from MLflow, and make the prediction using the model
* Credentials for selecting the latest registered model from registry:
    * MLFLOW_TRACKING_URI
    * MLFLOW_EXP_NAME
    * MLFLOW_REGISTERED_MODEL
* Credentials for AWS S3 access:
    * load `/home/user/.aws:/root/.aws:ro` as volume
    * AWS_PROFILE to select the role with the least possible permission
    * Alternatively the docker could run on EC2 instance with the correct user attached and there would be no need to load credentials

## Testing

Run `predict.py` locally to use flask server in debug mode. Test with `test_pred.py`. Make sure the ports agree.

### ColumnTransformer instance not fitted yet

When I call `mlflow.sklearn.log_model()` on the `clf` object, that has not been fitted yet, because the scores obtained is from `cross_val_score`, which does not return the fitted estimator. Need to use `cross_validate` and set `return_estimator=True`. Returns a `dict` with these keys: 

```
>>> scores = cross_validate(clf, X, y,
...                         scoring='precision_macro', cv=5,
...                         return_estimator=True)
>>> sorted(scores.keys())
['estimator', 'fit_time', 'score_time', 'test_score']
```

Should use `cross_validate` and log `scores['estimator']` instead. Note that according [to source code](https://github.com/scikit-learn/scikit-learn/blob/36958fb24/sklearn/model_selection/_validation.py#L381), `cross_val_score` is just a wrapper for `cross_validate` that only returns the `['test_scores']`. However, that setting returns estimators for *each* split. I'm looking for just one.

How about I fit on train as normal, `cross_val_score` to obtain training score, and then test on held out data. From source code, this uses a clone of the estimator to make separate fit and predicts for evaluation, so I can still log the original fitted `clf` object, even after running CV, without worrying about the estimators changing.

## Other deployment scenarios

Instead of POSTing the actual trip data as input to the web service...

* POST a path to the input file for the model to make predictions on
* Batch prediction; no web service. model will make predictions on a scheduled basis (or perhaps based on API trigger). Input file could be specified by that API call, or simply on the latest source data available based on the scheduled datetime. The goal would be to score the current deployed model against the newest batch of bikeshare trip data