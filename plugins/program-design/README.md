# Program Design 插件

提供 `project-docs` Skill：在已启用项目中按任务读取资料、维护受影响的普通文档，保存交接及验证证据。沿用已有目录，只为实际工作创建必要记录。自动匹配依赖 Codex 判断，不能保证每次触发。

## 安装与使用

需要支持 plugins 的 Codex。从本仓库根目录执行；无需初始化研究子模块。repo marketplace 使用官方生成器默认名称 `personal`，这是此目录的 catalog 名，不代表已安装到个人配置。若已有同名 marketplace，先用 `codex plugin list` 核查来源，避免安装错误目录的同名插件。

```bash
codex plugin marketplace add .
codex plugin add program-design@personal
codex plugin list
```

安装后开始新会话。显式调用示例：“使用 $project-docs 根据当前计划接续工作”。这只授权当前任务；规划模式仍不写文件。

希望相关任务自动使用时，由维护者在宿主实际加载的项目 AGENTS 中加入：

> 本项目启用 project-docs：相关任务使用该 Skill 读取和维护受影响的普通文档，沿用现有目录并记录交接与验证；遵守当前任务的授权范围。

本插件不会自行插入启用声明。项目若使用 AGENTS.override.md，应放在实际生效的指令中；同目录 override 不自动叠加 AGENTS.md。插件安装与项目启用是两个步骤。已有项目无需迁移文件；缺少文档时按实际任务创建记录。

## 卸载

```bash
codex plugin remove program-design@personal
codex plugin marketplace remove personal
```

第二条只在该 marketplace 不再需要时执行。卸载保留项目文档；维护者可移除对应启用语句。注册、安装、加载和卸载分别验证；结果见仓库 REP-0003。

源码为本目录中的 manifest、Skill 和参考说明，无生成分发副本，无 CLI、hooks、后台服务和运行时包依赖。首版试用不代表本研究仓库已通过自身接管门槛。
