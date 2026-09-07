# 配对维护试用的原始证据

`raw-evidence.tar.gz` 保存完整实验输入和输出，根目录为 `paired-maintenance/`。归档含 146 个文件，包括四次实施及四次冷读的完整 stdout JSONL、stderr、提示、前后文件内容、差异、新文件、退出状态、用量、插件注册/安装/卸载与缓存检查、冻结输入、共同基线/研究材料摘要值、独立验收及失败记录。`raw-manifest.json` 登记逐文件 SHA-256；`archive-sha256.txt` 登记压缩包摘要。

小文件另保留在本目录，便于直接阅读。`summary.json` 的输入 token 已包含缓存输入，不能把二者再相加；计时包含容器中安装和卸载。原日志中的日期可能采用 UTC；主报告统一采用 Asia/Shanghai（2026-09-08）。

在仓库根目录提取到自己选定的临时目录：

```bash
mkdir /tmp/program-design-evidence-review
# 先按 archive-sha256.txt 核对压缩包，再提取。
tar -xzf docs/reproduction/evidence/0004/raw-evidence.tar.gz -C /tmp/program-design-evidence-review
```

原始快照有大量重复的历史材料，使用压缩归档避免在日常导航中展开。恢复某个样本时使用其完整 `implementation/after.json` 的路径与内容；仅恢复目标脚本会缺少合法调度用例需要的基线分发目录。`contract-fixture-failure.json` 保留主 Agent 首次恢复不完整目录产生的验收准备失败；随后完整恢复的 `independent-contract.json` 为该样本实际验收。模型会话未重跑。

归档外的 `final-*.json` / `final-*.txt` 是最终主仓库整合后的验证，不能用它们替代某个冷读者当时缺失的测试输出。没有保存认证文件；模式扫描无凭据命中，扫描范围及限制见 `evidence-audit.json`。容器与执行工作区已移除，证据归档有意保留。

结果及限制见 [REP-0004](../../0004-paired-maintenance-trial.md)，独立内容判断与揭盲核查见 [REV-0004](../../../reviews/0004-comparison-review.md)。
