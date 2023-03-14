#!/usr/bin/env sh

# Helper script to execute pytest with coverage when invoked from the citrine-python repository directory
# This is invoked by the Travis test job, so is useful to check for when developing locally

pytest --cov=src/ --cov-report term-missing:skip-covered --cov-config=tox.ini --cov-fail-under=100 -r .
