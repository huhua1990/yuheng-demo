# 全量迁移验证优先级与提交准备

**workId:** YH-20261111-full-source-migration  
**关联计划:** `docs/plans/2026-11-11-full-source-migration.md`  
**基线:** Demo `b9c4906` 加现有未提交改动；Core `576e830` 加未提交菜单修正；业务模板 `73d19be`。  
**版本:** code `0.1.0-SNAPSHOT`、governance `0.2.0`、knowledge `0.1.0`。  
**状态口径:** 已完成是限定场景已有证据；进行中是已有实现或部分证据但未达到验收；待验证包含已有计划但尚无充分证据。历史证据需标明版本与环境，不能替代当前提交的复验。

## 2026-11-24 当前执行增量

本节覆盖下文较早快照的进度描述，保留原始拆批范围和历史记录。继续按用户明确的 BPM → OA → HRM 严格类型 → IM → AI/IoT/MES/FMS 顺序推进。

- BPM 基础消费闭环通过，证据在 Templates `docs/verification/2026-11-24-bpm-p2-consumer/`；复杂建模、表单和打印编辑器仍为 P3，迁移来源授权及约束审查不据此关闭。
- OA 已补齐 117 changeset 消费者的公告 UI/API/SQL 代表闭环；独立 159 changeset / 48 表冷装重启证据保留。后续消费者副本在本地 Core 归档 `98233183…` 下通过完整 strict 类型（0 诊断）、20 项 UI 测试和 4095 模块构建，无宽泛 shim 或页面排除；该包未发布 registry。不能将历史冷装独立外推为同制品全业务验收。
- HRM 主体不重复扩测；严格类型已在本地 Core 归档 `18d3cbb2…` 的隔离消费者通过，0 诊断。未发布或替换 registry 包，证据在 Templates `docs/verification/2026-11-24-hrm-p2-strict-consumer/`。
- IM 主体限定消费闭环通过：Skill 新建消费者、450 文件映射一致、严格类型 0 诊断、20 项 UI 测试、Vite 构建、40 项后端测试/打包、77 changeset 冷装/重启（IM 18）、17 张初始空表/249 列、好友/私聊/群组 API/SQL 及敏感词桌面 CRUD/刷新。Core/IM 上传进度回调类型经红绿验证修复；本地 Core 归档 `98233183…` 未发布。证据在 Templates `docs/verification/2026-11-24-im-p2-consumer/`。真实消息通道和推送仍为 P3。
- AI、IoT、MES 的主体消费批次继续开放；FMS 账套初始化仍缺权威完整科目树，不以临时数据代替。模板迁移的 `generated-pending-verification` 标记不等于上述限定消费工作未执行，也不因限定消费通过自动升级为已交付。

## 2026-11-25 剩余 P2 消费批次更新

本节更新上一节 AI/IoT/MES 继续开放的历史描述，保留原始拆批范围。

- AI、IoT、MES 的基础消费闭环已有本批次验收记录，分别位于 Templates `docs/verification/2026-11-25-{ai,iot,mes}-p2-consumer/verification.md`。AI 的原始日志已补齐同 schema 的 90/0 冷装重启证据；MES 最终 strict 归档边界及同 JAR 证据单独记录。不重复扩测已通过的 BPM、OA、HRM 门禁与 IM。
- FMS 新干净消费者已通过 376 文件映射核对、实际本地 Core 归档的消费构建、40 项已有后端测试、最终 JAR 的空库冷装及同 schema 重启（95 总 changeset / 36 FMS，30 表 / 494 列）。基础账套 API/SQL 与桌面列表、编辑已有证据；完整初始化仍因缺少 `560107` 失败，整组 FMS 行数据回滚已核验。
- FMS 官方 `fms.sql.zip` 分发入口已定位到知识星球主题 `55522821552524824`，当前会话需登录；附件内容、版本匹配和模板使用授权尚未取得。财政部官方 66 个编号科目仍不能替代本产品完整明细树。未取得并验证完整权威数据之前，FMS 与整体剩余 P2 目标保持未完成。
- 本地 Core archive 均未发布 registry；矩阵 `generated-pending-verification` 不因基础消费通过而升级。统一目标见 Templates `docs/plans/2026-11-25-remaining-p2-goal.md`，FMS 来源及运行证据见 `docs/verification/2026-11-25-fms-subject-source-audit.md` 与 `docs/verification/2026-11-25-fms-p2-consumer/verification.md`。

## 2026-11-26 P2 消费验收阶段收尾

本节为当前阶段收尾结论，下文早期拆批表与历史快照仅保留作为历史记录；统一口径以本节和 Templates `docs/plans/2026-11-25-remaining-p2-goal.md` 为准。

- **已通过的限定范围消费项（不重复扩测）：**
  - **BPM**：干净消费者基础消费闭环通过（`yuheng-business-templates/docs/verification/2026-11-24-bpm-p2-consumer/`）；复杂建模/表单/打印编辑器留 P3。
  - **OA**：117 changeset 消费者构建、冷装/重启与公告 API/SQL/桌面代表闭环通过（独立 159 changeset / 48 表冷装重启基线分开记录），后续消费者副本在本地 Core UI 归档 `98233183…` 下通过完整 strict 类型（0 诊断）、20 项 UI 测试与 4,095 模块构建（`2026-11-24-oa-p2-consumer/`）。
  - **HRM**：主体运行不重复扩测，严格 UI 类型门禁已在本地 Core UI 归档 `18d3cbb2…` 下通过（`2026-11-24-hrm-p2-strict-consumer/`）。
  - **IM**：在本地 Core UI 归档 `98233183…` 下完成 450 文件映射、严格类型 0 诊断、20 项 UI 测试、Vite 构建、40 项后端测试与打包、77 changeset 冷装/重启（IM 18）、好友/私聊/群组 API/SQL 及敏感词桌面 CRUD/刷新（`2026-11-24-im-p2-consumer/`）。
  - **AI、IoT、MES**：均已在 Skill 初始化的干净隔离消费者中完成各自限定范围消费闭环（`2026-11-25-{ai,iot,mes}-p2-consumer/verification.md`），其中 MES 在本地 Core UI 归档 `e3d54b2b…` 下通过完整 strict 类型门禁、4,399 模块构建、40 项后端测试及同最终 JAR `0f075268…` 的 379 changeset（MES 320）冷装/重启、权限拒绝、API/SQL 与桌面 CRUD。
- **制品与迁移边界：** 上述结果均按各自版本、制品和场景边界成立，不把不同消费者、不同 JAR 或不同 Core 归档的证据拼凑为同制品全量验收；所用本地 Core UI 归档均**未发布 registry**；消费验收通过不代表生产数据库迁移审查完成，迁移矩阵继续保持 `generated-pending-verification`。
- **FMS 最新事实与冻结阻塞：** 用户已明确**无法提供 `fms.sql.zip`**。因此不再要求用户提供该文件，也不再把获取该 ZIP、登录知识星球或重复访问同一下载入口作为下一步任务；不扩写未经证实的科目树，也不通过删改结账预设或跳过初始化步骤制造验收通过。FMS 当前准确状态为：**基础消费验证部分通过；完整账套初始化因缺少权威、版本匹配且允许使用的科目数据而阻塞**（376 文件映射、本地 Core 归档消费构建与 40 项已有后端测试、最终 JAR `c3e0ef9a…` 95/36 changeset 冷装与重启、基础账套 API/SQL 与桌面列表/编辑已验证；初始化因缺少 `560107` 返回 `1052105025` 并回滚，30 张 FMS 表数据保持不变）。该阻塞已冻结，仅当出现新的权威完整科目数据或用户明确批准调整 FMS 验收范围时才重新评估。
- **P2 收尾与 P3 范围：** 不依赖 FMS 科目数据的原定 P2 必要消费工作已全部收尾；复杂 BPM 建模/表单/打印、真实消息通道与推送、外部模型、IoT 硬件/时序库及复杂制造流程仍留 P3。整体目标因 FMS 完整账套初始化阻塞而仍未全部完成。

## P2/P3 范围拆分（2026-11-23）

**2026-11-24 P2/P3 收敛决定：** P2 验收主体交付：模板可被 Skill 选择性初始化到干净消费者；Core 版本和直接依赖明确；前后端基础页面、主体 API/逻辑可构建；DO/Mapper/继承字段与 SQL 表/索引覆盖一致；Liquibase 可冷装、重跑且保护已有表；初始化数据边界清晰；至少一条桌面代表流程在 API/SQL 上闭合。任一主体门槛未通过，模板仍留在 P2 待验收。

**P3 范围：** 真实微信/支付/短信/社交外部渠道，真实硬件与时序库，完整复杂流程/表单设计器、扩展打印编辑器，全站逐页视觉比对，完整权限/租户组合穷举，极端并发与故障注入，低频参数组合。基础菜单/页面入口、核心业务逻辑、常规权限校验、模块表结构、Liquibase 和消费构建不得降为 P3。仅页面本身属于手机移动端程序时做手机视口检查；桌面管理后台不做手机视口验收。

项目边界固定为：Core 持有平台能力源码；Business Templates 持有可选业务模块源码；Demo 是使用者最终运行和定制的工程，只依赖 Core，模板需由使用者显式初始化；Skill 负责初始化以及经预览、冲突分类后的选择性模板修复更新。更新模板不能重建、清空或覆盖 Demo 定制。P2/P3 验证始终在隔离消费者中执行，不把验证模板长期预置到正式 Demo。

P2 保留主体交付门槛：模块在 Demo 风格消费者中能被选择性初始化；后端源码/资源和前端页面/API 映射完整，构建可用；业务表字段覆盖当前 DO 及继承字段、必要索引有源码或 SQL 依据；Liquibase 冷装、重跑和已有表冲突保护成立；模块初始化数据边界清晰；至少一条桌面页面/API/SQL 主流程端到端一致。没有完整后端或核心 UI/构建不可用时，不能以“P3 长尾”掩盖 P2 主体缺口。CRM/BPM 本轮发现的严格类型及映射缺口仍属 P2，只有 BPM 重型建模/打印编辑器的可选资产可单独拆到 P3。

P3 接收主体验收通过后的扩展项：真实微信/支付宝/短信/社交渠道、真实硬件与时序数据库、重型流程建模和打印编辑器、全站逐页视觉对照、所有权限注解的穷举矩阵、极端并发/故障注入及低频参数组合。外部环境不可用或实现复杂时可以记录为 P3，但不把其对应的基础表、基础 API、页面入口或消费构建缺失一并降级。

### 模板验证优先级

状态按 `yuheng-business-templates/docs/migration-matrix.json` 当前快照和本计划中的消费证据填写；“SQL 部分证据”只表示冷装/重跑或特定结构断言，不等于生产 DDL 完整，也不改变矩阵中的模板交付状态。

| 优先级 | 模板 | 当前进度 | P2 主体验收重点 | P3 扩展 |
| --- | --- | --- | --- | --- |
| P2-A | Member、ERP | 主体代表闭环已验证；模板创建/更新路径已有隔离证据 | 保持当前 JAR 复验基线；新模板修复按 Skill 选择性带入 | 外部渠道、全量数据权限与长尾并发 |
| P2-A | Pay、PMS | Skill 消费及代表 API/SQL 已验证；桌面代表页面部分通过 | 清洁消费者严格类型、构建、模块迁移及代表桌面页面/SQL 同制品复验 | 真实支付渠道、PMS 全量页面与复杂分享权限 |
| P2-B | CRM、BPM | CRM 当前隔离 JAR 的 API/SQL 生命周期与 1440×900 桌面客户列表闭环已通过；CRM/BPM 当前 Core registry 包的生产消费构建仍失败，详见验证记录 | BPM 基础页面/API/SQL 与 Liquibase、基础 UI 清洁消费构建；CRM 其它核心业务页面按模板验收计划继续覆盖；按 Skill 选择性更新 | BPM 完整流程建模、表单建模、打印富文本编辑器和真实外部流程集成 |
| P2-C1 | AI、IoT、MES | SQL 冷装/重跑、DO 列覆盖契约有部分证据；Skill 消费构建和本地基础业务闭环待验证（3 个） | 清洁消费者构建、基础页面/API、初始化边界、MySQL 表/索引及桌面代表流程；保留时序以外关系型主体 | AI 真实模型渠道；IoT TDengine/IoTDB、硬件及设备链路；MES 跨域复杂制造流程 |
| P2-C2 | FMS、IM、OA | FMS 构建、36 个 Liquibase changeset 冷装/重启、桌面账套 CRUD 部分通过，但标准科目缺失阻断初始化；IM、OA 未完成消费者主体流程；WMS 已通过 P2。HRM 主体闭环通过，严格类型门禁单独跟踪 | 基础消费构建、表结构/索引核对、初始化边界和桌面代表 API/SQL 流程；FMS 完整科目数据必须有权威来源后再验收 | 外部消息、完整审批及低频业务组合；FMS 无权威来源的标准科目数据不视作通过，也不靠虚构夹具降级 |
| P2-C | MP、Report | 矩阵标记已交付且 SQL 冷装证据存在；当前 Core 消费版本仍需确认 | 清洁 Skill 消费构建、入口/依赖接线、代表桌面页面/API/SQL | 真实公众号回调、复杂报表与外部数据源 |

**模板状态以证据而非矩阵总数作为验收口径：** 当前 16 个模板中，矩阵仍将 12 个标作“生成待验收”。其中 CRM、ERP、PMS、WMS 已分别有代表性消费闭环证据，矩阵状态仍需在各自范围完整后复核；因此“矩阵待验收 12 个”不等于“12 个都没有验证”。CRM 客户代表页面/API/SQL 已通过，但 CRM 其它核心页面仍开放；BPM 基础 UI 清洁消费构建/API/SQL 仍开放，重型流程/表单/打印编辑器属于 P3。HRM 主体 API/SQL、桌面流程、迁移、后端与 Vite 构建已有通过证据，但严格类型消费未闭合，仍在 P2。P2-C 有 **6 个模板主体未闭合**：AI、IoT、MES、FMS、IM、OA；HRM 主体流程已通过但严格类型门禁仍开放，WMS 已通过。FMS 当前有前后端构建、36 个 changeset 冷装/重启和账套桌面 CRUD 的部分证据，但初始化因没有权威标准科目数据而失败，必须继续留在 P2。外部模型、真实硬件/时序服务、跨域复杂流程等可放 P3，但不得连带豁免关系型主体、基础页面/API、消费构建、表结构或 Liquibase。

### P2 剩余项拆批（2026-11-24）

P2 不再作为一个长周期大验收包推进，按模板分批关闭；每个模块只有在 Skill 选择性创建的干净消费者中通过前后端消费构建、主体页面/API/SQL、表结构与 Liquibase 后才移出待验收。HRM 的运行/API/SQL 子项已通过，但严格类型门禁未闭合；当前 6 个主体未闭合 P2-C 模板拆为：

| 批次 | 模板 | P2 主体范围 | 可单列 P3 的范围 | 当前门槛 |
| --- | --- | --- | --- | --- |
| P2-C2a | HRM | 已完成员工、招聘代表桌面流程，主体 API/SQL、51 个 changeset 冷装/重启和隔离消费者后端/Vite 构建；严格前端消费检查仍须在修复 Core 包类型边界后闭合 | 真实通知渠道、复杂审批扩展、全量薪资/绩效组合 | 当前 Core 包 HRM 运行通过；整仓 `vue-tsc` 被 BPM 页面及 Core compat 源码诊断阻断，模板路径筛选结果不能替代清洁包消费者类型验收 |
| P2-C2b | IM、OA | 各自基础页面、关系型 API/SQL、桌面代表流程、迁移与消费构建 | 外部消息通道、完整复杂审批及真实推送 | IM 后端 680 源码编译通过；模板已修复未读标题对 `appStore.getTitle` 的类型依赖，5 项模板契约通过，IM 清洁初始化消费者的 Vite 构建通过；严格类型仍被 Core compat 与既有 Member 诊断阻断，尚未做 SQL/API/桌面闭环。OA 当前 Core package 下 OA 路径严格类型诊断为 0，48/48 实体与 SQL 表字段匹配，后端 1335 源码离线编译通过；Liquibase 159 changeset 冷装/重启、48 张表及既有表哨兵冲突保护通过。Vite 被 BPM 基础消费缺口阻断，OA API/SQL 桌面闭环待验证 |
| P2-C1a | AI、IoT | AI 基础关系型资源；IoT 产品/设备模型等 MySQL 主体、桌面页面/API/SQL 和消费构建 | 真实模型渠道、硬件、TDengine/IoTDB 时序链路 | SQL/DO 契约有部分证据，消费者主体仍待验证 |
| P2-C1b | MES | 基础关系型生产资源、桌面页面/API/SQL、消费构建和迁移完整性 | 跨域复杂制造闭环、真实设备联动 | SQL/DO 契约有部分证据，消费者主体仍待验证 |
| P2-C2c | FMS | 账套及初始化主体、桌面页面/API/SQL、迁移与消费构建 | 仅在找到权威完整科目树来源后处理其来源接入；缺失科目不得由临时夹具掩盖 | 账套 CRUD 和 36 changeset 部分通过；初始化因权威科目树缺失而回滚，仍为 P2 阻塞 |

BPM 是与 HRM/CRM 交叉的独立 P2 基础消费项，不计入上述 6 个 P2-C 模板数：当前后端编译和 Vite 生产构建有历史/隔离通过证据，但当前固定 Core 包下严格类型消费及完整基础 UI 消费未通过；流程/表单设计器、富文本打印编辑器可拆为 P3，基础流程运行、任务处理、API、SQL 和 Liquibase 仍须在 P2 有明确可消费边界。HRM 中考勤请假审批只有同时选择 BPM 才启用；不选择 BPM 不影响 HRM 员工/组织等不依赖审批的主体功能。

## 顺序和整体目标

1. **P0 提交准备，先于高优先级验证。** 清点 Demo 变更，区分运行代码、治理快照、计划与可公开证据；检查敏感内容、生成文件、暂存/工作区差异以及 Core 未提交依赖。以可复现构建和不泄露凭据为提交门禁，按逻辑单元提交；不覆盖既有工作或顺手清理用户文件。记录无法随代码提交的证据及其替代位置。当前有 1197 个未跟踪文件，且两项暂存重命名的目标在工作区又被删除；现有暂存区不能直接代表最终代码。Core 菜单修改尚未提交，须明确版本依赖并验证后处理。**状态：代码与文本提交已完成；127 张历史截图保留本地待逐张审查。**
2. **P1 整体目标：可交付的平台最小闭环。** 同一可识别 Core 版本及 Demo 提交，在隔离环境完成前后端构建、启动、登录、动态菜单、系统管理和基础设施代表流程、权限/租户边界与数据库初始化/重启；保留历史密码。端到端证据、失败记录、资源清理及可重复命令齐备，才可标记 P1 完成。P1 是优先里程碑，不替代 T1/T3/T4 的全量验收。
3. **P2 业务主流程。** **状态：进行中；**Member、ERP 的代表性业务闭环及模板选择性更新已有证据。Pay/PMS 已在 Skill 创建的隔离消费工程完成前后端构建及 API/SQL、权限、租户、数据库重启复验；Core 当前包下 Pay/PMS/Member 业务目录严格类型检查与生产构建通过，Core 整棵旧 compat 源码树仍有独立历史诊断。CRM 客户代表页面/API/SQL 闭环通过，其它核心页面继续覆盖。HRM 主体真实运行/API/SQL 已通过，但严格类型消费门禁仍未闭合；BPM 基础消费和 BPM/Core compat 整仓类型边界仍待通过。重型建模/表单/打印编辑器归 P3，但基础页面、公开依赖、表结构及主体 API/SQL 留在 P2。矩阵仍有 12 个生成待验收标记，但 CRM、ERP、PMS、WMS 已有代表性消费证据；它们不应被重复计为未启动。P2-C 主体未闭合模板为 6 个（AI、IoT、MES、FMS、IM、OA）；HRM 主体已过但严格类型门禁仍开放。FMS 因无权威标准科目数据而阻塞初始化；AI 外部模型、IoT 硬件/时序数据库和 MES 跨域复杂流程拆到 P3，关系型主体与基础消费仍保留在 P2。桌面管理后台不纳入手机视口验收。**
4. **P3 全量扩展与低频故障。** 补齐真实外部服务/硬件、完整流程/表单/打印编辑器、全量权限租户事务矩阵、OAuth/社交/Quartz/文件存储集成、极端并发和故障注入。只有页面本身属于手机移动端程序时才进行手机视口验收；本项目桌面管理后台不在此范围。其他业务模板按业务优先级逐模块核对扩展 SQL 与外部集成。**状态：待验证及部分进行中。**

### P2 Pay/PMS Skill 消费复验（2026-11-23）

- **当前 Core 包复验：部分通过，P2 继续进行中。** Core `bb90a58` 修复 compat 标签 store 的类型和不必要的路由生成器依赖、Descriptions 属性过滤类型，并为 platform/setup 发布类型声明；迁移 Skill 增加真实包类型及直接依赖要求。Core UI 139 项测试、边界检查和发布构建通过；治理 58 项中 56 项通过、2 项需专用数据库而跳过。实际打包 UI SHA-256 `4fc06e4b744278e304a57e49edd7695823109e4cf4be032bf963be593d69ed88`，隔离消费者的严格类型检查和 3880 模块构建通过，仍保留 platform/setup 接入 shim，不能外推到全部 compat 源码。以该包构建的隔离 JAR SHA-256 `85240edb6794c5e30fb34dbf79ac35e6f1e5e892fe909186911fec5692fe5e17` 完成 Pay/PMS API/SQL、权限与双租户检查，107 changeset 首次和重启一致；1440×900 浏览器完成 Pay 应用、PMS 项目创建及匿名分享直接打开和刷新，错误与失败请求均为 0。随后 Templates 提交 `c94ed6e` 将 14 个 Pay/PMS 模板页面中的 16 条旧平台 alias 改用 Core 公开 compat 导出，全量测试 101 项通过；隔离消费者按模板更新流程只合并这 14 个文件，再次通过严格类型检查、平台导入边界和 3880 模块构建。使用更新后源码构建的隔离 JAR SHA-256 `cb643f6b36d3c86d8c878e2a240e6596add6c27aae9dc7e8d42c3b2d3de6d001`，同一 API/SQL、权限、双租户及桌面匿名分享探针通过。最终证据 `p2-pay-pms-template-core-current-20261123/runtime.json`、`browser.json`；容器和 13401/16481/48261/5221 端口已清理。运行时使用本地 tarball，不代表 Core 更新已发布 npm。
- **尚需处理：** 隔离消费者目前仍有宽泛 compat 类型 shim，未标注业务响应默认 `any`，且 platform/setup 需要接入声明；局部 compat 类型检查通过不能证明整个旧版 compat 树严格类型化。固定版本 manifest 下 21 项消费者测试通过时 pnpm 自动重新安装了 registry 包，该测试不属于上述本地 tarball 的测试证据。默认静态服务器队列运行曾发生大量静态资源连接重置；使用仓库已有 runner 的 128 队列后完整复验通过。较早失败 JSON 保存在 `p2-pay-pms-current-core-20261123/`，该次运行覆盖了该未跟踪目录先前的旧结果，旧结果不可由该路径恢复。临时后端日志含令牌，已删除，不作为证据。

- **Core 请求配置类型及同制品复验：限定范围通过，P2 仍进行中。** Core compat 请求配置现在复用公开请求契约，要求字符串 URL 并校验 Axios 选项；下载默认返回 `Blob`，原有未标注响应仍为 `any` 以兼容现有业务。将默认响应改为 `unknown` 曾导致 ERP/Member/Pay/PMS 大量现有调用无法编译，故不能认定业务响应已严格类型化。Core UI 全量 136 项通过，隔离消费者使用本地 UI tarball SHA-256 `9b9baa19530a645d1f19cc078d3593162c6b6e668366535fc3ec7e6c292258bf`，真实请求模块类型检查和 3880 模块构建通过；其它通用 shim 仍存在。最终 JAR SHA-256 `66fdcf7563c025cdc5b5b335f92beca5026af9be7778fbf63aaec67a8bddbea1` 的隔离 Pay/PMS API/SQL、权限租户、107 changeset 冷装/重启及桌面匿名分享通过，浏览器错误和失败请求为零；证据 `p2-pay-pms-core-request-types-20261123/runtime.json`、`browser.json`。容器和端口已清理，未发布 npm 包。隔离消费者 21 项测试中 20 项通过，固定 registry 坐标断言因使用 `file:` 包失败；另 10 项定向测试通过。
- **严格类型继续排查：未完成。** 将隔离消费者的 system area/user API 与 tree 工具映射到 Core 包内真实源码后类型检查通过；进一步映射 tagsView、字典及通用工具后失败。`tagsView` 的 Pinia `defineStore` 因消费者未加载 Core 随包提供的持久化插件类型扩展而不接受 `persist: false`，连带丢失 `delView` 等 action 类型；其依赖链还存在 `qs` 类型缺失和 compat 组件类型错误。Member 售后页面字典联合类型错误已确认在当前 Templates 源码中修复，但隔离消费者保留旧文件，需要按模板更新流程预览并选择性同步。上述为隔离类型检查结果，尚未证明运行时缺陷；应在 Core/Templates 源头补齐并重新从包消费验证，不用 shim 掩盖。
- **匿名分享与同制品复验：通过限定范围。** 隔离消费者将公开路由挂到 `Home` 时，页面虽可显示，但匿名打开及刷新各触发一次受保护通知请求并产生 `Missing refresh token`；失败记录 `/tmp/yuheng-p2-pay-pms-anonymous-share-20261123/browser.json`。根因是消费路由接线，`meta.public` 不改变父布局；改为顶层注册后，同一隔离制品 SHA-256 `1447cefaa0ae113d678558ed60498d99a20f5f12189b04279be3d7394c2ca6da` 通过 Pay/PMS API/SQL、权限与租户检查，107 个 changeset 冷装/重启一致。1440×900 桌面创建 Pay 应用及 PMS 项目，独立匿名上下文打开并刷新分享页面，未调用通知接口且浏览器错误和失败请求为零。机器证据 `p2-pay-pms-share-fixed-20261123/runtime.json`、`browser.json`；专用容器和端口已清理。第一次修正后运行因脚本未解析到 Playwright 而终止，显式使用隔离消费者依赖后完整重跑。Core Skill 提交 `2a665fd` 补充顶层路由注册及匿名检查要求；正式 Demo 业务代码未被覆盖。隔离消费者将请求模块映射到真实 Core 源码后类型检查通过，但该模块参数本身为 `any`，其余通用 shim 也仍存在，严格类型契约仍待处理，P2 总项继续进行中。
- Templates `1a48e5c`、Core `8ce0d1f`；在 `/tmp/yuheng-p2-skill-consumer-20261123` 创建 Pay/PMS，并保留 ERP/Member。Pay 的两个既有钱包 API 文件冲突时未覆盖，隔离映射保留消费端适配后创建其余文件；此结果不代表完整映射零冲突。
- 在隔离消费者接入 Core BOM、业务模块的支付 SDK 依赖、模块 changelog 和路由，UI 类型检查及 21 项测试通过，Vite 构建 3880 模块、890 个资源；后端编译 907 个业务源文件、40 项测试通过。类型检查使用扩展的宽松消费者声明，尚需完善可复用的严格类型契约及 Skill 接线后复验。
- 隔离消费者 JAR SHA-256 `30777dc9241173617a71838bb3226357857ed00317f81c49d32ec32c8d2c3d7a`；真实 API/SQL 探针通过 Pay 应用和钱包、PMS 项目与知识库公开分享、无权写入拒绝、双租户隔离及伪造租户拒绝。冷装和重启均为 107 changeset，专用容器和 13401/16481/48261 已释放。机器证据 `docs/verification/2026-11-11-full-source-migration/p2-pay-pms-skill-runtime-20261123.json`；本轮未运行桌面浏览器，历史桌面证据不能替代当前 JAR 的浏览器复验。
- **当前 Core 包补验：** Core `8ce0d1f` 本地 tarball SHA-256 `7e8cde7ac4c9b1ed765c6086b3333f9819fd70baee8225577bc7d051b364b07c` 未发布；隔离安装后，Pay/PMS 新增共享路径指向真实 Core compat 源码，并直接声明 `@element-plus/icons-vue` 和 `echarts-wordcloud`，`vue-tsc`、10 项定向测试及 Vite 构建通过。Demo 既有请求等通用声明仍为 shim，不将此结果称为无 shim 的全链路严格类型验收。全量 UI 测试 20 通过、1 失败，失败为固定 registry 坐标断言不接受本地 `file:` tarball。
- 新 JAR SHA-256 `0a4706735b78854ca847fb98cc7c8e446ad713a69b2aa99079710bf6b5a5994d` 在独立环境完成 107 changeset 冷装/重启、Pay/PMS API/SQL、权限和双租户检查；1440×900 桌面浏览器创建 Pay 应用和 PMS 项目，错误及失败请求均为 0。机器证据 `p2-pay-pms-current-core-20261123/runtime.json`、`browser.json`；第一次因未安装 Playwright 在浏览器启动前失败并清理，见 `first-attempt.json`。仍需补齐可复用 Skill 接线、共享类型契约和同制品公开分享页面浏览器验证，真实支付渠道排除。

### P2 财务单据桌面闭环补验（2026-11-23）

- `PHASE_GATE`：workId `YH-20261111-full-source-migration`；stage `verification`；规格/计划 `FROZEN`，依据为用户“按计划完成 P2 验证及功能修复”及随后确认的 Core/Templates 修复归属；原型 `NOT_REQUIRED`（复用现有 ERP 财务单、销售出库选择器及已验收桌面销售夹具）；`implementationAllowed: true`。
- `REQ-P2-ERP-FINANCE-UI`：在最终业务工程 Demo 中验证财务单页面真实消费模板/API/SQL；Demo 继续是使用者的可定制工程，模板更新不重建 Demo。
- `AC-P2-ERP-FINANCE-UI-1`：1440×900 桌面浏览器登录后，从真实收款页面创建收款单并通过来源出库选择器选中本轮销售出库，保存并审批；浏览器请求/页面错误为空。
- `AC-P2-ERP-FINANCE-UI-2`：API 响应 ID、收款单/明细、来源销售出库累计已收金额、审核状态及 SQL 一致；隔离库 Liquibase 冷装 59 changesets，历史种子密码不变。
- `AC-P2-ERP-FINANCE-UI-3`：所有运行依赖使用一次性 MySQL/Redis、专用端口及临时账号；运行后清理精确资源并记录结果。ERP 管理后台不做手机视口验收。
- Only Modify：Demo 验证探针/测试/本计划与验证证据；如实测发现产品缺陷，则在 Core 或业务模板源码修复，按 Skill 选择性同步至 Demo 并复验。Do Not Modify：正式共享数据库/Redis、历史用户密码、Demo 业务定制、已执行 changeset、Core/模板运行时代码（除非验收证据证明缺陷）。
- **验收结果：限定桌面子项通过。** 当前固定 Demo JAR SHA-256 `4e1f11283c811a908d2b534c518524a843a354ac28a968223eb73e1da15bb6b1`；隔离 schema 冷装 59 changesets。1440×900 真实浏览器在 `/erp/finance/receipt` 通过销售出库选择器新增并审批收款单，在 `/erp/finance/payment` 通过采购入库选择器新增并审批付款单；四个创建/审核 API 均 HTTP 200，页面错误、Console error 和 failed request 均为 0。SQL 确认收款单 `status=20,total=3,receipt=3`，明细 `biz_type=21,biz_id=993109,receipt=3`，来源销售出库 `status=20,receipt_price=3,total_price=36`；付款单 `status=20,total=4,payment=4`，明细 `biz_type=11,biz_id=993204,payment=4`，来源采购入库 `status=20,payment_price=4,total_price=20`；历史种子用户密码字段快照相同。结果见 `erp-finance-browser-20261123/runtime.json`、`browser.json`；隔离容器及 13432/16487/48274/5233 均清理。
- 验收期间曾出现探针定位器和 SQL 夹具插入顺序错误，均在实际业务请求前失败，没有形成独立可复核的失败 JSON；修正后在同一最终 runner 的全新隔离环境完整重跑通过。这些是验证脚本问题，没有发现 Core 或 Templates 产品缺陷，本子项没有修改业务源码。

### P2 ERP 采购/销售退货退款桌面闭环（2026-11-23）

- **状态：限定桌面闭环通过；P2 总体验收继续进行中。** 固定 Demo JAR SHA-256 `4e1f11283c811a908d2b534c518524a843a354ac28a968223eb73e1da15bb6b1`，在一次性 MySQL/Redis 与 1440×900 桌面浏览器中，先通过真实 UI 创建并审批采购订单→入库→采购退货、销售订单→出库→销售退货，再从财务付款/收款页面选择相应退货单，分别录入负数 `-3.00/-2.00` 并审批。
- **结果：** 退货及财务创建/审核 API 均 HTTP 200，页面错误、Console error、失败请求均为空。59 个 changeset 冷装；SQL 确认采购退货 `total=20,refund=3`、财务付款主单 `total=-3,payment=-3`、来源明细 `biz_type=12,biz_id=1,total=-20,payment=-3`；销售退货 `total=36,refund=2`、财务收款主单 `total=-2,receipt=-2`、来源明细 `biz_type=22,biz_id=1,total=-36,receipt=-2`。历史种子密码未变，JAR 与 dist 的 612 个静态资源字节一致。
- **证据及清理：** `docs/verification/2026-11-11-full-source-migration/erp-refund-browser-20261123/runtime.json`、`refund-browser.json`、`purchase-browser.json`、`sale-browser.json`；入口 `scripts/verification/erp_refund_browser_runner.py`，契约测试 `scripts/tests/test_erp_refund_browser_probe.py`。专用 MySQL/Redis、应用/UI 进程及 13448/16528/48328/5234 已清理，含运行凭据的原始日志已删除。
- **探针校准记录：** 退款选择器最初未沿用前置夹具名称；随后修正了负数退款输入方式及部分退款 SQL 字段符号断言。静态 chunk 请求曾偶发重置，runner 使用仓库其他浏览器 runner 已采用的 `request_queue_size=128` 后通过。这些均为验证实现问题；没有发现 Core/Templates 业务产品缺陷，未修改其源码或重建 Demo。ERP 仍只验桌面视口。

## P1 验收清单

| 项目 | 状态 | 现有证据和缺口 |
| --- | --- | --- |
| 前后端构建和打包 | 已完成（P1 范围） | Core `836125c` 重打包 SHA-256 `7d5adb2d1a27e0c68956ed64646dd1850adb733fb0e3b5467ff6adff0d9dcebc`；Demo UI 从 npm 公共 registry 按 `yuheng-ui@0.1.0-SNAPSHOT` 固定坐标和独立 pnpm 锁文件完成冻结安装、类型检查、14 项消费者测试及 Vite 3546 模块生产构建。Demo 后端 JAR SHA-256 `9a7b8fa44a02a2d42da0da98b518018a7c1c2f2e5e83d15711bd5afac156dcbd`（612 项静态资源）。Vite 保留既有大 chunk 警告；registry、SRI、锁文件及隔离消费证据见 `p1-build-20261118.json`。 |
| 数据库初始化与升级 | 已完成（P1 范围） | 同一固定 JAR 在独立 schema 首次执行 56 个 changeset，停止后重启同一 schema 再次启动；changeset 行、21 个种子用户密码哈希保持一致，空密码为 0，`system_operate_log.success` 列不存在。 |
| 登录、首页和菜单 | 已完成（P1 范围） | 固定包在隔离实例真实登录成功；角色页动态菜单和三视口页面通过，浏览器无 console、page、request 错误；启动脚本静态首页和匿名 API 保护也通过。 |
| 系统管理 | 已完成（P1 范围） | 隔离实例完成用户和角色创建、更新、查询回读、授权菜单和用户角色回读、删除清理；无角色用户执行授权返回 403 且关系未变。 |
| 基础设施 | 已完成（P1 范围） | 配置列表、筛选、取消和完整单条 CRUD 通过；无权/精确授权矩阵通过；任务列表和无权拒绝、文件列表和无权拒绝、数据库文件实际下载均通过。 |
| 租户和权限 | 已完成（P1 代表范围） | 配置、岗位、角色、用户精简列表完成匿名/无权/有权及租户头拒绝；角色和用户列表完成租户、启用状态、部门过滤；不外推为全量 T4 权限矩阵。 |
| 稳定运行和退出 | 已完成（P1 范围） | 隔离环境实际执行 `start.sh`、登录页/匿名后端检查和 `stop.sh`；Redis host/port/database 覆盖可传递，停止后端口释放，容器清理完成。 |
| 浏览器质量 | 已完成（P1 代表范围） | 固定包角色页在 1440×900、390×844、320×844 鼠标及390/320触摸场景通过；runner 启动前逐文件 SHA-256 比对 JAR 内612项静态资源与 dist，避免误归属。最终包配置页完成列表、筛选/重置、新增、详情、更新、软删除及取消编辑，浏览器/API 错误和失败请求均为 0，基础配置快照未变化；配置页 runner 也在启动前校验 JAR 与 dist 的 612 项资源一致。证据见 `config-crud-20261117/runtime.json`、`browser.json`。未将代表页面结果外推为全站视觉验收。 |

## 已完成的限定子项

- T2 前端配置、T5 JAR 静态资源和路由回退、T6 当时的构建与测试执行已在原计划标记完成；当前版本仍需按 P1 复验，不等于 T1/T3/T4 完成。
- 配置、角色窄屏弹窗、角色菜单保存回读、站内信主体隔离、OAuth 授权码绑定和单实例并发、部分 ERP 事务及权限场景已有隔离证据；具体条件见原计划及 `docs/verification/2026-11-11-full-source-migration/verification.md`。
- `role-page-collapse-desktop-20261117/result.json` 已更新为本轮固定 tarball 构建 JAR 的五场景回归（桌面、两种窄屏鼠标与两种窄屏触摸）；旧源码链接结果仅属历史记录。

## 后续执行纪律

### P2 当前固定 JAR 权限矩阵复验（2026-11-23）

- **状态：权限限定子项通过，P2 总项继续进行中。** 固定 Demo JAR SHA-256 `4e1f11283c811a908d2b534c518524a843a354ac28a968223eb73e1da15bb6b1`。ERP 方法级拒绝矩阵 128 个请求中 111 个受保护入口均返回拒绝且 33 张业务表快照不变；8 个上游没有方法级权限注解的认证读取入口仍可读。Member 管理端权限矩阵 67 个请求通过，冷装 59 changesets。ERP 正向角色矩阵当前 JAR 复验：基础资料 44 请求、主单据 30 请求、退货/辅助单据 50 请求、单据更新/删除 49 请求、库存与统计 11 请求；除 ERP 拒绝矩阵外各组均冷装 59 changesets。
- **机器证据：** `p2-erp-acl-current-20261123/runtime.json`、`p2-member-acl-current-20261123/runtime.json`、`p2-erp-master-auth-current-20261123/runtime.json`、`p2-erp-document-auth-current-20261123/runtime.json`、`p2-erp-aux-auth-current-20261123/runtime.json`、`p2-erp-mutation-auth-current-20261123/runtime.json`、`p2-erp-stock-auth-current-20261123-retry/runtime.json`。每组均确认自身容器已删除、应用/MySQL/Redis 专用端口无监听，密码未记录。
- **探针修正：** 库存/统计授权首次复验发现夹具仍使用 `2026-11-22` 单据日期；在 `2026-11-23` 执行时，统计 API 正确把金额归入昨日而非今日。只在 Demo 验收 runner 将夹具改成当前运行日，契约测试 3 项通过，并在新隔离 schema 复跑通过。没有发现需修复的 Core 或业务模板产品缺陷。
- **仍开放：** 本轮权限证据不覆盖 ERP 部门/仅本人数据范围，因模板尚未定义对应字段和规则；也不覆盖真实第三方认证/支付、缺少完整后端模板的 Trade/Promotion/Product 或 P2 全部业务验收。ERP 管理端只按桌面场景验收。

### P2 Member 实际签到与奖励事务（2026-11-23）

- `PHASE_GATE`：沿用 `YH-20261111-full-source-migration` 和本计划三类版本；任务为已有功能验证，规格/计划 `FROZEN`，授权来源为用户“按计划完成P2验证及功能修复”；原型 `NOT_REQUIRED`，无页面行为变更，`implementationAllowed=true`。
- AC/T-P2-SIGN-1：以当前 Demo JAR、独立 MySQL/Redis/端口和真实 App 登录，验证实际签到、积分、成长值、自动升级及各自流水的 API/SQL 一致性；重复签到拒绝且完整业务快照不变，另一会员无法读取其记录。
- AC/T-P2-SIGN-2：分别在成长值和等级流水插入处注入失败，证明此前签到和积分写入均原子回滚；移除故障后成功签到。平台历史用户密码保持不变。
- AC/T-P2-SIGN-3：失败保留独立证据；应用、UI、容器和专用端口精确清理。只修改验证入口、测试及证据；发现产品缺陷再在 Core/Templates 修复并选择性同步，不重建 Demo。
- **状态：限定子项通过；P2 总项进行中。** 固定 JAR `963149b3978618f370df9f63fe1db1a2841b7c3b2298d80766086cae27da5c97`、59 changeset 和关闭可选集成的独立 UI 构建完成 App/API/SQL 与桌面回归。经验流水、等级流水注入失败后五类数据快照不变；正常签到积分 15→19、经验 0→3 并自动升级，重复签到拒绝且无写入，另一会员分页和汇总为空；桌面扣分后 SQL 为 17。种子密码未变，浏览器无错误或失败请求，容器及端口清理完成。证据 `p2-member-signin-rewards-final4-20261123/`。不代表签到并发幂等或第三方授权已验证。

### P2 Member/Pay 钱包联调（2026-11-22）

- **PHASE_GATE：PASS；implementationAllowed=true。** 沿用 `YH-20261111-full-source-migration`；用户明确要求按计划完成 P2 并修复 Core/Templates，授权覆盖本子项。规格与计划 `FROZEN`：复用现有会员页面和钱包契约，无新页面设计（`NOT_REQUIRED`）。只改 Demo 验证脚本及证据；发现平台/模板缺陷时回到对应来源修复再消费，不清空 Demo、不把 Pay/PMS 临时消费者反写正式 Demo。
- **AC/T-P2-MEMBER-PAY-1：** 当前 Demo UI 构建时启用 `VITE_MEMBER_ENABLE_PAY=true`，连接显式初始化 Pay 的隔离消费包；桌面 1440×900 通过钱包读取、余额明细和增减余额，API 金额（分）、SQL 余额及流水与页面金额（元）一致；其它商城开关保持关闭。
- **AC/T-P2-MEMBER-PAY-2：** 真实只读角色无法修改余额，匿名与伪造租户头拒绝且钱包/流水快照不变；通过数据库故障注入证明余额更新和流水写入原子回滚。
- **AC/T-P2-MEMBER-PAY-3：** 凭据仅在内存/临时受限日志中使用；冷装及重启 changeset 一致，历史密码不变；应用、UI、专用 MySQL/Redis 和端口清理完成。失败保存独立证据，不覆盖历史通过结果。
- **执行状态：Pay 钱包与 Member 联动限定子项通过，P2 总项继续进行中。** 当前 Demo Python 测试 96 项（89 通过、7 项条件跳过）；Demo UI Vitest 20 项、类型检查、平台导入边界检查通过；Pay 开关开启的独立 Vite 生产构建通过（3548 模块，保留既有大 chunk 警告）。隔离消费者 JAR SHA-256 `15993a3d1986380abc84a9c07e7c0a0e8a0e6f1831e831605d1a99531571e8a5`，一次性 schema `yuheng_p2_member_pay_20261122`，首次/重启均为 107 个 changeset。桌面 1440×900 完成钱包详情与流水、增加 2.50 元和减少 0.75 元；API、页面与 SQL 最终余额 3.00 元/300 分及三条流水一致。真实只读角色余额修改 403、匿名修改 401、伪造 tenant-id 修改 403；流水插入故障返回 500，钱包和流水快照确认事务回滚。会员密码及所有平台种子密码保持不变，浏览器错误/失败请求为 0；专用容器、应用/UI 及 13402/16482/48262/5220 端口已清理。机器证据为 `p2-member-pay-second-20261122/member-pay-runtime.json` 与 `member-pay-browser.json`，回归入口 `scripts/verification/p2_member_pay_runner.py`。首轮浏览器失败属于角色菜单夹具没有包含会员页面父级菜单，失败与清理证据独立保留在 `p2-member-pay-first-20261122/`；已修正夹具并完整重跑。本轮没有发现需修复的 Core/Templates 产品源码缺陷，也没有修改其源码。真实社交/微信授权回调、真实支付渠道及其他外部服务、ERP 更细数据权限及 P2 总体验收仍开放；ERP 仅验收桌面管理后台。

### P2-MEMBER-OPTIONAL（2026-11-22）精简规格与实施计划

- **验证进展：部分通过，P2 继续进行中。** 模板与 Demo 的会员列表/详情已增加 Pay、Product、Trade、Promotion 独立开关，默认关闭；钱包字段、关联标签和列表操作依配置及权限显示。固定后端 JAR `fb66307402876756a689c7a9e4a079ceb351d16619d05404d2f67138fdc81302` 配合本次独立构建的 Demo UI，在隔离数据库完成 59 个 changeset、会员 API/SQL 和桌面浏览器验证；详情访问会员自有签到、成长值、地址时没有 Pay/Product/Trade/Promotion 请求，浏览器错误和失败请求均为零，隔离容器及端口已清理。证据 `p2-member-optional-final-20261122/member-runtime.json`；首次浏览器断言选择器不唯一导致失败，证据保留于 `p2-member-optional-20261122/`。Pay 钱包开启后的 Member 联动已由本计划 `P2 Member/Pay 钱包联调` 完成限定桌面/API/SQL 验证；Product/Trade/Promotion 尚无可接入的完整后端模板，不能声称其集成可用。
- **单模块构建：通过限定范围。** 模板核心页面改为只依赖无业务导入的集成契约和空适配器；Demo 在消费端适配器中注册现有 Pay/Mall 组件和 API。临时消费者排除 `src/api/pay`、`src/api/mall`、`src/views/mall` 及会员页面中的可选组件，使用模板空适配器直接执行 `vue-tsc --noEmit` 和 `vite build`，均退出 0。Demo 适配器属于消费端定制，模板更新不会覆盖它。隔离单模块构建不等同于开启所有商城集成的完整构建；Pay 钱包与 Member 的实际联动已有后续专项证据，Product/Trade/Promotion 后端仍未接入。
- **ERP 同版补充验证：通过限定范围。** `erp-p2-sidecar-20261122/runtime.json` 记录 10 个单据接口创建和更新明细归属、53 请求采购销售财务流程、24 请求库存入库/出库/调拨/正向盘点审核与反审核；隔离容器和端口清理通过。负向盘点、库存不足、并发和产品/仓库之外的授权组合仍待验证。
- **ERP 库存失败路径补充：通过限定范围。** `erp-stock-negative-20261122/runtime.json` 和 `stock-lifecycle.json` 记录固定 JAR `fb66307402876756a689c7a9e4a079ceb351d16619d05404d2f67138fdc81302`、59 changesets、31 个 HTTP 请求：盘亏审核/反审核/再审核库存正确；两行出库第二行库存不足返回业务错误，第一行变动、单据状态及流水均回滚。独立容器与 13387/16468/48232 端口已清理。并发和产品/仓库之外的授权组合仍待验证。
- **ERP 并发库存补充：通过限定范围。** `erp-stock-concurrency-20261122/runtime.json` 和 `stock-lifecycle.json` 记录同版 JAR、59 changesets、37 个 HTTP 请求：两个并发出库各申请 4 件时，一单审核成功、一单返回库存不足，最终库存为仓库 1 的 1 件、仓库 2 的 2 件，库存流水只增加一次；独立容器与 13388/16469/48233 端口已清理。产品/仓库的权限与租户组合已补验，其它 ERP 授权组合仍待验证。
- **ERP 产品/仓库权限与租户组合：通过限定范围。** 当前 Demo JAR `fb66307402876756a689c7a9e4a079ceb351d16619d05404d2f67138fdc81302` 在一次性 schema `yuheng_t4_erp_tenant_20261122` 执行 59 个 changeset，两个真实租户（121、122）分别使用有权限与无权限用户完成产品和仓库的查询、创建、更新、默认状态写入及删除；无权限请求逐项返回 403 且 SQL 快照不变，跨租户详情和分页不返回对方数据，同一 token 伪造 `tenant-id` 的读取和写入均返回 403，历史种子用户密码未改变。56 个 HTTP 请求、清理结果见 `docs/verification/2026-11-11-full-source-migration/erp-tenant-permission-20261122/runtime.json`，入口为 `scripts/verification/erp_tenant_permission_runner.py`。该结果只覆盖产品与仓库的权限/租户组合，其它 ERP 控制器、数据权限范围、并发授权和外部认证仍开放。
- **ERP 单据非法审核状态：通过限定范围。** 同版 JAR 在 `yuheng_t4_status_20261122` 冷装 59 个 changeset，真实登录后对采购、销售、库存和财务共 12 类单据调用 `update-status?status=99`；全部返回业务码 400，13 个请求（含登录）完成后 ERP 全表快照逐项保持不变。结构化结果位于 `docs/verification/2026-11-11-full-source-migration/erp-p2-sidecar-20261122/audit-status.json`，编排结果见同目录 `runtime.json`。该结果只关闭非法状态输入边界，不代表所有 ERP 权限、数据权限和事务组合完成。
- **ERP 方法级权限矩阵：通过限定范围。** 同版 JAR 在一次性 schema `yuheng_t4_erp_acl_20261122` 冷装 59 个 changeset，使用真实登录的无角色用户访问 ERP 20 个控制器的详情、分页、导出、创建、更新、审核和删除入口。128 个请求中，111 个带 `@PreAuthorize` 的入口全部返回 403；每次拒绝后 33 张 ERP 业务表快照均未变化。另记录 8 个上游源码本来就没有方法级 ERP 权限注解的已认证精简读取入口：产品、分类、单位、供应商、客户、账户、仓库 `simple-list`，以及库存 `get-count`；它们没有匿名放行，但无 ERP 权限用户可读取，属于原始项目继承的接口契约，不能把迁移一致性误写成缺陷。证据为 `docs/verification/2026-11-11-full-source-migration/erp-permission-matrix-20261122/runtime.json`，入口为 `scripts/verification/erp_permission_matrix_runner.py`。本轮只关闭 ERP 方法级拒绝矩阵；数据权限、各授权角色的成功矩阵、跨租户组合和外部认证仍开放。
- **ERP 基础资料授权正向矩阵：通过限定范围。** 在一次性 schema `yuheng_t4_erp_auth_20261122` 中为真实普通用户授予 7 类基础资料的 create/query/update/delete 权限，使用固定 JAR 完成 44 个 HTTP 请求：分类、单位、供应商、客户、账户、仓库、产品均可创建、详情/精简列表/分页读取和更新；仓库默认状态可更新；随后逐项删除且 SQL 确认创建行均为逻辑删除。历史种子用户密码未改变，专用 MySQL/Redis 与 13392/16473/48237 已清理。证据为 `docs/verification/2026-11-11-full-source-migration/erp-authorized-master-20261122/runtime.json`，入口为 `scripts/verification/erp_authorized_master_runner.py`。该结果补齐基础资料正向角色路径，不代表单据、库存、统计的全量授权成功矩阵或完整数据权限。
- **ERP 库存/统计授权正向矩阵：通过限定范围。** 同版 Demo JAR（SHA-256 `fb66307402876756a689c7a9e4a079ceb351d16619d05404d2f67138fdc81302`）在一次性 schema `yuheng_t4_erp_stock_auth_20261122` 冷装 59 个 changeset，为真实普通用户只授予 `erp:stock:query`、`erp:stock:export`、`erp:stock-record:query`、`erp:stock-record:export` 和 `erp:statistics:query`。11 个真实请求通过库存详情/分页/Excel 导出、库存明细详情/分页/Excel 导出、认证库存数量，以及采购和销售日/月统计；统计夹具按入库减退货、出库减退货得到采购 80、销售 170。证据为 `docs/verification/2026-11-11-full-source-migration/erp-stock-statistics-auth-20261122/runtime.json`，入口为 `scripts/verification/erp_stock_statistics_runner.py`，脚本回归为 `scripts/tests/test_erp_stock_statistics_probe.py`；专用容器和 13393/16474/48238 已清理。该轮只关闭库存/统计查询的正向授权子项，不代表 ERP 全量角色授权、数据权限组合或 P2 总体验收完成。
- **ERP 单据授权正向矩阵：通过限定范围。** 同版 Demo JAR 在一次性 schema `yuheng_t4_erp_document_auth_20261122` 冷装 59 个 changeset，为真实普通用户只授予采购订单、采购入库、销售订单、销售出库、付款单、收款单各自的 `create/query/export/update-status` 权限。30 个真实请求通过六类单据创建、详情/分页/Excel 导出和审核；SQL 最终库存为 6、付款为 100、收款为 80，各核心单据状态为 20。证据为 `docs/verification/2026-11-11-full-source-migration/erp-document-auth-20261122/runtime.json`，入口为 `scripts/verification/erp_document_authorized_runner.py`，脚本回归为 `scripts/tests/test_erp_document_authorized_probe.py`；专用容器和 13394/16475/48239 已清理。该轮只关闭采购/销售/资金主单正向授权子项，不代表 ERP 全量权限、数据权限组合、退货/其它库存单据角色路径或 P2 总体验收完成。
- **ERP 退货与库存辅助单据授权正向矩阵：通过限定范围。** 同版 Demo JAR 在一次性 schema `yuheng_t4_erp_aux_auth_20261122` 冷装 59 个 changeset，为真实普通用户授予采购/销售来源单、退货单、其它入库/出库、库存调拨/盘点各自的 `create/query/export/update-status` 权限。50 个真实请求通过退货、其它入库/出库、调拨和盘点的创建、详情/分页/Excel 导出与审核；采购/销售退货和库存辅助单据的 SQL 状态均为 20，双仓最终库存为 4 和 3。证据为 `docs/verification/2026-11-11-full-source-migration/erp-auxiliary-auth-20261122/runtime.json`，入口为 `scripts/verification/erp_auxiliary_authorized_runner.py`，脚本回归为 `scripts/tests/test_erp_auxiliary_authorized_probe.py`；专用容器和 13395/16476/48240 已清理。该轮只关闭辅助单据的正向授权子项，不代表 ERP 全量数据权限、其它写操作权限或 P2 总体验收完成。
- **ERP 单据更新/删除授权矩阵：通过限定范围。** 同版 Demo JAR 在一次性 schema `yuheng_t4_erp_mutation_auth_20261122` 冷装 59 个 changeset，为真实普通用户授予 12 类 ERP 单据的 `create/query/export/update/update-status/delete` 权限。49 个真实请求覆盖采购/销售订单、入库/出库、退货、其它入库/出库、盘点、调拨、付款和收款的草稿更新与逻辑删除；SQL 确认各草稿行 `deleted=1`，来源单据链仍可继续使用。证据为 `docs/verification/2026-11-11-full-source-migration/erp-mutation-auth-20261122/runtime.json`，入口为 `scripts/verification/erp_mutation_authorized_runner.py`，脚本回归为 `scripts/tests/test_erp_mutation_authorized_probe.py`；专用容器和 13396/16477/48241 已清理。该轮只关闭 ERP 单据 update/delete 的正向授权子项，不代表完整数据权限、已审核单据删除策略或 P2 总体验收完成。
- **ERP 全业务租户边界：通过限定范围。** 当前 Demo JAR `fb66307402876756a689c7a9e4a079ceb351d16619d05404d2f67138fdc81302` 在一次性 schema `yuheng_t4_erp_full_tenant_20261122` 执行 59 个 changeset，两个真实租户（121、122）使用完整 ERP 权限角色完成 23 个资源族、33 张业务表的代表性业务创建/审核和读取。263 个 HTTP 请求验证了本租户详情/分页可见、跨租户详情/分页不可见、跨租户审核/删除 SQL 快照不变及伪造 `tenant-id` 拒绝；历史种子密码未改变。删除服务对租户过滤后的空结果返回统一成功值，探针按 SQL 不变断言该上游契约。证据为 `docs/verification/2026-11-11-full-source-migration/erp-full-tenant-20261122/runtime.json`，入口为 `scripts/verification/erp_full_tenant_permission_runner.py`；专用容器和 13397/16478/48242 已清理。该轮关闭 ERP 全资源的代表性租户边界，不外推为完整数据权限范围、Member 外部认证、Pay/Mall 真实联调或 P2 总体验收完成。
- **ERP 全业务租户边界复验（当前 Demo JAR）：通过限定范围。** 当前 Demo JAR `963149b3978618f370df9f63fe1db1a2841b7c3b2298d80766086cae27da5c97` 在一次性 schema `yuheng_t4_erp_full_tenant_20261122` 冷装 59 个 changeset，两个真实租户完成 263 个 HTTP 请求；本租户详情/分页可见、跨租户详情/分页不可见、跨租户审核/删除不改变 33 张 ERP 业务表快照，伪造 `tenant-id` 被拒绝，历史种子密码不变，容器和 13397/16478/48242 已清理。当前证据覆盖 23 个资源族和 33 张业务表，不能外推为 ERP 部门或仅本人数据范围。模板静态复核确认业务表只有 `tenant_id` 与审计 `creator` 等字段，未注册 `dept_id/user_id` 数据权限列；此能力边界沿用原始 ERP 模板，不在 Core 中新增推断规则。证据为 `docs/verification/2026-11-11-full-source-migration/erp-full-tenant-20261122/runtime.json`，入口为 `scripts/verification/erp_full_tenant_permission_runner.py`。
- **ERP 全业务租户边界当前固定 JAR 复验（2026-11-23）：通过限定范围。** SHA-256 `4e1f11283c811a908d2b534c518524a843a354ac28a968223eb73e1da15bb6b1` 在隔离 schema `yuheng_t4_erp_full_tenant_20261123_p2` 冷装 59 changesets，263 个请求覆盖两个真实租户的 23 个资源族、33 张业务表；本租户读取成功、跨租户读取不可见、跨租户审核/删除后全表快照不变、伪造租户头拒绝，历史密码不变。证据 `docs/verification/2026-11-11-full-source-migration/p2-erp-full-tenant-current-20261123/runtime.json`；专用容器和 13430/16505/48300 已清理。runner 已增加 backend 日志密码和 Bearer token 脱敏及回归测试。该结果不覆盖尚未在 ERP 模板建模的部门/本人数据范围或 P2 总体验收。
- `PHASE_GATE`: workId `YH-20261111-full-source-migration`；code `0.1.0-SNAPSHOT`、governance `0.2.0`、knowledge `0.1.0`；stage `implementation/verification`。规格/计划 `FROZEN`，授权为用户“按计划完成 P2 验证及功能修复”以及明确的可自由选择业务模板、保留消费端定制的项目关系。局部接线原型 `NOT_REQUIRED`。implementationAllowed `true`。
- REQ-P2-OPTIONAL：独立会员模块不能默认调用尚未接入的支付/商城服务。保留已有完整关联组件，以消费端显式配置分别启用 Pay、Product、Trade、Promotion；默认关闭，开启以相应模块、权限和数据库已经接入为前提。模块配置不代替权限检查；不根据管理员通配权限推断模块已安装，不通过捕获错误返回空成功。
- AC-P2-OPTIONAL-1 / T-P2-OPTIONAL-1：先增加配置解析和模板接线回归红灯；模板增加模块配置，控制详情关联标签、钱包账户字段与请求、列表余额/优惠券操作；保留所有会员自有功能。
- AC-P2-OPTIONAL-2 / T-P2-OPTIONAL-2：仅同步本次相关模板文件到 Demo，保留原有 Core 导入适配与业务定制。类型检查、UI 测试、构建及当前制品隔离会员 API/SQL/桌面浏览器通过；关闭模块不得发出 Pay/Mall 请求，配置开启的接线仍存在。实际 Pay/Mall 集成未运行不得算通过。
- AC-P2-OPTIONAL-3 / T-P2-OPTIONAL-3：记录复现 JSON、修复版本/hash、检查与资源清理。Only Modify：Member 模板 UI/说明与对应测试、Demo 对应消费 UI 与验证脚本/证据；Do Not Modify：已执行 SQL、共享库/缓存、历史密码、其它业务定制。回滚限相关源码文件；不得重建或清空 Demo。

- 每个优先级的条目链接到具体运行结果和版本；失败、跳过、临时依赖或外部阻塞均明确标记，不借历史通过记录推断当前通过。
- 优先复用同一隔离环境完成一组相关业务验证，减少反复启动；测试前确认 schema、端口及进程归属，结束只清理本轮创建的资源。
- T1/T3/T4 和其他原定范围继续开放；独立 uni-app 工程不等同后台网页窄屏验证，其纳入范围须按原始需求和后续确认另行明确。
- 版本化 registry、第三方账号及真实外部服务无法使用时，记录其对验收的实际阻塞，同时推进不依赖它们的工作，不以模拟代替真实外部验收。

### P2 Member 外部认证边界（2026-11-22）

- **状态：限定子项通过，P2 总项继续进行中。** 通过 Core 回归测试和 Demo 隔离运行关闭短信参数/错误验证码、调试短信成功登录、社交参数/非法类型/无效 code、微信小程序参数/无效 code，以及失败请求不新增会员、社交绑定或 OAuth token 的边界。
- **Core 修复链路：** 根因先在 Demo 隔离 JAR 日志中定位为 `AuthRequestFactory` 对空 `extend` 配置的 NPE，随后发现无配置时的 `AuthException: Unsupported operation` 仍未被 `SocialClientServiceImpl` 转换。修复均在 `yuheng-core`，新增 `AuthRequestFactoryTest` 和 `SocialClientServiceImplTest`，5 项定向测试通过；Core 安装制品 SHA-256 为 `f281a3d229f40fc3ad0ed09c93cca5acd70950a761181856ad099126da7531cb`。
- **当前固定 JAR 复验（2026-11-23）：限定边界通过。** JAR SHA-256 `4e1f11283c811a908d2b534c518524a843a354ac28a968223eb73e1da15bb6b1`；schema `yuheng_p2_member_auth_20261123_current`；59 changesets；结果 `docs/verification/2026-11-11-full-source-migration/p2-member-external-auth-current-20261123/runtime.json`，底层请求/SQL 记录 `member-external-auth-runtime.json`；隔离入口 `scripts/verification/p2_member_external_auth_current_runner.py` 复用 `p2_member_external_auth_probe.py`。调试短信登录成功并验证会员创建、tenant_id、验证码消费及 OAuth token 行数；无效短信码、社交 code、微信小程序 code 均按预期拒绝，拒绝请求不增加会员、社交绑定或 token。token 值只在内存处理，系统用户密码未变化；专用 MySQL/Redis 和 13436/16491/48278 已清理。此结果更新此前 `963149…` JAR 的历史证据，但不代表真实社交/微信第三方成功回调已验收。
- **证据治理：** 运行日志曾暴露第三方 access token，已从工作区删除；探针现在只保留脱敏错误摘要，并有回归测试证明 URL 和 token 不进入摘要。不得把日志文件作为运行证据提交。
- **继续开放：** 当前通过的是 Core 调试短信渠道成功路径，不等同于真实运营商短信服务；没有真实第三方凭据，社交/微信成功授权和回调仍未验证。Pay/Mall 开启后的真实联调、ERP 更细数据权限组合和 P2 总体验收仍未关闭。

### P2 业务模板 Pay/PMS SQL 迁移复验（2026-11-22）

- **前端消费验证未通过：** 在隔离 Demo UI 副本中复制 Pay/PMS 模板并执行 `vue-tsc`，出现隐式 `any`、缺少本地兼容转发和声明等错误。Core 包已导出二维码、文件预览、人员选择和部分工具，当前 Demo 的兼容转发及类型声明仅覆盖既有用途；还需区分真实模板类型缺陷、Core 能力和消费端接线，并完成构建及桌面浏览器验收。临时副本中的 Pay API 与既有少量文件发生合并，该次不是干净的独立 Pay 模板验收。
- **Core 匿名请求修复：** PMS 公开分享请求使用 `headers.isToken=false`，旧 Core 会附加登录令牌并对 401 触发刷新。Core 请求客户端现识别该标记，移除认证及访问租户头且不改变已有会话；请求客户端红绿回归、完整 UI 127 项测试和发布构建通过。该修复尚未发布 npm，未在 Pay/PMS 完整消费工程中运行，公开分享桌面端到端验收继续开放。
- **Pay API 严格类型修复：** Templates 提交 `bcbfb6c` 为渠道导出、钱包充值套餐分页、钱包流水分页参数补充 `PageParam`。隔离副本的这三份实际源码在严格 TypeScript 检查下从 3 个 TS7006 变为通过；Templates 86 项 Python 测试通过。该检查不覆盖其他 Pay/PMS 页面。隔离转发实验还发现兼容源码被类型检查直接引用后存在额外 Core 类型错误；PMS 分享页面需要消费端显式注册 `/pms/kb/document/share/:token` 路由，Core 白名单本身不会注册路由。完整接线、构建和公开分享验证仍待完成。
- **PMS 分享链接子路径修复：** Templates 提交 `f060895` 使用 Vue Router 的 history base 生成公开分享链接，并编码令牌；隔离消费环境的真实 Vue Router 测试覆盖根路径和 `/app/`，从失败变为 2 项通过。模板说明补充顶层匿名路由及服务端回退要求。未执行真实服务及浏览器分享闭环，不能据此关闭该验收项。
- **Pay 微信证书上传修复：** Templates 提交 `d51cbc8`，原 `before-upload` 包装函数丢弃校验返回值，导致错误格式及超过大小限制的文件仍可进入读取；现传递校验结果。针对实际组件钩子的合法、错误格式和 2 MB 边界测试经红绿验证通过，模板 87 项测试通过。真实浏览器和支付渠道联调仍未执行。
- **Pay/PMS 消费构建与 Core 指令修复：** 隔离 UI 增加 Pay/PMS 页面 glob 和 PMS 顶层公开分享路由后，Vite 编译 3904 模块成功，仍有实验性兼容转发、合并目录和未通过的严格类型检查，不能视为完整接入。使用已发布旧 npm 包的桌面分享页测试在 API 请求前因权限指令 `useI18n` 未定义而空白。Core 提交 `6cdea24` 显式导入该依赖，红绿测试通过，UI 全量 128 项及发布构建通过；同步本地 tarball SHA-256 `a8ee56be3c248c785ab7c6ef723b16c552dd886744e11ed890f431ea855b427b`。新包尚未发布 npm 或在隔离消费者浏览器复验；临时 Vite 5219 已停止。
- **临时消费者后端代表验证：部分通过。** 人工将 Pay/PMS 后端及 changelog 复制到临时 Demo 副本，按消费端包名适配并添加支付 SDK；补入 Core 的 `lombok.config` 后编译、打包、启动成功。隔离库记录 106 个 changeset；Pay 应用 CRUD、订单/钱包空列表、匿名 401，以及 PMS 项目生命周期和知识库 CRUD 通过。该轮未运行 Skill 初始化、Pay/PMS 前端、普通用户权限矩阵或真实支付渠道与回调；正式 Demo 未预置 Pay/PMS，P2 总体验收继续进行中。详细记录见 `verification.md` 的“Pay/PMS 临时消费者运行验证”。

- **状态：SQL 迁移子项通过；P2 总项继续进行中。** 使用 Templates 当前 `template-pay` 与 `template-pms` 的独立 Liquibase changelog，在隔离 MySQL 8.0.33 schema 中分别执行首次更新和重复更新。Pay 首次执行 14 个 changeset、重复执行 0 个；PMS 首次执行 33 个、重复执行 0 个。Pay 14 张、PMS 33 张业务表均创建成功且业务行数为 0，未写入凭据、示例订单、钱包或知识库数据。
- **冲突保护：** 在两个新的冲突 schema 中预先创建首张业务表，Liquibase 均以 `PreconditionFailedException` 退出，更新摘要为 `Run: 0`，预先存在的表保持不变，没有把冲突标记为已执行。
- **证据与清理：** 结构化结果为 `docs/verification/2026-11-11-full-source-migration/p2-template-sql-20261122/runtime.json`；使用临时 probe 用户和独立 schema，验证后删除用户、schema 和临时资源，`cleanup=true`。共享 `yuheng_demo`、历史用户密码和运行服务未触碰。
- **运行边界：** 当前 `yuheng-demo` 只有 ERP、Member 后端模块，`yuheng-core` 的 Pay/PMS 路由仍是禁用占位入口；Templates 也没有独立完整的 Trade/Promotion/Product 后端模板接入。本轮不把 Pay/PMS SQL 冷装结果扩大为 Demo Pay/PMS API、支付渠道、商城订单或会员可选集成通过；需要联调时必须先通过 Skill 将完整模块源码和自身 changelog 显式初始化到 Demo，再使用当前 Core 版本构建验证。

### P2 PMS 模板前端类型与构建复验（2026-11-22）

- **状态：模板前端构建子项通过，P2 总项继续进行中。** Templates 提交 `95c2903` 修复 PMS 消费工程严格类型检查暴露的模板问题：Element Plus 树引用改用 `TreeInstance`，回收站层级变量、下拉命令、项目分组命令、字典选项、拖拽表格引用和项目模板 VO 回调补充显式类型；工作台“全部/迭代”页签明确返回无工作项类型，保持请求语义。
- 按 TDD 先增加模板类型契约测试，修复前 3 组契约断言失败，修复后 Templates 全量 Python 测试为 91/91；随后补充第二处 Sortable DOM 类型收窄，提交 `b2570b3` 后再次通过。`git diff --check` 通过。PMS 源码复制到隔离消费工程后，补齐消费工程直接声明的 `sortablejs`、`@types/sortablejs` 和 `@types/lodash-es`，正式 `src/views/pms` 路径的 `vue-tsc --noEmit` 诊断为 0，正式 Pay/PMS 目录也无自身诊断；Vite 生产构建成功，保留既有大 chunk 警告。
- 模板 README 已明确：`sortablejs` 是运行时依赖，`@types/sortablejs` 是开发依赖，项目模板表单还需要 `lodash-es` 与 `@types/lodash-es`；模板不携带全局类型声明，也不把这些依赖转化为 Demo 运行时依赖。隔离消费者的完整 `vue-tsc` 仍失败，剩余错误来自 Core compat 源码、Demo 系统组件重复默认导出，以及从 Templates 根目录直接纳入检查的 `share-url.ts` 路径解析；早期 `src/pay` 实验目录另有缺失 `AppForm.vue` 的复制残留，已确认正式模板 `src/views/pay` 包含该文件，不能把实验副本错误记为模板缺陷。
- 本轮没有把 PMS 页面或 SQL 写入 `yuheng-demo`。Demo 仍只初始化 ERP/Member；PMS 的源码复制、路由接入、后端 API/权限和桌面浏览器闭环必须由使用者通过 Skill 显式初始化。模板更新通过预览、冲突分类和选择性合并进入已有消费工程，不清空、重建或覆盖 Demo 定制。

### P2 模板更新治理闭环（2026-11-22）

- **状态：限定子项通过，P2 总项继续进行中。** 在 `yuheng-business-templates` 增加显式模板更新工具 `tools/template_update.py`、ERP 映射示例和回归测试；Core 的业务模板迁移 Skill 增加基线、预览、冲突、删除和 Liquibase 前向 changeset 规则。Demo 不作为模板运行时依赖，也不会因模板更新被重建、清空或覆盖。
- ERP 当前初始化基线记录在本机临时文件 `/tmp/yuheng-erp-template-state-20261122.json`。以 Templates `d838c90`、Core `c0aae65` 和 Demo `908c562` 为来源运行只读预览，309 个映射文件为 `unchanged`，`template_added`、`template_changed`、`consumer_only`、`consumer_customized`、`conflict`、`template_deleted` 和 `unclassified_difference` 均为 0；消费端文件未修改。结构化证据：`docs/verification/yuheng-template-update/erp-preview-20261122.json`。
- 更新工具的安全回归先验证红灯再修复：基线已有包名/请求/UI/数据库适配时，模板后续修改必须进入 `conflict`，禁止自动覆盖 Demo 定制；消费端独有文件保留，冲突和删除默认阻止应用。Templates 更新工具定向测试 7 项、全量测试 83 项通过；Demo 治理 `sync-specs-api.py --verify --json` 通过且同步无变化。
- SQL 仍按模板文件参与比较，但工具不会改写已执行 changeset、清理 checksum、删除业务数据或自动执行迁移。SQL 修复必须先回到业务模板增加新的前向 Liquibase changeset，再由 Demo 按目标库状态隔离验证。

## 2026-11-17 提交准备检查

- `git diff --check` 和暂存区 `git diff --cached --check` 均无输出；不能据此推断未跟踪文件已通过内容或凭据审查。
- 运行本地 Demo UI Vitest：3 个文件、14 项通过；沙箱限制导致 UnoCSS inspector 与 Vite WebSocket 监听报错，不能把本次作为无告警运行验收。依赖仍通过 Core 源码链接解析。
- 敏感模式初筛命中若干验证脚本，尚未逐一确认是临时夹具还是凭据；不能将初筛命中直接认定为泄露，也不能在完成审查前批量提交。
- 下一步按运行源码/配置、项目治理快照、验证脚本与证据分别审查，保留现有暂存状态直到确定完整提交内容；记录必要的 Core 版本及未提交菜单修正。固定版制品和独立锁文件缺口继续列入 P1，不用源码链接冒充版本化消费。

## P0 提交结果（2026-11-17）

- Demo 运行源码、配置、数据库迁移、生命周期脚本及其测试已提交：`01d1507`。Git 识别原有启动类和配置迁移至新模块；未包含构建产物。
- AI 规则、技能快照、迁移技能、验证脚本和计划已提交：`a41d8b3`。39 个 Python 验证脚本通过语法解析；受管 Markdown 的既有双空格换行保留。
- 结构化验证结果及文本已提交：`78a702b`；224 个 JSON 通过解析，文本敏感模式初筛没有命中。初筛不能证明不存在所有敏感数据。
- 127 张验证截图保留在本地、未提交；这些图片尚未逐张审查，仓库中的引用可能无法在其他检出环境访问。不得把结构化证据视为已替代需要截图的视觉验收。
- 本轮离线 Maven 测试 40 项通过，前端 `vue-tsc --noEmit` 通过；Python 脚本测试 30 项中 23 项通过、7 项跳过。Maven 复用本地编译产物并跳过前端构建。前一次 Demo UI Vitest 14 项通过但监听权限告警存在。
- 配置中非占位敏感字面值与提交前 Git 历史相同；其有效性未核实，不将“已存在于历史”当作安全证明。后续应按部署环境单独治理和轮换可能有效的凭据。
- Core 菜单修正已提交为 `836125c`；Demo 工作区 `node_modules/yuheng-ui` 仍是源码链接，最新菜单验收还需在该 Core 提交对应的固定制品上复验。固定版 registry 和独立锁文件仍是 P1 缺口。
- P0 的 Demo 代码和文本记录已提交；127 张截图经 OCR 初筛发现部分含隔离库用户名、登录日志或页面数据，保留本地而未提交。截图审查和固定制品构建继续作为明确的未完成项，不把 P0 记录解释为全量迁移完成。

## P1 固定包验证进展（2026-11-17 至 2026-11-18）

- **状态：进行中。** 沿用 workId `YH-20261111-full-source-migration`、code `0.1.0-SNAPSHOT`、governance `0.2.0`、knowledge `0.1.0`，基于已确认的完整迁移和 P1 优先验证授权。本轮修改范围为 Demo 构建脚本与验证探针，不改变平台业务或数据库迁移。
- Core `836125c` 的 UI 制品 `/tmp/yuheng-p1-core/yuheng-ui-0.1.0-SNAPSHOT.tgz`，SHA-256 `7d5adb2d1a27e0c68956ed64646dd1850adb733fb0e3b5467ff6adff0d9dcebc`。独立临时消费者实际安装此包，解析到自己的 pnpm 存储而非 Core 源码；类型检查、14 项 Vitest、平台导入边界和 Vite 生产构建通过。
- `scripts/build-ui.sh` 已支持校验版本匹配的本地 tarball，在临时目录安装、检查及构建。新增路径回归先复现 Maven bootstrap 子目录内相对 tarball 无法定位，再将相对 `YUHENG_UI_PACKAGE` 统一按 Demo 根目录解析；该回归及版本拒绝、pnpm 失败保护测试通过。使用 Core `836125c` 跟踪 tarball（SHA-256 `125b85b912806f517489c8824bc8c7651712d52723a59f1e0562497584e2d524`）重新构建：Demo UI 类型检查、Vite 3544 模块构建通过，Maven JAR 含 612 项静态资源，JAR SHA-256 `ed4896673689bb9b3176686a2b44af9273e9ca20029a11e900de4cc632c9fa9b`。此次 build 脚本跳过 Maven tests；单独执行 `mvn -o -Dexec.skip=true test` 为 40/40 通过。Vite 保留既有大 chunk 警告。
- 首版固定包（SHA-256 `d2b91f8f37a47c616c72b7c54d3b7e8c3b755189a6ebf23219baf2473595d2af`）在独立 MySQL/Redis 中完成上述 UI 验收。当前 Core tarball 重建的新 JAR 另在隔离 P1 平台探针复验：56 changesets 首次/重启一致，21 个种子用户密码字段保持不变，System/Infra 用户和角色创建/更新/授权回读、无角色 403、任务/文件拒绝、数据库文件下载及 start/stop 生命周期均通过；结构化结果仍在 `p1-fixed-package-20261117/platform-runtime.json`，已更新到本次 JAR 哈希。专用容器与 13372/16452/48212/48213/5202 均已清理。该条为旧跟踪 tarball 的阶段记录，最终重打包与复验结果以下节为准。
- 配置页列表、筛选、重置、编辑取消及单条新增/修改/删除完成，浏览器记录无错误和失败请求，基础配置快照前后一致，探针记录最终软删除。隔离容器和端口均清理。首次配置探针因旧断言 54 与实际 56 不符而失败；CRUD 探针两次因隐藏对话框与列表筛选器同名而失败，均在独立库发生，修正后重跑通过。
- 原共享 Demo 前后端进程为解除 JAR 占用而停止，目前未重新启动；共享 MySQL 和 Redis 未用于隔离验证。运行脚本的 PID 文件中后端 PID 已失效，启动前需先检查生命周期状态。
- P1 平台最小闭环已有当前 JAR 的隔离证据。仍未关闭的交付限制为固定 `yuheng-ui@0.1.0-SNAPSHOT` registry 干净安装和 Demo UI 独立锁文件；最终重打 tarball 的隔离消费者 typecheck/build、14 项测试和边界检查已补齐（见下节）。上述缺口与 T1/T3/T4 全量验收分开跟踪，不以 tarball 路径冒充 registry 冻结安装。

## P2 会员后台代表闭环（2026-11-17 至 2026-11-18）

- **状态：会员后台 API/SQL 代表范围通过；P2 总项继续进行中。** 使用固定 Demo JAR（SHA-256 `d2b91f8f37a47c616c72b7c54d3b7e8c3b755189a6ebf23219baf2473595d2af`）、新建隔离 schema `yuheng_p2_member_20261117`、独立 MySQL/Redis 容器和端口，首次执行 56 个 Liquibase changeset；共享 `yuheng_demo` 未连接。
- 匿名会员标签创建返回 401；真实登录但无角色的用户返回 403，数据库无写入。管理员对标签、分组、等级完成创建、更新、详情回读及 SQL 核对，随后完成逻辑删除。
- 两个租户的会员用户通过隔离夹具写入。租户 1 管理员读取租户 2 用户返回空；伪造租户 2 请求读取租户 1 用户返回 403，数据库行不变。管理员更新租户 1 会员资料后，HTTP 回读和 SQL 字段一致。
- 积分记录插入触发器故障注入后，`update-point` 返回 500，会员积分仍为 10、积分记录表仍为空；移除触发器后正常加 5 分，会员余额及记录表 `point:total_point` 为 `15` 与 `5:15`。分组和等级仍被会员引用时删除分别返回 `GROUP_HAS_USER`、`LEVEL_HAS_USER`；验证后仅在一次性 schema 中清除关联并完成逻辑删除。
- 结构化证据及可复跑探针：`docs/verification/2026-11-11-full-source-migration/p2-member-platform-20261117/member-runtime.json`、`scripts/verification/p2_member_platform_probe.py`。运行结束 Demo 进程停止、临时容器删除、13373/16453/48220 均无监听。凭据不写入证据。
- 标签页浏览器消费验收也在同一隔离 JAR/schema 完成：真实登录后加载会员标签列表，完成页面新增、编辑和删除；浏览器 console/page error、failed request 均为 0，三项写 API 均成功。浏览器结果保存在同目录 `member-browser.json`，运行探针自动执行并将结果嵌入 `member-runtime.json`。
- 会员用户浏览器验收于 2026-11-18 完成：页面按昵称筛出隔离夹具 `990951`，通过“更多 → 修改积分”扣减 2 分，计算值和列表刷新值均为 13。`PUT /admin-api/member/user/update-point` 返回 HTTP 200；API/SQL 回读用户积分为 13，最新流水为 `point=-2,total_point=13,biz_type=2`。标签页 CRUD 与用户页筛选/积分调整共用一次真实浏览器运行，console/page error 和 failed request 均为 0；详细请求和动作见 `member-browser.json`，最终运行及清理结果见 `member-runtime.json`。首次运行因 Playwright 点击 Element Plus 单选 input 被圆点拦截而超时，未发送该次积分写入；原始失败保存在 `member-browser-first-attempt.json`、`member-runtime-first-attempt.json`，修正定位后在新隔离环境复跑通过。
- 范围限制：本轮没有会员 UI 逐页验收。用户表继承 `TenantBaseDO`，标签、分组、等级继承 `BaseDO` 且迁移表均含 `tenant_id`；Core SQL 拦截器对这些已注册实体同样应用当前租户条件。后续 2026-11-23 独立双租户 API/SQL 证据已关闭三类维度的限定租户隔离子项。ERP 其它业务、会员其它流程和 P2 总体验收继续开放。

### P2 Member App 当前 JAR 复验（2026-11-22）

- **状态：限定子项通过，P2 总项继续进行中。** 使用当前 Demo JAR SHA-256 `963149b3978618f370df9f63fe1db1a2841b7c3b2298d80766086cae27da5c97`，在一次性 schema `yuheng_p2_member_20261117` 冷装 59 个 changeset，复验后台与 App 的真实登录、会员租户边界、权限拒绝、积分事务回滚、地址归属和签到规则生命周期。
- **运行范围：** 真实 HTTP/API 验证了匿名 401、无角色 403、伪造租户头拒绝、会员密码登录、地址超长姓名 400 且不写入、地址增改查删及跨会员不可见、会员积分故障注入回滚后正常加分、标签/分组/等级引用保护和软删除、签到配置重复日期拒绝及增改删。桌面浏览器完成标签 CRUD、会员筛选和扣积分，以及分组、等级、积分、签到和会员参数页面读取；浏览器错误和失败请求均为 0。
- **证据与清理：** 结果见 `docs/verification/2026-11-11-full-source-migration/p2-member-platform-20261117/member-runtime.json` 和 `member-browser.json`，入口为 `scripts/verification/p2_member_platform_probe.py`。隔离 MySQL/Redis、应用和 UI 已停止删除，13373、16453、48220、5203 均无监听；凭据未写入证据，历史系统用户密码未修改。
- **继续开放：** 本轮仍不覆盖真实社交/微信授权回调、Pay/Mall 开启后的真实联调、ERP 更细数据权限组合和 P2 总体验收；ERP 属于桌面管理后台，不扩展手机视口验收。

## P1 制品一致性修正与最终复验（2026-11-18）

- **总状态：P1 继续进行中；本地 tarball 平台闭环通过。** 当前 registry 固定版本安装和 Demo UI 独立锁文件仍未完成，未获豁免，不能标记整个 P1 完成。版本/授权沿用本计划；REQ/AC 和 T1/T3/T4 沿用原全量迁移计划。
- `PHASE_GATE`：workId `YH-20261111-full-source-migration`；stage `verification`；规格及计划按用户已确认完整实施和“那继续”的授权执行；原型 `NOT_REQUIRED`（既有页面验收及发布包一致性修正）；Only Modify 为 Core 跟踪 tarball、发布一致性测试、Demo 构建/验证脚本与证据；不修改业务契约、数据库迁移、共享库/Redis/服务或用户历史密码。范围内 implementationAllowed `true`；本地制品验收 `PASS`，registry/锁文件交付出口 `BLOCKED`。
- 根因：原跟踪包 `125b85…` 与 Core `836125c` 源码不一致，缺少 Menu、ConfigForm、RoleForm 三处已提交修复。用旧包构建后，390/320px 鼠标场景的“新增”被系统菜单 popper 拦截，未产生角色写请求。临时尝试清空折叠态默认展开项没有形成有效修复，源码修改已撤回。中途“纯输入模拟问题”的推断也撤销，最终包同时通过原鼠标与新增触摸场景。
- Core Vite build、`vue-tsc -p tsconfig.build.json` 通过，重打包 SHA-256 `7d5adb2d1a27e0c68956ed64646dd1850adb733fb0e3b5467ff6adff0d9dcebc`。发布回归 `tests/release/package-content.test.ts` 对旧包明确报告上述三个不同文件，对新包逐文件比对及 manifest 契约通过；不新增运行时行为修复。默认 `vue-tsc --noEmit` 仍报告 compat 类型配置问题，未计为通过。
- Demo 从根目录使用相对 `YUHENG_UI_PACKAGE` 执行 `./scripts/build.sh` 退出 0，临时消费者离线安装、类型检查、Vite 3544 模块构建及 Maven 打包通过，JAR `9a7b8fa44a02a2d42da0da98b518018a7c1c2f2e5e83d15711bd5afac156dcbd` 内有 612 项静态资源。独立消费者测试先因临时 file: manifest 触发固定版本契约断言；装包后恢复原始 manifest 再直接执行测试通过，不将此过程称为 registry 固定坐标安装。
- 同一最终 JAR：角色页 1440×900、390×844、320×844 鼠标场景与 390×844、320×844 触摸场景均命中“新增”，弹窗可填写/取消，无角色写入；桌面折叠悬停及展开活动项正常，console/page/request 错误为 0。证据 `role-page-collapse-desktop-20261117/result.json`。这是管理后台响应式验证，不是独立 uni-app 验收。
- 同一最终 JAR：平台探针首次/重启均为 56 changesets，21 个种子用户密码字段前后相等；System/Infra CRUD/授权回读、无权 403、文件下载、任务查询及启停脚本均通过。两组隔离容器和专用端口清理完成。证据 `p1-fixed-package-20261117/platform-runtime.json` 与 `p1-build-20261118.json`。
- 本轮保留 127 张原历史未跟踪截图；新增触摸场景截图亦保留本地，不批量提交图片。结构化证据只支持上述具体场景，P2/P3 与全量 T1/T3/T4 继续开放。

## P1 配置页最终包复验（2026-11-20）

- 使用与平台、角色页相同的 JAR SHA-256 `9a7b8fa44a02a2d42da0da98b518018a7c1c2f2e5e83d15711bd5afac156dcbd`，runner 启动前确认 JAR 与 `yuheng-demo-ui/dist` 的 612 个静态资源逐项字节一致。
- 隔离浏览器完成配置列表、筛选/重置、新增、详情读取、更新、软删除和取消编辑。所有写 API 返回成功；console/API 错误和失败请求均为 0。探针配置软删除，基线配置行前后 SHA-256 相同；隔离容器和 13353/16433/48188/5300 端口均已清理。证据：`docs/verification/2026-11-11-full-source-migration/config-crud-20261117/runtime.json`、`browser.json`。
- 最新 Demo Python 脚本测试：39 项，32 通过、7 项条件跳过、0 失败；新增 runner 接线测试要求配置 CRUD 验收使用的 JAR 与 dist 静态资源一致。P1 汇总结构化结果见 `p1-fixed-package-20261117/p1-build-20261118.json`。
- 2026-11-21 用户选择 npm 公共 registry 并开启发布 2FA。账号 `huhua8812` 将 Core 跟踪 tarball提交至 npm staged publishing，用户完成最终审批后，固定包在 `https://registry.npmjs.org/` 可查询且 tarball 下载返回 HTTP 200。公开制品 `yuheng-ui@0.1.0-SNAPSHOT` 的 SHA-256 为 `7d5adb2d1a27e0c68956ed64646dd1850adb733fb0e3b5467ff6adff0d9dcebc`，registry SHA-1 为 `90cb14a37b9d3f1af1cd541c04634afaac4d6ead`，SRI 与 Core tarball发布 dry-run 匹配；包含 655 个文件，访问级别 public，dist-tag 为 `snapshot`。
- `yuheng-demo-ui/pnpm-lock.yaml` 已从 registry 独立解析生成，yuheng-ui 锁定为 registry SRI，不包含 workspace 链接或机器路径；Demo UI 目录执行 `pnpm install --frozen-lockfile --lockfile-only --ignore-scripts --registry=https://registry.npmjs.org/` 通过。首次从干净临时消费者安装时 registry tarball 尚未完成分发，返回 404；分发就绪后再次 frozen install 成功，解析到临时消费者 pnpm store，`vue-tsc --noEmit` 通过、Vitest 3 个文件/14 项通过、Vite 3546 模块构建成功（保留既有大 chunk 警告）。此前首次测试因为临时副本未带 `.env` 有 1 项夹具文件缺失；复制 Demo `.env` 到临时目录（未提交）后全量通过。
- P1 固定版本 registry 干净安装和独立锁文件缺口已关闭；平台运行、数据库升级、登录/菜单、系统管理/基础设施、权限边界、生命周期及代表浏览器流程均有同一固定 JAR 的隔离证据。P1 验收清单各限定范围达到通过；全量 T1/T3/T4、P2/P3 和独立 uni-app 迁移仍按更大范围计划继续开放。
- **P1 状态：已完成（限定的平台最小闭环范围）。** 每个清单项目均有固定版本/固定 JAR 的构建、运行或浏览器证据；未把 P1 代表性权限/浏览器覆盖扩展解释为全量 T1/T3/T4、P2/P3 或独立 uni-app 验收完成。

## 2026-11-21 Member 与 ERP 模板数据库验收

- **状态：SQL 冷装及升级契约通过；P2 业务主流程继续进行中。** 使用专用容器 `codex-qc-schema-mysql` 的隔离映射端口 `51045` 和一次性 schema；未连接共享 `yuheng_demo`、本机 `mysql8` 或历史用户数据。验证结束后删除本轮创建的所有 schema。
- Member 模板按 `changelog.yaml` 冷装 14 个 changeset，重复执行后仍为 14；Demo 同步的增量迁移实际执行并移除旧复合索引。验证空手机号/空邮箱重复、同租户活动手机号唯一、逻辑删除后手机号复用及租户隔离。超长邮箱使 preflight changeset HALT，旧索引保留、DDL 未执行、用户行未修改。过程中发现并修复旧索引 precondition 将复合索引列数当作索引数的缺陷；模板和 Demo SQL 内容一致，SHA-256 `1b8f6da037f75dae86f3cc258a90dd2a62a1046c3c72f34e85f099e4dc019f2e`。
- ERP 模板按模块 changelog 冷装 35 个 changeset，建成 33 张表；重复执行后仍为 35，`erp_product.unit_id` 为 bigint。活动库存重复被唯一键拒绝，逻辑删除后允许重建，不同租户可分别保留库存。历史活动库存重复时 changeset precondition HALT，`active_marker` 未创建且 changeset 未记账，原行未被修改。模板与 Demo 的三份 ERP SQL 哈希一致。
- 验证命令结果：模板 `python3 -m unittest tests.test_template_migrations tests.test_template_resources tests.test_schema_contract -v` 47/47 通过；Demo `python3 -m unittest discover -s scripts/tests -p 'test_*.py' -v` 39 项、32 通过/7 条件跳过/0 失败；模板与 Demo 工作区 `git diff --check` 通过。跳过项需外部实例，不据此声称 HTTP 验收。
- 治理技能更新已从 Core 同步到 Demo，`sync-specs-api.py --verify --json` 为 PASS。同步工具额外改写的消费端 manifest 元数据已恢复，保留 Demo 项目身份；Demo 原有 AGENTS、升级草稿和本地截图未清理。
- 当前分支按 Skill 从模板重新初始化 ERP/Member，消费端接入及构建验证记录见 `verification.md`。下一项优先执行 ERP 真实 API/SQL 业务闭环，使用当前 Demo 制品和全新隔离数据库；至少覆盖主单与明细、库存变化、状态流转、权限拒绝和失败回滚。模板/消费端源码对照已在 `verification.md` 记录为一致，不再重复静态比较。

## P1 发布通道与当前 Core 复核（2026-11-20）

- 当前 Core `293abaf98346543613055cac36fbdb296d753d6e` 相对 P1 已验证源码提交 `836125ca005a2e340e443a9fd40f262c9a60bb38` 的 UI 差异仅为 tarball 内容一致性回归测试与同一发布包更新；Core UI 源码无变化。当前跟踪 tarball SHA-256 仍为 `7d5adb2d1a27e0c68956ed64646dd1850adb733fb0e3b5467ff6adff0d9dcebc`，与 Demo JAR 构建/浏览器证据一致。
- 当前 Core UI 全量 Vitest 复核通过：30 个测试文件、126 项；`tests/release/package-content.test.ts` 也通过。`verify_manifest.py release/yuheng-manifest.yaml --json` 与 `verify_bundle.py . --json` 均为 `PASS`。发布 dry-run 只检查包内容，不执行上传。
- Nexus 只读 REST `/service/rest/v1/repositories` 返回 HTTP 200 和空列表；configured `npm-group` 查询固定版本返回 404，`npm whoami` 退出码 1。当前环境未发现已认证身份或 hosted 仓库名称，不能完成 registry 安装和锁文件解析。未尝试注册、创建仓库、修改凭据或发布制品。
- P1 本地 tarball 平台闭环保持通过；固定坐标 registry 干净安装及独立 Demo UI 锁文件仍为明确未完成项，直到 Nexus 管理方提供有效 hosted registry、发布权限及版本可用性。

### P2 Member 管理端权限矩阵（2026-11-22）

- **状态：限定子项通过，P2 总项继续进行中。** 在当前 Demo JAR（SHA-256 `963149b3978618f370df9f63fe1db1a2841b7c3b2298d80766086cae27da5c97`）上使用一次性 schema `yuheng_t4_member_acl_20261123`、59 个 Liquibase changeset 和隔离 MySQL/Redis，执行 67 次真实 HTTP 请求。
- 通过范围包括 Member 用户、标签、分组、等级、会员配置、经验记录、等级记录、积分记录、签到配置和签到记录的查询权限拒绝/授权成功，以及标签、分组、等级、签到配置、会员配置和会员用户的写权限拒绝/授权成功。无权限账号所有受保护入口返回业务码 403；授权账号所有对应入口返回业务码 0。三个 `list-all-simple` 入口按源码既有契约记录为“认证可读”，没有方法级权限注解。
- 每次拒绝请求前后均比较 11 张 Member 表完整 SQL 快照，未发生写入；历史系统用户密码字段保持不变。结果见 `docs/verification/2026-11-11-full-source-migration/member-permission-matrix-20261123/runtime.json`，入口为 `scripts/verification/member_permission_matrix_runner.py`，契约测试为 `scripts/tests/test_member_permission_matrix_probe.py`。凭据、token 和密码哈希未写入证据；13399、16480、48260 端口及隔离容器已清理。
- 本轮没有修改 Core 或业务模板源码，失败均为验证夹具/快照基线问题并在探针中修正。Member 调试短信成功路径已关闭；真实社交/微信授权、Pay/Mall 开启后的真实联调、ERP 更细数据权限和 P2 总体验收仍开放。

### P2 模板更新工具消费端闭环（2026-11-23）

- **状态：更新 Skill 选择性合并子项通过，P2 总项继续进行中。** 使用 Templates `c3049cd3f524b646639681f69478ddc311f880e9` 与 ERP 示例映射，在临时消费者初始化 271 个映射文件并记录基线。只读预览、模板单方更新的选择性应用、消费端独有文件保留、映射外工程文件保留均通过；模板与消费者同时修改同一文件时归类为冲突，应用被拒绝且目标文件不变。消费者未重建，正式 Demo 未触碰。证据 `docs/verification/2026-11-11-full-source-migration/p2-template-update-e2e-20261123.json`。此项验证 Skill 更新工具契约，不表示对正式 Demo 更新模板。
- **业务数据边界：** 更正此前关于 Member 标签、分组、等级为共享维度表的静态推断。Core `TenantDatabaseInterceptor` 会按已注册实体在 `BaseDO` 上继续应用租户条件；模板表有 `tenant_id`，插入也由拦截器写当前租户。两租户隔离验证确认这些维度按租户隔离。ERP 模板没有部门/仅本人归属字段及规则，该项继续开放为模板能力边界。
- **Member 标签/分组/等级租户隔离：通过限定范围。** 当前 Demo JAR、59 changesets、隔离租户 1 与通过 Core 租户 API 创建的租户 162；35 个真实 HTTP 请求确认三类资源均各租户创建/读取成功、对方分页/详情/精简列表不可见、伪造租户头 403 且业务表快照不变。成功证据 `p2-member-dimensions-20261123/member-dimensions-final-runtime.json`。初次探针的租户缺失失败及第二次错误的共享可见性断言均保留在相应 `*-runtime.json`，不计成功证据；新探针修正依据是 Core 源码与 Liquibase 真实行为。
- **下一批 P2 待办（2026-11-23 更新）：** Member 配置、地址、等级、资料、手机号改绑、密码修改/重置及其负向边界已由 `member-lifecycle-final10-20261123/runtime.json` 收口。ERP 当前固定 JAR 的销售、采购、盘点与调拨、采购/销售退货退款桌面闭环均有隔离证据；库存全生命周期、审核/反审核、库存不足多明细回滚及并发竞争也已在当前固定 JAR 复验（`erp-stock-lifecycle-current-20261123/runtime.json`）。继续逐项对照证据补其他尚缺主流程和失败事务，不重复覆盖已验证项。ERP 部门/本人级数据范围仍需模板级规格与字段设计。真实社交/微信成功回调、支付渠道和其它外部服务需要有效第三方凭据，继续标记为外部条件未满足，不伪造成功路径。
- **P2 ERP 采购订单、入库与退货桌面闭环（2026-11-23）：限定子项通过。** 使用当前固定 Demo JAR SHA-256 `4e1f11283c811a908d2b534c518524a843a354ac28a968223eb73e1da15bb6b1`，在隔离 schema `yuheng_t4_erp_purchase_browser_20261123` 冷装 59 changesets。1440×900 浏览器创建并审批采购订单，经可入库订单选择器创建并审批采购入库单，再经可退货订单选择器创建并审批采购退货单；六个写 API 均 HTTP 200，page/console errors 和 failed requests 为 0。SQL 确认订单与入库数量 10、采购退货 2，订单明细累计 `in_count=10,return_count=2`，三张单据状态均为 20；库存从 0 增至 10 后因采购退货回落至 8，库存流水为 `70:+10`、`80:-2`。JAR/dist 612 项静态资源逐字节一致、系统种子密码未变、证据无凭据，MySQL/Redis/应用及 13433/16488/48275 均清理。机器证据 `erp-purchase-browser-20261123/runtime.json`、`browser.json`，runner/probe 与契约测试分别为 `scripts/verification/erp_purchase_browser_runner.py`、`erp_purchase_browser_probe.js`、`scripts/tests/test_erp_purchase_browser_probe.py`。初次夹具失败是仓库名超过 `varchar(20)`；第二次浏览器失败来自本地静态代理并发请求 reset，之后直接由同一隔离 JAR 提供静态资源和 API，通过验证。中间失败均未连接共享服务；SQL 断言首次把采购退货流水类型写成错误的 50，经查模板枚举确认为 80 后以全新隔离环境复跑通过。无产品源码缺陷或 Core/Templates 产品修复；本项仅增加 Demo 验收脚本、测试和证据。
- **P2 ERP 盘点与调拨桌面闭环（2026-11-23）：限定子项通过。** 当前固定 Demo JAR 在隔离 schema `yuheng_t4_erp_stock_browser_20261123` 冷装 59 changesets。1440×900 浏览器从真实库存盘点页选择仓 A 和产品，系统读取账面 5，录入实际 7 并审批；随后从真实库存调拨页选择仓 A、仓 B 和同一产品，调拨 3 件并审批。四个写 API 均 HTTP 200，浏览器错误、Console error 和 failed request 为 0。SQL 确认盘点单状态 20、明细 `stock_count=5,actual_count=7,count=2`；调拨单状态 20、明细关联两仓及产品；最终库存仓 A=4、仓 B=3，流水新增盘盈类型 40:+2、调出类型 32:-3、调入类型 30:+3。JAR/dist 612 项字节一致、种子密码未变，隔离 MySQL/Redis/应用与 13434/16489/48276 已清理。证据 `erp-stock-browser-20261123/runtime.json`、`browser.json`；runner/probe 和契约测试为 `scripts/verification/erp_stock_browser_runner.py`、`erp_stock_browser_probe.js`、`scripts/tests/test_erp_stock_browser_probe.py`。此前探针失败均发生在写入前或最终断言：初始行数与仓库库存读取流程未按 UI 初始化顺序执行；Element Plus 多仓选择器弹层在浏览器里会有遮挡/过渡，已按页面实际交互和提交前值断言处理；最终 SQL 首轮预期的盘盈流水类型 90 与模板枚举不符，真实类型为 40。全新隔离环境完整复跑通过，无产品源码缺陷或 Core/Templates 修复，本项只增加 Demo 验收探针、测试与证据。
- **P2 ERP 采购/销售退货退款桌面闭环（2026-11-23）：限定子项通过。** 固定 JAR `4e1f11283c811a908d2b534c518524a843a354ac28a968223eb73e1da15bb6b1` 在隔离环境冷装 59 changesets；1440×900 浏览器真实创建并审批采购订单→入库→退货、销售订单→出库→退货，再从财务页面选择退货单创建并审批 `-3` 采购付款和 `-2` 销售收款。API 全部成功，浏览器错误/失败请求为 0；SQL 确认退货累计退款分别为 3/2，财务主单金额及来源明细均与负数退款一致，种子密码不变、JAR/dist 612 资源字节一致，隔离容器和端口清理成功。证据 `erp-refund-browser-20261123/runtime.json`、`refund-browser.json`；runner `scripts/verification/erp_refund_browser_runner.py`。探针夹具名称、负数输入及金额符号断言按实际页面/SQL 校准后通过；静态 server 请求队列沿用现有 runner 设置为 128。未发现 Core/Templates 产品缺陷。
- **P2 ERP 库存生命周期、失败事务及并发（2026-11-23）：当前固定 JAR 限定子项通过。** 对 JAR SHA-256 `4e1f11283c811a908d2b534c518524a843a354ac28a968223eb73e1da15bb6b1` 在一次性 schema `yuheng_t4_stock_lifecycle_20261123_current` 冷装 59 个 changeset。真实 API 覆盖入库、出库、两仓调拨、正/负盘点的审批、反审批和再次审批；多明细出库第二行库存不足时，单据保持未审核、此前明细没有扣库存、库存流水数不变。两个竞争出库同时审核时恰有一个成功、另一个按库存不足拒绝；最终仓库库存与流水数量一致。历史系统种子密码字段前后相同，隔离 MySQL/Redis、应用及 13435/16490/48277 均已清理。结果 `erp-stock-lifecycle-current-20261123/runtime.json`、`stock-lifecycle.json`；入口 `scripts/verification/erp_stock_lifecycle_current_runner.py`，共享业务探针 `erp_stock_lifecycle_probe.py`。运行期间核实旧错误是期望遗漏保留为 0 的库存行，不是产品行为问题；本轮复跑没有发现需修复 Core/Templates/Demo 产品源码的问题。ERP 管理后台只验收桌面场景。
- **P2 Member 生命周期补充（2026-11-23）：限定子项通过。** 当前固定 Demo JAR `4e1f11283c811a908d2b534c518524a843a354ac28a968223eb73e1da15bb6b1` 在隔离 schema `yuheng_p2_member_lifecycle_20261123h` 冷装 59 个 changeset。真实 API/SQL 验证会员配置首次保存、再次保存原行更新且仅一条有效记录；App 两地址新增默认切换、更新默认切换、`get-default` 跟随及删除默认地址后没有默认地址、另一条地址保留；后台赋予/取消等级后 `member_user`、`member_level_record`、`member_experience_record` 同步，取消等级按模板契约使用 `level_id=0, experience=0`，随后等级逻辑删除；会员资料更新、短信验证改绑手机号、手机号新旧登录边界，以及短信验证修改密码、新旧密码登录边界。系统种子密码未变，专用容器和 13412/16493/48273 已清理。机器证据 `docs/verification/2026-11-11-full-source-migration/member-lifecycle-final7-20261123/runtime.json`，运行器/探针为 `scripts/verification/member_lifecycle_runner.py`、`scripts/verification/member_lifecycle_probe.py`。模板与 Demo 源码实现一致，本轮未发现产品缺陷、未修改 Core/Templates/Demo 业务产品源码。初次失败分别来自地址姓名超长、探针枚举值和等级哨兵断言、MySQL 客户端中文输出编码，以及同手机号一分钟短信限流；修正探针并按限流契约改用独立会员账号后，在全新隔离 schema 复跑通过。失败机器记录保留，不计产品失败。运行器只把后端日志写入系统临时目录并在退出时删除，证据目录不留启动日志。
- **P2 Member 忘记密码重置 API 补验（2026-11-23）：限定子项通过。** 在新的隔离 schema `yuheng_p2_member_lifecycle_20261123j` 使用同一固定 JAR 冷装 59 个 changeset，复验手机号/密码登录与短信校验后的匿名 `reset-password`：未注册手机号请求返回 `1004001001` 且不新增验证码；错误验证码返回 `1002014000` 且会员密码哈希不变；正确场景验证码仅在进程内使用并被消费，重置后新密码登录成功。证据写入 `member-lifecycle-final9-20261123/runtime.json`，专用容器和 13414/16495/48276 已清理；证据不含验证码、密码或 token。该入口当前仅完成 API/SQL 验证，Demo UI 没有发现会员忘记密码页面/调用，不将此结果说成 UI 闭环。因 Core 按手机号对所有短信场景执行 1 分钟频率限制，改用第三个隔离会员账号，未降低或绕过限流。无 Core/Templates/Demo 产品源码修复。
- **P2 Member 手机号改绑负向边界补验（2026-11-23）：限定子项通过。** 新 schema `yuheng_p2_member_lifecycle_20261123k` 以固定 JAR 冷装 59 changesets；占用手机号请求修改手机号验证码返回 `1004003007` 且验证码表不增行；可用手机号发码后使用错误码改绑返回 `1002014000`，会员手机号不变且验证码未消费，随后有效验证码完成改绑。证据 `member-lifecycle-final10-20261123/runtime.json`；13415/16496/48277 和容器已清理。无产品源码修改。
- **P2 明确排除及后续跟踪：** 真实社交/微信成功授权及回调、真实短信/支付渠道与其它外部服务需要外部凭据/环境；Trade/Promotion/Product 尚无可接入的完整后端模板；ERP 部门/仅本人数据权限需先由业务模板定义字段和规则。这些不属于当前已接入业务的代表性 P2 验收，不阻止 P2 范围收口，后续按外部集成、模块接入或规格设计单独立项。ERP 管理后台只按桌面场景验收。

- **P2 ERP 采购/销售退货删除生命周期（2026-11-23）：限定子项通过。** 当前固定 Demo JAR `4e1f11283c811a908d2b534c518524a843a354ac28a968223eb73e1da15bb6b1` 在专用隔离环境冷装 59 个 changeset。1440×900 浏览器分别完成采购订单→入库→采购退货和销售订单→出库→销售退货；随后真实 API 验证已审核退货直接删除分别返回业务拒绝码 `1030103001`、`1020203001`，拒绝前后单据、来源单累计退货数、库存和流水快照不变。反审批后删除成功，退货主单及明细逻辑删除，来源单 `return_count` 归零；采购库存回到 20，销售库存回到出库后基线 7，库存流水分别仅新增一次冲销记录。种子密码未变、JAR/dist 静态资源一致、专用容器和端口清理通过。机器证据 `erp-return-delete-current-20261123/runtime.json`；入口 `scripts/verification/erp_return_delete_current_runner.py`、`erp_return_delete_lifecycle.py`，契约测试 `scripts/tests/test_erp_purchase_browser_probe.py`。中间两次 SQL 期望分别错误地使用采购初始库存 10 和销售退货前库存 10；依实际入库/出库/退货顺序追踪流水后修正为 20 与 7，并在全新 schema 完整复跑通过。仅修正 Demo 验收脚本/测试和记录，没有发现需修复 Core 或 Templates 的产品缺陷。
- **P2 ERP 当前版本退货/退款事务（2026-11-23）：限定 API/SQL 子项通过。** 固定 Demo JAR SHA-256 `4e1f11283c811a908d2b534c518524a843a354ac28a968223eb73e1da15bb6b1` 在隔离 schema `yuheng_t4_returns_20261123_current` 冷装 59 个 changeset。复用真实 API 探针验证采购/销售双明细退货金额及小数舍入、第二条超量导致整笔请求回滚、审核/反审核/再审核库存对称、审核后禁止修改/删除、来源退货额度占用；退款收款/付款负向金额联动回写退货退款额，超额退款和反审核失败时完整 SQL 快照不变，财务反审核/删除与退货反审核/删除后额度和库存正确释放。最终库存为两个产品各 `7.000000`、`6.000000`，库存流水 20 行，活动退货/退款单为 0，历史种子密码不变。机器证据 `erp-returns-current-20261123/runtime.json`、`returns.json`；runner `scripts/verification/erp_returns_current_runner.py`，复用探针 `erp_returns_probe.py`。首次 runner 失败是种子密码快照误包含刚插入的临时测试用户；修正为仅比较 ID `<900000` 的既有系统用户后，在全新隔离环境完整通过。专用 MySQL/Redis、应用及 13438/16493/48280 均已清理。该探针只覆盖 API/SQL，不代表退货退款桌面页面已验收；没有发现需修复 Core/Templates 产品源码的缺陷。
- **P2 ERP 当前版本财务编辑与明细归属（2026-11-23）：限定 API/SQL 子项通过。** 当前固定 JAR 在两个顺序隔离 schema 分别通过付款/收款编辑及退款来源切换探针（66 个请求、16 项来源金额断言），以及明细归属负例探针（40 个请求）。编辑范围覆盖金额调整、跨来源替换、超额编辑原子回滚、删除旧项后新增、采购/销售入库出库与退货类型切换；归属负例覆盖外单、不存在、重复、新增自带明细 ID 与 tenant 999 明细 ID，拒绝前后 SQL 快照不变，合法编辑仍成功。两个 schema 均冷装 59 changesets，系统种子密码不变；专用 MySQL/Redis、应用及 13439/16494/48281 已清理。证据 `erp-finance-current-20261123/runtime.json`、`finance-edit.json`、`finance-owner.json`；runner `scripts/verification/erp_finance_current_runner.py`、契约测试 `scripts/tests/test_erp_finance_current_runner.py`。此前完整复验基于 JAR `9596b4d`，本次补齐 `4e1f112` 当前版本证据。无 Core/Templates 产品缺陷或源码修改；该项为 API/SQL 验收，不代表财务编辑 UI 已验收。

### P2 Member 同日并发签到幂等（2026-11-23）

- **状态：同会员同日并发子项通过，P2 总项继续进行中。** 源码追踪确认原实现先读取最近签到再写入，签到记录没有用户/日期唯一约束；并发请求可能同时读到“未签到”。Templates 在 `MemberUserMapper` 增加会员主行 `FOR UPDATE` 查询，并在签到事务中先锁会员行，再检查最近签到。锁持有到签到、积分、经验与等级写入事务完成；第二个请求读取到已提交的当日记录并按既有业务码拒绝。无需修改已执行 changeset。模板测试先红后绿，修复提交为 Templates `3ea638f`；随后通过模板更新工具只选择性同步两个 Java 文件到 Demo，Demo 专有文件保持不变。
- **隔离验收：** Demo JAR SHA-256 `4e1f11283c811a908d2b534c518524a843a354ac28a968223eb73e1da15bb6b1`，59 个 changeset。两个同步起跑的真实 App API 请求结果为一个成功、一个重复签到拒绝；SQL 确认仅一条新签到、积分流水和经验流水各一条，会员状态只增加 4 积分和 3 经验。此前签到事务故障回滚、普通串行重复拒绝、会员边界与桌面代表页面也在同一隔离运行复核通过，种子用户密码未变。证据 `p2-member-signin-concurrency-pass-20261123/member-runtime.json`、`member-browser.json`；隔离 MySQL、Redis、应用/UI 和 13373/16453/48220/5203 均清理。
- **验证失败记录：** `p2-member-signin-concurrency-20261123/`、`p2-member-signin-concurrency-final-20261123/`、`p2-member-signin-concurrency-verified-20261123/` 与 `p2-member-signin-concurrency-diagnostic-20261123/` 均记录两个真实并发 API 响应为一次成功、一次重复拒绝；运行随后分别在 MySQL/应用日期筛选或重复签到日规则的奖励金额断言处停止。前几次没有对每个失败分支单独重跑；diagnostic 运行记录的成功响应、签到行、积分/经验流水和会员余额证明这两类失败来自探针夹具断言。最终 `p2-member-signin-concurrency-pass-20261123/` 复用唯一规则并通过全部并发、奖励、桌面和清理断言；失败目录不作为产品失败结论。
- **本轮源码影响：** Core 无需修改；模板锁修复位于 Member 模板，Demo 通过 Skill 更新工具选择性应用。真实社交/微信成功回调、真实支付渠道、ERP 部门或本人级数据范围，以及 P2 总体验收仍开放。

### P2 Member 签到规则桌面 CRUD（2026-11-23）

- **状态：限定桌面子项通过，P2 总项继续进行中。** 在当前 Demo JAR SHA-256 `4e1f11283c811a908d2b534c518524a843a354ac28a968223eb73e1da15bb6b1` 和 59 个 changeset 的一次性 MySQL/Redis 环境中，通过 1440×900 浏览器在真实路由 `/member/signin/config` 完成签到规则新增、编辑奖励积分 23→24、删除；编辑请求体为 24、接口成功，列表刷新显示 24，SQL 确认删除记录为软删除。Console/page errors 和失败请求为 0。
- 本轮扩展 `p2_member_browser_probe.js` 与 `p2_member_platform_probe.py`，使完整 P2 Member 运行同时要求签到规则桌面 CRUD，并以 UI 创建的 ID 回查 SQL。最终机器结果见 `p2-member-signin-ui-crud-final2-20261123/member-runtime.json`、`member-browser.json`。冷装 59 changesets，签到奖励事务失败回滚、重复拒绝、跨会员记录隔离、并发一次成功/一次重复拒绝、种子密码不变等原有断言均通过；隔离容器、应用/UI 进程以及 13373/16453/48220/5203 均清理。
- 失败运行保留在 `p2-member-signin-ui-crud-20261123/`、`p2-member-signin-ui-crud-pass-20261123/`、`p2-member-signin-ui-crud-verified-20261123/`、`p2-member-signin-ui-crud-pass2-20261123/` 和 `p2-member-signin-ui-crud-diagnostic-20261123/`。根因分别是错误测试路由、旧积分输入框变量误改、未等列表刷新、刷新响应监听注册过晚，以及点击编辑后未等待详情加载导致探针提交旧值；最终轮加入真实路由、详情加载、输入值和请求体断言后通过。这些为探针问题，不构成产品缺陷证据。
- **本轮源码影响：** 只修改 Demo 验收脚本和测试，没有修改 Core、Templates 或 Demo 业务产品代码。真实第三方授权/支付、缺少的商城后端模块、ERP 部门或本人数据权限及 P2 总验收继续开放。

### P1 固定 npm UI 包消费复验（2026-11-23）

- **状态：固定版本 registry UI-only 消费验证通过；P1/P2 总状态不受本子项单独改变。** 从 npm 公共 registry 获取 Demo 已锁定的 `yuheng-ui@0.1.0-SNAPSHOT`，临时消费者 `pnpm install --frozen-lockfile --ignore-scripts` 通过，508 个依赖解析与锁文件一致；实际包解析到临时消费者 `.pnpm/yuheng-ui@0.1.0-SNAPSHOT`，其 integrity 为 `sha512-zYstszt9JvGc7CHWLkV/dgxq8WcQWRYSDXbhVze5RLXy2notLDhlicUjhHo5FPh/aY37wF94lleBhdRVH74icA==`。`npm whoami` 返回 401，只表示该环境没有 npm 发布身份；匿名安装固定公共包不需要 whoami 身份。
- 隔离消费者 `vue-tsc --noEmit` 通过、Vitest 4 文件/20 项通过、平台导入边界检查 PASS、Vite 生产构建 3548 模块通过；Vite 开发服务器也从已安装 registry 包成功启动。构建保留既有大 chunk 警告。安装时 pnpm 因构建脚本审批策略需加入 `--ignore-scripts`；lockfile 已冻结，相关可执行检查均实测通过。临时目录为 `/tmp/yuheng-demo-ui-registry-J9isPf`，未改 Demo manifest/lockfile/node_modules，没有发布制品。
- 本子项验证 UI 包安装、开发态解析、类型、测试、边界与生产构建；不代表后端 JAR 或浏览器业务联调。本轮尝试用 registry 副本接隔离浏览器时，首轮临时符号链接形成自循环，已定位并修正，Vite 配置加载及生产构建复验通过；为保持 UI-only 范围未重跑既有销售业务闭环。实际 ERP 桌面销售订单→出库→退货浏览器/API/SQL 闭环使用当前 Demo JAR 的证据仍见 `erp-sales-browser-20261123/`。

### P2 Pay/PMS 显式消费验证（2026-11-22）

- `PHASE_GATE`：沿用 workId `YH-20261111-full-source-migration`，code `0.1.0-SNAPSHOT`、governance `0.2.0`、knowledge `0.1.0`；规格/计划 `FROZEN`，用户授权“按计划完成P2验证及功能修复”，并要求修复提交 Core/Templates。原型 `NOT_REQUIRED`（复用模板既有页面和接口）；implementationAllowed `true`。
- REQ-P2-CONSUME：Skill 显式初始化 Pay/PMS 到隔离消费工程；正式 Demo 保留全部定制且不预置这两个模块。映射涵盖后端、前端 API/页面和独立 Liquibase。
- AC/T-P2-CONSUME-1：使用映射工具先预览再应用，记录来源提交、消费差异和基线；模板更新不得重建或清空消费工程。
- AC/T-P2-CONSUME-2：离线后端编译/测试/打包，前端类型检查/构建，明确所用 Core 包及版本，不使用 Templates 运行时依赖。
- AC/T-P2-CONSUME-3：独立 MySQL/Redis/端口，Liquibase 冷装/重启，真实 Pay 应用/钱包代表流程、PMS 项目/知识库/分享流程及匿名/无权/有权拒绝，SQL 对照。
- AC/T-P2-CONSUME-4：桌面代表页及公开分享接线，记录错误和清理；外部渠道和真实第三方回调无凭据时明确未执行。
- **桌面公开分享限定闭环通过：** 隔离消费者明确将 `/pms/kb/document/share/:token` 注册为顶层路由，使用本地 Core 包，生产构建及 Vite 开发模式分别在 1440×900 浏览器以同轮隔离后端生成的真实分享令牌显示文档内容，浏览器错误和失败请求均为零；107 个 changeset 首次和重启一致，专用容器及 UI 端口已停止。此前将路由挂在 Home 下产生匿名刷新令牌错误，改为 Skill 要求的顶层路由后消失；此前 502 为验证环境时序错误。开发模式首次因 `qs` CommonJS 未预构建而空白，消费端 Vite 显式设置 `optimizeDeps.include: ['yuheng-ui > qs']` 后复验通过，Templates `c3049cd` 补充接入说明；第三方 sourcemap 警告仍存在。此项不覆盖其他 Pay/PMS 页面、完整权限及真实渠道。
- **最新进展：部分通过，P2 仍进行中。** Templates `8d727bf` 增加 Pay/PMS 消费映射与 Pay 可选转账回调的前向 changeset，`04d0544` 补充 PMS 共享 UI 资产契约；`05530e5` 修正 Pay 数值字典、PMS 生命周期导入和 Member 售后字典类型，补齐 PMS 直接依赖说明，全量测试 99 项通过。映射初始化的隔离消费者 JAR SHA-256 `15993a3d1986380abc84a9c07e7c0a0e8a0e6f1831e831605d1a99531571e8a5` 完成 Pay 应用、钱包余额、PMS 项目、知识库文档及匿名分享代表请求，107 个 changeset 首次和重启一致；匿名 Pay 请求 401、无权限 PMS 查询 403，拒绝前后业务表快照一致。证据 `p2-pay-pms-consumer-20261122/runtime.json`；该探针没有覆盖完整普通角色权限、租户边界、桌面浏览器或真实支付渠道。Core `067f48e` 修复严格消费兼容类型并保留树工具原有空树行为，UI 打包和 130 项测试通过；本地 tarball SHA-256 `e517810021a1567784935a76ff196356431259aa7f6a2cafd19b07793d7397d2` 未发布 npm。独立安装的隔离消费者使用该包和 Pay/PMS 模板，补齐直接依赖、修正旧请求类型转发并更新 Member 字典类型后，完整 `vue-tsc --noEmit` 与 Vite 生产构建通过，保留大 chunk 警告；此结果不是桌面浏览器或线上 npm 版本的验收。
- **后续租户及授权复验：限定范围通过。** 固定 JAR `15993a3d1986380abc84a9c07e7c0a0e8a0e6f1831e831605d1a99531571e8a5` 在新建独立 MySQL/Redis 中首次及重启执行 107 个 changeset。两个真实租户分别创建 Pay 应用、PMS 项目和知识库，SQL 确认各行 `tenant_id` 与登录租户一致；本租户可读、对方租户不可读，PMS 跨租户更新被拒绝且业务表快照不变。普通角色未授权写入及伪造租户头被拒绝，快照不变；容器已清理。结果见 `p2-pay-pms-tenant-20261122/runtime.json`。本次补充替代上一段关于租户边界尚未覆盖的旧状态，仍不代表完整授权矩阵或真实支付渠道通过。
- Only Modify：Templates 映射/必要源码修复/测试/说明，Core 必要平台修复/测试，Demo 验证脚本和证据；Do Not Modify：正式 Demo 业务定制、已执行 changeset、共享数据库/Redis、历史密码。回滚仅本轮文件和精确临时资源。
