#!/usr/bin/env bash

set -euo pipefail

missing=0

require_file() {
  local path="$1"
  if [ ! -f "$path" ]; then
    echo "Missing: $path"
    missing=1
  fi
}

require_file ".continue/prompts/planweft.prompt"
require_file ".continue/skills/project-docs/SKILL.md"
require_file ".continue/skills/project-docs/examples.md"
require_file ".continue/skills/project-docs/reference.md"
require_file ".continue/skills/project-docs/scripts/init-session.sh"
require_file ".continue/skills/project-docs/scripts/init-session.ps1"
require_file ".continue/skills/project-docs/scripts/check-complete.sh"
require_file ".continue/skills/project-docs/scripts/check-complete.ps1"
require_file ".continue/skills/project-docs/scripts/session-catchup.py"

if [ "$missing" -ne 0 ]; then
  exit 1
fi

case ".continue/prompts/planweft.prompt" in
  *.prompt) ;;
  *) echo "Prompt file must end with .prompt"; exit 1 ;;
esac

echo "Continue integration files look OK."
