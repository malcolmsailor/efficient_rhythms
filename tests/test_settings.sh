#!/bin/bash

# Run misc. settings files, make sure they complete without error

BASEDIR=$(dirname "$0")
EFF_RHY_DIR="${BASEDIR}"/../
cd $EFF_RHY_DIR
TEMP_OUT="${BASEDIR}"/.temp_test_settings

settings=(
    "/test_settings/test_repeated_notes.py"
)

for item in "${settings[@]}"
do
    echo python3 efficient_rhythms.py --no-interface --settings "${BASEDIR}${item}"
    python3 efficient_rhythms.py --no-interface --settings "${BASEDIR}${item}" >& "$TEMP_OUT"
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
