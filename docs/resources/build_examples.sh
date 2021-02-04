# DEPRECATED in favor of docs/makefile
# #!/bin/bash
#
# BASEDIR=$(dirname "$0")
# EFF_RHY_DIR="${BASEDIR}"/../..
# cd $EFF_RHY_DIR
# TEMP_OUT="${BASEDIR}"/.temp_build_examples
# SVG_PATH="${EFF_RHY_DIR}"/docs/resources/svgs/
#
# # echo_and_run after https://stackoverflow.com/a/12240862/10155119
# echo_and_run() {
#     echo "\$ $*"
#     "$@" >& "$TEMP_OUT"
# }
#
# try_to_run() {
#     echo_and_run "$@"
#     if [[ $? -ne 0 ]]
#     then
#         cat "$TEMP_OUT"
#         echo Error running "$@", aborting
#         rm "$TEMP_OUT"
#         exit 1
#     else
#         rm "$TEMP_OUT"
#         echo ===============================================================
#     fi
# }
#
# ################################################################################
# # Run efficient_rhythms and get notation with verovio
# ################################################################################
# run_effrhy_vrv() {
#     # first argument is page height
#     # subsequent arguments are settings files
#     try_to_run python3 efficient_rhythms.py --settings "${@:2}" \
#         --verovio-arguments "--page-height $1" --no-interface \
#         --output-notation svg
# }
#
# try_to_run which verovio
#
# example_prefixes=(
#     "example"
#     "harmony_example"
# )
#
# page_heights=(
#     450 # 450 works well for two voices
#     600 # 600 seems to work for three voices
# )
#
# for i in "${!example_prefixes[@]}"
# do
#     example_prefix="${example_prefixes[i]}"
#     example_base="${EFF_RHY_DIR}"/examples/"$example_prefix"_base.py
#     for example in $(ls "${EFF_RHY_DIR}"/examples/"$example_prefix"[0-9].py)
#     do
#         run_effrhy_vrv "${page_heights[i]}" "$example_base" "$example"
#     done
#
#     if [[ ! -e "${SVG_PATH}" ]]
#     then
#         mkdir "${SVG_PATH}"
#     fi
#     try_to_run mv "${EFF_RHY_DIR}"/examples/midi/"$example_prefix"[0-9].svg \
#         "${SVG_PATH}"
# done
#
# ################################################################################
# # Run midani and get piano-roll pngs
# ################################################################################
#
# if [[ -z "$MIDANI" ]]
# then
#     echo 'Error: midani not found!'
#     echo 'This script expects to find path to midani.py in an environment'
#     echo '    variable called $MIDANI'
#     exit 1
# fi
#
#
# global_settings="${BASEDIR}"/midani/example_midani_settings.py
# stationary_settings="${BASEDIR}"/midani/stationary_midani_settings.py
# for settings in "${BASEDIR}"/midani/example_*_midani_settings.py
# do
#     try_to_run python3 "$MIDANI" --settings "$global_settings" \
#         "$stationary_settings" "$settings" --frames 2
# done
