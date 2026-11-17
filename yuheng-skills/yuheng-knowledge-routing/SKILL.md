---
name: yuheng-knowledge-routing
description: Use when Yuheng 任务需要定位知识轨道、确认框架符号，或技能发现、版本及知识与源码出现差异。
metadata:
  version: "0.2.0"
  entry: specialist
---

# Yuheng 知识路由

先读 [SDD 契约](../yuheng-workflow-router/references/sdd-contract.md)。本技能提供定位依据，不授予运行时代码修改权限。
沿用任务 `workId`、REQ/AC/T，在上游规格、计划和证据中记录 `codeVersion`、`governanceVersion`、`knowledgeVersion`。

## 入口与发现

1. 确认仓库根、已有修改和 core/消费端边界；core 读 `release/yuheng-manifest.yaml`，消费端读 `yuheng-manifest.yaml`。
2. core 规则来自 `governance/rules/`，消费端规则来自 `yuheng-rules/`；按任务读取，不混用其他框架契约。
3. 标准入口按工具选择 `.agents/skills/<name>/SKILL.md`、`.claude/skills/<name>/SKILL.md` 或 `.qoder/skills/<name>/SKILL.md`；先确认文件或链接真实可读。
4. 未安装时，core 直接读 `governance/skills/<name>/SKILL.md`，消费端直接读 `yuheng-skills/<name>/SKILL.md`。
5. 旧平铺说明不能证明技能已发现；缺入口就记录实际路径与缺口，不虚构技能调用成功，也不擅自执行安装。
6. 规格或计划缺失时回到 [流程路由](../yuheng-workflow-router/SKILL.md)；“创建页面”不能直接成为编码授权。

## 按任务读取

| 涉及内容 | 知识入口与核对对象 |
|---|---|
| 页面、Store、请求、路由 | `ai-knowledge-core/ui/`；包导出、类型、runtime 和实际页面 |
| 接口、服务、权限、租户 | `ai-knowledge-core/server/`；Controller、Service、Mapper 与测试 |
| 数据结构或迁移 | `ai-knowledge-core/data/` 及后端关系说明；既有脚本、配置和表定义 |
| 版本或兼容差异 | manifest、`ai-knowledge-core/metadata.json`、`ai-knowledge-core/release-matrix/` 与实际依赖 |

只读取当前任务涉及的索引和源码；必要文件不存在时注明缺失，不把逻辑路径当作相对技能路径。
当前前端包为 `yuheng-ui`，导出 `createYuhengRequest`、`installYuhengUi`、`useUserStore`、`usePermissionStore`、`useDictStore`。
它不导出静态 `request` 或 `useMenuStore`；已有实例复用 `runtime.context.request`，方法签名和解包行为须读实际源码。
HTTP 方法以 Controller 和客户端契约为准，含 GET/POST/PUT/DELETE；Service 接口与 Impl 也不能推定一律继承 `ServiceImpl`。
业务定制留在消费端；core 仅承载已确认的框架共性能力，不能因复用困难把业务逻辑移入 core。

## 输出与门禁

输出本任务选中的知识轨道、文件/符号位置、可复用能力及对应 REQ/AC/T，不复制一整套无关教程。
知识或规则与源码冲突时，记录双方位置、版本、已核实行为和兼容影响；仅在授权文件范围内修正文档。
必需契约、版本或来源无法核实时为 `BLOCKED`，非必需缺口才可 `WARN`；既有授权持续有效，不重复索要形式审批。
结论写入同一 `workId` 的现有产物；不默认提交、推送、发布或操作真实环境。
