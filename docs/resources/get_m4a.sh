#!/bin/bash

input_path=$1
output_path=$2

check_for_noisy_apps() {
    local noisy_apps=(
        "Google Chrome.app"
        "Logic Pro X.app"
        "iTunes.app"
        "VLC.app"
    )
    open_apps=( )
    for noisy_app in "${noisy_apps[@]}"
    do
        n_processes=$(ps aux | grep -v grep | grep -c "$noisy_app")
        if [[ $n_processes != 0 ]]
        then
            open_apps+=( "$noisy_app" )
        fi
    done
    if [[ ${#open_apps[@]} != 0 ]]
    then
        echo \
"The following potentially noisy apps are open, please close them and then try again:"
        for app in "${open_apps[@]}"
        do
            echo "    $app"
        done
        exit 1
    fi
}

TEMP_OUT=~/tmp/.temp_get_m4a
echo_and_run() {
    echo "\$ ${*:2}"
    if [[ "$1" = 'silent' ]]
    then
        "${@:2}" >& "$TEMP_OUT"
    else
        "${@:2}"
    fi
}

try_to_run() {
    echo_and_run "$@"
    if [[ $? -ne 0 ]]
    then
        if [[ "$1" = 'silent' ]]
        then
            cat "$TEMP_OUT"
        fi
        echo Error running "${@:2}", aborting
        if [[ "$1" = 'silent' ]]
        then
            rm "$TEMP_OUT"
        fi
        exit 1
    else
        if [[ "$1" = 'silent' ]]
        then
            rm "$TEMP_OUT"
        fi
        echo ===============================================================
    fi
}


# First, check for other applications that may emit sounds
check_for_noisy_apps

try_to_run silent which pygmid2aud.py
try_to_run verbose pygmid2aud.py "$input_path" --overwrite --output-path "$output_path"
