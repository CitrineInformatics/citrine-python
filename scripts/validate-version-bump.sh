#!/bin/bash

set -eu

extract_version() {
  sed -En "s/.*version='([0-9]+\.[0-9]+\.[0-9]+).*/\1/p" <<< "$@"
}

extract_major() {
  sed -En "s/([0-9]+).*/\1/p" <<< "$1"
}

extract_minor() {
  sed -En "s/.*\.([0-9]+)\..*/\1/p" <<< "$1"
}

extract_patch() {
  sed -En "s/.*([0-9])/\1/p" <<< "$1"
}

trap "$(set +eu)" EXIT

CURRENT="$(extract_version $(cat setup.py))"
MASTER="$(extract_version $(git show master:setup.py))"

CURRENT_MAJOR="$(extract_major ${CURRENT})"
CURRENT_MINOR="$(extract_minor ${CURRENT})"
CURRENT_PATCH="$(extract_patch ${CURRENT})"

MASTER_MAJOR="$(extract_major ${MASTER})"
MASTER_MINOR="$(extract_minor ${MASTER})"
MASTER_PATCH="$(extract_patch ${MASTER})"

if [ "${CURRENT_MAJOR}" -gt "${MASTER_MAJOR}" ]; then
  echo "major version bump"
  exit 0
elif [ "${CURRENT_MAJOR}" -lt "${MASTER_MAJOR}" ]; then
  echo "error - major version decreased!"
  exit 1
else
  if [ "${CURRENT_MINOR}" -gt "${MASTER_MINOR}" ]; then
    echo "minor version bump"
    exit 0
  elif [ "${CURRENT_MINOR}" -lt "${MASTER_MINOR}" ]; then
    echo "error - minor version decreased!"
    exit 2
  else
    if [ "${CURRENT_PATCH}" -gt "${MASTER_PATCH}" ]; then
      echo "patch version bump"
      exit 0
    elif [ "${CURRENT_PATCH}" -lt "${MASTER_PATCH}" ]; then
      echo "error - patch version decreased!"
      exit 3
    else
      echo "error - version unchanged!"
      exit 4
    fi
  fi
fi
