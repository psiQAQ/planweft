# REP-0003：首版插件验证

日期：2026-09-07；开发基线：`4041f46` 加本轮工作区。本记录是有限场景观察，不是模型 benchmark，不保证自动匹配总会触发。测试入口：[run-plugin-smoke.py](../../tests/run-plugin-smoke.py)；验收来源：[SPEC-0002](../specs/0002-project-docs-plugin.md)。

## 环境和复现

Linux/amd64；已有镜像 agent-memory-lab/codex:local，SHA `aa46e31c71577eb37c1e1d856427d9d159ddd5a41aa92472af722838b1c3a159`；实际 CLI 0.149.1；模型 gpt-5.6-terra。没有构建或更换镜像。Python 标准库仅用于开发实验，不是插件运行时依赖。

```bash
python3 tests/run-plugin-smoke.py --output /tmp/program-design-plugin-results-new --model gpt-5.6-terra --cases enabled unenabled unrelated readonly conflict blank evidence-gap repo-copy
```

输出目录必须不存在，以免覆盖旧证据。该命令会调用真实模型，使用本机已有认证；须处于已授权的实验任务中。每个 case 启动独立临时容器，最多同时 3 个；enabled 完成后，另起新容器执行 handoff，不传旧聊天或预期答案。

容器以当前非 root UID/GID、cap-drop、no-new-privileges、只读根目录运行，只有临时项目和 tmpfs 可写。仅将当前插件分发副本挂载为只读 /source，将认证单文件只读挂载后复制到临时 HOME；不挂载完整宿主配置、历史和记忆。通过 host 网络沿用已有代理，故不是网络隔离；认证与宿主内置 Skills 等仍是 CLI 运行背景，不宣称纯净模型实验。

临时 HOME 中保留安装生成的配置，实际模型入口：

```text
codex exec --ephemeral --json --skip-git-repo-check --sandbox danger-full-access --model gpt-5.6-terra --cd /workspace -
```

Docker 提供文件边界，CLI 不再嵌套 bwrap。不能带 `--ignore-user-config`，否则安装产生的插件配置也会被忽略。安装、列表、卸载和来源移除均调用 CLI 子命令，完整结果保存在各 stdout 的 lifecycle 对象。

## 故障与修正

| 轮次 | 实际结果 | 处理与计分 |
| --- | --- | --- |
| manifest 首次校验 | 精简后的 author/longDescription/developerName 不满足本地官方校验器 | 补齐项目身份与实际描述；复验 Passed |
| 01 | Docker 未传 -i，CLI 报 No prompt provided via stdin | 修复 stdin；模型未执行，不能计行为通过；保留 [失败记录](evidence/0003/failed-01/enabled/stderr.txt) |
| 02 | 安装成功，但 ignore-user-config 导致模型找不到本 Skill；卸载断言又把其他内置插件缓存算为本插件残留 | 移除该参数；清理限定 program-design 并核查卸载后 installed 列表；本轮不计插件验证。保留 [完整代表轨迹](evidence/0003/failed-02/conflict/stdout.jsonl) |
| 03 | 实际加载和样例行为成立；repo-copy 输入只含文档，读者正确指出源码与原 Git 历史不可见 | 前 8 项有效；repo-copy 为夹具范围错误，不计仓库副本验收；补入第一方文本源码，明确历史/子模块省略，再定向复测 |

01/02 的程序行为不能用于证明产品正确；两轮清理均完成。失败留作实验记录，不将其误记为产品 bug。

## 已核查行为

第三轮每项均保留 prompt、before/after 文本快照、完整 CLI stdout/stderr 和退出码，位于 [run-03](evidence/0003/run-03/)。stdout 同时提供安装版本、enabled 状态、实际 Skill 读取命令和卸载结果；[机械核对汇总](evidence/0003/mechanical-summary.json) 由主 Agent 对比实际快照及 lifecycle 提取，语义结果另按下表逐项核对。

| 场景 | 预期及实际观察 | 判定 |
| --- | --- | --- |
| enabled | 项目 AGENTS 启用；实际读取安装的 SKILL.md；只改 notes/guide.md 和 notes/work.md，引用原约定，保留目录、用户未提交修改和历史，通过记录 Not Run 留下下一步 | Passed |
| unenabled | 只改请求的 README 标题，没有读取 project-docs 或生成管理文件 | Passed |
| unrelated | 回答 42，无文件变化，未读取 project-docs | Passed |
| readonly | 读取 Skill，指出 Windows 实测缺失，区分历史证据；文件字节不变 | Passed |
| conflict | 读取 Skill，指出改为有 BOM 与批准需求冲突；没有修改需求或其他文件 | Passed |
| blank | 显式调用成功，只有一份按需创建的规格，记录 UTF-8 无 BOM、未实现/未运行验证及下一步；没有永久 opt-in | Passed |
| evidence-gap | 读取 Skill，仅在现有计划记录指纹/写锁待研究候选及阻塞、下一步、Not Run；未伪造搜索或采纳机制 | Passed |
| handoff | 独立新容器仅从 enabled 的文件恢复目标、已完成、Windows 下一步、历史与本次验证区别；引用正确，无写入 | Passed |
| repo-copy | 第四轮完整第一方文本副本：确认 manifest/marketplace/Skill/测试存在，识别收尾进度与未验证项，明确历史/子模块省略属于快照限制；无文件变化 | Passed（定向复测） |

blank 的读取为 sed SKILL.md 后执行 rg 的复合命令：输出包含完整 Skill，整体退出 1 来自空项目未找到 AGENTS，不应将它当作 Skill 读取失败。evidence-gap 执行了 git diff --check；Not Run 指候选机制检索/实现验证没有执行，不等于完全没有静态差异检查。

源文件和插件安装缓存内容一致，分发 SHA 保存在 [环境记录](evidence/0003/run-03/environment.json)。正例由工具轨迹证明确实读到 `/home/agent/.codex/plugins/cache/personal/program-design/0.1.0/skills/project-docs/SKILL.md`，不是仅凭回答“使用了 Skill”判定。负例不读取 Skill 是预期，未据此声称所有无关任务都不会误触发。

## 定向副本复测

实际执行 `python3 tests/run-plugin-smoke.py --output /tmp/program-design-plugin-results-04 --model gpt-5.6-terra --cases repo-copy`，退出 0；完整证据位于 [run-04](evidence/0003/run-04/)。前后快照字节一致，实际读取安装的 Skill。独立会话识别源码、安装入口与测试脚本，准确报告收尾中的阶段和未验证项，并将省略的 Git 历史/研究子模块/历史原始输出区分为快照限制。

这次读取发生于最终回填计划和 review 之前；其“收尾中”结论对应保存的 before.json，不假称在最终 commit 上另跑过冷读。环境文件记录实际最终测试脚本 SHA-256，可与当前文件核对。

## 静态检查与限制

官方 plugin validator 与 Skill quick_validate 已 Passed。使用 REP-0001 的已审检查代码，将本轮来源范围改为 R-00～R-21，并纳入 plugins 下 Markdown；当前 48 份 Markdown、222 个本地文件链接、12 个固定子模块，缺失目标 0。旧记录的固定数量只适用于旧快照，保留原样。最后状态以本记录收尾复核为准。

Windows 原生运行：**Not Run**，本机为 Linux，未发现可用的本地 Windows 执行环境；没有以 Linux 或文件格式校验代替。桌面 UI 安装、多个模型比较、插件内部自动委派 reviewer 的运行行为、可联网新机制检索均 **Not Run**；本轮独立来源审查由主 Agent 实际委派，记录于 [REV-0003](../reviews/0003-project-docs-plugin-review.md)。

本仓库正式自身接管、迁移与真实个人 override 加载均 **Not Run**。未在个人 Codex 安装；示例项目的启用不等于本仓库启用。测试只证明所列行为，尚无成本或准确率提升数据。

## 清理

第三轮 [cleanup.json](evidence/0003/run-03/cleanup.json) 确认本轮标签下容器为空、原有容器保留、镜像 ID 不变、临时目录删除。容器 HOME 和认证副本随 tmpfs 消失；宿主原认证不改写。第四轮 [cleanup.json](evidence/0003/run-04/cleanup.json) 也确认相同边界。所有输出已归档；宿主临时输出目录在 review 后清理，最终状态见下方收尾结果。

## 收尾结果

9 个有限场景已完成，其中 repo-copy 修正夹具后定向复测；正负行为和安装/卸载分别核查。官方插件与 Skill 校验再次 Passed；最终静态复核 48 份 Markdown、233 处本地文件链接、12 个固定子模块，缺失目标 0。git diff --check 通过。最终 Docker 查询确认本轮标签无残留容器，原 10 个容器 ID 和 Codex 镜像 ID 均保持；四个宿主临时输出目录已归档后删除。独立依据及实验审查 REV-0003 Passed，无剩余阻断项。
