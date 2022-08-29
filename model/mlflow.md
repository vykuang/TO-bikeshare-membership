# MLFlow

## Setup

Initialize MLflow backend. We already have a backend server on AWS EC2.

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
