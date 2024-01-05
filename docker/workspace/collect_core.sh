#!/bin/bash

pid=$1
vid=$2
tool=$3
use_Rewrite=$4
if [ -z $use_Rewrite ]; then
  use_Rewrite=true
fi

output_dir=/root/workspace/data/$pid-${vid}b
tmp_dir=/tmp/${pid}-${vid}b/
cov_path=$output_dir/coverage.pkl
commit_path=$output_dir/$tool/commits.pkl
source $HOME/.sdkman/bin/sdkman-init.sh && sdk use java 8.0.302-open
echo "Measuring coverage at $tmp_dir ....................................... OK"
(REL=true; sh ./measure_coverage.sh $pid $vid $tmp_dir $cov_path)
if [ $? -eq 0 ]; then
  [ ! -d $output_dir ] && mkdir $output_dir
  cp $tmp_dir/commits.log $output_dir/commits.log
  cp $tmp_dir/failing_tests.all $output_dir/failing_tests

  # java version setting
  if [[ $tool == "tracker" ]]; then
    source $HOME/.sdkman/bin/sdkman-init.sh && sdk use java 21.ea.35-open
  else
    source $HOME/.sdkman/bin/sdkman-init.sh && sdk use java 11.0.12-open
  fi

  # collect commit history
  [ ! -d $output_dir/$tool ] && mkdir $output_dir/$tool

  if [ ! -f $commit_path ]; then
    python collect.py $tmp_dir -v -l $tool -o $output_dir

    # save raw data
    if [[ $tool == "shovel" ]]; then
      mkdir $output_dir/$tool/raw
      cp $tmp_dir/shovel* $output_dir/$tool/raw/
    fi
    if [[ $tool == "tracker" ]]; then
      mkdir $output_dir/$tool/raw
      cp $tmp_dir/tracker* $output_dir/$tool/raw/
    fi
  else
    echo "$commit_path exists"
  fi

  source $HOME/.sdkman/bin/sdkman-init.sh && sdk use java 11.0.12-open
  sh ./tools/detect_style_change.sh $pid $vid $tool $use_Rewrite
  sh ./tools/combine_style_change_results.sh $pid $vid $tool $use_Rewrite

  rm -rf $tmp_dir
  echo "Cleaning up $tmp_dir"
else
  echo "Checkout failed!"
fi
