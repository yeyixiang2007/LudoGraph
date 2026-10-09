# 图谱存储选型与 Claim 持久化研究

> 调研日期：2026-10-09  
> 检索范围：Neo4j、Kùzu/LadybugDB、Memgraph、FalkorDB、Apache AGE、Oxigraph/GraphDB 官方文档、仓库与公开基准；重点核查 LPG/Cypher、部署与许可、断言模型及性能证据。价格与基准随版本和部署条件变化，未有可比证据处明确标注。

## 背景

LudoGraph 采用有向属性图本体，claim 包含 subject、predicate、object、限定值、certainty、证据与来源；要求事实可以回溯原文，矛盾说法并存，不因同名节点自动合并。当前设计将抽取合同与物理存储分离，考虑直接投影为关系或存为独立 Assertion。系统目标包括高并发和毫秒级查询，但没有给出数据规模、写入峰值、可用性或多租户威胁模型。本报告据此推荐先建立可替换的实现基线，而不是宣称某产品必然满足尚未量化的 SLO。

## 国内外现状

以下为截至检索日的公开资料判断，并非完整市场调查。

| 方案 | 图模型/语言 | 部署与许可/成本 | 对本项目的判断 |
|---|---|---|---|
| Neo4j | 原生 LPG，Cypher；关系可携带属性。官方手册提供约束、索引、事务等成熟能力。 | Community 为 GPLv3，Enterprise 商业许可；需自行核验具体部署和分发场景的许可义务。服务端产品和托管产品生态成熟。 | LPG 与属性丰富的 claim 匹配度高，运维和工具生态强；服务端隔离、并发事务适合共享服务。成本/许可需评估。 |
| Kùzu | 结构化 LPG、openCypher 子集；嵌入式、进程内，磁盘/内存模式。 | 原项目 MIT，但 GitHub 项目已标注 archived；原 Kùzu 不宜作为新项目长期依赖。 | 过去作为嵌入式分析引擎有吸引力，但项目停止维护风险高。 |
| LadybugDB | Kùzu 社区 fork，嵌入式 LPG/Cypher，预定义 schema。 | 仓库标示 MIT；新项目、社区和升级兼容性仍在演进。 | 若单实例嵌入式部署、分析优先且可接受维护风险，可作为候选，不应误称为仍活跃的 Kùzu 原项目。 |
| Memgraph | LPG/Cypher，服务端；强调流式/实时图处理。 | Community 当前采用 BSL 1.1（非 OSI 开源许可，变更日后切换许可），Enterprise MEL。 | 若实时流处理是核心可复评；对目前主要为溯源断言及图遍历的需求，没有证据显示明显胜过 Neo4j。 |
| FalkorDB | LPG、兼容 Redis 协议的服务端图数据库，使用 Cypher 方言。 | 社区版许可及托管成本应按选定版本/产品条款核对；部署模型偏服务端。 | 低延迟服务端候选，但方言兼容性、治理和关系约束需 PoC 验证。 |
| Apache AGE | PostgreSQL 扩展，openCypher 风格查询与 SQL/PostgreSQL 结合。 | Apache 2.0；基于 PostgreSQL，适合复用现有 PG 运维，但扩展版本、查询能力和升级矩阵需要管理。 | 若团队已有 PostgreSQL 且希望同库联结图/关系数据，可考虑；原生图工具链与 LPG 功能完整度需实测。 |
| Oxigraph / GraphDB | RDF 三元组/四元组与 SPARQL，而非 LPG/Cypher。Oxigraph 开源；GraphDB 产品许可/费用按版本核验。 | RDF 生态有本体、推理和语义网工具；需把现有关系属性模型映射为 RDF（如 reification/named graph）。 | 只有当互操作、OWL/RDF 推理成为优先目标时更适合；当前 canonical 关系类型和边属性是 LPG 形态，迁移会增加建模成本。 |

资料链接：
- Neo4j 开源/许可说明：[Community 与 Enterprise](https://neo4j.com/open-source-project/)、[open-core FAQ](https://neo4j.com/open-core-and-neo4j/)
- Neo4j [Cypher relationship patterns](https://neo4j.com/docs/cypher-manual/current/patterns/reference/node-and-relationship-patterns/)、[constraints](https://neo4j.com/docs/cypher-manual/current/schema/constraints/)
- Kùzu [仓库（归档状态）](https://github.com/kuzudb/kuzu)、[Cypher 手册](https://kuzudb.github.io/docs/cypher/)、[快速入门/嵌入部署](https://kuzudb.github.io/docs/get-started/)
- LadybugDB [仓库与许可](https://github.com/LadybugDB/ladybug)、[文档](https://docs.ladybugdb.com/)、[Cypher 手册](https://docs.ladybugdb.com/cypher/)
- Memgraph [仓库及许可说明](https://github.com/memgraph/memgraph)、[BSL 许可文件](https://github.com/memgraph/memgraph/blob/master/licenses/BSL.txt)
- [Apache AGE](https://age.apache.org/)
- [Oxigraph 仓库](https://github.com/oxigraph/oxigraph)、[SPARQL 能力说明](https://github.com/oxigraph/oxigraph/wiki/SPARQL)
- FalkorDB：[官方文档](https://docs.falkordb.com/)、[仓库](https://github.com/FalkorDB/FalkorDB)。GraphDB：[产品页](https://www.ontotext.com/products/graphdb/)。

## 关键发现

### 数据库选型

**建议基线：Neo4j Community 作为第一阶段服务端 PoC；生产部署前完成许可与容量/可用性核算。** 理由是它直接支持本项目的 LPG、关系属性、Cypher 查询和多条平行关系，并有成熟文档、工具和开发者生态。用 Assertion 节点建模可减少对特定数据库关系唯一性能力的依赖。此结论是基于需求贴合度及生态成熟度的工程判断，不是经同一工作负载基准证明的性能排名。

Kùzu 的嵌入式模式不需单独服务，适合本地工具或分析；但其仓库已归档，维护风险使其不宜成为新系统默认。LadybugDB 是承接该嵌入式方向的社区 fork，值得在明确接受年轻项目风险时测试，不能把旧 Kùzu 基准当作 Ladybug 当前版本基准。

**结论翻转条件：**
1. 已有稳定的 PostgreSQL 运维、要求同事务/SQL 集成且 AGE PoC 满足查询和并发 SLO：优先 AGE。
2. 产品确定为单机/进程内嵌入式分析、无需多个应用实例共享写入，并且 LadybugDB 维护/升级风险可接受：改选 LadybugDB。
3. 需要 RDF/OWL 推理、标准语义数据交换或既有 RDF 资产：转向 RDF store（如 GraphDB/Oxigraph），重做模型映射评估。
4. Neo4j 许可限制、总拥有成本或目标峰值不满足要求，且 FalkorDB/Memgraph 在真实负载 PoC 中胜出：按许可、兼容性和运维差异重新选择。

### Claim 两种存储模型

| 维度 | Claim 直接成为关系 | 独立 `Assertion` 节点 |
|---|---|---|
| 读取常见三元组 | 一跳 `subject-[predicate]->object` 直接遍历，路径查询简洁，通常少一次节点连接。 | 需通过 Assertion 的 subject/object 连接或显式端点属性；查询更冗长，路径可能多一跳。 |
| 证据/来源/限定值 | 可放关系属性中；数量、JSON/list 属性能力和索引方式依产品而异。 | 属性放 Assertion，能表达完整生命周期、审计字段与多证据集合；便于按 assertion_id 定位/索引。 |
| 重复/冲突 | LPG 通常允许同端点、同类型平行关系；每条可有独立属性。但若把同一 claim 重复导入，需应用层幂等键/唯一约束。 | 天然一条断言一节点；不同来源、相反 certainty、甚至相同内容的不同来源都可独立共存。 |
| 修订/废弃 | 原地更新关系会覆盖历史；需保留版本/替代关系或改为软删除并另建关系。生命周期审计较脆弱。 | 新建修订版并通过 `supersedes` 指向旧断言，旧项设 `status=deprecated`，保留可审计历史。 |
| 聚合/图遍历 | 适合只关心“当前有效事实”的高频拓扑遍历。 | 多一次关系/节点展开成本，但溯源、冲突、时间切片和复核查询直接。 |

Neo4j 手册描述关系模式和关系属性，并支持关系属性唯一约束（受版本/Edition 能力影响）；不可假定其他数据库约束完全相同。对本项目，溯源与冲突共存是数据正确性核心，**建议把 Assertion 作为规范存储**；可在验证通过后为热点查询建立/物化直接边投影，但投影不能取代规范断言历史，且须声明其一致性刷新策略。

### 建议 schema

```text
(:Entity {entity_id, game_id, system_id, label, name, ...})
(:Assertion {
  assertion_id, game_id, system_id,
  predicate, certainty, status,
  qualifiers, ontology_version,
  source_id, chunk_id, evidence,
  valid_from, valid_to, created_at, updated_at,
  revision, content_hash
})
(:Entity)-[:ASSERTS_SUBJECT_OF]->(:Assertion)
(:Assertion)-[:ASSERTS_OBJECT]->(:Entity)
(:Assertion)-[:SUPERSEDES]->(:Assertion)
```

建议约定：
- `status` 至少为 `active`、`deprecated`、`rejected`；`certainty` 保持抽取合同的 `explicit/possible/planned/negated`，两者语义不可混为一谈。
- 每个来源的说法独立建 Assertion。互相矛盾的 claim 不做覆盖、不以同一 `(subject,predicate,object)` 唯一键去重；可以另建审核/冲突分组字段或 `CONTRADICTS` 边，但不得自动裁决。
- 修订采取追加版本：新 Assertion 通过 `SUPERSEDES` 指向旧版本；旧项标为 deprecated，保留原文证据。废弃不物理删除。若来源文本本身撤回，则另记录撤回事件/状态变更审计。
- `evidence` 可初期存结构化数组（原文 quote、offset、source/chunk 引用）；若需单条证据独立复用/权限控制，再拆成 Evidence 节点。
- 节点唯一性按 `(game_id, system_id, entity_id)` 管理；实体对齐由受控流程负责。每条边/节点的 namespace 都保存范围，查询必须显式过滤 `game_id` 与必要的 `system_id`，防止跨游戏串读。
- 持久 `assertion_id` 用导入端确定性生成：对规范化 tuple `(game_id, system_id, source_id, chunk_id, 局部 claim id 或 source span, revision)` 做 SHA-256，再编码为稳定 ID。不要仅哈希三元组，否则不同来源的冲突会被错误合并；重抽取同一来源应通过版本/内容策略明确决定复用还是新增。局部 `c1` 仅批次内 ID，不作为全局键。
- 按数据库建立唯一约束/索引：Assertion `assertion_id` 唯一；Entity namespace+entity_id 唯一；对 `game_id,system_id,status,predicate` 及 `source_id,chunk_id` 建查询所需索引。不同产品约束语法/能力须验证。

### 性能证据与预期

公开基准不构成跨产品可比的写入峰值或毫秒 SLA。检索到的 [Kùzu study](https://github.com/prrao87/kuzudb-study) 比较嵌入式 Kùzu 与 Neo4j Community，在人工社交网络及特定版本/查询下测试；[其说明文章](https://thedataquarry.com/blog/embedded-db-2) 强调这是特定 join-heavy workload。该结果不能推出 LudoGraph 写入吞吐，且仓库原 Kùzu 已归档。LDBC SNB 等标准基准可提供更规范图查询工作负载，但必须核对产品版本、配置、硬件、scale factor 和更新 workload；本次未找到足以证明所有候选在同一配置下可比的公开数据。

**可验证的预期（估算，不是事实/保证）：** 单机 SSD、常驻服务、索引已热、图数据可容纳于内存的中小型项目，带 namespace/predicate 过滤的索引查 Assertion，再展开 subject/object 的简单查询有机会达到数毫秒量级；多跳遍历、冷缓存、宽范围聚合、写入锁竞争、同步持久化可能显著超过毫秒。该估算仅作为 PoC 假设，没有公开 benchmark 直接验证。不能在缺少数据规模与硬件时诚实承诺高并发写入数值。

建议在选型阶段跑可复现 PoC：使用预计实体/断言数量与 10 倍增长数据，混合执行批量导入、并发追加 Assertion、按游戏/系统/predicate 查询、冲突审计和 1–3 跳图查询；报告 p50/p95/p99、吞吐、CPU/RAM、索引/存储体积、写入与查询并发下的尾延迟。记录硬件、数据库和驱动版本、配置、数据分布及事务大小。SLO、峰值、数据量需由产品侧补齐后才能判定达标。

## 对本项目的具体影响

1. 继续保留与数据库无关的抽取 claim 合同；导入层负责稳定 ID、幂等、事务与 namespace。
2. 将 `Assertion` 节点作为可审计规范记录，关系连接承担 subject/object 角色；普通直接边投影作为后续可选优化，不作为事实唯一来源。
3. 先用 Neo4j 做服务端基线 PoC；把导入器/查询接口限制在应用适配层，便于在许可、性能或运维条件触发时切换 AGE/FalkorDB 等候选。
4. 对证据与来源建强制校验：不能缺 source/chunk/evidence；导入时校验谓词白名单、端点 namespace 一致、ID 唯一和修订链合法。
5. 查询 API 必须注入 `game_id`（及可选 `system_id`）过滤，不能依赖调用方偶然附加过滤条件。若用户权限不同，另需数据库/服务层授权隔离，namespace 字段本身不是安全边界。

## 风险与未知

- Neo4j Community GPLv3 的使用、修改、分发和网络服务适用边界需由法务按实际交付方式确认；Enterprise 成本未在本报告估价。
- Kùzu 已归档；LadybugDB 虽承接代码与方向，但新项目的长期维护、版本兼容和生产案例仍需持续观察。[Kùzu 状态来源](https://github.com/kuzudb/kuzu/)。
- 存储数据库版本、Edition、约束/索引功能可能不同；不能把 Neo4j 关系约束等同为全行业通用功能。
- 高并发“写”定义缺失（单写者/多写者、事务大小、持续时间、峰值、HA），毫秒级查询缺少 p95/p99 口径和数据规模；所有性能结论必须以本项目负载压测为准。
- Assertion 节点增添遍历跳数，会影响热点查询；需用真实查询证明是否要物化边或维护读模型。物化投影带来双写/一致性与删除重建风险。
- 证据数组的最大尺寸、文本隐私/保留期、跨租户授权、数据备份恢复及来源撤回语义尚未定义。
- FalkorDB、GraphDB 的具体许可和商业报价可能随版本/部署计划改变；[unverified] 本报告不对价格或企业功能矩阵作固定断言，应在采购时以官方现行条款核验。
