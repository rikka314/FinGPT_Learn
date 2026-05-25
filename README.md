# FinGPT Learn

这是一个面向学习与简历展示的 FinGPT 金融文本情绪分析复现项目。原始上游项目来自 [AI4Finance-Foundation/FinGPT](https://github.com/AI4Finance-Foundation/FinGPT)，本仓库重点保留个人复现层、实验脚本、结果记录和错误分析，便于查阅者快速检查我实际完成的工作。

## Project Focus

- 任务：金融文本情绪分类。
- 数据集：Financial PhraseBank `sentences_50agree`。
- 标签：`negative`、`neutral`、`positive`。
- 本地复现层：`student_local/`。
- 主要目标：跑通最小训练与评估闭环，而不是维护完整上游 FinGPT。

## What Is Included

| path | purpose |
| --- | --- |
| `student_local/README.md` | 本地复现入口，包含环境、数据、运行命令和已知限制。 |
| `student_local/run_sentiment_inference.py` | HF/LoRA 金融情绪推理入口。 |
| `student_local/run_sentiment_benchmark.py` | benchmark 脚本，输出 metrics、confusion matrix 和 error cases。 |
| `student_local/train_sentiment_qlora.py` | QLoRA sanity training 脚本。 |
| `student_local/results.md` | 已验证结果汇总。 |
| `student_local/error_analysis.md` | 首版错误样本分析。 |
| `WORKLOG.md` | 复现过程、命令、产物和限制记录。 |
| `AI_CONTEXT.md` | 项目长期上下文和协作规则。 |

## Verified Results

首版 HF FinGPT LoRA benchmark 基于 Financial PhraseBank 固定 `seed=42` 测试切分前 32 条样本：

| backend | samples | accuracy | macro F1 | weighted F1 | unparsed predictions | error cases |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| hf | 32 | 0.2500 | 0.2222 | 0.3125 | 11 | 24 |

结果文件：

- `student_local/results.md`
- `student_local/outputs/fpb_benchmark_hf_32_20260522_metrics.json`
- `student_local/outputs/fpb_benchmark_hf_32_20260522_confusion_matrix.csv`
- `student_local/outputs/fpb_benchmark_hf_32_20260522_errors.csv`
- `student_local/error_analysis.md`

## Important Boundaries

- 当前结果是小样本复现证据，不是高性能模型结果。
- QLoRA 训练是 8 条训练样本的 sanity check，只证明训练链路可运行。
- 大模型权重、数据缓存、checkpoint 和本地运行环境没有上传到仓库。
- 上游 FinGPT 的完整代码请参考原始仓库；本仓库用于展示我个人完成的复现闭环和实验记录。

## Quick Start

```bash
cd student_local
```

进入个人复现层目录。

```bash
cat README.md
```

阅读详细环境、数据准备、推理、benchmark 和训练命令。
