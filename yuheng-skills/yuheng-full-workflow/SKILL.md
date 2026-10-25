---
id: yuheng-full-workflow
version: 0.1.0
entry: public
---

# yuheng-full-workflow

完整工作流按以下顺序运行：

```text
requirement-to-spec
→ prototype（可选）
→ spec-to-plan
→ delivery-execution
→ verification / release-check
```

任何阶段门禁为 `BLOCKED` 时停止向下执行，保留当前快照和报告。阶段完成后才允许进入下一阶段。

参考：[Yuheng AI 治理设计](../../../docs/superpowers/specs/2026-10-25-yuheng-ai-governance-design.md)。
