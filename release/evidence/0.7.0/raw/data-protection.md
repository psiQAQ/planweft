# 0.7.0 data protection evidence

The P1 state store remains task-side `.planweft-state/`, separate from installer `.planweft/`, and is excluded from the npm archive. New state is disabled until explicit `state init`. Artifact paths are project-bound and symlink/path traversal checks reject escapes. `record` archives files and treats command/argv strings as data; it never executes them.

Checkpoint apply uses a single owner lock, write-before-hash checks, atomic replacement of each selected Markdown file, conflict rejection, and retained before/after snapshots. The reducer only reads Receipt-referenced, hash-verified Artifacts and returns byte-verifiable quotes. The existing user-modification and package-replacement tests remained passing.
