#!/usr/bin/env bash

# Run misc. settings files, make sure they complete without error

# This script could probably be merged into the tests makefile

# Any pathnames in the settings should be either relative to the repository
# root or absolute
cd "$(dirname "${BASH_SOURCE[0]}" )/.."

TEMP_OUT=.temp_test_settings

for item in tests/test_settings/*.py
do
    # TODO remove skip for cont_rhythms tests after implementing
    if [[ $item =~ .*test_fail.* ]] || [[ $item =~ .*cont_rhythms.* ]]
    then
        echo Skipping "${item}"
    else

        echo python3 -m efficient_rhythms --no-interface --settings "${item}"

        python3 -m efficient_rhythms --no-interface --settings "${item}" \
            >& "$TEMP_OUT"
        if [[ $? -ne 0 ]]
        then
            cat "$TEMP_OUT"
            echo Error running efficient_rhythms with settings "${item}", \
                aborting
            rm "$TEMP_OUT"
            exit 1
        else
            rm "$TEMP_OUT"
            echo ===============================================================
        fi
    fi
done
