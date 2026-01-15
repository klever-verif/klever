#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <path-to-review-file-relative-to-repo-root>" >&2
  exit 2
fi

repo_root=$(git rev-parse --show-toplevel 2>/dev/null)
file_rel="$1"
file_abs="$repo_root/$file_rel"

shopt -s nocasematch

read_status() {
  local line
  local status
  status=""

  if [ ! -f "$file_abs" ]; then
    printf '%s' "$status"
    return 0
  fi

  while IFS= read -r line; do
    line=${line#${line%%[![:space:]]*}}
    if [[ "$line" == status:* ]]; then
      status=${line#status:}
      status=${status#${status%%[![:space:]]*}}
      status=${status%${status##*[![:space:]]}}
      status=${status,,}
      break
    fi
  done <"$file_abs"

  printf '%s' "$status"
}

last=""
while true; do
  status=$(read_status)

  if [ "$status" != "$last" ]; then
    echo "$(date +%H:%M:%S) status=$status"
    last="$status"
  fi

  if [ "$status" = "feedback_provided" ] || [ "$status" = "done" ]; then
    exit 0
  fi

  sleep 1
done
