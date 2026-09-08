# 0.3.0 目录分发与原生生命周期证据

完整结果见 [REP-0006](../../0006-native-distributions.md)。本轮保存新的 0.3.0 运行输出；0.3.1 仅是 A/B 变更 fixture，不是已发布版本。

- `raw-evidence.tar.gz`：实际命令/退出码/日志、runner 快照、安装文件清单、原始与移植 JUnit、Codex 合成 Responses 请求、原生加载与扫描结果、初次失败及独立修复证据。
- `manifest.json`：归档 SHA-256 与逐文件 size/SHA-256。成员名限定为相对路径；采集器脚本也在归档中，列出具体来源与排除范围。
- `summary.json`：最终状态索引、宿主版本与目录来源摘要。测试环境路径用于复现，没有远程已发布坐标。

归档不包含认证、临时 HOME/profile、node_modules、venv、缓存或整份重复源码。保留的项目片段、Skill 文本和请求来自合成 fixture；不调用付费模型。已做常见密钥模式检查，结果写入 manifest；该检查不构成对任意敏感信息不存在的证明。原始日志保留本机路径，公开转发前需要审阅并对路径脱敏，不应把此内部证据归档原样作为上游 issue 附件。

真实生命周期区分市场注册、安装、更新、发现、卸载和缓存清理。Codex/Claude/Gemini/Pi/Copilot/CodeBuddy 按完整内容与执行位核对；OpenCode 调用真实 debug loader 及其工具；Factory 检查实际 active installPath；Hermes 保留默认扫描拒绝。没有把 CLI 管理命令通过等同于实际模型会话理解，也没有把本地渠道当作远端更新验证。

上游对照显式使用隔离 GNU mkdir；63 个跳过及 ini 的 Node engine 警告保存在日志中。初次 Gemini 信任确认超时、Codex provider 配置错误、CodeBuddy loopback 拒绝和 OpenCode 网络沙箱拒绝与最终结果分开，不删除失败历史。

校验示例：

```bash
python3 - <<'PY'
from pathlib import Path
import hashlib, json, tarfile
root = Path('docs/reproduction/evidence/0006')
m = json.loads((root / 'manifest.json').read_text())
p = root / m['archive']['path']
assert hashlib.sha256(p.read_bytes()).hexdigest() == m['archive']['sha256']
with tarfile.open(p, 'r:gz') as archive:
    assert {x.name for x in archive.getmembers()} == set(m['files'])
    for item in archive.getmembers():
        data = archive.extractfile(item).read()
        assert len(data) == m['files'][item.name]['size']
        assert hashlib.sha256(data).hexdigest() == m['files'][item.name]['sha256']
print('Passed')
PY
```

复现需要对应官方 CLI；runner 不下载全局工具。Factory/Hermes 一次性 runner 与原始版本/扫描说明位于归档；其他入口已在 tests 中。公开发布或远程更新测试必须另有授权和真实来源，不可把 `example.invalid` scoped 打包 fixture 当作发布仓库。
