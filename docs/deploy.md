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

### `retrieve()` is hanging

From logs the function is stuck at `model = mlflow.pyfunc.load_model(model_uri)`

In a notebook it took just under 20 minutes to load a 2 MB model.pkl. Something is going on with S3. Tried with loading straight from mlflow server, same debug output:

```
DEBUG:s3transfer.tasks:Executing task IOWriteTask(transfer_id=0, {'offset': 2097152}) with kwargs {'fileobj': <s3transfer.utils.DeferredOpenFile object at 0x7ff1f0567130>, 'offset': 2097152}
DEBUG:s3transfer.tasks:IOWriteTask(transfer_id=0, {'offset': 2359296}) about to wait for the following futures []
DEBUG:s3transfer.tasks:IOWriteTask(transfer_id=0, {'offset': 2359296}) done waiting for dependent futures
```

Worked earlier on the laptop, but even then it took 10+ seconds. At this point the laptop is seeing the same results in terms of model loading.

Maybe because I'm loading a canada server from asia?

I should try running the frontend on amazon EC2. *Passed in 4.84 seconds*. Welp. Try restarting my computer maybe, who knows.

Restart allowed model loading in 50 seconds. That's about 49 more than I'm willing to spend.

### Launching a new EC2 instance for our deployment

Let's run the docker on an EC2 to avoid the unloadable object issue.

#### Set up EC2 instance

* Make sure IAM *role* (not user) attached has access to our MLflow artifact store.
* Forward the ${MODEL_PORT}
* S3 Policy attached to role must apply to the bucket *as well as all objects within the bucket*, otherwise we'll be able to access the bucket, but not download the objects, i.e. our models.
    * Object ARN to apply to all objects inside bucket: `arn:aws:s3:::<bucket_name>/*`

#### Setting up instance environment

* git
* pipenv
* pyenv
* docker

1. docker

    ```bash
    # in amazon linux, yum replaces apt
    sudo yum update

    sudo amazon-linux-extras install docker
    sudo service docker start
    # For both cases:
    # add current user to `docker` group to run docker without sudo
    # make group
    sudo groupadd docker
    # add user
    sudo usermod -aG docker $USER
    # update changes
    newgrp docker
    # try
    docker run hello-world
    ```

2. docker compose - [see offical docs](https://docs.docker.com/compose/install/linux/#install-the-plugin-manually).

    ```bash
    # install manually
    DOCKER_CONFIG=${DOCKER_CONFIG:-$HOME/.docker}

    mkdir -p $DOCKER_CONFIG/cli-plugins

    curl -SL https://github.com/docker/compose/releases/download/v2.10.2/docker-compose-linux-x86_64 -o $DOCKER_CONFIG/cli-plugins/docker-compose

    chmod +x $DOCKER_CONFIG/cli-plugins/docker-compose

    # test
    docker compose version
    ```

3. git

    ```bash
    sudo yum install git
    ```

4. Clone our project repo, and run the docker compose file with `docker compose up -d --build`

    Can stop here if we only want to deploy our docker container.

    If we want to develop on this instance, continue below.

5. (Optional) Pyenv, pipenv
    Follow [offical pyenv docs](https://github.com/pyenv/pyenv#installation) for installation

    ```bash
    git clone https://github.com/pyenv/pyenv.git ~/.pyenv

    # add to .bashrc
    echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
    echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
    echo 'eval "$(pyenv init -)"' >> ~/.bashrc

    # add to bash_profile
    echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bash_profile
    echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bash_profile
    echo 'eval "$(pyenv init -)"' >> ~/.bash_profile

    # restart shell
    exec "$SHELL"

    # Python build dependencies; needed to install new python versions
    sudo yum install gcc zlib-devel bzip2 bzip2-devel readline-devel sqlite sqlite-devel openssl-devel tk-devel libffi-devel xz-devel

    # install python
    pyenv install 3.9.12

    # upgrade pip
    pip install --upgrade pip

    # pipenv
    pip install --user pipenv
    ```

    Development on this instance would also necessitate adding github credentials to enable push. Install github CLI and configure a security token.

## Other deployment scenarios

Instead of POSTing the actual trip data as input to the web service...

* POST a path to the input file for the model to make predictions on
* Batch prediction; no web service. model will make predictions on a scheduled basis (or perhaps based on API trigger). Input file could be specified by that API call, or simply on the latest source data available based on the scheduled datetime. The goal would be to score the current deployed model against the newest batch of bikeshare trip data