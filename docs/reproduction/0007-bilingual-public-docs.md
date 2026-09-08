# REP-0007：双语公开文档与生成验证

日期：2026-09-08；基线：`ff9e6a4`；产品保持 0.3.0。范围见 [PLAN-0007](../plans/0007-bilingual-public-docs.md)。本轮整理项目说明与交付文档，没有修改任务状态协议、运行脚本、hooks 或 JavaScript。

公开入口包括 [README 中文](../../README.md) / [English](../../README.en.md)、[安装中文](../installation.md) / [English](../installation.en.md)、[跨平台设计中文](../platforms.md) / [English](../platforms.en.md)。各平台安装包的 README 与 INSTALL 也提供中英版本；内部工程记录保留原文并在公开引用中标明语言。

## 结果

| 检查 | 结果 | 具体范围 |
| --- | --- | --- |
| 公开文档链接与语言配对 | Passed | 首页、独立指南、overlay 及14平台包；开头双向切换、公开引用并列中英、本地相对链接存在 |
| 安装内容一致性 | Passed | 中英17个命令块逐字相同；独立review核对14平台步骤及23个官方URL，人工核查翻译语义 |
| 确定性与漂移 | Passed | 重复构建无变化；`--verify` 覆盖两份仓库安装镜像，手改英文指南时拒绝且不自动修复 |
| 本地回归 | Passed：54 tests | 原有运行协议、分发、生命周期参数边界，加双语导航/命令/包完整性检查 |
| OpenCode编译绑定 | Passed | 使用已有锁定工具链重编译，`--check` 无差异；实际JavaScript不变，仅文档allowlist使编译输入摘要变化 |
| npm实际产物 | Passed | OpenCode包230文件、Pi包49文件；两包的README.md、README.en.md、INSTALL.md、INSTALL.en.md与对应dist字节完全相同 |
| 运行文件变化审计 | Passed | 相比基线，14平台只变README/INSTALL语言文件、Pi/OpenCode files清单及OpenCode BUILD绑定；运行脚本、hooks、Skills、模板与编译JS均未变 |
| 来源与原创归属 | Passed | 两名reviewer按非作者范围交叉核查；比较表依据固定原文，不宣称首创文件规划/ADR/冷读或效果排名 |
| 真实宿主、模型与扫描器 | Not Run | 本次为文档与打包包含调整；REP-0006的8宿主与Hermes拒绝是历史证据，不冒充本轮产物已实测 |

仓库安装指南与包内正文来自同一对 overlay 文件；构建仅对对应位置的导航做适配，不分别维护正文。npm包保留英文文档由实际打包清单确认，不能只以磁盘存在代替入包。

## 发现与修复

- 独立审查发现跨平台初稿将 `PLANNING_DISABLED=1` 的充分关闭保证写得过宽，已在中英两版明确仅限已验证路径；严格只读或完整关闭使用宿主禁用机制。
- 验证矩阵原稿对历史日期的表述可能让读者误认为本次重跑宿主，已明确历史来源与本轮未运行范围。Hermes 42/41 findings 属于先前包，不预测加入英文文档后的扫描数量。
- 首轮54项测试中，53项通过，1项失败：overlay README引用包根的 INSTALL.md，在源码目录中不存在。源码链接改为 install/INSTALL.md，生成器在包内明确转换为 INSTALL.md；英文同样处理。定向复验通过，生成包字节与修复前相同。

审查范围与关闭依据见 [公开文档审查](../reviews/0007-public-docs-review.md) 及 [README/分发独立审查](../reviews/0007-readme-distribution-review.md)。参与比较表建议的 reviewer 明确披露参与范围，比较/原创段另由未参与作者独立复核。

## 可重复检查

```bash
python3 scripts/build-plugin.py
python3 scripts/build-plugin.py --verify
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 scripts/prepare-native-release.py --output /tmp/pd-public-docs-release-new
```

输出目录必须新建。最后一项只准备本地npm包与Git发布树，不发布、不push；运行时编译可按开发说明复用已有锁定工具链，本次未安装新依赖。具体日志、文件变化与npm摘要保存在 [证据目录](evidence/0007/README.md)，历史失败也保留。版本、安装命令与支持范围没有因翻译而升级为新的兼容性保证。
