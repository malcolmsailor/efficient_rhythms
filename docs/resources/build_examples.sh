#!/bin/sh



BASEDIR=$(dirname "$0")
cd $BASEDIR/../..

# which midani.py
# if [[ $? -eq 1 ]]
# then
#     midani_not_found=1
# else
#     midani_not_found=0
#     for settings in "${BASEDIR}"/example_*_midani_settings.py
#     do
#         midani.py --settings "$settings" --frames 2
#     done
# fi


if [[ -z "$MIDANI" ]]
then
    midani_not_found=1
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

exit_code=0
if [[ ! -z $midani_not_found ]]
then
    echo 'Error: midani not found!'
    echo 'This script expects to find path to midani.py in an environment'
    echo '    variable called $MIDANI'
    exit_code=1
fi

exit $exit_code
