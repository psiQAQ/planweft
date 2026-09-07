# 定向阅读：如何评价首版文档协作

日期：2026-09-08；目的：为 PLAN-0004 的真实维护任务选择可观察的判据，不预设插件获胜。原文许可、中文范围和固定 commit 见 [参考索引](../reference/README.md)。

| 问题 | 精确出处 | 借鉴及本地差异 | 成本与验证 |
| --- | --- | --- | --- |
| Agent 能否找到正确入口和更新位置？ | R-01 Harness engineering：We made repository knowledge the system of record；Entropy and garbage collection | 使用短入口、按需资料与过期检查；文章经验不证明本插件效率，现有治理保留在两臂 | 记录阅读轨迹、错改/遗漏和人工纠正；不增加索引器 |
| 如何保护批准需求与历史？ | P-03 OpenSpec docs/concepts.md：Philosophy、Keep It Lightweight: Progressive Rigor、Artifacts、Delta Specs | 按行为写验收，区分现状与变化；不强制照搬 OpenSpec 格式/目录或引擎 | 根据内容评审，最小修改优先，不按模板命中评分 |
| 没有旧聊天能否继续？ | R-05 Anthropic：Incremental progress；P-06 skills/doc-coauthoring/SKILL.md：Stage 3 Reader Testing | 独立读者复核进展、验证和下一步；本轮四位读者均无插件，隔离交付文件的作用 | 四次冷读需要额外模型调用；记录真正执行的离线验证与限制 |
| 评分是否偏向某种工具？ | P-01 docs/evals.md：Grader validated against every method；What this test does not measure；Reproducing | 作者报告曾因目录检测漏记竞争方案；本地按可观察行为和文档内容评分 | 不复用作者数字；其原始 benchmark workspace 未随当前仓库提供，本轮没有复核上游数字 |
| 输入错误如何在副作用前报告？ | R-22 argparse：choices、type、Exiting methods | 使用已有错误语义，重复项/合法集合由用户需求定义 | 标准库离线替身验证，不启动 Docker/模型来测试参数错误 |

结论：本轮先修真实入口问题，再观察代码与文档产物。没有依据新增 hooks、状态协议或写回引擎；没有需要声称原创的机制。若发现重复问题，最多形成一项后续插件改进建议，插件本身仍固定 0.1.0。
