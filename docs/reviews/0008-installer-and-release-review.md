# REV-0008：独立安装器与公开发布审查

范围：单 npm 的入口/依赖、安装器所有权/范围/失败恢复，以及原 master@07e79c0 的公开历史。
主 Agent 实施；独立 reviewer 只读审查并在临时 fixture 复现，不修改实现。

## 实现复核

发现并处理：外来 catalog 重试覆盖、卸载后 registry 残留、Claude 其他项目误判、
full/skill-only 切换遗留 hooks、Gemini 拒绝替换后丢状态、Pi 替换失败恢复、
node_modules/锁完整性、payload staging、部分组件删除接续、部分复制失败恢复。

独立最终定向复核：17 Node tests Passed，0 Failed/Skipped。复核指纹：

- lib/installer.mjs：3f417b82681e50c6dcfb50a41c8618fc3b502b1d2d45782c834c62d687c44d19
- tests/installer.test.mjs：6c5d5248b83b1e50a56ed1f237d8a06408e098230078e2abd274340e52ec9511

该指纹之后的宿主实测修正另行记录：Pi 显式单次 project approve、OpenCode 原生 .ts loader
与辅助命令、Codex 配置目录初始化及本地 marketplace 不调用不存在的 update。
这些变化由主 Agent 运行原生生命周期及相同故障回归，不将先前指纹冒充最终全量独立审查。

## 公开历史审查

检查 16 个提交、975 个可达对象、626 个唯一 blob、26 个归档（含嵌套 ZIP）。
未发现真实凭据或 RFC1918 地址；常见 key/token 命中已核实为 fixture。
8 个证据文件含本机路径或 tar owner/group 元数据：

- evidence/0004/raw-evidence.tar.gz
- evidence/0005/installation/codex-preflight.tar.gz
- evidence/0005/host-environment.json
- evidence/0005/installation/program-design-installation-tests-executable-bits-failure.log
- evidence/0005/local/earlier-attempts/program-design-02-local-tests.log
- evidence/0005/regression/regression-evidence.tar.gz
- evidence/0006/raw-evidence.tar.gz
- evidence/0007/unittest-initial.log

路径均相对于 docs/reproduction。最早引入提交分别为 2dca0f6、3197f81、ff9e6a4、07e79c0。
新增清理提交无法移除历史中的这些内容；公开推送前需决定历史处理，不自动改写原本地历史。
固定 PWF 归档中的公开示例不作私人资料清理；本轮不修改该归档。

许可：PWF MIT 保留；研究子模块仅 gitlink；公开译文保留各自 MIT/CC 署名与许可。
根 MIT 不覆盖其他出版物。用户提供的文档布局材料保持来源/许可限制，不声称原创 MIT。
此审查不是商标或法律意见，也不能保证不存在任意编码的秘密。

## 最后增量复核

独立 reviewer 对上述宿主修正、文本 staging、旧计划链接与发布 gate 再次定向复核：
未发现阻止候选交付的新问题。独立执行安装器 17 Passed、发布 gate 2 Passed。

最终指纹：

- lib/installer.mjs：5177c6d12d75e38f6d60674d424443d05715e035d216831c3b8751c4eb89c714
- overlays/planweft/workflow.md：fb8009888a3c9499e4c848580a4c41826e8b79f97ec1325a1422e79bd95ee73d
- scripts/check-release-gate.py：d5fa33857f7608ad47b3eba9495bde0136c9dc5f867a6baab2f8bc42e6c2b3b8

结论仅覆盖列明源码和故障回归；真实模型与原生结果引用 REP-0008。

## Codex 真实维护与独立冷读复核

独立 reviewer 核对最终场景：README → notes/work → 唯一 task_plan 的相对链接均可解析，旧历史观察保留；批准需求、用户注释、README 与 AGENTS 逐字未变。新测试先失败，修复后两项测试和四组独立字节检查通过。冷读使用独立 ephemeral 会话、无插件、关闭 memories，仅读取项目文件，正确识别 Windows 验证为唯一下一步；前后快照相同。

首次场景的 `old_plan_points_to_task_plan=false` 仍记录 Failed，最终复测才 Passed。仅支持一次 Linux Codex 场景，不推断其他宿主、Windows/macOS、gated 或成功率。维护调用显式采用已审查 hook trust bypass；默认交互信任确认仍 Not Run。冷读前项目记录中的 fresh-reader Not Run 保留，后续结果记在外部验收中。

原始证据 SHA-256：

- maintenance/after.json：`fa8d677b3c577501850d9c96bfdb2a6e643a26f8ca82965b31d2642baff8ac72`
- maintenance/stdout.jsonl：`1a4237688948381a5f926eddbde1f441e2158fba7bcf86c2f21b5c19ad5c5bc0`
- cold-reader/stdout.jsonl：`3aebe92236ff6e3e64430cfadb64d8a7a79e63d99ac3f638c5f40baf9669ca99`
