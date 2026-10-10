# 详细设计

- **状态：** v1 设计草案。
- **范围：** 抽取、图谱导入、NL2Cypher 路由、规则 IR、Z3 三类检查、结果回映射。
- **原则：** 下文的算法是可实现的 MVP 设计，不是已经运行并验证的实现；性能数字仍以实测为准。

## 1. 公共类型与接口

### 1.1 版本化上下文

```text
ExecutionContext {
  contract_version: String
  ontology_version: String
  ir_version: String
  schema_version: String
  run_id: String
  source_revision: String
  assumptions: AssumptionSet
}
```

`AssumptionSet` 至少包含：开放/闭世界语义、单位是否已解析、缺省值策略、例外优先级、时间框架、随机语义、状态深度 `k`。缺少会改变结论的假设时，编译器返回 `not-modeled`，不擅自填默认值。

### 1.2 统一接口签名

```text
extract_chunk(request: ExtractionRequest) -> ExtractionEnvelope
validate_extraction(envelope: ExtractionEnvelope, chunk: Chunk) -> ValidationReport
project_assertions(envelope: ExtractionEnvelope, mode: ProjectionMode) -> ImportReport
route_query(request: QueryRequest) -> RoutedQuery | QueryRefusal
compile_rule_ir(request: VerificationRequest) -> RuleIR | NotModeled
run_check(ir: RuleIR, check: CheckType, options: CheckOptions) -> VerificationReport
build_version_diff(a: SnapshotRef, b: SnapshotRef) -> VersionDiff
```

所有接口以 JSON 合同承载；宿主语言的类、异常和数据库对象不能泄漏到跨模块合同。

## 2. 本体约束抽取

### 2.1 处理阶段

```text
S1 source registration
  → S2 deterministic chunk segmentation
  → S3 candidate attribution (rule/intent/experience)
  → S4 ontology-constrained candidate extraction
  → S5 evidence/certainty binding
  → S6 deterministic validation + uncovered classification
  → S7 review queue and persist
```

只有规则事实（主要落在规则、状态和机制层）可以进入确认图谱。设计意图和玩家体验可以作为有来源的 claim/外部陈述，但不得被自动转换为规则事实或形式化性质。

### 2.2 proposer 的合同

模型或规则 proposer 接收：

```json
{
  "chunk_id": "chunk-001",
  "chunk_text": "...",
  "scope": {"game_id": "...", "system_id": "..."},
  "ontology_version": "2.0.0",
  "output_schema_ref": "extraction-envelope/v1"
}
```

只允许生成候选的 `nodes`、`claims`、`uncovered`，不能直接生成数据库查询、SMT 公式或持久 ID。约束解码/API structured output 只负责格式层；本体和事实证据仍由确定性 validator 与人工审核处理。

### 2.3 确定性校验算法

```text
validate(envelope, chunk, ontology):
  check top-level version/scope/status
  for node in nodes:
    require leaf_label(node.type)
    require evidence.quote == chunk[start:end]
    require allowed_properties(node.properties)
  for claim in claims:
    require subject/object refer to local node IDs
    require predicate in ontology
    require endpoint labels satisfy domain/range
    require certainty in four-state enum
    require evidence span is contiguous and in chunk
    validate qualifier raw/value/unit without implicit conversion
  for item in uncovered:
    require reason_code and contiguous evidence
  reject duplicate local IDs, dangling references, illegal reverse inference
```

验证失败的输出不能被写入确认断言；可恢复的候选应保留原始响应与诊断，供重试或人工查看。

### 2.4 证据与保守拒绝

`EvidenceCheck` 只证明引用边界和连续性，不声称自动证明自然语言蕴含。若 quote 相关但不能支持 claim 的全部方向、条件或数量，则：

- 降低 `certainty` 不能替代缺失证据；或
- 写入 `uncovered`/人工审核队列；
- 不得由 validator 依据常识补全条件。

### 2.5 抽取伪代码

```text
extract_chunk(req):
  candidates = proposer.generate(req, constrained_schema(req.ontology_version))
  structural = contracts.validate(candidates, req.chunk)
  if structural.has_hard_errors:
      return rejected_envelope(structural.diagnostics)
  for c in candidates.claims:
      c.assertion_id = null  # import 阶段生成
      if not evidence_contiguous(c.evidence, req.chunk):
          move_to_uncovered(c, EVIDENCE_NOT_CONTIGUOUS)
  return normalize_without_semantic_rewrite(candidates)
```

## 3. 图谱导入与断言生命周期

### 3.1 规范表示

规范表示是独立 `Assertion` 记录/节点：

```text
Assertion {
  assertion_id
  subject_ref
  predicate
  object_ref
  qualifiers
  certainty
  status: active | deprecated | rejected
  source_id
  chunk_id
  evidence
  scope
  ontology_version
  revision
  supersedes[]
}
```

直接关系属性是热点查询的物化投影，不是审计历史。若投影后端不能保存相同端点的多条相同谓词关系，必须回退到 Assertion 形态，不能覆盖冲突来源。

### 3.2 确定性 ID

```text
make_assertion_id(a):
  key = normalize(game_id, system_id, source_id, chunk_id,
                  local_claim_id_or_span, revision)
  return "as_" + sha256(utf8(canonical_json(key)))
```

哈希输入必须包含来源/位置/版本；仅哈希三元组会把冲突说法错误合并。节点持久 ID 同样不能仅按显示名称生成。

### 3.3 幂等导入

1. 校验 envelope。
2. 为每个 claim 生成 assertion ID。
3. 若相同 ID 已存在且 payload 相同，返回 `unchanged`。
4. 若 payload 不同，拒绝静默覆盖，创建新 revision 并建立 `supersedes`。
5. 若不同来源给出相反 claim，分别保存为 active（或交审核），不做自动裁决。
6. 生成可选 hot projection，并记录投影版本。

## 4. NL2Cypher 路由与编译

### 4.1 Intent IR

```text
Intent {
  kind: fact_lookup | path_lookup | aggregate | provenance | verification_input
  scope: {game_id, system_id, snapshot_id?}
  slots: {
    node_types[], predicates[], names[], source_filters[],
    path_length?, group_by?, measures?, temporal_filters?
  }
  constraints[]
  requested_provenance: bool
}
```

Intent 必须是封闭枚举；`slots` 只能引用当前 ontology version 的标签、谓词和字段。不能把一个任意 Cypher 字符串藏进 `slots` 作为逃逸通道。

### 4.2 两步路由

```text
route(question, context):
  if template_cache.hit(fingerprint(question, context)):
      return cached_intent_and_query
  intent = intent_router.classify(question, allowed_intents, context)
  if intent.refused:
      return QueryRefusal(OUT_OF_ONTOLOGY)
  caps = backend.capabilities()
  if not supports(caps, intent.required_features):
      return QueryRefusal(BACKEND_CAPABILITY_MISSING,
                          fallback=explain_or_alternate_path(caps, intent))
  query_ir = query_compiler.compile(intent, ontology, caps)
  return RoutedQuery(intent, query_ir, compile_diagnostics)
```

MVP 的模型输出只决定候选 intent；查询编译器以参数绑定生成 Cypher，禁止把用户字符串直接拼入标签、谓词或语句。动态标识符必须从 schema 白名单映射，动态值使用参数。

### 4.3 Query IR 到 Cypher

```text
QueryIR {
  match_patterns[]
  where_predicates[]
  projections[]
  aggregations[]
  order_limit?
  provenance_required
  parameters
}
```

编译器先做：类型/谓词白名单检查、scope 强制注入、参数化、结果 provenance 字段注入；再输出方言查询。数据库执行返回断言 ID，`graph/` 负责补齐 `chunk → span` 回指链。

### 4.4 路由拒绝

以下情况必须拒绝或返回 `not-modeled`：问题要求体验/文化意义推断；要求未在 ontology 中的谓词；要求后端不支持且无等价降级；scope 缺失且会造成跨游戏混查；要求把 `uncovered` 当作确认事实。

## 5. 规则 IR 与保守编译

### 5.1 Rule IR 最小结构

```text
RuleIR {
  entities[]
  resources[]
  actions[]
  states[]
  transitions[]
  guards[]
  effects[]
  quantities[]
  time_frames[]
  random_processes[]
  assumptions[]
  source_map: IRNode -> AssertionEvidenceRef[]
  approximation: exact | over | under | unresolved
}
```

每个 IR 节点和表达式都需携带 source map。claim 缺少明确量词、时间、单位、概率、默认值或例外优先级时，IR builder 可生成 `unresolved` 节点，但不能把它当作精确模型继续输出 `proved`。

### 5.2 三分编译契约

- **过近似（over-approximation）：** 保留所有真实行为并可能引入假行为。若过近似模型证明安全，可在声明假设后支持安全结论；若发现违规，需回放确认，可能是 spurious。
- **欠近似（under-approximation）：** 只保留一部分可执行行为。找到反例可作为真实漏洞候选，找不到不代表全局安全。
- **未决定（unresolved）：** 缺失语义可能改变结论，返回 `not-modeled`/`unknown`，列出缺失字段。

## 6. D1 经济死锁检查

### 6.1 模型

对资源 `r∈R`、操作 `a∈A`、步 `t∈[0,k]`：

- `x[r,t] ∈ Int`：库存；
- `fire[a,t] ∈ Bool`：该步是否执行；
- `consume[a,r]`、`produce[a,r]`：非负系数；
- `enabled[a,t]`：前置条件与资源足够的合取。

基本约束：

```text
x[r,0] = initial[r]
fire[a,t] -> enabled[a,t]
x[r,t+1] = x[r,t]
               - Σ_a fire[a,t] * consume[a,r]
               + Σ_a fire[a,t] * produce[a,r]
x[r,t] >= 0
```

死锁候选在 `k` 步检查：

```text
not goal(state[k])
AND for every action a: not enabled(a, k)
```

还需显式声明「等待是否是合法动作」；不能把玩家主动选择等待直接判成死锁。

### 6.2 两个不可混淆的预检查

1. **资源依赖/SCC：** 发现环和候选子图，不能证明死锁。
2. **净产出流/LP：** 判断是否存在满足守恒条件的流，不能证明存在合法顺序。

只有库存非负、前置条件、动作顺序和目标状态联合检查，才形成 D1 的反例候选。

### 6.3 D1 输出

- `counterexample`：给出步序、动作、每项库存变化和来源映射；
- `bounded-no-counterexample`：给出 `k`，只表示该边界内无反例；
- `unknown`：超时、非线性或假设不足；
- `not-modeled`：概率/时间/例外等未定义。

## 7. D2 状态机冲突检查

### 7.1 单状态机

对机器 `m` 的状态集合 `Q_m` 建立布尔变量 `s[m,q,t]`。每个时刻加入：

```text
exactly_one_q(s[m,q,t] for q in Q_m)
```

状态迁移由事件、guard、优先级与更新原子性决定。互斥冲突可编码为：

```text
exists t, q != q': s[m,q,t] AND s[m,q',t]
```

在正确 one-hot 构造下此式不可满足；它仍适合作为 schema/编码回归检查，不等于可达性证明。

### 7.2 多状态机联合转移

对共享事件、锁、优先级和同时更新建立联合迁移 `T((s1,...,sn), event, (s1',...,sn'))`。禁止简单地分别检查每台机器后推断联合系统无冲突，因为竞争可能只出现在同步层。

目标不可达：逐步增加 `k`，检查 `goal(s[k])` 是否可满足。`unsat` 只限当前 `k`；若要全局结论，需无界证明或明确的有限状态穷举条件。

## 8. D3 数值极值检查

### 8.1 类型选择

| 运行时语义 | IR/SMT 类型 | 说明 |
| --- | --- | --- |
| 数学整数、无机器溢出 | `Int` | 可检查上下界，不模拟位宽溢出 |
| 有限宽带符号/无符号整数 | `BitVec(w)` | 直接检查 wraparound，与程序语义一致 |
| 明确实数/比率 | `Real` | 需说明舍入和精度 |
| 语义未说明 | 不编译 | 返回 `not-modeled` |

### 8.2 边界公式

对变量 `v_i(t)` 和边界 `L_i,U_i`：

```text
violation := v_i(t) < L_i OR v_i(t) > U_i
```

对属性更新 `v' = f(v, inputs)`，区间抽象先传播上下界。若抽象发现违反，进入 SMT 精化；若抽象证明不违反，仅在抽象包含和边界假设明确时报告对应范围结论。机器位宽场景另行检查数学整数结果与 `BitVec` 结果差异。

“数值爆炸”“归零”不是自动定义的性质，必须由配置边界、单调性或有限时间窗口具体化。

## 9. Solver worker 与结果协议

### 9.1 并发模型

每个 worker 私有 solver/context；跨 worker 只传递可序列化 Rule IR、SMT-LIB 或任务 JSON。不要把 AST、solver 或 context 作为任务对象跨线程/进程传输。长任务有墙钟超时和资源限制；结束后可重建 solver，避免无限增量状态。

### 9.2 结果映射

```text
SolverOutcome {
  solver_status: sat | unsat | unknown | timeout
  bound: int | null
  model_or_core: serialized | null
  assertion_ids[]
  assumptions[]
}
```

映射规则：

- `sat` 且 witness 满足回放：`counterexample`；
- `sat` 但回放失败：`spurious-counterexample`（若来自过近似）；
- `unsat` 且是无界/完备有限模型：`proved`；
- `unsat` 仅在深度 `k`：`bounded-no-counterexample`；
- `unknown`/timeout：`unknown`；
- 无法保守编译：`not-modeled`。

不能把求解器 `unsat` 直接翻译为业务层「安全」，必须附模型范围和 assumptions。

## 10. 反例回译

反例记录最小可读路径：检查类型、版本、状态深度、动作/事件序列、资源/状态/数值快照、触发断言 ID、原文来源 span、回放状态。回译失败时不得丢弃求解器模型；报告 `unknown` 或 `spurious-counterexample` 并保留序列化模型供诊断。

## 11. 详细设计验收

- 合法/非法抽取 fixture 能覆盖所有白名单和证据失败路径。
- 两步路由对 schema 外请求拒绝，对支持请求产生参数化查询。
- D1、D2、D3 每项至少有正例、真实反例和边界/未知例。
- 每个输出状态都能由一个明确的 solver/编译路径产生，且含 assumptions。
- 随机抽查任意验证结果，可沿 source map 回到原文连续 span。

## 修订记录

| 版本 | 变更 |
| --- | --- |
| v1 (draft) | 初稿：公共接口、抽取算法、NL2Cypher、规则 IR、三类检查与结果映射。 |
