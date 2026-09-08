# PlanWeft addition: existence is only a diagnostic, never activation.
# These legacy locations are inspected, never executed or used as fallback.
for PD_OLD_SURFACE in \
    "$HOME/.claude/skills/planning-with-files" \
    "$HOME/.agents/skills/planning-with-files" \
    "$HOME/.codex/skills/planning-with-files" \
    "$HOME/.codex/plugins/cache/"*/planning-with-files \
    ".claude/skills/planning-with-files" \
    ".agents/skills/planning-with-files"; do
    if [ -d "$PD_OLD_SURFACE" ]; then
        warn "original PWF installation detected at $PD_OLD_SURFACE; directory presence does not prove activation. Enable only one planning plugin's hooks per session."
    fi
done
