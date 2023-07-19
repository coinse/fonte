#!/bin/bash
error_trace=/root/workspace/setup.error

project=$1
version=$2
tmpdir=$3
path_to_coverage=$4

if [ ! -z $path_to_coverage ] && [ -f $path_to_coverage ]; then
  echo "$path_to_coverage already exists"
  skip_coverage=1
else
  skip_coverage=0
fi

faulty_version=$(grep ^${version}, /defects4j/framework/projects/${project}/commit-db | cut -d',' -f2)

if [ -d ${tmpdir}/coverage_xmls ]; then
  mv ${tmpdir}/coverage_xmls /tmp/${project}-${version}-coverage_xmls
fi

[ -d $tmpdir ] && rm -rf $tmpdir
defects4j checkout -p $project -v ${version}b -w ${tmpdir}
if [ ! -d $tmpdir ]; then
  echo "${project}-${version}b: [Error 1] checkout failure"
  exit 1
fi

cd ${tmpdir}
if [ -d /tmp/${project}-${version}-coverage_xmls ]; then
  mv /tmp/${project}-${version}-coverage_xmls ${tmpdir}/coverage_xmls
else
  mkdir coverage_xmls
fi

# classes.relevant: the classes loaded by all triggering (failing) test cases
defects4j export -p classes.relevant -o classes.relevant
defects4j export -p tests.trigger -o tests.trigger.expected
defects4j export -p dir.src.classes -o dir.src.classes

if [[ "$project" = "Time" ]] && (( $version > 20 )); then
  git reset $faulty_version
  git checkout -- JodaTime/$(cat dir.src.classes)
  rm -rf $(cat dir.src.classes)
  mv JodaTime/$(cat dir.src.classes) $(cat dir.src.classes)
else
  git reset $faulty_version
  git checkout -- $(cat dir.src.classes)
  if [ $? -ne 0 ]; then
    echo "${project}-${version}b: [Error 2] no matching src dir"
    exit 2
  fi
fi
echo "Reset to the actual buggy version $faulty_version  OK"

git rev-list HEAD > commits.log

if ! defects4j compile; then
  echo "${project}-${version}b: [Error 3] compile error"
  exit 3
fi

if ! timeout 10m defects4j test; then
  echo "${project}-${version}b: [Error 4] timeout error"
  exit 4
fi

if [ -f failing_tests ]; then
  cp failing_tests failing_tests.all
  grep "\-\-\- \K(.*)" failing_tests -oP > tests.trigger
else
  touch tests.trigger
fi

touch tests.all
sort all_tests | while read test_case; do
  method=$(expr match "$test_case" '\([^(]*\)')
  class=$(expr match "$test_case" '[^(]*(\([^)]*\))')
  echo "$class::$method" >> tests.all
done

echo "=========== Expected Failing Tests ==========="
cat tests.trigger.expected
echo ""
echo "============ Actual Failing Tests ============"
cat tests.trigger
echo ""

var1=$(sort tests.trigger.expected)
var2=$(sort tests.trigger)

if [ "$var1" != "$var2" ]; then
  echo "${project}-${version}b: [Error 5] failing tests are not as expected"
  exit 5
fi

if [ $skip_coverage -eq 1 ]; then
  exit 0
fi

touch tests.relevant
sort classes.relevant | while read relevant_class; do
  cat tests.all | grep "$(echo $relevant_class | rev | cut -d. -f1 | rev)" >> tests.relevant
done

[ -d coverage_xmls/failings ] || mkdir coverage_xmls/failings
sort tests.trigger | while read test_method; do
  if [ ! -f coverage_xmls/failings/$test_method.xml ]; then
    echo "Failing: $test_method"
    defects4j coverage -t $test_method -i classes.relevant
    mv coverage.xml coverage_xmls/failings/$test_method.xml
  else
    echo "Failing: $test_method (exists)"
  fi
done
#CONFIGURABLE [ tests.relevant | tests.all ]

total="$(cat tests.relevant | wc -l)"
count=1
[ -d coverage_xmls/passings ] || mkdir coverage_xmls/passings
sort -u tests.relevant | while read test_method; do
  if [ ! -f coverage_xmls/failings/$test_method.xml ]; then
    if [ ! -f coverage_xmls/passings/$test_method.xml ]; then
      echo "Relevant ${count}/${total}: $test_method"
      defects4j coverage -t $test_method -i classes.relevant
      mv coverage.xml coverage_xmls/passings/$test_method.xml
    else
      echo "Relevant ${count}/${total}: $test_method (exists)"
    fi
  else
    echo "Relevant ${count}/${total}: $test_method (skipped)"
  fi
  count=$((count+1))
done
