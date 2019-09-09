#!/bin/sh
echo "Removing type hints to satisfy Python 3.5"
find ./src -regex '.*\.py'|while read fileName; do
  echo $fileName
  strip-hints $fileName --to-empty --only-assigns-and-defs >tmp.py
  mv tmp.py $fileName
done
find ./tests -regex '.*\.py'|while read fileName; do
  echo $fileName
  strip-hints $fileName --to-empty --only-assigns-and-defs >tmp.py
  mv tmp.py $fileName
done