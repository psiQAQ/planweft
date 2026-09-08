# 双语公开文档验证证据

结果说明见 [REP-0007](../../0007-bilingual-public-docs.md)。文件由本次实际运行输出复制，`manifest.json` 记录每份证据的 SHA-256 和大小。

- `unittest-initial.log`：首轮54检查中的overlay源链接失败；其余53项通过。
- `targeted.log`、`unittest.log`：修复后定向与完整回归。
- `build-verify.json`：14平台、Codex镜像、marketplaces和两份公开安装镜像无漂移。
- `compile-check.log`：锁定TypeScript重新编译一致。
- `distribution-delta.json`：相对基线的14平台逐文件差异；无运行脚本、hooks、Skills或编译JS变化。
- `native-pack.log`、`npm-contents.json`：实际npm准备与入包文档的字节/摘要核对，未发布到registry。

本次没有重新运行真实宿主、扫描器或模型；已有0.3.0宿主证据保持历史范围。原始日志可能包含本地路径，公开转发前应审阅。没有保存认证、依赖目录或宿主个人配置。
