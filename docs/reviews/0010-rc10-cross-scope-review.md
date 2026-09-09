# RC10 跨 scope 安装预检独立审查

日期：2026-09-09。审查者：独立 review subagent。

## 结论

- **Passed：** Pi/OpenCode 项目安装预检补查全局注册的离线回归；合法自有注册、同版本 OpenCode Skill-only 配对仍可用。
- **Passed：** JSON 转义的自有路径误报修复。首次发现与失败复现保留于下文，不以最终通过抹除。
- **Passed（源码与离线边界审查）：** 新 `native-duplicate` 入口可用于“真实全局注册后拒绝第二次项目注册预检”的有限验收。
- **Failed（已独立核验的 RC9 原生负对照）：** OpenCode 全局 loader 已被原生宿主发现，但第二次项目 dry-run 返回 exit 0。该失败保留。
- **Passed（修复后离线）：** 正反 scope 的已知 loader、配置和 same-root alias 分支验证通过；准确修复包的原生复验仍须另行绑定。
- **Not Run：** 本 reviewer 未执行容器、真实宿主或模型；仅检查现有原生证据。实际双 hooks 执行与提醒去重未验证。

## 修复依据与失败历史

`detectDuplicates` 原先只检查当前 scope 的 Pi settings/OpenCode 配置。首次最小离线复现中，两个宿主的默认和自定义全局配置四个负向分支均出现 `Missing expected rejection`，两个自有注册正对照通过。

当前修复为 project 预检补查全局注册文件，尊重 `PI_CODING_AGENT_DIR` / `XDG_CONFIG_HOME`，并通过 `foreignChecks` 禁止把项目的 nativeSource/catalog 豁免套用到另一 scope。另一 scope 即使引用相同 Pi source，仍拒绝；当前项目原有 source 仍允许。OpenCode 同版本 npm runtime 搭配 Skill-only 不增加第二个 loader，继续允许；异版本和完整运行时安装拒绝。

首次修复新增本地路径识别后暴露 P2：`text.split(old.nativeSource)` 匹配不到 JSON 转义后的路径。Windows 反斜杠和带双引号的 POSIX 路径两项叶测试均误报 `Another planning registration`。最终在非 foreign 分支先排除完整 `JSON.stringify(old.nativeSource)`，再保留原有 raw 匹配，两个回归分支均通过。这是序列化单元证据，不是 Windows 原生运行证据。

## 独立验证

```bash
node --test --experimental-test-isolation=none --test-reporter=spec tests/installer.test.mjs
python3 -m unittest discover -s tests -p test_fixture_containers.py -v
```

- 首次闭环 Node：46 test records Passed，0 Failed，0 skipped。后续追加 loader/反向 scope/alias 测试并修复 alias 回归后，完整复跑 **64 test records Passed，0 Failed，0 skipped**。数量包含父测试；不是 64 个原生场景。
- Python wrapper：4 tests Passed。Docker 和 subprocess 均被 mock；这些测试只验证无副作用输入拒绝、资源预检、超时及清理控制、worker 场景路由。
- `git diff --check`：Passed。

## 新原生入口的证据强度

`run-native-duplicate.py` 通过 archive 内的实际 installer 安装全局包，记录宿主版本和安装命令；随后进行原生查询、项目 dry-run、状态比较、再次原生查询及自有 doctor/update dry-run。预检没有拒绝或保护快照改变时，结果为 Failed。不会为了失败负对照实际创建第二套运行时。

- Pi `pi list --approve` 证明原生 package manager 中能看到 receipt 所指 source。它不是 RPC Extension discovery；若要声明 Extension 实际加载，还需要已有 RPC `get_commands` 并绑定来源等证据。
- OpenCode `debug agent build` 验证工具可见，`debug skill` 验证单一主 Skill。它们比目录扫描强，但单个 tools 键可覆盖冲突，不能证明两个 handler 曾同时执行或被正确去重。
- 当前 `PLANNING_DISABLED=1` 与 model_sessions / execution_time_deduplication 的 Not Run 标识一致。不可把此入口用于宣称模型上下文、提醒去重或停止机制已运行。
- 第二次操作是实际 installer 的 `--project --dry-run`。同一 preflight 也是写入前路径，因此可证明此次拒绝机制；不是完整第二次安装生命周期。
- 全局 remove 后仅检查 receipt 中 agents 清空。这是本场景的自有清理检查，不证明原生卸载无文件、符号链接或缓存残留。

## 隔离、资源与清理

wrapper 在输出创建前校验 archive SHA、安全成员、参数、固定镜像身份、资源余量。只接受 Pi/OpenCode 的 native-duplicate 场景；无认证/模型参数。worker 使用新合成 HOME、项目、TMPDIR，保留最小命令环境；wrapper 拒绝含凭据的代理 URL。

容器采用只读根、非 root UID、cap-drop/no-new-privileges、2 CPU、3 GiB 内存与总 swap、256 PID、512 MiB tmpfs，单宿主串行，整体超时至多 600 秒。失败终止后续宿主；清理校验随机容器名与唯一 ownership label，失败时不删除缓存证据。项目保护文件和预检前后注册快照有明确断言。网络用于包依赖的真实安装，不是离线或无网络运行。

## 尚未闭合的范围

1. **OpenCode 全局 local loader：** RC9 实测证实漏检，原始 Failed 见下文。后续检测覆盖已知 `plugins/planweft.{ts,js,mjs}` 与 Pi `extensions/planweft.ts` / `extensions/planweft/index.ts`，正反方向离线通过；任意别名 loader 和准确修复包的原生结果仍不能从离线测试推定。
2. **反向 global 安装：** 后续修复现在检查调用目录对应项目的 Pi settings、OpenCode 原生 root JSON/JSONC 和已知 loader；新增三种配置、十种 loader 的方向组合通过。没有遍历其他项目，仍不能声称全项目或任意宿主来源的完整去重。
3. **真实双 hooks / reminder dedup：** 本入口验证第二注册预防，无两个 hook 的实际调用与投递计数。该门槛仍需独立原生事件和模型上下文证据。
4. **发布证据绑定：** wrapper 绑定 worker、wrapper、archive 和 raw summary；日志与 before/after 附件仍应在最终验收记录逐一绑定 SHA。只引用 summary 的 Passed 不足以替代原始证据审查。

## 后续 alias 复核与处置

初版已知 loader 检查会把 `XDG_CONFIG_HOME/opencode` 指向项目 `.opencode` 的同一自有 loader 判为 foreign。独立正对照当时 17 Passed / 1 Failed（含父记录），失败为 doctor 返回 1。不能仅跳过同名根目录，否则可能同时放过额外 foreign loader。

最终按 `realpath` 只豁免已由 `assertRecord` 验证、与旧 receipt component 指向同一文件的 loader；设置路径同一实体也不重复按 foreign 处理。Pi 同根设置正对照、OpenCode 自有 `.ts` 的 symlink alias 正对照、alias 下额外 unowned `.js` 仍拒绝，均通过。当前已无该回归的未关闭测试。

## RC9 原生负对照：保留 Failed

现有运行标识：`rc9-opencode-duplicate-baseline`。本 reviewer 只读其合成项目和运行附件，没有重新执行宿主。

- 包：`0.4.0-rc.9`，archive SHA-256 `06eb7aa07a7d90761dd2b5727d572849791f0191ba0f660c3ab0040921c5d395`。
- 宿主：OpenCode `1.18.22`；镜像 `sha256:35d7e7989b6fdbefb83135c647cf3eefffcd843b6a6a2a6b0587ced548efeec1`。
- global-install exit 0；原生 `debug agent build` 显示 `pw_init/pw_status/pw_check` 可见；`debug skill` 显示单一 `project-docs`，位置为本次合成全局 Skill 路径。
- second-project-preflight 实际 exit **0**，输出待安装项目完整 runtime 的 dry-run options；worker 因 `Second registration preflight was not rejected` 返回 Failed。
- before.json 与 after.json 完全相同；project_records_unchanged=true；wrapper 确认唯一所属容器已移除，保留失败缓存/日志。
- 这是“真实第一套已加载后，第二次预检漏拦截”证据；没有真的安装第二套，更没有两个 hooks 的调用计数，不能称为双 hooks 执行证据。

附件哈希以该运行目录为基准。只绑定生成的日志、快照、summary 和 frozen 执行器；不读取认证、native 历史或依赖缓存。

| 附件 | SHA-256 |
| --- | --- |
| `summary.json` | `301d2115b93a63d1b1653b4a62d672104922f6e2b7ac45502c8c5818b95ba455` |
| `opencode/container.json` | `33d9e0ee096d64197752ee2ddc7cc02b7e371e496195cb748aefd79c7d6ac4d7` |
| `opencode/container.stdout` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `opencode/container.stderr` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `opencode/run/summary.json` | `ee26e1311f0b7a6b18090513311785bfb19badcbb7557dc6b01cfc982cf892b4` |
| `opencode/run/version.log` | `c8df13def282c20b16211441bc3151c9ba7dd42ddf81f16525bbabebb9222736` |
| `opencode/run/global-install.log` | `71461b89a2ee301d19d787b9807a976a12897e318df2f6dc2095ad6d8f810de9` |
| `opencode/run/native-before.log` | `141fbe13ac2dd3dc68e7cdce3f1938d62526a0fd14d2752a8e638c38b59f7345` |
| `opencode/run/native-before-skills.log` | `0c86b42a65f4eebdd00b1e0c66c816a3c3417f6a8a306c8c8badaf26764d064f` |
| `opencode/run/second-project-preflight.log` | `08a59758792f4654b953702225c1bcbf8ef73ce011f08eb4dc6c6a5b0ed8dbfa` |
| `opencode/run/before.json` | `06b5bd073328df48823e01850cbe808b0678793d8e7c2389e1cce3ab583fdde4` |
| `opencode/run/after.json` | `06b5bd073328df48823e01850cbe808b0678793d8e7c2389e1cce3ab583fdde4` |
| `frozen/container-images.json` | `9a0b159a93aa3acdd5669e521608aeec00ffd0d6533fa37a397472e24d329216` |
| `frozen/run-fixture-containers.py` | `9b099b4323889205f0d23839072d0379d5cddf5b9064ba318716da99c9d61479` |
| `frozen/run-installer-lifecycle.py` | `43f1d007540a4cc856fcd5ab91d4935143d50f41fb492d784c79b1f5d074019e` |
| `frozen/run-native-duplicate.py` | `56dde6c6609551d439aca4e91d092afd151814a9c6e2bde0141c79fd0bd7d829` |
| `frozen/run-project-isolation.py` | `67a667a43c80de58f53d5baf60ac9eec960cafa8afbb2966fe5fc2fcbb0907d0` |
| `frozen/run-registry-containers.py` | `6ae0078428f560ba733c8ae5295c4e01871b4ad9109c64f29a54a414324db81d` |

## 本次源码绑定

| 文件 | SHA-256 |
| --- | --- |
| `lib/installer.mjs` | `788be5868dda89e87ce875b0cdb1e204155469f8b395d8260c6541e7c8fcee66` |
| `tests/installer.test.mjs` | `a4a1452ebf330694790731a9f7e847356cb8affb52d58a0187c359bf54a0cec8` |
| `tests/run-native-duplicate.py` | `56dde6c6609551d439aca4e91d092afd151814a9c6e2bde0141c79fd0bd7d829` |
| `tests/run-fixture-containers.py` | `9b099b4323889205f0d23839072d0379d5cddf5b9064ba318716da99c9d61479` |
| `tests/test_fixture_containers.py` | `d53fb7c95d1302a6567bfb2b1b58303ca831bf4c4af9faedc70323c475a84433` |

本次 reviewer 只补充测试和独立 review 文档，没有修改运行时，没有 Git 提交，也没有执行模型或容器。
