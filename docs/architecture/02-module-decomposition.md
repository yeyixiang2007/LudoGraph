# 模块划分

- **文档性质：** 设计草案（v1 draft）。本文件把 MVP 能力拆为可独立开发、可独立测试、可独立替换的模块，并给出每个模块的职责、边界与 I/O 合同。
- **对齐锚点：** `src/ludograph/README.md` 已声明的目录布局（`contracts/`、`extract/`、`graph/`、`query/`、`verify/`、`versioning/`）。本文档的模块划分与之一一对应，不另造命名。
- **上游依据：** `01-requirements-spec.md` 的功能需求编号（`FR-*`）。

---

## 1. 划分原则

### 1.1 四条切分原则

1. **按语义层次切分，而非按技术栈切分。** 抽取、表示、验证是三个语义上不可互相替代的层次（见需求 §1.2），因此它们是三个顶层模块边界。按「LLM 服务」「数据库服务」切分会把语义边界打散。
2. **以「可独立验证的合同」为模块接口。** 模块之间只通过带版本的 JSON 合同通信；不允许跨模块共享内存对象、共享数据库连接或共享模型上下文。这条原则的直接收益是每个模块可以用 fixture 独立测试。
3. **实现可替换性内聚在适配层。** 数据库、求解器、模型都是可替换基线；替换它们不应修改上游模块的任何一行。因此适配器必须是被依赖方向指向的叶子模块。
4. **不确定性外化为数据结构。** `uncovered`、`not-modeled`、`unknown`、`bounded-no-counterexample` 不是错误分支，而是合同中的一等字段。模块边界必须让这些状态可以无损穿过。

### 1.2 依赖方向

```text
contracts/            （无依赖：schema、枚举、ID 规范、错误码）
    ▲
    │
extract/   graph/   query/   verify/   versioning/
    │         │        │         │          │
    └─────────┴────────┴─────────┴──────────┘
                  ▲
                  │
        adapters（db / solver / model，叶子）
```

**规则：** `contracts/` 不依赖任何模块；五个能力模块只能依赖 `contracts/` 与适配器的抽象接口；适配器实现只能依赖 `contracts/`。任何反向依赖（如 `contracts/` 引入数据库类型）视为架构违规。

### 1.3 模块总览

| 模块 | 目录 | 单一职责 | MVP 可独立交付 |
| --- | --- | --- | --- |
| 合同与本体 | `contracts/` | 定义并校验所有跨模块数据形态 | ✅（最先交付） |
| 抽取 | `extract/` | 文档 → 本体化 claim（带证据） | ✅ |
| 图谱 | `graph/` | claim 的持久化、投影、查询执行 | ✅ |
| 路由 | `query/` | 自然语言 → 结构化意图 → 方言查询 | ✅ |
| 验证 | `verify/` | claim → 规则 IR → 形式化检查 → 结论 | ✅ |
| 版本 | `versioning/` | 快照、diff、兼容性报告 | ✅ |
| 适配器 | `adapters/`（实现置于各模块内） | 具体 db/solver/model 绑定 | ✅（每类一个） |

---

## 2. `contracts/` — 合同与本体模块

### 2.1 职责

- 持有**单一权威来源**的机器可读本体 schema：17 个 canonical 叶子标签、24/25 个关系类型（见 `05-graph-schema-design.md` 的计数裁决）、domain/range 矩阵、限定字段定义、`certainty` 与 `status` 枚举、原因代码枚举、错误码。
- 从该 schema **生成**：抽取输出的 JSON Schema、校验器白名单、数据库约束脚本、文档中的数据字典表。
- 提供断言 ID 的确定性生成规范（规范化 tuple → SHA-256）。
- 提供跨模块的信封结构（`status`/`result`/`diagnostics`）与版本字段规范。

### 2.2 边界（**不**做什么）

- 不执行抽取、不做数据库操作、不求解。
- 不持有任何具体数据库或求解器类型。
- 不做「业务规则」判断——它只回答「形状与白名单是否合法」，不回答「事实是否为真」。

### 2.3 I/O 合同

| 方向 | 内容 |
| --- | --- |
| 输入 | 无（或来自仓库内的 schema 源文件） |
| 输出 | `OntologySchema`（可序列化）、`ExtractionEnvelope` JSON Schema、`AssertionId` 生成器、`ErrorCode` 枚举、`ReasonCode` 枚举 |

### 2.4 关键接口（签名示意，语言无关）

```text
load_schema(ontology_version: str) -> OntologySchema
validate_extraction(doc: JSON, schema: OntologySchema) -> ValidationReport
make_assertion_id(tuple: NormalizedTuple) -> str   # 确定性
list_leaf_labels(schema) -> set[str]
domain_range(predicate: str, schema) -> (set[str], set[str])
```

### 2.5 覆盖的需求

`FR-EX-2`、`FR-EX-3`、`FR-EX-8`、`FR-GX-3`、`FR-GX-4`、`FR-GX-6`、`IR-1`、`IR-3`、`IR-4`

### 2.6 独立测试方式

纯函数、无外部依赖：以 schema fixture + 合法/非法抽取 JSON fixture 做表驱动测试。**验证的是格式层与本体层，不涉及事实层。**

---

## 3. `extract/` — 抽取模块

### 3.1 职责

把单个 chunk 转换为符合抽取合同的 `nodes`/`claims`/`uncovered`，并保证：

- 抽的是**原文明确说出**的事实；
- 每条 claim 都有连续原文证据；
- 无法可靠表示的进入 `uncovered`；
- 数值、周期、概率保留原文形态。

### 3.2 内部子模块（可分阶段实现，不改变对外边界）

| 子模块 | 职责 | 备注 |
| --- | --- | --- |
| `chunking` | 文档切分与来源登记 | 切分版本变化视为版本事件（`DR-1`） |
| `proposer` | 调用模型产出候选结构（受 schema 限形） | 可替换：提示式 / API 结构化输出 / 约束解码 |
| `validator` | 确定性校验（白名单、domain/range、证据连续、限定值） | 与 `contracts/` 同一 schema |
| `evidence` | 证据绑定与 span 对齐 | 服务端检查 `quote == chunk[start:end]` |
| `uncovered` | 拒绝分类与原因代码 | 拒绝能力是一等指标 |

### 3.3 边界

- **不做**跨 chunk 实体合并（`entity_link` 属 MVP 外）。
- **不做**冲突裁决：矛盾 claim 并存。
- **不做**单位换算、周期换算、概率归一化。
- **不做**形式化编码——它输出的是图谱事实，不是约束。

### 3.4 I/O 合同

| 方向 | 内容 |
| --- | --- |
| 输入 | `chunk_id`、`chunk_text`、`scope{game_id, system_id}`、`ontology_version`、模型/提示模板版本 |
| 输出 | `ExtractionEnvelope{ontology_version, scope, status, nodes[], claims[], uncovered[]}` + `ExtractionDiagnostics{tokens, latency, retries, model_version}` |

### 3.5 关键接口

```text
extract_chunk(req: ExtractionRequest) -> ExtractionEnvelope
validate(envelope: ExtractionEnvelope, schema) -> ValidationReport
bind_evidence(claim: Claim, chunk_text: str) -> EvidenceCheck
classify_uncovered(raw_text: str, reason: ReasonCode) -> UncoveredItem
```

### 3.6 覆盖的需求

`FR-EX-1` … `FR-EX-11`、`DR-2`、`DR-3`、`DR-4`、`DR-5`、`NFR-1`、`NFR-A1`

### 3.7 独立测试方式

- 单元：validator、evidence span 对齐、uncovered 分类（纯函数）。
- 回归：固定 chunk fixture + gold 抽取输出，报告 §5.1 指标。
- 稳定性：同一输入多次采样的 `certainty` 一致率。

---

## 4. `graph/` — 图谱模块

### 4.1 职责

- 把 `ExtractionEnvelope` 投影为物理存储（两种形态：关系属性 / 独立 `Assertion` 节点），语义一致。
- 生成确定性断言 ID，维护 `status`/`supersedes` 生命周期。
- 执行编译后的图查询，并返回带回指链的结果。
- 提供「当前有效事实」视图与「完整断言历史」视图的区分。

### 4.2 边界

- **不**理解自然语言。
- **不**决定查询意图——它只执行路由模块给出的已编译查询。
- **不**做本体判断——非法结构在进入之前应已被校验器拒绝。
- **不**把物化投影当作规范来源：投影是热点查询优化，规范来源是断言历史。

### 4.3 I/O 合同

| 方向 | 内容 |
| --- | --- |
| 输入 | 校验通过的 `ExtractionEnvelope`；已编译查询；`CompiledQuery{backend, dialect, params, capabilities_required}` |
| 输出 | 导入报告（新增/更新/supersede 计数）；`QueryResult{rows, provenance[], warnings[]}` |

### 4.4 关键接口

```text
project(envelope: ExtractionEnvelope, mode: ProjectionMode) -> ImportReport
upsert_assertion(a: Assertion, revision_policy) -> AssertionId
execute(query: CompiledQuery) -> QueryResult
resolve_provenance(assertion_ids) -> ProvenanceChain   # → chunk → span
materialize_hot_view(view_spec) -> ViewStatus          # 可选优化
```

### 4.5 覆盖的需求

`FR-GX-1` … `FR-GX-5`、`FR-QR-3`、`NFR-A1`、`NFR-E1`、`NFR-S2`

### 4.6 独立测试方式

- 集成：起一个真实（或容器化）后端，做导入→查询→回指链断言。
- 双投影一致性：同一 envelope 分别以两种 `ProjectionMode` 导入，对同一组查询断言结果等价。
- 审计：修订后旧断言仍可查询，`supersedes` 链完整。

---

## 5. `query/` — 路由模块

### 5.1 职责

两步路由：**意图/槽位分类 → schema-aware 查询编译**。

| 步骤 | 输出 | 特点 |
| --- | --- | --- |
| 意图/槽位路由 | `Intent{kind, slots[], constraints[]}` | 类别可枚举、可单测、可用小模型或规则 |
| 能力探测 | `BackendCapabilities` 与需求比对 | 显式拒绝 + 降级路径 |
| 方言编译 | `CompiledQuery{backend, dialect, params}` | 与后端解耦的 IR → 具体方言 |

### 5.2 边界

- **不**直接执行查询（由 `graph/` 执行）。
- **不**在自然语言空间做算术或聚合——属于编译后查询的职责。
- **不**把本体外问题强行为可编译查询；须返回 `unanswerable` + 原因（`FR-QR-5`）。
- **不**承担抽取——它只消费图谱已有事实。

### 5.3 I/O 合同

| 方向 | 内容 |
| --- | --- |
| 输入 | `question: str`、`scope`、`ontology_version`、`backend_profile` |
| 输出 | `RoutedQuery{intent, slots, compiled, confidence, fallback}` 或 `QueryRefusal{reason, missing_fields}` |

### 5.4 关键接口

```text
route_intent(question: str, scope) -> Intent | QueryRefusal
detect_capabilities(backend_profile) -> BackendCapabilities
compile(intent: Intent, capabilities: BackendCapabilities) -> CompiledQuery | QueryRefusal
fast_path_lookup(question_fingerprint) -> CompiledQuery | None   # 模板/缓存快路径
```

### 5.5 覆盖的需求

`FR-QR-1` … `FR-QR-5`、`IR-5`、`NFR-P1`、`NFR-P2`、`NFR-P3`

### 5.6 独立测试方式

- 单元：意图分类准确率（固定问题集）；编译正确性（gold IR → gold 方言）。
- 能力矩阵：对着能力表逐项断言「支持 → 编译」/「不支持 → 拒绝 + 降级路径」。
- 快路径：模板命中不触发模型调用（可断言调用计数为 0）。

---

## 6. `verify/` — 验证模块

### 6.1 职责

把图谱 claim 保守编译为规则 IR，再编译为形式化查询，执行后返回**多结果协议**，并保留 assertion → claim → evidence 回映射。

### 6.2 分层（对应 `05-formal-verification.md` 的分层思想）

| 层 | 手段 | 成本 | 产出 |
| --- | --- | --- | --- |
| L0 结构 | 图遍历、SCC、可达性、one-hot 检查 | 线性/多项式 | 结构性结论（**不足以**作为死锁证明） |
| L1 抽象数值 | 区间域传播（过近似快筛） | 低 | 候选风险区间 |
| L2 离散动态 | 有界模型检查（BMC，深度 `k`） | 中 | `counterexample` 或 `bounded-no-counterexample(k)` |
| L3 约束精化 | 有界 SMT（`QF_LIA`/`QF_BV`） | 中高 | 精化结论、回映射 assertion |
| L4 未决定 | 缺字段/语义不明的显式外化 | — | `not-modeled` + 缺失字段清单 |

**MVP 只做 L0–L3 + L4 的外化**；无界证明与随机博弈求解不在 MVP 范围。

### 6.3 边界

- **不**重新解释图谱事实；它只消费 claim 与 qualifiers。
- **不**把语义不明的 claim 强行编码（返回 `not-modeled`）。
- **不**把 `bounded-no-counterexample` 表述为全局安全。
- **不**共享 solver context 跨任务。

### 6.4 I/O 合同

| 方向 | 内容 |
| --- | --- |
| 输入 | 检查类型（D1/D2/D3）、`scope`、图谱查询或断言集合、`assumptions`（开放/闭世界、缺省、单位、例外优先级）、规模上限 `k` |
| 输出 | `VerificationReport{check_type, results[], mapping[], timing[], protocol_stats}` |

`results[]` 每项为 `{status: proved|counterexample|bounded-no-counterexample|unknown|not-modeled|spurious-counterexample, assumptions, k?, witness?, missing_fields?}`。

### 6.5 关键接口

```text
build_rule_ir(assertions, assumptions) -> RuleIR | NotModeled(missing_fields)
compile_over_approx(ir: RuleIR, domain: AbstractDomain) -> ApproxModel
compile_under_approx(ir: RuleIR, k: int) -> BoundedModel
check_economic_deadlock(ir, opts) -> VerificationReport      # D1
check_state_conflict(ir, opts) -> VerificationReport         # D2
check_numeric_bounds(ir, opts) -> VerificationReport         # D3
map_assertions(report) -> AssertionProvenanceMap             # → claim → span
```

### 6.6 覆盖的需求

`FR-VF-1` … `FR-VF-10`、`NFR-3`、`NFR-4`、`NFR-A3`、`NFR-P4`

### 6.7 独立测试方式

- 编码单元测试：三类检查各有一组「有环但无死锁」「one-hot 合法但目标不可达」「LP 有解但不可执行」等具名失败模式用例。
- 回映射测试：每个 assertion 都能回溯到 claim 与 span。
- 并发：worker pool 压力测试，断言无跨 context 对象传递。
- 性能：分层报告实测曲线，与 `NFR-P4` 的「不设统一数字目标」一致。

---

## 7. `versioning/` — 版本模块

### 7.1 职责

- 规则快照的创建、存储与比较。
- 生成版本 diff：哪些断言被 `supersede`、哪些查询/结论受影响。
- 生成三类兼容性报告（资源价值 / 目标可达性 / 旧存档可继续），**分别**报告，不合并为一个布尔值。

### 7.2 边界

- **不**做「精化保持定理」的证明（研究阶段）。
- **不**自动迁移反例——MVP 只报告「需重跑」，不声称反例已迁移。
- **不**修改历史快照。

### 7.3 I/O 合同

| 方向 | 内容 |
| --- | --- |
| 输入 | 两个快照引用、`scope` |
| 输出 | `VersionDiff{added, superseded, removed, affected_queries[]}` + `CompatibilityReport{resource_value, goal_reachability, save_continuity}` |

### 7.4 关键接口

```text
snapshot(scope, label) -> SnapshotRef
diff(a: SnapshotRef, b: SnapshotRef) -> VersionDiff
compatibility(a: SnapshotRef, b: SnapshotRef) -> CompatibilityReport
impact_paths(b: SnapshotRef) -> list[ImpactPath]
```

### 7.5 覆盖的需求

`FR-VS-1` … `FR-VS-4`

### 7.6 独立测试方式

固定两版 fixture，断言 diff 与三类兼容性报告的结论可复核。

---

## 8. 跨模块合同与共用地基

### 8.1 模块间不允许的耦合

| 禁止 | 理由 |
| --- | --- |
| 共享数据库连接对象 | 破坏可替换性与可测性 |
| 跨模块共享模型上下文 | 破坏可复现性与并行安全 |
| `query/` 直接读库绕过 `graph/` | 破坏回指链与权限/审计边界 |
| `verify/` 重新解析原文 | 破坏「证据绑定在抽取层完成」的单一职责 |
| `contracts/` 依赖数据库/求解器类型 | 破坏依赖方向 |

### 8.2 共用地基（各模块复用，但归属 `contracts/`）

- `Envelope{status, result, diagnostics}` 统一信封
- `ErrorCode` / `ReasonCode` 枚举
- `ProvenanceChain` 结构（断言 → chunk → span）
- 版本四元组：`contract_version`、`ontology_version`、`ir_version`、`schema_version`

### 8.3 模块 × 里程碑映射（详见 `08-mvp-milestones.md`）

| 模块 | 首个可交付里程碑 |
| --- | --- |
| `contracts/` | M1 |
| `extract/` | M2 |
| `graph/` | M3 |
| `query/` | M4 |
| `verify/` | M5（L0–L1）→ M6（L2–L3） |
| `versioning/` | M7 |

---

## 9. 已知的划分风险（诚实声明）

1. **`extract/` 的 `validator` 与 `contracts/` 的校验函数存在职责重叠风险。** 裁决：校验逻辑的**唯一实现**放在 `contracts/`，`extract/` 只调用。若实现中出现两份白名单，即视为架构违规。
2. **`query/` 的「能力探测」与 `graph/` 的「方言执行」边界可能漂移。** 裁决：能力矩阵由 `graph/` 的适配器声明，`query/` 消费；矩阵本身是数据，不是代码分支。
3. **`verify/` 的 L0 图算法与 `graph/` 的查询能力重叠。** 裁决：L0 的图算法在 `verify/` 内部实现于 IR（模型）之上，而不是在图数据库上跑——因为验证对象是「编译后的模型」而非「库里的图」，二者规模与语义不同。这一条是本设计中最容易被质疑的边界，已列入 `99-design-decisions-and-open-questions.md`。

---

## 修订记录

| 版本 | 变更 |
| --- | --- |
| v1 (draft) | 初稿：六模块划分、依赖方向、I/O 合同、需求覆盖映射、已知划分风险。 |
