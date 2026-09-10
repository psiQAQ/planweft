# ADR-0009：能力分级、证据定级与不可变正式包

状态：接受；实施与验证见 SPEC-0005、PLAN-0010 和 `release/support-policy.json`。

## 背景

旧发布门禁把五宿主的所有聚合项都视为同一等级，并要求全部 `Passed`。这会把确定性的安装、卸载、用户文件保护与真实模型自动采用混成一个承诺，也可能诱使发布者把非阻塞失败改写成 `Passed`。候选包的历史证据仍有价值，但不能替代最终稳定包的准确产物、最终安装/卸载、用户文件保护和显式 Skill 读取。

## 决定

0.4.0 使用受版本控制的支持策略和 acceptance schema 3。`release/support-policy.json` 逐宿主、逐检查、逐场景声明 `required`、`evidence_based` 或 `experimental`，并声明证据能否复用。缺少策略项、结果项或附件时拒绝放行。

`Passed`、`Failed`、`Inconclusive`、`Not Run` 保留观察本义。门禁根据策略和实际子场景计算 `release_blocking`；acceptance 中的同名字段只是可复核投影，不能自行授权发布。`required` 非 `Passed` 必须阻塞；非阻塞的失败或不确定结果必须带公开限制 ID，`Not Run` 必须带原因。

五宿主的准确归档、确定性生命周期、显式 Skill 读取、项目隔离、用户修改保护、重复注册检测，以及离线验证的默认 advisory、明确禁用、cap 和 stall 控制属于正式支持。实际模型的上下文投递、恢复与 stopping 仍是实验性，不能用来代替离线控制门禁。Codex 的显式维护到独立冷读是必需工作流。Pi 的 explicit/auto 分别以冻结条件的维护、独立冷读和范围遵循定级；每个模式只有全部通过才可公开称为正式，否则保持实验性。其他宿主自动采用、五宿主 autonomous/gated 自动续跑以及其余十个平台适配保持实验性。

模型范围遵循是公开评测，不是安全隔离保证。越界必须保留为 `Failed` 并影响对应工作流定级；只有当该工作流本身属于 `required` 时才阻塞整个发布。

证据分为 `fresh` 和 `reused`。复用必须绑定原包与目标包版本/SHA、逐文件 manifest 差异、受影响检查和 reviewer。策略明确禁止复用的场景不能以差异审查替代。证据引用最多放宽到仓库根，仍拒绝绝对路径、`..`、越界或自引用 symlink，以及摘要不匹配。

独立 review 必须分别在 prepublication 和 promotion 阶段绑定策略摘要、最终 npm 包摘要及本阶段全部结果附件。promotion 的 `fresh_session_native_loading` 是无新模型调用的原生发现/加载探针；不扩大批准的模型运行次数。正式包先以 `next` 发布同一不可变归档，远端验收和 promotion gate 通过后才提升 `latest` 并创建 GitHub Release。

## 后果

发布报告会保留非阻塞失败，不再用“总体通过”掩盖真实子场景。门禁和证据结构更明确，但 acceptance 生成与 review 需要逐项绑定。0.4.0 发布到 `next` 后如远端验收失败，不覆盖或删除该 npm 版本，不移动 `latest`，也不创建正式 Release；后续修复使用 0.4.1。
