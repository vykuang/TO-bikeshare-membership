# Orchestration with Prefect

Some basic questions to be answered

* Do I need a separate env for prefect deployment? Or will prefect be installed into my current venv?
* Should I have a separate `flow.py` that invokes scripts from my `models/` dir, one that has the `@task` and `@flow` decorators? This way I don't change the existing code, and retain the option to run it manually without prefect.
* Should I try scheduling a basic flow for testing? Yes. Let's try with `preprocess`.

## Refresh

[Docs here](https://docs.prefect.io/concepts/deployments/)

* Our code are referred to as *flows*
* We define and create *Deployment* which specifies
    * what's packaged with the flow
    * scheduling
    * API trigger
    * Storage, remote or local
    * Infra in which the flow will run
* Prefect API manages the workflow
* Prefect agent pulls flows from queue and runs them, on the specified infra:
    * requirements.txt
    * docker network config
    * etc.

## Setup

* Server - let's not have another EC2 instance. I'll be using the free tier offered by Prefect Cloud
    * Create API Key pair after logging in
    * `prefect cloud login --key <generated_key>` to activate profile
        * `prefect profile ls` to view profiles
        * `use` to activate one of those profile
    * Create a *Workspace* to organize flows on web UI (no API to create workspace?)
        * Never mind - free tier provides only one workspace
    * `prefect cloud workspace set --workspace "${email_without_punctuation}/${existing_workspace_name}"`
    * Set up storage and block? Maybe I'll leave that in code
    * CLI can also set up via `prefect block register -f <my_block.py>`???
        * `create s3` only gives you a link to the UI so you can make it there instead

## Deployment

Deployment is how prefect refers to scheduling the flow, or triggering via API call. Deployment is what takes the script from manual calls to *API-managed entities.*

Requirements:

* flow script
* prefect orchestration engine:
    * prefect orion, or
    * remote prefect orion server on my AWS EC2 instance, initiated with `prefect orion start`
* agent and work queue
* storage for the flow script (optional)

### DeploymentSpec

Code from mlops-zoomcamp used `DeploymentSpec` to define deployment. That is now **deprecated and removed**. [See docs here](https://docs.prefect.io/concepts/deployments/?h=deploymentspec)

[Use `Deployment` instead](https://docs.prefect.io/api-ref/prefect/deployments/)

### Deployment Parameters

[Docs here](https://docs.prefect.io/api-ref/prefect/deployments/)

The `.prefectignore` is placed not in the flow's current director, but in project home, which is `~/to-bikes` in our case.

Work queue should also be created and assigned here, to organize our flows, and have agents dedicated to specific queues.

Flow parameters:

* data_path - s3 path to the bikeshare csv files
* dest-path - path in prefect-agent local dir to store the .pkl files

Save as .env vars? Currently hard-coded.

I do not think I should pass a `dict` of flow parameters through CLI when I call `flow_deploy.py`. Requires me to pass it as `'{"key": "val"}'` and then use `json.loads` as type, and even after all that it throws me this `multiple param passed for arg flow_parameter` error.

It's because of this:

```py
# definition
def build(
    flow_params,
    storage: Union[S3, LocalFileSystem],
    deploy_name: str = "my_flow",
    work_queue_name: str = "to-bikes",
    apply: bool = True,
):
    ...

# invoke
deployment = build(
        storage,
        deploy_name=deploy_name,
        flow_params=parameters,
        apply=apply,        
    )
```

I defined `flow_params` as positional arg, and put `storage` in the first position. Immediately after I define `flow_params` again, this time the way I want to. Add `storage=storage` when invoking `build()`.

#### .prefectignore

Trying to work this thing with `deploy.py` is kind of frustrating. Their workflow expects you to use CLI and `prefect deploy build ...` and a `deploy.yaml`, which automatically creates a `.ignore` in the same folder. Also, it's kind of important because if I can't properly configure this thing, it'll upload everything in the same directory as the flow script.

Also having issues invoking `flow_deploy.py` because of the whole relative import thing.

> Relative imports only work if the importing module has `__name__` other than `__main__`, i.e. NOT CALLING IT FROM CLI

If I call `flow_deploy.py` from CLI, the ignore file needs to be present in `pwd`.

### `prefect deploy build <.yaml>`

Easier to just do it this way I think. Have a flow.py, build a yaml with the command, then apply and run. Edit the parameters inside the yaml.

```bash
#! /usr/bin/env sh
prefect deployment build ./flow.py:my_flow \
	--name to-bikes-clf-train-s3 \
	--version v0 \
	--tag to-bikes \
	--work-queue TO-bikes-clf \
	--storage-block s3/to-bikes-flows \
	--cron "0 0 1 * *" \
	--output to-bikes-clf-train-s3-deployment.yaml \
	--path to-bikes-clf-train/
    --apply
```

### Storage

Stores the flow code for deployments. Uses the concept of *Blocks*. Define a block to be our S3 bucket. Note that default is local filesystem.

Create a block via UI or python:

```python

block = S3(
    bucket_path="my-bucket/a-sub-directory", 
    aws_access_key_id="foo", 
    aws_secret_access_key="bar")
block.save("example-block")

# Use the block in building deployment
s3_block = S3.load("example-block")
deployment = Deployment.build_from_flow(
    ...
    storage=s3_block,
)
```

In the CLI, it would be `--storage-block s3/example-block`. Doesn't make much sense to me? Mmmmh no Okay I see it.

Can I look for this block before trying to make it? Maybe the wrong question. The `.save()` only creates a block *configuration* to be used. Could set overwrite to False too, so that if a block with the same name exists, it doesn't get overwritten. Need to use `try except ValueError` block if it already exists.

### Blocks

Storage uses *Blocks* as its underlying structure. Enables storage of configs and allows interface for interacting with external sys.

More interestingly they take on the `xcom` role in Airflow of allowing data transfer between tasks in a flow:

```py
from prefect.blocks.system import JSON

# instantiate
json_block = JSON(value={"the_answer": 42})

# save
json_block.save(name="life-the-universe-everything")

# load
@flow
def what_is_the_answer():
    json_block = JSON.load("life-the-universe-everything")
    print(json_block.value["the_answer"])

what_is_the_answer() # 42
```

Can also save encrypted secrets (e.g. AWS credentials) in a `SecretStr` block, so that those values are not exposed even if the block object is logged:

```py
from typing import Optional

from prefect.blocks.core import Block
from pydantic import SecretStr

class AWSCredentials(Block):
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[SecretStr] = None
    aws_session_token: Optional[str] = None
    profile_name: Optional[str] = None
    region_name: Optional[str] = None
aws_credentials_block = AWSCredentials(
    aws_access_key_id="AKIAJKLJKLJKLJKLJKLJK",
    aws_secret_access_key="secret_access_key"
)
print(aws_credentials_block)
# aws_access_key_id='AKIAJKLJKLJKLJKLJKLJK' 
# aws_secret_access_key=SecretStr('**********') 
# aws_session_token=None 
# profile_name=None 
# region_name=None
```

When we define `storage` for deployments, we're defining a *file system block* object

Delete block with `prefect block delete <FILESYSTYPE>/<BLOCK_NAME>`, where FILESYSTYPE could be s3, local, etc. View with `prefect block ls`.

### Agent and Work queues

When a flow is deployed, it is submitted to a specific *work queue*. Agents in the *execution environment* polls that work queue for new flows to execute.

To orchestrate with prefect, an agent needs to run and poll a work queue.

In the execution environment, `prefect agent start "my-queue"` will start the agent, and poll the API given by `PREFECT_API_URL`. For us that points to my prefect cloud endpoint, but if I ran `prefect orion start` on an AWS EC2 instance, it would be `<external_ip>:<port>`.

If we configure a remote instance to act as agent, and install the project dependencies, we wouldn't need to pass the `infrastructure` arg to Deployment. This would be a very basic setup.

Work queues are mostly managed by prefect automatically. Set in deployment and agent start so that they match. Think of it as a pub/sub topic.

Local agent was able to properly collect the flow when I applied `s3` as storage, since it was able to read/write to S3. Took 6 minutes but it worked. One wrinkle: where did it save my pickles???

As far as I know, I ran it as local agent under ~/to-bikes, and I saved it to `./output/`. But nothing new in `~/to-bikes`. Let's add a debug statement:

```py
logger.debug(f'absolute dest_path: {dest_path.resolve()}')
```

Edited and reapplied flow deployment, but didn't take. How would I update my flow?

* Delete and reapply
* Or just reapply

### Agent Infra

What does it need?

* Poll prefect cloud (set API and work-queue env var)
* Fetch flow code from S3 block (S3 read)
* Fetch data (S3 read)
* Retrieve model from MLflow registry (S3 read)
* Preprocess and write to intermediate storage (S3 write)
* Fetch from intermediate model and train
* Register model back to MLflow artifact store (S3 write)

Requirements

* prefect
* boto3
* all reqs of model training
    * sklearn
    * mlflow, etc.

Elephant in the room - I need a way to put all the bikeshare data onto the S3 bucket.

Okay let's put one up, and run a dockerized agent locally

Again, needs API, but *also*, API_KEY to authenticate itself. Not really mentioned in the docs.

Let's upload a file to the cloud. But do I want the prefect-agent to pull directly from TO open data and push to cloud, and then pull from cloud??? I almost think that first part, of pulling from source and pushing to cloud, should be a different flow.

I think to simplify, let's assume that part is done. All relevant files are stored in S3. Leave the pull and store as future dev.

#### Prefect-agent

Runs much quicker in docker than in local mode, perhaps due to lack of infrastructure setup.

How will prefect-agent know which file to pull? How should the training file name be parametrized? Parametrize flow when applying deployment.

Also needs MLflow variable to be set in `.env`.

Okay, now that I've made changes to the code, I need to re-upload them to the remote storage for my prefect agent. Re-build and re-apply the `.yaml`. Also note that I've hard-coded the parameters inside the `deployment.yaml`.

* MLflow is not being loaded; TRACKING_URI not being used. Causes agent to create SQLite.db
    * Cause: When I load functions from `trials.py`, I'm loading them directly and bypassing the `trials` module. This means the top level function where I'm loading the `.env` is not being executed.
    * Action:
        1. Move `load_dotenv` to within model_search()?
        2. Import trials in my flow.py?
    * I think #1 is most straightforward
    * Seems to be breaking my initial ideology of leaving the existing code alone, if I have to shift these things around to fit the flow.
* Removed `dest_path`, the intermediate storage for the `.pkl` files; just pass the test_train_split results directly to model_search

Clean run at 11:38 pm.

Remaining issues:

* How to parametrize the flow dynamically? Currently the yaml file needs to be manually edited.
* Testing, possibly within prefect context.
* Add `fetch.py` to the pipeline, to pull from source and push to S3 data bucket.
* Using CLI to deploy and apply the flows also forces me to create storage blocks manually. The original idea behind using python API to do so was so that I could avoid that.

### local block

When I ran using local block, the prefect agent threw an error:

```
ERROR   | Flow run 'alpha3-valo' - Flow could not be retrieved from deployment.
FileNotFoundError: [Errno 2] No such file or directory: 'prefect_block'
```

So my docker agent didn't have access to the block, probably because it's dockerized. Need to attach as a volume, perhaps, if I need to use local storage with docker agent.

## Testing

Couldn't run the `flow_deploy.py` from CLI without getting ensnarled by Import Error, so used pytest. After adding the *mandatory* `.prefectignore`, apparently it copies the entire project directory into the storage block. The path of the storage block is also relative to the project home, so by setting it as `./prefect_block` I now have `to-bikes/prefect_block`. Hmm.

If I try testing with `tmp_path`, because I've already created the `local` block and set overwrite False, no new block gets created, and existing block does not have its directory updated, and so remains `./prefect_block` in my home directory.

Making blocks doesn't lend itself well to testing, requiring a few workaround and being resource intensive, but loading it is okay. Workarounds meaning using pytest's `tmp_path_factory` and `subprocess.run(["bash", "cmd"])` to remove the created blocks as part of teardown since the python SDK doesn't allow block deletion.

Currently as of 2022/9/3 I need to run both `test_flow_deploy` and `test_make_block` for the teardown to work properly and not fail.
