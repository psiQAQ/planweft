# 0.5.1 可重建归档

状态：Passed。日期：2026-09-13。

- 使用发布 workflow 对应的 Node `v24.20.0` 和 npm `11.11.0` 运行 `npm pack`。
- 归档 `planweft-0.5.1.tgz` 内的 `package/package.json` 标识 `planweft@0.5.1`。
- SHA-256：`8071dee2ffe8c0500e739e17723cf307d3c29276055bbc5a8d1c860358419b28`。
- `python3 scripts/build-plugin.py --verify` 报告 15 个生成目标零差异；归档中包含新 `references/documentation-map.md`。

本记录只证明可重建包及其静态身份；不声明 registry 已发布。
