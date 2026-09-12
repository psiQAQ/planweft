# 0.5.1 registry 静态安装

状态：Passed。日期：2026-09-13。

- 在新建临时目录执行 `npm install --ignore-scripts --no-audit --no-fund --registry=https://registry.npmjs.org planweft@0.5.1`。
- 安装后读取的包身份为 `planweft@0.5.1`，且包含 `dist/codex/planweft/skills/project-docs/references/documentation-map.md`。
- 未执行包脚本或 Agent/Hook 工作流。
- npm 9 在 Node 22.22.1 下对传递依赖 `ini@7.0.0` 的引擎范围给出 `EBADENGINE` 警告；安装退出码为 0，且不影响已安装包身份或文件存在性。预发布归档使用 Node 24.20.0/npm 11.11.0 构建。
