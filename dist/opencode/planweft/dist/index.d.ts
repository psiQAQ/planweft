/**
 * OpenCode plugin entry for planweft.
 *
 * Only the plugin function is exported from this module: OpenCode treats every
 * exported function of a plugin module as a plugin, so the helpers live in
 * ./core.js. Hooks (all fail open: a planning error never breaks a turn):
 *
 * - chat.message: append the framed active plan to the outgoing user message
 *   (or a once-per-turn ambiguity notice), plus the queued write reminder
 * - tool.execute.after: append the progress reminder to write-like tool output
 * - experimental.session.compacting: keep the plan pointer and attestation in
 *   the compaction summary
 * - event session.idle: the completion gate in gated mode, re-prompting the
 *   session with the gate reason (Tier 2: follow-up inject)
 * - tools pw_init, pw_status, pw_check for the model
 */
import { type Plugin } from "@opencode-ai/plugin";
export declare const PlanningWithFiles: Plugin;
