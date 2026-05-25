# FinGPT Worklog

本文件记录本项目后续复现、训练、评估、README 和简历素材沉淀过程。AI 每次完成实质操作后都应追加或更新本文件。

## 2026-05-19

### 本次目标

- 把用户的项目背景和三天任务计划固化成项目默认提示词。
- 让新对话进入本仓库时自动读取默认上下文，不需要手动调用 skill。
- 建立后续操作记录文件。

### 已完成

- 新增 `AGENTS.md`：作为仓库级默认提示词入口，规定启动顺序、工作边界、记录规则和三天执行目标。
- 新增 `AI_CONTEXT.md`：记录项目目标、当前状态、目录约定、运行偏好、D1-D3 计划和简历口径。
- 新增 `WORKLOG.md`：作为后续实验、报错、命令、产物和下一步的记录文件。

### 已观察到的现有状态

- 根目录已有上游 FinGPT 文件和 `fingpt/` 代码。
- 根目录已有 `student_local/`，包含本地情绪分析复现相关脚本和说明。
- `student_local/README.md` 已记录 WSL、Windows fallback、Ollama fallback、情绪推理、benchmark、数据准备和 QLoRA sanity training 命令。
- 当前 git 状态中已有用户侧改动：`.gitignore` 已修改，`student_local/` 为未跟踪目录。本次没有回退这些内容。

### 下一步建议

- D1：盘点并锁定环境，确认 WSL 下 `student_local/check_env.py` 输出。
- D1：确认 Financial PhraseBank 数据切分脚本是否复用 `student_local/prepare_sentiment_subset.py`，还是新增独立 `split_dataset.py`。
- D2：在现有脚本基础上补齐训练与评估闭环，确保指标来自脚本输出。
- D3：整理 README、`results.md`、`error_cases.csv` 和已知限制。

### 不能写进简历的内容

- 尚未由本次对话验证的训练指标。
- 尚未实际生成的错误分析文件、结果图表或完整 README。
- 尚未实现的 `QuantPlatform`、`PDFDemo`、`Career` 模块。

## 2026-05-20

### 本次目标

- 回答用户对 HF backend、LoRA、QLoRA、4-bit NF4、benchmark、adapter、Financial PhraseBank 和评估指标的概念问题。
- 固化新的协作要求：以后给出代码或命令时，下一行必须解释其具体作用。

### 已完成

- 更新 `AGENTS.md`：加入代码/命令逐行解释要求。
- 更新 `AI_CONTEXT.md`：把该解释要求记录为项目长期协作偏好。

### 下一步建议

- 继续按 D1/D2 主线确认 HF backend 是否能实际加载 base model 和 FinGPT LoRA adapter。
- 成功后再跑 `run_sentiment_benchmark.py --backend hf`，记录真实 accuracy、macro F1、weighted F1。

## 2026-05-21

### 本次目标

- 固化新的协作要求：后续操作必须详细说明做了什么、为什么这么做、有什么用，并补充有助于理解项目复现的背景。
- 验证 HF backend 是否真正可用：不仅确认 GPU，还要确认 Hugging Face token、base model 和 FinGPT LoRA adapter 的访问与加载能力。

### 已完成

- 更新 `AGENTS.md`：加入后续操作说明深度要求。
- 更新 `AI_CONTEXT.md`：把该说明要求记录为项目长期协作偏好。
- 新增 `student_local/check_hf_backend.py`：检查 Hugging Face token、base model、FinGPT LoRA adapter 访问与加载状态，并可做一条样例推理。
- 新增 `student_local/check_hf_backend_wsl.sh`：WSL 包装脚本，负责激活本地 venv 后运行 HF backend 检查。
- 新增 `student_local/check_hf_backend_offline_wsl.sh`：离线包装脚本，使用本地 HF cache 验证 base model + LoRA adapter 是否能加载。
- 新增 `student_local/diagnose_hf_imports.py` 和 `student_local/diagnose_hf_imports_wsl.sh`：诊断 HF backend 相关依赖导入耗时与失败点。

### 验证记录

- 命令：`bash student_local/check_hf_backend_wsl.sh --skip-load`
  - 作用：只检查 Hugging Face 仓库访问权限，不加载 7B 模型权重。
  - 结果：WSL 中 `HF_TOKEN` 未配置；FinGPT LoRA adapter 仓库可访问；`NousResearch/Llama-2-7b-hf` 在线访问失败，报 `SSL: UNEXPECTED_EOF_WHILE_READING`。
- 命令：`bash student_local/diagnose_hf_imports_wsl.sh`
  - 作用：确认 `torch`、`transformers`、`peft`、`bitsandbytes` 等 HF backend 依赖能否导入，并定位冷启动耗时。
  - 结果：核心依赖可导入，但冷启动较慢；观测到 `torch` 约 12s、`transformers` 约 40s、`peft` 约 31s、`bitsandbytes` 约 14s。
- 命令：`bash student_local/check_hf_backend_offline_wsl.sh`
  - 作用：跳过在线访问，使用 `.runtime/hf-home` 本地 cache 实际加载 `NousResearch/Llama-2-7b-hf` + FinGPT LoRA adapter。
  - 结果：模型以 4-bit quantization 成功加载，完成样例推理；`sample prediction: neutral`，`sample raw output: neutral`。
- 用户命令：`python student_local/check_hf_backend.py --skip-load`
  - 作用：在已配置 `HF_TOKEN` 后重新检查 Hugging Face 在线仓库访问权限，但不加载 7B 模型权重。
  - 结果：`hf token configured: True`；`NousResearch/Llama-2-7b-hf` 在线访问成功，sha 为 `8efe6c9b93655b934e27bd9981e3ec13e55aee9d`；FinGPT LoRA adapter 在线访问成功，sha 为 `f9449d2d7ab16e0b08f5e524af8f3a5451555d55`。
- 命令：`python student_local/run_sentiment_inference.py --backend hf`
  - 作用：使用正式推理入口加载 `NousResearch/Llama-2-7b-hf` + FinGPT sentiment LoRA adapter，以 HF backend 跑最小金融文本情绪推理，证明当前不是 Ollama fallback。
  - 结果：模型权重加载完成；三条默认样例输出合法标签：`positive`、`neutral`、`positive`。其中 raw output 包括 `+` 和 `2`，由 `student_local/common.py` 中的 label alias / digit map 解析为 `positive`。
- 命令：`python student_local/check_env.py`
  - 作用：正式记录当前 WSL 本地复现环境，作为后续 README、实验日志和简历表述的证据。
  - 结果：Python `3.12.3`；platform `Linux-6.6.87.2-microsoft-standard-WSL2-x86_64-with-glibc2.39`；git commit `4e53f8d`；Torch `2.10.0+cu128`；CUDA available `True`；GPU `NVIDIA GeForce RTX 5070`；bf16 supported `True`；total memory `11.94 GiB`。
- 命令：`python student_local/check_fpb_data.py`
  - 作用：检查本地 Financial PhraseBank 数据缓存和训练子集是否符合 D1 数据准备要求，尤其确认 `fpb_mini` 是否来自固定随机种子 `seed=42`。
  - 结果：`student_local/data/fpb_full` 含 4846 条，字段为 `sentence/label`；`student_local/data/fpb_mini` 含 `train=128`、`test=32`，字段为 `input/output/instruction`；`mini_train_matches_seed_split=True`；`mini_test_matches_seed_split=True`；全量标签分布为 `neutral=2879`、`negative=604`、`positive=1363`。
- 决策：暂不新增 `split_dataset.py`
  - 依据：现有 `student_local/prepare_sentiment_subset.py` 已使用 `train_test_split(test_size=0.2, seed=42)` 完成固定切分，并生成 QLoRA sanity training 所需的 `instruction/input/output` 格式；`check_fpb_data.py` 已验证 `fpb_mini` 与该切分逐行匹配。
  - 作用：避免新增与现有脚本重复的维护入口，当前 D1 目标以复用 `prepare_sentiment_subset.py` 为准；如果后续需要正式 `train/validation/test` 三切分，再单独新增或扩展数据切分脚本。

### D2 命令模板

- 命令：`cd /mnt/d/Learn/20_Projects/FinGPT-github`
  - 作用：进入 FinGPT 项目根目录，确保后续脚本能使用正确的相对路径读取 `student_local/`、`.runtime/`、数据和输出目录。
- 命令：`source ~/.bashrc`
  - 作用：加载 WSL 用户环境变量，尤其是 `HF_TOKEN`，避免 Hugging Face 请求以未认证状态访问模型仓库。
- 命令：`source student_local/activate_wsl_env.sh`
  - 作用：激活项目本地 Python venv，并设置 `HF_HOME=.runtime/hf-home`、`PIP_CACHE_DIR` 等项目内运行路径，保证模型和数据缓存落在本仓库约定位置。
- 命令：`python student_local/run_sentiment_inference.py --backend hf`
  - 作用：用正式 HF backend 跑最小情绪推理，确认 `base model + FinGPT LoRA adapter` 能正常输出 `negative/neutral/positive` 标签。
- 命令：`python student_local/run_sentiment_benchmark.py --backend hf --max-samples 32`
  - 作用：用 HF/LoRA 路线在 Financial PhraseBank 小样本测试集上计算 `accuracy`、`f1_macro`、`f1_weighted`，生成可记录的首版评估指标。
- 命令：`python student_local/prepare_sentiment_subset.py`
  - 作用：按 `seed=42` 重新生成 `student_local/data/fpb_mini`，产出 QLoRA sanity training 所需的 `instruction/input/output` 格式训练数据。
- 命令：`python student_local/check_fpb_data.py`
  - 作用：在训练前确认 `fpb_mini` 仍然是固定 seed 切分结果，避免训练数据被意外覆盖或切分漂移。
- 命令：`python student_local/train_sentiment_qlora.py`
  - 作用：用 `fpb_mini` 跑本地 QLoRA sanity training，只训练 LoRA adapter，验证本机可以完成最小训练闭环。

### DAY1 总结

- 已完成：WSL + 本地 GPU 环境已记录，Python `3.12.3`、Torch `2.10.0+cu128`、CUDA 可用、GPU 为 `NVIDIA GeForce RTX 5070`、显存 `11.94 GiB`、bf16 支持、git commit 为 `4e53f8d`。
- 已完成：`HF_TOKEN` 在线访问检查已通过，`NousResearch/Llama-2-7b-hf` 和 FinGPT sentiment LoRA adapter 仓库均可访问。
- 已完成：HF backend 离线加载已通过，`base model + FinGPT LoRA adapter + 4-bit quantization` 可以在本机加载并完成样例推理。
- 已完成：正式推理入口 `run_sentiment_inference.py --backend hf` 已跑通，默认三条样例输出合法情绪标签。
- 已完成：Financial PhraseBank 本地数据状态已确认，`fpb_full=4846` 条，`fpb_mini=train 128/test 32`，且 `fpb_mini` 与 `seed=42` 固定切分逐行匹配。
- 已完成：决定暂不新增 `split_dataset.py`，D1/D2 先复用 `prepare_sentiment_subset.py` 作为数据准备入口。
- 已完成：D2 命令模板已整理，明天可从 HF benchmark 开始进入训练评估闭环。

### DAY1 未验证

- 未验证：HF benchmark 指标尚未生成，当前没有可信的 `accuracy`、`f1_macro`、`f1_weighted` 结果。
- 未验证：本地 QLoRA sanity training 尚未实际完成，`student_local/outputs/fpb_qlora_adapter` 不能作为已训练产物写入成果。
- 未验证：训练后 adapter 的评估、对比和错误样本分析尚未完成。
- 未验证：`confusion matrix`、`results.md`、`error_cases.csv` 尚未生成。

### 当前不能写进简历

- 不能写：已经完成完整 FinGPT 大模型训练。
- 不能写：已经取得某个 accuracy、macro F1、weighted F1 指标。
- 不能写：已经完成错误样本分析或结果图表。
- 不能写：已经复现 FinGPT Forecaster、Robo-advisor、Trading、QuantPlatform、PDFDemo 或 Career 等模块。
- 可以谨慎写成进行中：已在 WSL + RTX 5070 上搭建 FinGPT sentiment 本地复现环境，完成 HF/LoRA 推理链路和 Financial PhraseBank 固定 seed 数据准备验证。

### 下一步建议

- 在线仓库访问权限已验证通过；完整重新下载能力未单独验证，但当前 cache 已可加载模型。
- 下一步可以跑 `run_sentiment_benchmark.py --backend hf --max-samples 32`，用 HF backend 生成真实 accuracy、macro F1、weighted F1。

### D2 上午：训练闭环 sanity check

### 本次目标

- 检查 `student_local/train_sentiment_qlora.py` 是否覆盖 D2 上午要求：数据加载、tokenize、Trainer/QLoRA 训练、checkpoint 或 adapter 保存。
- 跑通最小训练 sanity check，证明本机可以完成一次小规模训练闭环，但不把它当作正式效果指标。
- 回答用户关于 tokenize、checkpoint、sanity check 和短 epoch 的概念问题。

### 已完成

- 更新 `student_local/train_sentiment_qlora.py`：
  - 新增 `--max-train-samples` 和 `--max-eval-samples`，用于 D2 sanity check 时限制样本数，避免每次都跑完整 `fpb_mini`。
  - 新增 `--skip-reload-check`，必要时可只验证训练与保存，不做二次加载。
  - 在保存 adapter 后释放旧模型显存，再重新加载 adapter 做 reload check，降低 12GB 显存下二次加载 OOM 风险。
  - 兼容当前 `transformers` 的 `eval_strategy` 参数名，同时保留旧版 `evaluation_strategy` fallback。
- 语法检查通过：`.runtime\conda\fingpt310win\python.exe -m py_compile student_local\train_sentiment_qlora.py`。
- Windows fallback 环境检查：
  - `.runtime/conda/fingpt310win` 为 Python `3.10.20`。
  - Windows fallback 中 `torch` 为 `2.11.0+cpu`，`cuda available: False`，不能用于 7B QLoRA 训练。
- WSL CUDA 环境检查通过：
  - Python `3.12.3`。
  - Torch `2.10.0+cu128`。
  - CUDA available `True`。
  - GPU `NVIDIA GeForce RTX 5070`。
  - bf16 supported `True`。
  - total memory `11.94 GiB`。
- 数据检查通过：
  - `fpb_full=4846`。
  - `fpb_mini train=128/test=32`。
  - `mini_train_matches_seed_split=True`。
  - `mini_test_matches_seed_split=True`。
- 最小 QLoRA sanity training 已跑通：
  - 使用 8 条训练样本、4 条评估样本。
  - 训练完成 8 个 step。
  - 产物目录：`student_local/outputs/fpb_qlora_sanity_20260521_am`。
  - 保存文件包括 `adapter_model.safetensors`、`adapter_config.json`、`tokenizer.json`、`checkpoint-8/`。
  - 训练日志关键结果：`train_loss=2.416`，`eval_loss=1.122`，`train_runtime=14.01s`。
  - reload check 输出：`1. Positive\nExplanation: L&T`。

### 关键命令

- 命令：`wsl.exe bash -lc "cd /mnt/d/Learn/20_Projects/FinGPT-github && source ~/.bashrc && source student_local/activate_wsl_env.sh && python student_local/check_env.py"`
  - 作用：在 WSL CUDA 环境中确认 Python、Torch、CUDA、GPU 和显存状态，判断是否具备本地 QLoRA 训练条件。
- 命令：`.runtime\conda\fingpt310win\python.exe student_local\check_fpb_data.py`
  - 作用：确认 Financial PhraseBank 本地缓存和 `fpb_mini` 固定 seed 切分没有漂移。
- 命令：`wsl.exe bash -lc "cd /mnt/d/Learn/20_Projects/FinGPT-github && source ~/.bashrc && source student_local/activate_wsl_env.sh && python student_local/train_sentiment_qlora.py --output-dir student_local/outputs/fpb_qlora_sanity_20260521_am --max-train-samples 8 --max-eval-samples 4 --num-train-epochs 1 --gradient-accumulation-steps 1 --logging-steps 1 --train-batch-size 1 --eval-batch-size 1 --max-length 192"`
  - 作用：用极小样本跑通 QLoRA 训练闭环，验证数据加载、tokenize、训练、保存 checkpoint/adapter 和 reload check 均可执行。

### 失败点与注意事项

- 未提升权限时，当前 Codex 沙盒内 `wsl.exe` 无法访问已安装 WSL；提升权限后 WSL CUDA 环境可用。
- Windows fallback 环境是 CPU 版 `torch`，不能用于 7B QLoRA 训练。
- 训练时出现 `Warning: You are sending unauthenticated requests to the HF Hub`，但本次使用本地 cache 成功加载；后续如果需要联网下载，仍应在 WSL 中确认 `HF_TOKEN` 已加载。
- reload check 的 raw output 不是干净单词，而是 `1. Positive` 加解释文本；后续正式评估仍需通过 `extract_label` 将 raw output 解析为 `negative/neutral/positive`。

### 当前仍未验证

- 尚未生成正式 benchmark 指标：不能写已有可信 `accuracy`、`macro F1`、`weighted F1`。
- 尚未评估训练后 adapter 的分类效果。
- 尚未生成 `confusion matrix`、`results.md`、`error_cases.csv`。

### 下一步建议

- 先跑 `python student_local/run_sentiment_benchmark.py --backend hf --max-samples 32`，生成 base FinGPT LoRA 的首版指标。
- 再扩展评估脚本支持本次训练出的本地 adapter：`student_local/outputs/fpb_qlora_sanity_20260521_am`。
- D3 再整理错误样本和结果表，避免在没有指标证据前写 README 成果段。

## 2026-05-22

### D2 下午：评估与结果闭环

### 本次目标

- 检查并补齐 `student_local/run_sentiment_benchmark.py`，确保评估脚本输出 `accuracy`、`macro F1`、`weighted F1`。
- 增加 `confusion matrix` 和错误样本文件，方便后续 D3 做错误分析。
- 跑首版 HF benchmark，生成有脚本输出和文件产物支撑的真实指标。

### 已完成

- 更新 `student_local/run_sentiment_benchmark.py`：
  - 原有 `accuracy`、`f1_macro`、`f1_weighted` 保留。
  - 新增 `--metrics-json`，保存结构化指标。
  - 新增 `--confusion-matrix-csv`，保存混淆矩阵。
  - 新增 `--errors-csv`，保存误判样本。
  - 新增 `unparsed_predictions` 统计，用于观察模型输出无法解析成标准标签的情况。
- 新增 `student_local/results.md`：
  - 记录首版 benchmark 命令、指标表、混淆矩阵、产物路径和注意事项。
- 语法检查通过：
  - `.runtime\conda\fingpt310win\python.exe -m py_compile student_local\run_sentiment_benchmark.py`
  - WSL 中 `python -m py_compile student_local/run_sentiment_benchmark.py`
- 首版 HF benchmark 已完成：
  - backend：`hf`
  - base model：`NousResearch/Llama-2-7b-hf`
  - adapter：`oliverwang15/FinGPT_v32_Llama2_Sentiment_Instruction_LoRA_FT`
  - dataset：Financial PhraseBank `sentences_50agree`
  - split：固定 `seed=42` 测试切分前 32 条
  - samples：32
  - accuracy：`0.2500`
  - f1_macro：`0.2222`
  - f1_weighted：`0.3125`
  - unparsed_predictions：`11`
  - error_cases：`24`

### 关键命令

- 命令：`wsl.exe bash -lc "cd /mnt/d/Learn/20_Projects/FinGPT-github && source ~/.bashrc && source student_local/activate_wsl_env.sh && python -m py_compile student_local/run_sentiment_benchmark.py && python student_local/run_sentiment_benchmark.py --backend hf --max-samples 32 --batch-size 2 --output-csv student_local/outputs/fpb_benchmark_hf_32_20260522.csv --metrics-json student_local/outputs/fpb_benchmark_hf_32_20260522_metrics.json --confusion-matrix-csv student_local/outputs/fpb_benchmark_hf_32_20260522_confusion_matrix.csv --errors-csv student_local/outputs/fpb_benchmark_hf_32_20260522_errors.csv"`
  - 作用：在 WSL CUDA 环境中先检查评估脚本语法，再加载 HF base model + FinGPT LoRA adapter，对 32 条固定测试样本生成预测，计算真实评估指标，并保存预测明细、指标、混淆矩阵和误判样本。

### 产物路径

- `student_local/results.md`
- `student_local/outputs/fpb_benchmark_hf_32_20260522.csv`
- `student_local/outputs/fpb_benchmark_hf_32_20260522_metrics.json`
- `student_local/outputs/fpb_benchmark_hf_32_20260522_confusion_matrix.csv`
- `student_local/outputs/fpb_benchmark_hf_32_20260522_errors.csv`

### 混淆矩阵

| actual \ predicted | negative | neutral | positive | unparsed |
| --- | ---: | ---: | ---: | ---: |
| negative | 0 | 3 | 0 | 1 |
| neutral | 4 | 6 | 4 | 5 |
| positive | 0 | 2 | 2 | 5 |
| unparsed | 0 | 0 | 0 | 0 |

### 失败点与注意事项

- 本次 benchmark 运行时仍提示 `Warning: You are sending unauthenticated requests to the HF Hub`；由于本地 cache 可用，模型仍成功加载。后续若换机器或清空 cache，需要重新确认 WSL 中 `HF_TOKEN` 已加载。
- `unparsed_predictions=11`，说明当前 prompt 或输出解析还不稳定。部分 raw output 如 `p` 或乱码没有被解析为标准标签，后续可围绕 prompt 约束、label parser、max_new_tokens 和生成配置做改进。
- 指标偏低，不能包装成“模型效果好”。当前可写成：已经建立了真实评估闭环，并发现首版输出解析不稳定的问题。

### 当前仍未验证

- 尚未评估本地 sanity training 产物 `student_local/outputs/fpb_qlora_sanity_20260521_am`。
- 尚未做 20 条错误样本的人工分类和错误类型总结。
- 尚未比较不同 prompt、不同 label parser 或不同 adapter 的指标变化。

### D2 晚上：日志、复盘与简历边界

### 本次目标

- 汇总 D2 已实际执行的训练与评估命令。
- 记录成功结果、失败点、报错/警告和产物路径。
- 判断哪些内容可以进入简历草稿，哪些必须暂时排除。
- 固化新的协作规则：后续 AI 默认使用“学习解释模式”，在完成任务后解释关键代码、命令、专有名词和面试口径。

### 今天实际跑过的关键命令

- 命令：`wsl.exe bash -lc "cd /mnt/d/Learn/20_Projects/FinGPT-github && source ~/.bashrc && source student_local/activate_wsl_env.sh && python student_local/check_env.py"`
  - 作用：确认 WSL CUDA 训练环境是否可用，记录 Python、Torch、CUDA、GPU、bf16 和显存信息。
  - 结果：WSL 环境可用，`torch=2.10.0+cu128`，`cuda available=True`，GPU 为 `NVIDIA GeForce RTX 5070`，显存 `11.94 GiB`。
- 命令：`.runtime\conda\fingpt310win\python.exe student_local\check_fpb_data.py`
  - 作用：确认 Financial PhraseBank 本地数据和 `fpb_mini` 固定 seed 切分没有漂移。
  - 结果：`fpb_full=4846`，`fpb_mini train=128/test=32`，`mini_train_matches_seed_split=True`，`mini_test_matches_seed_split=True`。
- 命令：`wsl.exe bash -lc "cd /mnt/d/Learn/20_Projects/FinGPT-github && source ~/.bashrc && source student_local/activate_wsl_env.sh && python student_local/train_sentiment_qlora.py --output-dir student_local/outputs/fpb_qlora_sanity_20260521_am --max-train-samples 8 --max-eval-samples 4 --num-train-epochs 1 --gradient-accumulation-steps 1 --logging-steps 1 --train-batch-size 1 --eval-batch-size 1 --max-length 192"`
  - 作用：用极小样本验证 QLoRA 训练闭环，包括数据读取、tokenize、Trainer 训练、checkpoint/adapter 保存和 reload check。
  - 结果：完成 8 个 training step；`train_loss=2.416`，`eval_loss=1.122`，`train_runtime=14.01s`；产物保存到 `student_local/outputs/fpb_qlora_sanity_20260521_am`。
- 命令：`wsl.exe bash -lc "cd /mnt/d/Learn/20_Projects/FinGPT-github && source ~/.bashrc && source student_local/activate_wsl_env.sh && python -m py_compile student_local/run_sentiment_benchmark.py && python student_local/run_sentiment_benchmark.py --backend hf --max-samples 32 --batch-size 2 --output-csv student_local/outputs/fpb_benchmark_hf_32_20260522.csv --metrics-json student_local/outputs/fpb_benchmark_hf_32_20260522_metrics.json --confusion-matrix-csv student_local/outputs/fpb_benchmark_hf_32_20260522_confusion_matrix.csv --errors-csv student_local/outputs/fpb_benchmark_hf_32_20260522_errors.csv"`
  - 作用：在 WSL CUDA 环境中运行首版 HF benchmark，生成真实 `accuracy`、`macro F1`、`weighted F1`、混淆矩阵和误判样本。
  - 结果：32 条样本，`accuracy=0.2500`，`f1_macro=0.2222`，`f1_weighted=0.3125`，`unparsed_predictions=11`，`error_cases=24`。

### 今天已验证的成功结果

- 已验证本地 WSL + RTX 5070 可运行 HF/QLoRA 训练与评估相关脚本。
- 已验证 `student_local/train_sentiment_qlora.py` 可以完成最小训练闭环，并保存 LoRA adapter 与 checkpoint。
- 已验证 `student_local/run_sentiment_benchmark.py` 可以输出真实评估指标、混淆矩阵和错误样本。
- 已生成首版结果记录：`student_local/results.md`。

### 产物路径

- 训练产物：`student_local/outputs/fpb_qlora_sanity_20260521_am`
- 训练 checkpoint：`student_local/outputs/fpb_qlora_sanity_20260521_am/checkpoint-8`
- benchmark 预测明细：`student_local/outputs/fpb_benchmark_hf_32_20260522.csv`
- benchmark 指标：`student_local/outputs/fpb_benchmark_hf_32_20260522_metrics.json`
- benchmark 混淆矩阵：`student_local/outputs/fpb_benchmark_hf_32_20260522_confusion_matrix.csv`
- benchmark 误判样本：`student_local/outputs/fpb_benchmark_hf_32_20260522_errors.csv`
- 人工可读结果页：`student_local/results.md`

### 失败点、警告与限制

- 未提升权限时，当前 Codex 沙盒内 `wsl.exe` 无法访问已安装 WSL；提升权限后 WSL CUDA 环境可用。
- Windows fallback 环境中的 `torch` 是 CPU 版，不能用于 7B QLoRA 训练。
- 训练和 benchmark 都出现过 Hugging Face 未认证请求警告；本次依赖本地 cache 成功加载模型。后续换机器、清空 cache 或重新下载模型前，需要确认 WSL 中 `HF_TOKEN` 已加载。
- reload check 输出为 `1. Positive\nExplanation: L&T`，说明模型可以生成，但输出格式不够干净。
- benchmark 中 `unparsed_predictions=11`，部分 raw output 如 `p` 或乱码无法解析为标准标签，说明当前 prompt 和 label parser 仍需改进。
- 首版指标偏低，不能包装成高性能结果；当前更适合写成“已建立评估闭环并发现输出解析问题”。

### 可以进入简历草稿的内容

- 可以写：在 WSL + RTX 5070 本地环境中复现 FinGPT 金融情绪分析的最小训练与评估闭环。
- 可以写：基于 Financial PhraseBank `sentences_50agree` 构建固定 `seed=42` 的可复现数据切分。
- 可以写：使用 QLoRA 思路完成小样本 sanity training，保存 LoRA adapter 与 checkpoint，并完成 reload check。
- 可以写：实现/补齐 benchmark 脚本，输出 `accuracy`、`macro F1`、`weighted F1`、confusion matrix 和 error cases。
- 可以写：首版 benchmark 暴露了 `unparsed` 输出较多的问题，并据此规划 prompt 约束和 label parsing 改进。

### 不能进入简历草稿的内容

- 不能写：完成了完整大规模 FinGPT 训练。
- 不能写：取得了高准确率或优秀 F1 指标。
- 不能写：已经完成系统性错误分析；目前只是生成了误判样本文件，还没有人工分类总结。
- 不能写：已经完成不同 prompt、不同 adapter 或本地训练 adapter 的系统对比。
- 不能写：复现了 FinGPT Forecaster、Robo-advisor、Trading、QuantPlatform、PDFDemo 或 Career 等其他模块。

### 后续默认解释模式已固化

- 已更新 `AGENTS.md`：新增 `Learning Explanation Mode`，要求后续任务默认解释关键代码、命令、专有名词、产物和面试口径。
- 已更新 `AI_CONTEXT.md`：把该解释模式记录为后续 AI 行为要求。
- 后续每次完成实质任务时，最终回答都应包括：做了什么、证据路径、关键代码/命令解释、相关专有名词解释、可写入简历的边界和下一步。

## 2026-05-25

### D3：README、错误分析与结果固化

### 本次目标

- 完成第三天任务：整理 README、错误分析、结果页、图表、输出目录说明和已知限制。
- 所有结论基于 D2 已生成的 benchmark、metrics、confusion matrix 和 error cases，不把未跑过的实验写成已完成。

### 已完成

- 重写 `student_local/README.md`：
  - 明确当前复现目标、数据集、模型、目录说明、推荐运行环境和最小复现命令。
  - 写入已验证 benchmark 指标和已知限制。
  - 补充可以写入简历与不能写入简历的边界。
- 补强 `student_local/results.md`：
  - 增加结果索引，统一列出 metrics、predictions、confusion matrix、error cases、error analysis 和 QLoRA sanity training 产物。
  - 增加 benchmark 解读、混淆矩阵解读、错误分析摘要、QLoRA sanity training 边界和面试安全口径。
- 新增 `student_local/error_cases_20_labeled.csv`：
  - 从 `student_local/outputs/fpb_benchmark_hf_32_20260522_errors.csv` 前 20 条误判样本出发，人工标注主错误类型。
- 新增 `student_local/error_analysis.md`：
  - 汇总 20 条误判样本的错误类型统计、主要发现、改进方向和复现边界。
- 新增 `student_local/outputs/fpb_benchmark_hf_32_20260522_confusion_matrix.svg`：
  - 基于已有 confusion matrix CSV 导出可读图表，方便 README/results 引用或后续展示。
- 更新 `AI_CONTEXT.md`：
  - 记录 D3 已完成的项目级事实和新增产物路径。

### 验证记录

- 命令：`$rows=Import-Csv -LiteralPath 'D:\Learn\20_Projects\FinGPT-github\student_local\error_cases_20_labeled.csv'; "rows=$($rows.Count)"; $rows | Group-Object error_type | Sort-Object Name | Select-Object Name,Count | Format-Table -AutoSize`
  - 作用：确认人工标注 CSV 能被 PowerShell 正常解析，并统计 20 条误判样本的错误类型数量。
  - 结果：`rows=20`；错误类型统计为 `unparsed_short_output=6`、`unparsed_noisy_output=4`、`neutral_positive_confusion=4`、`neutral_negative_confusion=3`、`negative_neutral_confusion=1`、`positive_neutral_confusion=1`、`unparsed_non_label_word=1`。
- 命令：`[xml](Get-Content -LiteralPath 'D:\Learn\20_Projects\FinGPT-github\student_local\outputs\fpb_benchmark_hf_32_20260522_confusion_matrix.svg' -Raw); 'svg_xml_ok'`
  - 作用：确认导出的 SVG 是合法 XML，避免后续展示或引用时报格式错误。
  - 结果：输出 `svg_xml_ok`。
- 命令：`Get-Item -LiteralPath 'D:\Learn\20_Projects\FinGPT-github\student_local\README.md','D:\Learn\20_Projects\FinGPT-github\student_local\results.md','D:\Learn\20_Projects\FinGPT-github\student_local\error_analysis.md','D:\Learn\20_Projects\FinGPT-github\student_local\error_cases_20_labeled.csv','D:\Learn\20_Projects\FinGPT-github\student_local\outputs\fpb_benchmark_hf_32_20260522_confusion_matrix.svg' | Select-Object Name,Length | Format-Table -AutoSize`
  - 作用：确认 D3 关键产物文件均已生成且非空。
  - 结果：5 个关键文件均存在且有内容。

### 产物路径

- `student_local/README.md`
- `student_local/results.md`
- `student_local/error_analysis.md`
- `student_local/error_cases_20_labeled.csv`
- `student_local/outputs/fpb_benchmark_hf_32_20260522_confusion_matrix.svg`

### 主要结论

- D3 已完成文档固化和错误分析闭环，但分析范围仍是首版 32 条 benchmark 与前 20 条误判样本。
- 当前首要问题是输出格式不稳定：32 条 benchmark 中有 11 条 `unparsed`。
- 中性事实描述容易被模型按词面情绪误判，后续需要优化 prompt 和 label parser。

### 当前仍未验证

- 尚未重新运行改进 prompt 后的 benchmark。
- 尚未评估本地 QLoRA sanity adapter 在测试集上的表现。
- 尚未做多 prompt、多 adapter 或完整测试集系统对比。

### 下一步建议

- 优先改 `run_sentiment_benchmark.py` 的 prompt 约束和生成配置，目标是降低 `unparsed_predictions`。
- 改完后用同一套 32 条样本重新跑 benchmark，与 `fpb_benchmark_hf_32_20260522_metrics.json` 做对比。
- 如果 `unparsed` 明显下降，再扩大样本或评估本地 sanity adapter。
