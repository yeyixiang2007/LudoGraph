# ADR-0006：以带来源映射的规则 IR 作为抽取与验证之间的边界

- **状态：** Proposed
- **决策域：** 抽取到验证的语义编译

## 背景

图谱 claim 适合检索，但不能直接等同于状态转移、量词、时间或机器数值语义。若验证模块直接把数据库字段拼成 SMT，限定词、假设和来源映射容易丢失。

## 备选方案

1. 验证器直接查询图并即时拼接 solver 公式。
2. 让 LLM 直接生成 SMT-LIB。
3. 采用版本化、类型化 Rule IR，携带 assumptions、approximation 和 source map，再由确定性后端编译。

## 决策

采用方案 3。Rule IR 明确实体、资源、动作、状态、转移、guard、effect、数量、时间、随机过程和假设；每个 IR 节点/表达式回指 Assertion 与原文 evidence。

## 理由与边界

- 把 claim 语义与求解器 API 解耦；
- 允许 over/under/unresolved 三分编译；
- 可测试“缺字段拒绝”与 assertion 级回映射；
- 不能凭 IR 合法证明原文抽取正确；
- 完整游戏语义仍可能超出当前 IR。

## 推翻条件

- 证明直接图到形式模型能保持全部限定语义、版本和 provenance，且复杂度更低；
- Rule IR 长期不再需要状态/时间/随机表达，简单 schema 足够；
- 采用已验证的外部形式语言作为唯一规范模型。

## 影响

需要维护 `ir_version`、编译器、source map 和 IR fixture；任何新增量词/时间/概率语义须递增 IR 版本。

## 修订记录

| 版本 | 变更 |
| --- | --- |
| v1 | 初稿。 |
