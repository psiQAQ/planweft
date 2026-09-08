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

## 验收工具：修订后待复审

独立审查发现并要求处理：原生命令退出码不足以证明加载；恢复必须接续前次项目；维护需要独立字节断言；DSH 文本不提供工具事件证据；认证异常和日志须防凭据落盘；远端内容须绑定下载归档；卸载须检查实际注册消失；冷读与审查须关联实际输入输出摘要。

主 Agent 已逐项修订相关边界。DSH 缺少工具事件时不标 no-tools Passed；Codex 单次 trust bypass 不计正常持久信任。真实模型验收和最终源码复审结果尚未全部完成，不据本记录放行稳定发布。
