# 对抗性架构审查

- **审查对象：** `docs/architecture/01-requirements-spec.md`、`02-module-decomposition.md`、`03-system-architecture.md`、`04-detailed-design.md`、`05-graph-schema-design.md`、`08-mvp-milestones.md` 及 `docs/api/01-interface-contract.md`
- **审查立场：** 不把设计草案中的目标、伪代码或验收条款当作已实现能力；以下结论只基于仓库内可复核材料。该审查是设计草案阶段的独立审查快照。
- **审查结论计数：** 3 个致命问题，13 个重要问题。未发现密钥或凭据。
- **证据状态：** 设计文件大多标为 draft；`src/ludograph/`、`tests/` 目前只有 README/占位文件，实际实现与测试结果均为**未验证**。

## 1. 执行摘要

设计草案已经把若干风险写进了文档，但没有把最危险的风险真正封闭：**系统仍可能把“有连续引用的模型猜测”编译成一个求解器可以正确求解、但并不代表原文的模型**。同时，README 仍对外宣称“端侧微调 SLM”“高并发、毫秒级响应”“出厂即正确”，而 MVP 规格明确不做 SLM 微调、不承诺高并发写入 SLA，且研究证据只支持缓存/模板快路径的毫秒级假设。设计文档中的分层验证和异步方向是合理的工程假设，但缺少可执行的 CEGAR 闭环、精确的 `proved` 语义、字段级证据合同、资源隔离和真实门禁，因此不能支撑 README 的产品级表述。

**最危险的组合不是某个数据库或 Z3 API 选错，而是：** 端到端范围过大 + 语义证据未闭环 + README 仍然过度承诺。建议先砍掉动态 NL2Cypher、双物理投影、三类验证全覆盖和三类版本兼容性报告中的大部分内容，先做一个有 gold set、可回放、只针对一个后端和一个验证性质的垂直切片。

## 2. 致命问题

### C-01：证据链只证明“引用连续”，不能证明“引用蕴含断言”

- **问题：** `quote == chunk[start:end]` 被当作硬门槛，但它只证明字符边界，不能证明 quote 支持 claim 的主体、方向、条件、数量、否定和时序。设计承认这个鸿沟，却仍把通过 validator 的 claim 送入 Assertion，再送入 Rule IR；没有强制的字段级证据、人工裁决状态或蕴含失败后的不可编译状态。
- **证据：** `docs/architecture/04-detailed-design.md` §2.4 只规定连续性检查并说蕴含可能需要人工/NLI；`docs/architecture/01-requirements-spec.md` §1.2、R-b 也承认证据蕴含不能完全自动化。相反，`docs/research/02-neurosymbolic-extraction.md` §2.4、§4.1 要求 subject、predicate、object、quantity、condition 各自有支持片段；`docs/research/literature-review-ludograph.md` §4.4 明确指出连续且相关的 quote 仍不等于支持整个 claim。
- **为什么重要：** 这直接击穿“求解器结论可回溯即可信”的核心承诺。错误的 claim 只要引用了一段相关文本，就能获得完整 provenance；Z3 随后可能返回 `proved`，但它证明的是错误编码。
- **建议怎么修：** 在确认图谱与 Rule IR 入口之间增加不可绕过的 `evidence_review` 状态：字段级 span/支持判定、人工或独立审查结果、审查者/版本/理由；未通过蕴含审查只能进入 `uncovered`/`not-modeled`，不得进入 `proved`。将 `provenance_complete` 与 `evidence_entails_claim` 分成两个字段和两个门禁；为否定、条件范围、数量、周期和方向各建对抗 fixture。

### C-02：性能承诺没有可证伪的统一边界，README 与设计规格相互冲突

- **问题：** README 仍把“高并发、毫秒级响应”写成无条件性能目标，并把端侧微调 SLM、Z3 验证放在实时链路中；架构设计虽增加异步分支，却没有给出队列容量、背压、并发模型、取消语义、缓存键和端到端 SLO，也没有任何实测。
- **证据：** `README.md`“性能目标”及架构概要；`docs/architecture/01-requirements-spec.md` §3.2/NFR-P1~P4 明确说只对快路径设待实测目标、不承诺端到端验证；`docs/architecture/03-system-architecture.md` §2.2、§4.1 只说 SMT/冷路径异步，但 §8 仍只有报告字段要求。`docs/research/04-nl2cypher-routing.md` §2.1、§3.4 记录 8B 零样本执行准确率 26.21%/30.99%，并指出 3B 端侧自回归生成通常是百毫秒到秒级；`docs/research/05-formal-verification.md` §4.2 和 `07-formal-verification-methodology.md` §2.6 都反对按约束条数推导毫秒延迟。
- **为什么重要：** “高并发”与“毫秒级”没有定义请求类型、读写比例、数据量、硬件、P95/P99 或租户隔离，无法验收；更严重的是，调用方会把慢任务排进同步请求，造成排队放大和尾延迟崩溃。对外材料还会把未实现目标误读为能力。
- **建议怎么修：** 立即把 README 改成分层、带 `target/unverified` 的口径，并明确 `proved`/`counterexample` 之外的长任务只能异步。先冻结单机、单租户、一个固定后端和固定数据规模的 workload；定义并测量队列等待、路由、编译、DB、求解、回译各段的 P50/P95/P99、吞吐、超时率和资源上限。没有实测前不得保留“工业级高并发”或“毫秒级响应”的无条件句子。

### C-03：MVP 同时交付六个高风险子系统，出口条件无法由当前仓库满足

- **问题：** MVP 同时要求抽取、双投影、查询路由、D1/D2/D3 验证、异步接口、版本 diff、三类兼容性报告、评测集和性能报告；这些不是一个最小垂直切片，而是一组尚未实现的研究项目。设计将“有 fixture 能跑通”当作架构验收，但当前没有实际模块、gold set、后端集成、solver worker 或测试文件。
- **证据：** `docs/architecture/01-requirements-spec.md` §6.1 列出 9 项 in-scope；`docs/architecture/08-mvp-milestones.md` M0–M7 要求每阶段可运行；仓库当前 `src/ludograph/` 与 `tests/` 只有 README/`.gitkeep`（**未验证实现**，本审查未改动这些目录）。`docs/architecture/04-detailed-design.md` 顶部虽写“可实现的 MVP 设计”，但没有实现证据。
- **为什么重要：** 每一个“最小实现”都可能在语义、性能和测试上形成独立失败面；把全部放进 MVP 会诱发 stub/fixture 通过、端到端能力不存在、最后不得不降低门禁的结果。版本兼容性还依赖未定义的运行时模型，不能与基础抽取同时作为 MVP 强承诺。
- **建议怎么修：** 将 MVP 砍为一条可复核链：公开 chunk → 确定性/单模型候选 → 字段级证据审核 → 一个 Assertion 存储后端 → 一个查询模板 → 一个 D1 或 D2 有界性质 → 可回放反例。其余 D 类、动态 NL2Cypher、双投影、三类兼容性和跨模块替换性作为后续里程碑，必须在真实 benchmark 通过后再放入范围。

## 3. 重要问题

### M-01：README 的 SLM/CoT 叙述与调研结论及 MVP 范围不一致

- **问题：** README 把“LLM CoT”和“端侧微调 SLM”写成架构事实；MVP 又明确不做 SLM 微调，且研究建议先做规则/模板基线、积累审核数据后再微调。CoT 也没有消融、unsupported-claim 指标或关闭条件。
- **证据：** `README.md`架构概要；`docs/architecture/01-requirements-spec.md` §6.2 #2；`docs/research/04-nl2cypher-routing.md` §3.1、§4.3；`docs/research/02-neurosymbolic-extraction.md` §2.3、§4.1 明确 CoT 是可选优化而不是抽取合同。
- **为什么重要：** 设计方会按 README 误选技术、误估算延迟，并将未训练 SLM 当成生产路由器；长 CoT 还可能提高 unsupported claim rate。
- **建议怎么修：** README 改为“可替换 proposer/意图路由基线”；CoT 变成实验变量，只有在固定 gold set 上同时提升 recall/F1 且不增加 unsupported claim rate 时才启用。MVP 先采用模板/规则路由与强模型离线基线，不训练 SLM。

### M-02：声明了“分层验证”，但没有 CEGAR 的实际闭环

- **问题：** 设计有 L0/L1/L2/L3 和 over/under/unresolved 名词，却没有抽象反例回放、spurious 反例的谓词精化、终止条件、精化预算或 soundness 记录。`spurious-counterexample` 是结果枚举，不是 CEGAR 算法。
- **证据：** `docs/architecture/02-module-decomposition.md` §6.2、`docs/architecture/04-detailed-design.md` §5.2、§9；`docs/research/07-formal-verification-methodology.md` §2.1、§4.2 明确推荐 CEGAR 和“抽象→回放→精化”。
- **为什么重要：** 没有闭环时，区间过近似的假阳性可能被展示为游戏漏洞，欠近似的“没找到”可能被误读为无风险；多结果协议无法修复错误的抽象方向。
- **建议怎么修：** 先只支持一种可证明方向（例如固定边界下的欠近似反例搜索或有明确包含关系的安全过近似），为每个结果记录抽象关系、回放结果和精化次数。没有证明保持关系的抽象直接返回 `unknown/not-modeled`，不产生 `proved`。

### M-03：`proved` 的生成条件与 MVP 实际能力冲突

- **问题：** 设计允许输出 `proved`，但 MVP 明确只有 L0–L3：图算法、区间抽象和有界 SMT。有限深度 `unsat` 只能是 `bounded-no-counterexample`；区间“未发现越界”只有在明确的保守包含关系下才可能证明某个范围性质。当前没有统一的完备有限状态条件、全局不变量或证明证书合同。
- **证据：** `docs/architecture/04-detailed-design.md` §9 映射规则；§7.2、§8.2 把有界结果限制为 `k`；`docs/research/05-formal-verification.md` §4.1、`07-formal-verification-methodology.md` §2.3、§3 明确 `unknown`/有界 UNSAT 不能当全局安全。
- **为什么重要：** 同一 `proved` 枚举可能被不同后端解释为“某 k 内未发现”或“无界安全”，客户端无法安全消费。
- **建议怎么修：** 把 `proved` 拆为 `proved_under_assumptions`、`proved_finite_complete`、`bounded_no_counterexample`；结果必须携带 proof_scope、approximation、completeness_basis、assumptions 和 checker version。MVP 如无证明证书，删除全局 `proved`，只交付可回放反例/有界无反例/未建模。

### M-04：跨模块错误传播和异步状态仍有不一致

- **问题：** API 文档把任务超时写成 HTTP/任务层 `failed + TIMEOUT`，同时要求验证报告写 `unknown`；部分批次可提交成功 chunk，但没有定义批次快照是否可被验证、失败 chunk 是否阻断版本发布。取消、重试、已排队任务的幂等和结果可见性也没有端到端状态机。
- **证据：** `docs/api/01-interface-contract.md` §2、§6.2、§8；`docs/architecture/03-system-architecture.md` §2.2、§7；`docs/architecture/01-requirements-spec.md` IR-3/IR-5。
- **为什么重要：** 客户端容易把 envelope 的 `failed` 当成没有结果，也可能把部分快照当完整快照进行验证；重试时还可能重复导入或读取过期缓存。
- **建议怎么修：** 为 extraction/import/verify/job/batch 分别定义状态机和原子提交点；规定 timeout 的 envelope status、业务 result.status、可重试条件和快照可见性；批次必须带 completeness bitmap/失败列表，未完整快照禁止声称全局结论。

### M-05：chunk-only 证据合同无法覆盖实际输入形态

- **问题：** 设计背景承认 Excel、流程图、截图、伪代码和口头约定，但接口只接受一个 `chunk_text` 和字符 offset；没有表格单元格、图片/流程节点、跨 chunk 句子、重叠 chunk、Unicode offset、解析失败和原始文档版本的合同。
- **证据：** `docs/api/01-interface-contract.md` §3.1；`docs/architecture/01-requirements-spec.md` DR-1/FR-EX-5；`docs/research/game-design-theory/03-analysis-method.md` §6 记录流程不能处理图文混合、表格和跨文档一致性。
- **为什么重要：** 输入被切断或错误解析时，连续 offset 仍可能合法但指向错误文本；游戏规则最关键的数值常在表格/配置中，MVP 会系统性漏掉或伪造其语义。
- **建议怎么修：** MVP 明确只接受纯文本公开 fixture，其他输入返回 `unsupported_source_format`；为后续 parser 定义稳定 source block、坐标系、表格 cell/图节点证据和重叠 chunk 规则。不要把“支持策划文档”写成比实际输入合同更宽的能力。

### M-06：设计意图、体验主张和规则事实没有一个可执行的合同分叉

- **问题：** 详细设计说意图和体验可以作为外部陈述保留，但 `ExtractionEnvelope` 只有 `nodes/claims/uncovered`，claim 的四态 `certainty` 只表达原文语气，不表达 `rule_fact/design_intent/experience/implementation_fact` 层。验证器没有可机械拒绝“意图冒充规则”的字段。
- **证据：** `docs/architecture/04-detailed-design.md` §2.1；`docs/architecture/05-graph-schema-design.md` §4.2；`docs/research/game-design-theory/03-analysis-method.md` S3–S7 及 P1–P5 明确要求分层；`docs/research/literature-review-ludograph.md` §3.2、§4.4 强调分析层与可编译层分离。
- **为什么重要：** “希望玩家感到压力”“目标是完整体验”可以带数字和陈述句，若只靠 proposer 自律，会成为可验证规则；这会把不可验证设计意图带进 SMT。
- **建议怎么修：** 抽取合同增加不可混淆的 `layer`/`claim_kind`，至少区分 rule fact、design intent、experience、implementation fact；只有 rule fact 且通过证据审查的项可进入 Assertion/Rule IR。其余保留为文档级陈述或 `uncovered`。

### M-07：单一 schema 权威源没有落地，且 24/25 计数问题仍未关闭

- **问题：** 设计要求一个机器可读源生成 JSON Schema、白名单、数据库约束和文档，但未指定源文件路径、生成命令、漂移 CI 或 schema 发布物。关系设计选择 24 项，同时保留“25/24 待决”；需求又要求 MVP 内解决。`docs/architecture/99-design-decisions-and-open-questions.md` 被引用但当前不存在，`docs/adr/` 只有 `.gitkeep`。
- **证据：** `docs/architecture/02-module-decomposition.md` §2.1；`docs/architecture/05-graph-schema-design.md` §1、§9；`docs/architecture/01-requirements-spec.md` R-d、§7；仓库文件检查显示目标 99 文档缺失、ADR 目录无 ADR。
- **为什么重要：** 这不是排版问题：白名单、domain/range 和 DB 约束若各自维护，会造成抽取通过而导入失败，或不同版本产生不同含义。
- **建议怎么修：** 在 M0 明确唯一机器源及生成器，提交生成物 hash/版本，CI 做 round-trip/diff；立即裁决 24 或补出第 25 项（含 domain/range、对称性和 qualifier），删除“待决”状态后才允许 M1。

### M-08：双投影要求把规范存储和读模型的一致性成本塞进 MVP

- **问题：** MVP 要求关系属性和 Assertion 节点两种投影语义一致，同时又说 direct edge 只是可选热点投影。两者的重复断言、冲突、生命周期、证据数组和投影刷新点没有定义成同一个可观测事务；“语义一致”也没有明确查询集合和一致性时间点。
- **证据：** `docs/architecture/01-requirements-spec.md` FR-GX-1/2；`docs/architecture/03-system-architecture.md` §3、§5.1；`docs/architecture/04-detailed-design.md` §3.1–3.3；`docs/research/03-graph-storage.md`“Claim 两种存储模型”明确指出 direct edge 是优化且带一致性/删除重建风险。
- **为什么重要：** 双写会产生 stale hot view；查询可能读到没有审核状态或错误版本的 direct edge，破坏“Assertion 是规范历史”的原则。
- **建议怎么修：** MVP 只保留 Assertion 规范存储；若必须快路径，先做单一只读物化视图并定义 projection revision、刷新/失效和读一致性。把双投影 round-trip 降为后续优化验收，而非基础语义门禁。

### M-09：数据库选型与适配器边界仍是假抽象

- **问题：** 设计说“Neo4j 兼容 LPG/Cypher 的适配器”，但没有锁定 Neo4j 版本/Edition/驱动能力，也没有真实能力矩阵、方言 parser 或替换判定。`src/ludograph/README.md` 没有 `adapters/`，与模块文档所说的适配器布局不一致。
- **证据：** `docs/architecture/03-system-architecture.md` §3；`docs/architecture/02-module-decomposition.md` §1.3、§9.2；`docs/research/03-graph-storage.md` 指出 Neo4j 许可/能力需按版本核验，Kùzu 原项目已 archived，LadybugDB 也不能直接继承旧基准。
- **为什么重要：** “兼容 Cypher”不等于支持关系属性、约束、路径、JSON、事务和 provenance 查询；后端能力不足会在运行时才暴露，破坏路由拒绝和性能目标。
- **建议怎么修：** MVP 明确一个实际后端、版本、Edition 和部署模式，提交能力矩阵和可运行 PoC；其他后端只保留 IR 设计，不宣称可替换。把许可与容量 PoC 作为 M3 的硬阻断，不用“adapter”三个字替代证据。

### M-10：工业化安全/运维边界被主动排除，却没有防止误部署

- **问题：** 架构明确 MVP 不做多租户安全边界、跨区域 HA 和容量承诺，但 API 有 HTTPS/权限/审计的外观，且 README 使用“工业级”定位；没有认证主体到 scope 的授权映射、租户隔离、备份恢复、来源文本保留/删除、审计不可抵赖或队列资源隔离。
- **证据：** `docs/architecture/03-system-architecture.md` §4.1；`docs/api/01-interface-contract.md`开头及 §8；`docs/architecture/01-requirements-spec.md` NFR-S2、NFR-S3、NFR-S4；`docs/research/03-graph-storage.md`风险项指出权限、备份恢复、证据保留期尚未定义。
- **为什么重要：** 单租户本地 PoC 可以不做这些，但若被部署为共享服务，`game_id/system_id` 不是安全边界，跨游戏读写和敏感策划文档泄漏是架构级事故，不是后续小修。
- **建议怎么修：** 在所有入口加“仅本地/单租户开发基线，禁止生产部署”的硬标记；MVP 至少定义认证、授权检查点、scope 与主体绑定和无权限测试。把备份、恢复、删除、保留期和队列资源隔离列为生产前阻断条件，而不是未来扩展。

### M-11：版本兼容性三类性质只有名字，没有判定语义

- **问题：** `resource_value`、`goal_reachability`、`save_continuity` 被列为独立报告，但没有定义资源价值的度量、目标集合、玩家状态映射、观察窗口、随机/策略量词、旧存档 schema 和未知时的结果。
- **证据：** `docs/architecture/01-requirements-spec.md` FR-VS-2/3/4；`docs/api/01-interface-contract.md` §7；`docs/research/07-formal-verification-methodology.md` §4.3、§5.3 指出版本精化保持和反例迁移仍属研究问题。
- **为什么重要：** 三个字段可以由 stub 永远返回“需要重跑”或空报告，表面上满足接口却不构成兼容性验证；未经定义的“资源价值不下降”尤其不能进入 `proved`。
- **建议怎么修：** MVP 将版本模块降为断言 diff、影响查询列表和“需重跑”清单；删除兼容性结论或只支持一个明确的、有限状态的性质。每一种兼容性都必须先有 oracle、状态映射和最小反例集，随后才进入范围。

### M-12：测试设计覆盖了合同，却没有覆盖事实正确性和真实运行边界

- **问题：** 测试矩阵大量是 schema fixture、确定性 proposer 和具名反例，容易出现“stub 端到端”——合同、图、verify 链路通过，但真实抽取、字段蕴含、数据库事务、队列超时和模型升级未测。当前仓库也没有实现测试可执行证据。
- **证据：** `docs/architecture/02-module-decomposition.md` 各模块“独立测试方式”；`docs/architecture/03-system-architecture.md` §8.1 明确允许无模型 fixture；`docs/architecture/08-mvp-milestones.md` M2/M7 要求 gold set 与端到端，但仓库 `tests/` 只有占位文件。`docs/research/02-neurosymbolic-extraction.md` §5 要求合成集、脱敏真实集、对抗集、人工盲评，不能只依赖 LLM-as-a-judge。
- **为什么重要：** 结构测试只能回答“输出长得对”，不能回答“事实正确”；没有真实后端和失败注入，`unknown`、重复提交、stale cache、跨 context 泄漏都可能在上线才出现。
- **建议怎么修：** 先建立可公开归因的 gold set 和人工标注协议，分开测 format/ontology/evidence/claim semantics/solver mapping；加入真实后端容器、故障注入、超时取消、重试幂等、版本漂移和负载测试。确定性 proposer 只能测合同，不能计入抽取精度或端到端通过率。

### M-13：高并发验证缺少队列、资源配额和缓存一致性设计

- **问题：** 有私有 solver/context 和异步 job，但没有 worker 数量、CPU/内存配额、取消是否杀死 native solver、优先级、公平性、排队上限、熔断、幂等缓存键或快照失效规则。查询缓存也没有把后端、schema、权限、snapshot 纳入合同。
- **证据：** `docs/architecture/03-system-architecture.md` §2.2、§4.1、§7 只规定“有超时/取消”；`docs/architecture/04-detailed-design.md` §9.1 只规定私有 context；`docs/research/04-nl2cypher-routing.md` §5 风险指出冷启动、排队、权限/schema 变化会导致尾延迟和缓存不一致；`docs/research/05-formal-verification.md` §4.3 建议 CPU/内存配额、取消和按租户限流。
- **为什么重要：** 私有 context 解决线程安全，不解决资源耗尽。一个恶意或意外的大图任务即可占满 worker，使所谓高并发请求全部排队。
- **建议怎么修：** MVP 固定单 worker/单队列并明示容量；生产前增加任务大小上限、CPU/内存/墙钟配额、排队拒绝、取消后进程回收、优先级和可观测指标。所有缓存键至少包含 snapshot、ontology/IR/schema、backend、权限主体和模板版本。

## 4. 与既有调研结论的矛盾/偏离

1. **`README.md` ↔ `docs/research/04-nl2cypher-routing.md`：** README 把端侧微调 SLM 和实时 NL2Cypher 写成主架构；04 报告给出零样本执行准确率 26.21%–30.99%（8B）及复杂查询显著下降，并明确反对未经基线和真实数据就早期微调。MVP 虽然把微调移出范围，但 README 未同步。
2. **`README.md` ↔ `docs/research/04-nl2cypher-routing.md`/`05-formal-verification.md`：** README 的“高并发、毫秒级响应”没有限定快路径；04 只把毫秒级放在缓存/模板，05 说明 SMT 延迟不能由约束数通用推导。该声称与研究证据不相容，至少属于未验证的过度表述。
3. **验证设计 ↔ `docs/research/07-formal-verification-methodology.md`：** 设计有分层 L0–L3，但把 CEGAR 的关键闭环、Petri/离散动态、无界不变量和随机/博弈量词留在名词或范围外，没有定义抽象保持关系。若仍将分层结果用于全局“验证通过”，即与 07 的“过近似反例需回放、有限 UNSAT 不可推广、性质量词必须显式”的结论相悖。
4. **`README.md`“出厂即正确” ↔ `docs/research/02-neurosymbolic-extraction.md`、`literature-review-ludograph.md`：** 研究明确区分格式、本体、事实、模型四层，并指出 quote 连续不等于 claim 蕴含、求解器只保证错误模型的正确答案；“Correct-by-Construction”未限定为仅构造层的结构约束，容易成为与调研结论相冲突的产品表述。
5. **MVP 双投影 ↔ `docs/research/03-graph-storage.md`：** 03 建议 Assertion 作为规范存储，direct edge 只是热点投影，并明确存在双写/一致性/删除重建风险；MVP 却把两种投影语义一致列为基础需求，未给一致性时点和刷新协议。
6. **本体治理 ↔ `docs/research/01-ontology-game-design-theory.md`/`literature-review-ludograph.md`：** 研究把 24/25 计数不一致列为进入实现前必须解决的治理问题；架构文档仍把它保留为待决事项，虽选择 24，却没有完成权威源、ADR 和 CI 裁决。
7. **输入范围 ↔ `docs/research/game-design-theory/03-analysis-method.md`：** S1–S7 流程要求来源登记、可验证性筛选和边界记录，并明确流程不能处理表格、图文混合和跨文档一致性；设计接口仍用宽泛“策划文档”描述，只提供 chunk 文本，未将这些限制提升为拒绝契约。

## 5. 隐含假设与未定义边界清单

- **规模：** 没有默认实体/Assertion/状态变量/路径深度/输出行数上限；“单机”不是规模定义。
- **并发：** 未定义读写比例、单写者/多写者、请求突发、公平性、租户配额、队列上限。
- **部署：** Neo4j 版本/Edition、驱动、持久化、备份和容器资源未定；Kùzu 已 archived，替代 LadybugDB 也未完成 PoC。
- **模型：** proposer/intent router 的模型尺寸、上下文上限、温度、结构化输出支持、拒答语义和成本未定；“端侧”无硬件定义。
- **输入：** chunk 是否重叠、跨句/跨表/跨图引用、字符编码、表格列语义、图片 OCR 和文档解析失败未定。
- **身份：** 同一 chunk 内重复 mention 的 identity key、人工 entity-link 结果格式、节点持久 ID 与 claim ID 关联未定。
- **语义：** 初始状态、合法等待、动作原子性、并发更新、回滚、默认值、例外优先级、开放/闭世界开关的默认与可切换范围未定。
- **概率/时间：** 概率独立性、权重与概率、抽样是否放回、回合/现实时间/tick、重置和有效期未定；现有字段不足以支持 07 报告中的随机/时间性质。
- **版本：** 快照一致性、partial snapshot 是否可读、反例失效判定、目标集合和存档映射未定。
- **权限/运维：** scope 不是安全边界；认证主体、授权、审计、备份恢复、数据删除和私有文档保留期未定。

## 6. 可测试性审查

### 6.1 能机械验证的部分

JSON Schema、枚举、局部引用、连续 offset、domain/range、确定性 ID、错误码枚举、`k` 字段、私有 solver 对象禁止跨 worker，这些可以写成确定性测试。它们只证明格式/本体/资源隔离层，不证明事实和模型语义。

### 6.2 当前不能机械验证或尚未定义的部分

- “抽取正确”：需要按 claim/字段标注的 gold、人工分歧裁决、unsupported claim 和拒绝样本；连续 quote 不够。
- “验证通过”：必须定义性质、量词、初始状态、模型边界和证明保持关系；有界 UNSAT 只能机械生成有界结果。
- “投影语义一致”：必须固定查询集合、历史/当前视图、时间点和 stale projection 行为。
- “版本兼容”：必须有状态/资产映射和独立 oracle；目前只有字段名。
- “高并发/毫秒”：必须有固定 workload、硬件、冷暖缓存、并发、数据规模和真实测量；当前**未验证**。

### 6.3 防止 stub 冒充端到端验收

确定性 proposer fixture 只能证明合同链路，不得计入抽取质量；真实后端容器、真实/脱敏 gold set、故障注入和端到端 provenance replay 应作为 M7 硬门禁。每个端到端结果都应标记输入来源、模型版本、数据库版本、solver 状态和是否经过人工证据审核。

## 7. 过度设计、需求蔓延与建议砍项

### 建议从 MVP 砍掉

1. **端侧 SLM 微调**：研究 04 明确应在数据和基线之后再做；保留规则/模板意图路由。
2. **自由动态 NL2Cypher**：先只支持有限查询模板和参数槽位；动态编译作为实验/异步功能，不进入可靠路径。
3. **双物理投影**：只保留 Assertion 规范存储；热点边/视图待真实查询证明必要性后再做。
4. **三类 D1/D2/D3 同时交付**：选择一个可定义、可回放的性质（建议 D2 有界状态机或 D1 小资源流）做垂直切片。
5. **三类版本兼容性结论**：MVP 只做快照、断言 diff、影响查询和需重跑清单；不报告未定义的价值/存档兼容性。
6. **“证明”类结果**：在没有完备有限模型或证明证书前，只交付可回放反例、带 k 的有界无反例、unknown、not-modeled。
7. **CoT 和多 agent 编排**：CoT 保留为可消融实验，多 agent 直接砍掉；两者都不是可靠性的替代物。
8. **多后端可替换性实现**：MVP 锁定一个真实后端；只保留 IR 边界，不实现多方言能力矩阵。

### 不可同时满足的诉求

- **“任意自然语言长尾覆盖”** 与 **“端侧、毫秒级、可证明正确”** 不能同时作为 MVP SLA；必须选模板覆盖/低延迟，或长尾覆盖/异步高延迟。
- **“冲突/不确定性全部保留”** 与 **“自动输出单一 proved 结论”** 不能无条件同时满足；冲突必须阻断或显式作为假设分支。
- **“物理后端可随时替换”** 与 **“MVP 立即利用某后端特性达到性能”** 需要读模型/适配器边界，不能用一个抽象接口同时保证。
- **“只做单租户本地 MVP”** 与 **“工业级高并发服务”** 不是同一个验收目标；README 必须二选一地表述。

## 8. 上游八条软件工程规范的落地判断

| 规范 | 判断 | 证据与缺口 |
| --- | --- | --- |
| 1. 流程分阶段 | **部分落地** | `08-mvp-milestones.md` 有 M0–M7 和出口条件；但当前没有实现、CI gate 或阶段产物证据，里程碑仍是计划。 |
| 2. 需求对齐 | **部分落地，存在明显漂移** | `01-requirements-spec.md` 很详细且引用研究；但 README 未同步微调、性能和 Correct-by-Construction 口径，规格还依赖缺失的 99 文档。 |
| 3. 设计边界清晰 | **未通过** | 模块职责写得清楚，但证据蕴含、意图/事实、抽取输入、验证证明边界、适配器能力和版本兼容仍不能执行。 |
| 4. 编码规范 | **未验证** | 只有接口伪代码和目录 README，尚无实现代码可检查；不能把命名示意视为 Python/接口/错误处理规范已落地。 |
| 5. 版本控制与协作 | **未通过/未验证** | ADR 目录为空，设计引用的 99 文档缺失，技术裁决不可独立追踪；分支、评审和变更记录尚未形成可审计证据。 |
| 6. 多层测试门禁 | **部分落地** | 文档列出 schema、集成、回放、压力和性能门禁；实际测试目录是占位，且真实语义/gold/故障注入尚未存在。 |
| 7. 文档同步 | **未通过** | README 与需求/研究的性能和模型路线冲突；24/25 计数仍待决；引用的 99 文档不存在。 |
| 8. 安全与运维 | **仅有边界声明** | API 有错误码/审计概念，架构明确不做多租户/HA/容量；未提供认证授权、备份恢复、数据保留、资源隔离和生产禁止护栏。 |

## 9. 不可证伪或目前无法验证的声称

- “高并发、毫秒级响应”：未定义 workload、硬件、并发和尾延迟；**未验证**。
- “出厂即正确 / Correct-by-Construction”：未限定只对结构不变量成立；自然语言蕴含和模型编译仍未闭环。
- “每个查询/验证结果都能回到原文”：连续 span 可测，字段语义蕴含、partial snapshot 和物化视图一致性尚未验证。
- “替换图后端或求解器不改变语义”：没有第二个真实后端/solver 的一致性 PoC；**未验证**。
- “三类检查的最小可运行版本”：当前无实现和真实测试；**未验证**。
- “版本兼容性可分别报告”：字段已定义，判定 oracle、状态映射和反例标准未定义；**未验证**。
- “分层验证控制求解器风险”：没有 CEGAR 迭代、抽象保持证据或真实性能曲线；**未验证**。

## 10. 最小修复顺序

1. 先修 README 口径，删除无条件性能和正确性承诺，并明确 MVP 是单租户本地基线。
2. 裁决 24/25，建立机器 schema 单源、生成器、ADR 和漂移 CI。
3. 定义 `claim_kind/layer`、字段级 evidence review 和不可编译状态，封闭从抽取到 Rule IR 的错误路径。
4. 锁定一个后端、一个性质和一个公开 gold set，完成真实端到端回放。
5. 仅在第 4 步有数据后再评估 SLM/CoT、缓存、投影和性能；把所有未知结果保留为未知，不用 stub 通过替代证据。

## 11. 审查结论

当前设计可作为研究方向草案，不能作为“工业级高并发毫秒响应”或“出厂即正确”的实现基线。阻断发布的不是缺少更多技术名词，而是三件事：**证据蕴含没有成为硬边界、性能承诺没有可复现实测、MVP 范围超过可验证能力**。在这三项关闭前，不应进入大规模实现或对外性能/正确性宣称。

## 12. 第二轮复核：设计方回应后的裁决

### 12.1 复核方法与判定口径

本轮重新读取了 `01`、`02`、`03`、`04`、`05`、`07`、`08`、`99`、API 合同、`docs/adr/0001`–`0010` 以及 `docs/LudoGraph 图谱数据模型设计.md`。判定对象是当前仓库中的**可执行合同/验收门禁**，不是“已经写出风险”或“未来可以实现”的陈述。当前 `src/`、`tests/`、`configs/`、`scripts/` 仍只有占位 README/`.gitkeep`，因此任何仅有 fixture 规划、接口伪代码、ADR `Proposed` 状态或“应当”措辞的项目均不能判为 FIXED。

### 12.2 逐条裁决

| 编号 | 二轮裁决 | 当前证据与具体缺口 |
|---|---|---|
| C-01 | **PARTIAL** | `04-detailed-design.md` §2.4 已明确“连续性不等于蕴含”，并要求不能支持方向/条件/数量时进入 `uncovered`/人工队列；`0003` 的“理由与边界”也承认这一点。这关闭了第一轮的概念混淆，但 `ExtractionEnvelope`（`04` §1.2、API §3.1）没有字段级 evidence entailment/review 状态、审核主体/版本/理由或不可绕过的导入/Rule IR 门禁；`02` §3.2 的 evidence 仍只有 span 对齐接口。因此只能算部分修复，仍可能把“结构校验通过、蕴含未审”的 claim 送入确认图谱。 |
| C-02 | **PARTIAL** | `01` §3.2 已给出按场景的 P50/P95 目标、求解器 P50/P95/P99，并要求输入规模/硬件/冷热/并发；`07` §3.4 也要求吞吐、资源、超时和失败率。这是对性能口径的实质收缩。但 `README.md` 的“LLM CoT/端侧微调 SLM”和“高并发、毫秒级响应”仍未改；`03` §2.2、§4.1/§7 与 `ADR-0009` 仍没有固定 workload、队列容量、背压、配额或真实测量结果。故 P95/P99 已进入规格，性能承诺和验收仍未闭合。 |
| C-03 | **OPEN** | `01` §6.1 仍把双投影、两步路由、D1/D2/D3、版本三类报告和评测骨架全部列为 in-scope；`08` 仍为 M0–M7 全链路出口，并未把 MVP 收缩为一个后端/一个性质/一个 gold-set 垂直切片。仓库也没有实现、真实后端、solver worker、gold set 或可执行测试，故当前出口条件不可由仓库满足。 |
| M-01 | **PARTIAL** | `01` §6.2 虽写明“不做端侧 SLM 微调”，`ADR-0004` 也把两步路由优越性列为待测假设；但 `README.md` §架构概要和“三层职责”仍把 CoT、端侧微调 SLM 写成事实。模型路线已在设计层收窄，但设计文档与对外入口仍冲突。 |
| M-02 | **OPEN** | `02` §6.2、`04` §5.2 现在有 over/under/unresolved 和 spurious 结果，`ADR-0005` 也明确抽象风险；但没有“抽象→反例回放→谓词精化→重新求解”的循环接口、终止/预算、精化产物或保持关系证明。`04` §9.2 只是把 `sat` 回放失败映射为 spurious，不能称为 CEGAR 闭环。 |
| M-03 | **PARTIAL** | `04` §9.2、`API` §6.1 已把深度 `k` 的 UNSAT 限定为 `bounded-no-counterexample`，并把只有无界/完备有限模型的 UNSAT 才映射为 `proved`；`08` §8 也有对应出口。这关闭了“所有 UNSAT 都是 proved”的直接错误。但结果合同没有强制 `proof_scope`、`approximation`、`completeness_basis`、checker/proof artifact；`01` §2.4 仍保留宽泛 `proved` 枚举。因此证明语义尚不可安全消费。 |
| M-04 | **PARTIAL** | `03` §2.2、§7 和 API §2/§6 增加了异步 `job_id`、`queued/running/succeeded/failed/cancelled`、幂等、取消、超时及部分批次失败列表；API §6.2 也区分任务层 `failed/TIMEOUT` 与报告层 `unknown`。但没有 extraction/import/verify/batch 的完整状态转移、原子提交点、批次 completeness bitmap、partial snapshot 可见性/验证禁令，重试与缓存快照关系也未定义。 |
| M-05 | **OPEN** | API §3.1 仍只有 `chunk_text` 和字符 `start/end`；`01` §1.1 仍把 Excel/流程图等列为背景输入，却没有表格 cell、图节点、跨 chunk、Unicode 坐标或解析失败合同，也没有 `unsupported_source_format` 拒绝码。`08` 的 fixture 仍只覆盖 chunk。 |
| M-06 | **PARTIAL** | `04` §2.1 增加了 `candidate attribution (rule/intent/experience)`，并规定只有规则事实可进入确认图谱；`01` §1.2/§6.3 也强调保守拒绝。这改善了边界说明。但 API/模型文档的 Claim 仍没有强制 `layer`/`claim_kind`（`docs/LudoGraph 图谱数据模型设计.md`“Claim 字段”），`04` §2.1 仍允许意图/体验作为有来源 claim；没有验证器字段和编译门禁阻止其进入 Assertion/Rule IR。 |
| M-07 | **PARTIAL** | 本轮已补上 `99-design-decisions-and-open-questions.md` 与 `ADR-0001`–`0010`；`05` §1、§3 明确逐项是 24 个谓词，`08` M0/M1 也写出 17/24。这解决了上一轮的缺失文件问题。但 `05` §1、§252 仍把 25/24 留作治理待决，`02` §2.1、`07` §4/§5 只要求“单一机器源/生成/漂移 CI”，没有源文件路径、生成命令、生成物或已运行的 CI。计数和 schema 单源尚未真正关闭。 |
| M-08 | **PARTIAL** | `03` §3/§5.1、`05` §6.1–6.2、`ADR-0002` 明确 Assertion 是规范历史、direct edge 是可重建投影并带 `projection_revision`；这是比第一轮清楚的单向权威关系。但 `01` §6.1 #3 和 `08` M3 仍把两种投影等价作为 MVP 出口，没有事务边界、刷新/失效协议、读一致性时间点或 stale-view 行为。 |
| M-09 | **PARTIAL** | `03` §3、`ADR-0001` 已建立 Graph adapter 边界，并把 LPG/Cypher 作为首个 PoC；但 ADR 状态为 Proposed，未锁定 Neo4j 版本/Edition/驱动/部署模式，没有真实能力矩阵、第二后端对等测试或运行 PoC。抽象边界已有回应，但不能据此宣称多后端可替换。 |
| M-10 | **PARTIAL** | `03` §4.1 明确单租户/单机、不做多租户和 HA，API 开头和 `01` NFR-S2 也明确 namespace 不是授权；`07` §6 增加了秘密、日志、备份恢复、访问控制测试和审计字段。这些是边界改善。但没有主体到 scope 的授权映射、生产禁止护栏、租户/资源隔离、删除/保留期的可执行合同；API 的 `403` 只是错误码，不能证明安全边界。 |
| M-11 | **OPEN** | `01` FR-VS-3、API §7.2、`02` §7.1/§7.3 仍只列 `resource_value`、`goal_reachability`、`save_continuity` 名称及“分别报告”。`99` 开放问题 #7 仍要求人类定义度量、状态映射、观察窗口、量词、旧存档 schema 和 unknown 规则；没有 oracle 或最小反例集。 |
| M-12 | **OPEN** | `07` §3.3–§3.4、`08` M2/M7 和 `03` §8.1 增加了 gold set、真实后端容器/系统 fixture、故障注入、性能上下文和“无模型 fixture 仅合同链路”的要求，方向正确；但当前 `tests/` 仍仅占位，且没有真实抽取、人工证据蕴含、后端事务、队列取消/重试、缓存失效或版本漂移的可执行端到端证据。设计验收条件不是验收结果。 |
| M-13 | **PARTIAL** | `03` §2.2/§4.1/§7、`04` §9.1、`ADR-0010` 已规定异步、私有 solver context、超时和资源限制的方向；但没有 worker 数、队列上限/拒绝、CPU/内存/墙钟配额、优先级/公平性、native solver 取消回收或熔断。API §5 的查询缓存也没有强制 snapshot、schema/IR、backend、权限主体、模板版本等 key 分量和失效规则。私有 context 不能替代资源配额和缓存一致性。 |

### 12.3 二轮计数与发布裁决

- **二轮计数：** FIXED = 0，PARTIAL = 12（C-01、C-02、M-01、M-02、M-03、M-04、M-06、M-07、M-08、M-09、M-10、M-13），OPEN = 4（C-03、M-05、M-11、M-12）。
- **接受的设计改进：** 结果协议已区分 `unknown`/`not-modeled`/`bounded-no-counterexample`；`README` 以外的规格已加入 P95/P99 和 workload 上下文；Assertion 被明确为规范存储、direct edge 为可重建投影；版本四元组、异步 job、私有 solver context、冲突并存、24 项清单和 ADR 索引已补齐。
- **仍阻断进入实现/发布的事项：** C-01 的证据蕴含硬门禁、C-02 的 README/实测闭环、C-03 的 MVP 缩范围，以及 M-01 的 README 同步、M-02、M-05、M-09 的真实后端 PoC、M-11、M-12、M-13。尤其不能把文档中“应有的 fixture/CI/PoC/报告”当成已完成证据。

### 12.4 必须由人类决策的事项

1. 指定 evidence review 的责任主体、字段级通过阈值、审核版本和 `uncovered`/不可编译转换规则。
2. 将 MVP 裁成一个真实后端、一个验证性质、一个公开 gold set，并批准删除/后移双投影、三类验证和三类兼容性强承诺。
3. 对 24/25 作最终治理裁决，并指定唯一机器 schema 源、生成命令和漂移 CI 的责任人。
4. 锁定后端版本/Edition/许可证、固定 benchmark 硬件与 workload，批准 P50/P95/P99 和队列/超时预算；在实测前禁止对外“高并发/毫秒级”。
5. 定义 `proved` 的 proof scope/completeness 证据，以及 `possible`/`planned`/`negated` 是否可分支验证。
6. 定义三类版本兼容性 oracle、旧存档映射和 partial snapshot 规则。
7. 决定 MVP 的认证授权、数据保留/删除、备份恢复和资源配额边界；在这些边界存在前，禁止将单机方案部署为共享生产服务。
