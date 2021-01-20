#!/bin/sh


BASEDIR=$(dirname "$0")
EFF_RHY_DIR="${BASEDIR}"/../..
cd $EFF_RHY_DIR
TEMP_OUT="${BASEDIR}"/.temp_build_examples
SVG_PATH="${EFF_RHY_DIR}"/docs/resources/svgs/

exit_code=0

which verovio
if [[ $? -ne 0 ]]
then
    echo 'Error: verovio not found'
    exit_code=1
else
    for example in "${EFF_RHY_DIR}"/examples/example*.py
    do
        echo python3 efficient_rhythms.py --settings "$example"
        echo     --verovio-arguments '--page-height 450' --no-interface
        echo     --output-notation svg
        python3 efficient_rhythms.py --settings "$example" \
            --verovio-arguments '--page-height 450' --no-interface \
            --output-notation svg >& "$TEMP_OUT"
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
    if [[ ! -e "${SVG_PATH}" ]]
    then
        mkdir "${SVG_PATH}"
    fi
    mv "${EFF_RHY_DIR}"/examples/midi/example*.svg "${SVG_PATH}"
fi

exit 0

if [[ -z "$MIDANI" ]]
then
    echo 'Error: midani not found!'
    echo 'This script expects to find path to midani.py in an environment'
    echo '    variable called $MIDANI'
    exit_code=1
else
    global_settings="${BASEDIR}"/midani/example_midani_settings.py
    stationary_settings="${BASEDIR}"/midani/stationary_midani_settings.py
    for settings in "${BASEDIR}"/midani/example_*_midani_settings.py
    do
        # INTERNET_TODO how to echo command and also run it?
        echo python3 "$MIDANI" --settings "$global_settings" \
        echo      "$stationary_settings" "$settings" --frames 2
        python3 "$MIDANI" --settings "$global_settings" \
            "$stationary_settings" "$settings" --frames 2
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
