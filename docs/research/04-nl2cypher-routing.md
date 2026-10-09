# LudoGraph 路由层：NL2Cypher 与端侧 SLM 技术路线调研

- **调研日期：** 2025-02-14
- **检索范围：** 公开论文与预印本、ACL Anthology、Neo4j 官方文档/仓库、Kùzu 官方文档、llama.cpp 公开基准与项目资料；重点检索 2024–2025 年的 Text2Cypher/NL2Cypher、端侧小模型、量化推理、意图路由、延迟和 Cypher 方言兼容性。本文只讨论路由层，不修改现有设计文档或本体定义。
- **证据标记：** “事实”指来源明确报告的结果；“推断”是基于事实对 LudoGraph 的工程判断；无法由公开资料直接核验的数值标为 **[unverified]**。

## 1. 背景

LudoGraph 的路由层要把自然语言问题转换为图查询，并把查询结果交给后续规则验证。这里有两个不同难度的任务：

1. **意图路由：** 判断用户是在查实体、关系、规则、数值、状态、版本，还是请求验证；确定图谱子域、槽位和查询模板。
2. **查询编译：** 在给定 schema、实体/关系候选和安全约束后生成可执行 Cypher，并进行语法、schema 和结果校验。

两者不应混同。意图标签是低熵、可枚举的分类问题；NL2Cypher 是 schema linking、自然语言消歧、多跳图推理和程序生成的组合问题。把两者都交给一个端侧通用生成模型，可能减少编排代码，但会增加不可控输出和延迟。

本项目既希望支持 Neo4j，也保留 Kùzu 的存储选项，因此路由层不能把某一个数据库的方言、函数和元数据假定为唯一真相。更稳妥的抽象是：**统一意图/中间表示（IR）→ 后端能力探测与方言编译 → 数据库执行**。

## 2. 国内外现状

### 2.1 Text2Cypher 的公开基准与模型差距

最直接的公开证据是 Neo4j 相关研究的 Text2Cypher 基准。论文 **[A Benchmark Dataset towards Text2Cypher Task](https://aclanthology.org/2025.emnlp-industry.133.pdf)** 报告了跨 11 个图数据集的 27,529 个自然语言/Cypher 对，并通过 schema、运行时、值检查和人工审核验证数据；训练/验证/测试划分为 18,470/2,000/7,059，测试域与训练域分离。论文同时评测了从 8B 到 72B 的模型，并以执行准确率（生成查询与基准查询执行结果一致）衡量效果。

该论文的零样本总执行准确率如下（原论文表 3）：

| 模型 | 参数规模 | 零样本执行准确率 |
|---|---:|---:|
| Granite-3.3-8B-Instruct | 8B | 26.21% |
| Llama-3.1-8B-Instruct | 8B | 30.99% |
| Phi-4 | 约 14B | 62.01% |
| Llama-3.3-70B-Instruct | 70B | 64.69% |
| Llama-4-Maverick | MoE | 70.97% |
| DeepSeek-V3 | MoE | 76.75% |
| Qwen2.5-72B-Instruct | 72B | 66.32% |

事实是：大模型通常优于 8B 级零样本模型，但即使最好结果也不是可靠的生产级正确率；复杂查询类别下降尤为明显。论文报告复杂类别与简单类别的差距平均约 37 个百分点。少样本检索示例平均只带来约 2.5 个百分点提升，而且 schema 不匹配的示例可能误导模型。

同一研究线的 **[Text2Cypher: Bridging Natural Language and Graph Databases](https://aclanthology.org/2025.genaik-1.11/)** 汇总、清洗了 44,387 个实例，并公开了数据与训练代码；其结果显示，在领域数据上微调后的模型相对基础模型在 Google-BLEU、Exact Match 等指标上提升。该论文中，Llama-3.1-8B-Instruct 使用 LoRA、2 个 epoch、rank=8，在单张 NVIDIA A100 80GB 上训练。需要注意：不同论文的数据集、测试划分和指标不同，不能直接把它们的百分比横向当作同一排行榜。

更贴近 SLM 的证据是 **[Refining Text2Cypher on Small Language Model with Reinforcement Learning Leveraging Semantic Information](https://www.mdpi.com/2076-3417/15/15/8206)**。该工作以 Qwen2.5-3B-Instruct 为基线，在监督微调后使用 GRPO，并增加 key-value 与关系三元组抽取辅助任务；论文报告在未见 schema 上达到 85% 执行准确率，且相对仅监督微调提高 5.03 个百分点。这个结果支持“3B 级模型经过任务化训练可以有竞争力”，但它是特定数据集、训练流程和评测设置的论文结果，**不能直接推断 LudoGraph 的未训练 3B 模型也能达到 85%**。

### 2.2 生产工具与零样本能力

Neo4j JDBC 的 **[Text2Cypher 官方手册](https://neo4j.com/docs/jdbc-manual/current/text2cypher/)** 描述了一个实验性 translator：将当前 graph schema 与问题发送给 OpenAI，生成 Cypher；文档明确提醒输出具有非确定性，可能语法正确但语义不符合用户意图，建议先取回并检查生成语句，再单独执行。该文档还说明已翻译查询可缓存。

这与基准结果一致：零样本大模型适合快速原型、长尾问题和离线辅助，但不能把“能生成语法正确的 Cypher”当作“语义正确”。生产路由至少需要 schema 白名单、只读权限、参数化值、解析/解释计划、超时和失败回退。

### 2.3 端侧小模型、量化与实测性能

公开资料支持端侧运行 1B–3B 级模型，但性能强烈依赖硬件、上下文长度、量化格式、批量和后端，不能给出与 LudoGraph 无关的单一“毫秒数”。

- **llama.cpp 的公开基准**：[IQ4_NL CPU benchmark](https://github.com/ggml-org/llama.cpp/pull/10541) 报告了约 1.24B、约 4.5 bpw 的量化模型在 CPU 上的 token/s；在其 M2 Ultra 测试中，Qwen2 3B IQ4_NL 约 1.70 GiB，8 线程生成约 56 token/s，16 线程约 78 token/s（`tg64`）。这相当于仅生成 10–30 个 token 也可能需要约 130–540ms，尚未计入模型加载、prompt prefill、schema 注入、网络和数据库查询。
- 同一项目的 **[llama.cpp/vLLM 比较](https://github.com/ggml-org/llama.cpp/discussions/15180)** 在单 RTX 4090、Qwen2.5-3B、单并发、约 2,048 prompt token 和 256 generated token 的测试中报告约 90–94ms 的端到端运行时间（该测试定义和硬件条件特殊，不能等同于首 token 延迟）。
- 量化通常显著降低模型内存和带宽压力，但会有质量损失；具体损失必须在 Text2Cypher 执行准确率上重新评估。公开资料没有给出“同一 NL2Cypher 数据集上 FP16 vs INT4、同一端侧设备”的完整可复现实验，故该差异 **[unverified]**。

由此可得工程级区间，而非承诺：

- 0.5B–1.5B INT4 分类/模板路由：在常驻内存、短输入、专用 CPU/NPU 上，**几十毫秒量级是可行假设**，但 LudoGraph 的实际 P50/P95 需自测。
- 3B INT4 自回归 NL2Cypher：端侧 CPU 常见是百毫秒到秒级；GPU/NPU 常驻可更快，仍取决于输入 schema 和输出长度。
- 首次加载、冷启动、长 schema、并发排队和数据库执行不能纳入“模型 token/s”而忽略。

## 3. 关键发现

### 3.1 是否需要微调：明确结论

**结论：第一阶段不建议一开始就微调；上线稳定性要求达到后，应对意图路由做轻量微调，对 NL2Cypher 则优先做领域 SFT/LoRA 或受约束模板化微调。**

理由如下：

1. 不微调的大模型有公开基准，但结果跨度约 26%–77%，且最好结果仍会在复杂查询失败；8B 零样本仅约 26%–31%。因此“不微调”可以支持原型和低风险问答，不能据此承诺可靠查询编译。
2. 微调确实有公开收益：44,387 实例研究报告基础模型到微调模型提升；Qwen2.5-3B + SFT/GRPO 论文在未见 schema 报告 85%。这证明“微调小模型”可行，但不是 LudoGraph 的保证。
3. LudoGraph 是单一、相对窄的领域，意图集合和查询模板可以先由规则/分类器实现；先收集真实问题、拒答样本、schema 变更样本，再微调比凭空构造数据更可靠。
4. NL2Cypher 的主要难点是 schema 与语义落地，不只是语言流畅度。微调应配合 schema 检索、执行反馈和静态校验，不能用微调替代验证器。

**可接受的分阶段策略：**

- P0：不训练 SLM；规则/关键词 + embedding 检索路由，云端或本地大模型生成候选，执行前严格校验。
- P1：对 0.5B–1.5B 意图路由模型做分类微调；对高频查询用模板和参数槽位，不让 SLM 自由生成完整 Cypher。
- P2：积累至少数千条经人工审核、按意图/难度/schema 分层的数据后，对 3B 级模型做 LoRA；用执行准确率、拒答准确率和安全违规率验收。
- P3：只有在 P2 的失败样本表明通用模型仍是瓶颈时，才考虑 GRPO/执行反馈等更昂贵训练。

### 3.2 数据量、构造与成本

公开工作提供了规模参考，但没有证明某个固定样本数适用于所有 schema：

- 公开 Text2Cypher 基准为 27,529 个严格验证的对；另一整理工作为 44,387 个实例。规模足以支撑跨域研究，但不等于 LudoGraph 必须收集 4 万条。
- LudoGraph 初始数据建议按模板自动生成候选，再由执行器和人工审核过滤：每个实体/关系/规则模板生成多种中文问法；加入别名、时间/版本条件、否定、边界值、歧义和不可回答问题；按 schema 版本做 domain split，避免训练测试泄漏。
- 最有价值的标注包括：意图、实体/关系链接、槽位、期望 IR、可执行 Cypher、结果等价性、是否应拒答、风险等级。单纯 Exact Match 不足以评估查询语义。
- 训练成本可从 LoRA 开始。上述公开工作在 A100 80GB 上用 8B 模型训练 2 epoch；LudoGraph 的 3B LoRA 预计可用单张 24GB 级 GPU，但具体显存/时长 **[unverified]**，应以目标序列长度和数据量实测。

### 3.3 两步路由+编译优于端到端

**推荐两步：意图/槽位路由 → schema-aware 查询编译。** 直接针对 Text2Cypher 的公开研究并没有形成“端到端永远优于两步”的结论；相反，基准中复杂查询、schema mismatch 和长尾语义造成明显错误，Neo4j 官方文档也提醒生成结果需检查。因此以下是基于风险和可验证性的工程推断，而非已被同一基准严格证明的定理：

- 分类器可输出有限标签，易测、易缓存、易在端侧运行。
- 编译器只接收相关 schema 子图和结构化槽位，prompt 更短，减少幻觉和延迟。
- 中间表示可以在 Neo4j 与 Kùzu 之间复用；端到端文本生成则更容易绑定某一方言。
- 对复杂或低置信度问题，两步架构可升级到云端大模型；对高频意图直接走模板。

备选端到端方案适合早期原型：把用户问题、schema 摘要和 few-shot 示例送给一个大模型，配合 Cypher parser、执行试跑和重试。优点是开发快、长尾覆盖好；缺点是成本、延迟、可解释性和安全边界都更难控制。端侧 3B 端到端自由生成不作为默认生产路径。

### 3.4 “毫秒级”是否现实

应把指标拆成四个部分：

`总延迟 = 路由 + schema/示例检索 + 查询编译 + 数据库执行 + 结果整理`

结论：

- **纯规则/缓存命中：** 1–10ms 级目标可现实（推断，需在目标设备实测）。意图表查找、模板填槽和已编译查询缓存可以接近此级别。
- **常驻 0.5B–1.5B 做意图分类：** P50 数十毫秒级是合理目标；P95 取决于设备和并发，不能写成无条件 SLA。
- **端侧 3B 自回归 NL2Cypher：** 不应承诺端到端毫秒级。公开 llama.cpp 结果显示 3B 级 CPU 生成本身可能是百毫秒到秒级；还要加数据库执行。
- **数据库查询本身：** 即使模型不耗时，冷 cache、复杂多跳、磁盘 I/O 和结果序列化也可能超过 1ms。

建议将验收指标改成分层目标：

1. 高频模板/缓存命中：P50 ≤10ms、P95 ≤30ms（作为待实测目标，不是当前事实）。
2. 常驻小模型意图路由：P50 ≤50ms、P95 ≤150ms（设备和输入上限固定后验证）。
3. 动态 NL2Cypher：P50 ≤300ms、P95 ≤1s 作为第一版工程目标；若调用远程 LLM，应单独报告网络和服务端排队。
4. 数据库执行与总链路分别记账，禁止用模型 token 生成速度替代端到端延迟。

“毫秒级”只适用于**缓存、规则、模板和已编译查询**这类快路径；不适用于任意自然语言到 Cypher 的完整冷路径。RAG 可以缩短 prompt、提高 schema grounding，但会增加向量检索和序列化开销；缓存只能覆盖重复或语义等价请求，不能证明长尾查询也能毫秒完成。

### 3.5 Neo4j 与 Kùzu 的耦合

Kùzu 官方 **[Cypher manual](https://kuzudb.github.io/docs/cypher/)** 说明其实现 openCypher 的语句、子句、表达式和函数；其 **[数据类型文档](https://kuzudb.github.io/docs/cypher/data-types/)** 也指出 JSON 等能力需要扩展。Neo4j 则拥有自身的 Cypher 版本、函数、过程、索引和运行计划。两者共享大量 MATCH/WHERE/RETURN 基础语法，但不能假设任意 Neo4j Cypher 在 Kùzu 上可执行。

因此：

- 路由意图、实体/关系链接和查询 IR 应与数据库无关。
- IR 编译器分别实现 `Neo4jDialect` 和 `KuzuDialect`，维护能力矩阵（函数、聚合、路径、全文/向量、JSON、写操作）。
- 生成阶段只允许目标后端能力矩阵中的构造；执行前做 parser/解释计划/只读白名单校验。
- 评测必须按后端分别跑执行准确率，不能用 Neo4j 的结果替代 Kùzu 结果。
- 若最终只选一个后端，可减少方言测试成本；但仍建议保留 IR，因为它把 schema 变化与 LLM 提示解耦。

## 4. 对本项目的具体影响

### 4.1 推荐架构

```text
用户问题
  -> 规则/缓存快路径
  -> 轻量意图路由（标签、置信度、槽位、后端）
  -> schema 子图检索（实体/关系/模板）
  -> 结构化 Query IR
  -> Neo4j/Kùzu 方言编译器
  -> parser + schema + 只读/资源限制校验
  -> EXPLAIN/受限执行
  -> 结果与证据返回
```

推荐组件职责：

1. **规则与缓存：** 覆盖固定查询和历史等价查询，承担“毫秒级”承诺。
2. **路由 SLM/分类器：** 只输出有限 JSON 标签，不直接拥有任意数据库写权限。
3. **schema 检索：** 只注入相关节点、边、属性和可用模板，限制上下文长度。
4. **IR：** 表示实体、关系路径、过滤器、聚合、排序、分页和验证意图。
5. **编译与校验：** 生成参数化 Cypher；检查语法、白名单、复杂度、超时和结果规模。
6. **回退：** 低置信度、复杂多跳或编译失败时转人工澄清或较强模型；明确返回“无法安全编译”，不猜测执行。

### 4.2 备选方案

- **A：全云端大模型端到端。** 最快验证产品价值，长尾能力强；延迟、成本、数据合规和供应商依赖最大。
- **B：端侧路由 + 云端编译。** 推荐的过渡方案；路由低延迟，复杂问题保留大模型能力，但需处理网络抖动。
- **C：端侧 3B SLM + 模板/受限解码。** 适合离线部署和隐私场景；覆盖面较窄，需要持续收集失败样本，不能默认支持任意自然语言。
- **D：无生成式 NL2Cypher。** 纯意图分类、实体链接和模板拼装；最可控、最快，但需要预先覆盖查询类型，适合作为快路径和安全基线。

### 4.3 建议的验收实验

在决定是否微调前，建立同一数据集、同一 schema、同一硬件的对照：

- 0-shot 8B/云端强模型；few-shot + schema 检索；3B INT4；3B LoRA；模板基线。
- 指标：执行准确率、结果等价率、语法通过率、schema linking F1、拒答准确率、越权/写操作率、P50/P95 首 token和总延迟、峰值内存。
- 按简单/复杂、seen/unseen schema、中文别名、版本条件、歧义问题分层报告。
- 每次 schema 或方言变化都回归测试；把数据库执行错误和人工修正回流为训练/评测数据。

## 5. 风险与未知

1. **公开数据与 LudoGraph 分布差异：** 论文主要使用英文、多领域图数据；中文游戏规则、版本语义和数值约束的准确率未知，标记 **[unverified]**。
2. **基准指标不可直接互换：** Execution Accuracy、Exact Match、Google-BLEU 衡量不同性质；不同 schema 划分也会显著改变结果。
3. **模型量化影响未知：** 公开 llama.cpp 性能资料并未提供 LudoGraph Text2Cypher 的质量/延迟联合曲线；INT4 是否满足安全阈值需要实测。
4. **复杂查询的语义风险：** 语法合法不代表路径、聚合、时间条件正确；必须以执行结果和人工审核为准。
5. **数据库方言漂移：** Neo4j/Kùzu 版本、扩展和函数差异可能使训练样本失效；需要能力矩阵和后端独立回归集。
6. **缓存一致性：** schema、本体、版本或权限变化后，旧查询缓存可能返回不适用结果；缓存 key 必须包含后端、schema 版本、权限和模板版本。
7. **延迟尾部：** 冷启动、模型加载、并发排队、长上下文、数据库锁/I/O 和网络会主导 P95；“毫秒级”只能针对定义清楚的快路径。
8. **数据构造成本：** 自动合成容易产生模板偏差和错误标注；必须做执行验证、跨模板留出和人工抽样，不能只扩大样本数量。
9. **当前研究空白：** 尚未找到公开、统一硬件下“意图路由+NL2Cypher+Neo4j/Kùzu 执行”的端到端毫秒级基准，故该指标对 LudoGraph 仍属待验证假设。

## 6. 最终建议

1. **要不要微调：** 不把微调作为 P0 前置条件；先用规则/模板、schema 检索和强模型建立可测基线。达到真实数据量和稳定性门槛后，明确建议对意图路由做轻量微调，并对 3B 级 NL2Cypher 做 LoRA/SFT；不建议未经评测直接使用自由生成 SLM。
2. **延迟指标：** 将“毫秒级”改写为“缓存/模板快路径 P50 10ms 级；意图路由 P50 数十毫秒；动态 NL2Cypher 首版 P50 数百毫秒、P95 约 1 秒，具体以固定硬件实测为准”。
3. **架构：** 采用两步路由+编译、统一 Query IR、Neo4j/Kùzu 方言适配器、执行前校验和强模型/人工回退。
4. **成功标准：** 以分层执行准确率、拒答安全性和 P95 端到端延迟验收，而不是以生成文本相似度或 token/s 单项指标验收。

## 参考来源

1. [A Benchmark Dataset towards Text2Cypher Task, ACL/EMNLP Industry 2025](https://aclanthology.org/2025.emnlp-industry.133.pdf)
2. [Text2Cypher: Bridging Natural Language and Graph Databases, GenAIK 2025](https://aclanthology.org/2025.genaik-1.11/)
3. [Refining Text2Cypher on Small Language Model with Reinforcement Learning Leveraging Semantic Information](https://www.mdpi.com/2076-3417/15/15/8206)
4. [Neo4j JDBC Text2Cypher manual](https://neo4j.com/docs/jdbc-manual/current/text2cypher/)
5. [llama.cpp CPU quantization benchmark](https://github.com/ggml-org/llama.cpp/pull/10541)
6. [llama.cpp vs vLLM performance comparison](https://github.com/ggml-org/llama.cpp/discussions/15180)
7. [Kùzu Cypher manual](https://kuzudb.github.io/docs/cypher/)
8. [Kùzu data types and extensions](https://kuzudb.github.io/docs/cypher/data-types/)
