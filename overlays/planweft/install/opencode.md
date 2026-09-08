Use `dist/opencode/planweft/`, a precompiled **OpenCode V1** package.
The local package is named `opencode-planweft`; no public npm package is
assumed to exist.

1. Copy the complete package to your project's
   `.opencode/packages/opencode-planweft/`.
2. In that copied package directory, run `npm ci --omit=dev --ignore-scripts`
   to install locked runtime dependencies without changing your application
   package.json or compiling TypeScript.
3. Copy its complete `skills/project-docs/` directory to
   `.opencode/skills/project-docs/`. Optionally copy `commands/pw-*.md` to
   `.opencode/commands/`.
4. Create `.opencode/plugins/planweft.ts` with:

   ```typescript
   export { PlanningWithFiles } from "../packages/opencode-planweft/dist/index.js"
   ```

   Alternatively, adapt `install/loader-template.ts` to the absolute file URL of
   the package's `dist/index.js`. Keep that source package in place. Register only
   one loader; do not also register an npm copy of the same plugin.
5. Restart OpenCode. Check `project-docs` and `pw_init` / `pw_status` / `pw_check`.
   Normal installation does not require TypeScript compilation or development dependencies.

For user scope, use the same `packages/`, `plugins/`, `skills/` and optional
`commands/` layout under `~/.config/opencode/`.

To update, replace the complete plugin-owned package and Skill/command copies,
reinstall the locked runtime dependencies inside that package, then restart. To uninstall, remove only these paths and the loader; keep shared
configuration, project plans and evidence.

After an actual npm release, use the published versioned package in OpenCode's
`plugin` configuration instead of the local loader. The release preparer maps a
real scope to `@scope/planweft-opencode`. Explicitly change that version to
upgrade, or remove the entry to uninstall. Skill discovery remains separate:
deploy the complete Skill from the same package version to the path above.

This V1 adapter uses `session.idle` follow-ups for gated continuation; it cannot
block completion of the original turn. See the [official plugin guide](https://opencode.ai/docs/plugins/).
