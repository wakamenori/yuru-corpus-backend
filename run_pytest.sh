#!/bin/bash
array=($(ls | grep _api))
for apiDir in ${array[@]}; do
  python -m pytest ${apiDir}
done
