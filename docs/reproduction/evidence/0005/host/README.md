# Codex 0.2.0 隔离宿主试用证据

固定 Linux 镜像 `aa46e31c...`、Codex CLI 0.149.1、模型 `gpt-5.6-terra`。本主归档含 14 个真实模型会话、4 次无模型安装预检；后续两次语言策略预检见[独立附录](skill-discovery-README.md)。每次使用独立 tmpfs HOME；未挂载个人配置、历史或记忆。认证只读单文件挂载后复制到已清理的容器 tmpfs，不纳入证据。

- [汇总](summary.json)保留每轮原始自动判定，包括失败；各轮人工语义审查在归档内 `smoke-*/semantic-review.json`。
- [原始证据归档](raw-evidence.tar.gz)包含完整 JSONL、stderr、原始提示、前后快照、diff、实际 hooks/list 与安装生命周期、schema、cleanup、精确试用 ZIP 和最终文案差异。
- [逐文件清单](raw-manifest.json)给出归档与每个成员的 SHA-256；[有限凭据扫描](evidence-audit.json)说明检查范围。

| 轮次 | 结果及解释 |
| --- | --- |
| smoke-01 | 真实受信注入、全新会话恢复、简问、只读及核心冷读成立；untrusted 缺显式诊断、维护未采用 PWF 的失败保留。首轮边界过度禁止环境变量读取。 |
| smoke-02 | hooks/list 确认 7 条未信任 hook；普通调用没有上下文。澄清合法变量后，维护仍未采用三文件，定位默认采用语义歧义。冲突与证据缺口行为正确；后者未写文件名使通用引用判定失败，人工审查单独说明。 |
| smoke-03 | 仅澄清默认采用后，同一无启用语句任务自动读主 Skill、生成唯一三文件计划、承接关键状态并重定向旧记录，维护与独立冷读 Passed。 |
| preflight-final（当时最终） | 当时最终包真实注册、安装 0.2.0、源包/cache 全部字节核对、7 条 hook 元数据和卸载通过。最终与第三轮模型包仅有 6 份 Skill 的状态承接补句及 INSTALL 环境说明差异；运行时未变。 |

第三轮观察到新计划填充和旧指针更新属于同一成功 patch，CLI 不暴露 patch 内部逐文件时序。最终新增“先承接状态再 redirect”句子的内容要求已被该样本满足，但没有另作严格写入顺序试验。

/tmp 和 /home/agent 的 tmpfs 带 `noexec`，直接执行脚本曾返回 126；源包和安装脚本 mode 均正确，使用解释器正常。这是隔离环境限制。真实任务均正常停止并清理，但 CLI JSON 不给出独立 Stop hook 完成通知；不以退出码充当该事件已观测的证据。真实 gated 循环未运行，使用单独离线协议验证。

初始两轮 ZIP 根据第三轮精确包与首次 trace 中完整捕获的旧 workflow 重建，整个 ZIP SHA 与首次记录完全一致；方法记录在 `smoke-01/frozen-package-recovery.json`。前两轮 runner 仅记录源码 hash，第三轮及最终预检另保留精确 runner 源码；各轮实际提示、fixture、输出和控制器结果均完整保留。

这些样本证明限定场景下的行为，不构成平台全面兼容或效果优于 PWF 的统计结论。Windows、macOS 和其它宿主实际运行在本套试用中均为 Not Run。

当前最终包的新增五份 Codex 原生语言策略、实际 skills/list 发现结果及 API 可观察范围见[语言策略附录](skill-discovery-README.md)。原 `raw-evidence.tar.gz` 与其清单未修改。
