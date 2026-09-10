[简体中文](INSTALL.md) | [English](INSTALL.en.md)

> Package: **pi**. Use this host's installation section.

# Install, update, roll back, and remove

PlanWeft 0.4.0 is distributed as one `planweft` npm package. The installer selects the native layout for each host and records the files it manages. Do not merge `dist` directories made for different hosts.

Node.js 22 or newer is required; Node.js 24 LTS is recommended. Some hosts also require Python 3, Bash, PowerShell, or their own package manager.

## Install

Project scope is the default. Complete Codex, Copilot, Gemini, Hermes, and DSH integrations support user scope only and require `--global`; these hosts can still install Skill-only at project scope. These examples cover the five supported hosts:

```bash
npx planweft@0.4.0 add -a codex --global
npx planweft@0.4.0 add -a claude
npx planweft@0.4.0 add -a pi
npx planweft@0.4.0 add -a opencode
npx planweft@0.4.0 add -a dsh --global --dsh-profile headless
```

Repeat `-a` to select several hosts in one command. Non-interactive use must provide a host ID.

| Option | Default | Purpose |
| --- | --- | --- |
| `-a / --agent` | Interactive selection | Select one or more hosts |
| `--project / --global` | `--project` | Select project or user scope; unsupported scope is an error |
| `--skill-only` | Off | Install the portable Skill without complete plugin hooks |
| `--copy / --symlink` | Prefer symlink | Control how CLI-managed components are installed |
| `--dsh-profile NAME` | `headless` | Select the profile for a complete DSH integration |
| `--approve-pi-project` | Off | Pass native `--approve` only to this Pi project operation |
| `--dry-run` | Off | Show selections and target paths without writing |
| `--source FILE.tgz` | Current exact npm version | Use a local accepted archive matching the running CLI identity and version |

Host IDs are `codex claude pi opencode hermes cursor gemini copilot mastracode kiro continue factory codebuddy agents dsh`. The five supported hosts are `codex`, `claude`, `pi`, `opencode`, and `dsh`; the other adapters are experimental.

Use `--skill-only` explicitly when only the Skill is needed:

```bash
npx planweft@0.4.0 add -a opencode --skill-only --symlink
npx planweft@0.4.0 add -a dsh --skill-only
```

Skill-only installation does not register plugin hooks or add lifecycle events that the host does not provide.

## Verify installation

Check the recorded and discoverable state after installation:

```bash
npx planweft@0.4.0 list
npx planweft@0.4.0 doctor
```

Reload the host or start a new session, then invoke the main Skill explicitly:

| Host | Fresh-session check |
| --- | --- |
| Codex | Invoke `$project-docs`, then inspect the current hook definition and trust state in the host |
| Claude Code | Invoke `/planweft:project-docs` |
| Pi | Invoke `/skill:project-docs`; only explicit `/pw-plan-execute` starts the execution loop |
| OpenCode V1 | Check `project-docs` and `pw_init`, `pw_status`, `pw_check` |
| DSH | In a new session for the selected profile, explicitly request `project-docs` |

Installation, host discovery, current-session loading, hook trust, and actual model reading are separate checks. `doctor` does not replace a Skill read in a fresh session.

## Update, roll back, and remove

`update` uses the version of the CLI that is running. Running the same command from an older exact CLI version performs a rollback; replace `<version>` with the exact version to restore:

```bash
npx planweft@0.4.0 update -a pi
npx planweft@<version> update -a pi
npx planweft@0.4.0 remove -a pi
npx planweft@0.4.0 doctor -a pi
```

Use the same host, scope, and DSH profile as the original installation. The installer restores copy/symlink and Skill-only choices from its record. To switch between a complete plugin and Skill-only installation, run `remove` before `add`.

Project versions are stored in `.planweft/versions/`, with records in `.planweft/installations.json`. User state uses `$XDG_DATA_HOME/planweft` (default `~/.local/share/planweft`) or LocalAppData on Windows. `PLANWEFT_HOME` can override the user-state location. Do not commit project `.planweft/`.

Removal retains version storage and project documents. After rollback is no longer needed, users may separately clean caches they own; the installer does not delete unknown files.

## User files and duplicate sources

The installer overwrites only files whose ownership it recorded and can verify. Update or removal stops, and `doctor` reports the issue, when:

- a managed file has user changes;
- the target directory contains foreign files;
- the same host finds another PlanWeft source, an old `program-design` source, or independent PWF hooks;
- the installation record, digest, or target path does not match;
- another operation owns `.operation-lock`.

Update and removal do not delete `task_plan.md`, `findings.md`, `progress.md`, `.planning/`, attestations, ledgers, specs, ADRs, reproduction records, or user notes. Rolling back the plugin does not roll back project documents changed during a task.

## Trust, disable behavior, and host differences

Installation does not grant hook, project-file, or command permissions. Codex, Claude Code, Pi, and other hosts retain their native trust and approval flows. Pi's `--approve-pi-project` approves only that local package operation and does not change another host.

The default runtime is advisory. To disable execution hooks on verified adapter paths, set `PLANNING_DISABLED=1` before starting the host. Pi can also use `/pw-plan-execute reset` to return to passive state. Autonomous/gated behavior requires explicit activation and remains experimental on every host.

A complete DSH integration is installed in user scope for one profile. Update and removal must use the same `--dsh-profile`. GUI platforms and Mastra hook merging may be reported as manual and must be completed in the host UI; copied files do not prove loading.

Hermes remains an experimental distribution. Simplifying this guide does not change the historical default-scanner rejection, and the installer does not provide a scanner-bypass switch.

## Troubleshooting

**`doctor` reports duplicate hooks.** Use the host's listing command to find the real registration ID, then remove the old source through its original installation channel. Do not delete unknown caches or run complete plugin hooks beside manual Skill/hooks copies.

**Old behavior remains after update.** Confirm that `update` ran from the target version, then refresh the host marketplace, reload plugins, or start a new session as required. Source refresh, file replacement, and process reload are separate operations.

**Installation stops on a user change.** Inspect the diff and save the content that must remain. After confirming ownership, restore, migrate, or remove it through the original channel. Do not force an overwrite.

**An `.operation-lock` remains.** Confirm that no installer process is running and inspect the records and failure state before removing an empty lock directory. Do not run concurrent installation operations in one project.

**A local exact archive is required.** The CLI version and `--source` archive must have the same identity and version:

```bash
npx planweft@0.4.0 add -a codex --global --source /absolute/path/planweft-0.4.0.tgz
```

## Migrate from an old identity

When migrating from `program-design`, `personal`, or `program-design-local`, use the host's listing command to identify the old registration and remove its execution hooks through the original channel. Install PlanWeft and start a new session. The main Skill remains `project-docs`; auxiliary commands change from `pd-` to `pw-`, and OpenCode tools change from `pd_` to `pw_`.

The installer does not automatically remove an old plugin or the original PWF installation. Project plans, approved requirements, and user changes remain intact.

See the repository's [platform support](https://github.com/psiQAQ/planweft/blob/master/docs/platforms.en.md) for capability levels and known limitations. Maintainers can find manual layouts, catalogs, and protocol details in the [development documentation](https://github.com/psiQAQ/planweft/blob/master/docs/development.md).
