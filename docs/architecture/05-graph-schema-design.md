# 图谱模式设计

- **状态：** v1 设计草案。
- **权威对齐文档：** `docs/LudoGraph 图谱数据模型设计.md`。
- **对齐原则：** 本文不重新定义本体；把权威文档的标签、谓词、限定值、证据、命名空间和投影选择整理为工程可执行的模式要求。任何新增标签/谓词须先修改权威模型文档并增加 schema 版本。

## 1. 计数裁决与范围

权威数据模型文档的叙述提到“25 个关系类型”，但其关系表逐项数出 **24 个唯一关系类型**。本 v1 以逐项列出的 24 个 canonical 谓词为准：

- 不凭空添加第 25 个谓词；
- 不把 `Assertion` 当作关系类型，它是断言的物理存储形态；
- 不把上位分类（`Entity`、`Mechanic` 等）当作可抽取叶子标签；
- 将“25/24”保留为 schema 治理待决事项，直到权威文档明确第 25 项的名称、domain/range 和语义。

这是一项**规格澄清**，不是对既有文档的静默修订。机器可读 schema、validator 白名单和数据库约束必须由同一份生成源产生。

## 2. 节点标签

抽取输出只允许以下 17 个 canonical 叶子标签；括号中的上位类型只用于组织或数据库额外标签，不可直接作为抽取类型。

| 上位组 | canonical 叶子标签 | 语义边界 |
| --- | --- | --- |
| `Entity` | `Character` | 角色/单位 |
| `Entity` | `Item` | 可持有对象 |
| `Entity` | `Facility` | 建筑/舱室/设施 |
| `SocialContext` | `Organization` | 阵营、公司、部门或命名组织 |
| `Mechanic` | `Action` | 可执行动作 |
| `Mechanic` | `Event` | 离散事件 |
| `Mechanic` | `Location` | 地点 |
| `Mechanic` | `Level` | 具有流程或难度语义的区域 |
| `Mechanic` | `Effect` | 机制效果 |
| `Mechanic` | `StatusEffect` | 可施加、移除或持续的状态 |
| `Mechanic` | `Trait` | 稳定词条/特性 |
| `Mechanic` | `Condition` | 规则条件 |
| `Mechanic` | `Rule` | 可原子化的规则结构 |
| `Mechanic` | `System` | 子系统/机制系统 |
| `Measure` | `Resource` | 可流通、累积、消耗或交换的资源 |
| `Measure` | `Attribute` | 描述对象状态的数值维度 |
| `Conceptual` | `Concept` | 有明确名称且参与规则表达、但不属其他类型的概念 |

### 2.1 节点属性

节点属性当前只允许原文明示的：

| 属性 | 类型/约束 | 说明 |
| --- | --- | --- |
| `kind` | 原文字符串，可选 | 如“行动牌” |
| `code` | 原文字符串，可选 | 如“DM02” |
| `tier_raw` | 原文字符串，可选 | 等级原文；不隐式转数值 |

此外，物理实现必须有内部稳定 ID、标签、scope、source/chunk provenance，但这些是存储元数据，不得冒充策划事实属性。任意数值状态使用 `Attribute` 节点与 `HAS_ATTRIBUTE` 断言表达，不能塞进自由格式 properties。

## 3. 关系白名单（24 项）

下表是 v1 的完整 canonical 谓词清单。具体 domain/range 矩阵必须由同一 schema 文件维护；下表保留权威文档的语义边界。

| 语义组 | 谓词 | 方向/语义 |
| --- | --- | --- |
| 资源与效果 | `COSTS` | source 使用/动作支付 object 成本 |
| 资源与效果 | `CONSUMES` | source 一般消耗或移除 object |
| 资源与效果 | `PRODUCES` | source 产出 object |
| 资源与效果 | `RESTORES` | source 恢复 object |
| 资源与效果 | `MODIFIES_ATTRIBUTE` | source 改变 object 的数值或资源属性；方向由 qualifier 表示 |
| 战斗与交互 | `DEALS_DAMAGE` | source 对具名受击角色/设施造成明确伤害 |
| 战斗与交互 | `APPLIES_STATUS` | source 对 object 施加短时状态效果 |
| 战斗与交互 | `COUNTERS` | source 明示克制 object |
| 战斗与交互 | `RESISTS` | source 明示抵抗 object |
| 战斗与交互 | `TARGETS` | source 明示指定 object 为目标 |
| 规则与进程 | `REQUIRES` | source 的前置条件是 object |
| 规则与进程 | `TRIGGERS` | source 触发 object |
| 规则与进程 | `UNLOCKS` | source 解锁 object |
| 规则与进程 | `UPGRADES_TO` | source 升级/转化为 object |
| 规则与进程 | `SPAWNS` | source 生成 object |
| 规则与进程 | `HAS_ACTION` | source 拥有或配置 object 动作 |
| 归属与组成 | `BELONGS_TO` | source 属于 object |
| 归属与组成 | `CONTAINS` | source 包含 object |
| 归属与组成 | `HAS_ATTRIBUTE` | source 具有 object 属性 |
| 归属与组成 | `HAS_TRAIT` | source 具有 object 稳定词条/特性 |
| 空间与事件 | `LOCATED_IN` | source 位于 object |
| 空间与事件 | `OCCURS_IN` | source 事件发生在 object |
| 空间与事件 | `ADJACENT_TO` | source 与 object 明确相邻；语义对称 |
| 约束 | `CONFLICTS_WITH` | source 与 object 明确互斥/不能共存；语义对称 |

### 3.1 方向与对称性

- 除 `ADJACENT_TO`、`CONFLICTS_WITH` 外均按有向边处理。
- 对称谓词只保存一条有证据的断言；查询层可在语义上按无向关系匹配，但不得物理复制反向断言。
- 不提供泛化 `RELATED_TO`；不明确或不支持的语义进入 `uncovered`。
- `COSTS`（明确支付）与 `CONSUMES`（一般消耗/移除）不可互换。
- `DEALS_DAMAGE`（明确伤害+具名受击对象）与 `MODIFIES_ATTRIBUTE`（降低恶意、资源或数值属性）不可互换。
- `APPLIES_STATUS`（短时施加）与 `HAS_TRAIT`（稳定拥有）不可互换。

## 4. 断言合同

### 4.1 抽取顶层

```json
{
  "ontology_version": "2.0.0",
  "scope": {"game_id": "示例游戏", "system_id": "战斗"},
  "status": "complete",
  "nodes": [],
  "claims": [],
  "uncovered": []
}
```

`status`：

- `complete`：当前 chunk 的可表示事实已抽取；
- `partial`：存在 `uncovered`；
- `no_facts`：没有可抽取事实。

### 4.2 Claim 字段

```text
Claim {
  local_id: string
  subject: local node id
  predicate: canonical predicate
  object: local node id
  qualifiers: Qualifiers
  certainty: explicit | possible | planned | negated
  evidence: Evidence
}
```

`certainty` 表示原文语气，不表示模型置信度；`status` 是持久断言生命周期，取 `active`/`deprecated`/`rejected`，二者必须分开。

### 4.3 限定字段

| 字段 | 保存规则 |
| --- | --- |
| `quantity` | 必有原文 `raw`；可附 `value`、`unit` |
| `probability` | 必有 `raw`；只有明确解析到 0–1 才附 `value` |
| `weight` | 保留原文权重；禁止归一化为概率 |
| `duration` | 保留原文 `raw`；可附数值和原文单位 |
| `condition_text` | 保留明示规则成立条件 |
| `trigger_text` | 保留明示触发时点 |
| `cycle_text` | 保留明示周期；不得自行转换成 tick/回合/工作日 |
| `direction` | 只取 `increase`/`decrease`/`set`/`transfer`/`reset`/`unknown` |

### 4.4 证据

每个节点、claim、uncovered 项至少一条证据：

```json
{"quote":"每次使用消耗2枚冰晶","start":123,"end":133}
```

`quote` 必须等于当前 chunk 的连续子串 `chunk[start:end]`。不得拼接多个片段或引用 chunk 外材料。连续性检查是硬约束；语义蕴含仍可能需要人工/NLI 审核。

## 5. 命名空间、身份和生命周期

- `scope.game_id`、`scope.system_id` 用于隔离图谱数据；`system_id` 可为 `null`。
- 没有 game ID 时，工具可使用来源文档名作为临时隔离命名空间。
- `n1`、`c1` 仅是一次抽取内局部 ID，不是持久 ID。
- 持久 `assertion_id` 应由 `(game_id, system_id, source_id, chunk_id, local claim id 或 source span, revision)` 的规范化 tuple 确定性生成。
- 同名节点不得自动跨 chunk、文档或游戏合并；entity-link 是后续 planned 能力，需候选证据和人工审核。
- 不同来源的冲突 claim 并存，不互相覆盖；修订通过新增版本和 `supersedes` 表达。

## 6. 物理投影

### 6.1 Assertion 规范存储

推荐以独立 `Assertion` 记录/节点作为规范存储，以支持：

- 同一端点相同谓词的多来源断言；
- `certainty` 与生命周期 `status` 独立更新；
- 证据集合、审计、废弃和修订链；
- 冲突并存。

连接方式可为：

```text
(subject)-[:ASSERTS_SUBJECT]->(Assertion)-[:ASSERTS_OBJECT]->(object)
```

这两个连接是物理实现关系，不属于 24 个抽取 canonical 谓词。

### 6.2 直接边热点投影

可把 canonical predicate 投影成带属性的有向边，以支持常见一跳查询；必须复制 qualifiers、certainty、evidence、source/chunk、scope 和 ontology version。投影必须可重建、带 projection revision，不能成为唯一历史来源。

## 7. 约束与索引

### 7.1 合同约束

1. label 必须属于 17 个叶子标签；
2. predicate 必须属于 24 项白名单；
3. domain/range 必须匹配；
4. claim 的局部引用必须存在；
5. evidence span 合法且 quote 连续；
6. quantity/probability/duration 的 `raw` 非空；
7. `probability.value`（若有）在 `[0,1]`；
8. `direction` 属于枚举；
9. `certainty`、断言 `status`、chunk `status` 属于各自枚举；
10. 对称谓词不得复制反向断言；
11. `assertion_id` 对同一规范化输入稳定；
12. scope 不可缺失（`system_id` 可为 null）。

### 7.2 推荐索引

索引名称为逻辑建议，具体语法由后端 adapter 生成：

| 索引 | 用途 |
| --- | --- |
| `assertion_id` 唯一索引 | 幂等导入、修订查询 |
| `(game_id, system_id, status)` | 当前快照过滤 |
| `(ontology_version, predicate)` | 本体/谓词过滤 |
| `(source_id, chunk_id)` | 来源与证据回指 |
| `(subject_ref, predicate)` | 一跳事实查询 |
| `(object_ref, predicate)` | 反向条件查询 |
| `revision`/`supersedes` | 版本审计 |
| `node scope + canonical label + stable id` | 节点隔离与身份查找 |

索引不是访问控制；namespace 过滤必须与真实认证、授权和租户边界分开。

## 8. 数据字典

| 对象 | 字段 | 含义 | 约束 |
| --- | --- | --- | --- |
| Scope | `game_id` | 游戏命名空间 | 必填或使用明确临时来源命名空间 |
| Scope | `system_id` | 子系统命名空间 | 可 null |
| Node | `local_id` | chunk 内节点引用 | 只在 envelope 内唯一 |
| Node | `type` | 17 个叶子标签之一 | 禁止上位标签 |
| Node | `kind`/`code`/`tier_raw` | 原文明示节点属性 | 禁止自由属性扩张 |
| Claim | `predicate` | 24 项 canonical 谓词之一 | domain/range 校验 |
| Claim | `qualifiers` | 条件、数值、时间、概率等 | 保留 raw，不隐式换算 |
| Claim | `certainty` | 原文断言语气 | 四态枚举 |
| Evidence | `quote/start/end` | 原文连续证据 | chunk 内、可复核 |
| Assertion | `assertion_id` | 持久断言 ID | 确定性、含来源与 revision |
| Assertion | `status` | 生命周期 | active/deprecated/rejected |
| Assertion | `supersedes` | 修订关系 | 不覆盖旧断言 |
| Chunk | `status` | 抽取完整性 | complete/partial/no_facts |
| Uncovered | `reason_code` | 未覆盖原因 | 枚举、可统计 |
| Version | `ontology_version` | 本体合同版本 | 与 contract/IR/schema 版本分别记录 |

## 9. 模式演化规则

- 新增节点标签或谓词：更新权威模型、机器 schema、validator、适配器能力矩阵、文档和 fixture，并递增 ontology version。
- 改变既有谓词 domain/range 或限定语义：视为破坏性变更，禁止复用旧版本号。
- 仅增加可选字段：可在兼容规则允许时递增 minor；仍需兼容性测试。
- 删除标签/谓词：先 deprecated，再保留读取与迁移期，不物理删除历史断言。
- 任何 schema 变更必须有 ADR 或更新相关 ADR。

## 修订记录

| 版本 | 变更 |
| --- | --- |
| v1 (draft) | 初稿：17 标签、24 谓词、断言合同、限定值、证据、索引与演化规则。明确记录权威文档 25/24 计数差异。 |
