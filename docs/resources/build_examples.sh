#!/bin/sh


BASEDIR=$(dirname "$0")
EFF_RHY_DIR="${BASEDIR}"/../..
cd $EFF_RHY_DIR

exit_code=0

which verovio
if [[ $? -ne 0 ]]
then
    echo 'Error: verovio not found'
    exit_code=1
else
    for example in "${EFF_RHY_DIR}"/examples/example*.py
    do
        python3 efficient_rhythms.py --settings "$example" \
            --verovio-arguments '--page-height 450' --no-interface \
            --output-notation svg
    done
    # TODO check if docs/resources/svgs exists
    mv "${EFF_RHY_DIR}"/examples/midi/example*.svg \
        "${EFF_RHY_DIR}"/docs/resources/svgs/
fi

if [[ -z "$MIDANI" ]]
then
    echo 'Error: midani not found!'
    echo 'This script expects to find path to midani.py in an environment'
    echo '    variable called $MIDANI'
    exit_code=1
else
    global_settings="${BASEDIR}"/example_midani_settings.py
    for settings in "${BASEDIR}"/example_*_midani_settings.py
    do
        # TODO how to echo command and also run it?
        echo python3 "$MIDANI" --settings "$global_settings" "$settings" --frames 2
        python3 "$MIDANI" --settings "$global_settings" "$settings" --frames 2
        if [[ $? -ne 0 ]]
        then
            echo Error running midani, aborting
            exit 1
        else
            echo ===============================================================
        fi
    done
fi

exit $exit_code
