[简体中文](INSTALL.md) | [English](INSTALL.en.md)

> Package: **opencode**. Use this host's installation section.

Commands target candidate RC15 and require confirming its publication in the official registry first. RC14 was published, but independent maintenance review found scope violations and inaccurate records. RC15 changes entry selection before exploration and provides named planning-variable lookups; its actual behavior requires new validation. Candidate publication and installer checks do not prove the five-host model gates passed; historical latest=RC1 is not a stable release. Known-source checks do not guarantee arbitrary custom-loader detection; updates do not remove other installation channels.

## Unified installer (0.4.0 candidate)

The only npm package is `planweft`. Run the remote commands below only after the corresponding version is published;
the repository release evidence states current acceptance status. Full native integration is the default, with project scope.
Use `--skill-only` explicitly for a complete portable Skill; it does not register plugin hooks.

```bash
npx planweft@0.4.0 add -a claude -a pi
npx planweft@0.4.0 add -a codex --global
npx planweft@0.4.0 add -a opencode --skill-only --symlink
npx planweft@0.4.0 list
npx planweft@0.4.0 doctor
npx planweft@0.4.0 update -a pi
npx planweft@0.4.0 remove -a pi
```

| Option | Default | Purpose |
| --- | --- | --- |
| `-a / --agent` | Interactive selection | Repeat for multiple platform IDs; required in non-interactive use |
| `--project / --global` | project | Project or user scope; unsupported scopes fail without escalation |
| `--skill-only` | Off | Complete portable Skill without another host's executable frontmatter |
| `--copy / --symlink` | Prefer links | Auto mode reports copy fallback; explicit symlink failures are errors |
| `--dsh-profile NAME` | headless | User-level profile for full DSH integration; updates retain the installed profile |
| `--dry-run` | Off | Show choices and paths without installation or state writes |
| `--source FILE.tgz` | Exact npm version | Local npm artifact for validation; identity/version must match the running CLI |

Pi project package operations retain native trust checks. For an untrusted project, explicitly add `--approve-pi-project` to pass `--approve` for this Pi command only. This trusts project-local files for that command; it is off by default and does not change other hosts’ trust.

Platform IDs: `codex claude pi opencode hermes cursor gemini copilot mastracode kiro continue factory codebuddy agents dsh`.
Requires Node.js 22+; Node.js 24 LTS is recommended. Runtime helpers may additionally require Python 3, Bash or PowerShell.

Project versions live in `.planweft/versions/`, with receipts in `.planweft/installations.json`. User storage uses
`$XDG_DATA_HOME/planweft` (default `~/.local/share/planweft`), or LocalAppData on Windows. `PLANWEFT_HOME` overrides
user storage, not native plugin scope. Exclude project `.planweft/` from Git. Each version retains resolved npm dependencies
and full resources independently of temporary npx caches.

`update` targets the running CLI version; run an older CLI's update command to roll back. Existing copy/symlink and
skill-only choices are retained. Switching full integration and Skill-only requires remove then add. User modifications,
foreign files, duplicate planning plugins and integrity failures prevent replacement. `doctor` reports actual state.
Removal retains version storage for rollback. An interrupted operation may leave `.operation-lock`; inspect the receipt
and filesystem and confirm no installer is running before manually removing this empty lock directory.

CLI-owned catalogs use separate host/scope hashes; the public Git marketplace is still `planweft`. Marketplace registration
may be user-wide while plugin enablement is project-scoped; receipts distinguish these operations. Codex, Copilot and
Gemini full integrations do not offer project installation. Host caches remain native; copy/symlink describes CLI-managed
components only. Pi uses the full local package; OpenCode uses one local loader and a paired Skill. Do not activate the same
plugin through a second npm/native route. GUI actions and Mastra hook merging remain manual, not installed. Hermes full
installation is blocked by its default scanner; no bypass is provided. CLI-managed Gemini replacement currently requires
remove/add; its native Git channel still supports native update.

To migrate `program-design`, `personal` or `program-design-local`, inspect and remove old execution hooks using their
original installation channel, then install PlanWeft. `$project-docs` remains; auxiliary `pd-` commands become `pw-`, and
`pd_` tools become `pw_`. The installer does not uninstall the old plugin or original PWF automatically. Project plans,
approved requirements, user changes and PWF state formats remain unchanged.

# PlanWeft 0.3.0 Installation, Updates and Removal

This release provides `dist/<host>/planweft/` directly and does not generate ZIP files. The 14 hosts are `codex`, `claude`, `pi`, `opencode`, `hermes`, `cursor`, `gemini`, `copilot`, `mastracode`, `kiro`, `continue`, `factory`, `codebuddy` and `agents`. Select the complete directory for one host; do not combine packages from different platforms.

In the examples, `/abs/repo` is the source repository root, `/abs/package` is the selected `dist/<host>/planweft` directory, and `/abs/project` is the target project. Replace them with actual absolute paths. The repository contains six host-specific marketplace catalogs, all named `planweft`. **Register `/abs/repo` as the marketplace source.** A platform directory is the plugin payload and cannot universally serve as a marketplace. A standalone package supports separate directory registration only if it actually contains its own catalog.

These instructions describe the delivered interfaces and official capabilities; they do not imply that every host or operating system has passed live testing. Actual validation results are recorded separately. The publication target is `https://github.com/psiQAQ/planweft` and the only npm name is `planweft`. Git commands require the corresponding branch to have been pushed; npm commands require the named version to exist. Replace `REPOSITORY_URL` or `OWNER/REPO` with that repository only once its contents are available.

## Before installation and when updating

Build and verify from the source repository:

```bash
python3 scripts/build-plugin.py
python3 scripts/build-plugin.py --verify
```

An ordinary build uses the Python 3 standard library and fixed repository inputs. It does not install a host, compile TypeScript, change personal configuration or publish anything. `dist/manifest.json` records directory contents, file digests and executable bits; `--verify` checks missing files, extra files and permission drift. If you already have a complete release directory, proceed directly to your host's installation instructions.

Keep every script, template, reference, `LICENSE`, `UPSTREAM.json` and hidden directory. Do not copy only `SKILL.md`, or use a `*` glob that omits hidden files. Before replacing an existing directory with the same name, save local changes. Replace the complete directory owned by this plugin and remove obsolete files from the previous version. Merge or remove only this plugin's entries in shared configuration. Installation, updates and removal preserve project plans, attestations, ledgers and long-term documents.

Updates are explicit by default: first obtain the new source or refresh the native catalog, then update the plugin, and finally reload as required by the host. A pinned version or SHA does not advance to the next version by itself. Use the native Git or npm sources below for continued updates. A local copy changes only when explicitly replaced; a local path reference requires its source directory to remain available. There is no shared background updater.

Enable only one set of planning execution hooks. Installing PlanWeft does not uninstall PWF. Check for old standalone Skills, project hooks and plugins with the same name from other sources. Confirm that `project-docs` is actually read and that the selected plan path is correct before initializing a plan in an authorized maintenance task. Successful installation, loading in the current session and hook trust are separate states.

Shell routes require the host to find the selected interpreter and Python 3. On Windows, use the PowerShell or launcher configuration supported by the host. Preserve `.sh` executable bits; invoke manual helper scripts on a `noexec` filesystem through explicit `sh` or `bash`. Historical 0.2.0 validation found that uutils `mkdir` 0.8.0 did not reliably support concurrent directory locks, while GNU `mkdir` 9.7 passed the comparison. Packaging changes do not remove that environment limitation. Do not maintain one plan concurrently in an environment known to have unreliable locks.

## Codex

The repository's `.agents/plugins/marketplace.json` points to the Codex package. `plugins/planweft/` is a retained generated compatibility mirror, not another manually maintained source tree.

```bash
codex plugin marketplace add /abs/repo
codex plugin add planweft@planweft
codex plugin list
```

To update, first obtain the new repository contents and verify the distributions, then run:

```bash
codex plugin marketplace upgrade planweft
codex plugin remove planweft@planweft
codex plugin add planweft@planweft
```

Explicitly use `$project-docs` in a new session. This route does not use another host's `--scope` argument. Inspect and trust the current definitions in `/hooks`; review them again when an update changes their digest. The complete plugin locates assets through `PLUGIN_ROOT`. Copying a Skill into the global Skills directory does not register plugin hooks. [Official hooks documentation](https://learn.chatgpt.com/docs/hooks)

Uninstall with `codex plugin remove planweft@planweft`, then check `codex plugin list`. A 0.2.0 installation may use `planweft@personal` or `planweft@planweft-local`. Remove the actual old ID shown in the list, then install the new ID to avoid duplicate hooks. Remove the old marketplace only if no other plugins depend on it.

## Claude Code

Use the repository's `.claude-plugin/marketplace.json`. These CLI examples use user scope. Use `project` for shared project configuration, or `local` for this local project only.

```bash
claude plugin marketplace add /abs/repo
claude plugin install planweft@planweft --scope user
claude plugin list
```

Keep the installation scope when updating or removing:

```bash
claude plugin marketplace update planweft
claude plugin update planweft@planweft --scope user
# To uninstall:
claude plugin uninstall planweft@planweft --scope user
```

After installation or an update, use `/reload-plugins` or start a new session as prompted, and check `/planweft:project-docs`. For a single development session, use `claude --plugin-dir /abs/repo/dist/claude/planweft`; do not enable it alongside a persistent installation. Once a Git marketplace is published, replace the registration source with the actual repository. Increment the plugin version for each release so cached installations refresh. Marketplace automatic updates are not enabled by default. [Official marketplaces](https://code.claude.com/docs/en/plugin-marketplaces), [plugin management](https://code.claude.com/docs/en/discover-plugins)

## Pi

`dist/pi/planweft` is itself a `pi-package`; its root `package.json` declares both the Skill and Extension. Run in the target project:

```bash
pi install -l /abs/repo/dist/pi/planweft
pi list
```

`-l` writes the project's `.pi/settings.json`; omitting it writes the user's `~/.pi/agent/settings.json`. A local path records a reference without copying files, so keep the source directory. After updating that directory, use `/reload` or restart. Remove a project installation with `pi remove -l /abs/repo/dist/pi/planweft`; omit `-l` for a user installation.

After publication, use the single unscoped package:

```bash
pi install -l npm:planweft@0.4.0
pi install -l npm:planweft@NEW_VERSION
# Remove the project installation:
pi remove -l npm:planweft@NEW_VERSION
```

Pin a version with `npm:planweft@VERSION`; upgrade by running `pi install -l` again with the new version. In the current official CLI, bare `pi update` updates Pi itself, while `pi update --extensions` updates packages; a targeted update is shown above. Pi handles dependencies for npm and Git installations. A local package does not require users to run development tests. [Official packages](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/packages.md)

After loading, check `/skill:project-docs` and `/pw-plan-status`. Only explicit `/pw-plan-execute` enables injection and the execution loop; `/pw-plan-execute reset` restores passive behavior. The configuration key remains `planningWithFiles`. `PWF_MODE` supports `auto`, `parity`, `cache-safe` and `notify`; execution loops retain the platform's limitations.

## OpenCode V1

`dist/opencode/planweft` is an npm package with precompiled `dist/index.js`, locally named `opencode-planweft`. Ordinary installation does not compile TypeScript. The local-copy route requires installing runtime dependencies inside the plugin's own directory.

1. Copy the complete package to the project's `.opencode/packages/opencode-planweft/`.
2. Run `npm ci --omit=dev --ignore-scripts` inside that copied, separate package directory. This installs runtime dependencies only; it does not change the application's root package.json or run `npm run build`.
3. Copy the package's complete `skills/project-docs/` directory to the project's `.opencode/skills/project-docs/`.
4. Write the following loader to the project's `.opencode/plugins/planweft.ts`. The package also includes an absolute file URL template in `install/loader-template.ts`. Choose one loader route; do not register both.

```typescript
export { PlanningWithFiles } from "../packages/opencode-planweft/dist/index.js"
```

If you need commands, copy the package's `commands/pw-*.md` files to `.opencode/commands/`. For user scope, use the same `packages/`, `plugins/`, `skills/` and `commands/` hierarchy under `~/.config/opencode/`. After restarting, check `project-docs`, `pw_init` / `pw_status` / `pw_check`, and the optional `/pw-pwf` and `/pw-pwf-status` commands.

For local updates, replace the complete separate package and its Skill and command copies, reinstall the locked runtime dependencies in the separate package, then restart. To uninstall, remove only the loader, separate package, Skill and commands installed by this procedure; preserve the shared `.opencode` directory. Assets come from the installed package; plans are written in the target project. These locations are not interchangeable.

After npm publication, the native configuration can use `"plugin": ["planweft@VERSION"]`. To upgrade, explicitly change the version and restart. To uninstall, remove that entry and the manually installed Skill and commands. Preserve existing configuration and change only this plugin's entries. Choose either this route or the manual loader. The host's package manager installs runtime dependencies for the npm route. Loading npm plugin code does not imply Skill discovery; deploy the complete `skills/project-docs/` directory from the same version to the discovery directory above. [Official plugins](https://opencode.ai/docs/plugins/), [Skills](https://opencode.ai/docs/skills/)

This is the V1 adapter. Gated mode continues through a follow-up after `session.idle`; it cannot prevent the host from finishing the original turn. Claude Skill frontmatter hooks are not OpenCode's execution entry point.

## Hermes

**Recorded validation limitation (2026-09-08):** Official Hermes v0.21.1, source commit `9fd44b4dfc44138b9e5d5689acb56c438364ff7b`, could run plugin management with an isolated configuration and no authentication. However, the default Plugin Guard rejected Git installation during the 0.3.0 delivery checks: the first package was rated dangerous with 42 findings; the final directory, after a language-resource path fix, was still rated dangerous with 41 findings. Both native installation attempts are **Failed**. Update, rollback and removal are **Not Run** because installation did not finish. These counts describe the package contents tested at that time; the bilingual documentation revision did not rerun Hermes scanning. The original rejection evidence is retained. Scanning was not disabled, text was not changed to evade rules, and manual copying was not used to relabel rejection as success. The following describes officially supported discovery layouts and management interfaces; it is not a promise that this package currently installs successfully through the native route.

Copy the complete `dist/hermes/planweft/` directory to `<HERMES_HOME>/plugins/planweft/` in the active Hermes profile. Then copy its complete `skills/project-docs/` directory to **the same** `<HERMES_HOME>/skills/project-docs/`. Use the user root selected by the host configuration; do not assume every operating system uses `~/.hermes`.

```bash
hermes plugins enable planweft
hermes plugins list
```

Restart Hermes and check the Skill and native commands. Plugin enablement and capability grants are separate. The host asks again when an update introduces capabilities. Update manually copied local packages by replacing the two plugin-owned directories above; `plugins update` does not fetch arbitrary local copies. Uninstall with `hermes plugins remove planweft` and remove the separately copied Skill.

For remote publication, this project places `plugin.yaml` and `__init__.py` directly at the root of the `release/hermes` branch. The current official installer supports Git subdirectories, but extracting a subdirectory does not retain the repository root's `.git`, so `plugins update` cannot pull an unpinned installation there. Publishing a package-root tree avoids this problem. Hermes accepts only an immutable full 40-character SHA for `--ref`:

```bash
hermes plugins install OWNER/REPO --ref FULL_40_CHARACTER_SHA --enable
# Upgrade the pinned plugin: select a new release-branch commit explicitly
hermes plugins install OWNER/REPO --force --ref NEW_FULL_40_CHARACTER_SHA --enable
```

`hermes plugins update planweft` refuses to move a pinned plugin. `hermes skills install` does not offer an equivalent `--ref` pin. For a reproducible installation, copy `skills/project-docs/` from a separate checkout at the same SHA, record the Skill/plugin SHA pairing, and replace both when upgrading. An unpinned Skill Hub import cannot substitute for this pairing. [Official plugin installation, updates and removal](https://hermes-agent.nousresearch.com/docs/user-guide/features/plugins/)

Project-level plugins also require `HERMES_ENABLE_PROJECT_PLUGINS=1`, starting from the project and explicitly enabling the plugin. Desktop uses the user-level route. Continuation through `pre_verify` is subject to the host's trigger conditions and attempt limits; it is not a native Stop rejection.

## Cursor

This package uses `.cursor-plugin/plugin.json`. For local development installation, place the complete `dist/cursor/planweft/` directory at `~/.cursor/plugins/local/planweft/`. Then use Developer: Reload Window or restart, and inspect Customize. Update by replacing that complete directory. Uninstall by removing this plugin's directory and reloading. Do not also copy old project hooks and cause duplicate execution.

For team Git distribution, import the repository through Dashboard. Cursor reads the repository's `.cursor-plugin/marketplace.json`; installation and management use the Customize/Marketplace UI. Team scope and administrator policies depend on the actual interface. Check for new versions after an explicit Refresh. Auto Refresh requires the GitHub App, and public marketplace listing requires official review. No general `cursor plugin marketplace add/update` CLI has been identified; do not reuse Claude commands. [Official plugins](https://cursor.com/docs/plugins)

## Gemini CLI

The root `gemini-extension.json`, `skills/` and `hooks/hooks.json` form an Extension. Native `${extensionPath}` resolves bundled hooks and assets; the event supplies the target project.

```bash
gemini extensions install /abs/repo/dist/gemini/planweft
gemini extensions list
```

Keep the source directory after a local installation. Once the source has a new version, run `gemini extensions update planweft`; version detection depends on changes to the local source manifest. For development, use `gemini extensions link /abs/repo/dist/gemini/planweft`. Local sources do not accept `--ref` or `--auto-update`. Check `/skills list` in a new session. Uninstall with `gemini extensions uninstall planweft`.

Git Extensions require the manifest at the repository root and have no general Git subdirectory installation argument. This project provides the required layout through a dedicated `release/gemini` branch. After actual publication:

```bash
gemini extensions install REPOSITORY_URL --ref release/gemini
gemini extensions update planweft
```

An explicit update follows new commits on that branch. An immutable ref does not automatically advance across versions. `--auto-update` is not enabled by default. Installation is generally user-level; enable/disable can use the host's workspace or user scope. Disabling is different from uninstalling. [Official Extension reference](https://geminicli.com/docs/extensions/reference/), [releasing and updates](https://geminicli.com/docs/extensions/releasing/)

## GitHub Copilot CLI

The repository's `.github/plugin/marketplace.json` points to the Copilot package with a root `plugin.json`:

```bash
copilot plugin marketplace add /abs/repo
copilot plugin install planweft@planweft
copilot plugin list
```

Git marketplace updates and removal:

```bash
copilot plugin marketplace update planweft
copilot plugin update planweft
# Uninstall:
copilot plugin uninstall planweft
```

A path plugin in a local directory marketplace loads in place. After updating its source directory, use `/restart` or a new session; a copied-cache update is not required for this route. With Copilot CLI 1.0.83, uninstalling a local path plugin disables it and retains both source files and a disabled record. When the entire source is no longer needed, run `copilot plugin marketplace remove planweft` to remove its listing. Direct installation is also supported through `copilot plugin install /abs/repo/dist/copilot/planweft`; do not install it again through the catalog. Plugin installation does not expose a comparable project `--scope`: the official argument applies to single-Skill installation from a file or URL. Check the active user/profile. CLI results do not establish that IDE or Coding Agent behavior has passed. [Official CLI plugin reference](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-plugin-reference)

## Factory / Droid

The repository's native catalog is `.factory-plugin/marketplace.json`. This release provides a Skill-only plugin wrapper and does not register Factory execution hooks. **Droid derives the actual registered marketplace name from the source path/repository and pin, so it may differ from the catalog's `name`.** Check the registered name first:

```bash
droid plugin marketplace add /abs/repo
droid plugin marketplace list
```

Replace `REGISTERED_NAME` below with the actual name in the list. A local directory named `planweft` normally registers as `planweft`; the isolated validation source directory was named `source`, so its actual plugin ID was `planweft@source`.

```bash
droid plugin install planweft@REGISTERED_NAME --scope project
droid plugin list --scope project
# Explicit update:
droid plugin marketplace update REGISTERED_NAME
droid plugin update planweft@REGISTERED_NAME --scope project
# Uninstall:
droid plugin uninstall planweft@REGISTERED_NAME --scope project
```

Use `--scope user` for a user installation and keep the scope consistent when updating or uninstalling. Check `project-docs` in a new session. `marketplace add` requires a catalog source, not a bare plugin directory. Git publication uses the complete repository containing both the native catalog and payload. With an isolated configuration, Droid 0.213.0 passed local directory catalog installation, an A→B update with added/modified/deleted files, rollback to A and removal. This validates plugin management and the active cache, not model reading or remote Git installation. [Official plugins](https://docs.factory.ai/harness/plugins)

## CodeBuddy

The repository's native catalog is `.codebuddy-plugin/marketplace.json`. This release also registers only Skills and does not claim automatic execution of frontmatter hooks.

```bash
codebuddy plugin marketplace add /abs/repo
codebuddy plugin install planweft@planweft --scope project
# Explicit update:
codebuddy plugin marketplace update planweft
codebuddy plugin update planweft@planweft --scope project
# Uninstall and preserve plugin data:
codebuddy plugin uninstall planweft@planweft --scope project --keep-data
```

Scopes are `user`, `project` and `local`; keep update/removal scope consistent with installation. Check after `/reload-plugins` or a new session. Increment the plugin version for each release to avoid continued use of an old cached package. `/plugin` can manage automatic updates, but this distribution does not enable them by default. A Git catalog suits this repository's relative payload paths better than a standalone HTTP JSON file. [Official reference](https://www.codebuddy.ai/docs/cli/plugins-reference), [marketplaces](https://www.codebuddy.ai/docs/cli/plugin-marketplaces)

## Kiro IDE and CLI v3

The root `plugin.json` in `dist/kiro/planweft` defines a Skill-only Power. In the IDE, use Powers → Add Custom Power and select this **complete local directory**, then inspect the installed entry in Powers. Kiro CLI v3 automatically discovers IDE-installed Powers; no additional CLI plugin copy is needed. [Official creation guide](https://kiro.dev/docs/powers/create/), [installation](https://kiro.dev/docs/powers/installation/), [CLI v3 auto discovery](https://kiro.dev/docs/cli/v3/new-features/#powers-auto-pickup)

After updating the local source, use the Power's Check for updates / Install updates actions. If the current version does not detect a local-source change, uninstall the Power and import the new directory. Uninstall through the Powers management UI, then start a new session. The official installation page supports Git repositories with multiple Power subdirectories. This repository may retain its multiple-host layout when published remotely, but the exact remote subdirectory selection interaction has not been tested. This guide does not present a `tree/.../dist/...` URL as verified installation syntax.

The current official CLI and slash command references do not expose Power install, update or removal commands. CLI support covers automatic discovery after IDE installation. [CLI commands](https://kiro.dev/docs/reference/cli-commands/), [slash commands](https://kiro.dev/docs/reference/slash-commands/)

A Power provides no default execution hooks. Only after authorization to create project records and selection of the Kiro layout, explicitly run `assets/scripts/bootstrap.sh` from the loaded Skill's directory, with the target project as the working directory (`.ps1` on Windows). It creates missing `.kiro/plan/` three-file records and `.kiro/steering/planning-context.md`. Resolve assets from the actual installation path; do not hard-code the project's `.kiro/skills`. Do not create a competing plan when another task plan already exists or the task is read-only. This layout is not the canonical `.planning/<id>` selector.

## Continue, Mastra Code and generic Agent Skills

These three routes retain complete Skill/project-configuration copies and do not provide a shared native marketplace updater.

| Host | Installation mapping | Updating, loading and removal |
| --- | --- | --- |
| `continue` | Package `.continue/skills/project-docs/` → project or user `.continue/skills/project-docs/`; optionally include this plugin's prompts from `.continue/prompts/` | Replace the complete Skill/prompt copies and start a new session. Remove only this plugin's paths. Check CLI `/skills` and invoke `/skill-project-docs` explicitly; IDE prompts and CLI Skills are validated separately. |
| `mastracode` | `.mastracode/skills/project-docs/` → project `.mastracode/skills/`; merge this plugin's events from the package's `.mastracode/hooks.json` into the target hooks.json | Replace the Skill and review hook differences, then reload configuration with `/hooks` or start a new session. Remove only the Skill and corresponding hook entries. User-level Skills can live in `~/.mastracode/skills/`; do not copy project-relative hooks unchanged into global configuration. |
| `agents` | `.agents/skills/project-docs/` → project or user `.agents/skills/project-docs/` | The selected host must support this discovery path. Replace the complete copy and reload. Remove only this Skill; there is no general plugin/update command. |

Mastra Code officially supports `.mastracode/skills` and `.mastracode/hooks.json`, with `/hooks` to reload hooks. `/update` updates the host itself, not this plugin. [Official configuration](https://code.mastra.ai/configuration)

Continue CLI's `/import-skill <url-or-name>` asks a model to help download and copy a Skill. It does not record a package source for continued updates and is not a version-pinned installer. The official repository currently states that active maintenance has ended; this does not justify inventing a shared updater. Retain a version-controlled installation source, explicitly update its checkout, and replace the copies. [Official Skills loader](https://github.com/continuedev/continue/blob/main/extensions/cli/src/util/loadMarkdownSkills.ts), [import implementation](https://github.com/continuedev/continue/blob/main/extensions/cli/src/tools/skills.ts), [maintenance status](https://github.com/continuedev/continue)

## Runtime capabilities and recovery

Directories, manifests and native installation commands solve distribution; they do not make all host lifecycles equivalent. Some inherited behavior in Cursor, Gemini, Copilot and Mastra still centers on a root `task_plan.md`. Named-plan, read-only and disable support depend on the corresponding implementation and its actual validation records. For a complete shutdown, use the host's disable mechanism. `PLANNING_DISABLED=1` is sufficient only on routes where that implementation has been verified.

If an update fails, restore the previous verified complete package, reinstall/reload at the same scope and recheck hook trust. Do not overlay old files on a newer directory and leave a mixed version. Rolling back an installation does not automatically roll back plans or documents; handle project-state differences separately for the task. Existing `PLAN_ID`, `PWF_*`, three-file records, `.planning`, attestation and ledger formats remain compatible. There is no general state migrator.

## DeepSeek Harness (DSH)

The adapter provides a native DSH bundle, complete Skill and the official Claude command-hook bridge. DSH `0.1.2-rc.1` was tested; native plugin management also requires `pnpm` on PATH. The npm commands below become available after the candidate is published.

Full integration belongs to a user-level **profile**, defaulting to `headless`; select `web` explicitly when needed. The installer manages one DSH profile at a time. Updates retain the recorded profile; remove it before switching. The native source links to the persistent version directory through DSH/pnpm, independently of the CLI's `--copy` option. Starting the selected profile loads its bundled Skill and hooks.

```bash
npx planweft@0.4.0 add -a dsh --global --dsh-profile headless
npx planweft@0.4.0 doctor -a dsh --global
npx planweft@0.4.0 update -a dsh --global
npx planweft@0.4.0 remove -a dsh --global
```

Alternatively use DSH native commands with the single npm package. This is a separate ownership channel; do not mix it with the PlanWeft CLI:

```bash
dsh plugin --profile headless add planweft@0.4.0
dsh --profile headless --dump-config
dsh --profile headless "Use project-docs for this maintenance task."
dsh plugin --profile headless remove planweft
```

A local platform directory can be installed with `dsh plugin --profile headless add file:/absolute/path/to/dist/dsh/planweft`. Its manifest declares `dsh.bundle.patch`; no marketplace is involved. Use `add` with an exact new or old version for upgrades or rollback, then start a new session. No background update is enabled. Removal drops only the PlanWeft dependency and bundle, preserving the profile, other user settings and project records.

Project-level Skill-only installation:

```bash
npx planweft@0.4.0 add -a dsh --skill-only
npx planweft@0.4.0 doctor -a dsh
npx planweft@0.4.0 update -a dsh
npx planweft@0.4.0 remove -a dsh
```

Add `--global` to every command for user-level Skill-only management. `--copy`, `--symlink` and `--dry-run` retain their shared semantics.
Project Skills live in `.dsh/skills/project-docs/` at the nearest Git root. Run commands from that root so receipts and locks share the same project; without Git, use the invoking directory.
User Skills live in `$DSH_HOME/skills/project-docs/`, defaulting to `~/.dsh/skills/project-docs/`, with native tilde expansion.
For manual installation copy the complete `dist/dsh/planweft/skills/project-docs/` directory; the CLI does not adopt existing copies. Same-name Skills follow DSH provider priorities.

Assets resolve from the installed package; task state uses each session's cwd. SessionStart, UserPromptSubmit, PostToolUse and Stop are bridged. There is no PreCompact bridge. DSH drops context-only PreToolUse output, so that reminder is not registered. Default Stop does not force continuation, and DSH does not display PWF's `systemMessage` reminder. Gated mode uses the native Stop decision channel; full model continuation acceptance has not been run. PWF refreshes the plan on each prompt; UserPromptSubmit deduplication is not claimed.
RC3 uses a private disposable temporary cache for each DSH hook; workspace-write cannot write HOME caches. The native bridge facade binds the host session ID and deduplicates PostToolUse reminders in bounded process memory. It delegates to the original sandbox executor without changing permissions or Stop payloads. Stop counters and stall ledgers remain in the selected plan. The upstream `pwf-prog` cross-call cache warning is not retained across isolated hook invocations; do not treat it as a DSH progress-regression safeguard.

Set `PLANNING_DISABLED=1` when starting a read-only host session to disable execution hooks while retaining the Skill's read-only rules. Enable one planning hook source per session. The installer refuses to overwrite foreign PlanWeft profile registrations.

Linux native install/A-B update/rollback/removal and config composition passed. Protocol probes use the real official bridge and subprocesses to check injection, project isolation, recovery and permission preservation. These are not DSH model-session or Windows/macOS results.

Sources: [official Skill provider](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/skill/skill-filesystem/README.md), [official hook bridge](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/hooks/hooks-claude-code/README.md), [CLI profiles](https://github.com/deepseek-ai/deepseek-harness/blob/master/apps/cli/README.md).

Full integration also checks home/profile patches for known planning-hook text, ignoring whole-line comments. This is a conservative hint check, not resolved runtime configuration; inspect the actual source when warned. Skill-only skips this hook-duplication check.
