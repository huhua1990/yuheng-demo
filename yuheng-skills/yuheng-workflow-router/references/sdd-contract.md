# SDD 工作产物契约

所有 Yuheng SDD 技能共同遵守本文件；技术规则从当前工程的 `governance/rules/`（core）或 `yuheng-rules/`（消费端）读取。core 标准技能通过 `.agents/skills/`、`.claude/skills/`、`.qoder/skills/` 发现，均链接至 `governance/skills/<name>/`；消费端未安装时直接读取 `yuheng-skills/<name>/SKILL.md`。不要把这些逻辑路径误当成相对于当前技能的文件路径。

## 定位工程与版本

先确认工作目录、所属 Git 仓库、已有未提交修改与任务边界。core 的版本入口为 `release/yuheng-manifest.yaml`，消费端为 `yuheng-manifest.yaml`；缺失或与实际依赖不一致必须记录，不能猜测版本。

读取与任务有关的规则和 knowledge；knowledge 与真实源码/类型定义冲突时，以已验证契约和兼容要求定位差异，记录证据，再修正文档或提出变更。不能照搬 Athena 的包名、组件、API 或数据模型。

## 产物路径与追踪

使用稳定 `workId`，例如 `YH-20261110-dict-category`。同一任务的需求、实现、后续修复沿用它，不另起无关联的“完成报告”。

| 产物 | 默认路径 | 必填内容 |
|---|---|---|
| 规格 | `docs/specs/<workId>.md` | 目标、范围、REQ、AC、契约、确认依据 |
| 计划 | `docs/plans/<workId>.md` | 规格引用、T、文件范围、依赖、验证命令 |
| 证据 | `docs/verification/<workId>/verification.md` | AC/T、实际命令、时间、退出码、日志、未验证项 |

用户指定已有路径时沿用，不为了符合目录惯例复制第二份规格。每份文档记录 `workId`、`codeVersion`、`governanceVersion`、`knowledgeVersion`，并引用上游文档。REQ 和 AC 使用稳定编号；每个 AC 至少对应一个任务和验证记录；每个任务说明关联的 REQ/AC。不适用的页面、迁移等项目写明 `N/A` 和理由。

模板包含 `{{...}}` 供生成时替换；生成后的工作产物必须填入真实内容，未决问题单独列出，不把占位符或预期输出冒充已验证证据。

## 阶段和授权

文档状态：`UNKNOWN → DRAFT → READY_FOR_REVIEW → FROZEN`。找不到输入文件、文件状态或授权来源时用 `UNKNOWN`，不能猜测。原型状态为 `UNKNOWN / PENDING_ASSESSMENT / NOT_REQUIRED / DRAFT / READY_FOR_REVIEW / OWNER_APPROVED`；按页面复杂度判断后记录依据。规格/计划冻结必须记录确认来源与范围，例如用户消息、需求单的明确验收或已批准的文件版本；生成文件本身不是确认。

既有授权持续有效。用户已经批准方案或明确授权完整实施时，范围内的技术细节、计划拆解和文档补录由 AI 完成，记录依据后继续，不重复索要形式审批。用户只要求需求分析、设计或计划时，交付到该阶段为止。业务含义不明确、改变已确认行为、扩大范围或高风险动作仍须明确决策；等待时先完成不受影响的分析和文档。

每阶段门禁为 `PASS / WARN / BLOCKED / WAIVED`：

- `PASS`：该阶段必需证据齐全且实际核实。
- `WARN`：缺口不影响本阶段，记录风险和后续动作；不能用于隐藏验收失败。
- `BLOCKED`：必需输入、业务决策、兼容评估或验证证据缺失，禁止进入依赖它的阶段。
- `WAIVED`：明确授权的临时豁免，记录负责人、范围、风险、到期日和后续任务。未验证事实仍写未验证；豁免不等于测试通过。
- `UNKNOWN`：必要输入、文件或授权来源未提供/不可读，尚无依据判定冻结状态；缺失项会阻塞依赖阶段。
- `PENDING_ASSESSMENT`：阶段资料存在，但原型必要性尚未判断；判断前不进入依赖该决定的计划/实现。

## 实现前状态

```yaml
PHASE_GATE:
  workId: YH-20261110-dict-category
  taskType: frontend / backend / mixed / governance
  stage: spec / plan / delivery / verification
  spec: {status: UNKNOWN, path: "", approval: ""}
  prototype: {status: PENDING_ASSESSMENT, source: "", reason: ""}
  plan: {status: UNKNOWN, path: "", approval: ""}
  onlyModify: []
  doNotModify: []
  consumerImpact: ""
  implementationAllowed: false
  result: BLOCKED
  evidence: []
```

规格和计划均冻结且证据存在，相关原型和兼容评估具备后，才能设 `implementationAllowed: true`。仅做需求分析时 AC 可处于待追踪状态；计划阶段补齐 AC→T，交付/验证阶段补齐 AC→测试/证据，不要求需求分析预写未生成的计划。纯文档/格式调整或不改变既有契约的局部修复可在同一规格中记录精简设计与任务清单，仍须明确验收；不能因此跳过测试或隐瞒权限、租户影响。

原型只对新页面、主要布局或核心交互缺少已确认设计时按需创建；既有被认可设计可作为证据。局部字段/样式、API 接线或权限接线可为 `NOT_REQUIRED`，记录参考来源和理由。原型、计划阶段不能擅自修改运行时代码。

## 实现、漂移和交付

后端行为变更先运行行为测试看到断言红灯，再最小实现并重跑转绿；依赖缺失、启动失败、编译失败不算行为红灯。前端逻辑变更测试与浏览器验收结合；纯样式等用可重复的视觉检查。

专项技能相互引用用于补齐本任务尚未完成的检查；已执行并有证据的步骤直接引用结果，不递归反复进入其他专项流程。

发现规格与实现冲突时先判断：技术细节在范围内可调整计划并记录；业务行为或契约变化更新受影响的 REQ/AC，取得对应差异的决策后再实现。不要事后改验收标准以迁就失败。

交付前实际检查 diff，逐项核对 AC → T → 测试/日志，执行适用的 API、UI、迁移和兼容验证。环境不可用时记录未验证项、错误和补验命令；必需验收缺证据则最终为 `BLOCKED`。可以报告“实现已提交待验收”的事实，不能报告全部完成。提交、推送、发布、操作真实环境按本次用户授权执行，技能不默认授权这些动作。
