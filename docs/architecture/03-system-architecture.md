# 系统架构设计

- **状态：** v1 设计草案，供评审，不是实现承诺。
- **目标：** 将策划文本中的可追溯规则事实，经过本体约束抽取、图谱存储、统一查询编译，转换为可回放的形式化验证任务。
- **非目标：** 不承诺由规则图谱推出玩家体验、文化意义或“可玩性”；不把任何单一数据库、LLM 或求解器固化为系统语义。

## 1. 架构原则

1. **非对称神经-符号分工：** LLM/SLM 只提出候选、识别意图和生成基于证据的表达；本体 validator、查询编译器、图算法和求解器负责确定性约束与验证。
2. **证据优先：** 每个 claim、查询结果和验证 assertion 都能回指来源 chunk 与连续 span。
3. **保守而非强行完整：** 无法可靠表示的内容进入 `uncovered`；语义不完整的验证任务进入 `not-modeled`/`unknown`。
4. **合同与物理实现解耦：** 抽取合同、规则 IR 与验证结果协议不绑定 Neo4j、某个模型或 Z3 API。
5. **增量与版本一等：** 原文切分、本体、断言和验证结论均带版本；修订追加，不覆盖历史。

## 2. 分层架构

```text
┌──────────────────────────────────────────────────────────────┐
│ API / CLI / Batch ingress                                    │
├──────────────────────────────────────────────────────────────┤
│ Orchestration：任务、权限、超时、幂等、审计                   │
├───────────────┬──────────────────────┬───────────────────────┤
│ extract/      │ query/               │ verify/               │
│ 文本→claim    │ 问题→Intent→Query     │ claim→Rule IR→检查     │
├───────────────┴──────────────────────┴───────────────────────┤
│ contracts/：schema、本体、版本、错误码、证据与结果协议        │
├──────────────────────────────────────────────────────────────┤
│ graph/：Assertion 规范存储、物化视图、图查询                  │
├───────────────────────┬──────────────────────────────────────┤
│ DB adapter             │ Solver/model adapter                │
└───────────────────────┴──────────────────────────────────────┘
```

### 2.1 控制面与数据面

- **控制面：** 任务提交、状态、版本、配置、模型/提示模板版本、能力矩阵、审计日志。
- **数据面：** chunk、节点、claim、Assertion、Rule IR、查询结果、验证报告与 provenance map。
- 控制面元数据不能替代数据面证据；仅有任务 ID 或数据库行 ID 不构成原文支持。

### 2.2 同步与异步

- 小型意图路由、缓存命中查询和已编译检查允许同步调用。
- 批量抽取、数据库导入、冷路径查询和 SMT 检查使用异步任务合同：提交返回 `job_id`，客户端通过状态接口获取结果。
- 所有任务都必须有超时、取消和幂等键；超时返回 `unknown`/`timeout`，不得伪装成通过。

## 3. 技术选择（MVP 基线）

| 领域 | MVP 基线 | 选择理由 | 明确边界 |
| --- | --- | --- | --- |
| 数据合同 | 版本化 JSON Schema + 确定性 validator | 易于 fixture 测试、跨语言交换、可审计 | JSON 合法不等于事实正确 |
| 图存储 | Neo4j 兼容 LPG/Cypher 的适配器作为首个 PoC | 原生属性图、关系属性和 Cypher 生态成熟 | 非性能排名；许可证/TCO 需单独确认 |
| 规范断言 | 独立 `Assertion` 记录/节点；可选直接边物化 | 支持冲突并存、生命周期、证据集合 | 物化边不是规范历史 |
| 查询 | 统一 Intent/Query IR → 后端能力探测 → 方言编译 | 避免直接端到端吐 Cypher；可替换后端 | 两步优于端到端仍是待测假设 |
| 验证 | 图算法 + 区间抽象 + 有界 SMT | 先便宜筛选，再局部精化，控制求解器风险 | MVP 不提供无界全局证明 |
| SMT | Z3 adapter，私有 context/worker | 对受限整数/位向量约束可用，增量能力成熟 | 不承诺按约束数线性延迟 |
| 模型服务 | provider-neutral `Proposer` 接口；先使用可配置结构化输出 | 不把供应商 schema 子集写入语义合同 | 提示/解码策略可替换 |

Neo4j 只是部署基线，不是合同层依赖。若许可证、真实负载 PoC 或运维约束不满足 ADR 边界条件，应替换 `graph` adapter，而不改变抽取合同和 IR。

## 4. 部署形态

### 4.1 MVP：单租户/单机可复现服务

MVP 采用一个可本地运行的组合：API/任务编排进程、图数据库服务、模型调用适配器、验证 worker。所有外部依赖都通过适配器隔离；本地 fixture 可在无外部模型时使用确定性 proposer 完成合同和验证链路测试。

```text
Client
  │ HTTPS/CLI
  ▼
API + Orchestrator ── Job store / audit log
  ├── Extract worker ── Model provider (optional)
  ├── Query worker   ── Graph adapter ── Graph DB
  ├── Verify worker  ── Solver adapter ── Private solver contexts
  └── Version worker ── Snapshot / diff store
```

MVP 不做多租户安全边界、不做跨区域高可用、不做大规模队列容量承诺。命名空间只用于数据隔离语义，不替代认证、授权和网络隔离。

### 4.2 未来扩展方向

- 任务队列与 worker 横向扩展；
- 图存储热读视图与断言历史分离；
- 只读验证快照与可回滚导入；
- 多后端能力矩阵和方言编译；
- 版本影响路径缓存。

这些方向不改变 MVP 合同；任何增加量词、随机语义或新本体标签的扩展须先更新 schema 与 ADR。

## 5. 关键数据流

### 5.1 抽取与导入

```text
source document
  → source registration + chunking(versioned)
  → proposer (schema-constrained)
  → deterministic validator
  → ExtractionEnvelope(nodes/claims/uncovered)
  → assertion-id generation
  → Assertion history
  → optional hot projection
```

拒绝路径：schema 错误、证据不连续、domain/range 违反等进入诊断；语义有意义但未建模进入 `uncovered`，不进入已确认图事实。

### 5.2 查询

```text
question + scope
  → fast template lookup (optional)
  → intent/slot route
  → schema and backend capability check
  → Query IR
  → dialect compiler
  → graph execution
  → result + provenance chain + diagnostics
```

### 5.3 验证

```text
snapshot + check type + assumptions
  → selected assertions
  → rule IR (with source mappings)
  → structural/abstract pre-check
  → bounded SMT refinement
  → witness or proof metadata
  → result protocol
  → assertion → claim → chunk/span mapping
```

## 6. 关键一致性边界

| 边界 | 必须保持的性质 |
| --- | --- |
| chunk → claim | span 连续；限定词和原文单位不丢失 |
| claim → Assertion | 来源、版本、certainty、status 独立保存；冲突不覆盖 |
| Assertion → Rule IR | 只编译满足语义前提的 claim；缺字段显式降级 |
| Intent → Query | 只生成能力矩阵允许的查询；参数化，禁止字符串拼接注入 |
| solver result → report | 区分全局证明、有界无反例、反例、未知和未建模 |

## 7. 失效与恢复

- 模型拒答/格式错误：有限重试后返回契约错误，不写入确认事实。
- 图数据库不可用：任务失败或排队；不从缓存生成无 provenance 的“最新”事实。
- 求解器超时/资源耗尽：返回 `unknown`，保留输入规模、超时和 assumptions。
- 版本冲突：并存两个快照，禁止自动选择“更可信”版本。
- 部分批次失败：按 chunk 幂等重试，成功 chunk 可提交，但批次报告必须列出失败项。

## 8. 架构验收条件

1. 无模型调用也能用 fixture 跑通 `contracts → graph → verify` 的确定性链路。
2. 任一验证结论都能找到 Rule IR assertion mapping，继续找到 claim 和原文 span。
3. 替换图后端或求解器适配器不改变抽取 JSON、Rule IR 和结果协议。
4. 对同一输入重跑产生相同断言 ID、相同 schema 校验结果和可解释的版本差异。
5. 所有性能报告包含输入规模、硬件、冷/热、并发、理论片段五项上下文。

## 修订记录

| 版本 | 变更 |
| --- | --- |
| v1 (draft) | 初稿：分层、技术基线、部署形态、数据流、失效恢复与验收条件。 |
