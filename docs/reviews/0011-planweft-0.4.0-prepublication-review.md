# REV-0011：PlanWeft 0.4.0 预发布独立审查

独立 reviewer：`release_plan_review`。结论：**Passed；未发现预发布证据阻塞项，可以将 schema 3 的 prepublication review 置为 Passed。** 本审查不授权跳过远端 registry 验收、promotion review 或三系统 CI，也不把实验性失败改写为成功。

## 审查绑定

| 对象 | SHA-256 / 结果 |
| --- | --- |
| 唯一 npm 归档 | `e611338a619adabb0ba943d75460a01d83e4670dbe7d69f5d1050a1c1467c132` |
| `release/support-policy.json` | `bfd7ac9b18c8e6675374114758b9d33b6232ff25a1b03aa855bf2c9e7ff5749e` |
| 结果集合 | `b30afcd62449c82a28edb1679ba51220b43a40742a961a933457df496758ff5c` |
| 结果 attestation | 53/53，无重复，与 reviewer 集合精确相等 |

门禁使用完整草案实测时只因 `prepublication review=Not Run` 拒绝，未出现策略、包摘要、结果集合、附件、复用或聚合错误。

首次本地预审错误绑定 Node `22.22.1` / npm `9.2.0` 生成的 `438f…7e4c`。OIDC workflow `34430655159` 在 npm 写入前 fail closed；发布 workflow 的 Node `24.20.0` / npm `11.11.0` 生成当前 canonical 归档。reviewer 实算两个 gzip 解压后的 tar stream 均为 `b195ce9c9d1a11590e456c613cc22636ab3a30ed118089e55e2036864085b1d0` 且逐字相同，确认差异只在 gzip 封装。首轮 attestation 未沿用；本表、53 项结果和第二轮 review 均 fresh 绑定 canonical SHA。

## Fresh 与 reused 证据

五宿主准确产物、最终安装/卸载、用户文件保护、离线控制及实际 Skill 读取均在 canonical `0.4.0` 上重新生成 fresh evidence 并 Passed。RC15 仅复用 update/rollback/reinstall、fixture 恢复及未受影响的权限类检查。

逐文件 manifest 记录 RC15 到 canonical 目标包的 255 个差异，affected checks 仅为五宿主 `single_main_skill`，且均已用目标包重新验证。该结果也与旧、新 gzip 的 tar 内容逐字一致相容。因此，本轮复用范围与策略相符。

## 工作流与非 Passed 项

Codex explicit、Pi explicit 和 Pi auto 的维护与冷读分别使用不同容器运行和不同附件。每组维护输出 SHA 精确等于冷读输入 SHA，冷读前后快照相等。冷读未安装插件；Codex 使用 ephemeral 会话并禁用 plugins，Pi 使用 `--no-session`。维护 trace 均证明实际读取 Skill。

Codex `gate_cap` 与 `gate_cap_disabled` 原样保留 `Failed`，绑定公开限制 `LIMIT-CODEX-TRACE-INCOMPLETE`；policy 将 stopping 定义为 experimental，因此不阻塞已通过的正式核心能力。所有 `Not Run` 均逐场景保留原因；中英文 [预发布记录](../reproduction/0011-0.4.0-prepublication.md) 公开模型预算边界、实验性结果、远端 registry/promotion 待办和该限制，没有把失败改写为 Passed。

## 隐私与验证

八个 canonical tar 的 manifest 覆盖全部成员且成员 SHA 全部匹配，无 redaction 差异。对 tar、canonical 包、acceptance 输入、manifest 和 attestations 的路径、常见 token、邮箱及认证头模式扫描未发现个人路径、凭据或认证头。

本地证据记录 Python `332 Passed, 1 Skipped`，Node `123 Passed, 1 Windows-only Skipped`，DSH `3 Passed`。

配置中的六个 `01a...` 外层 session ID 没有嵌入公开附件，reviewer 无法独立核验这些字符串本身；但不同新会话、无历史复用的实际属性由不同容器身份、fresh-session 调用参数、独立附件和连续快照共同证明。该限制不影响工作流结果绑定，未列为发布阻塞。
