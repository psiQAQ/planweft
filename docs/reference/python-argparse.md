# Python argparse：入口校验与退出

编号 R-22；作者 Python Software Foundation / Python 文档贡献者。原文：[argparse 官方文档](https://docs.python.org/3/library/argparse.html)，定位 `choices`、`type`、`Exiting methods`。访问：2026-09-08。整理范围：中文要点摘要；原文适用 Python 文档 PSF License，本条仅摘要，不复制全文或示例代码。

## 原文要点

- `choices` 为命令行取值声明允许集合，解析时拒绝不在集合内的值。
- `type` 可以做简单转换或检查；复杂资源管理应在解析之后执行，避免后面的无效参数留下已打开的文件等副作用。
- `ArgumentParser.error(message)` 向 stderr 输出 usage 与错误信息，并以状态码 2 退出。

## 本地应用

本仓库 smoke 入口需要先拒绝未知/重复场景及非正整数超时，再建立输出目录、访问 Docker 和认证。重复项检查与具体合法集合是本轮用户需求，不是 argparse 自动保证。保留默认场景、repo-copy 与内部 handoff 行为。使用已有标准库，无新增依赖。

验证独立检查退出码、错误内容和副作用边界，不以是否采用特定函数名判定实现。官方在线页面可能对应更新的 Python 小版本；所借鉴基础 API 不依赖 3.14 新增的错误建议或颜色选项。

返回 [参考索引](README.md)。
