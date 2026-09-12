#!/bin/sh
# Classify the one PlanWeft document-handoff marker in a selected task plan.
# This helper is called only by packaged hooks. It never changes project files;
# malformed, absent, or duplicated markers remain conservatively pending.

set -u

PLAN_FILE="${1:-}"
[ -n "${PLAN_FILE}" ] && [ -f "${PLAN_FILE}" ] || {
    printf '%s\n' pending
    exit 0
}

awk '
    { sub(/\r$/, "") }
    /<!--[[:space:]]*planweft-docs-status:/ { all_markers++ }
    $0 == "## Documentation Handoff" {
        headings++
        in_handoff = 1
        next
    }
    in_handoff && /^## / { in_handoff = 0 }
    in_handoff && $0 ~ /^<!-- planweft-docs-status:/ {
        markers++
        if ($0 ~ /^<!-- planweft-docs-status: (pending|not_required|complete) -->$/) {
            valid_marker = 1
            value = $0
            sub(/^<!-- planweft-docs-status: /, "", value)
            sub(/ -->$/, "", value)
        } else {
            valid_marker = 0
        }
    }
    in_handoff && $0 ~ /^- Documents considered: .+/ { documents = 1 }
    in_handoff && $0 ~ /^- Rationale \/ evidence: .+/ { rationale = 1 }
    in_handoff && $0 ~ /^- Next action: .+/ { next_action = 1 }
    END {
        if (headings == 1 && all_markers == 1 && markers == 1 && valid_marker &&
            (value == "pending" || value == "not_required" || value == "complete") &&
            (value == "pending" || rationale) &&
            (value != "complete" || (documents && rationale && next_action))) {
            print value
        } else {
            print "pending"
        }
    }
' "${PLAN_FILE}"
