# RC11 scope recovery: independent source review

范围：只读核查六语言入口第 2 步新增的范围摘要、`templates/task_plan.append.md` 的指针，以及固定 PWF 的普通 head/smart 提取契约。未修改实现、runtime、生成分发或维护任务项目；未启动容器或模型。准确 RC11 的模型效果 **Not Run**。

当前结论：**源码审查 Passed**。下述初检 P2 已关闭，修正内容、独立重跑和最终摘要见文末复核关闭记录。

## 初次发现：本地化目标标题的契约需明确

**[P2] “existing `## Goal`” 并非所有保留布局实际具有的标题。** 新段落六语言都要求使用现有 `## Goal`，但随包保留的本地化 `templates/task_plan.md` 实际分别是 `## 目标`、`## 目標`、`## Ziel`、`## Objetivo`、`## الهدف`。单纯要求向不存在的 Goal 段写入，可能促使建立第二目标段，或让 Agent 沿用本地化标题却以为 smart 会保留该段。

这是提取器的实际区别：固定 PWF `inject-plan.py` 的 `smart_plan_extract()` 只识别英文 `## Goal`；没有识别到英文 `## Phases`/`### Phase` 时返回 None 并回退 head。若计划包含英文 Phases、但目标段保持本地化标题，smart 提取成功却不包含该目标段。已有入口要求保留 `### Phase` 等解析器字面格式，因此不能假定所有本地化任务永远处于纯本地化 fallback。

最小建议：明确复用原目标段；对已获准编辑的任务计划，将该段规范为 canonical `## Goal`，保留本地化内容或标题说明，不再另建第二目标段；受保护布局/只读/明确禁止迁移时仍服从原限制。另一种保留本地化标题的选择必须如实说明 head fallback 和 mixed-layout 限制，不能声称该布局获得 smart 保证。无需修改固定上游提取器来扩大机制。

## 源码支持的结构依据

- `inject-plan.py:1133` 的 PreToolUse 路径使用 `plan_view(plan, 30, smart)`。普通模式取前 30 行；`plan_view()` 再按 65536 字节限制截断。前 30 行不等于任何长度的正文都完整送达，摘要仍需简短。
- `smart_plan_extract()` 在 `:696-703` 保留 Goal、Next Step、Current Phase；活跃阶段与部分决策另行选取。独立 `## Scope` 即使放到文件开头，也不是保留区段。
- Shell `inject-plan.sh` 的 `emit_plan_head()` 与 Python 同样在 smart 无法识别结构时回退 head；PreToolUse 采用 head 30。此设计沿用已有提取行为，不新增 hook、helper 或磁盘状态。
- 入口要求按实际用户/项目来源填写授权对象、禁止读取/写入和验证限制，而不是只抄通用规则；这针对 RC10 实际 owner 记录漏掉具体实验边界的问题。将同一摘要放入被提取的现有目标区段属于有源码依据的记录布局调整。
- 附录从第二份 `Authorized work and constraints` 值改成指向 Goal 的维护规则，避免维护两份 live scope。scope 摘要记录授权事实及其来源，不构成新授权。

## 离线最小反例

只提取并执行已有 `smart_plan_extract()` 纯函数，未运行 injector、文件写入 hook 或容器。相同 `SCOPE_TEST_MARKER` 放在前 30 行目标段，结果：

| Goal 标题 | Phases 标题 | smart 是否 fallback | smart 输出保留摘要 | head 30 保留摘要 |
| --- | --- | --- | --- | --- |
| `## Goal` | `## Phases` | 否 | Passed | Passed |
| `## 目标` | `## Phases` | 否 | **Failed：摘要被过滤** | Passed |
| `## 目标` | `## 阶段` | 是 | 不适用；实际回退 head | Passed |

此处 Failed 是契约反例，不是一次新模型运行。主 Agent 后续正式提取对照测试及准确包验证应包含本地化/混合标题和 fallback。

## 已保留的边界

六语言新增段落在只读/简单任务/明确禁令的范围判断以及拒绝、恢复、初始化分支之后。现有只读短句仍明确不创建或修改项目记录；新增要求没有授权只读任务为了补 scope 而写计划。明确禁止新文件、采用或改变旧权威入口的例外仍要求实际指令依据；不得把计划模板当成越过这些例外的许可。

六语言均包含实际来源、任务具体约束、简明摘要、前 30 行、单一维护位置、记录而非授予权限等含义，没有发现新增语义分歧。没有要求 hook 自动写项目文件，也没有改写批准要求。

这项变化最多改善**初始化之后**任务范围在文件恢复/提醒中的可见性。RC10 Claude 的宿主配置读取在原始调用第 626 行，计划到第 8736 行才初始化；此改动无法补救那个已经发生的访问。RC10 原始 scope Failed 不变。该轮 raw 也未呈现可绑定的 ACTIVE PLAN/frame 内容，因此不能把静态提取缺口说成已证明的行为因果链，更不能声称范围摘要足以约束模型。

## 初次受审源码摘要

以下摘要与同一次读取到的新增 scope 段绑定；路径相对于 `overlays/planweft/`。

| 文件 | SHA-256 |
| --- | --- |
| `entrypoints/en.md` | `888fb51e08cbfc88cc7b6a0860fa93eb580466d53b8fee1ae47990732608fa9c` |
| `entrypoints/zh.md` | `8b129acecd15181d582b0765812f89f424d3620ec78b39098f39685ccb8c5d7f` |
| `entrypoints/zht.md` | `7563381c87121da99b28bf22390a3390aec2aac187c337d053bf30aa16c0b591` |
| `entrypoints/de.md` | `ec339016371eda64875b439780814f117da35cc6d3a7cc65b08e86c97552b879` |
| `entrypoints/es.md` | `72f8fd0e88e5f4b5ea9fad3f101d50467d2f664f470b702466da8d26f78dcda8` |
| `entrypoints/ar.md` | `c904c3cc91651384d2ce75e6073b1ee7eac1915ad38870028fc254e75de751f6` |
| `templates/task_plan.append.md` | `95ed82c3a0d976cf9946b1bb98c5d54c819289b1ed839674c63fc675a5ad058d` |

初次结论：结构方向有依据，标题契约 P2 待明确；模型、实际提醒送达与完整跨宿主效果仍 **Not Run**。

## 复核关闭：本地化标题 P2 已解决

主 Agent 修正后，reviewer 实际重读六语言当前入口。新文案先称“现有目标段”，仅对**新初始化的计划**将这一个目标标题规范为 `## Goal`，保留正文原语言且明确不增加第二目标段。已有受保护标题保持原样；文案明确 smart 可能忽略本地化目标，需读取完整计划，不假定提醒已经保留范围。六语言包含相同的限制和替代操作，没有把所有旧计划强制转换为新标题。

因此上述 P2 已在源码层面关闭，**最终源码审查 Passed**。初检问题保留为修改历史，不再代表当前源码仍待修复。第 1 步的只读/明确禁令继续先于记录写入；模板指向现有目标区段，并未增加第二份范围值、自动写入或新的授权来源。无法更改受保护布局时完整读取计划，是明确的能力限制，不是 smart 行为已被修改的主张。

reviewer 阅读并独立重跑了 `tests/test_scope_recovery.py`：

```text
python3 -m unittest discover -s tests -p test_scope_recovery.py -v
Ran 2 tests in 4.107s
OK
```

测试从固定上游经现有构建器迁移的 `inject-plan.py` 导入真实 `head_lines()`、`smart_plan_extract()` 和 `Injector.plan_view()`；未调用完整 injector.run 或 hook。覆盖末尾附录与 Goal 的对照、唯一摘要、Next Step 保留，以及纯本地化 fallback、混合标题遗漏和一个目标标题规范化后保留；各自包含 LF/CRLF。临时导入文件由 `addClassCleanup` 清理。测试证明提取契约，不证明模型按要求填写/规范标题，也不证明上下文实际送达宿主。

最终源码和测试摘要：

| 文件 | SHA-256 |
| --- | --- |
| `overlays/planweft/entrypoints/en.md` | `7143f66c0cc5bcd5fcec12025a547efc850d2cc4f6230e672bb2a8ec55c202be` |
| `overlays/planweft/entrypoints/zh.md` | `a7e0f1dafa39b0332e8a0f3748977c67adeb11dac06076e6d725f35d1f5210e7` |
| `overlays/planweft/entrypoints/zht.md` | `c4548c9ede9781f2e1cb460740aeeef5130708d998303b23ed1f9a7b776de056` |
| `overlays/planweft/entrypoints/de.md` | `2776b7771f0d16e82367496b2ada0403a09ce87487cbaf5669cc524cdae5b049` |
| `overlays/planweft/entrypoints/es.md` | `4ee1c1410020dbe40873bbda0b92cdfb53b84791707a13a1e167eac0c2f58d0a` |
| `overlays/planweft/entrypoints/ar.md` | `c7458acd4f946b836c84dd904bcc22116e5f6e872f2b23d693dedec706fbafa9` |
| `overlays/planweft/templates/task_plan.append.md` | `95ed82c3a0d976cf9946b1bb98c5d54c819289b1ed839674c63fc675a5ad058d` |
| `tests/test_scope_recovery.py` | `4ed03bb4db3ac647edd7d5da7cdd2377b940d268bdcc06aff69c345357065f20` |

主 Agent 提供的两项测试日志 SHA-256 为 `5a7cab5f3e8e191932b0764540ba9f3d65ecfd5dbde93a91e3673f7ed8798537`；其 4.153s 运行与上述 reviewer 4.107s 重跑分别记录，不混为同一次执行。

最终限制保持：准确 RC11 模型效果、原生实际提醒送达、跨宿主完整行为仍 **Not Run**；这一修正不能解决初始化前的配置访问，不能改变原 RC10 Failed，更不表示建立了强制权限隔离。
