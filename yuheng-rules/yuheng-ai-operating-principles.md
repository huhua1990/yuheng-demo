---
id: yuheng-ai-operating-principles
version: 0.1.0
scope: core
---

# Yuheng AI 编码工作原则

Yuheng 把 AI 当作受约束的交付协作者。任何可交付变更都必须能追溯到需求、规格、计划和验证证据。

- 先确认边界、现状和兼容契约，再提出实现方案。
- 规则、技能和知识必须有来源提交、版本和适用范围。
- 运行时代码、治理资产、消费端 overlay 和验证证据分别维护。
- 先复用现有 API、表结构、权限、租户和前端契约，再申请破坏性变化。
- 失败必须保留确定性错误、证据路径和修复建议，不能吞掉异常。
- 治理检查只约束交付过程，不调用模型，也不读取业务源码来推断版本。

工作产物至少关联同一个 `workId`，并记录 `codeVersion`、`governanceVersion` 和 `knowledgeVersion`。
