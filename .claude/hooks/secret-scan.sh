#!/usr/bin/env bash
# PreToolUse(Edit|Write): block content that looks like a credential.
set -euo pipefail
payload=$(jq -r '[.tool_input.content, .tool_input.new_string] | map(select(. != null)) | join("\n")')
[ -z "$payload" ] && exit 0
if echo "$payload" | grep -Eq 'AKIA[0-9A-Z]{16}|sk-ant-[A-Za-z0-9_-]{20,}|sk-[A-Za-z0-9]{32,}|ghp_[A-Za-z0-9]{36}|xox[baprs]-[A-Za-z0-9-]{10,}|-----BEGIN [A-Z ]*PRIVATE KEY-----'; then
  echo "Blocked: content looks like a secret. Use an env var and document it in .env.example." >&2
  exit 2
fi
exit 0
