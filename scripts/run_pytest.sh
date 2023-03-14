#!/usr/bin/env sh

# Helper script to execute pytest with coverage on the citrine-python test directory
# This is invoked by the Travis test job, so is useful to check for when developing locally

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
REPO_DIR=$(dirname $SCRIPT_DIR)

pytest --cov=src/ --cov-report term-missing:skip-covered --cov-config=tox.ini --cov-fail-under=100 -r .
