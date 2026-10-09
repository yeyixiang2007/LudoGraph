# LUDO-6：LudoGraph 验证层形式化技术路线调研

> 调研日期：2026-10-09
> 检索范围：SMT/Z3 官方资料与性能研究、Petri 网死锁分析、有限状态机/模型检查、抽象解释与区间分析、知识图谱/本体到逻辑约束的映射先例；重点评估三类游戏规则验证、增量与并发工程方案。本文是技术调研与建议，不修改既有设计或本体。

## 1. 背景

LudoGraph 目标是把策划规则及图结构用于验证游戏经济死锁、状态机冲突和数值极值。关键并非“把整个图交给 Z3”，而是建立语义明确的中间表示（IR），将其分解成可判定、规模可控的约束问题。求解器返回的 `sat`、`unsat`、`unknown` 分别代表找到反例/模型、在所编码模型中无反例、或资源/理论限制下无法判定；`unknown` 不能视为通过。

**事实：** Z3 支持多种 SMT 理论及增量检查；抽象解释和 Petri 网分别提供适用于数值近似和资源流/可达性的成熟形式化基础。**推断：** 对本项目，混合式验证（图算法与抽象分析先筛，有限的 SMT 精化后验）比“全图、全规则、一次性 SMT”更符合延迟与可解释性目标。

## 2. 国内外现状

### 2.1 经济系统与死锁

Petri 网以库所、变迁、标识（token 数量）描述资源与操作；变迁的输入弧刻画消耗/前置资源，输出弧刻画产出。其可达性分析能够提出目标状态是否可达的问题；siphon（虹吸集）/trap 等结构用于资源分配系统的活性与死锁分析。相关研究覆盖资源分配和制造系统，且已有面向游戏任务/关卡的 Petri 网建模案例，但这不是商业游戏经济验证的直接性能证据。[Petri-net siphon survey](https://cedric.cnam.fr/fichiers/art_3836.pdf)；[游戏任务 Petri 网研究检索源](https://www.researchgate.net/publication/220800018_A_Petri_Net_Approach_for_the_Modeling_and_Analysis_of_Video_Games)

SMT 的优势是可结合布尔条件、整数资源量、线性算术及位向量，表达“某组资源库存和操作可否到达违反性质的状态”。一般 Petri 网可达性问题会有状态空间爆炸，因此结构分析、界限和抽象很重要；不应把 SCC 或资源依赖环直接等同于死锁——循环可能可持续，死锁取决于初始资源、产消量、操作前置条件和可执行顺序。

### 2.2 状态机及图结构验证

有限状态机可表示为迁移系统 `(S, I, T)`：状态集合、初始状态、迁移关系。模型检查常针对可达性、安全性（如互斥状态不同时成立）和活性（如终将离开等待状态）进行检查。状态空间有限且变量域小的时候显式枚举/模型检查往往更直接；SMT 有界模型检查把长度为 `k` 的迁移展开成布尔/算术公式，适合快速找有界反例，但单独使用固定深度不能证明任意深度可达/不可达。

TLA+ / TLC、Promela / SPIN、Alloy 等是可选的状态建模/模型检查工具。Z3 官方教程介绍了求解器的断言、push/pop 和 assumptions 用法；工具选择应由模型形态决定，而非预设所有状态机都必须转 SMT。[Programming Z3](https://theory.stanford.edu/~nikolaj/programmingz3.html)

### 2.3 数值静态分析

抽象解释以具体语义的保守近似计算程序/系统性质；区间域为每个变量维护上下界，并通过转移函数传播。循环通过不动点迭代求不变量，使用 widening 保证终止、必要时 narrowing 提高精度。区间分析易扩展且能保守检查越界，但丢失变量间关系（例如 `x=y`）可能导致误报。经典理论基础见 Cousot & Cousot 1977。[论文 PDF](https://wcl.cs.rpi.edu/pilots/library/papers/TAGGED/3936-Cousot_Cousot%20(1977)%20-%20Abstract%20Interpretation.pdf)

对离散运算、整型溢出，应明确采用数学整数语义还是引擎实际位宽语义：前者用 `Int`，后者用 Z3 `BitVec`，两者对溢出行为不同。概率、非线性增长和复利需单独建模/近似；不应将浮点、概率和无界循环隐式假设为精确整数线性算术。

### 2.4 本体/知识图谱到 SMT 的先例与语义鸿沟

关系逻辑已被研究用于关系结构建模、Alloy 和 OWL 类本体的约束求解映射；例如 Relational Constraint Solving 讨论有限关系及其 join、product、transitive closure 等运算。[论文](http://theory.stanford.edu/~barrett/pubs/MRT+17.pdf)；[Satisfiability modulo relations](https://exa.ai/library/publication/9cdnrm8jgll)。OWL 描述逻辑也有将本体蕴含归约为知识库可满足性的问题研究。[OWL entailment 相关资料](https://scispace.com/pdf/reducing-owl-entailment-to-description-logic-satisfiability-ncjiytfq1o.pdf)

这类先例证明“关系/本体可映射到逻辑”不是新概念，但不意味着任意 LudoGraph 子图能无损转换成 SMT。主要语义差异：开放世界（没有边不表示边不存在）与闭世界数据库查询；存在性/基数限制与有限图实例；关系的推理闭包与显式边；时间、概率、版本有效期和自然语言模态；以及属性值的单位、舍入和缺省值。映射必须将这些语义选择显式化，不能将 Neo4j/Cypher 的匹配结果直接解释成逻辑完整模型。

## 3. 关键发现：三类检查的形式化方案

以下是推荐的建模草案，不代表已在 LudoGraph schema 上验证；变量和谓词应经项目语义确认后落为 IR 模板。

### 3.1 经济死锁 / 不可持续闭环

#### 模型变量

- 资源 `r ∈ R`、操作/配方 `a ∈ A`、库存 `x[r,t] ∈ Int`；离散步 `t=0..k`。
- `fire[a,t] ∈ Bool` 表示该步是否执行操作；配方系数 `consume[a,r] ≥ 0`、`produce[a,r] ≥ 0`，可为常量或从图谱读取的版本化数据。
- 可选 `enabled[a,t]` 表示前置条件成立；`goal[t]` 表示目标/推进条件满足。

#### 约束

- 初始库存：`x[r,0] = initial[r]`，且所有步 `x[r,t] ≥ 0`。
- 可执行性：`fire[a,t] ⇒ x[r,t] ≥ consume[a,r]`，并且满足解锁/状态前提。
- 资源转移：`x[r,t+1] = x[r,t] - Σa fire[a,t]*consume[a,r] + Σa fire[a,t]*produce[a,r]`。同一步并发操作需定义同步语义，最小原型可限制每步最多一个操作。
- 编码“死锁反例”：对每个 `a`，`¬enabled[a,k]`，同时 `¬goal[k]`，并要求前面每步转移合法。对不允许停顿的模型，可另设停滞判定；不要将玩家可主动等待误判为死锁。

#### 求解目标与算法

- 有界反例搜索：查询上述死锁条件是否 `sat`，对 `k=1..K` 增深；SAT 给出具体资源/操作轨迹。
- 资源依赖图先做 SCC、可达性与净产出分析。对候选闭环再做 Petri 网标识/可达分析或 SMT；强连通不是死锁证明。
- 若需证明无界活性，优先找线性不变量/正权势函数或使用 Petri 网结构性 liveness 条件；也可把递归转移编码成 CHC 并尝试 Spacer。仅有有限深度 UNSAT 只能说明深度 `K` 内未找到反例。
- 目标是“生产/消耗循环无法启动”时，定义目标产出资源 `g`，查询是否存在满足库存约束的执行轨迹到达 `x[g] ≥ q`；`unsat` 在给定边界/模型假设下表明不可达。

### 3.2 状态机冲突 / 不可达状态

#### 模型变量

- 状态机 `M` 的状态布尔量 `s[m,q,t]`，输入事件 `e[t]`；若状态互斥，采用 one-hot 状态编码或显式互斥约束。
- 图节点对应状态，边对应迁移；迁移守卫条件转成布尔/算术谓词 `guard[e]`。

#### 约束

- 初始状态唯一：`Σq s[m,q,0] = 1`（布尔 one-hot 表示）。
- 迁移关系：`s[m,q,t] ∧ guard(q→q',e,t) ⇒ s[m,q',t+1]`，并定义无迁移时的停留/错误语义。
- 互斥冲突检查：查询 `s[m,q,t] ∧ s[m,q',t]`（`q≠q'`）是否可满足；SAT 是冲突轨迹。
- 不可达：目标状态 `s[m,q*,k]` 与初始/迁移关系合取，逐步增加 `k`；SAT 给出到达路径。若全有限状态空间已经完整枚举则可给出不可达结论；固定深度 UNSAT 不可推广到无界。
- 多状态机同步时，为共享事件、锁、优先级和更新原子性建立显式联合转移；否则可能制造不真实的冲突或遗漏竞争。

**检测方法建议**：无条件图可先做 BFS/DFS 可达性、SCC/死状态和图结构检查，成本通常低且结果直观；有数值守卫、跨机约束、动态条件时再用 SMT 有界展开。无界性质可考虑 TLA+/TLC、SPIN 或 CHC/归纳不变量。状态冲突性质若可直接由 schema 约束（例如 one-hot）保证，构造时强制比事后求解更稳健。

### 3.3 数值极值 / 越界、爆炸与归零

#### 模型变量

- 每个数值属性 `v_i ∈ Int` / `Real` / `BitVec(w)`，按运行时语义选择；时间步 `t` 和版本参数作为常量或受约束变量。
- 转移式 `v_i(t+1)=f_i(v(t), action, parameters)`；外部输入范围和触发条件必须显式定义。

#### 约束与目标

- 设合法区间 `[L_i,U_i]`，查询可达状态中的违规：`v_i(t)<L_i ∨ v_i(t)>U_i`。SAT 提供输入/状态反例。
- 检查溢出：若程序用 `w` 位整数，则按位向量运算验证结果与期望数学整数之间的差异，或检查结果符号/饱和边界；不应仅用无界 `Int` 推断机器溢出。
- 爆炸检查需先定义可操作指标：最大增速、达到阈值步数、长期有界性或净增量；“爆炸”不是自带数学定义的性质。
- 线性/仿射更新优先区间不动点传播，循环用 widening；区间抽象报疑点时用关系域（差分约束/多面体）或 SMT 路径查询精化。对有界深度做优化（最大化 `v_i` 或最小化到达阈值步数）可求具体极值/反例。

**结果解释**：抽象解释给保守上界，越界可能是误报；求解器 SAT 反例需验证可执行路径；超时/unknown 要标为未判定。将区间传播作为全量快筛，SMT 用于疑难局部和反例解释，是合理的分工。

## 4. Z3 接入与高并发方案

### 4.1 图到约束的编译建议

建立确定性的、版本化的编译器流水线：

1. 从图查询取带来源、版本、单位与类型的候选子图；保存查询快照/哈希。
2. 通过 schema/type checker 检验节点关系类型、数值单位、缺失值及版本一致性；拒绝语义不完整输入，不让 LLM 直接生成任意 SMT-LIB。
3. 使用三类稳定模板将 IR 编译成 SMT；每条约束保留回映射（SMT assertion ↔ 图边/原文出处），便于反例与 UNSAT core 解释。
4. 先执行图算法/区间分析；必要时调用 Z3；记录逻辑、变量数、断言数、理论组合、超时、solver version 与结果。
5. 输出 `safe within assumptions` / `counterexample` / `unknown`，附假设、范围、反例轨迹；禁止将有限深度无反例标成全局安全。

### 4.2 性能边界与“毫秒级”修订

SMT 的运行时间没有可按约束条数通用推导的界限；同样数量的断言可因理论、公式结构、变量耦合、量词、非线性及 SAT/UNSAT 查询方向而相差巨大。TU Delft 对 20 个实数约束基准进行的研究报告中，部分 QF_NRA 实例平均耗时为秒级（MBO 默认策略非超时实例均值约 50.47 秒，另一策略约 12.99 秒），另一些基准表现则截然不同；作者强调策略和基准限制，不支持按“约束数”承诺延迟。[论文](https://repository.tudelft.nl/file/File_dde6c259-4a73-4078-a900-255bb7f95ff9)

Z3 官方 `Programming Z3` 说明增量查询依靠上下文复用，但增量模式可能改变求解策略；现实案例中，加入 `push` 后同一类实例从 0.03 秒升至 151.32 秒，issues 中还记录了 incremental solving / preprocessing 的性能差别。这些是特定案例而非普遍基准，却足以说明 push/pop 并非必然加速。[Z3 增量教程](https://theory.stanford.edu/~nikolaj/programmingz3.html)；[Z3 issue #1141](https://github.com/Z3Prover/z3/issues/1141)；[Z3 issue #7441](https://github.com/Z3Prover/z3/issues/7441)

**结论与指标建议（推断，依据上述性能差异及模型检查经验）：**

- “毫秒级”仅承诺给固定模板、受限理论（无量词 QF_LIA/QF_BV 或简单 QF_LRA）、有界小子图的热路径目标，并以本项目目标硬件的 P95/P99 基准验收；不能作通用 Z3 SLO。
- 首阶段可将轻量本地检查目标定为 P95 ≤ 10ms，复杂 SMT 查询目标定为 P95 ≤ 100ms；这是待测的工程目标而非已证实能力。超时应返回 `unknown/pending`，复杂无界分析进后台任务。
- 用 1k/10k/100k 节点边的图输入、不同断言数和理论类别构造基准，报告建模、图查询、求解独立耗时及总耗时，并分别统计 SAT/UNSAT/unknown、P50/P95/P99、吞吐量和内存。不能仅报告平均值或公式条数。
- 单次变化时 assumptions 可便于条件开关；push/pop 可用于局部作用域。但应比较三种方式：新 solver/一次性查询、assumptions、push/pop；固定逻辑及数据分布做本机实测后选型。缓存可复用解析/图索引与基准子图，不应假定 solver 内部搜索知识在任意跨请求复用都获益。

### 4.3 并行与上下文隔离

Z3 的对象归属 Context；官方 Python 并行示例说明并行工作应使用独立 context，且创建/访问共享 context 对象并发不安全。[Z3 parallel.py](https://github.com/Z3Prover/z3/blob/master/examples/python/parallel.py) C++ API 亦以 Context 管理 Z3 对象。[Context API](https://z3prover.github.io/api/html/classz3_1_1context.html)

建议服务端采用无共享 solver 的 worker pool：每个 worker 持有私有 Context/solver，任务间不跨 context 传递 AST；以可序列化 SMT-LIB 或项目 IR 在 worker 间传输。按经济子系统/状态机/规则版本拆分任务，设置 CPU/内存配额、超时与取消；线程或进程模型依语言绑定及部署测量决定，必要时进程隔离以控制 native solver 崩溃/内存。每个查询有 request id 和幂等缓存键，限制单租户并发，避免高峰时无界排队。

增量复用宜限定在“同一模板、固定基底、反复切换少量条件”的 worker 内，并监测 solver 状态膨胀与尾延迟。不同逻辑/子系统共享长期 solver 可能导致断言累积和隔离问题；定期重建 solver。Z3 的增量能力存在，不等于所有查询都应 push/pop。

## 5. 对本项目的具体影响

1. **将验证输入定义成有类型 IR，而不是通用图转 SMT。** 每个量需有单位、整数/实数/位宽、缺省值语义、版本范围、来源置信状态；每条业务规则需有前提、动作、效果、并发/时序语义。
2. **验证分层**：图遍历先检测依赖环、不可达、孤立状态；区间分析扫描属性上下界；Petri/状态机模型表达资源与离散迁移；Z3 精化跨条件、反例路径和算术关系。
3. **明确证明边界**：优先上线有界反例与有限状态完全枚举；无界结论必须依赖不变量、归纳证明或适用的专用模型检查器，不要把有界 UNSAT 混同于安全证明。
4. **将数据语义与证据链一并编译**：规则从 claim 到逻辑须保留来源文本、抽取置信度、审核状态、版本及映射表。语义不明的 claim 不可强行编码，应返回“未建模/待确认”。
5. **先离线/CI 验证，再评估交互延迟**：前置阶段以结果正确性、覆盖率和超时率为主；编辑器同步路径只运行已基准确认的轻量规则，复杂求解异步执行。
6. **用项目数据建基准**：当前外部数据不能给出适用于 LudoGraph 的约束规模阈值。性能目标必须基于真实子图、真实规则分布和目标机器实测。

## 6. 风险与未知

### 最高风险环节

最高风险不是 Z3 API 本身，而是**从知识图谱 claim 到形式化语义的正确、保守编译**。若抽取将“通常”“每周重置”“概率掉落”“可选消耗”等语义压成错误的确定性约束，求解器仍会对错误模型给出正确答案。开放世界/闭世界差异、缺失事实、单位、时间/版本及并发更新均可能让模型与游戏实际行为不一致。这个风险贯穿抽取、本体、IR 和验证结果解释，不能由换求解器解决。

### 可替代或互补方案（不依赖 SMT）

- **Petri 网工具/结构分析**：资源流、配方依赖、死锁候选，适于离散 token 语义；比通用 SMT 更贴近资源消费，但一般可达性仍可能状态爆炸。
- **显式模型检查**：TLC、SPIN 对有限离散状态系统提供状态枚举与时序性质检查；状态规模可控时更易解释，状态空间大时需抽象/对称约简。
- **图算法**：BFS/DFS、SCC、拓扑排序、依赖闭包适合确定性结构属性，通常无需 SMT；但不能处理任意复杂守卫和数值语义。
- **抽象解释/区间传播**：适用于数值范围的保守静态分析，便于批量扫描；精度不足可能误报，关系性质需更强抽象域或精化。
- **仿真、属性测试与统计模型检查**：适合概率/随机游戏经济和动态生成内容，提供经验性风险而非对所有路径的证明；需报告样本量与置信度，不可宣称完备。

这些方法是互补分工，不是“完全不需要形式方法”。推荐初期以图算法 + 区间分析 + 有界模型检查为验证骨架，Z3 用于约束丰富的局部精化；当状态机为主可选 TLC/SPIN，当资源 token 语义自然可选 Petri 网工具。选择依据应是各类真实工作负载的准确性、性能和解释成本对比。

### 尚未解决 / [unverified]

- 未找到可直接外推到 LudoGraph 的游戏经济 Z3 约束数—延迟曲线或端到端高并发实测；任何“毫秒级可达”具体规模均为 **[unverified]**，须项目基准验证。
- 未对当前 LudoGraph 本体、图数据库结构、语言绑定或目标硬件做代码/环境检查；本文给出的 IR 与并发设计是建议，不是现有实现事实。
- 经济闭环是否应把市场交易、玩家行为、赛季重置、随机掉落纳入一个模型取决于产品语义；范围未定义时不应作全局经济稳定性结论。
- 上述文献与官方资料覆盖基础方法和求解器行为，未证明其在本项目生产规模上满足吞吐量或可用性指标。

## 参考来源

1. Cousot & Cousot, *Abstract interpretation: a unified lattice model...*（1977）: https://wcl.cs.rpi.edu/pilots/library/papers/TAGGED/3936-Cousot_Cousot%20(1977)%20-%20Abstract%20Interpretation.pdf
2. Girard et al., *A survey of siphons in Petri nets*: https://cedric.cnam.fr/fichiers/art_3836.pdf
3. *Relational Constraint Solving in SMT*: http://theory.stanford.edu/~barrett/pubs/MRT+17.pdf
4. *Satisfiability modulo relations: theory and applications*: https://exa.ai/library/publication/9cdnrm8jgll
5. Z3, *Programming Z3*: https://theory.stanford.edu/~nikolaj/programmingz3.html
6. Z3 repository, Python parallel contexts example: https://github.com/Z3Prover/z3/blob/master/examples/python/parallel.py
7. Z3 C++ Context API: https://z3prover.github.io/api/html/classz3_1_1context.html
8. *Evaluating Z3's Performance on Real Number Constraints*: https://repository.tudelft.nl/file/File_dde6c259-4a73-4078-a900-255bb7f95ff9
9. Z3 GitHub issue #1141, push/pop performance example: https://github.com/Z3Prover/z3/issues/1141
10. Z3 GitHub issue #7441, incremental solving discussion: https://github.com/Z3Prover/z3/issues/7441
11. *Reducing OWL entailment to description logic satisfiability* (检索资料): https://scispace.com/pdf/reducing-owl-entailment-to-description-logic-satisfiability-ncjiytfq1o.pdf
12. *A Petri Net Approach for the Modeling and Analysis of Video Games* (检索入口): https://www.researchgate.net/publication/220800018_A_Petri_Net_Approach_for_the_Modeling_and_Analysis_of_Video_Games
