# 0.5.0 Hook 逻辑

日期：2026-09-13。`tests/test_document_handoff.py` 的离线夹具覆盖唯一 marker、
有效状态、gated 条件、cap/stall 短路和各宿主 Stop 能力差异；4 项通过。
`tests/test_document_release_gate.py` 同时验证 policy/evidence/archive 的摘要绑定和错误输入拒绝；3 项通过。
