# LUDO-2：游戏设计理论与游戏本体对照调研

> **调研日期：** 2026-10-09  
> **检索范围：** LudoGraph 当前设计文档（`docs/LudoGraph 图谱数据模型设计.md`）、MDA 原始论文及 AAAI 页面、Game Ontology Project（GOP）官网及其代表性论文、Stanford Game Description Language（GDL）说明与规范、GDL-III、游戏时间性（Temporal Frames）论文、Sicart 的游戏机制定义、RMDA 游戏设计本体论文、玩家能动性本体论文、Unity 状态机官方文档，以及公开的游戏经济设计资料。检索以英文公开资料为主，未对商业内部本体、付费数据库或所有中文论文穷尽检索；未能直接核验的内容标记为 `[unverified]`。

## 1. 背景

LudoGraph 当前采用有向属性图，以 17 个 canonical 叶子节点标签和一组白名单关系表达策划文本中的玩法事实；数值、条件、时序、概率和证据主要放在 claim 的限定字段中，而不是任意节点属性中。这个方向与“抽取事实而非让模型补写规则”的目标一致，但需要回答两个不同问题：

1. 这些标签是否覆盖游戏系统中普遍存在的对象、动作、状态和规则？
2. 这些关系是否足以表达状态变化、经济流、时序、概率和玩家/代理人的行为？

本报告只作理论校验和扩展建议，不修改现有设计文档或本体定义。一个重要的基线事实是：当前设计文档标题和工单都称有 **25 个关系类型**，但文档表格逐项数得出 **24 个唯一关系类型**。这是本地设计文档的可复核计数，不是理论判断；应在主工单中确认是否有一个关系遗漏，或把版本号更正为 24。

## 2. 国内外现状

### 2.1 游戏设计理论提供的是不同观察层，而不是一套节点清单

MDA 将游戏拆成 Mechanics、Dynamics、Aesthetics：Mechanics 是数据表示和算法层面的组件，Dynamics 是机制在玩家输入和彼此输出作用下随时间运行的行为，Aesthetics 是玩家与系统交互时产生的期望情感反应（[Hunicke, LeBlanc & Zubek, MDA](https://www.cs.northwestern.edu/~hunicke/MDA.pdf)，pp. 2–5；亦见 [AAAI 页面](https://aaai.org/papers/ws04-04-001-mda-a-formal-approach-to-game-design-and-game-research/)）。因此 MDA 很适合说明“规则/动作如何导致状态变化，再影响体验”，但 Aesthetics 不是一条可从策划文本直接抽取的玩法事实边；把它当作 LudoGraph 的普通节点标签会混淆设计意图和系统事实。

Sicart 将 game mechanics 定义为“由代理人调用、用于与游戏状态交互的方法”，并明确区分 mechanics 与 rules：规则定义可能性空间和状态转换，机制则面向代理人的行动（[Defining Game Mechanics](https://gamestudies.org/0802/articles/sicart)）。这为 `Action`、`Rule`、`Condition`、状态变化之间的分工提供了比“所有机制都叫 System”更精确的依据。MDA/RMDA 研究也指出，现有游戏本体常偏分析视角，未必容易转换为设计工作流；该结论来自一篇提议性研究，不应视为已经统一的学界标准（[Junior & Silva, 2021](https://www.it.pt/Publications/DownloadPaperJournal/31734)）。

### 2.2 GOP 是可扩展的分析层级，GDL 是可计算的状态转移语言

GOP 官方把自己定义为从多个具体游戏分析中抽象出的、持续增长的层级概念框架，而不是唯一正确的分类；其顶层包括 Interface、Rules、Entity Manipulation、Goals（[GOP 官网](https://gameontology.org/)）。GOP 的价值在于提醒我们：`Goal`、玩家行动、规则、空间和交互是独立的分析维度；它并不要求 LudoGraph 逐字复制其层级。

Stanford GDL 则把游戏建模为有限状态图：存在初始状态、终止状态、角色、当前状态、合法动作、动作效果和每个角色的目标值。官方说明明确列出 `role`、`base`、`action`、`init`、`control`、`legal`、`goal`、`terminal` 等语义，并用规则描述动作对下一状态的影响（[GDL Overview](http://ggp.stanford.edu/overview/game_description.html)，[GDL Specification](http://ggp.stanford.edu/readings/gdl_spec.pdf)）。GDL 原始范围是有限、离散、确定性、完全信息的游戏；GDL-III 扩展到不完全信息和认知/知识游戏（[IJCAI: GDL-III](https://www.ijcai.org/proceedings/2017/177)）。这说明 LudoGraph 当前 `Rule`/`Action`/`Event` 结构可以覆盖一部分形式化规则，但不能假设 `Character` 代替 `Role`，也不能假设 `Effect` 自动等于“下一状态”。

### 2.3 时间、能动性和经济已被研究为独立维度

Zagal 与 Mateas 的 Temporal Frames 将游戏时间视为事件之间的关系，区分 real-world time、gameworld time、fictive time 和 coordination time；回合、轮次、tick、延迟行动和同时行动都属于协调时间语义（[A Unifying Framework for the Analysis of Game Temporality](https://users.soe.ucsc.edu/~michaelm/publications/zagal-digra2007.pdf)，pp. 1–5）。所以 `Event` + `OCCURS_IN` 不能充分表达“何时可做、何时结算、持续多久、是否在回合结束时触发”。

玩家能动性也不是普通 `Character` 的同义词。2023 年的 agency-centered ontology 工作明确以 mechanics、玩家能动性及两者关系为建模目标（[Mitchell et al., Towards an Agency-centered Ontology of Game Mechanics](https://dl.acm.org/doi/10.1145/3582437.3587201)）。这支持把玩家、AI、系统、队伍角色和它们的目标/意图作为 agent 维度，而不是把“谁做了动作”隐含在 `HAS_ACTION` 中。

经济设计实践通常以 sources/faucets 和 sinks/drains 追踪资源产生与消耗，并按玩家活动频次、目标进度和 grind 时间平衡收入与支出（[GameDeveloper, A Practical Guide Into Creating a F2P Game Economy](https://www.gamedeveloper.com/design/a-practical-guide-into-creating-a-f2p-game-economy---a-cake-recipe)）。这与 `PRODUCES`、`CONSUMES`、`COSTS`、`RESTORES` 的方向相符，但经济验证还需要周期、流量、所有者、汇率、库存和随机掉落等限定信息。

## 3. 关键发现

### 3.1 17 个节点标签的校验

下表是建议的 v2 处置。这里的“保留”表示保留为 canonical 叶子标签；不等于它可以无条件承载所有语义。

| 当前标签 | 建议 | 理论依据与边界 |
|---|---|---|
| `Character` | 保留 | 对应具名可行动的游戏内角色/单位；但不代替玩家、AI 控制器或抽象角色 `Role`。GDL 的 `role` 和 Sicart 的 agent 维度表明两者需分开。 |
| `Item` | 保留 | 适合可持有、移动、使用或交易的对象；同一对象若承担货币/库存计量角色，可同时参与 `Resource` 语义，但不能因“可消耗”就自动改成 Resource。 |
| `Facility` | 保留 | 建筑、商店、基地、工作站是可定位且提供功能的实体；与抽象地点和进度容器有明确区别。 |
| `Organization` | 保留 | 阵营、公司、部门等社会归属实体；GOP 的实体/规则/交互分层支持单独保留。 |
| `Action` | 保留 | 对应代理人调用的机制/动作；Sicart 的定义和 GDL 的 `action` 直接支持。必须补充执行者、可用条件和结果。 |
| `Event` | 保留 | 表示已经发生或被规则观察到的离散事件；不要与可供代理人调用的 Action 合并。 |
| `Location` | 保留 | 表示空间地点/区域；可由 `LOCATED_IN`、`ADJACENT_TO` 连接。 |
| `Level` | 保留 | 表示关卡、波次、章节或具有进度/难度语义的结构，不是 Location 的同义词。GOP 的层级化玩法分段研究支持保留进度维度。 |
| `Effect` | 保留但收窄 | 建议定义为一次动作/事件产生的结果或状态改变描述；不要把持续状态、概率分支和情绪体验都塞进 Effect。未来可将名称改为 `Outcome`，但本工单不改定义。 |
| `StatusEffect` | 保留 | 表示可施加、移除、持续、叠层或抵抗的状态；与一次性 Effect 的时间性质不同。 |
| `Trait` | 保留 | 表示相对稳定的定性特征；与可变化、可计算的 Attribute 分开。 |
| `Condition` | 保留为兼容标签，但默认降为限定项 | 逻辑上它通常是 Rule 的前提、Action 的可用条件或 Trigger 的谓词，而不是独立实体。仅在原文给它命名、复用或单独管理时建节点。该建议来自 GDL 的条件/规则结构，是本次工程推断。 |
| `Rule` | 保留 | 是状态转移、合法性、胜负、经济或叙事约束的载体；GDL 的规则语言和 Sicart 对 rules 的区分直接支持。 |
| `System` | 保留 | 表示战斗、经济、任务、建造等机制集合/子系统，而非某条规则或某个事件。它是设计组织层，不应承担所有未分类事实。 |
| `Resource` | 保留 | 表示可累积、流通、生产、消耗或交换的资源；经济 sources/sinks 模型直接支持。 |
| `Attribute` | 保留 | 表示对象的可测量维度/数值状态，如生命、速度、容量；应允许时间点、方向和单位限定。 |
| `Concept` | 不建议继续作为开放兜底叶子；vNext 建议废弃或改为受控概念引用 | 具名关键词、阵营理念、规则术语确实需要表达，但开放的 Concept 会逃避类型判定并降低召回/精度可审计性。建议保留旧数据兼容映射，同时把无法判定的内容放入 `uncovered`，把可复用术语放入受控词表。这是本次推断，不是 GOP 或 GDL 的强制结论。 |

**结论：**没有理由删除 `Action`、`Event`、`Rule`、`System`、`Resource`、`Attribute` 等核心标签；真正的冗余风险集中在 `Condition` 和开放式 `Concept`，以及 `Effect`/`StatusEffect` 的边界。`Effect` 与 `StatusEffect` 不宜简单合并：前者是结果，后者是可持续状态，时间语义不同。

### 3.2 建议新增的节点/语义维度

优先建议先增加为 claim 的受控限定或实体化结构，再决定是否升格为 canonical 节点；这样可以避免 17 个标签快速膨胀。

| 建议新增 | 解决的缺口 | 依据与优先级 |
|---|---|---|
| `Agent` / `Role` | 玩家、AI、系统、队伍、阵营控制者；表达“谁执行/控制/观察” | GDL 明确有 `role`/`control`，Sicart 明确允许人类或计算机代理人。**高优先级**。 |
| `Goal` / `Objective` / `Intent` | 玩家想达成的目标、任务目标、设计目标、代理人的意图 | GDL 有 `goal`，GOP 顶层有 Goals，能动性本体直接把 agency 作为核心。**高优先级**；不要从 Action 自动推断 Intent。 |
| `State` / `StateTransition` | 当前状态、初始/终止状态、迁移、可达性和状态机 | GDL 的 `init`、`true`、`next`、`terminal` 是明确先例；Unity 状态机也将 state、transition、condition 分开（[Unity State Machine Basics](https://docs.unity3d.com/6000.6/Documentation/Manual/StateMachineBasics.html)）。**高优先级**。可先将 Transition 作为 Rule 的结构化子项。 |
| `TimeFrame` / `Phase` / `Turn` / `Cycle` | 回合、轮次、tick、冷却、持续时间、赛季、结算窗口 | Temporal Frames 证明 real/gameworld/fictive/coordination time 不可由 Location 或 Event 单独替代。**高优先级**；时间值仍应保留 `raw`。 |
| `RandomProcess` / `ChanceOutcome` | 抽卡、掉落、暴击、随机事件、加权表和分支概率 | 当前 `probability` 限定能存数值，却没有表达“随机过程”和“互斥结果集合”的位置。**高优先级**；概率不是普通 Attribute，也不能把 weight 自动归一化为 probability。 |
| `Information` / `Observation` | 卡牌隐藏信息、迷雾、已知/未知、揭示与玩家视野 | 原始 GDL 是完全信息；GDL-III 说明不完全信息需要额外知识语义。**卡牌/叙事中优先**。 |
| `NarrativeBeat` / `Dialogue`（可选） | 叙事探索中的对话、线索、选择节点和叙事时间 | `Event` 可以表达发生的事，但不区分可选对话、线索证据和叙事结构。建议先作为 `Event`/`Concept` 的受控 kind，而非立即新增叶子。 |

### 3.3 关系类型的校验、缺口和去歧义

**建议保留现有关系，但写清 domain/range 和限定字段：**

- `COSTS` 与 `CONSUMES` 保留：前者表达支付/价格，后者表达实际消耗或移除；`COSTS` 不应暗示已发生扣除。
- `PRODUCES` 与 `SPAWNS` 保留：前者适合资源/结果产出，后者适合实体生成。掉落可另用 `DROPS`，不要把所有生成都写成 SPAWNS。
- `RESTORES`、`MODIFIES_ATTRIBUTE`、`DEALS_DAMAGE` 保留：分别区分恢复、一般数值改变和明确伤害。`DEALS_DAMAGE` 的 object 应是受击目标或可受伤实体，伤害数值放 qualifier。
- `APPLIES_STATUS`、`COUNTERS`、`RESISTS`、`TARGETS` 保留：它们分别描述施加状态、克制机制、抵抗效果和目标选择，不应因都涉及战斗而泛化。
- `REQUIRES`、`TRIGGERS`、`UNLOCKS`、`UPGRADES_TO` 保留：前置、触发、可用性解锁和进阶转化的时序/逻辑不同。
- `HAS_ACTION`、`HAS_ATTRIBUTE`、`HAS_TRAIT` 保留，但要区分“拥有/配置”与“在此状态实际可执行”；后者还需要 `Agent`、`LEGAL_IN` 或 `AVAILABLE_IN` 语义。
- `BELONGS_TO` 与 `CONTAINS` 保留但不可互相自动推断：前者是成员/归属，后者是空间或组成容器。`LOCATED_IN` 与 `OCCURS_IN` 也不可合并。
- `ADJACENT_TO`、`CONFLICTS_WITH` 可标记为对称关系；按当前设计只存一条有证据边，不自动生成反向断言。

**建议新增的关系（按优先级）：**

| 建议关系 | 用途 |
|---|---|
| `PERFORMED_BY` / `CONTROLLED_BY` | 将 Action/Event 与 Agent/Role 连接；补足“玩家意图和执行者”缺口。 |
| `AIMS_AT` / `PURSUES` / `SATISFIES_GOAL` | 表达代理人或规则面向的目标；不能从 `TARGETS` 推断玩家意图。 |
| `PRECEDES` / `FOLLOWS` / `DURING` / `ENDS_WITH` | 表达事件、阶段、回合和叙事时间关系；`OCCURS_IN` 只表达地点或容器不足以承载时序。 |
| `TRANSITIONS_TO` / `CHANGES_STATE` / `SETS_ATTRIBUTE` | 使状态机迁移和赋值与一般 `MODIFIES_ATTRIBUTE` 区分；若暂不加边，必须在 Rule/Effect 的结构化限定中提供等价字段。 |
| `HAS_OUTCOME` / `HAS_PROBABILITY` / `SAMPLED_FROM` | 表达一个随机过程的结果集合、概率和抽样表；概率值应保留原文和单位/范围。 |
| `REVEALS` / `HIDES` / `OBSERVES` | 支持卡牌、迷雾和不完全信息。 |
| `REWARDS` / `PENALIZES` | `PRODUCES`/`MODIFIES_ATTRIBUTE` 可以近似表达，但奖励/惩罚携带规则语用和目标归属；可先作为受控 kind，避免立即扩充。 |
| `DROPS` / `EQUIPS` / `USES` | 分别补足掉落、装备和使用关系；适用于卡牌和物品系统。优先级低于 Agent/时间/状态。 |

**当前关系的结构性问题：**

1. `REQUIRES` 太容易同时表示资源需求、前置条件、能力要求和信息要求，应通过 qualifier 或更窄的关系（如 `HAS_PRECONDITION`、`REQUIRES_RESOURCE`）消歧。
2. `TRIGGERS` 只说明因果触发，不说明触发时点、一次性/重复性、延迟和概率；必须配 `condition_text`、`cycle_text`、`duration` 或新的 TemporalFrame。
3. `UNLOCKS` 与 `HAS_ACTION` 的可用性边界需明确：解锁是进度事实，拥有动作是配置事实，当前可用还受状态/回合条件约束。
4. `CONFLICTS_WITH` 只说明互斥，不说明冲突是资源竞争、规则禁止、目标相反还是状态不能共存；至少应有受控 `conflict_kind`。
5. 关系清单按工单所称“25”校验时实际只有 24 项，遗漏项必须在进入实现前补齐或更正文档，避免 schema 版本和抽取白名单不一致。

### 3.4 不同玩法类型的覆盖情况

- **卡牌：**已有 `Item`、`Resource`、`Action`、`Effect`、`StatusEffect` 可覆盖牌、费用、打出和效果，但缺 `Agent/Role`、隐藏信息、抽样/洗牌/抽牌、牌库/手牌容器和回合结算。至少需要 `HAS_OUTCOME`/`HAS_PROBABILITY`、`REVEALS`、`DRAWS_FROM` 或等价结构。
- **塔防：**已有 `Facility`、`Location`、`Level`、`Event`、`SPAWNS`、`TARGETS`、`DEALS_DAMAGE` 较合适；缺波次/时间窗、路径顺序、敌人生成表、攻击冷却和状态机。`ADJACENT_TO` 不能替代路径或可达性。
- **经营：**已有 `Resource`、`Attribute`、`Facility`、`PRODUCES`、`CONSUMES`、`COSTS` 是最强的一组；缺所有者、周期、库存/容量、汇率、预算和来源/去向聚合。要验证经济死锁，必须保留每次流动的方向、时间尺度与条件。
- **叙事探索：**已有 `Event`、`Location`、`Level`、`Condition`、`Rule` 可表达部分任务链；缺 Agent/Intent、叙事时间、对话/线索、选择分支、知识状态和“已观察/已揭示”。`CONFLICTS_WITH` 不能替代剧情前置、角色动机或叙事互斥。

## 4. 对本项目的具体影响

### 4.1 建议的最小演进顺序

1. **先修正文档计数和语义合同：**确认 24/25 的事实；为每条关系补 domain/range、对称性、是否可传递、允许的 qualifier 和反例。
2. **先不扩大 17 个 canonical 标签的数量：**新增 `Agent`、`Goal`、`State`、`TimeFrame`、`RandomProcess` 可先作为受控结构或 claim qualifier 试点。若跨玩法数据证明其重复出现且需要被查询，再升格为叶子。
3. **把状态机作为一等结构测试：**每个状态转换至少支持 source state、action/event、condition、effect、target state、duration/phase；这比单纯新增一个 `State` 标签更重要。
4. **把“谁、何时、以何概率、为了什么”纳入 claim：**建议最小字段为 `agent`、`goal`、`temporal_frame`、`probability`、`outcome_set`、`condition`。原文没有这些信息时保持缺省或进入 `uncovered`，不从上下文补齐。
5. **建立跨玩法回归集：**至少各准备卡牌、塔防、经营、叙事探索四类样本，分别测试覆盖率、类型错误、时序、概率和证据可回溯性；不能只用战斗文本验证本体。

### 4.2 理论结论与工程推断的边界

**较接近学界共识或直接有来源支持的结论：**

- 游戏的规则、动作/机制、状态变化、目标和玩家体验是相关但不同的分析层；MDA、Sicart、GOP 和 GDL 都以不同方式支持这一分层。
- 游戏状态、行动合法性、初始/终止状态和转移是可计算游戏模型的核心；GDL 官方规范直接展示了这些语义。
- 时间不是只有一个“发生地点”字段；回合、轮次、tick、持续时间和叙事时间需要单独建模。
- 经济系统通常需要同时看资源来源与消耗；`PRODUCES`/`CONSUMES` 方向适合做第一层图模型。
- 不完全信息、玩家能动性和代理人目标不能被一个普通实体标签可靠替代；这是 GDL-III、agency-centered ontology 和相关研究明确关注的维度。

**本次对 LudoGraph 的推断，需用数据验证的结论：**

- `Condition` 默认作为 Rule/claim 限定而非节点，可减少节点噪声，但可能损失对命名条件的复用查询。
- 开放 `Concept` 会成为未知类型的兜底，因此应废弃为 canonical 叶子；这取决于 LudoGraph 的召回率目标，不是外部本体的强制规定。
- `Agent`、`Goal`、`State`、`TimeFrame`、`RandomProcess` 是比继续扩展 `Effect` 子类更优先的缺口；优先级来自当前 17 标签、GDL 和四类玩法的交叉分析。
- `REWARDS`、`DROPS`、`EQUIPS` 等是否需要独立关系，取决于下游查询和验证是否需要它们的语用差别；若仅做资源流分析，可先用受控 kind 和 qualifiers。

## 5. 风险与未知

1. **覆盖率风险：**GOP 明确是持续演进的研究框架，不能证明 17 个标签对所有商业游戏完备。当前结论是理论对齐，不是召回率实验。
2. **跨层混淆风险：**MDA 的 Aesthetics、玩家意图、叙事动机和设计目标不一定是可从规则事实推出的对象；把推断出的体验或意图导入图谱会违反当前“原文证据优先”的设计原则。
3. **概率验证风险：**保存概率数值不等于能够验证随机系统；需要区分概率、权重、独立性、条件概率、抽样是否放回和随机种子。当前设计文档未定义这些语义，相关结论应标 `[unverified]`。
4. **时间语义风险：**“每回合”“持续 3 秒”“下一波”“每天重置”可能分别属于 coordination、real-world 或 gameworld time；若只存一个 duration，会丢失结算时点。
5. **信息与代理人风险：**卡牌隐藏信息、玩家已知信息、AI 可见信息和系统真实状态可能不同；GDL 原始完全信息假设不能直接覆盖它们。
6. **关系爆炸风险：**一次性新增所有专门关系会提高抽取歧义和 schema 维护成本。推荐先用结构化 qualifiers、受控 kind 和可验证样本决定哪些关系必须升格。
7. **国内现状的不确定性：**本次公开检索未发现一个与 GOP/GDL 同等成熟、公开可核验且直接面向中文游戏策划事实抽取的统一中文游戏本体；这不是“国内没有相关研究”的证明，标记为 `[unverified]`，需要主工单另行补充中文文献检索。
8. **实现前的必测未知：**尚无本项目数据集支持“17 标签覆盖率”“新增维度带来的准确率提升”或“关系拆分降低歧义”的量化证据。应以标注集比较 baseline、扩展 schema 和 qualifiers 三种方案，而不是仅依据理论直觉定案。

## 6. 结论清单

- **建议保留：**17 个标签中的 `Character`、`Item`、`Facility`、`Organization`、`Action`、`Event`、`Location`、`Level`、`Effect`、`StatusEffect`、`Trait`、`Rule`、`System`、`Resource`、`Attribute`；其中 `Effect` 必须收窄为结果，`Condition` 只在命名/复用时建节点。
- **建议兼容保留但逐步降级：**`Condition` 作为 Rule/claim 的条件结构；`Concept` 作为旧数据兼容类型或受控词表引用，不再作为未知类型兜底。
- **建议新增维度：**优先 `Agent/Role`、`Goal/Intent`、`State/StateTransition`、`TimeFrame/Turn/Phase`、`RandomProcess/ChanceOutcome`；卡牌和叙事项目再增加信息可见性与叙事结构。
- **建议新增关系：**优先 `PERFORMED_BY`、`CONTROLLED_BY`、`AIMS_AT`、`PRECEDES`/`DURING`、`TRANSITIONS_TO`/`CHANGES_STATE`、`HAS_OUTCOME`/`HAS_PROBABILITY`、`REVEALS`/`OBSERVES`。`REWARDS`、`DROPS`、`EQUIPS` 可先试验为受控关系。
- **建议合并/删除：**没有证据支持合并 `Action` 与 `Event`、`Location` 与 `Level`、`Effect` 与 `StatusEffect`；它们在 agent、时间或进度语义上不同。应把 `Condition` 合并进 Rule/claim 结构，并在 vNext 废弃开放式 `Concept` 叶子，但保留迁移兼容，而不是立即破坏现有数据。
- **必须确认：**当前关系表列出的不是 25 而是 24 项；在 schema 版本发布前解决该计数/遗漏问题。

上述建议仅用于 LUDO-2 调研结论，不构成对现有设计文档的直接修改。
