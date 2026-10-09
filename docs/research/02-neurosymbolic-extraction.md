# LUDO-3：本体受限的神经符号抽取调研

> **调研日期：2025-02-14**
> **检索范围：** 公开论文、评测数据集、开源约束解码/信息抽取工具，以及 OpenAI、Anthropic、Google、JSON Schema 等官方文档；重点覆盖 2022–2025 年的 LLM 结构化输出、schema-guided extraction、证据绑定、幻觉控制与信息抽取评测。本文只给出抽取层路线建议，不修改 LudoGraph 设计或本体。

## 1. 背景

LudoGraph 的抽取输入是策划文档中的自然语言、表格或半结构化片段，输出是受本体约束的 `nodes`、`claims`、`uncovered`，并且每条结果要保留连续原文证据、限定值和四态 `certainty`。抽取层的目标不是让模型“理解后补全一个合理世界”，而是把**原文明确说出的事实**转换为可校验候选；缺少证据、无法归类或需要跨文档推断的内容应拒绝导入或进入 `uncovered`。

这与一般 JSON 信息抽取有一个重要差别：JSON 合法并不等于事实正确。需要同时解决四个层次：

1. **结构约束：** 输出是合法 JSON，字段、枚举、类型和嵌套关系符合 schema。
2. **本体约束：** 节点标签、谓词、domain/range、限定字段和命名空间符合 LudoGraph ontology。
3. **证据约束：** 每一项都能定位到输入 chunk 中的连续子串；不能凭模型常识添加因果、换算或实体合并。
4. **语义/业务审核：** 候选事实可能仍然错误，必须通过规则校验、冲突保留和人工抽样评估。

## 2. 国内外现状

### 2.1 结构化输出、schema-guided extraction 与约束解码

当前实践大致分为三档：

- **提示式 JSON/schema：** 把字段定义、枚举和示例放入 prompt，让模型生成 JSON。实现简单、适合快速试验，但只能形成软约束，模型可能漏字段、加字段或输出不符合类型的值。
- **API 级结构化输出/function calling：** 工具调用将参数声明为 JSON Schema，模型返回参数对象。OpenAI 的 Structured Outputs 文档明确区分了普通 JSON mode 与 `strict: true` 的 schema adherence；Anthropic 的 tool use 和 Google Gemini 的 structured output 也提供类似的 schema/function-call 接口。[OpenAI Structured Outputs](https://openai.com/index/introducing-structured-outputs-in-the-api/)、[OpenAI function calling](https://platform.openai.com/docs/guides/function-calling)、[Anthropic tool use](https://docs.anthropic.com/en/docs/build-with-claude/tool-use)、[Gemini structured output](https://ai.google.dev/gemini-api/docs/structured-output)。
- **解码时硬约束：** 在 token 生成过程中限制可行 token，使输出满足 JSON Schema、CFG、正则或有限语法。代表性开源项目包括 [Outlines](https://github.com/dottxt-ai/outlines)、[Guidance](https://github.com/guidance-ai/guidance)、[LM Format Enforcer](https://github.com/noamgat/lm-format-enforcer) 和 [llama.cpp grammar](https://github.com/ggerganov/llama.cpp/blob/master/grammars/README.md)。这类方法通常能显著降低格式错误，但不自动保证事实与证据正确；复杂 schema 还会带来编译、吞吐和模型兼容性成本。

对于 LudoGraph，最稳妥的工程组合不是让模型直接生成图数据库语句，而是让模型生成一个**版本化、封闭的中间 JSON 合同**，再由确定性 validator 做二次校验。schema 负责形状，本体 validator 负责语义白名单，导入层负责投影。

### 2.2 信息抽取与本体/知识图谱方向

传统联合实体关系抽取（如 [TACRED](https://nlp.stanford.edu/projects/tacred/)、[DocRED](https://github.com/thunlp/DocRED)、[SciERC](https://github.com/allenai/SciERC)）已经形成实体、关系、跨句推理和证据评测范式。LLM 时代的代表性方向包括：

- [Universal Information Extraction (UIE)](https://github.com/universal-ie/UIE) 以统一结构表达不同抽取任务，说明“任务 schema + 统一解码”具有可迁移性。
- [REBEL](https://github.com/Babelscape/rebel) 将文本转为关系三元组，展示了生成式关系抽取的可行性，但裸三元组合同不够表达限定值、否定、来源和不确定性。
- [LLMs4OL](https://github.com/HKUST-KnowComp/LLMs4OL) 研究用 LLM 完成 ontology learning，并提供基准任务。它更接近本体学习而非“已给定本体下的保守抽取”，可借鉴评测思路但不能直接当作 LudoGraph 抽取方案。
- [ExtractBench](https://github.com/Team-TTT/ExtractBench) 评估 LLM 的复杂结构化抽取能力，反映了字段嵌套、格式和长文本方面的难点。[unverified] 该基准覆盖范围和最新模型排行会随仓库版本变化，应在选型时固定 commit 和数据版本。

总体成熟度是：**结构化格式控制已经产品化；受固定本体约束的开放域抽取仍需领域 validator 和数据集；连续证据、保守不推断和版本化冲突处理没有被通用 API 自动解决。**

### 2.3 CoT 在抽取任务中的证据与限制

[Chain-of-Thought Prompting Elicits Reasoning in Large Language Models](https://arxiv.org/abs/2201.11903) 和 [Self-Consistency Improves Chain of Thought Reasoning](https://arxiv.org/abs/2203.11171) 表明，分步推理/多路径采样可改善一部分需要组合推理的任务。对抽取而言，CoT 可能帮助模型先识别实体、关系、条件和数值，再组装 claim；对跨句关系、否定和条件范围尤其可能有帮助。

但这些结果主要来自数学、常识和推理基准，不能直接推出“CoT 一定提升信息抽取”。抽取还要求**忠实于输入**，而长篇自由推理会增加模型把常识当作文本事实的机会。关于解释不忠实，见 [Turpin et al., 2023](https://arxiv.org/abs/2305.04388)；关于 CoT 的成本、脆弱性和并非普遍增益，见 [CoT 综述](https://arxiv.org/abs/2309.15402)。因此建议：

- 默认不把内部 CoT 作为结果字段，也不把它当证据；证据只能来自原文连续 span。
- 仅在需要跨句归因、条件范围或复杂数值解析时启用“短步骤、隐藏思考、结构化中间字段”。
- 先做无 CoT 与短步骤版本的消融；若 CoT 只提高召回却提高 unsupported-claim rate，应弃用。
- 对高风险规则采用“两次独立抽取/抽取+审查”而非无限延长 CoT。[推断] 依据是上述研究说明推理能力与解释忠实性是不同属性，故应分别测量。

### 2.4 证据绑定（evidence grounding）

证据绑定常见方法有三类：

1. **字符/词 token span：** 输出 `start`、`end` 和 `quote`，服务端检查 `quote == chunk[start:end]`。这是最适合 LudoGraph 的方法，因为连续性和可复核性明确。
2. **句子/段落引用：** 输出句子 ID 或文档页码，适合长文档但不够精细；应作为定位信息，不能替代连续 quote。
3. **检索证据 + 生成：** RAG 系统先检索片段，再要求回答带引用。它降低上下文长度，却不能证明每个字段都被证据支持；需要逐字段 entailment/coverage 检查。

可复用的评测资源包括 [FEVER](https://fever.ai/)、[ERASER benchmark](https://www.eraserbenchmark.com/)（含 evidence selection）、[Evidence Inference](https://github.com/jayded/medical-evidence-inference) 和 [DocRED supporting facts](https://github.com/thunlp/DocRED)。这些数据集的任务定义不同：FEVER 侧重声明是否被证据支持，ERASER 同时评估 rationale，DocRED 侧重文档级关系。它们可借鉴指标与人工标注流程，但不等价于游戏策划规则。

推荐将 evidence 作为不可变输入片段的引用，而非让模型自由改写：

```json
{"quote":"每次使用消耗2枚冰晶","start":123,"end":133}
```

validator 应检查：边界合法；quote 是 chunk 的连续子串；subject、predicate、object、quantity、condition 各自至少有支持片段；不能引用 chunk 外上下文。若只有“看起来相关”的证据而没有明确蕴含，应转 `uncovered` 或降低 certainty，而不是创建 confirmed claim。

### 2.5 幻觉、过度推断与身份合并控制

单一 prompt 无法阻止以下错误：把“可能”变成事实、从顺序推导因果、把“每回合”换算成“每分钟”、把同名角色跨文档合并、把相关性扩成 `REQUIRES`。可组合的控制手段如下：

- **封闭世界输出：** 只允许本体枚举的标签/谓词，未知谓词进入 `uncovered`；禁止 `RELATED_TO` 兜底。
- **证据门槛：** 无连续原文 span 的节点/claim 不得导入；quote 必须由代码校验。
- **原文保真数值：** 保存 `raw`、unit、范围和 qualifier；只有明确可解析时才填归一化 value，禁止隐式换算。
- **否定、可能和计划分开：** `certainty` 记录原文语气而非模型置信度；`negated` 不应转为正向图边。
- **实体对齐隔离：** 局部 ID 只在 chunk 内有效；跨 chunk 合并需要独立 entity-link 流程、候选证据和人工审核，不能按同名自动合并。
- **独立校验/拒答：** schema validator、ontology validator、evidence validator 和数值/范围 validator 分层；失败返回可解释错误并保留原文。
- **冲突不覆盖：** 不同来源的矛盾 claim 并存，交给后续审核；不要用模型“综合”为一个新事实。

[Neural-symbolic approaches: a survey](https://arxiv.org/abs/2109.05308) 概括了神经提议、符号约束/验证的通用范式；它支持“LLM 提议、确定性系统裁决”的架构判断，但不是 LudoGraph 抽取质量的直接实证。

## 3. 关键发现

1. **最成熟的可复用能力是结构控制，不是事实正确性。** 官方 Structured Outputs/function calling 可减少 JSON/schema 错误；仍须自建证据、ontology 和业务校验。
2. **约束解码应分层。** token/grammar 层解决语法，JSON Schema 层解决字段类型，本体层解决合法标签和 domain/range，规则层解决不应发生的推断。把所有规则塞入 prompt 不如在后处理建立硬拒绝。
3. **CoT 是可选优化，不是抽取合同。** 复杂跨句抽取可试短步骤，但必须以 evidence-supported precision、unsupported claim rate 和 recall 的消融结果决定是否启用。
4. **连续证据是低成本、高收益的可信边界。** span 校验能直接阻止“没有原文”的幻觉，却不能保证 quote 真的蕴含整个 claim；因此仍要做字段级 entailment/人工审核。
5. **游戏策划文本的直接公开 benchmark 很少。** 通用数据集能测组件能力，但不能代表 LudoGraph 的条件、时序、数值、版本和 `uncovered` 需求。[unverified] 未发现公开、成熟且专门针对游戏策划文档的 ontology-constrained extraction benchmark。

## 4. 对本项目的具体影响

### 4.1 推荐技术路线

**推荐：受限 JSON 合同 + 两阶段 LLM + 确定性验证器 + 保守导入。**

1. 对每个 chunk 固定 `ontology_version`、scope 和输入文本；模型只生成 `nodes`、`claims`、`uncovered`。
2. 优先使用支持严格 JSON Schema 的托管模型；自部署时使用 Outlines/LM Format Enforcer/llama.cpp grammar 等约束解码方案。[unverified] 不同 provider 对复杂 JSON Schema、流式输出、refusal 和 schema 子集的支持并不完全一致，接入前需做兼容性测试。
3. 对复杂关系采用“候选抽取 → 证据/本体审查”两次调用，而不是让一次调用直接写图数据库。第二阶段只能引用第一阶段候选和原文，不能新增无证据事实。
4. 本地 validator 严格检查 schema、枚举、domain/range、局部 ID、连续 quote、限定值 raw/unit、certainty 和重复/冲突规则。
5. 通过规则模板把通过验证的候选导入图谱；失败项保留为 `uncovered`，并记录原因码。导入层不调用 LLM 做自动修复后直接落库。
6. 高风险 claim（数值、经济产出、解锁条件、身份合并）设置人工审核或双模型一致性门槛；低风险显式节点可自动导入。[推断] 这是在成本和错误影响之间的分级控制，不代表“双模型一致”就是事实证明。

### 4.2 备选路线

- **低成本路线：** 单模型 JSON Schema + validator + 失败重试。适合 PoC，风险是语义错误和证据错配较多。
- **高可靠路线：** 小模型/规则做候选 span 和实体边界，大模型只做关系分类与 qualifier 组装，再用符号 validator 裁决。成本更高，但可降低自由生成空间。
- **本地路线：** 开源 instruct 模型 + grammar constrained decoding + LoRA/少样本微调。适合数据不可出域，但需要自行维护推理服务、schema 兼容性和回归集。
- **知识库/RAG 辅助路线：** 先检索术语和本体候选，再抽取。只能辅助消歧，不能把检索到的背景知识当作当前 chunk 的证据。

### 4.3 可直接复用与必须自研

**可以直接复用：**

- OpenAI/Anthropic/Gemini 的 function calling/structured output 接口（或同类供应商能力）。
- Outlines、Guidance、LM Format Enforcer、llama.cpp grammar 等约束解码组件。
- JSON Schema validator（如 [jsonschema](https://json-schema.org/) 生态）。
- DocRED、SciERC、TACRED、FEVER、ERASER 的数据格式、span/evidence 评测思路。
- UIE/REBEL 的 few-shot 任务组织方式；不能直接复用其输出合同。

**必须自研：**

- LudoGraph ontology 的版本化 schema、domain/range 和限定字段 validator。
- `nodes`/`claims`/`uncovered` 合同与四态 certainty 的映射规则。
- 连续 quote 的 offset 校验、Unicode/分词边界处理和字段级证据覆盖检查。
- 游戏领域的条件、触发、周期、数量、概率、否定、冲突和版本语义解析规则。
- 跨 chunk entity linking、冲突并存、人工审核队列和风险分级策略。
- 游戏策划文档 gold set、错误注入集和端到端回归基准。

## 5. 评测方案建议

### 5.1 数据组成

建立三层数据集并固定版本：

1. **合成控制集：** 由模板生成显式节点、关系、否定、条件、数量、范围、概率、时序和同名实体；可精确计算真值。
2. **脱敏真实集：** 不同玩法、不同作者和不同文档格式的策划片段；每片段由两名标注者标注 nodes、claims、uncovered、连续 evidence、certainty 和 qualifier，第三人解决分歧。
3. **对抗集：** 人工注入因果过推、数值换算、实体同名、否定范围、跨 chunk 泄漏、冲突版本、表格/列表歧义和无证据常识。对抗集用于验证“拒绝错误”能力。

同时保留按文档/游戏划分的测试集，避免同一实体名和模板泄漏到训练集。

### 5.2 指标与计算

- **结构通过率：** `valid_json / all_outputs`；包括 schema、枚举、引用完整性。
- **节点/claim micro Precision、Recall、F1：** 以 canonical label、关系方向和局部实体对齐后的 gold 为准；严格匹配与宽松匹配分别报告。
- **证据 span：** Exact Match、token-level precision/recall/F1；另报 `supported_claim_rate = 有明确 gold evidence 的 claim 数 / 全部输出 claim 数`。
- **证据连续性：** `quote == chunk[start:end]` 的比例，应达到 100%；这是代码约束指标而非模型平均分。
- **幻觉/过度推断率：** `unsupported_claims / all_claims`；把因果、换算、身份合并错误单独分桶。
- **保守性：** `correctly_rejected / (correctly_rejected + false_positive)`，以及 `uncovered recall`（gold 中应拒绝项被放入 uncovered 的比例）。不能只追求 recall。
- **数值与限定值准确率：** raw、unit、range、direction、condition、cycle 分字段计算 exact match；禁止换算的案例单独计数。
- **certainty 准确率：** 四态 macro-F1；模型置信度不得混入该指标。
- **本体一致性：** domain/range、谓词白名单、类型约束违反率，目标为 0（上线前硬门槛）。
- **稳定性和成本：** 同一输入多次运行的一致率、P50/P95 延迟、token/费用、重试率；报告 temperature、模型版本和 schema 版本。

### 5.3 建议的通过门槛

首版可采用以下**工程建议值**，不是外部事实，需在内部数据上校准：

- JSON/schema/domain-range/证据连续性硬错误：`0`（validator 拒绝，不以平均分掩盖）。
- 受支持 claim 的 precision ≥ 0.95；unsupported claim rate ≤ 0.02。
- claim strict micro-F1 ≥ 0.85；证据 token-F1 ≥ 0.90。
- 高风险数值/条件 claim precision ≥ 0.98；跨文档自动实体合并默认不自动通过。
- 对抗集中的因果、换算、同名合并错误拒绝率 ≥ 0.95。
- 相比无 CoT 基线，启用 CoT 必须在 recall/F1 上有稳定提升，且 unsupported claim rate 不上升超过 0.5 个百分点；否则关闭 CoT。

这些门槛应在至少两轮标注后用置信区间复核。任何模型升级、ontology 版本变化或 prompt 变化都要跑完整回归集。

## 6. 风险与未知

- **模型/API 约束边界：** 各厂商对 JSON Schema 子集、拒答、流式和工具调用的行为不同；以官方文档为准仍不足以预测所有嵌套 schema 组合。[unverified]
- **证据蕴含难判定：** quote 连续且相关，不代表它支持 claim 的全部方向、条件和数量；需要规则 + NLI/人工复核，且 NLI 本身可能幻觉。
- **长文档和跨 chunk 关系：** 强行在单 chunk 输出会漏召回，放开跨 chunk 又容易引入无证据合并。第一版应明确只允许 chunk 内证据，跨 chunk 另设流程。
- **本体覆盖不足：** `uncovered` 增多可能表示模型差，也可能表示 ontology 尚未覆盖真实需求；不能把所有 uncovered 简单当失败。
- **标注成本与一致性：** certainty、条件范围和“明确因果”常需专家判断；应报告 inter-annotator agreement，并保留争议样本。
- **CoT 可见性和隐私：** 不应把模型内部推理当审计日志或对用户承诺；审计对象应是输入、输出、validator 结果和证据 span。
- **“神经符号”边界：** JSON Schema/本体校验是硬约束，但不等于形式化证明事实为真；最终可信度仍取决于原文质量、标注和人工治理。
- **直接游戏领域证据不足：** [unverified] 当前公开工作尚不足以证明某个通用模型在 LudoGraph 类文本上达到上述门槛，必须用自建 gold set 做选型。

## 7. 结论

LudoGraph 应采用“**LLM 提议、schema/grammar 限形、本体 validator 限义、连续证据验真、失败进入 uncovered、人工/规则系统裁决**”的抽取路线。托管 structured output 或开源 constrained decoding 可以直接复用；LudoGraph 的证据合同、四态 certainty、限定值保真、冲突并存、跨文档身份策略和游戏领域评测必须自研。

该路线的关键取舍是宁可少抽、明确暴露 `uncovered`，也不把模型常识伪装成图谱事实。CoT 只作为可测量的局部优化，不作为抽取可信性的来源；可信性来自可验证的原文 span、封闭本体、确定性拒绝和持续回归评测。

## 参考来源

1. OpenAI, *Introducing Structured Outputs in the API*: <https://openai.com/index/introducing-structured-outputs-in-the-api/>
2. OpenAI, *Function calling*: <https://platform.openai.com/docs/guides/function-calling>
3. Anthropic, *Tool use*: <https://docs.anthropic.com/en/docs/build-with-claude/tool-use>
4. Google, *Structured output*: <https://ai.google.dev/gemini-api/docs/structured-output>
5. Outlines: <https://github.com/dottxt-ai/outlines>
6. LM Format Enforcer: <https://github.com/noamgat/lm-format-enforcer>
7. Wei et al., *Chain-of-Thought Prompting*: <https://arxiv.org/abs/2201.11903>
8. Wang et al., *Self-Consistency*: <https://arxiv.org/abs/2203.11171>
9. Turpin et al., *Language Models Don’t Always Say What They Think*: <https://arxiv.org/abs/2305.04388>
10. Kojima et al., *Large Language Models are Zero-Shot Reasoners*: <https://arxiv.org/abs/2205.11916>
11. Thorne et al., *FEVER*: <https://fever.ai/>
12. DeYoung et al., *ERASER*: <https://www.eraserbenchmark.com/>
13. Yao et al., *DocRED*: <https://github.com/thunlp/DocRED>
14. Zhang et al., *Universal Information Extraction*: <https://github.com/universal-ie/UIE>
15. Cabot & Navigli, *REBEL*: <https://github.com/Babelscape/rebel>
16. LLMs4OL: <https://github.com/HKUST-KnowComp/LLMs4OL>
17. ExtractBench: <https://github.com/Team-TTT/ExtractBench>
18. Garcez et al., *Neural-Symbolic Learning and Reasoning: A Survey*: <https://arxiv.org/abs/2109.05308>
19. JSON Schema: <https://json-schema.org/>
