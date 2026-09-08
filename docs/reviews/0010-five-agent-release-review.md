# REV-0010：五 Agent 发布验收审查

## 历史脱敏：Passed

独立 reviewer：`container_release_plan_review`。主 Agent 在执行前提供原始 bundle、隔离仓库和重写脚本；reviewer 未执行推送。

- 核对 27 对提交：作者、提交者、日期、消息原字节保留，父关系仅按映射替换。
- 树成员及 mode/type 保留；恰好八个 reproduction evidence blobs 改变，vendor 与其他源码不变。
- 递归检查 1,906 个 tar 成员、1,350 个 ZIP 成员、3,344 个普通 payload；未发现原私人 home 或归档身份元数据残留。
- 54 个变化 payload 只有约定的 home 前缀替换；原始 bundle 校验通过。
- 原 master `c2f6c0655dc9d57ad3575faf471e7d8b5f967eb2` → 公开 master `52dcacac9efafbe7b309283ed44ac1d32d730155`。
- 用户批准后，主 Agent 使用包含原远端完整 SHA 的 lease 更新且只推送 master；备份未上传。

公开[提交与 blob 映射](../reproduction/evidence/0010/history-sanitization.json)。映射中的原始摘要属于历史观察，清理后的附件摘要见 public_sha256；不将它们冒充原始未改动附件。历史重写不能撤回其他人已有副本。

## 验收工具：有限范围可合并

独立审查发现并要求处理：原生命令退出码不足以证明加载；恢复必须接续前次项目；维护需要独立字节断言；DSH 文本不提供工具事件证据；认证异常和日志须防凭据落盘；远端内容须绑定下载归档；卸载须检查实际注册消失；冷读与审查须关联实际输入输出摘要。

主 Agent 已逐项修订相关边界。DSH 缺少工具事件时不标 no-tools Passed；Codex 单次 trust bypass 不计正常持久信任。真实模型验收和最终源码复审结果尚未全部完成，不据本记录放行稳定发布。

最终复审结论：可以作为候选发布工具和有限验收证据合并，不可作稳定版放行。修复了 Pi/OpenCode 远端项目级发现的工作目录遗漏。运行汇总的容器基线遗漏已修复；旧 Codex 组该项未证实，保留原始记录并在 REP-0010 更正，未冒称完整隔离验收通过。

独立语义审查：Codex maintenance 与 cold-reader 两项 Passed；代码字节回归、批准合同、用户改动、单一计划、历史保留、Windows Not Run 均准确。冷读输入与维护输出一致。另确认原生 TUI 的 7 hooks 激活记录和无 bypass 新会话无工具返回随机码；不推导全部权限策略已验证。

合并时受审文件摘要（最后容器基线修复由主 Agent 验证）：

```json
{
  "tests/five_agent_runtime.py": "b869bf32a75ff0ad8e37bb937a5ecfe21956eb57065d9a4252c53121bd534cdc",
  "tests/run-five-agent-release.py": "d311a7bad3976e5b37e9537e51193f8b0b650eeb84f79caff4cc65d13107d68b",
  "tests/run-registry-smoke.py": "c5c79c33eac84aeaa8e8b99808c9d00bbcf2a02fcea57b7435d5a5fe7854230b",
  "scripts/check-release-gate.py": "999db1a346fe4cce72d0c282921603a0cf3e9817dfda5f8af2f9e8e0cb470c2f",
  "scripts/check-release-artifact.py": "84ebba023eb72913fd6e89ba0306d56545dde4a42f67d91c029a25d711f2bd25",
  ".github/workflows/publish.yml": "e27600dff1fdc2cfd068f181a39ea55d470bec215161e96110e767524ca9cc77"
}
```

容器基线检查的复跑发现 Docker `ps` 不支持负 label filter；主 Agent 已改为全体 ID 减去正 label 查询的 ID，保留失败尝试并复验。

## RC2 原生修复与模型语义复核

独立 reviewer `container_release_plan_review` 核查 DSH Cordis 相对插件定位（宿主 anchorInsertedPluginNames 会将 patch 中相对文件名绑定到包根）、OpenCode 同版本 npm 插件独立 Skill 配对以及仅包含官方 URL/key 的临时模型输入，未发现新的设计阻塞。已有 PWF 状态协议和上游固定源码保留。

Pi 维护记录保存了完整历史事实，仅重排“历史：”展示标题，原断言误报；使用明确重判附件，不能宣称重跑模型。Pi context 的原生消息包含 token 但模型未返回，仍为 Failed。Claude 维护与独立冷读语义 Passed；冷读“未执行任何命令”的自述不准确，应限定为未写文件、未重跑测试。

OpenCode 未自动读取 Skill 的实际维护失败需要修复，reviewer 同意在现有 chat.message 无计划/无冲突分支加入条件式指引。保留禁用、有效根检查与去重，不新增调度或直接初始化。要求实际维护、simple 和 readonly 复验；协议测试不能放行稳定版。

后续复审提出两项增强，主 Agent 已处理：非空但失效的 PLAN_ID 保持原有静默，不被当作新任务提醒；对照入口保存 Vitest JSON 并机械检查 raw 失败集合恰为两项有意差异，额外失败或 pending 不能放行。新增显式绑定 hook 测试。typecheck 仅覆盖运行时 src，不声称覆盖测试 TypeScript。

## RC2 OpenCode 与 RC3 DSH 复审

OpenCode RC2 维护与独立冷读语义 Passed，附 REP-0010 中的错误日志和措辞差异。reviewer 先从维护后的文件重建结果，再核对 trace；两个会话身份不同，冷读未安装插件、输入完全等于维护输出、冷读前后项目不变。

DSH reviewer 确认 HOME 缓存在原沙箱不可写，且 bwrap 每次调用会替换 /tmp，故仅改缓存不足以保存去重。所提临时缓存、session 映射和有界进程状态方案不修改原生权限；指出的 JSON null 透明传递、有效 Stop stdin 和容量边界已经补回归。临时 pwf-prog 限制明确公开，不据协议测试放行稳定版。

独立 RC3 readiness 复审：真实 Cordis 私有 provider fiber 方案可激活官方 bridge；原 direct apply 协议不足以验证注册。Pi 精确镜像 0.84.3 的 settled/state/EOF 顺序已核实，修订收集器及七种失败边界回归通过。两项修改仍须新准确归档和真实模型证据。
