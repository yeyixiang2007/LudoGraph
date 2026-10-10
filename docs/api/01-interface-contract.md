# 统一接口设计

- **状态：** v1 设计草案。
- **范围：** 抽取、导入、查询、验证、版本比较五类接口的统一请求参数、返回格式、错误码与版本管理。
- **传输：** MVP 可通过 HTTP/JSON、CLI JSON Lines 或内部函数调用承载同一合同；传输方式不改变字段语义。
- **安全提醒：** 文档给出的是接口合同，不是访问控制方案；namespace 不能替代认证与授权。

## 1. 版本模型

接口请求必须携带或由服务端补全以下四个版本，并在响应中原样回显：

| 字段 | 作用 | 变化示例 |
| --- | --- | --- |
| `contract_version` | API 信封与字段合同 | 新增响应字段 |
| `ontology_version` | 节点/谓词/domain/range/限定值 | 新增 canonical predicate |
| `ir_version` | Intent/Query IR/Rule IR 语义 | 新增时间或随机语义 |
| `schema_version` | 物理投影/索引/迁移 | Assertion 存储改变 |

四者可独立演进，但任何结果必须记录完整版本四元组。兼容矩阵由服务端发布；不能仅凭字符串版本号猜测兼容。

## 2. 统一信封

### 2.1 请求

```json
{
  "request_id": "req-opaque",
  "idempotency_key": "idem-opaque",
  "contract_version": "1.0.0",
  "context": {
    "game_id": "game-example",
    "system_id": "combat",
    "snapshot_id": "snap-001",
    "ontology_version": "2.0.0",
    "ir_version": "1.0.0",
    "schema_version": "1.0.0"
  },
  "operation": "extract|import|query|verify|diff",
  "payload": {},
  "options": {
    "timeout_ms": 5000,
    "dry_run": false,
    "include_provenance": true
  }
}
```

`request_id` 用于追踪；`idempotency_key` 用于可重试写操作，不是事实 ID。`game_id`/`system_id` 是语义 scope，不是安全凭据。

### 2.2 响应

```json
{
  "request_id": "req-opaque",
  "contract_version": "1.0.0",
  "versions": {
    "ontology_version": "2.0.0",
    "ir_version": "1.0.0",
    "schema_version": "1.0.0"
  },
  "status": "ok|partial|rejected|accepted|running|failed",
  "result": {},
  "diagnostics": {
    "warnings": [],
    "uncovered": [],
    "not_modeled": [],
    "trace_id": "trace-opaque"
  },
  "error": null
}
```

- `ok`：操作完成且没有影响结果的诊断；
- `partial`：完成但存在 `uncovered`/警告；
- `rejected`：输入或能力不满足，未产生确认结果；
- `accepted`/`running`：异步任务已接收/运行；
- `failed`：内部失败或依赖不可用。

接口成功不等于事实正确；验证报告的业务状态必须另由 `result.results[].status` 表示。

## 3. 抽取接口

### 3.1 `POST /v1/extractions`

请求 payload：

```json
{
  "source": {
    "source_id": "doc-001",
    "revision": "rev-001",
    "chunk_id": "chunk-001",
    "chunk_text": "...",
    "segmentation_version": "seg-1"
  },
  "scope": {"game_id": "game-example", "system_id": "combat"},
  "ontology_version": "2.0.0",
  "proposer": {"model_ref": "configured-provider", "prompt_ref": "extract-v1"}
}
```

响应 `result` 为 `ExtractionEnvelope`：

```json
{
  "ontology_version": "2.0.0",
  "scope": {"game_id": "game-example", "system_id": "combat"},
  "status": "complete|partial|no_facts",
  "nodes": [],
  "claims": [],
  "uncovered": [],
  "diagnostics": {"validation_errors": [], "model_ref": "..."}
}
```

`evidence.quote` 必须是 `chunk_text[start:end]` 的连续子串；不合格输出不能进入确认图谱。

## 4. 导入接口

### 4.1 `POST /v1/assertions:import`

请求 payload：

```json
{
  "extraction": {},
  "projection_mode": "assertion|direct_edge|both",
  "revision_policy": "idempotent_append",
  "dry_run": false
}
```

响应：

```json
{
  "imported": [{"assertion_id": "as_...", "action": "created|unchanged|superseded|rejected"}],
  "projection_revision": "proj-001",
  "provenance_complete": true
}
```

`direct_edge` 是物化热点投影，不替代 Assertion 历史；不同来源冲突不得覆盖。

## 5. 查询接口

### 5.1 `POST /v1/query`

请求 payload：

```json
{
  "question": "哪些动作消耗冰晶？",
  "scope": {"game_id": "game-example", "system_id": "combat", "snapshot_id": "snap-001"},
  "backend_profile": "neo4j-lpg-v1",
  "requested_provenance": true,
  "route_mode": "fast_or_dynamic"
}
```

成功结果：

```json
{
  "intent": {
    "kind": "fact_lookup",
    "slots": {"predicates": ["COSTS"], "names": ["冰晶"]}
  },
  "compiled": {
    "backend": "neo4j-lpg",
    "dialect": "cypher",
    "parameters": {},
    "query_ref": "compiled-opaque"
  },
  "rows": [],
  "provenance": [
    {"assertion_id": "as_...", "source_id": "doc-001", "chunk_id": "chunk-001", "start": 0, "end": 10, "quote": "..."}
  ]
}
```

服务端不得把任意用户字符串直接拼成标签、谓词或查询语句；schema 标识来自白名单，值使用参数绑定。

### 5.2 查询拒绝

超出 ontology、要求体验/文化推断、scope 缺失造成跨游戏歧义、后端不支持且没有等价降级时，返回 `status: rejected`、错误码 `QUERY_OUT_OF_ONTOLOGY`/`BACKEND_CAPABILITY_MISSING`，不得返回语义漂移的近似查询。

## 6. 验证接口

### 6.1 `POST /v1/verifications`

请求 payload：

```json
{
  "snapshot_id": "snap-001",
  "check_type": "economic_deadlock|state_conflict|numeric_extreme",
  "scope": {"game_id": "game-example", "system_id": "economy"},
  "assumptions": {
    "world": "open|closed",
    "time_frame": "explicit",
    "probability_semantics": "explicit|not_applicable",
    "exception_priority": "explicit",
    "wait_is_legal": true
  },
  "bound": {"kind": "steps", "k": 20},
  "selection": {"assertion_ids": []}
}
```

响应 `result`：

```json
{
  "job_id": "job-001",
  "check_type": "economic_deadlock",
  "results": [
    {
      "status": "proved|counterexample|bounded-no-counterexample|unknown|not-modeled|spurious-counterexample",
      "assumptions": {},
      "bound": 20,
      "witness": null,
      "missing_fields": [],
      "mapping": [{"solver_assertion": "a-1", "assertion_id": "as_...", "evidence_ref": "..."}]
    }
  ],
  "timing": {"queue_ms": 0, "solver_ms": 0, "total_ms": 0}
}
```

`bounded-no-counterexample` 必须带 `bound.k`，不得解释为全局安全。`unknown` 不得映射为通过。每个 witness 要能回放或明确标为 `spurious-counterexample`。

### 6.2 `GET /v1/jobs/{job_id}`

返回统一信封，`result` 为：

```json
{"job_id":"job-001","state":"queued|running|succeeded|failed|cancelled","progress":0.5,"result_ref":"...","failure":null}
```

任务超时返回 `failed` + `TIMEOUT`，验证语义状态仍由报告记录为 `unknown`。

## 7. 版本接口

### 7.1 `POST /v1/snapshots`

```json
{
  "scope": {"game_id": "game-example", "system_id": "combat"},
  "label": "release-candidate",
  "source_revision": "rev-002",
  "assertion_selection": {"status": ["active"]}
}
```

### 7.2 `POST /v1/version-diffs`

```json
{"from_snapshot":"snap-001","to_snapshot":"snap-002","include_impact_paths":true}
```

响应分别报告：

- `added`/`superseded`/`removed`；
- 受影响的查询和验证结论；
- `resource_value`、`goal_reachability`、`save_continuity` 三类兼容性，不合并为一个 `compatible` 布尔值；
- 需要重跑的任务。

MVP 不承诺自动迁移所有旧反例；只报告影响和需重跑项。

## 8. 错误码

错误码是稳定合同的一部分；新增码只能新增，不复用旧码表达新语义。

| HTTP/任务层 | 错误码 | 含义 | 客户端动作 |
| --- | --- | --- | --- |
| 400 | `INVALID_REQUEST` | JSON/必填字段/类型错误 | 修正请求 |
| 400 | `VERSION_UNSUPPORTED` | 版本不支持或兼容矩阵不允许 | 选择支持版本 |
| 400 | `SCOPE_REQUIRED` | 缺少或歧义 scope | 补充 game/system/snapshot |
| 422 | `SCHEMA_INVALID` | 输出结构不符合合同 | 不写入，检查诊断 |
| 422 | `ONTOLOGY_LABEL_INVALID` | 非 canonical 叶子标签 | 修正或进入 uncovered |
| 422 | `PREDICATE_INVALID` | 谓词不在白名单 | 修正 ontology/请求 |
| 422 | `DOMAIN_RANGE_VIOLATION` | 端点类型不匹配 | 不写入 |
| 422 | `EVIDENCE_INVALID` | quote 非 chunk 连续子串或边界非法 | 重新绑定证据 |
| 422 | `QUALIFIER_INVALID` | raw/unit/probability/direction 非法 | 保留 raw，补齐字段 |
| 409 | `CONFLICT_REQUIRES_REVIEW` | 版本/来源冲突需审核 | 并存并提交审核 |
| 409 | `IDEMPOTENCY_MISMATCH` | 同幂等键 payload 不同 | 使用新幂等键或调查 |
| 404 | `NOT_FOUND` | snapshot/job/assertion 不存在 | 检查引用 |
| 403 | `FORBIDDEN` | 认证主体无权访问 | 检查授权 |
| 422 | `QUERY_OUT_OF_ONTOLOGY` | 问题超出当前本体能力 | 显式降级/拒答 |
| 422 | `BACKEND_CAPABILITY_MISSING` | 方言不支持所需特性 | 选择后端或 fallback |
| 422 | `NOT_MODELED` | 语义缺字段，不能保守编译 | 补充假设/原文 |
| 429 | `RATE_LIMITED` | 请求受限 | 退避重试 |
| 500 | `INTERNAL_ERROR` | 未预期内部错误 | 带 trace 重试/报障 |
| 503 | `DEPENDENCY_UNAVAILABLE` | 数据库/模型/求解器不可用 | 稍后重试 |
| 504 | `TIMEOUT` | 超时 | 查询 job/report；不可视为通过 |

## 9. 兼容性与弃用

1. 旧客户端可忽略新增可选响应字段；服务端不得删除既有必填字段。
2. 改变字段语义、枚举含义、domain/range 或结果状态时递增 major。
3. 新增可选字段/新错误码通常递增 minor；修复文档拼写可递增 patch。
4. 弃用至少保留一个迁移窗口，并在响应 diagnostics 中返回 `deprecation`。
5. 物理数据库迁移不得改变历史 Assertion 的语义；迁移失败可回滚，投影可重建。

## 10. 接口验收

- 每种操作都有合法、缺字段、版本不兼容、能力缺失和超时 fixture。
- 查询结果包含完整 provenance；验证结果包含 assertion mapping。
- 任何 `not-modeled`、`unknown`、`bounded-no-counterexample` 都不会被客户端 SDK 映射为成功通过。
- 同一幂等键重试不产生重复 Assertion；不同 payload 被拒绝。
- 错误码文档、schema 与实现来源一致。

## 修订记录

| 版本 | 变更 |
| --- | --- |
| v1 (draft) | 初稿：统一信封、抽取/导入/查询/验证/版本接口、错误码和兼容性。 |
