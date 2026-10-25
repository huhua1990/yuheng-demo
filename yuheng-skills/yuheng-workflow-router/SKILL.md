---
id: yuheng-workflow-router
version: 0.1.0
entry: public
---

# yuheng-workflow-router

根据用户输入选择一个公开工作入口，不要求用户记忆 specialist skill。

路由顺序：

1. 新工程或刷新快照：先执行初始化体检；
2. 原始需求或口头想法：进入 `yuheng-requirement-to-spec`；
3. 已确认规格：进入 `yuheng-spec-to-plan`；
4. 已有计划：进入 `yuheng-delivery-execution`；
5. 报错或异常：先收集日志和复现证据，再进入交付执行；
6. 需要完整串联时：进入 `yuheng-full-workflow`。

路由结果必须返回当前阶段、缺失证据和下一步入口。

参考：[阶段门禁](../../../governance/rules/yuheng-phase-gate.md)。
