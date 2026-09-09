export declare const VERSION = "0.4.0-rc.11";
export declare const BANNER = "[planweft] ACTIVE PLAN \u2014 current state:";
export declare const REMINDER = "[planweft] Update progress.md with what you just did. If a phase is now complete, update task_plan.md status.";
export declare const PLANNING_FILES: readonly ["task_plan.md", "findings.md", "progress.md"];
export declare const WRITE_LIKE_TOOLS: Set<string>;
export type Env = Record<string, string | undefined>;
export declare function isRegularFile(target: string): boolean;
export declare function isRealDir(target: string): boolean;
export declare function slugIsValid(slug: string): boolean;
export declare function planRootIsPinned(env: Env): boolean;
/** Apply the PWF_PLAN_ROOT pin; a broken pin returns null (fail closed). */
export declare function effectiveProjectRoot(project: string, env: Env): string | null;
/**
 * Direct children whose own .planning holds a live plan. Mirrors the
 * `*\/.planning/*\/task_plan.md` probe of inject-plan.sh: depth one, dotted
 * children skipped, and only a LIVE nested plan competes.
 */
export declare function nestedLivePlans(root: string): string[];
export type Resolution = {
    planDir: string | null;
    conflicts: string[];
};
/**
 * Resolve the active plan directory. `explicit` marks a selection that skips
 * the nested-root check (a PWF_PLAN_ROOT pin, an attached session, PLAN_ID).
 */
export declare function resolvePlan(root: string, opts: {
    planId?: string;
    explicit?: boolean;
}, env: Env): Resolution;
export declare function planIdFor(root: string, planDir: string): string;
export declare function attestationPathFor(root: string, planDir: string): string;
export declare function ambiguityNotice(conflicts: string[]): string;
export declare function normalizeWallClock(text: string): string;
export declare function selectLines(text: string, opts: {
    head?: number;
    tail?: number;
}): {
    text: string;
    truncated: boolean;
};
export declare function frameBytes(kind: "plan" | "progress", data: Buffer, truncated?: boolean): string;
/**
 * Effective mode for a plan: the slug's .mode raised by the project root's
 * .mode FLOOR (issue #238). [] when neither file is present; null when either
 * file carries a token outside MODE_TOKENS.
 *
 * A project makes attestation mandatory by committing a root .mode, which is a
 * reviewed project setting. Reading only <plan-dir>/.mode let a slug plan
 * silently exempt itself: initPlan writes no .mode unless the operator asked
 * for a mode, so creating a plan turned the project's policy off in one
 * agent-invocable call.
 *
 * Strictness-RAISING tokens (autonomous, gate, inject-smart) are effective when
 * EITHER file carries them: a slug may go stricter than the project asked, it
 * can never go looser. The single strictness-LOWERING token (plan-guard-off)
 * survives only when the slug carries it AND, where a root .mode exists, that
 * file carries it too, so a slug cannot switch off a protection the project
 * kept on.
 *
 * A malformed ROOT .mode returns null, the same "not allowed" signal a
 * malformed slug .mode already produces. That is the fail-closed reading: the
 * committed policy is unreadable, so verifyPlan refuses the plan ("unsafe mode
 * marker") instead of proceeding as if the project had asked for nothing.
 *
 * With no root .mode the effective set is byte-identical to the slug's, which
 * is the invariant existing projects depend on. Root scope has no second
 * source at all: <root>/.mode already IS the plan's .mode there.
 */
export declare function modeTokens(root: string, planDir: string): string[] | null;
export type Verified = {
    ok: true;
    plan: Buffer;
    mode: string;
} | {
    ok: false;
    reason: string;
};
/** Read task_plan.md and enforce the v3 attestation contract. */
export declare function verifyPlan(root: string, planDir: string): Verified;
/** The per-turn injection block for a resolved plan. */
export declare function buildContext(root: string, planDir: string): string;
/** What the compaction summary must carry so the continuation can resume. */
export declare function compactionNote(root: string, planDir: string): string;
export declare function gateCounts(text: string): {
    total: number;
    complete: number;
    in_progress: number;
    pending: number;
};
export declare function firstInProgressPhase(text: string): string;
export declare function ledgerLineCount(planDir: string): number;
/** Returns the continuation message when the stop must be held, otherwise null. */
export declare function evaluateGate(root: string, planDir: string, env: Env): string | null;
export declare function slugify(name: string): string;
/** First skill directory that carries templates/task_plan.md, in OpenCode's own discovery order. */
export declare function findSkillDir(_root: string, env: Env): string | null;
export type InitResult = {
    ok: boolean;
    error?: string;
    project_dir: string;
    plan_dir?: string;
    plan_id?: string;
    created?: string[];
    existing?: string[];
    mode?: string;
    marker?: string;
    attestation?: string;
    skill_root?: string | null;
};
export declare function writeAttestation(root: string, planDir: string): string;
export declare function applyV3Mode(root: string, planDir: string, mode: "autonomous" | "gated"): {
    marker: string;
    attestation: string;
};
export declare function initPlan(root: string, opts: {
    name?: string;
    template?: string;
    mode?: string;
}, env: Env): InitResult;
export type StatusResult = {
    exists: boolean;
    message?: string;
    project_dir: string;
    plan_dir?: string;
    plan_id?: string;
    mode?: string;
    attested?: boolean;
    current_phase?: string;
    counts?: ReturnType<typeof gateCounts>;
    conflicts?: string[];
};
export declare function extractCurrentPhase(text: string): string;
export declare function summarizeStatus(root: string, env: Env): StatusResult;
export declare function checkComplete(root: string, env: Env): {
    complete: boolean;
    message: string;
    plan_id?: string;
    counts?: ReturnType<typeof gateCounts>;
};
