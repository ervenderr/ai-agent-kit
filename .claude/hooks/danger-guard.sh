#!/usr/bin/env bash
# PreToolUse(Bash): exit 2 blocks the command and sends stderr to Claude.
set -euo pipefail
cmd=$(jq -r '.tool_input.command // empty')
[ -z "$cmd" ] && exit 0
patterns=(
  'rm -rf /' 'rm -rf ~' 'rm -rf \*'
  'git push.*(--force|-f( |$))'
  'git reset --hard origin'
  'curl[^|]*\|[[:space:]]*(sh|bash)' 'wget[^|]*\|[[:space:]]*(sh|bash)'
  'chmod -R 777' 'DROP[[:space:]]+(TABLE|DATABASE)'
)
for p in "${patterns[@]}"; do
  if echo "$cmd" | grep -Eiq -- "$p"; then
    echo "Blocked by danger-guard (matches /$p/). Ask the user to run this themselves." >&2
    exit 2
  fi
done
exit 0
