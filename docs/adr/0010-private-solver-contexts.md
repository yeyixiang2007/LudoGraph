# ADR-0010：验证 worker 使用私有 solver context

- **状态：** Proposed
- **决策域：** 求解器并发与资源隔离

## 背景

Z3 context、solver 和 AST 是有状态对象；跨 worker 共享对象会产生线程安全、生命周期和诊断隔离风险。增量求解能力也不意味着所有任务都应共享一个长期 solver。

## 备选方案

1. 全局共享 solver/context，所有请求 push/pop。
2. 每个请求在同一共享 context 上创建 solver。
3. 每个 worker 私有 context/solver，任务间只传序列化 Rule IR/SMT-LIB，必要时重建 solver。

## 决策

采用方案 3。worker 不跨边界传递 AST；任务有明确超时、资源上限和 solver 生命周期。

## 理由与边界

- 降低共享状态和跨任务污染；
- 使并发模型与可序列化审计输入一致；
- 允许按理论片段隔离 worker 和报告资源；
- 私有 context 不解决模型编译错误或公式本身的复杂度；
- 性能仍须在本机对一次性、assumption 和 push/pop 方案实测。

## 推翻条件

- 受控 benchmark 证明共享 context 在同等安全隔离下显著改善性能且不改变结果；
- solver 官方/适配器提供明确的跨任务线程安全与生命周期保证；
- 任务完全串行且无需并发隔离（仍需保留可序列化输入）。

## 影响

需要 worker pool、任务序列化、超时取消、context 释放和结果 provenance；禁止把 solver 对象放入共享缓存。

## 修订记录

| 版本 | 变更 |
| --- | --- |
| v1 | 初稿。 |
