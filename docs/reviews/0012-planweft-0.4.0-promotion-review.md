# REV-0012：PlanWeft 0.4.0 promotion 独立审查

独立 reviewer：`release_plan_review`。状态：**Passed**。

## 绑定

- npm 归档 SHA-256：`e611338a619adabb0ba943d75460a01d83e4670dbe7d69f5d1050a1c1467c132`
- support policy SHA-256：`bfd7ac9b18c8e6675374114758b9d33b6232ff25a1b03aa855bf2c9e7ff5749e`
- promotion result set SHA-256：`c4257583637ba0d8af0fecee2e97432eacc17213c53b63a69d63d05b5991cf3d`
- prepublication review attestation SHA-256：`95a27e485006cd8f43e378768b830d91e8928c842187b28a0833f3201ed79d6f`
- registry evidence SHA-256：`d4c04ddcdfa8c2ce7c680dd1df27227b49bfa2f62b6cbaac2791e469525b6b69`
- registry proof SHA-256：`c514e7088e8f942998f77189de67a7595fcead79326d6762bb1585b63903b1d7`
- canonical lifecycle evidence SHA-256：`6e54a20c7661fab3f05b9d1325ac19153ddac7610d653b36d1d621ef8f45a40c`
- RC15→stable manifest SHA-256：`488fb3af16a14a6fb97ef879a1752ef015c046dcd980fca2eb5ac5e5012ae32e`

## 结论

68 个聚合结果的名称、attestation SHA 与 result-set 摘要均精确一致：47 Passed、20 Not Run、1 Failed。两个 Failed 子场景仅为实验性的 Codex `gate_cap` 与 `gate_cap_disabled`，均绑定 `LIMIT-CODEX-TRACE-INCOMPLETE`；Not Run 均保留原因，未把历史失败改写为成功。

Promotion 的 40 个 required 远端子场景全部 Passed。其中 20 个 fresh 绑定五宿主 stable uninstall、fresh-process loading 及 native install/remove；其余 20 个 reused 绑定 15 个跨版本 lifecycle 场景和五宿主 `native_update`，复用最终 stable 生命周期与 RC15→stable 逐文件 manifest。registry 中观察到的 same-version update 不冒充跨版本 update。fresh-process 探针不声明模型调用、hook 执行或上下文投递。

Registry 证据的 94 个成员均由 manifest 完整覆盖且摘要匹配；隐私扫描未发现个人路径、认证头、私钥或常见 npm/GitHub token。`.planning/` 不属于发布证据且必须保持未跟踪。审查未发现阻塞 promotion 的剩余问题；仍须由重新生成的 attestation、`check-release-gate.py --promotion` 和同提交三系统 CI 共同放行。
