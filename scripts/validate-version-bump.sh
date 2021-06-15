#!/bin/bash

set -eu

extract_version() {
  sed -En "s/.*version.*=*['\"]([0-9]+\.[0-9]+\.[0-9]+).*/\1/p" <<< "$@"
}

extract_major() {
  sed -En "s/([0-9]+).*/\1/p" <<< "$1"
}

extract_minor() {
  sed -En "s/.*\.([0-9]+)\..*/\1/p" <<< "$1"
}

extract_patch() {
  sed -En "s/.*\.([0-9]+)/\1/p" <<< "$1"
}

trap "$(set +eu)" EXIT

CURRENT="$(extract_version $(cat src/citrine/__version__.py))"
MAIN="$(extract_version $(git show main:src/citrine/__version__.py))"

CURRENT_MAJOR="$(extract_major ${CURRENT})"
CURRENT_MINOR="$(extract_minor ${CURRENT})"
CURRENT_PATCH="$(extract_patch ${CURRENT})"

MAIN_MAJOR="$(extract_major ${MAIN})"
MAIN_MINOR="$(extract_minor ${MAIN})"
MAIN_PATCH="$(extract_patch ${MAIN})"

if [ "${CURRENT_MAJOR}" -gt "${MAIN_MAJOR}" ]; then
  echo "major version bump"
  exit 0
elif [ "${CURRENT_MAJOR}" -lt "${MAIN_MAJOR}" ]; then
  echo "error - major version decreased!"
  exit 1
else
  if [ "${CURRENT_MINOR}" -gt "${MAIN_MINOR}" ]; then
    echo "minor version bump"
    exit 0
  elif [ "${CURRENT_MINOR}" -lt "${MAIN_MINOR}" ]; then
    echo "error - minor version decreased!"
    exit 2
  else
    if [ "${CURRENT_PATCH}" -gt "${MAIN_PATCH}" ]; then
      echo "patch version bump"
      exit 0
    elif [ "${CURRENT_PATCH}" -lt "${MAIN_PATCH}" ]; then
      echo "error - patch version decreased!"
      exit 3
    else
      echo "error - version unchanged!"
      exit 4
    fi
  fi
fi
