# Student Local FinGPT Workflow

本目录是在上游 FinGPT 仓库之上增加的本地复现层，目标是把金融文本情绪分析做成一个可验证、可解释、可写入简历的最小项目闭环。上游代码尽量保持不动，本地数据准备、训练、评估、错误分析和学习说明放在 `student_local/`。

## 当前复现目标

- 任务：金融文本情绪分类。
- 标签：`negative`、`neutral`、`positive`。
- 数据集：Financial PhraseBank `sentences_50agree`。
- 数据切分：固定 `seed=42`，当前本地小样本为 `train=128`、`test=32`。
- 推理模型：`NousResearch/Llama-2-7b-hf` + `oliverwang15/FinGPT_v32_Llama2_Sentiment_Instruction_LoRA_FT`。
- 训练验证：使用 QLoRA 思路完成 8 条训练样本的 sanity training，证明训练、保存、reload check 闭环可运行。

## 目录说明

| path | purpose |
| --- | --- |
| `student_local/check_env.py` | 检查 Python、Torch、CUDA、GPU 和当前 git commit。 |
| `student_local/check_fpb_data.py` | 检查 Financial PhraseBank 本地数据和固定 seed 切分是否匹配。 |
| `student_local/prepare_sentiment_subset.py` | 生成本地 `fpb_mini` 小样本训练与测试数据。 |
| `student_local/run_sentiment_inference.py` | 跑少量金融文本情绪推理。 |
| `student_local/run_sentiment_benchmark.py` | 跑 Financial PhraseBank benchmark，输出指标、混淆矩阵和错误样本。 |
| `student_local/train_sentiment_qlora.py` | 跑本地 QLoRA sanity training 并保存 LoRA adapter。 |
| `student_local/results.md` | 记录已由脚本产物验证的结果。 |
| `student_local/error_analysis.md` | 对首版 benchmark 的 20 条误判样本做人工错误类型总结。 |
| `student_local/outputs/` | 保存预测、metrics、confusion matrix、error cases、checkpoint 等实验产物。 |

## 推荐运行环境

优先使用 WSL Ubuntu，因为当前已验证 CUDA 路线可用。Windows fallback 主要用于轻量脚本、语法检查或环境排查，不适合 7B QLoRA 训练。

已验证环境：

- Python `3.12.3`
- Torch `2.10.0+cu128`
- CUDA available: `True`
- GPU: `NVIDIA GeForce RTX 5070`
- GPU memory: `11.94 GiB`
- bf16 supported: `True`

## 最小复现命令

```bash
cd /mnt/d/Learn/20_Projects/FinGPT-github
```

进入项目根目录，确保后续脚本能用相对路径找到 `student_local/`、`.runtime/`、数据和输出目录。

```bash
source ~/.bashrc
```

加载 WSL 用户环境变量，尤其是 `HF_TOKEN`。访问 gated Llama 模型时需要 Hugging Face token。

```bash
source student_local/activate_wsl_env.sh
```

激活项目本地 Python 环境，并设置 `HF_HOME=.runtime/hf-home` 等缓存路径。

```bash
python student_local/check_env.py
```

检查当前 Python、Torch、CUDA、GPU、bf16 和 git commit，作为环境可复现证据。

```bash
python student_local/check_fpb_data.py
```

检查 Financial PhraseBank 全量数据和 `fpb_mini` 是否仍然匹配固定 `seed=42` 切分。

```bash
python student_local/run_sentiment_inference.py --backend hf
```

使用 HF backend 加载 Llama-2 base model 和 FinGPT LoRA adapter，跑少量金融文本情绪推理。

```bash
python student_local/run_sentiment_benchmark.py --backend hf --max-samples 32 --batch-size 2 --output-csv student_local/outputs/fpb_benchmark_hf_32_20260522.csv --metrics-json student_local/outputs/fpb_benchmark_hf_32_20260522_metrics.json --confusion-matrix-csv student_local/outputs/fpb_benchmark_hf_32_20260522_confusion_matrix.csv --errors-csv student_local/outputs/fpb_benchmark_hf_32_20260522_errors.csv
```

在固定测试切分前 32 条样本上生成预测，计算 `accuracy`、`macro F1`、`weighted F1`，并保存预测明细、混淆矩阵和错误样本。

```bash
python student_local/train_sentiment_qlora.py --output-dir student_local/outputs/fpb_qlora_sanity_20260521_am --max-train-samples 8 --max-eval-samples 4 --num-train-epochs 1 --gradient-accumulation-steps 1 --logging-steps 1 --train-batch-size 1 --eval-batch-size 1 --max-length 192
```

用极小样本跑 QLoRA sanity training，验证数据加载、tokenize、Trainer 训练、checkpoint/adapter 保存和 reload check 都能执行。

## 已验证结果

首版 HF FinGPT LoRA benchmark 已完成，产物见 `student_local/results.md`：

| backend | samples | accuracy | macro F1 | weighted F1 | unparsed predictions | error cases |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| hf | 32 | 0.2500 | 0.2222 | 0.3125 | 11 | 24 |

这个结果只能说明评估闭环已经建立，并暴露出 prompt 和输出解析不稳定的问题，不能包装成高性能模型结果。

## 已知限制

- 当前 benchmark 只跑了固定测试切分前 32 条样本，样本规模很小。
- `unparsed_predictions=11`，说明模型输出经常不是干净的标准标签。
- QLoRA sanity training 只用了 8 条训练样本和 4 条评估样本，只能证明训练链路可运行，不能代表正式训练效果。
- 本机成功加载模型依赖已有 Hugging Face cache；换机器、清空 cache 或重新下载前，需要重新确认 `HF_TOKEN` 和模型访问权限。
- 当前尚未系统比较不同 prompt、不同解析策略、不同 adapter 或本地训练 adapter 的效果。

## 可写入简历的谨慎口径

可以写：

- 在 WSL + RTX 5070 环境中复现 FinGPT 金融文本情绪分析的最小训练与评估闭环。
- 基于 Financial PhraseBank 构建固定随机种子的数据切分。
- 使用 QLoRA 思路完成小样本 sanity training，保存 LoRA adapter 和 checkpoint。
- 实现 benchmark 输出 `accuracy`、`macro F1`、`weighted F1`、confusion matrix 和 error cases。
- 基于首版 benchmark 发现 `unparsed` 输出较多，进一步整理错误类型和改进方向。

不能写：

- 完成了完整大规模 FinGPT 训练。
- 取得了高准确率或优秀 F1 指标。
- 已经完成多模型、多 prompt 或多 adapter 的系统性对比实验。
- 已经复现 FinGPT Forecaster、Robo-advisor、Trading 等其他模块。
