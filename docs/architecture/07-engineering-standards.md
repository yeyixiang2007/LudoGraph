# 工程规范配套

- **状态：** v1 设计草案。
- **目的：** 为文档中的合同、抽取、查询、验证和版本能力提供可审计的工程门禁。本文不替代团队的组织级安全、法务或发布制度。

## 1. 分支与变更策略

### 1.1 分支

- `main`：仅接收评审通过并通过全部门禁的合并。
- `feat/<slug>`：新功能或文档设计变更。
- `fix/<slug>`：缺陷修复。
- `docs/<slug>`：仅文档或 schema 说明变更。
- `chore/<slug>`：依赖、CI 或维护变更。

一个分支只服务一个工作项；禁止把无关格式化、重命名或临时调试混入。

### 1.2 提交

提交主题使用：

```text
<type>(<scope>): <imperative summary>
```

推荐 `type`：`feat`、`fix`、`docs`、`test`、`refactor`、`chore`。主题不超过 72 个字符；正文说明动机、合同/迁移影响和验证命令。不得提交密钥、凭据、`.env` 或私有原文。

## 2. Code Review / Merge Gate

每个变更至少需要一名非作者审阅者；涉及 schema、结果协议、错误码或验证语义时，需要额外的领域审阅。

审阅者必须逐项确认：

1. 需求编号和变更范围明确；
2. 抽取格式、本体、证据三个层次没有混淆；
3. `uncovered`/`not-modeled`/`unknown` 没有被静默转为确认或通过；
4. domain/range、版本、ID、冲突保留规则同步；
5. solver assertion、查询结果都有 provenance；
6. 新的 schema/接口/错误码有迁移和兼容说明；
7. 测试、文档、schema 生成物已同步；
8. 无秘密、调试输出和无关重排。

合并门禁：schema 校验、格式/lint、类型检查、单元测试、集成测试、文档链接检查、安全扫描全部通过；确实不适用的门禁必须在 PR 中解释，而不能省略。

## 3. 测试分层

### 3.1 单元测试

离线、快速、确定性，覆盖：

- JSON 合同、17 标签、24 谓词、domain/range；
- quote 与 chunk span 连续性；
- raw/value/unit/probability/direction 校验；
- 确定性 Assertion ID；
- Intent/Query IR 编译和参数绑定；
- D1/D2/D3 编码小函数、结果状态映射；
- 版本 diff 与兼容性分类。

### 3.2 集成测试

使用容器或可替换测试适配器覆盖：

- 抽取合同 → Assertion 导入 → provenance 查询；
- Assertion 形态与直接边物化形态结果等价；
- 图后端能力探测和查询编译；
- Rule IR → solver adapter → 结果回映射；
- 版本快照、supersedes 和重跑影响。

### 3.3 系统测试

以公开、可归因 fixture 模拟端到端流程：文档登记、切分、抽取、审核、导入、查询、三类验证、报告和版本 diff。系统测试必须分别覆盖：

- 有环但无死锁；
- LP 有解但不存在合法执行序列；
- one-hot 合法但目标不可达；
- 概率均值安全但尾部/周期语义缺失；
- 例外优先级冲突；
- 旧版本反例受版本变化影响。

### 3.4 性能测试

报告输入规模、硬件、冷/热状态、并发数、模型版本、图后端、理论片段和数据分布。至少报告 P50/P95/P99、吞吐、CPU、内存、超时与失败率。禁止只报一个“毫秒级”数字。

快路径目标（待实测）：模板/缓存 P50 ≤10ms、P95 ≤30ms；意图路由 P50 ≤50ms、P95 ≤150ms；动态 NL2Cypher P50 ≤300ms、P95 ≤1s。SMT 不设跨问题统一延迟目标。

### 3.5 安全测试

- 输入注入：用户问题不能突破 schema 白名单或参数绑定；
- 访问控制：scope 不作为授权，验证跨 scope 越权；
- 数据泄漏：错误、日志、缓存不输出凭据或未经授权原文；
- 依赖与许可证扫描；
- 资源耗尽：chunk 大小、模型重试、图查询、SMT 深度/超时限制；
- 审计：查询/导入/验证均记录 trace、版本和主体。

## 4. CI 门禁

建议流水线顺序：

```text
pre-commit secret scan
  → schema generation/check-diff
  → markdown/link/style checks
  → lint + type check
  → unit tests
  → integration tests (service containers)
  → system fixtures
  → security/dependency scan
  → performance smoke (非阻断基线，回归阈值阻断)
```

当 schema 源文件改变时，必须强制运行合同生成、迁移检查、完整集成测试和文档数据字典检查。任何生成物漂移都失败。

## 5. 文档—代码同步

- canonical schema 只保留一个机器可读源；文档中的标签、谓词和错误码由生成或校验脚本检查。
- 每个接口字段、结果状态和 ADR 决定必须有文档链接或反向索引。
- 每次改变 `ontology_version`、`ir_version`、`schema_version` 都要更新兼容矩阵、fixture 与修订记录。
- 研究文档中的待实测目标不能在 README/API 中被改写成承诺。
- 关系计数、标签数量和枚举数量必须在 CI 中自动计算，防止 24/25 类漂移再次发生。

## 6. 安全与运行维护

### 6.1 秘密与数据

秘密只由部署平台的秘密管理系统注入，仓库只提交占位配置。策划原文按敏感数据处理；日志默认记录 source/chunk 引用而非完整正文；导出和备份须有授权、保留期和删除流程。

### 6.2 可观测性

每个请求/任务记录：trace ID、主体、scope、版本四元组、输入规模、耗时分段、依赖版本、结果状态、错误码。日志不得把 `unknown`、超时、拒绝或 `not-modeled` 计为成功。

关键指标：抽取硬错误率、证据连续性率、uncovered 率、domain/range 违规率、查询拒绝率、provenance 完整率、验证结果分布、solver timeout、快路径命中率、断言导入幂等冲突。

### 6.3 备份与恢复

Assertion 历史和版本快照是规范数据，须可备份、校验和恢复。物化边可删除重建；恢复演练必须验证 assertion ID、supersedes、provenance 和版本 diff 不变。

## 7. 发布与回滚

- 发布前冻结 schema/ontology/IR 版本及 fixture；
- 先 dry-run 导入，比较新增、supersede、冲突和受影响结论；
- 物化投影支持重建，规范 Assertion 先写后切换读视图；
- 发现语义回归时回滚读视图或服务版本，不删除历史断言；
- solver/模型升级须保留旧适配器用于结果差异比较；
- 发布报告须明确哪些结果是 `proved`、哪些仅是有界无反例、哪些为 `unknown`。

## 8. 违规处理

架构违规（绕过 validator、直接端到端生成执行查询、覆盖冲突断言、把 unknown 当通过、跨 context 传 solver AST）必须阻断合并。临时例外需记录范围、风险、期限、替代门禁和责任人，过期自动关闭。

## 修订记录

| 版本 | 变更 |
| --- | --- |
| v1 (draft) | 初稿：分支、提交、评审门禁、测试分层、CI、文档同步、安全与运维。 |
