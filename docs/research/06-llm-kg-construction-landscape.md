# LLM 知识图谱构建技术全景与团队脉络调研

> **调研日期：2026-10-09**
> **检索范围：** 公开论文、会议论文/预印本、官方项目页、GitHub 仓库、数据集说明与软件许可证；重点检索 2023–2026 年 LLM-based Knowledge Graph Construction（LLM-KGC）、ontology/schema-guided extraction、open information extraction、GraphRAG、agentic/multi-agent extraction、神经符号推理与 solver 集成。游戏领域额外检索 video game rules、VGDL、game ontology、game documentation、rule formalization、text-to-game rules 等组合词。本文是论文 Related Work 与创新点定位素材，不是技术选型建议，也不修改既有设计文档。

## 1. 背景与问题边界

知识图谱构建（Knowledge Graph Construction, KGC）通常包含从文本或多模态资料中发现实体、类型化、抽取关系/事件、共指消解、实体对齐、规范化、冲突处理、图谱融合和持续更新。传统系统把这些任务拆为 NER、entity linking、relation extraction、ontology engineering 等模块；LLM 的加入改变了“如何提出候选事实”和“如何从非结构化文本诱导 schema”的方式，但没有消除事实性、可追溯性和一致性问题。

本报告将“LLM-KGC”限定为：LLM 参与从文本、文档集合或环境交互中产生 KG 的 schema、节点、边、限定词或更新操作。纯粹用 KG 做问答/RAG 而不构建或更新图谱的工作，放在检索增强一节作为相邻方向；纯粹的 ontology learning 不等同于给定本体下的保守事实抽取，但在 ontology-driven KGC 中一并讨论。需要区分三个层次：

1. **格式层（syntactic）：** JSON、RDF、Cypher、函数参数是否合法；
2. **结构/本体层（structural/ontological）：** 类型、谓词、domain/range、层级和基数约束是否满足；
3. **事实层（factual/evidential）：** 输出的断言是否被原文支持、是否错误合并实体、是否把推断当作显式事实。

**学界共识（依据 Text2KGBench、KG 构建综述及近期 EDC/Wikontic 等工作）：** LLM 能显著降低领域抽取和 schema 变化的人工成本，但“输出格式正确”不等于“事实正确”；高质量 KG 仍需要 schema、证据、规范化和验证层。**本次推断：** LudoGraph 类游戏规则图谱的研究价值不在于再做一个通用三元组生成器，而在于检验 LLM 抽取在条件、时序、数量、否定、版本和规则推理约束下的保守性与可验证性。

## 2. 国内外现状与路线分类

### 2.1 流水线式 Pipeline KGC

**定义。** 将文档依次经过实体发现/类型化、关系或事件抽取、共指与实体链接、规范化、schema 对齐、冲突消解和入库。LLM 可以替代其中一个或多个模块，但模块边界和中间产物显式保留。传统自动 KGC 的系统综述将 knowledge acquisition、refinement、evolution 作为三阶段；这仍是今天最容易审计和工程化的骨架。[A Comprehensive Survey on Automatic Knowledge Graph Construction](https://dl.acm.org/doi/10.1145/3618295)

**代表工作与适用边界。** [Text2KGBench](https://arxiv.org/abs/2308.02357)（Mihindukulasooriya 等，ISWC Resource Track 2023，IBM/语义网社区，多机构）把“给定 ontology 和句子，抽取符合 concept、relation、domain/range 且忠于句子的事实”正式化，并提供 Wikidata-TekGen 和 DBpedia-WebNLG 两组数据。它适合测 schema adherence 和 hallucination，但句子较短、领域相对干净，不覆盖长篇规则文本、版本冲突或时序。

[Ontology-guided Knowledge Graph Construction from Maintenance Short Texts](https://aclanthology.org/2024.kallm-1.8.pdf)（Bikaun 等，KALLM 2024，维护/工业文本研究团队）用 Llama-2/3、ontology-guided prompting 和 in-context learning，在少量相似示例下做领域事实抽取，并报告高性能模型的幻觉较少、较小模型可通过 pruning 改进。该工作说明 pipeline 可以让专家以增量方式提供示例，但结果仍依赖领域本体、原文可见性和后处理；不能将工业短文本结果外推到开放域长规则文档。

**优点：** 每一步可替换、可定位错误，可保留证据和置信度；适合 schema 固定、合规审计、需要人工复核的场景。**局限：** 误差会级联；模块间的实体边界、关系方向和版本语义可能丢失；跨句/跨文档关系和全局一致性需要额外合并阶段；多次 LLM 调用带来成本与延迟。

### 2.2 端到端或生成式 KGC

**定义。** 将文本直接生成线性化三元组、事件结构、RDF/JSON 或统一 IE 序列，模型同时学习实体和关系，不再显式运行传统 NER→RE 子任务。REBEL、UIE 代表了此前的生成式路线；ChatIE、CodeKGC 等把 LLM prompting 进一步用于零/少样本抽取。

[ChatIE: Zero-shot Information Extraction via Chatting with ChatGPT](https://arxiv.org/abs/2302.10205)（Wei 等，2023）把抽取组织成多轮问答，利用对话澄清实体与关系；[CodeKGC](https://arxiv.org/)（Bi 等，2024，[具体 arXiv 链接与作者版本需固定，部分索引信息为 **[unverified]**）把 KGC 转成代码生成。它们适合小 schema、快速迁移和少标注场景，但当 schema 很大时，完整 schema 放进 prompt 会消耗上下文，且自由生成会产生无效类型、重复实体、关系方向错误和未被文本支持的边。

[Extract, Define, Canonicalize (EDC)](https://aclanthology.org/2024.emnlp-main.548/)（Zhang 与 Soh，EMNLP 2024，新加坡国立大学/相关研究团队，仓库 [clear-nus/edc](https://github.com/clear-nus/edc)）是端到端与 pipeline 之间的重要折中：先做 schema-free open extraction，再由 LLM 定义实体/关系，再用向量检索和 LLM verification 做 canonicalization；已有 target schema 时进行 alignment，没有时自生成 schema。EDC 还训练 schema retriever，只把与当前文本有关的 schema 部分放进上下文。其核心贡献不是“一个更大的 prompt”，而是把开放发现与后验规范化解耦，缓解大 schema 的 context-window 问题。

[KGGen: Extracting Knowledge Graphs from Plain Text with Language Models](https://arxiv.org/abs/2502.09956)（Belinda Mo、Kyssen Yu、Joshua Kazdan、Joan Cabezas、Proud Mpala、Lisa Yu、Chris Cundy、Charilaos Kanatsoulis、Sanmi Koyejo，2025，Stanford/相关机器学习团队；Python 包与代码信息见 [KGGen](https://github.com/)。仓库的准确 URL/许可证需以发布版本核验，部分索引为 **[unverified]**）强调对相关实体进行 clustering 以降低图稀疏，并发布 MINE-1 benchmark，试图直接衡量文本信息在节点与边中的保留。它的价值在于把“图是否保留了原文信息”从传统 triple F1 中独立出来；但 clustering 也可能将同名、同类而非同一实体合并，不能替代证据级 entity linking。

**优点：** 任务统一、少样本迁移强、减少手写模块。**局限：** 黑盒程度高，错误原因难定位；生成 token 的概率不是事实置信度；端到端方法若无约束解码和后验验证，无法保证 ontology conformance；对长文本和密集 schema 扩展性有限。

### 2.3 多智能体 / Agentic extraction

**定义。** 把抽取、schema 对齐、证据核验、冲突解析、融合与评估分配给多个有角色的 LLM agent，由控制器编排并允许迭代/辩论/工具调用。它不是简单“并发调用多个 prompt”：关键是 agent 之间有可检查的中间状态、职责边界和合并协议。

[KARMA: Multi-Agent Knowledge Graph Enrichment](https://arxiv.org/abs/2502.06472)（论文作者与机构列表需以 arXiv 版本固定，**[unverified]**；2025）提出多个专门 agent，覆盖实体发现、关系抽取、schema alignment、冲突解决与评估，在 PubMed 三个领域的 1,200 篇文章上报告最多 38,230 个新实体、LLM 验证正确率 83.1%、冲突边下降 18.6%。这是“多角色审查”路线的代表，但主要指标含 LLM-as-a-judge，真实专家 gold、重复调用成本和 agent 相关错误仍是未知。

[Graphusion: Leveraging Large Language Models for Scientific Knowledge Graph Fusion and Construction in NLP Education](https://arxiv.org/abs/2407.10794)（Rui Yang、Boming Yang、Sixun Ouyang、Tianwei She、Aosong Feng、Yuang Jiang、Freddy Lecue、Jinghui Lu、Irene Li，2024，教育/NLP 知识图谱团队）将融合、对齐、整合和推理组织到统一的 prompt-driven 流程。它体现了从“只抽取新三元组”走向“抽取 + 图融合”的趋势。

[AGENTiGraph](https://arxiv.org/abs/2508.02999)（Sinketsu Zao 等，2025，仓库 [SinketsuZao/AGENTiGraph](https://github.com/SinketsuZao/AGENTiGraph)，许可证/活跃度应按仓库当前状态复核）把意图识别、任务规划、图交互、动态更新做成 agent pipeline，并在教育场景 3,500 查询上报告 95.12% 意图分类准确率和 90.45% 执行成功率。该 benchmark 主要评测图交互而非从游戏文本抽取，不能把结果当成 KGC precision。

**优点：** 可并行化、可对高风险事实设置独立审查、适合持续更新和冲突多的科学文献。**局限：** 调用数与成本快速增长；agent 之间可能“相互确认”同一个错误；最终裁决若仍是 LLM-as-a-judge 就没有独立证据；不可复现性、死循环、状态污染和权限安全是新增问题。**推断：** 多 agent 的真正增益应通过删去 verifier、resolver、schema agent 的 ablation 证明，而不是以 agent 数量或 prompt 长度作为质量代理。

### 2.4 检索增强与 KG-as-memory / GraphRAG

**定义。** 以 LLM 从文档构建开放或弱 schema 图，再用图遍历、社区摘要、PPR 或混合向量检索为 LLM 提供上下文。这里 KG 既是构建产物，也可能是 RAG 的索引；不少工作优化的是问答而非图谱本身的准确性。

[GraphRAG](https://arxiv.org/abs/2404.16130)（Darren Edge、Haibo Li、Ahmed Maher、等，Microsoft Research，2024；官方仓库 [microsoft/graphrag](https://github.com/microsoft/graphrag)，MIT License，GitHub 页面在本次检索中约 3.5 万 stars、数千 forks）先从文档抽取实体图，再做层次化社区发现和社区摘要，以 map-reduce 方式回答全局问题。它改进的是大语料“全局主题/总体趋势”问答，不证明抽取的每条边为真。官方 README 已提示项目主要处于维护和 bug/dependency 更新状态，故 stars 不能等同于研究活跃度。

[HippoRAG](https://proceedings.neurips.cc/paper_files/paper/2024/file/6ddc001d07ca4f319af96a3024f6dbd1-Paper-Conference.pdf)（Gutiérrez 等，NeurIPS 2024，OSU-NLP 团队；仓库 [osu-nlp-group/hipporag](https://github.com/osu-nlp-group/hipporag)，MIT License，约 4 千 stars）用 LLM 做 schemaless OpenIE，结合 Personalized PageRank 形成类似长期记忆的图索引，在多跳 QA 上以一次图检索整合跨段落信息。它的适用边界是关联检索和记忆，不是本体严格抽取。

[AriGraph: Learning Knowledge Graph World Models with Episodic Memory for LLM Agents](https://www.ijcai.org/proceedings/2025/2)（Anokhin 等，IJCAI 2025；交互式文本游戏与 agent memory 团队）在文本游戏环境中将 semantic memory 和 episodic memory 建成动态图，并让 agent 持续更新世界模型。它是游戏领域最相关的公开工作之一，但输入是环境观察/交互轨迹，目标是 agent 决策，不是从商业游戏设计文档构建可审计规则本体。

[LightRAG](https://arxiv.org/abs/2410.05779)（Guo 等，2024；仓库 [HKUDS/LightRAG](https://github.com/HKUDS/LightRAG)，MIT License，GitHub 页面约 4 万 stars）采用 KG 与向量双层索引，主张降低 GraphRAG 的索引和增量更新成本。其开源活跃度高，但仍应把“RAG 回答质量”与“KG 构建质量”分开评测。

**优点：** 对跨文档关系、全局问答和长时记忆有效；可把文本证据与图结构组合。**局限：** 图错误会被检索反复放大；社区摘要会丢失限定词、否定和来源；PPR/向量相似度不是逻辑推理；大多数 benchmark 测 QA，缺少逐边 precision、证据完整性和 schema 一致性。

### 2.5 本体/约束驱动路线

**定义。** 把本体用于 schema-guided prompting、候选关系检索、domain/range 检查、类型层级推理、后抽取 canonicalization 或解码时限制合法输出；强约束还可以将输出编译到规则/逻辑求解器。

- **Ontology-grounded post-extraction：** EDC 先开放抽取，再把 schema definition、向量候选和 LLM verification 放在后处理；Wikontic 则把 Wikidata ontology 直接置于抽取管线中，做候选三元组、关系合法性、实体类型和名称去重。
- **Schema-guided extraction：** Text2KGBench 明确要求遵守概念、关系和 domain/range；维护短文本工作证明少量 in-context examples 可以适配领域本体；[LLMs4OL](https://github.com/HKUST-KnowComp/LLMs4OL) 更偏 ontology learning，不应与固定 ontology extraction 混为一谈。
- **Constrained decoding：** 通过 grammar、JSON Schema、有限词表或 trie 在 token 生成时禁止非法输出。Dialogue Ontology Relation Extraction via Constrained CoT Decoding（[SIGDIAL 2024](https://aclanthology.org/anthology-files/anthology-files/pdf/sigdial/2024.sigdial-1.33.pdf)）把候选术语和关系类型限制在目标 ontology，并用多分支 CoT decoding 选关系。解码约束主要保证输出空间和置信筛选，不自动证明句子蕴含该关系。
- **Schema/guardrail co-optimization：** [PARSE](https://aclanthology.org/2025.emnlp-industry.184.pdf)（EMNLP Industry 2025）提出 ARCHITECT 优化给 LLM 的 JSON schema，SCOPE 用静态检查、grounding verification、缺失字段检查和 retry 做结构化抽取。其启示是 schema 本身影响模型可理解性，但 JSON 合规仍低于本体语义和事实正确性。
- **本体用于推理约束而非仅限形：** [Wikontic: Constructing Wikidata-Aligned, Ontology-Aware KGs](https://arxiv.org/abs/2512.00590)（2025，作者团队 **[unverified]**）将 Wikidata domain/range 与关系约束用于候选关系排序、实体去重和最终 ontology verification，并报告在 MINE-1 上的信息保留率约 84–86%。这是“本体参与后验语义裁决”的较新代表，而不只是让 JSON 长得对。

**优点：** 限制输出空间、减少关系类型幻觉、使 schema 迁移和审计更可解释。**局限：** 过强约束会降低召回、把 ontology 缺失误判为文本无事实；ontology 本身可能不完备或含冲突；domain/range 合法不等于事实存在；大 schema 会造成上下文和检索开销；本体推理通常是开放世界语义，不能直接当作闭世界数据库否定。

## 3. 代表工作与团队脉络

| 工作 | 作者/团队、年份、venue | 路线与核心贡献 | 开源/引用量级 |
|---|---|---|---|
| Text2KGBench | Mihindukulasooriya 等；ISWC 2023 Resource Track | 首批明确评测 ontology-driven KG generation；7 类指标覆盖事实、ontology conformance、hallucination | [GitHub](https://github.com/cenguix/Text2KGBench)，Apache-2.0 code；数据 CC BY 4.0；约 90 stars，活跃度中等 |
| Schema-adaptable KGC / AdaKGC | Ye 等；2023，arXiv/ACL 相关研究 | 横向、纵向、混合 schema expansion；SPI + schema-conditioned dynamic decoding，免重新训练适配 schema | [论文](https://arxiv.org/abs/2305.08703)；仓库信息 **[unverified]** |
| ChatIE | Wei 等；2023，arXiv | 多轮对话式零样本 IE，减轻一次生成多个关系的困难 | 论文/实现链接见 [arXiv](https://arxiv.org/abs/2302.10205)，项目活跃度 **[unverified]** |
| GraphRAG | Edge 等；Microsoft Research，2024 | LLM 抽取实体图、社区检测与摘要，支持全局语料 sensemaking | [仓库](https://github.com/microsoft/graphrag)，MIT；高 stars，官方称主要维护 |
| EDC | Zhang & Soh；EMNLP 2024 | Extract→Define→Canonicalize；开放抽取、schema 定义、后验规范化，支持超大/未知 schema | [仓库](https://github.com/clear-nus/edc)，许可证/最新活跃度 **[unverified]** |
| Ontology-guided KG from Maintenance Short Texts | Bikaun 等；KALLM 2024 | Llama-3 + ontology prompt + ICL；研究领域小样本、幻觉 pruning 与 human-in-the-loop | [ACL Anthology](https://aclanthology.org/2024.kallm-1.8.pdf)，代码/数据随论文发布，具体许可证 **[unverified]** |
| HippoRAG | Gutiérrez 等；OSU-NLP，NeurIPS 2024 | schemaless KG + PPR 长期记忆，优化多跳检索而非严格 KGC | [仓库](https://github.com/osu-nlp-group/hipporag)，MIT；约 4k stars |
| Graphusion | Rui Yang 等；2024，arXiv | 科学知识图谱融合、对齐、整合和推理的统一 LLM 流程 | [论文](https://arxiv.org/abs/2407.10794)，仓库/许可证 **[unverified]** |
| KGGen | Mo 等；Stanford/相关团队，2025，arXiv | 从纯文本生成 KG，聚类实体降低稀疏；提出 MINE-1 信息保留 benchmark | [论文](https://arxiv.org/abs/2502.09956)，Python 包；仓库许可证 **[unverified]** |
| KARMA | 作者与机构需按 arXiv 版本核对；2025，arXiv | 多 agent 做实体、关系、schema、冲突和评估，面向科学 KG enrichment | [论文](https://arxiv.org/abs/2502.06472)，开源仓库 **[unverified]** |
| SymAgent | 作者团队 **[unverified]**；2025，arXiv | LLM planner 从 KG 诱导 symbolic rules，executor 调工具并发现缺失 triples，自学习更新 | [论文](https://arxiv.org/abs/2502.03283)，代码 **[unverified]** |
| AriGraph | Anokhin 等；IJCAI 2025 | 交互式文本游戏的 semantic/episodic world model，图用于 agent 记忆与规划 | [论文](https://www.ijcai.org/proceedings/2025/2)，代码链接需按论文版本核验 |
| Wikontic | 作者团队 **[unverified]**；2025，arXiv | Wikidata-aligned ontology-aware pipeline；关系 domain/range、类型约束、去重与验证 | [论文](https://arxiv.org/abs/2512.00590)，仓库 [screemix/Wikontic](https://github.com/screemix/Wikontic)，活跃度/许可证 **[unverified]** |
| KG-Prover | 作者团队 **[unverified]**；2025，arXiv | 从 ProofWiki 建 6 万节点/30 万边图，LLM 检索图、生成/自动形式化证明并用 Lean 验证 | [论文](https://arxiv.org/abs/2503.11657)，实现与许可证 **[unverified]** |

**团队脉络（事实与推断分开）：**

- **语义网/知识图谱评测脉络：** Text2KGBench 以 ontology、domain/range 和 hallucination 为核心，连接 ISWC/ESWC 语义网社区；EDC 将这一问题推进到 LLM 的开放抽取与 schema 规模化。事实依据是两篇论文的任务定义与实验设置。
- **Microsoft Research：** GraphRAG 从 2024 年起把 KG construction 作为企业私有语料的全局检索索引，官方项目页、MIT 仓库和持续的 GraphRAG/LazyGraphRAG 叙事可核验。它更持续产出系统/产品化路线，不代表严格本体抽取路线。
- **OSU-NLP、Stanford/ML 团队及 HKU/HKUDS：** HippoRAG、KGGen、LightRAG 分别强化图记忆、图信息保留和低成本图检索，体现“KG 为 LLM 外部记忆”方向的持续产出。按 stars 判断活跃度只是仓库事实，不是论文质量结论。
- **科学文献 KG enrichment：** KARMA、Graphusion 等将 schema alignment、conflict resolution 和多 agent 协作引入科学领域。其共同趋势是从单文档 extraction 转向增量融合，但专家 gold 与成本仍不足。
- **神经符号/形式推理团队：** SymAgent、LQOT、CLOVER、KG-Prover 将 LLM 限定为规划、语义解析或候选生成，把规则、SAT/Z3、fuzzy KGQA 或 Lean 作为执行/验证器。该脉络与 KGC 相邻但关键地提出了“图谱不仅用于召回，也用于约束推理”。

## 4. 2023→2026 时间线与技术演进

### 2023：从 schema-guided prompt 和基准开始

主流问题是“LLM 是否能在给定 ontology 下抽取事实”。Text2KGBench 以 10 个 Wikidata-TekGen ontology、19 个 DBpedia-WebNLG ontology 及 18,000 余句规模，定义事实、合规与幻觉指标；AdaKGC 则把“schema 会变化”明确成任务，提出不用重新训练的 schema expansion。同期 ChatIE 将 IE 改写成多轮问答。主流仍是单模型/少量模块、短文本、小 schema，缺少长文档全局融合。

### 2024：开放抽取、后验规范化和图检索结合

EDC 代表的变化是承认完整 schema 无法一直塞进 prompt，先抽取开放三元组，再用定义、检索和 canonicalization 对齐。GraphRAG 将抽取图、社区发现和摘要连接起来，目标从“每个三元组是否正确”扩大到“大语料的全局问答”。HippoRAG 将 schemaless KG 变成长期记忆并用 PPR 做多跳检索。维护短文本工作表明开源 LLM 的 ICL 可降低标注和微调门槛。由此形成两条并行主流：**schema-first 的一致性路线**和 **schema-free 的覆盖/检索路线**。

### 2025：信息保留、agentic enrichment、本体后处理与 solver 结合

KGGen/MINE-1 试图测量图从文本保留多少信息，而不只看固定 gold triples；KARMA 和 AGENTiGraph 将抽取、对齐、冲突和图更新拆给 agent；Wikontic 把 Wikidata 约束放入抽取后的关系验证、类型检查和去重；AriGraph 在交互式游戏中构建可持续更新的 episodic/semantic memory。神经符号方向出现更清晰的“LLM 生成/规划 + 符号执行/验证”分工：SymAgent 以 KG 结构诱导规则并从外部文本补图，KG-Prover 以图检索辅助证明并用 Lean 过滤不可证候选。

### 2026：状态与预测边界

截至本次调研日期，公开检索可稳定核验的代表性论文主要集中在 2025 及以前；**2026 年的新论文、引用量、仓库活跃度尚未形成稳定索引，具体结论标为 [unverified]**。可以观察到的延续方向是：ontology-grounded post-extraction、schema retriever、graph memory、agentic verification 和 solver-backed reasoning 的组合，而不是某一种“完全端到端模型”替代全部 pipeline。**推断：** 技术演进不是线性淘汰：pipeline 仍用于审计和本体一致性，端到端用于候选生成，RAG 用于上下文召回，agent 用于分工和迭代，solver 用于可判定的约束；未来更可能是分层组合。

## 5. 神经—符号 KG 与符号求解器

### 5.1 从 KGQA 到逻辑查询

[Logic Query of Thoughts (LQOT)](https://arxiv.org/abs/2404.04264) 将复杂逻辑查询分解成依赖图上的子问题，同时调用 LLM 和 fuzzy logic KGQA；KG 的结果抑制 LLM 幻觉，LLM 又为不完整 KG 提供候选。它说明 KG 与 LLM 可以双向补充，但 fuzzy vector 的高分仍不是形式化证明。

[SymAgent](https://arxiv.org/abs/2502.03283) 把 KG 当作动态环境：Agent-Planner 从图中抽取 symbolic rules 进行问题分解，Agent-Executor 通过工具调用 KG 和外部文档，自动触发 triple extraction 并发现缺失事实。该设计与 KGC 直接相关，因为抽取不再是离线一次性过程，而是由推理需求驱动的局部补图。风险是 planner 诱导的规则可能不是本体明示规则，必须保留规则来源并区分事实、规则和假设。

### 5.2 LLM→逻辑公式→SAT/Z3

[CLOVER: Divide and Translate](https://arxiv.org/)（论文完整链接、作者/年份索引 **[unverified]**）让 LLM 先做组合式一阶逻辑翻译，再用 SAT solver 比较候选公式的一致性与反例解释，实施中使用 Z3。其关键是把 LLM 限制为语义解析器，将规划和执行交给 solver；这比要求模型直接输出最终真假更可控。该思路可迁移到“自然语言规则→约束 IR→solver”，但不能假设自然语言到逻辑的翻译天然正确。

### 5.3 图检索与形式证明

[KG-Prover](https://arxiv.org/html/2503.11657) 从 ProofWiki 页面和超链接构建约 60,000 节点、300,000 边的数学知识图，LLM 先做语义检索和图扩展，再生成非形式证明、自动形式化并由 Lean 验证。它展示了“图用于选择候选概念，定理证明器用于最终裁决”的组合；也揭示了中间自然语言翻译会引入额外错误。**学界共识程度：** 神经模型提出候选、符号系统验证，在逻辑任务中有清晰的互补性；**本次推断：** 对规则图谱，solver 的最有价值位置不是替代抽取，而是拒绝违反类型、守卫、资源守恒或可达性约束的候选，并返回可解释反例。

## 6. 游戏领域检索结果

### 6.1 直接相关公开工作

本次检索的严格查询包括：

- `"game rules" AND "knowledge graph" AND extraction`
- `"video game" AND ontology AND knowledge graph`
- `"game documentation" AND LLM AND knowledge graph`
- `"rule text" AND formalization AND game`
- `"text-to-game" AND rules AND VGDL`
- `"game rules" AND "SAT" OR "SMT" OR "formal verification"`
- 以及对应的 `游戏规则 知识图谱`、`游戏文档 本体 抽取`、`规则文本 形式化 游戏`、`LLM 游戏规则 抽取` 中英文组合。

**结论（检索范围内）：未发现一个已被广泛采用、公开可复现、专门从商业游戏策划文档/规则文本构建本体化 KG 的 LLM benchmark 或成熟系统。** 这不是“绝对不存在”的证明，较小众会议、工业内部项目、未索引仓库和 2026 新论文可能遗漏，故该句关于“没有”的强版本标为 **[unverified]**。

最接近的是 [AriGraph](https://www.ijcai.org/proceedings/2025/2)：在交互式文本游戏中从观察和经历构建 episodic/semantic memory graph，并用于 agent 规划；它不从规则文档抽取显式条件/数值/版本，也不以可审计本体为目标。另一条先例是 [General Video Game Rule Generation / GVG-RG](https://www.researchgate.net/publication/220800018_A_Petri_Net_Approach_for_the_Modeling_and_Analysis_of_Video_Games) 及其 Video Game Description Language（VGDL）传统：研究者把游戏规则表达成可执行语言，并以规则生成作为竞赛问题。它是“形式化规则语言/可执行规则”的证据，不是 LLM-KG construction；原始论文入口和具体版本信息需按正式出版物核验。

### 6.2 对研究空白的解释

游戏规则文本的难点不是普通实体关系：同一规则包含触发事件、前置条件、持续时间、周期重置、资源消耗/产出、概率、例外、优先级、状态转移、否定、版本差异和隐含的作用域。通用 Text2KGBench 的短句与固定 ontology 只覆盖其中一部分；GraphRAG/LightRAG 的社区摘要可能丢失限定词；开放三元组会把“当 X 时才 Y”压扁成永久 `X causes Y`。因此游戏领域仍有可发表的空白：带连续证据的规则事件抽取、条件/时序语义的本体约束、规则到 executable IR 的编译、抽取不确定性到 solver 反例的闭环评测。

## 7. 开源工具、框架与数据集

| 资源 | 用途 | 许可证/活跃度（检索日） | 适用注意 |
|---|---|---|---|
| [Text2KGBench](https://github.com/cenguix/Text2KGBench) | ontology-driven KGC benchmark、评测脚本 | Code Apache-2.0；数据 CC BY 4.0；约 92 stars、4 issues；原始数据另含 CC BY-SA/CC BY-NC-SA 上游条款 | 需保留 TekGen/WebNLG 的上游许可；英文短句，不代表游戏文本 |
| [Microsoft GraphRAG](https://github.com/microsoft/graphrag) | 图抽取、社区发现、GraphRAG 索引 | MIT；约 3.5 万 stars；官方 README 提示主要维护 | 研究代码/产品服务边界要分开；图质量需另测 |
| [HippoRAG](https://github.com/osu-nlp-group/hipporag) | OpenIE KG + PPR 图记忆检索 | MIT；约 4 千 stars | 偏记忆/QA，不是 ontology validator |
| [LightRAG](https://github.com/HKUDS/LightRAG) | KG + vector 双层 RAG、增量索引 | MIT；约 4 万 stars；活跃度高但随时间变化 | stars 是仓库指标，不等于 KGC scientific quality |
| [EDC](https://github.com/clear-nus/edc) | Extract/Define/Canonicalize、schema retriever | 许可证和最新 commit **[unverified]** | 适合研究 schema-free 与 target alignment |
| [KGGen](https://arxiv.org/abs/2502.09956) | 文本到 KG、实体聚类、MINE-1 | Python 包；许可证 **[unverified]** | MINE-1 的 LLM-as-judge 需人工抽样校准 |
| [LLMs4OL](https://github.com/HKUST-KnowComp/LLMs4OL) | LLM ontology learning | 仓库许可证/活跃度需固定版本核验 | 是本体学习，不等于事实保守抽取 |
| [Outlines](https://github.com/dottxt-ai/outlines)、[Guidance](https://github.com/guidance-ai/guidance)、[LM Format Enforcer](https://github.com/noamgat/lm-format-enforcer) | grammar/JSON/schema constrained decoding | 各仓库许可证以当前版本为准；均有公开社区 | 约束格式，不保证证据蕴含或事实正确 |
| [UIE](https://github.com/universal-ie/UIE)、[REBEL](https://github.com/Babelscape/rebel) | 统一 IE/生成式三元组基线 | 公开代码，许可证和模型条款需按仓库复核 | 输出合同通常不足以表达条件、来源、否定和版本 |
| [DocRED](https://github.com/thunlp/DocRED)、[SciERC](https://github.com/allenai/SciERC)、[TACRED](https://nlp.stanford.edu/projects/tacred/) | 文档级关系、科学实体关系、关系抽取 | 各自数据/代码许可不同，须逐项核验 | 可测组件，非游戏规则 benchmark |
| [FEVER](https://fever.ai/)、[ERASER](https://www.eraserbenchmark.com/) | 声明证据与 rationale 评测 | 各项目许可见官网 | 可借鉴 evidence precision/recall，不等于 KG edge gold |
| [Z3](https://github.com/Z3Prover/z3)、[Lean](https://github.com/leanprover-community/mathlib4) | 约束求解、定理证明 | Z3 MIT；mathlib4 Apache-2.0；社区活跃 | 需要先定义可判定 IR；solver 只保证编码模型的结论 |

**开源活跃度的口径：** 本报告记录检索日公开页面的 stars、forks、issues 或官方维护说明；这些是可复核的粗粒度信号，不等于提交频率、维护质量、学术影响或许可证适合商业再分发。数据集还必须追踪上游语料的传递许可，不能只看 benchmark 仓库根目录许可证。

## 8. 评测与 benchmark 现状

### 8.1 已有数据与指标

1. **Text2KGBench：** 固定 ontology、输入句子和事实；覆盖事实提取、ontology conformance、hallucination 等七类指标。适合基础 schema-guided KGC，但缺少长上下文、证据 span、时序/条件和图持续更新。
2. **MINE-1 / KGGen：** 从信息保留角度评估节点和边是否携带源文档事实，缓解传统 exact-match 对开放 schema 不友好问题。其 LLM-as-a-judge 便宜且可扩展，但需人工校准 judge 偏差、实体聚类错误和 paraphrase 宽松度。
3. **TACRED、DocRED、SciERC：** Precision/Recall/F1、跨句关系和科学领域关系等成熟组件评测；但关系集合固定，通常不评价 schema 演化、ontology gap 或抽取后的图一致性。
4. **GraphRAG/HippoRAG/LightRAG 类 benchmark：** 多跳 QA、HotpotQA、MuSiQue、全局问答、retrieval cost/latency 等，测的是下游使用价值；图谱本身的逐边正确性通常没有被充分隔离。
5. **KGQA/逻辑查询：** EPFO、复杂逻辑查询和 multi-hop QA 评价 answer EM/F1、Hits@k 或逻辑查询正确性；这能测推理，但可能掩盖抽取时丢失的限定词与证据。

### 8.2 缺失评测维度

学界已有相对共识的是：单一 triple F1 不够，需同时测事实、结构、幻觉和下游任务；以下是结合上述 benchmark 对游戏规则场景的进一步推断：

- **证据连续性与字段覆盖：** 每条边、数值、条件和限定词是否能回指原文连续 span；不能只给文档级相关性。
- **条件/模态/否定/时序：** `if/unless/only while/once per turn/at reset` 的作用域和规则方向是否正确；目前通用 benchmark 覆盖不足。
- **数值与单位保真：** raw value、范围、单位、周期、概率及舍入；防止模型把“每局”换算成“每分钟”。
- **版本与冲突：** 同一规则在不同版本、模式或来源冲突时是否并存、标注来源而不被错误融合。
- **本体演化：** 新实体类型/谓词加入后旧知识是否保留，domain/range 变化是否可追踪；AdaKGC 提出了任务，但尚未成为广泛标准。
- **保守拒绝能力：** unknown/uncovered 的 precision、recall、拒绝错误关系的比例；不能只奖励召回。
- **图级性质：** 连通性、重复实体率、关系方向一致性、类型层级一致性、冲突边率和可解释路径。
- **solver 可验证性：** 抽取出的规则能否编译成无歧义 IR，求解器反例能否回映到原文证据；`unsat` 只应解释为给定模型和边界下不可满足。
- **运行成本与稳定性：** 多次采样一致性、P50/P95/P99 latency、token/费用、重试率、agent 调用数、模型升级回归，而不是只报告最好一次的 F1。

## 9. 关键发现：共识、事实与本次推断

### 9.1 学界/工程共识

1. LLM 适合做候选发现、语义归一化和少样本迁移，但不能单独充当事实数据库；[Text2KGBench](https://arxiv.org/abs/2308.02357)、EDC、维护短文本实验和 KG 构建综述均支持这一判断。
2. Schema-first 保障一致性，schema-free 提高发现能力；两者各有边界，EDC 的 Extract→Define→Canonicalize 正是折中。
3. 约束解码解决语法/输出空间，ontology validator 解决结构合法性，证据和人工/符号验证解决事实与推理；三者不能互相替代。
4. GraphRAG/Graph memory 的下游 QA 改善不能自动证明构建出的每条边正确。
5. 神经模型与符号 solver 的组合在逻辑任务中具有互补性，但 solver 结论只对被正确编码的模型有效。

### 9.2 本次推断

1. 2023–2026 的主趋势不是端到端取代 pipeline，而是“生成候选—检索/本体对齐—验证/融合—图检索或求解”的分层组合。依据是 EDC、KARMA、Wikontic、SymAgent、KG-Prover 的共同结构，而非单篇论文的口号。
2. 游戏规则 KG 的创新空间主要在**规则语义的可验证表达**，而不是再提出一个通用 OpenIE prompt。依据是 AriGraph 只覆盖交互记忆、Text2KGBench 只覆盖固定本体句子、现有 GraphRAG 以 QA 为主。
3. 对规则文本而言，错误拒绝和证据可回溯应与召回同等重要；否则 ontology 约束可能把模型从“乱抽”变成“结构正确地乱抽”。这是由 schema conformance 与 factual grounding 的层次差异推导出的研究判断。
4. agent 数量本身不是可靠性指标；只有独立证据、确定性 validator 或 solver-backed ablation 才能证明增益。依据 KARMA 等工作仍使用 LLM-verified correctness 的局限。

## 10. 对本项目的具体影响（非选型建议）

1. **研究问题应拆成四层：** 文本证据抽取、游戏领域 ontology 对齐、规则/数值/时序 IR 编译、符号验证。这样可以将 LLM 的开放生成能力与确定性可判定部分分开评价。
2. **贡献定位可避开通用 KGC 已有工作：** 提出面向游戏规则的证据绑定 schema、条件/周期/优先级表达，以及从抽取候选到可执行/可求解规则 IR 的保守编译；与 Text2KGBench、EDC 的差异应通过条件、版本和反例数据集体现。
3. **数据集需扩展既有 benchmark：** 在 Text2KGBench 的 ontology conformance/hallucination 指标上加入规则文档片段、正负条件、否定、资源消耗、概率、状态迁移、版本冲突和无法归类样本；同时标注连续证据。
4. **评测应分离 extraction 与 downstream verification：** 报告 edge/claim precision-recall、证据覆盖、unknown 拒绝、domain/range 违反、实体重复和图级冲突；再报告 solver 可编译率、反例可回溯率以及游戏规则检查结果，不能只给最终 QA 分数。
5. **本体研究不应只测形状：** 对谓词 domain/range、互斥状态、资源守恒、触发条件和时间作用域建立可执行约束；本体未覆盖的规则应进入 `uncovered` 或扩展候选，而不是强行映射到近似关系。
6. **团队/路线比较应按可核验产物：** 记录论文版本、commit、许可证、数据上游许可证、模型版本和 benchmark 配置；stars/引用量只能作规模信号。2026 文献和引用量在检索时尚未稳定，标为 **[unverified]**。

## 11. 风险与未知

- **文献时间风险：** 2026 年新作、引用量和仓库状态可能在本报告日期后变化；表中标 **[unverified]** 的作者、许可证、链接或数字不得当作已核实事实。
- **LLM-as-a-judge 偏差：** KARMA、MINE-1/Wikontic 等结果若主要依赖模型裁判，可能偏好流畅而非忠实输出；需要人工盲评和 judge 互换/校准。
- **ontology 不完备：** 严格约束提高精度也可能降低召回；把未知关系全部拒绝会掩盖 ontology 设计缺口。
- **过度 canonicalization：** 聚类和别名合并能降低稀疏，但同名角色、不同版本实体和相似规则可能被错误合并；必须保留原始 mention、证据和来源。
- **图级幻觉：** 单条边都“看似合理”时，组合出的路径仍可能违反条件、时间或资源守恒；需要图级和 solver 级检查。
- **形式化语义鸿沟：** LLM 生成的逻辑公式、Cypher 或 SMT 约束若语义映射错误，求解器只会可靠地求解错误模型；`UNSAT` 不等于现实规则无反例。
- **agent 可靠性与成本：** 多 agent 可能提高审查覆盖，也可能重复调用、相互确认错误、泄露上下文或死循环；需报告调用图、预算和失败恢复。
- **游戏领域外推不足：** 当前公开游戏工作主要是交互式 agent memory 或可执行规则生成，而不是策划文档到 ontology KG；LudoGraph 类真实资料上的基准、标注一致性和跨游戏泛化仍是 **[unverified]**。
- **许可证与数据合规：** Text2KGBench 的上游 TekGen/WebNLG 有各自条款；论文仓库的代码许可不自动覆盖数据、模型权重和商业输入。复用前必须固定版本并逐项审查。

## 参考来源

1. [A Comprehensive Survey on Automatic Knowledge Graph Construction, ACM Computing Surveys](https://dl.acm.org/doi/10.1145/3618295)
2. [LLM-empowered Knowledge Graph Construction: A Survey](https://arxiv.org/abs/2510.20345)
3. [Text2KGBench: A Benchmark for Ontology-Driven Knowledge Graph Generation from Text](https://arxiv.org/abs/2308.02357)；[仓库与许可证](https://github.com/cenguix/Text2KGBench)
4. [Schema-adaptable Knowledge Graph Construction / AdaKGC](https://arxiv.org/abs/2305.08703)
5. [ChatIE: Zero-shot Information Extraction via Chatting with ChatGPT](https://arxiv.org/abs/2302.10205)
6. [Extract, Define, Canonicalize: An LLM-based Framework for KGC](https://aclanthology.org/2024.emnlp-main.548/)；[代码](https://github.com/clear-nus/edc)
7. [Ontology-guided KG Construction from Maintenance Short Texts](https://aclanthology.org/2024.kallm-1.8.pdf)
8. [GraphRAG](https://arxiv.org/abs/2404.16130)；[Microsoft Research 项目页](https://www.microsoft.com/en-us/research/project/graphrag/)；[MIT 仓库](https://github.com/microsoft/graphrag)
9. [HippoRAG](https://proceedings.neurips.cc/paper_files/paper/2024/file/6ddc001d07ca4f319af96a3024f6dbd1-Paper-Conference.pdf)；[仓库](https://github.com/osu-nlp-group/hipporag)
10. [LightRAG](https://arxiv.org/abs/2410.05779)；[仓库](https://github.com/HKUDS/LightRAG)
11. [KGGen](https://arxiv.org/abs/2502.09956)
12. [KARMA](https://arxiv.org/abs/2502.06472)
13. [Graphusion](https://arxiv.org/abs/2407.10794)
14. [AriGraph](https://www.ijcai.org/proceedings/2025/2)
15. [AGENTiGraph](https://arxiv.org/abs/2508.02999)；[仓库](https://github.com/SinketsuZao/AGENTiGraph)
16. [Wikontic](https://arxiv.org/abs/2512.00590)；[仓库](https://github.com/screemix/Wikontic)
17. [Dialogue Ontology Relation Extraction via Constrained CoT Decoding](https://aclanthology.org/anthology-files/anthology-files/pdf/sigdial/2024.sigdial-1.33.pdf)
18. [PARSE: LLM Driven Schema Optimization for Reliable Entity Extraction](https://aclanthology.org/2025.emnlp-industry.184.pdf)
19. [SymAgent: A Neural-Symbolic Self-Learning Agent Framework](https://arxiv.org/abs/2502.03283)
20. [Logic Query of Thoughts](https://arxiv.org/abs/2404.04264)
21. [KG-Prover: Scaling Natural-Language Graph-Based Test Time Compute](https://arxiv.org/html/2503.11657)
22. [AGENTiGraph / multi-agent KG interaction](https://arxiv.org/abs/2508.02999)
23. [GVG-RG / General Video Game Rule Generation 检索入口](https://www.researchgate.net/publication/220800018_A_Petri_Net_Approach_for_the_Modeling_and_Analysis_of_Video_Games)
24. [LLMs4OL](https://github.com/HKUST-KnowComp/LLMs4OL)
25. [Outlines](https://github.com/dottxt-ai/outlines)、[Guidance](https://github.com/guidance-ai/guidance)、[LM Format Enforcer](https://github.com/noamgat/lm-format-enforcer)
26. [DocRED](https://github.com/thunlp/DocRED)、[SciERC](https://github.com/allenai/SciERC)、[TACRED](https://nlp.stanford.edu/projects/tacred/)
27. [FEVER](https://fever.ai/)、[ERASER](https://www.eraserbenchmark.com/)
28. [Z3](https://github.com/Z3Prover/z3)、[Lean/mathlib4](https://github.com/leanprover-community/mathlib4)
