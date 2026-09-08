[简体中文](platforms.md) | [English](platforms.en.md)

## 0.4.0 candidate validation

One npm package now exposes the installer, Pi resources and OpenCode V1 entry. Local native lifecycle tests on Linux passed for the four core hosts; model and remote-channel validation remain separate gates. Other eleven adapters retain their implementations but are experimental in 0.4.0. Windows/macOS installer CI is configured, not yet run. [Release: 中文](releasing.md) / [English](releasing.en.md). The 0.3.0 evidence below remains historical.

# Cross-platform design

PlanWeft 0.4.0 generates independent distributions for 15 hosts from one set of file-planning and documentation rules. The workflow and state protocol are shared; installation entry points, event formats, caches, trust, and continuation follow each host's native mechanisms.

For project goals and design sources, read the project introduction: [简体中文](../README.md) | [English](../README.en.md). For installation, updates, rollback, and removal, read the installation guide: [简体中文](installation.md) | [English](installation.en.md). This page explains platform structure and capability boundaries without repeating installation procedures.

| Platform | Static | Protocol | Native lifecycle (Linux) | Model maintenance (Linux) |
| --- | --- | --- | --- | --- |
| Codex | Passed | Passed | Passed | Passed |
| Claude Code | Passed | Passed | Passed | Not Run |
| Pi | Passed | Passed | Passed | Not Run |
| OpenCode V1 | Passed | Passed | Passed | Not Run |
| Cursor | Passed | Passed | Not Run | Not Run |
| Copilot CLI | Passed | Passed | Not Run | Not Run |
| Gemini CLI | Passed | Passed | Not Run | Not Run |
| Hermes | Passed | Passed | Not Run | Not Run |
| Factory | Passed | Not Run | Not Run | Not Run |
| CodeBuddy | Passed | Not Run | Not Run | Not Run |
| Kiro | Passed | Not Run | Not Run | Not Run |
| Continue | Passed | Not Run | Not Run | Not Run |
| Mastra Code | Passed | Not Run | Not Run | Not Run |
| Agents | Passed | Not Run | Not Run | Not Run |
| DeepSeek Harness / DSH | Passed | Passed (bridge/Skill) | Passed | Not Run |

All remote npm/Git lifecycles and real Windows/macOS host sessions remain Not Run until separately recorded. Pi RPC and OpenCode debug discovery are actual host loading, not model calls. Non-core native runs from 0.3.0 are not reused as 0.4.0 results.

The Codex model scenario uses an isolated container and an explicit hook trust bypass. It validates the reviewed hooks at runtime, not the default interactive trust confirmation flow.

## One source, multiple native directories

The build uses a pinned upstream snapshot, local overlays, and deterministic generation. The current base is PWF v3.17.0 at commit `0d21b6c4aa5f2c5bdd3d042e7473ee09f7fae9e7`. Normal builds do not read the research submodule, personal plugin caches, or the network.

| Layer | Location | Responsibility |
| --- | --- | --- |
| Pinned source | `vendor/planning-with-files/` | Original source archive, file inventory, provenance, and MIT license; never patch the archive directly |
| Shared overlays | `overlays/planweft/` | Documentation rules, templates, product identity, and installation resources |
| Native adapters | `overlays/planweft/native/` | Host manifests, event bridges, component layouts, and installed resource resolution |
| Compiled resources | `overlays/planweft/opencode-compiled/` | OpenCode V1 outputs bound to a source digest; maintainers compile them, users install the result |
| Generator | `scripts/build-plugin.py` | Apply identity mappings and patches; generate all platform directories, six catalogs, and the content manifest |
| Distributions | `dist/<host>/planweft/` | Self-contained installation sources with `LICENSE`, `UPSTREAM.json`, and required runtime assets |
| Compatibility mirror | `plugins/planweft/` | Generated Codex mirror retained for 0.3.x, identical to `dist/codex/planweft/` |

Maintainers edit generation sources and rebuild instead of editing platform copies. `dist/manifest.json` records the product version, upstream commit, platform paths, per-file hashes, executable bits, and aggregate hashes. `--verify` checks missing files, extra files, content, and executable-bit drift without writing. The generator cleans only explicitly managed outputs and preserves other plugins' root catalog entries.

PWF uses hidden root directories to hold several platform adapters. This repository keeps shared implementation in the source snapshot and overlays, and installation contents in `dist`; hidden root directories serve as host discovery entry points. The presence or absence of a host-named root directory therefore does not determine platform support.

Directories provide inspectable installation sources; host channels provide ongoing updates. The build no longer generates platform ZIPs. Release preparation can still create native npm `.tgz` packages and package-root Git trees for Gemini and Hermes. See [upstream and distribution maintenance (engineering record, Chinese)](upstream-maintenance.md) for maintainer details.

## Six marketplaces provide independent discovery

The paths below are relative to the repository root. Each catalog has `planweft` as its `name` metadata, but uses its host's own schema. Registering one does not register the others. There is no generic root `marketplace.json`, avoiding discovery precedence that could select another host's package.

| Host | Repository discovery entry | Package directory |
| --- | --- | --- |
| Codex | `.agents/plugins/marketplace.json` | `dist/codex/planweft/` |
| Claude Code | `.claude-plugin/marketplace.json` | `dist/claude/planweft/` |
| Cursor | `.cursor-plugin/marketplace.json` | `dist/cursor/planweft/` |
| Copilot CLI | `.github/plugin/marketplace.json` | `dist/copilot/planweft/` |
| Factory / Droid | `.factory-plugin/marketplace.json` | `dist/factory/planweft/` |
| CodeBuddy | `.codebuddy-plugin/marketplace.json` | `dist/codebuddy/planweft/` |

Use the host's listing to obtain the actual registered ID. Droid's name also depends on the source directory, repository, and pin, so it cannot be inferred from JSON `name` alone. A published Git marketplace must include both the catalog and referenced directories; hosting JSON alone does not make relative files downloadable. Cursor uses its native UI; a catalog does not imply a universal management CLI.

## Package shapes and channels for all 14 platforms

This table describes the entry points generated in 0.3.0 and the selected channels. A native entry point does not prove successful host installation or event execution. See the validation matrix below for actual results.

| Platform / `host` | Main package entry points | Distribution and update design | Official reference |
| --- | --- | --- | --- |
| Codex / `codex` | `.codex-plugin/plugin.json`, Skills, hooks | Git marketplace; refresh the source, reinstall, and start a new session; handle hook trust separately | [plugins](https://developers.openai.com/codex/plugins/), [hooks](https://learn.chatgpt.com/docs/hooks) |
| Claude Code / `claude` | `.claude-plugin/plugin.json`, Skills, commands, hooks | Git marketplace; marketplace refresh and plugin update are separate; reload or start a new session | [marketplaces](https://code.claude.com/docs/en/plugin-marketplaces) |
| Pi / `pi` | Root `package.json`, `SKILL.md`, TypeScript Extension | An npm `pi-package` distributes the Skill and Extension together; local paths can be referenced in place; change the pin to upgrade a fixed version | [packages](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/packages.md) |
| OpenCode / `opencode` | Root npm `package.json`, compiled `dist/index.js`, Skills, loader template | V1 npm or local package; pair the plugin with its separately discovered Skill; change the version and restart, with no user compilation | [plugins](https://opencode.ai/docs/plugins/), [Skills](https://opencode.ai/docs/skills/) |
| Hermes / `hermes` | Root `plugin.yaml`, `__init__.py`, `skills/project-docs/` | Package-root Git tree pinned to a full SHA; copy and pair the Skill from the same commit; native installation is currently rejected by the host scanner | [plugins](https://hermes-agent.nousresearch.com/docs/user-guide/features/plugins/) |
| Cursor / `cursor` | `.cursor-plugin/plugin.json`, Skills, hooks | Native local plugins and Marketplace/team Git entry points; the UI manages refresh and updates | [plugins](https://cursor.com/docs/plugins) |
| Gemini CLI / `gemini` | Root `gemini-extension.json`, Skills, `hooks/hooks.json` | Package-root `release/gemini` Git branch; explicit native Extension updates track the branch | [reference](https://geminicli.com/docs/extensions/reference/), [releasing](https://geminicli.com/docs/extensions/releasing/) |
| Copilot CLI / `copilot` | Root `plugin.json`, Skills, `hooks.json` | Native marketplace and plugin updates; local path sources load in place; CLI results do not cover IDE or cloud capabilities | [CLI reference](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-plugin-reference) |
| Mastra Code / `mastracode` | `.mastracode/skills/` and separate hook configuration | Complete Skill directory with hooks merged as needed; explicitly update files managed by this plugin | [configuration](https://code.mastra.ai/configuration) |
| Kiro / `kiro` | Root `plugin.json`, Skills, supporting scripts | Skill-only Power; install and update in the IDE, with CLI v3 discovering IDE-installed Powers | [installation](https://kiro.dev/docs/powers/installation/), [CLI v3](https://kiro.dev/docs/cli/v3/new-features/#powers-auto-pickup) |
| Continue / `continue` | `.continue/skills/project-docs/`, optional prompts | Complete Skill directory; update from a pinned checkout or manually, without a separate package updater | [Skill loader](https://github.com/continuedev/continue/blob/main/extensions/cli/src/util/loadMarkdownSkills.ts) |
| Factory / `factory` | `.factory-plugin/plugin.json`, Skills | Native Git marketplace and plugin updates; this release registers only Skills | [plugins](https://docs.factory.ai/harness/plugins) |
| CodeBuddy / `codebuddy` | `.codebuddy-plugin/plugin.json`, Skills | Native Git marketplace and plugin updates; increment the version and reload; this release registers only Skills | [reference](https://www.codebuddy.ai/docs/cli/plugins-reference), [marketplaces](https://www.codebuddy.ai/docs/cli/plugin-marketplaces) |
| Generic Agents / `agents` | `.agents/skills/project-docs/` | Complete Skill in the selected host's discovery directory; optional third-party Skills installer, with no universal runtime or updater guarantee | [Agent Skills](https://agentskills.io/specification) |

## Installed assets and project state are separate

Scripts, templates, and language resources resolve from the actual installed plugin or Skill directory; task records resolve from the target project. An installation cache is not a project directory, and updating the plugin does not migrate project state. Adapters use the host-provided package root or equivalent resolution, such as Cursor's `CURSOR_PLUGIN_ROOT`, Copilot's `PLUGIN_ROOT`, Gemini's `${extensionPath}`, and OpenCode's `import.meta.url`.

The main entry remains `project-docs`, auxiliary commands use `pw-`, and OpenCode tools use `pw_`. Codex and Claude retain their supported language-entry layouts and invocation policies. Platforms using the portable Skill layout place variants in the main Skill's `references/language-variants/`, using `GUIDE.md` as an explicitly read resource to avoid duplicate discovery during recursive scans. Pi also includes language resources; these assets must travel with any copy of the complete main Skill.

The runtime retains `PLAN_ID`, `PWF_*`, `PLANNING_DISABLED`, and the PWF disk protocol. Kiro retains its platform-specific `.kiro/plan` layout. Installers do not delete or rewrite the three planning files, attestations, ledgers, or long-term documents. Automatic recovery reads project files only; session-history access still requires explicit invocation. Multi-agent work keeps one plan owner and separate worker records, with separate plans or worktrees for independent tasks. The plugin uses existing host Agent capabilities without adding a unified scheduling service.

## Hooks respect native capability boundaries

Reminder mode is the default. Explicit autonomous or gated behavior is limited by each host's actual capabilities. Skill discovery, a valid hook definition, execution, context delivery, and continuation are separate layers of behavior.

| Platform or type | Integration in this release | Capability boundary |
| --- | --- | --- |
| Codex | Native session, tool, compaction, permission, and Stop events; Windows launcher | Installation does not automatically grant hook trust; shipping a launcher does not prove Windows execution |
| Claude Code | Lifecycle hooks, Python fast path, and Shell fallback | Plugin and standalone routes must not enable duplicate execution hooks |
| Pi | TypeScript Extension, commands, status bar, and cache policy | Execution mode requires explicit activation and inherits native continuation limits |
| OpenCode V1 | Native tools, context injection, compaction handling, and idle follow-up | V1 adapter; no claim of compatibility with the different V2 protocol |
| Cursor | `sessionStart`, `postToolUse`, and `stop` bridge | Script protocol tested; real GUI event delivery not tested |
| Copilot CLI | `sessionStart`, `postToolUse`, and `agentStop` bridge | Advisory output does not include tool approval through `permissionDecision: "allow"` |
| Gemini CLI | `SessionStart`, `BeforeAgent`, `AfterTool`, and `PreCompress` bridge | PreCompress `systemMessage` is a user notice, not claimed as model-context injection |
| Hermes | Native Python plugin and `pre_verify` integration | Host limits govern triggers and attempts; installation currently fails, so runtime success is not claimed |
| Mastra Code | Skill and independent hook configuration | Merge configuration as needed without overwriting existing project hooks |
| Kiro, Continue, Factory, CodeBuddy, generic Agents | Skill, Power, or directory discovery | Packaging alone does not supply full execution hooks or a native stop gate |

Reading, diagnosis, and host planning mode should not initialize or modify project records; project rules and the user's scope take priority. Some inherited behavior in Cursor, Gemini, Copilot, and Mastra still centers on a root `task_plan.md`; named-plan and read-only support depend on the corresponding implementation and validation. For strict read-only operation or a complete shutdown, use the host's disable mechanism. `PLANNING_DISABLED=1` is sufficient only on verified adapter routes; the plugin does not promise to recognize every natural-language read-only request. Attestation is not human approval, and a gated check does not prove correctness.

Enable only one planning plugin's execution hooks in a session. Doctor and installation guidance help identify detectable duplicate sources; this plugin does not automatically uninstall the original PWF. Hook-private caches, installation caches, and project records are validated separately.

## Updates belong to the host lifecycle

An update involves the source, installed contents, current process or session, trust, and project state. Marketplace refresh updates source information; the host decides whether installed content changes, and replacing files does not guarantee that the current session reloads them. Hosts such as Claude and CodeBuddy use plugin versions for caching, so releases must increment the version.

Updates are explicit by default. A pinned installation upgrades by selecting a new version or commit; automatic updates use only host-provided settings. Skill directories without a native updater are updated from pinned checkouts or by replacing the complete managed directory, removing stale plugin files while preserving user changes. Rolling back a plugin does not roll back project documents changed during a task.

Pi packages the Skill and Extension together. OpenCode records matching versions, sources, and content hashes for the plugin and separately installed Skill. Hermes also requires pairing, without inventing a `skills install --ref` option: the reproducible route copies the complete Skill from the same SHA checkout. A Skills Hub route tracking the default branch cannot guarantee atomic upgrades with the plugin.

Release preparation outputs Gemini and Hermes Git trees with installation files at the branch root. Gemini requires a root Extension manifest. The Hermes installer supports subdirectories, but extraction does not preserve `.git`, so this repository uses package-root release trees to retain repository metadata. Gemini tracks `release/gemini`; Hermes uses a full commit SHA from the `release/hermes` tree. Later preparation runs can continue the preceding Git history.

These are implemented local release-preparation capabilities. Publishers must explicitly provide the Git URL and npm identity; this repository does not claim installation URLs are already live. Preparation does not push, publish to npm, list a marketplace entry publicly, or install into personal global configuration. For procedures and migration from old installation identities, see the installation guide: [简体中文](installation.md) | [English](installation.en.md).

## Validation status

The following summarizes existing 0.3.0 validation recorded on 2026-09-08; this bilingual documentation update did not rerun real hosts or scanners. All 14 directories passed static and build-consistency checks in that run. “Local lifecycle” means installing A, updating to B, rolling back to A, and uninstalling, including added, changed, and deleted files. It does not mean that a remotely published Git or npm channel was tested.

| Platform / tested version | Protocol or discovery evidence | Native install | Local lifecycle | Actual loading coverage |
| --- | --- | --- | --- | --- |
| Codex 0.153.4 | Passed, real `skills/list` | Passed | Passed, updates through reinstallation | Passed, real exec with local synthetic responses checks trust, injection, fresh-session recovery, and disable behavior |
| Claude Code 2.1.263 | Passed, structure and inherited hook protocol | Passed | Passed; uninstall may leave orphan caches | Not Run, no authenticated model session |
| Pi 0.85.1 | Passed, 54 Extension tests | Passed, actual npm tarball | Passed | Not Run, Extension activation not checked in a model session |
| OpenCode V1 1.18.29 | Passed, real debug discovery of three `pw_` tools and one main Skill | Passed | Passed, local packages and fresh processes | Passed, debug loading and direct tool execution; model calls and in-session reload are Not Run |
| Gemini CLI 0.58.0 | Passed, four-event script protocol | Passed | Passed, retaining trust/install confirmations | Not Run, no authenticated model session |
| Copilot CLI 1.0.83 | Passed, native output protocol | Passed | Passed; local source loads in place, uninstall disables discovery and preserves the source directory | Not Run, no authenticated model session |
| CodeBuddy 2.147.0 | Passed, Skill/catalog | Passed | Passed; uninstall may leave orphan caches | Not Run, no authenticated model session |
| Factory Droid 0.213.0 | Passed, actual installation metadata | Passed | Passed, checking the actual `installPath` | Not Run, no authenticated model session |
| Hermes 0.21.1 | Passed, package-root and resource contracts | **Failed**, rejected by default Plugin Guard | Not Run | Not Run |
| Cursor | Passed, three-event script protocol | Not Run, GUI/account unavailable | Not Run | Not Run |
| Kiro | Passed, Power/Skill and cached script-path contracts | Not Run, GUI unavailable | Not Run | Not Run |
| Continue | Passed, complete Skill/directory static checks | Not Run | Not Run | Not Run |
| Mastra Code | Passed, static checks and disable protocol | Not Run | Not Run | Not Run |
| Generic Agents | Passed, standard-directory static checks | Not Run, no host specified | Not Run | Not Run |

The eight installable hosts also checked the three planning files, a user note, an approved spec, an accepted ADR, and an existing reproduction record; their contents were preserved across the lifecycle. Native uninstallation and physical cache deletion are recorded separately; cleaning a temporary test profile does not mean the host removed orphan caches.

Hermes used official commit `9fd44b4dfc44138b9e5d5689acb56c438364ff7b`. The default scanner rejected installation of the final directory as dangerous with **41 findings**, compared with 42 in the first run. Tests did not disable the scanner or relabel a manual discovery route as successful native installation.

All host runs used isolated configuration on Linux x86_64, with no personal authentication or paid model calls. Windows, macOS, GUI installation, remote publication channels, and new-version real-model maintenance and cold-reader trials are **Not Run**. Codex's synthetic responses prove hook delivery; OpenCode debug proves loading and direct execution. Neither proves model-level semantic quality.

Full reproduction details, raw logs, and limitations are in [REP-0006 (engineering record, Chinese)](reproduction/0006-native-distributions.md). Design contracts are in [SPEC-0004 (engineering record, Chinese)](specs/0004-native-distributions.md) and [ADR-0007 (engineering record, Chinese)](adr/0007-native-distributions.md). The 0.2.0 records remain historical evidence and do not substitute for validation of the 0.3.0 distribution.
