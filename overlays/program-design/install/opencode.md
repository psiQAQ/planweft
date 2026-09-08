Use the **OpenCode** ZIP from this repository's `dist/`. It contains a local
source package; `opencode-program-design` has not been published to npm.

1. Copy `.opencode/packages/opencode-program-design/`,
   `.opencode/plugins/program-design.ts`, and `.opencode/skills/project-docs/`
   from the ZIP to the same paths under your target project. Keep existing
   unrelated configuration and plugins. Optionally copy `.opencode/commands/pd-*.md`.
2. In the copied `.opencode/packages/opencode-program-design/` directory, run:

   ```bash
   npm ci --ignore-scripts
   npm run build
   ```

3. Keep `node_modules/` in that local package and restart OpenCode. The shipped
   loader imports `../packages/opencode-program-design/dist/index.js`; no npm
   `plugin` registration or manually written loader is needed. Verify that
   `project-docs` and `pd_init` / `pd_status` / `pd_check` are available.

For user scope, put the same `packages/`, `plugins/`, `skills/` and optional
`commands/` directories under `~/.config/opencode/`, preserving relative paths.
Uninstall only these plugin-owned paths; keep your project plans and evidence.
