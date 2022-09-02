# Pytest

Trying the follow the `src` layout [per pytest's recommendation](https://docs.pytest.org/en/7.1.x/explanation/goodpractices.html#choosing-a-test-layout-import-rules) really through me for a loop. How in the world did those tests import from the `src` layer?

## Installed package and standard practice

The answer was hidden in SWE standard practices. Sometimes, for a package, tests are written against *installed* versions of those packages. So if they have `src/my_pkg`, the tests would simply have `import my_pkg` because in that test environment, `my_pkg` has been installed, and is importable like any other packages e.g. numpy and pandas.

Most repos will have a `setup.py`, and then install in a virtualenv with `pip install --editable .`. Tests are then run in that virtualenv, where, again, `my_pkg` is installed as a site package.

[See blogpost on benefits of src](https://bskinn.github.io/My-How-Why-Pyproject-Src/). Notice that most of the discussion revolves around packages and distributing those packages.

[Another one talking about testing against packages](https://hynek.me/articles/testing-packaging/):

> If you use the ad hoc layout without an src directory, your tests do not run against the package as it will be installed by its users. They run against whatever the situation in your project directory is.

and,

> That GitHub issue demonstrated to me that there’s likely more that can go wrong than I thought and that isolating the code into a separate – **un-importable** – directory might be a good idea

Emphasis mine.

[Above post links to another reference](https://blog.ionelmc.ro/2014/05/25/python-packaging/#the-structure).

> You will be forced to test the installed code (e.g.: by installing in a virtualenv). This will ensure that the deployed code works (it's packaged correctly) - otherwise your tests will fail. Early. Before you can publish a broken distribution.
    You will be forced to install the distribution. If you ever uploaded a distribution on PyPI with missing modules or broken dependencies it's because you didn't test the installation. Just beeing able to successfuly build the sdist doesn't guarantee it will actually install!

They also make direct reference to a `src`-less layout, with `my_pkg` in root, allowing tests against local files instead of the installed version.

## PYTHONPATH and `sys.path`

Another obstacle was this unspoken assumption that PYTHONPATH has been edited so that it includes `my_pkg`. PYTHONPATH and within python code, `sys.path`, defines the paths where packages and modules can be imported.

And in fact that is an configuration option now built into `pytest`. In my `pyproject.toml` I have this standard snippet to include `src` so that my tests can simply import `my_pkg` as if it was installed.

```toml
[tool.pytest.ini_options]
pythonpath = [
"src",
]
```

[Credit to this SOF post](https://stackoverflow.com/questions/50155464/using-pytest-with-a-src-layer)

However this actually defeats the whole point of having `src` because `pytest` *wants* you to not be able to easily import locally and *wants* you to test against an installed version.

But if my package isn't meant to be installed, does it still make sense? In the end, I'm deploying my model as a web application, not a library. Is there a different way?

## Outdated tests

Seeing some cases where pytest is testing an older snapshot files that's already been modified. I need to save and close those files.

## Fixtures

### tmp_path and scope mismatch

So I created a prefect block fixture with a `session` scope, requiring `tmp_path` but it lead to a scope mismatch error:

```py
    ScopeMismatch: You tried to access the function scoped fixture tmp_path with a session scoped request object, involved factories:
    tests/conftest.py:5:  def tmp_prefect_block(tmp_path)
```

As the log states, `tmp_path` is function scoped by default; each test which calls the tmp_path fixture will procedurally create its own temporary directory. What I need, also from the log, is `tmp_path_factory`, which *is* session-scoped.

Fixture becomes

```py
import pytest

from prefect.filesystems import LocalFileSystem 

@pytest.fixture(scope="session")
def tmp_prefect_block(tmp_path_factory):
    test_name = 'test1'
    test_path = tmp_path_factory.mktemp(test_name)
    test_block = LocalFileSystem(
        name=test_name, 
        basepath=test_path,
        )
    test_block.save(name=test_name, overwrite=True)
    test_block = LocalFileSystem.load(name=test_name)
    return test_block
```

Not sure if I can delete the blocks after creating them, but the idea of *tear downs* are built into pytest. Instead of `return`, we `yield` the requested object, and have the teardown portion after `yield`. [Docs here](https://docs.pytest.org/en/latest/how-to/fixtures.html#teardown-cleanup-aka-fixture-finalization)

Delete with CLI:

```py
import subprocess
subprocess.run(
        ["prefect", "block", "delete", f"local-file-system/{test_name}"],
        check=True, text=True,
    )
```