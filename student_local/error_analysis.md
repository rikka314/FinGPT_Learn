# FinGPT Sentiment Error Analysis

本文基于 `student_local/outputs/fpb_benchmark_hf_32_20260522_errors.csv` 的前 20 条误判样本进行人工错误类型整理。原始 benchmark 共有 32 条样本，其中 24 条为 error cases。

## 数据来源

- benchmark 明细：`student_local/outputs/fpb_benchmark_hf_32_20260522.csv`
- metrics：`student_local/outputs/fpb_benchmark_hf_32_20260522_metrics.json`
- confusion matrix：`student_local/outputs/fpb_benchmark_hf_32_20260522_confusion_matrix.csv`
- 原始错误样本：`student_local/outputs/fpb_benchmark_hf_32_20260522_errors.csv`
- 本次人工标注：`student_local/error_cases_20_labeled.csv`

## 20 条误判样本类型统计

| error type | count | explanation |
| --- | ---: | --- |
| `unparsed_short_output` | 6 | 模型只输出 `p`、`a` 等单字符，不能安全映射为标准标签。 |
| `unparsed_noisy_output` | 4 | 模型输出乱码、反斜杠或其他无法解析的符号。 |
| `neutral_positive_confusion` | 4 | 中性事实描述被预测为正面。 |
| `neutral_negative_confusion` | 3 | 中性事实描述被预测为负面。 |
| `negative_neutral_confusion` | 1 | 负面财务变化被预测为中性。 |
| `positive_neutral_confusion` | 1 | 正面业务进展被预测为中性。 |
| `unparsed_non_label_word` | 1 | 模型输出 `none`，不属于允许标签。 |

说明：一条样本只标一个主错误类型，便于快速定位首要问题。当前首要问题不是某个情绪方向特别弱，而是输出格式不稳定导致 `unparsed` 较多。

## 主要发现

1. 输出格式问题很突出。

首版 benchmark 的 `unparsed_predictions=11`，占 32 条样本的 34.4%。在人工查看的 20 条误判里，`unparsed_short_output`、`unparsed_noisy_output` 和 `unparsed_non_label_word` 合计 11 条。这说明 prompt 或生成配置没有强约束模型只输出 `negative`、`neutral`、`positive` 三个词。

2. 中性样本容易被情绪化解读。

`neutral_positive_confusion` 和 `neutral_negative_confusion` 合计 7 条。Financial PhraseBank 中很多中性句子是客观事实、交易描述、公司背景或数值陈述。模型看到 `margin`、`decrease`、`orders`、`+` 等词时，容易按词面情绪而不是数据集标注规则判断。

3. 财务变化方向仍会漏判。

例如现金及等价物从 `EUR10.5m` 降到 `EUR6.5m` 的样本被预测为 `neutral`。这类错误说明模型没有稳定抓住数值变化方向。

4. 显式正面信号也可能因为解析失败丢分。

含有 `positive impact`、`bullish`、`buy ranking` 的样本本应容易判断，但 raw output 是 `\` 等非法输出，最终被计为 `unparsed`。这类样本不是语义完全不会，而是输出协议失败。

## 改进方向

优先级从高到低：

1. 收紧 prompt，明确要求只输出一个小写标签：`negative`、`neutral` 或 `positive`。
2. 降低生成自由度，例如使用更短的 `max_new_tokens`，并确认 `do_sample=False`。
3. 改进 `extract_label`，但只增加高置信映射，避免把所有单字母都强行解释为情绪标签。
4. 增加一个专门的 neutral 判断提示，让模型区分事实描述和真实利好/利空。
5. 在修复输出格式后再比较不同 prompt 或 adapter，否则指标会被 `unparsed` 问题主导。

## 复现边界

当前错误分析只基于首版 32 条小样本 benchmark 和其中前 20 条误判的人工归类。它可以用于说明已经建立了评估与错误分析闭环，但不能声称完成了大规模系统性错误分析。

## 术语解释

- `unparsed`：模型有输出，但脚本无法从 raw output 中解析出 `negative`、`neutral`、`positive` 三个合法标签。
- `confusion matrix`：按真实标签和预测标签交叉统计错误方向的表格，用于看模型把哪类样本错分成哪类。
- `macro F1`：先分别计算每个类别的 F1，再做平均；小类别表现差时会明显拉低它。
- `weighted F1`：按各类别样本数加权平均 F1；在类别不均衡时更接近整体样本表现。
- `error cases`：预测错误或无法解析的样本，通常用于人工检查模型失败原因。
