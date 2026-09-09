[中文](0010-rc14-checkpoint.md) | [English](0010-rc14-checkpoint.en.md)

# RC14 候选发布与 Claude 采集检查点

`0.4.0-rc.14` 已发布到 npm `next`，正式 `0.4.0` 尚未发布。`latest` 的历史 RC1 不代表稳定发布。本记录是完成时的检查点；后续状态以[当前计划](../plans/0010-five-agent-release.md)为准。

- 冻结源码：`6e54876bf6249bb1d83514767920fdeb793f3573`。
- 官方远端准确包：5,462,803 bytes；SHA-256 `9ecfd09b82d118a99f7593fa3fcd948234a334ac11f7c2e06d63e446e693b85a`。SHA-512 integrity 与 SHA-1 也匹配。[npm 候选版](https://www.npmjs.com/package/planweft/v/0.4.0-rc.14)。
- [三系统 CI](https://github.com/psiQAQ/planweft/actions/runs/34382490295)与[OIDC 发布](https://github.com/psiQAQ/planweft/actions/runs/34383018444) Passed。CI 重建包与上述准确摘要匹配后才发布。
- 直接依赖仍为用户批准的 `toml@4.3.0`，没有升级其他包。RC14 修改的是六语言采用分支与中英本地操作例程，模型效果仍需实际任务证明。

初次 Windows CI 因默认 cp1252 读取中文文档失败；显式 UTF-8 读写及强制 ASCII 子进程反例修复后，三系统通过。旧 `2c96af78` 归档不用于发布。一次 worktree 打包因容器无法访问 `.git` 指针失败；改用自包含隔离 clone。随后一次短 SHA fetch 失败后误启动旧源码打包，该产物也排除；最终准确包绑定上述完整提交。首次远端查询使用了个人 npm 默认镜像，严格来源检查在下载前拒绝；显式选择官方 registry 后通过，不修改个人 npm 配置。

Claude 的提醒诊断使用已发布 RC13 准确包 `793e3f2c…09bda`，而非 RC14：独立审查确认同进程两回合、四次串行 Write、原生结果与实际文件一致、受保护项目记录未变，Docker 退出码为0，私有追踪清理通过。**采集 Passed，归因 Incomplete，提醒去重 Not Run**。实际 native init 指向受管 marketplace payload，旧测试器却绑定 cache；另一个未完成 read 没有观察到 FD 创建来源。不能据 `fs.watch` 线程名、读取长度或空 hooks 数组判为无关或去重成功。

测试器已修正实际加载根的 manifest 内容校验、会话路径绑定及逐文件/目录链接拒绝；独立审查的原始发现和关闭证据保留。离线七 hook 预检观察到 PostToolUse 字节 `187, 0, 187, 0`，但它没有模型，不能替代真实投递验收。追踪仅导出受限数字、固定枚举与摘要；已认证原始 syscall 轨迹在私有目录销毁，无认证/无网络诊断原轨迹另行私有保留。

[脱敏证据包](evidence/0010/rc14-candidate-and-claude-trace.tar.gz)共115项，427,682 bytes，SHA-256 `fa2f27ca2b411618b28d7a19ea1617f5104fa6b73ba98c52fc796b2e7cff3cc8`。manifest 同时记录原始与公开字节摘要；含原始失败、冻结测试器、项目快照、独立审查和 CI/registry 结果，不含认证、可重建安装树或私有原轨迹。

后续必过项仍包括五核心宿主模型行为、权限/停止/去重、维护和独立交接，以及最终稳定准确归档与远端生命周期。Windows/macOS 真实宿主、GUI 未执行项保持 Not Run；三系统安装器 CI 不等于这些场景通过。
