# AGENTS.md

`citrine-python` is the Python SDK for the Citrine Platform. Users install it from PyPI as `citrine`. It calls the platform REST APIs and builds on the `gemd` package from `gemd-python`.

## Layout

| Path | Contents |
|------|----------|
| `src/citrine/citrine.py` | `Citrine`, the client entry point |
| `src/citrine/_session.py` | HTTP session, auth, and request logging |
| `src/citrine/resources/` | Platform resources and their collections, such as projects, teams, and datasets |
| `src/citrine/informatics/` | AI Engine models: predictors, design spaces, constraints, and workflows |
| `src/citrine/gemtables/`, `src/citrine/gemd_queries/` | GEM Table definitions and GEMD query criteria |
| `src/citrine/_rest/`, `src/citrine/_serialization/` | Base collection and pagination classes, and the base classes for serialization |
| `src/citrine/__version__.py` | Package version, read by setuptools |
| `tests/` | Unit tests, which mirror `src/citrine/`. Shared fakes and factories are in `tests/utils/` |
| `docs/source/` | Sphinx source in `.rst` |
| `scripts/` | Test runner, version-bump check, and docs build |

## Commands

CI installs dependencies with pip from `requirements.txt` and `test_requirements.txt`, which pin exact versions. The repo has no `uv.lock`, and CI uses none of the dependency groups in `pyproject.toml`. Set up a virtual environment the same way:

```bash
pip install -r requirements.txt -r test_requirements.txt
pip install --no-deps -e .
```

| Task | Command |
|------|---------|
| Lint | `flake8 src/citrine` |
| Format | `ruff format src tests` |
| Expired deprecations | `derp src src/citrine/__version__.py` |
| Tests with coverage | `pytest --cov=src/citrine --cov-report term-missing:skip-covered --cov-config=tox.ini --no-cov-on-fail --cov-fail-under=100 tests/` |
| Version-bump check | `python scripts/validate_version_bump.py`. It runs `git fetch origin` first. |
| Version check, lint, deprecations, and tests | `scripts/run_tests.sh`. It exits with an error on `main`. |
| Docs | `pip install -r doc_requirements.txt`, then `make -C docs html` |

## CI gates

Pull requests into `main` and `release/**` run `.github/workflows/pr-checks.yml` and `pr-tests.yml`. Both call shared workflows in `CitrineInformatics/common-gh-actions`. To pass, a PR needs:

1. A higher version in `src/citrine/__version__.py` than `origin/main` has.
2. A clean `flake8` run on `src/citrine`.
3. No `removed_in` deprecation at or below the current version, checked by `derp`.
4. Passing tests at 100% line coverage, on Python 3.10 through 3.14, on Linux, macOS, and Windows.

The docs job builds with `-W` but has `continue-on-error`, so doc warnings do not block. Publishing a GitHub release deploys to PyPI and GitHub Pages.

## Conventions

- Style is PEP 8 with a 99-character code limit and a 119-character docstring limit. `tox.ini` holds the flake8 config and its ignore list.
- Lint with `flake8` and format with `ruff format`. `pyproject.toml` holds the ruff config.
- Write Numpy-style docstrings. Sphinx autogenerates `docs/source/reference/`, which git ignores.
- Make arguments keyword-only, except a first argument that is required, obvious, and shared by similar methods.
- Name an object's own identifier `uid`. Name the identifier of another type `<type>_id`, such as `bar_id`.
- Mark unsupported experimental APIs with `[ALPHA]` at the start of the docstring.
- Add runtime dependencies to `pyproject.toml` and pin them in `requirements.txt`. Pin test-only dependencies in `test_requirements.txt`.
- `Citrine()` reads `CITRINE_API_KEY` and `CITRINE_API_HOST` when the caller passes no `api_key` or `host`. Unit tests use fake sessions from `tests/utils/` and run offline.

## Further reading

- `CONTRIBUTING.md`: style rules, logging, docs layout, and the release-notes template
- `.github/pull_request_template.md`: the PR checklist
- Published docs: https://citrineinformatics.github.io/citrine-python/
