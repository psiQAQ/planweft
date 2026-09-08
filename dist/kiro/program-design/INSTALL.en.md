[简体中文](INSTALL.md) | [English](INSTALL.en.md)

> Package: **kiro**. Use this host's installation section.

# Program Design 0.3.0 Installation, Updates and Removal

This release provides `dist/<host>/program-design/` directly and does not generate ZIP files. The 14 hosts are `codex`, `claude`, `pi`, `opencode`, `hermes`, `cursor`, `gemini`, `copilot`, `mastracode`, `kiro`, `continue`, `factory`, `codebuddy` and `agents`. Select the complete directory for one host; do not combine packages from different platforms.

In the examples, `/abs/repo` is the source repository root, `/abs/package` is the selected `dist/<host>/program-design` directory, and `/abs/project` is the target project. Replace them with actual absolute paths. The repository contains six host-specific marketplace catalogs, all named `program-design`. **Register `/abs/repo` as the marketplace source.** A platform directory is the plugin payload and cannot universally serve as a marketplace. A standalone package supports separate directory registration only if it actually contains its own catalog.

These instructions describe the delivered interfaces and official capabilities; they do not imply that every host or operating system has passed live testing. Actual validation results are recorded separately. No verified public Git or npm release address is currently provided. `REPOSITORY_URL`, `OWNER/REPO` and `@scope/...` are parameters that can be replaced with usable addresses only after publication.

## Before installation and when updating

Build and verify from the source repository:

```bash
python3 scripts/build-plugin.py
python3 scripts/build-plugin.py --verify
```

An ordinary build uses the Python 3 standard library and fixed repository inputs. It does not install a host, compile TypeScript, change personal configuration or publish anything. `dist/manifest.json` records directory contents, file digests and executable bits; `--verify` checks missing files, extra files and permission drift. If you already have a complete release directory, proceed directly to your host's installation instructions.

Keep every script, template, reference, `LICENSE`, `UPSTREAM.json` and hidden directory. Do not copy only `SKILL.md`, or use a `*` glob that omits hidden files. Before replacing an existing directory with the same name, save local changes. Replace the complete directory owned by this plugin and remove obsolete files from the previous version. Merge or remove only this plugin's entries in shared configuration. Installation, updates and removal preserve project plans, attestations, ledgers and long-term documents.

Updates are explicit by default: first obtain the new source or refresh the native catalog, then update the plugin, and finally reload as required by the host. A pinned version or SHA does not advance to the next version by itself. Use the native Git or npm sources below for continued updates. A local copy changes only when explicitly replaced; a local path reference requires its source directory to remain available. There is no shared background updater.

Enable only one set of planning execution hooks. Installing Program Design does not uninstall PWF. Check for old standalone Skills, project hooks and plugins with the same name from other sources. Confirm that `project-docs` is actually read and that the selected plan path is correct before initializing a plan in an authorized maintenance task. Successful installation, loading in the current session and hook trust are separate states.

Shell routes require the host to find the selected interpreter and Python 3. On Windows, use the PowerShell or launcher configuration supported by the host. Preserve `.sh` executable bits; invoke manual helper scripts on a `noexec` filesystem through explicit `sh` or `bash`. Historical 0.2.0 validation found that uutils `mkdir` 0.8.0 did not reliably support concurrent directory locks, while GNU `mkdir` 9.7 passed the comparison. Packaging changes do not remove that environment limitation. Do not maintain one plan concurrently in an environment known to have unreliable locks.

## Codex

The repository's `.agents/plugins/marketplace.json` points to the Codex package. `plugins/program-design/` is a retained generated compatibility mirror, not another manually maintained source tree.

```bash
codex plugin marketplace add /abs/repo
codex plugin add program-design@program-design
codex plugin list
```

To update, first obtain the new repository contents and verify the distributions, then run:

```bash
codex plugin marketplace upgrade program-design
codex plugin remove program-design@program-design
codex plugin add program-design@program-design
```

Explicitly use `$project-docs` in a new session. This route does not use another host's `--scope` argument. Inspect and trust the current definitions in `/hooks`; review them again when an update changes their digest. The complete plugin locates assets through `PLUGIN_ROOT`. Copying a Skill into the global Skills directory does not register plugin hooks. [Official hooks documentation](https://learn.chatgpt.com/docs/hooks)

Uninstall with `codex plugin remove program-design@program-design`, then check `codex plugin list`. A 0.2.0 installation may use `program-design@personal` or `program-design@program-design-local`. Remove the actual old ID shown in the list, then install the new ID to avoid duplicate hooks. Remove the old marketplace only if no other plugins depend on it.

## Claude Code

Use the repository's `.claude-plugin/marketplace.json`. These CLI examples use user scope. Use `project` for shared project configuration, or `local` for this local project only.

```bash
claude plugin marketplace add /abs/repo
claude plugin install program-design@program-design --scope user
claude plugin list
```

Keep the installation scope when updating or removing:

```bash
claude plugin marketplace update program-design
claude plugin update program-design@program-design --scope user
# To uninstall:
claude plugin uninstall program-design@program-design --scope user
```

After installation or an update, use `/reload-plugins` or start a new session as prompted, and check `/program-design:project-docs`. For a single development session, use `claude --plugin-dir /abs/repo/dist/claude/program-design`; do not enable it alongside a persistent installation. Once a Git marketplace is published, replace the registration source with the actual repository. Increment the plugin version for each release so cached installations refresh. Marketplace automatic updates are not enabled by default. [Official marketplaces](https://code.claude.com/docs/en/plugin-marketplaces), [plugin management](https://code.claude.com/docs/en/discover-plugins)

## Pi

`dist/pi/program-design` is itself a `pi-package`; its root `package.json` declares both the Skill and Extension. Run in the target project:

```bash
pi install -l /abs/repo/dist/pi/program-design
pi list
```

`-l` writes the project's `.pi/settings.json`; omitting it writes the user's `~/.pi/agent/settings.json`. A local path records a reference without copying files, so keep the source directory. After updating that directory, use `/reload` or restart. Remove a project installation with `pi remove -l /abs/repo/dist/pi/program-design`; omit `-l` for a user installation.

After npm publication, use the actual scope:

```bash
pi install -l npm:@scope/program-design-pi
pi update npm:@scope/program-design-pi
# Remove the project installation:
pi remove -l npm:@scope/program-design-pi
```

Pin a version with `npm:@scope/program-design-pi@VERSION`; upgrade by running `pi install -l` again with the new version. In the current official CLI, bare `pi update` updates Pi itself, while `pi update --extensions` updates packages; a targeted update is shown above. Pi handles dependencies for npm and Git installations. A local package does not require users to run development tests. [Official packages](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/packages.md)

After loading, check `/skill:project-docs` and `/pd-plan-status`. Only explicit `/pd-plan-execute` enables injection and the execution loop; `/pd-plan-execute reset` restores passive behavior. The configuration key remains `planningWithFiles`. `PWF_MODE` supports `auto`, `parity`, `cache-safe` and `notify`; execution loops retain the platform's limitations.

## OpenCode V1

`dist/opencode/program-design` is an npm package with precompiled `dist/index.js`, locally named `opencode-program-design`. Ordinary installation does not compile TypeScript. The local-copy route requires installing runtime dependencies inside the plugin's own directory.

1. Copy the complete package to the project's `.opencode/packages/opencode-program-design/`.
2. Run `npm ci --omit=dev --ignore-scripts` inside that copied, separate package directory. This installs runtime dependencies only; it does not change the application's root package.json or run `npm run build`.
3. Copy the package's complete `skills/project-docs/` directory to the project's `.opencode/skills/project-docs/`.
4. Write the following loader to the project's `.opencode/plugins/program-design.ts`. The package also includes an absolute file URL template in `install/loader-template.ts`. Choose one loader route; do not register both.

```typescript
export { PlanningWithFiles } from "../packages/opencode-program-design/dist/index.js"
```

If you need commands, copy the package's `commands/pd-*.md` files to `.opencode/commands/`. For user scope, use the same `packages/`, `plugins/`, `skills/` and `commands/` hierarchy under `~/.config/opencode/`. After restarting, check `project-docs`, `pd_init` / `pd_status` / `pd_check`, and the optional `/pd-pwf` and `/pd-pwf-status` commands.

For local updates, replace the complete separate package and its Skill and command copies, reinstall the locked runtime dependencies in the separate package, then restart. To uninstall, remove only the loader, separate package, Skill and commands installed by this procedure; preserve the shared `.opencode` directory. Assets come from the installed package; plans are written in the target project. These locations are not interchangeable.

After npm publication, the native configuration can use `"plugin": ["@scope/program-design-opencode@VERSION"]`. To upgrade, explicitly change the version and restart. To uninstall, remove that entry and the manually installed Skill and commands. Preserve existing configuration and change only this plugin's entries. Choose either this route or the manual loader. The host's package manager installs runtime dependencies for the npm route. Loading npm plugin code does not imply Skill discovery; deploy the complete `skills/project-docs/` directory from the same version to the discovery directory above. [Official plugins](https://opencode.ai/docs/plugins/), [Skills](https://opencode.ai/docs/skills/)

This is the V1 adapter. Gated mode continues through a follow-up after `session.idle`; it cannot prevent the host from finishing the original turn. Claude Skill frontmatter hooks are not OpenCode's execution entry point.

## Hermes

**Recorded validation limitation (2026-09-08):** Official Hermes v0.21.1, source commit `9fd44b4dfc44138b9e5d5689acb56c438364ff7b`, could run plugin management with an isolated configuration and no authentication. However, the default Plugin Guard rejected Git installation during the 0.3.0 delivery checks: the first package was rated dangerous with 42 findings; the final directory, after a language-resource path fix, was still rated dangerous with 41 findings. Both native installation attempts are **Failed**. Update, rollback and removal are **Not Run** because installation did not finish. These counts describe the package contents tested at that time; the bilingual documentation revision did not rerun Hermes scanning. The original rejection evidence is retained. Scanning was not disabled, text was not changed to evade rules, and manual copying was not used to relabel rejection as success. The following describes officially supported discovery layouts and management interfaces; it is not a promise that this package currently installs successfully through the native route.

Copy the complete `dist/hermes/program-design/` directory to `<HERMES_HOME>/plugins/program-design/` in the active Hermes profile. Then copy its complete `skills/project-docs/` directory to **the same** `<HERMES_HOME>/skills/project-docs/`. Use the user root selected by the host configuration; do not assume every operating system uses `~/.hermes`.

```bash
hermes plugins enable program-design
hermes plugins list
```

Restart Hermes and check the Skill and native commands. Plugin enablement and capability grants are separate. The host asks again when an update introduces capabilities. Update manually copied local packages by replacing the two plugin-owned directories above; `plugins update` does not fetch arbitrary local copies. Uninstall with `hermes plugins remove program-design` and remove the separately copied Skill.

For remote publication, this project places `plugin.yaml` and `__init__.py` directly at the root of the `release/hermes` branch. The current official installer supports Git subdirectories, but extracting a subdirectory does not retain the repository root's `.git`, so `plugins update` cannot pull an unpinned installation there. Publishing a package-root tree avoids this problem. Hermes accepts only an immutable full 40-character SHA for `--ref`:

```bash
hermes plugins install OWNER/REPO --ref FULL_40_CHARACTER_SHA --enable
# Upgrade the pinned plugin: select a new release-branch commit explicitly
hermes plugins install OWNER/REPO --force --ref NEW_FULL_40_CHARACTER_SHA --enable
```

`hermes plugins update program-design` refuses to move a pinned plugin. `hermes skills install` does not offer an equivalent `--ref` pin. For a reproducible installation, copy `skills/project-docs/` from a separate checkout at the same SHA, record the Skill/plugin SHA pairing, and replace both when upgrading. An unpinned Skill Hub import cannot substitute for this pairing. [Official plugin installation, updates and removal](https://hermes-agent.nousresearch.com/docs/user-guide/features/plugins/)

Project-level plugins also require `HERMES_ENABLE_PROJECT_PLUGINS=1`, starting from the project and explicitly enabling the plugin. Desktop uses the user-level route. Continuation through `pre_verify` is subject to the host's trigger conditions and attempt limits; it is not a native Stop rejection.

## Cursor

This package uses `.cursor-plugin/plugin.json`. For local development installation, place the complete `dist/cursor/program-design/` directory at `~/.cursor/plugins/local/program-design/`. Then use Developer: Reload Window or restart, and inspect Customize. Update by replacing that complete directory. Uninstall by removing this plugin's directory and reloading. Do not also copy old project hooks and cause duplicate execution.

For team Git distribution, import the repository through Dashboard. Cursor reads the repository's `.cursor-plugin/marketplace.json`; installation and management use the Customize/Marketplace UI. Team scope and administrator policies depend on the actual interface. Check for new versions after an explicit Refresh. Auto Refresh requires the GitHub App, and public marketplace listing requires official review. No general `cursor plugin marketplace add/update` CLI has been identified; do not reuse Claude commands. [Official plugins](https://cursor.com/docs/plugins)

## Gemini CLI

The root `gemini-extension.json`, `skills/` and `hooks/hooks.json` form an Extension. Native `${extensionPath}` resolves bundled hooks and assets; the event supplies the target project.

```bash
gemini extensions install /abs/repo/dist/gemini/program-design
gemini extensions list
```

Keep the source directory after a local installation. Once the source has a new version, run `gemini extensions update program-design`; version detection depends on changes to the local source manifest. For development, use `gemini extensions link /abs/repo/dist/gemini/program-design`. Local sources do not accept `--ref` or `--auto-update`. Check `/skills list` in a new session. Uninstall with `gemini extensions uninstall program-design`.

Git Extensions require the manifest at the repository root and have no general Git subdirectory installation argument. This project provides the required layout through a dedicated `release/gemini` branch. After actual publication:

```bash
gemini extensions install REPOSITORY_URL --ref release/gemini
gemini extensions update program-design
```

An explicit update follows new commits on that branch. An immutable ref does not automatically advance across versions. `--auto-update` is not enabled by default. Installation is generally user-level; enable/disable can use the host's workspace or user scope. Disabling is different from uninstalling. [Official Extension reference](https://geminicli.com/docs/extensions/reference/), [releasing and updates](https://geminicli.com/docs/extensions/releasing/)

## GitHub Copilot CLI

The repository's `.github/plugin/marketplace.json` points to the Copilot package with a root `plugin.json`:

```bash
copilot plugin marketplace add /abs/repo
copilot plugin install program-design@program-design
copilot plugin list
```

Git marketplace updates and removal:

```bash
copilot plugin marketplace update program-design
copilot plugin update program-design
# Uninstall:
copilot plugin uninstall program-design
```

A path plugin in a local directory marketplace loads in place. After updating its source directory, use `/restart` or a new session; a copied-cache update is not required for this route. With Copilot CLI 1.0.83, uninstalling a local path plugin disables it and retains both source files and a disabled record. When the entire source is no longer needed, run `copilot plugin marketplace remove program-design` to remove its listing. Direct installation is also supported through `copilot plugin install /abs/repo/dist/copilot/program-design`; do not install it again through the catalog. Plugin installation does not expose a comparable project `--scope`: the official argument applies to single-Skill installation from a file or URL. Check the active user/profile. CLI results do not establish that IDE or Coding Agent behavior has passed. [Official CLI plugin reference](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-plugin-reference)

## Factory / Droid

The repository's native catalog is `.factory-plugin/marketplace.json`. This release provides a Skill-only plugin wrapper and does not register Factory execution hooks. **Droid derives the actual registered marketplace name from the source path/repository and pin, so it may differ from the catalog's `name`.** Check the registered name first:

```bash
droid plugin marketplace add /abs/repo
droid plugin marketplace list
```

Replace `REGISTERED_NAME` below with the actual name in the list. A local directory named `program-design` normally registers as `program-design`; the isolated validation source directory was named `source`, so its actual plugin ID was `program-design@source`.

```bash
droid plugin install program-design@REGISTERED_NAME --scope project
droid plugin list --scope project
# Explicit update:
droid plugin marketplace update REGISTERED_NAME
droid plugin update program-design@REGISTERED_NAME --scope project
# Uninstall:
droid plugin uninstall program-design@REGISTERED_NAME --scope project
```

Use `--scope user` for a user installation and keep the scope consistent when updating or uninstalling. Check `project-docs` in a new session. `marketplace add` requires a catalog source, not a bare plugin directory. Git publication uses the complete repository containing both the native catalog and payload. With an isolated configuration, Droid 0.213.0 passed local directory catalog installation, an A→B update with added/modified/deleted files, rollback to A and removal. This validates plugin management and the active cache, not model reading or remote Git installation. [Official plugins](https://docs.factory.ai/harness/plugins)

## CodeBuddy

The repository's native catalog is `.codebuddy-plugin/marketplace.json`. This release also registers only Skills and does not claim automatic execution of frontmatter hooks.

```bash
codebuddy plugin marketplace add /abs/repo
codebuddy plugin install program-design@program-design --scope project
# Explicit update:
codebuddy plugin marketplace update program-design
codebuddy plugin update program-design@program-design --scope project
# Uninstall and preserve plugin data:
codebuddy plugin uninstall program-design@program-design --scope project --keep-data
```

Scopes are `user`, `project` and `local`; keep update/removal scope consistent with installation. Check after `/reload-plugins` or a new session. Increment the plugin version for each release to avoid continued use of an old cached package. `/plugin` can manage automatic updates, but this distribution does not enable them by default. A Git catalog suits this repository's relative payload paths better than a standalone HTTP JSON file. [Official reference](https://www.codebuddy.ai/docs/cli/plugins-reference), [marketplaces](https://www.codebuddy.ai/docs/cli/plugin-marketplaces)

## Kiro IDE and CLI v3

The root `plugin.json` in `dist/kiro/program-design` defines a Skill-only Power. In the IDE, use Powers → Add Custom Power and select this **complete local directory**, then inspect the installed entry in Powers. Kiro CLI v3 automatically discovers IDE-installed Powers; no additional CLI plugin copy is needed. [Official creation guide](https://kiro.dev/docs/powers/create/), [installation](https://kiro.dev/docs/powers/installation/), [CLI v3 auto discovery](https://kiro.dev/docs/cli/v3/new-features/#powers-auto-pickup)

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
