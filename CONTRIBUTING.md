# Contributing

## Coding Style
The citrine-python library follows [PEP8](https://www.python.org/dev/peps/pep-0008/), with the following exceptions:
* Maximum line length is 99 characters for code and 119 characters for docstrings
* Several docstring rules are relaxed (see tox.ini for a list of the ignored rules)

Type hints are strongly encouraged.

Docstrings must follow [Numpy style](https://numpydoc.readthedocs.io/en/latest/format.html) so that Sphinx can parse them to make the docs.

For additional (non-binding) inspiration, check out the [Google Python Style Guide](https://github.com/google/styleguide/blob/gh-pages/pyguide.md).

## PR Submission
Features should be developed in a branch with a descriptive name and the pull request (PR) submitted into the `develop` branch.
In order to be merged a PR must be approved by one authorized user and the build must pass.
A passing build requires the following:
* All tests pass
* The linter finds no violations of PEP8 style
* Every line of code is executed by a test (100% coverage)
