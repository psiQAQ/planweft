# 0.5.1 离线测试套件

状态：Passed。日期：2026-09-13。

- `python3 -m unittest discover -s tests -p 'test_*.py'`：350 项通过，1 项按既有条件跳过。
- `npm run check`：生成验证的 15 个目标零差异；Node 安装器测试 123 项通过、1 项跳过；DSH hook shell 测试 3 项通过。
- `git diff --check`：通过。

测试使用仓库内测试与离线夹具。参数拒绝夹具产生的 argparse 错误输出是预期断言，不是测试失败。
