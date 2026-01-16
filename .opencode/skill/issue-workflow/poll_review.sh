#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 2 ]; then
  echo "Usage: $0 <path-to-review-file-relative-to-repo-root> <status-to-wait-for> [status-to-wait-for...]" >&2
  exit 2
fi

repo_root=$(git rev-parse --show-toplevel 2>/dev/null)
file_rel="$1"
file_abs="$repo_root/$file_rel"
expected_statuses=()
for expected in "${@:2}"; do
  expected_statuses+=("$(printf '%s' "$expected" | tr '[:upper:]' '[:lower:]')")
done

read_status() {
  local line
  local status
  status=""

  if [ ! -f "$file_abs" ]; then
    printf '%s' "$status"
    return 0
  fi

  while IFS= read -r line; do
    line=${line#$'\xef\xbb\xbf'}
    if [[ "$line" =~ ^[[:space:]]*status[[:space:]]*:[[:space:]]*(.*)$ ]]; then
      status=${BASH_REMATCH[1]}
      status=${status%%#*}
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

  for expected in "${expected_statuses[@]}"; do
    if [ -n "$expected" ] && [ "$status" = "$expected" ]; then
      exit 0
    fi
  done

  sleep 1
done
