# 0.5.0 registry 静态安装

日期：2026-09-13。用 Node.js 24.20.0 的临时目录执行
`npm install --registry=https://registry.npmjs.org --ignore-scripts --no-package-lock --no-audit --no-fund planweft@0.5.0`。

安装后确认 `node_modules/planweft/package.json` 为 `planweft@0.5.0`，
Codex `project-docs` Skill 含 `planweft-docs-status` marker，且
`dist/codex/planweft/scripts/document-handoff-check.sh` 存在。该检查只读取安装布局。
