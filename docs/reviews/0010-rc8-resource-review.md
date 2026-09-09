# RC8 安装验收入口资源与失败证据审查

本记录由独立 reviewer 对主 Agent 的修改进行源码复核和离线复验。范围仅为项目隔离与 A/B 安装 fixture 的资源和失败记录，不代表 RC8 或正式版已通过真实宿主验收。

结论：下列已发现问题在当前源码中已修复，相关 12 项离线测试 Passed。fixture 的**整个宿主场景最多 600 秒仍须由外层容器执行器保证**；其内部单命令 240 秒超时不能代替整个场景的预算。

## 原始发现与关闭情况

| 原始发现 | 修复与核查结果 | 状态 |
| --- | --- | --- |
| 项目隔离把 HOME、两个项目和解包源放在 `/tmp`，增加 tmpfs 内存占用，容器删除后失败 profile 与项目丢失。 | 全部改到挂载输出目录，TMPDIR 也固定在所属磁盘目录；失败记录与 profile 不随容器删除。已复核 worker 路径和挂载关系。 | Closed：源码 |
| 缺少启动前资源检查，tmpfs 为 2 GiB。 | 在创建输出目录或访问 Docker 前检查可用 RAM 至少 4 GiB、磁盘至少 8 GiB；tmpfs 改为 512 MiB。2 CPU、3 GiB 内存、总内存加 swap 3 GiB、256 PID 保留。资源不足反例证明不访问 Docker、不建输出。 | Closed：源码与离线测试 |
| 外层 timeout 为参数乘 30，可能超过批准的 600 秒整场上限。 | 参数只接受 1..600，外层直接使用该值。超时反例检查整个容器调用的 timeout，没有乘数。 | Closed：源码与离线测试 |
| 容器超时在写日志前抛出，partial stdout/stderr 丢失；cleanup 查询失败可能没有最终记录。 | 保存 TimeoutExpired 携带的 partial 输出；finally 写入容器失败、超时和 cleanup 结果。清理要求精确名称与所属 label，拒绝其他 owner，无法确认 daemon 状态时报告未清理。 | Closed：源码与离线测试 |
| fixture 没有独立磁盘 TMPDIR。 | 子进程 TMPDIR 固定为本次输出的 `tmp`，不继承用户任意临时目录；HOME 与 npm-cache 同样位于独立输出。 | Closed：源码 |
| fixture 解包、复制、A/B 构造和 npm pack 位于结果处理的 try 外，准备失败可能只留下 In Progress。 | 先写初始报告，再将准备与执行纳入统一异常处理。复制失败与 npm pack 超时/中断均生成 Failed，已产生的源和输出保留。增加实际 A/B 归档摘要，区分输入归档与修改后的 fixture。 | Closed：源码与离线测试 |
| 文件缺失使最终记录检查再次抛错，覆盖原始失败报告。 | `records_unchanged()` 对缺失、类型变化、链接及读取错误返回 False；删除 progress 后注入复制失败，仍保留原错误与 Failed 报告。 | Closed：源码与离线测试 |
| 二次审查发现：同字节 symlink 可以通过成功路径的字节比较，但最终记录字段为 False，造成 Passed/False 矛盾。 | 成功判定与最终字段共用 `records_unchanged()`；检查为 False 时明确失败。已补同字节 symlink 反例。 | Closed：源码与离线测试 |
| 二次审查发现：KeyboardInterrupt 跳过最终报告，命令超时不存 partial 输出，Pi RPC 没有 finally 清理。 | 统一捕获普通异常与 KeyboardInterrupt；超时写 partial 日志。Pi RPC 增加 finally、terminate/kill 和输出保存。pack 中断/超时已复验；Pi RPC 清理路径本轮仅源码复核。 | Closed：源码；pack 路径有离线测试 |

这些发现及初次、二次复核的残留均在本表保留；关闭表示当前修复通过上述检查，不将修复前状态改写为 Passed。此前归档预检与 Python 3.11 兼容解包继续保留，不是本轮新实现。

## 独立复验

```bash
python3 -m unittest discover -s tests -p 'test_installer_fixture_preflight.py' -v
python3 -m unittest discover -s tests -p 'test_project_isolation.py' -v
```

| 检查 | 本轮结果 |
| --- | --- |
| fixture 参数、准备失败、缺失记录、pack 超时/中断、同字节链接 | Passed：5 tests |
| 项目隔离输入、资源、超时留痕、所有权清理等离线契约 | Passed：7 tests |
| Docker、原生安装、模型、实际 OOM/磁盘耗尽 | Not Run：独立审查未启动这些场景 |
| Pi RPC 中断后的真实进程回收 | Not Run：本轮只有源码复核，没有原生进程故障注入 |

测试中的 Docker 和原生调用由 mock 替代；没有读取模型认证、调用模型或联网安装。上述数量是测试方法数，包含各自的反例分支。

## 被审查源码绑定

基础提交为 `a3d6cc3c41e2f6ffe636add694b6096fb342ba81`，审查对象包含其后的未提交修改，以文件摘要确定实际版本：

| 文件 | SHA-256 |
| --- | --- |
| `tests/run-project-isolation.py` | `67a667a43c80de58f53d5baf60ac9eec960cafa8afbb2966fe5fc2fcbb0907d0` |
| `tests/run-installer-lifecycle.py` | `43f1d007540a4cc856fcd5ab91d4935143d50f41fb492d784c79b1f5d074019e` |
| `tests/test_project_isolation.py` | `46bdd06da3b7571e4a2a5e66d268e137dd9231cd2ac1fd5a30ec71bd4d52c4f4` |
| `tests/test_installer_fixture_preflight.py` | `8c32c7fcc7857a3840fd13901e96c86bc20555ffb491a402ff0612fff4105029` |

## 执行与证据边界

fixture 仍是无容器管理能力的 worker。正式执行必须由外层提供批准的资源前检、2 CPU/3 GiB/256 PID、512 MiB tmpfs、磁盘输出、**总计最多 600 秒**以及超时后按所有权删除容器。内部超时负责诊断，不能保证所有后代进程都退出；容器清理是最后的资源回收边界。失败 profile、准确输入归档、已生成 A/B 归档和失败日志须保留。

项目隔离入口禁用了 planning hooks，只证明安装来源及受保护项目记录的隔离；Codex/DSH 的不支持项目级完整安装拒绝结果，不能替代运行时多项目上下文隔离。A/B fixture 修改了包内容，其证据不得充当未经修改的最终 stable 归档验收。正式放行仍需五宿主对最终准确包及远端来源的独立证据集合。

## 补充审查：fixture 外层容器入口

随后新增 `tests/run-fixture-containers.py`，承接前文要求的外层约束。本节补充原审查，不删除前文原始限制或失败发现。

源码核查确认：

- 先验证输入归档与摘要，再复用 registry 参数、完整镜像 ID 和资源检查；可用内存/磁盘不足时不创建输出、不访问 Docker。
- 每宿主串行执行，整次 `docker run` 使用受校验的 1..600 秒 timeout；采用 2 CPU、3 GiB 内存、总内存加 swap 3 GiB、256 PID、512 MiB tmpfs、只读根文件系统和只读脚本/输入归档挂载。fixture worker 的 HOME、项目、npm-cache、TMPDIR 保留在磁盘输出目录。
- stdout/stderr 直接写入各宿主输出文件；超时、中断、普通运行异常都进入 finally。复用精确名称和本次 label 的所有权清理，未确认清理则失败并停止后续宿主；失败 profile 与缓存保留。成功仅清理明确可重建的 npm-cache。
- 宿主返回零还不足以通过：检查 worker 的 Passed、宿主、输入摘要、受保护记录以及 A/B 元数据存在。保存原始 summary 摘要；外层状态始终标明这是修改后的 fixture，模型会话 Not Run。
- 保存 worker、wrapper、使用的 helpers 和镜像锁源码供审计。冻结文件是来源附件；本轮没有宣称该扁平附件目录可直接作为独立仓库运行。

独立运行：

```bash
python3 -m unittest discover -s tests -p 'test_fixture_containers.py' -v
```

结果为 **Passed：3 tests**，分别覆盖非法输入无副作用、资源不足无副作用，以及整场超时、清理失败、缓存保留和不启动下一宿主。Docker 调用均为 mock；没有运行容器、联网安装或模型。这些是失败路径和资源契约的回归，不替代正向真实安装与 A/B 产物内容复核。

| 新增或依赖文件 | SHA-256 |
| --- | --- |
| `tests/run-fixture-containers.py` | `73647b613f4b9ab0e0c08c61514a14d632b8aa0ed2841c88e06e2762f5cc4a83` |
| `tests/test_fixture_containers.py` | `64b782b05f1c81a1f331a2ed5143047f3d171c82fd4edcfa87e5851a8dc64ed2` |
| `tests/run-registry-containers.py` | `6ae0078428f560ba733c8ae5295c4e01871b4ad9109c64f29a54a414324db81d` |

worker 和 project-isolation helper 摘要仍与前表一致。就本次资源与失败留痕审查范围，没有新增阻塞性发现；fixture 的外层 600 秒承接已实现，实际运行结果仍需单独取得。
