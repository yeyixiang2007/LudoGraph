## 设计目标

LudoGraph 面向不同玩法类型的游戏策划资料，例如卡牌、塔防、经营和叙事探索。模型要能用一套稳定结构描述角色、物品、规则、资源、空间与它们之间的玩法事实，同时保留事实来自哪段原文。

核心选择是把“事实”保存在图谱或检索层，把语言模型用于抽取、查询翻译和基于证据的表达。模型不把策划案事实记入参数，也不在抽取时补写原文没有说的因果、数值换算或实体身份。

```text
策划原文 chunk
    │
    ├── 节点 nodes：事实涉及的对象
    ├── 断言 claims：对象间有方向、有类型的事实
    └── 未覆盖 uncovered：有意义但暂不能可靠表示的内容
             │
             ├── 本体白名单与 domain/range 校验
             ├── 原文证据与限定值校验
             └── 后续投影为有向属性图
```

## 本体分类

本体采用有向属性图（Directed Property Graph）。上位类型用于组织语义类别；抽取输出必须使用具体的 canonical 叶子标签，避免把不同对象都标成宽泛的 `Entity` 或 `Mechanic`。

| 语义分组                 | Canonical 节点标签                                                                                  | 用途                         |
| -------------------- | ----------------------------------------------------------------------------------------------- | -------------------------- |
| 具象实体 `Entity`        | `Character`、`Item`、`Facility`                                                                   | 角色/单位、可持有对象、建筑/舱室/设施       |
| 社会关系 `SocialContext` | `Organization`                                                                                  | 阵营、公司、部门或其他明确命名的组织         |
| 玩法机制 `Mechanic`      | `Action`、`Event`、`Location`、`Level`、`Effect`、`StatusEffect`、`Trait`、`Condition`、`Rule`、`System` | 可执行动作、离散事件、空间、状态、条件、规则和子系统 |
| 度量 `Measure`         | `Resource`、`Attribute`                                                                          | 可流通/累积的资源，以及描述对象状态的数值维度    |
| 概念 `Conceptual`      | `Concept`                                                                                       | 有明确名称且参与规则表达、但不适合其他类型的概念   |

分类边界有意保持清晰：`Resource` 可被消耗、产出或交换，`Attribute` 是描述状态的维度；`StatusEffect` 表示可施加、移除或持续一段时间的状态，`Trait` 表示较稳定的词条或特性；`Location` 是地点，具有流程或难度语义的区域用 `Level`。`Concept` 不是未知类型的兜底标签。

节点 `properties` 目前只允许原文明示的 `kind`、`code` 和 `tier_raw`。例如，“行动牌”可作为 `kind`，“DM02”可作为 `code`，等级文本原样放入 `tier_raw`。任意数值状态不塞入自由格式属性字典，而由 `Attribute` 节点及 `HAS_ATTRIBUTE` 关系表达。

## 关系模型

关系具有方向和 canonical 类型。每种关系都在 ontology 中声明允许的源类型 `domain`、目标类型 `range` 及可用限定字段；校验器拒绝白名单外的谓词或不符合端点类型的连接。

| 语义组   | 关系类型                                                                | 表达内容                      |
| ----- | ------------------------------------------------------------------- | ------------------------- |
| 资源与效果 | `COSTS`、`CONSUMES`、`PRODUCES`、`RESTORES`、`MODIFIES_ATTRIBUTE`       | 支付成本、消耗/移除、产出、恢复、改变数值或资源  |
| 战斗与交互 | `DEALS_DAMAGE`、`APPLIES_STATUS`、`COUNTERS`、`RESISTS`、`TARGETS`      | 明示伤害、施加状态、克制、抵抗、指定目标      |
| 规则与进程 | `REQUIRES`、`TRIGGERS`、`UNLOCKS`、`UPGRADES_TO`、`SPAWNS`、`HAS_ACTION` | 前提、触发、解锁、升级/转化、生成、拥有/配置动作 |
| 归属与组成 | `BELONGS_TO`、`CONTAINS`、`HAS_ATTRIBUTE`、`HAS_TRAIT`                 | 归属、包含、具有属性、具有词条/状态        |
| 空间与事件 | `LOCATED_IN`、`OCCURS_IN`、`ADJACENT_TO`                              | 位于、事件发生地点、明确相邻            |
| 约束    | `CONFLICTS_WITH`                                                    | 明确互斥或不能共存                 |

几组容易混淆的语义需要分开：明确支付使用 `COSTS`，一般消耗或移除使用 `CONSUMES`；明确造成伤害且有具名受击角色/设施时使用 `DEALS_DAMAGE`，降低恶意、资源或其他数值使用 `MODIFIES_ATTRIBUTE` 并标明方向；短时施加效果使用 `APPLIES_STATUS`，稳定拥有的特性使用 `HAS_TRAIT`。关系集合不设泛化的 `RELATED_TO`，不确定或暂不支持的语义进入 `uncovered`。

`CONFLICTS_WITH` 和 `ADJACENT_TO` 在语义上对称，但只保存一条有证据的断言。其他关系按有向边处理，不能因为存在一条关系就自动生成反向关系。

## 抽取记录：nodes、claims 与 uncovered

单个 chunk 的抽取输出有固定顶层结构：

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

节点表示实体或概念，claim 表示一条带证据的事实断言。claim 的 `subject` 和 `object` 引用当前输出里的节点局部 ID；`predicate` 是关系类型；`qualifiers` 保存条件、数值、时序等限定；`certainty` 表示原文的断言语气；`evidence` 保存原文依据。

例如原文“冰霜女巫拥有技能极寒风暴。极寒风暴消耗2枚冰晶。”会形成 `Character`、`Action`、`Resource` 三个节点，以及 `HAS_ACTION` 和 `COSTS` 两条 claim。第二条 claim 的数量限定保留 `raw: "2枚"`，并可同时记录可解析的 `value: 2` 与 `unit: "枚"`。每条 claim 分别附上支持它的连续原文片段。

复杂但可原子化的规则可建为 `Rule` 节点，再用多条 claim 表达前提、动作和效果。这样可以保留规则各部分之间的结构，而不是把整段规则塞进节点描述或一条无差别的大边。

`uncovered` 用于记录有规则意义、但当前不能可靠表示的文本，例如关系类型尚不支持、指代不明确、占位内容或实体类型无法判断。每项包含原文片段、原因代码和证据。它是待扩展或待审核队列，不作为已确认事实导入图谱。chunk 状态 `complete`、`partial`、`no_facts` 分别表示完整抽取、存在未覆盖内容、没有可抽取事实。

## 限定值与证据

数值字段不只保存归一化结果，也保留原文形式，避免单位、范围和表达精度丢失。

| 限定字段 | 保存约定 |
| --- | --- |
| `quantity` | 必须有原文 `raw`；可附数值/区间 `value` 和原文单位 `unit` |
| `probability` | 保留 `raw`；只有能明确解析到 0–1 时才附 `value` |
| `weight` | 保留原文权重；不得归一化成概率 |
| `duration` | 保留原文 `raw`；可附数值和原文单位 |
| `condition_text`、`trigger_text` | 保留规则成立条件或触发时点的明示文本 |
| `cycle_text` | 保留结算周期原文；不得自行换算成 tick、回合或工作日 |
| `direction` | 仅使用 `increase`、`decrease`、`set`、`transfer`、`reset`、`unknown` |

每个节点、claim 和 uncovered 项都必须至少有一条 evidence。`evidence.quote` 必须是当前输入 chunk 的连续原文子串；不能改写、拼接，也不能引用 chunk 外材料。节点名、别名、允许的节点属性值和各限定字段的原文部分同样需要有输入依据。这样每个查询结果都可以回到对应来源检查，而不是只得到一个无法审计的三元组。

`certainty` 的取值为 `explicit`、`possible`、`planned`、`negated`，描述原文语气，不表示模型自己的置信度。原文互相矛盾时保留各自的 claim 与来源，不在抽取阶段替策划者裁决。

## 命名空间与身份

`scope.game_id` 和 `scope.system_id` 用于隔离不同游戏和子系统。若样本没有提供 `game_id`，当前工具以来源文档名作为临时隔离命名空间；无法确认子系统时 `system_id` 为 `null`。同名节点不会因为名字相同就自动跨 chunk、跨文档或跨游戏合并。

`n1`、`c1` 这类 ID 只在一次抽取输出内唯一，不是数据库持久 ID。持久化时应由导入层生成稳定的断言 ID，并保留来源 chunk。跨文档实体对齐属于后续 `entity_link` 流程，需结合候选匹配和人工审核；本体把它列为 planned 能力，当前不允许仅按同名自动合并。

## 图数据库投影与实现状态

本体可以投影到 Neo4j、Kùzu 等 labeled property graph（LPG）数据库：canonical 节点标签成为标签，canonical 谓词成为有向关系类型；上位类型可作为额外标签，例如 `:Entity:Character`。抽取输出仍只使用叶子标签 `Character`。

一条 claim 投影为一条有向关系时，`qualifiers`、`certainty`、证据、来源 `source/chunk_id`、命名空间及 `ontology_version` 必须一并保留。若数据库需要保存同一对节点间的多条相同类型关系、不同来源的冲突断言或完整断言生命周期，可将 claim 存成独立 `Assertion` 记录，并连接到 subject/object；这属于存储实现选择，不改变抽取合同。不同来源的冲突事实应作为不同断言保存，不互相覆盖。

## 设计取舍

- 使用统一上位本体和严格叶子标签，在复用跨玩法结构的同时减少每个项目自造类型的漂移。
- 用方向、谓词白名单和 domain/range 提高数据可校验性；代价是暂时不能表达的机制必须放入 `uncovered`，后续扩展本体后再处理。
- 将数值、条件和证据保存在 claim 上，避免只靠裸三元组丢失规则语境；直接查图时也必须保留来源信息。
- 对原文没有明确支持的关系不做推断，对同名节点不做自动合并，优先保证可追溯性；跨文档综合能力依赖未来的实体对齐与审核流程。
- 把抽取数据合同与具体图数据库分离，使 schema 可先被校验和用于训练，再由后续导入层决定关系属性或 Assertion 的物理存储方式。