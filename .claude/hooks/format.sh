#!/usr/bin/env bash
# PostToolUse(Edit|Write): best-effort formatting; never fails the turn.
f=$(jq -r '.tool_input.file_path // empty')
{ [ -z "$f" ] || [ ! -f "$f" ]; } && exit 0
case "$f" in
  *.py) command -v ruff >/dev/null && { ruff format -q "$f"; ruff check --fix -q "$f"; } || true ;;
  *.ts|*.tsx|*.js|*.jsx|*.json|*.css) command -v prettier >/dev/null && prettier --write --log-level silent "$f" || true ;;
esac
exit 0
