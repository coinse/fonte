#!/bin/bash

pid=$1
vid=$2
tool=$3
use_Rewrite=$4

if [ "$use_Rewrite" = true ]; then
  postfix=""
else
  postfix="_noOpenRewrite"
fi

scdir=/root/workspace/data/$pid-${vid}b/$tool/validation${postfix}
commits=/root/workspace/data/${pid}-${vid}b/$tool/commits.pkl
aggregated=/root/workspace/data/${pid}-${vid}b/$tool/validation${postfix}.csv

if [ ! -f $aggregated ]; then
  touch $aggregated
  python /root/workspace/tools/get_candidates.py $commits | while read sha; do
    if [ -f $scdir/$sha.csv ]; then
      sed -e "s/^/${sha},/" $scdir/$sha.csv >> $aggregated
    else
      rm $aggregated
      break
    fi
  done
  [ -f $aggregated ] && echo "Successfully generated: $aggregated"
else
  echo "$aggregated exists"
fi
