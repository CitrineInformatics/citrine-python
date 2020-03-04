# Contributing

## Coding Style
The citrine-python library follows [PEP8](https://www.python.org/dev/peps/pep-0008/), with the following exceptions:
* Maximum line length is 99 characters for code and 119 characters for docstrings
* Several docstring rules are relaxed (see tox.ini for a list of the ignored rules)

Type hints are strongly encouraged.

Docstrings must follow [Numpy style](https://numpydoc.readthedocs.io/en/latest/format.html) so that Sphinx can parse them to make the docs.

For additional (non-binding) inspiration, check out the [Google Python Style Guide](https://github.com/google/styleguide/blob/gh-pages/pyguide.md).

## PR Submission
Features should be developed in a branch with a descriptive name and the pull request (PR) submitted into the `master` branch.
In order to be merged, a PR must be approved by one authorized user and the build must pass.
A passing build requires the following:
* All tests pass
* The linter finds no violations of PEP8 style
* Every line of code is executed by a test (100% coverage)

## Dependencies
Dependencies are tracked in multiple places:
* requirements files (requirements.txt and test_requirements.txt)
* setup.py
* Pipfile

The setup.py file only contains libraries that are necessary for users to run citrine-python.
If you add a dependency that is necessary to run the repo, it is crucial that you add it to setup.py.

The requirements files and the Pipfile *additionally* contain dependencies for testing/development.
The two options are redundant, but we maintain both to give developers options (Pipfile is more powerful but more involved to use).
Please keep both up to date whenever you add or change dependencies.
If you change the Pipfile, run `pipfile lock` to generate a new version of Pipfile.lock.
Other developers can use this file to recreate the precise environment.