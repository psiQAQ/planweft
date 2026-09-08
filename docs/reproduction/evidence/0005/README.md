# Program Design 0.2.0 交付证据

结论及验证限制见 [REP-0005](../../0005-pwf-based-plugin.md)。本目录保存实际输入、命令、输出和失败，原始记录不会因为后续修复通过而覆盖。

| 入口 | 内容 |
| --- | --- |
| [regression](regression/README.md) | 231份原始/迁移回归记录、最小mkdir竞争复现、GNU对照、最终源码SHA与增量验证；归档逐文件校验 |
| [host](host/README.md) | 14个真实模型会话、4次初始安装预检的完整轨迹、fixture、文件差异、hooks信任、精确包、语义判定及清理；后续补充预检另记 |
| [local](local/manifest.json) | 最终25项unittest、13项入口合同、确定性生成检查；旧系统validator结果单独列为已知差异 |
| [installation](installation/README.md) | 提交整理时追加的29项unittest、原始/迁移各13项Skill检查、14平台安装审查、Gemini配置修复、当前精确Codex包无模型安装预检及与旧包差异；不覆盖历史输出 |
| [host-environment.json](host-environment.json) | 当前Linux/工具版本及PATH宿主盘点；只读PATH-alias警告保留，不等于安装失败 |
| [baseline/summary.json](baseline/summary.json) | 初始基线摘要，另补指向后续uutils/GNU调查；不单独代表默认环境可靠并发 |

完整第三方源快照已位于vendor，证据归档不重复打入源码图片、node_modules、venv、认证或私有配置。host中的模拟业务项目和三文件是真实模型产物，不是本仓自身接管。

归档完整性可按各目录manifest复验。解压时使用新临时目录，保留归档内相对路径，不把实验项目覆盖到业务项目或全局配置。
