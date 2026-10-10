# ADR-0008：显式组合抽取 certainty 与验证结果协议

- **状态：** Proposed
- **决策域：** 不确定性语义

## 背景

抽取的 `certainty` 描述原文语气（`explicit`、`possible`、`planned`、`negated`），验证结果描述形式化任务状态（`proved`、`counterexample`、`bounded-no-counterexample`、`unknown`、`not-modeled`）。两者不能被一个“置信度”字段替代。

## 备选方案

1. 所有 claim 都按事实处理，求解器统一返回 pass/fail。
2. 把 certainty 当作数值概率，直接加权或吸收进求解器。
3. 保持两套正交枚举，并用显式编译矩阵/分支表示哪些 certainty 可以进入何种模型。

## 决策

采用方案 3。`possible`/`planned`/`negated` 不因可解析就自动成为确认运行时事实；缺语义时返回 `not-modeled`，冲突来源分支验证或分别报告。`unknown` 不得当通过。

## 理由与边界

- 防止原文语气被误译为模型概率；
- 让“存在形式反例”和“来源不确定”同时可见；
- 支持保守过近似/欠近似与人工澄清；
- 组合矩阵的完整形式仍需基于具体业务规则定稿；
- `explicit` 也不自动证明自然语言蕴含或模型编码正确。

## 推翻条件

- 形成经过验证的统一概率/模态语义，并能证明不丢失来源语气与验证边界；
- 业务明确所有输入均为已审核执行规则，不再存在计划/可能/否定语气；
- 外部形式语言提供等价的来源与结果多值语义。

## 影响

接口、Rule IR、报告和评测必须分开统计 certainty 与 result status；文档不能使用单一“confidence”替代。

## 修订记录

| 版本 | 变更 |
| --- | --- |
| v1 | 初稿。 |
