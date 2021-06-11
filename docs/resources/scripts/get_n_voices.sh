#!/usr/bin/env bash

# Get the number of voices in each example.
# We parse the settings files in sequence looking for "num_voices"; later
# files we override earlier ones.
# We assume that "num_voices" will appear at most once in each file. If it
# doesn't occur in any file, we set it to the default value (3).
n_voices=3
for settings in "$@"
do
  # The capturing in this regex doesn't seem to work in the system sed on my
  # mac so using gsed instead
  result=$(gsed -n 's/ *"num_voices": *\([0-9]\+\) *,/\1/p' "$settings")
  # after https://unix.stackexchange.com/a/146945/455517
  if ! [[ -z "${result// }" ]]
  then
    n_voices="$result"
  fi
done

echo "$n_voices"
