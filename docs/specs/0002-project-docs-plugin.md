# SPEC-0002：首版文档协作插件

状态：Accepted；日期：2026-09-07。需求来源：用户确认的首版计划及实施授权，承接 SPEC-0001 REQ-01～10。

## 问题与验收

将普通 Markdown 协作封装为可安装的 Codex Skill，减少每次重新描述工作方式的需要；不预先宣称提高准确率或节省时间。

| ID | 行为与验收 |
| --- | --- |
| PD-01 | program-design 0.1.0 提供一个 project-docs Skill；repo marketplace 可注册、安装、加载及卸载，包内流程不依赖研究库 |
| PD-02 | 生效项目 AGENTS 明确启用后按任务匹配；显式调用只授权当前任务。未启用项目、无关任务不自动建管理文档或改 AGENTS |
| PD-03 | 按入口和任务读取需求/计划/决定/证据；沿用非标准目录，无文档时按需创建 |
| PD-04 | 授权内增量维护，保护已有修改和历史；只读请求不写入，不为匹配代码擅改批准需求 |
| PD-05 | 实质设计逐文件引用；资料未覆盖时实际检索或记 Not Run。独立 review 不可用时如实记录 |
| PD-06 | 计划保留完成、下一步、阻塞和证据；无旧聊天的新读者能定位并接续 |
| PD-07 | 按观察记录 Passed/Failed/Not Run，不以退出码或模型断言替代验证 |

## 接口与限制

入口是自然语言任务及 `$project-docs`；description 匹配并保持允许隐式调用。启用检查为模型工作约定，不是宿主安全边界。输入输出为 Markdown 与现有 Agent 文件工具，不新增状态协议或 CLI。

源码唯一维护于 plugins/program-design。repo catalog 使用生成器默认名称 personal；本次不安装到个人配置。未来可执行工具采用 TypeScript/Node.js；本版无必须引入运行时的功能。

临时样例及本仓库副本用于验证。Windows 不可用单列 Not Run。正式自身接管仍受 ADR-0003 限制。依据：[ADR-0005](../adr/0005-skill-first-plugin.md)；结果：[REP-0003](../reproduction/0003-project-docs-plugin.md)。
