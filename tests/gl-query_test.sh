# #!/bin/bash

FILENAME='test_commands.txt'

# String replacement for 'DATE'
TODAY=$(date '+%Y-%m-%d')
YESTERDAY=$(date -j -v-1d -f "%Y-%m-%d" $TODAY "+%Y-%m-%d")
if [[ "$(uname -s)" == "Darwin" ]]
then
    echo "You're on Mac, so sed requires a backup file : sed -i '.bak'  "
    sed -i '.bak' "s/DATE/$TODAY/g" test_commands.txt
    sed -i '.bak' "s/YESTERDAY/$YESTERDAY/g" test_commands.txt
else
    echo "You're not on Mac. You can use sed as usual"
    sed -i "s/DATE/$TODAY/g" test_commands.txt
    sed -i "s/YESTERDAY/$YESTERDAY/g" test_commands.txt
fi

# Run tests. After each test, check exit code with $?
s=0
f=0
num_tests=0
while read p || [ -n "$p" ]; do
    ((num_tests=num_tests+1))
    echo "Test # $num_tests / $(grep -c '' $FILENAME) "
    echo "Executing the following command: $p"
    eval "time $p --silent"
    if [[ $? -eq "0" ]]
    then
        echo -e "[ SUCCESS ] : Exit Code was 0 \n"
        ((s=s+1))
    else
        echo -e "[ FAILURE ]: Exit Code was $? \n"
        ((f=f+1))
    fi
done < $FILENAME

num_commands=$( grep -c "" $FILENAME )
if ! command -v bc &> /dev/null
then
    echo "bc doesn't exist";
else
    success_rate=`bc <<< "scale=3; $s/(($num_commands)) * 100"`
    failure_rate=`bc <<< "scale=3; $f/(($num_commands)) * 100"`
fi
echo "Successful Commands: ${s} / ${num_commands} - $success_rate %"
echo "Failed     Commands: ${f} / ${num_commands} - $failure_rate %"


# Set file back to normal -- safety check if running this script locally

if [[ "$(uname -s)" == "Darwin" ]]
then
    echo "You're on Mac, so sed requires a backup file : sed -i '.bak'  "
    sed -i '.bak' "s/$TODAY/DATE/g" test_commands.txt
    sed -i '.bak' "s/$YESTERDAY/YESTERDAY/g" test_commands.txt
else
    sed -i "s/$TODAY/DATE/g" test_commands.txt
    sed -i "s/$YESTERDAY/YESTERDAY/g" test_commands.txt
fi

rm test_commands.txt.bak || true
rm test.csv|| true # CSV may not be generated if no results found

# Gate check
if [[ $f -gt 0 ]]
then
    echo "Test Suite FAILED!"
    exit 1
fi
