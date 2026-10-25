---
id: yuheng-phase-gate
version: 0.1.0
scope: core
---

# Yuheng 阶段门禁

阶段结果只有 `PASS`、`WARN`、`BLOCKED` 和 `WAIVED`。

- `PASS`：必需证据齐全，版本和引用均可解析。
- `WARN`：存在已记录且不影响当前阶段的缺口。
- `BLOCKED`：版本不兼容、规则冲突、路径缺失或必需证据缺失。
- `WAIVED`：有负责人、到期时间、风险和后续任务的临时豁免。

阶段 1 的工作必须完成 `spec → plan → delivery → verification`。进入发布门后，`BLOCKED` 不得继续发布；`WAIVED` 到期后自动按 `BLOCKED` 处理。
