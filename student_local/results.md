# FinGPT Sentiment Results

本文只记录已经由脚本输出、日志或生成文件验证的结果。没有证据的计划不要写成已完成结论。

## Result Index

| item | status | path |
| --- | --- | --- |
| HF FinGPT LoRA benchmark | verified | `student_local/outputs/fpb_benchmark_hf_32_20260522_metrics.json` |
| benchmark predictions | verified | `student_local/outputs/fpb_benchmark_hf_32_20260522.csv` |
| confusion matrix CSV | verified | `student_local/outputs/fpb_benchmark_hf_32_20260522_confusion_matrix.csv` |
| confusion matrix SVG | generated from verified CSV | `student_local/outputs/fpb_benchmark_hf_32_20260522_confusion_matrix.svg` |
| raw error cases | verified | `student_local/outputs/fpb_benchmark_hf_32_20260522_errors.csv` |
| 20-case manual error labels | manually summarized | `student_local/error_cases_20_labeled.csv` |
| error analysis notes | manually summarized | `student_local/error_analysis.md` |
| QLoRA sanity training | verified as runnable training loop | `student_local/outputs/fpb_qlora_sanity_20260521_am` |

## 2026-05-22 HF FinGPT LoRA Benchmark

运行命令：

```bash
python student_local/run_sentiment_benchmark.py --backend hf --max-samples 32 --batch-size 2 --output-csv student_local/outputs/fpb_benchmark_hf_32_20260522.csv --metrics-json student_local/outputs/fpb_benchmark_hf_32_20260522_metrics.json --confusion-matrix-csv student_local/outputs/fpb_benchmark_hf_32_20260522_confusion_matrix.csv --errors-csv student_local/outputs/fpb_benchmark_hf_32_20260522_errors.csv
```

该命令使用 HF backend 加载 `NousResearch/Llama-2-7b-hf` 与 `oliverwang15/FinGPT_v32_Llama2_Sentiment_Instruction_LoRA_FT`，在 Financial PhraseBank `sentences_50agree` 固定 seed 测试切分的前 32 条样本上生成预测并计算指标。

| backend | samples | accuracy | macro F1 | weighted F1 | unparsed predictions | error cases |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| hf | 32 | 0.2500 | 0.2222 | 0.3125 | 11 | 24 |

## Confusion Matrix

CSV 产物：

```text
student_local/outputs/fpb_benchmark_hf_32_20260522_confusion_matrix.csv
```

SVG 图表：

```text
student_local/outputs/fpb_benchmark_hf_32_20260522_confusion_matrix.svg
```

| actual \ predicted | negative | neutral | positive | unparsed |
| --- | ---: | ---: | ---: | ---: |
| negative | 0 | 3 | 0 | 1 |
| neutral | 4 | 6 | 4 | 5 |
| positive | 0 | 2 | 2 | 5 |
| unparsed | 0 | 0 | 0 | 0 |

解读：

- `neutral` 样本最多，也最容易被分到 `negative`、`positive` 或 `unparsed`。
- `positive` 样本有 5 条进入 `unparsed`，说明即使语义信号明显，输出格式失败也会直接拉低指标。
- `negative` 样本没有被正确预测为 `negative`，但当前 negative 样本只有 4 条，不能仅凭这 32 条样本断言模型完全不会识别负面。

## Error Analysis

本次 D3 从原始 error cases 中抽取前 20 条做人工错误类型标注：

```text
student_local/error_cases_20_labeled.csv
```

错误分析说明：

```text
student_local/error_analysis.md
```

20 条样本主错误类型统计：

| error type | count | meaning |
| --- | ---: | --- |
| `unparsed_short_output` | 6 | 模型只输出单字符，例如 `p` 或 `a`。 |
| `unparsed_noisy_output` | 4 | 模型输出乱码或非法符号。 |
| `neutral_positive_confusion` | 4 | 中性事实描述被预测为正面。 |
| `neutral_negative_confusion` | 3 | 中性事实描述被预测为负面。 |
| `negative_neutral_confusion` | 1 | 负面财务变化被预测为中性。 |
| `positive_neutral_confusion` | 1 | 正面业务进展被预测为中性。 |
| `unparsed_non_label_word` | 1 | 模型输出 `none` 等非标签词。 |

主要结论：

- 首要问题是输出协议不稳定。32 条 benchmark 中有 11 条 `unparsed`。
- 中性样本容易被模型按词面情绪误判，例如看到 `margin`、`decrease`、`orders` 后给出正面或负面。
- 下一步应先修 prompt 和解析策略，再谈模型效果对比。

## 2026-05-21 QLoRA Sanity Training

运行命令：

```bash
python student_local/train_sentiment_qlora.py --output-dir student_local/outputs/fpb_qlora_sanity_20260521_am --max-train-samples 8 --max-eval-samples 4 --num-train-epochs 1 --gradient-accumulation-steps 1 --logging-steps 1 --train-batch-size 1 --eval-batch-size 1 --max-length 192
```

该命令用极小样本跑通 QLoRA 训练闭环，验证数据加载、tokenize、Trainer 训练、checkpoint/adapter 保存和 reload check。

已验证结果：

- 训练样本：8
- 评估样本：4
- training steps：8
- `train_loss=2.416`
- `eval_loss=1.122`
- `train_runtime=14.01s`
- 输出目录：`student_local/outputs/fpb_qlora_sanity_20260521_am`
- 保存内容包括：`adapter_model.safetensors`、`adapter_config.json`、`tokenizer.json`、`checkpoint-8/`

注意：这是 sanity training，只能证明训练链路可执行，不能作为正式模型效果指标。

## Known Limitations

- benchmark 样本数只有 32 条，结论只能作为首版复现证据。
- 首版指标偏低，不能写成高性能结果。
- `unparsed_predictions=11` 表明 prompt 和输出解析仍需改进。
- QLoRA 训练只用了 8 条训练样本，不能说完成了完整大模型训练。
- 尚未评估本地 sanity adapter 在测试集上的效果。
- 尚未比较不同 prompt、不同生成配置、不同 parser 或不同 adapter。

## Interview-Safe Summary

可以这样讲：

> 我在本地 WSL + RTX 5070 环境中复现了 FinGPT 金融文本情绪分析的最小闭环，基于 Financial PhraseBank 固定随机种子构建数据切分，跑通了 HF LoRA 推理、QLoRA 小样本 sanity training，以及包含 accuracy、macro F1、weighted F1、confusion matrix 和 error cases 的 benchmark。首版 32 条样本 benchmark 的 accuracy 为 0.25，主要问题是模型输出格式不稳定，出现 11 条 unparsed prediction，因此后续改进重点是 prompt 约束和标签解析。

不能这样讲：

> 我完成了完整 FinGPT 大模型训练，并取得了优秀分类效果。
