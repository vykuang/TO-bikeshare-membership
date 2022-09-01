# Orchestration with Prefect

Some basic questions to be answered

* Do I need a separate env for prefect deployment? Or will prefect be installed into my current venv?
* Should I have a separate `flow.py` that invokes scripts from my `models/` dir, one that has the `@task` and `@flow` decorators? This way I don't change the existing code, and retain the option to run it manually without prefect.
* Should I try scheduling a basic flow for testing? Yes. Let's try with `preprocess`.

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

#### Storage

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

Can I look for this block before trying to make it? Maybe the wrong question. The `.save()` only creates a block *configuration* to be used. Could set overwrite to False too, so that if a block with the same name exists, it doesn't get overwritten.