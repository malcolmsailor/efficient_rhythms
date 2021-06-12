#!/bin/bash

# Run misc. settings files, make sure they complete without error

TEMP_OUT=.temp_test_settings

for item in test_settings/*.py
do
    echo python3 -m efficient_rhythms --no-interface --settings "${item}"

    python3 -m efficient_rhythms --no-interface --settings "${item}" \
        >& "$TEMP_OUT"
    if [[ $? -ne 0 ]]
    then
        cat "$TEMP_OUT"
        echo Error running efficient_rhythms, aborting
        rm "$TEMP_OUT"
        exit 1
    else
        rm "$TEMP_OUT"
        echo ===============================================================
    fi
done
