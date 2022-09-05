# Project Layout

Why does this deserve its own document? It relates to this thing called **relative imports**. It's bugged me for

* tests,
* uploading code for prefect flows,
* running scripts within modules,
* loading `.env`, and
* just about any time I don't need it there, it comes up.

## Ideogical layout

```
to-bikes/
    data/
    docs/
    src/
        bikeshare/
        __init__.py        
            model/                
                __init__.py
                preprocess.py
                trials.py
                flow.py
                flow_deploy.py
        prefect_agent/
            agent.Dockerfile
            docker-compose.yaml
            Pipfile
            .env
    tests/
```

Flow deployment:

* `python -m src.bikeshare.model.flow_deploy -f local`
    * `from .flow import my_flow`
* `.prefectignore` in `to-bikes/`

I switched to using CLI: `prefect deployment build ./flow.py:to_bikes_flow` to make yaml and then `prefect deployment apply <flow_ID>`. 

## Relative imports

Relevant links:

* [SOF relative imports](https://stackoverflow.com/questions/14132789/relative-imports-for-the-billionth-time/14132912#14132912)
* [docs on __main__](https://docs.python.org/3/library/__main__.html)
* [docs on modules](https://docs.python.org/3/tutorial/modules.html#executing-modules-as-scripts)

When we run .py as a script, it is treated as *top-level script*, and `__name__` becomes `__main__`.

When .py is *imported*, it is run as a module. `__name__` is then derived from the folder hierarchy, e.g. `bikeshare.model.trials`. Where the name starts depends on the placement of `__init__.py`. Again, only if the module is *imported*. If run as script, name is overridden.

### Scripts and relative imports

Relative imports use the `__name__` to determine the relative import locations. But because script's name is overridden as `__main__`, the `.` operator aren't found; its name has no dots. Nothing is relative to this top-level script. It results in *relative-import in non-package* error.

> Relative imports are only for use within module files.
