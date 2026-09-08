#!/bin/sh
# The official DSH bridge substitutes pluginRoot in commands but does not
# export CLAUDE_PLUGIN_ROOT. Derive it from this installed launcher instead.
set -eu
[ "${PLANNING_DISABLED:-}" = "1" ] && exit 0
CLAUDE_PLUGIN_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
export CLAUDE_PLUGIN_ROOT
# An absent plan is different from broken state or a rejected explicit binding.
# This reminder delegates task classification/selection to the Skill; no files
# are initialized here, including for read-only or host planning requests.
if [ "${1:-}" = "user-prompt-submit" ] && [ -z "${PLAN_ID:-}" ] && [ -z "${PWF_PLAN_ROOT:-}" ] \
    && [ ! -e task_plan.md ] && [ ! -L task_plan.md ] && [ ! -e .planning ] && [ ! -L .planning ]; then
    printf '%s\n' '{"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": "[planweft] For an authorized multi-step implementation task, first load the installed project-docs Skill and follow its plan-selection workflow. Simple tasks, read-only review, diagnosis and planning mode must not initialize project records. User scope and project rules take precedence."}}'
    exit 0
fi
# DSH workspace-write confines shell hooks too: HOME caches are read-only.
# Snapshots are private and disposable. The native adapter owns turn dedup;
# the sandbox may mount a fresh /tmp for each invocation.
umask 077
cache=$(mktemp -d /tmp/planweft-hook.XXXXXX) || exit 0
trap 'rm -rf -- "$cache"' EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
XDG_CACHE_HOME="$cache" sh "$CLAUDE_PLUGIN_ROOT/hooks/claude-hook.sh" "$@"
