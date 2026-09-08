#!/bin/sh
# The official DSH bridge substitutes pluginRoot in commands but does not
# export CLAUDE_PLUGIN_ROOT. Derive it from this installed launcher instead.
set -eu
CLAUDE_PLUGIN_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
export CLAUDE_PLUGIN_ROOT
exec sh "$CLAUDE_PLUGIN_ROOT/hooks/claude-hook.sh" "$@"
