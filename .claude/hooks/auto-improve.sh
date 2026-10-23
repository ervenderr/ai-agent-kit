#!/usr/bin/env bash
# UserPromptSubmit: nudge Claude to run improve-prompt on weak prompts. Stdout is added as context; never blocks.
p=$(jq -r '.prompt // empty')
case "$p" in ""|/*) exit 0 ;; esac
echo "If the user's prompt is vague, underspecified or poorly structured, first apply the improve-prompt skill: write the improved prompt in one short block, then carry it out. If it is already clear, ignore this note and do not mention it."
exit 0
