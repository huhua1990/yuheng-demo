---
name: yuheng-task-decomposition
description: Use when a Yuheng requirement crosses frontend, backend, data, permissions or public framework boundaries before implementation.
metadata:
  version: 0.2.0
  entry: specialist
---

# Yuheng 任务拆解

先用 [知识路由](../yuheng-knowledge-routing/SKILL.md) 查复用，再按 [SDD 契约](../yuheng-workflow-router/references/sdd-contract.md) 拆交付单元。

1. 明确 core 共性能力、消费端业务和治理文档各自归属，标注 Only Modify / Do Not Modify。
2. 查现有 Controller 路由、Service/Mapper、API 家族、请求上下文、Store、菜单权限和表关系，记录可复用的文件与符号。
3. 以验收结果拆任务，分离数据迁移、契约、后端行为、前端接线与联调；明确依赖，不按目录机械创建无用层。
4. 框架公共能力变更列出消费端影响、兼容策略和回归入口；不把业务模块塞入 core。
5. 对每个任务给出关联 REQ/AC、影响文件、验证方式、失败时恢复方法和环境依赖。

输出复用决策、任务依赖与验收映射，供 [编写计划](../yuheng-writing-plans/SKILL.md) 使用。该技能不绕过规格/计划门禁。
