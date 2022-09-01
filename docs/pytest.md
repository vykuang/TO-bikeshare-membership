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

>
    You will be forced to test the installed code (e.g.: by installing in a virtualenv). This will ensure that the deployed code works (it's packaged correctly) - otherwise your tests will fail. Early. Before you can publish a broken distribution.
    You will be forced to install the distribution. If you ever uploaded a distribution on PyPI with missing modules or broken dependencies it's because you didn't test the installation. Just beeing able to successfuly build the sdist doesn't guarantee it will actually install!

They also make direct reference to a `src`-less layout, with `my_pkg` in root, allowing tests against local files instead of the installed version.

## PYTHONPATH and `sys.path`

Another obstacle was this unspoken assumption that PYTHONPATH has been edited so that it includes `my_pkg`. PYTHONPATH and within python code, `sys.path`, defines the paths where packages and modules can be imported.

And in fact that is an configuration option now built into `pytest`. In my `pyproject.toml` I have this standard snippet to include `src` so that my tests can simply import `my_pkg` as if it was installed.

    [tool.pytest.ini_options]
    pythonpath = [
    "src",
    ]

[Credit to this SOF post](https://stackoverflow.com/questions/50155464/using-pytest-with-a-src-layer)

However this actually defeats the whole point of having `src` because `pytest` *wants* you to not be able to easily import locally and *wants* you to test against an installed version.

But if my package isn't meant to be installed, does it still make sense? In the end, I'm deploying my model as a web application, not a library. Is there a different way?

## Outdated tests

Seeing some cases where pytest is testing an older snapshot files that's already been modified. I need to save and close those files.