#!/bin/bash
analyzer_jar=/root/workspace/tools/java_analyzer/target/java-analyzer-1.0-SNAPSHOT-shaded.jar

pid=$1
vid=$2
commit_log=$3
sha=$4
use_Rewrite=$5
output=$6

[ -f $output ] && rm $output
output=$(realpath $output)

workdir=/tmp/${pid}-${vid}b
[ ! -d $workdir ] && defects4j checkout -p ${pid} -v ${vid}b -w $workdir

cd $workdir

python /root/workspace/tools/get_touched_files.py $commit_log \
  --output $workdir/modified_files_${sha} \
  --commit $sha

echo "- Commit:" $sha
for file in $(cat $workdir/modified_files_${sha}); do
  echo "-- File:" $file
  # checkout to $sha
  git checkout $sha $file
  if [ "$use_Rewrite" = true ]; then
    java -cp $analyzer_jar analyzer.RewriteRunner $file cleanup.diff
    patch -p1 < cleanup.diff
    rm cleanup.diff
  fi
  cp $file $file.$sha
  # checkout to $sha~1
  git checkout $sha~1 $file
  if [ $? -eq 0 ]; then
    # only when $file is a valid path in $sha~1
    if [ "$use_Rewrite" = true ]; then
      java -cp $analyzer_jar analyzer.RewriteRunner $file cleanup.diff
      patch -p1 < cleanup.diff
      rm cleanup.diff
    fi
    cp $file $file.$sha~1

    # compare AST
    java -cp $analyzer_jar analyzer.ASTIsomorphicChecker \
      $file.$sha $file.$sha~1 > $file.$sha.is_isomorphic
    if [ $? -eq 0 ]; then
      if grep -Fxq "true" $file.$sha.is_isomorphic; then
        result='U'
      else
        result='C'
      fi
    else
      result='E' # error
    fi
    echo "--- ASTs are Isomorphic (w/ Rewrite: $use_Rewrite):" $(cat $file.$sha.is_isomorphic)

    rm $file.$sha
    rm $file.$sha~1

    echo $file,$result >> $output
  else
    rm $file.$sha

    echo "$file may not exist in $sha~1"
    echo "$file,N" >> $output
  fi
done

echo "* Summary:" $output
cat $output
echo ""
echo ""
