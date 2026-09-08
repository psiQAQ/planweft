import * as fs from "node:fs"
import * as os from "node:os"
import * as path from "node:path"
import { afterEach, beforeEach, expect, it } from "vitest"
import { PlanningWithFiles } from "../src/index.js"
import { findSkillDir } from "../src/core.js"

let root: string
const saved: Record<string, string | undefined> = {}
beforeEach(() => {
  root = fs.mkdtempSync(path.join(os.tmpdir(), "pw-workflow-"))
  for (const key of ["PLANNING_DISABLED", "PWF_PLAN_ROOT", "PLAN_ID"]) {
    saved[key] = process.env[key]
    delete process.env[key]
  }
})
afterEach(() => {
  for (const [key, value] of Object.entries(saved)) {
    if (value === undefined) delete process.env[key]
    else process.env[key] = value
  }
  fs.rmSync(root, { recursive: true, force: true })
})

it("reminds once without a plan, states scope boundaries, and writes no project files", async () => {
  fs.writeFileSync(path.join(root, "user.md"), "user bytes\r\n")
  const client = { session: { get: async () => ({ data: { directory: root } }) } }
  const hooks = await PlanningWithFiles({ client, directory: root } as never)
  const input = { sessionID: "new" }
  const output = { message: { id: "m" }, parts: [] as Array<{ text: string; synthetic: boolean }> }
  await hooks["chat.message"]!(input as never, output as never)
  await hooks["chat.message"]!(input as never, output as never)
  expect(output.parts).toHaveLength(1)
  expect(output.parts[0].synthetic).toBe(true)
  for (const boundary of ["project-docs", "multi-step implementation", "Simple tasks", "read-only", "diagnosis", "planning mode", "must not initialize", "project rules take precedence"]) {
    expect(output.parts[0].text).toContain(boundary)
  }
  expect(fs.readdirSync(root)).toEqual(["user.md"])
  expect(fs.readFileSync(path.join(root, "user.md"), "utf8")).toBe("user bytes\r\n")
  process.env.PLANNING_DISABLED = "1"
  const disabled = { message: { id: "m2" }, parts: [] }
  await hooks["chat.message"]!(input as never, disabled as never)
  expect(disabled.parts).toEqual([])
})

it("uses installed templates instead of similarly named project files", () => {
  const hostile = path.join(root, ".agents/skills/project-docs/templates")
  fs.mkdirSync(hostile, { recursive: true })
  fs.writeFileSync(path.join(hostile, "task_plan.md"), "project replacement")
  const bundled = findSkillDir(root, {})!
  expect(bundled).toBeTruthy()
  expect(bundled.startsWith(root)).toBe(false)
  expect(fs.existsSync(path.join(bundled, "templates/task_plan.md"))).toBe(true)
  expect(findSkillDir(root, { PLANNING_WITH_FILES_SKILL_ROOT: path.dirname(hostile) })).toBe(path.dirname(hostile))
  expect(findSkillDir(root, { PLANNING_WITH_FILES_SKILL_ROOT: path.join(root, "absent") })).toBe(null)
})

it("does not treat a rejected explicit plan binding as an unplanned task", async () => {
  const plan = path.join(root, ".planning/2026-09-08-selected")
  fs.mkdirSync(plan, { recursive: true })
  fs.writeFileSync(path.join(plan, "task_plan.md"), "# Explicit selection\n")
  const client = { session: { get: async () => ({ data: { directory: root } }) } }
  const hooks = await PlanningWithFiles({ client, directory: root } as never)
  for (const selector of ["missing", "../outside", "2026-09-08-selected"]) {
    process.env.PLAN_ID = selector
    const output = { message: { id: selector }, parts: [] as Array<{ text: string }> }
    await hooks["chat.message"]!({ sessionID: "bound" } as never, output as never)
    if (selector === "2026-09-08-selected") {
      expect(output.parts[0]?.text).toContain("Explicit selection")
    } else {
      expect(output.parts).toEqual([])
    }
  }
  expect(fs.readdirSync(root)).toEqual([".planning"])
})
