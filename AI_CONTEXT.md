# FinGPT AI Context

最后更新：2026-05-25

## 默认提示词摘要

这是一个克隆来的 FinGPT 研究复现仓库。用户的目标是在三天内把金融文本情绪分析方向做成一个可复现、可解释、可写入简历的项目。AI 在本项目中应默认协助完成复现、实验记录、README、错误分析、结果固化和简历表述，不要把没有验证过的内容写成已完成成果。

新对话应自动读取：

1. `AGENTS.md`
2. `AI_CONTEXT.md`
3. `WORKLOG.md`
4. 当前任务相关的最小必要代码或文档

## 当前状态

- 仓库路径：`D:\Learn\20_Projects\FinGPT-github`
- 上游项目：FinGPT
- 当前研究主线：金融文本情绪分析
- 已有本地研究层：`student_local/`
- 已有脚本包括环境检查、WSL/Windows 环境设置、情绪推理、Financial PhraseBank 小样本 benchmark、数据子集准备、QLoRA sanity training。
- 用户说明：目前主要想复现和研究项目，并准备未来写进简历。
- 用户已在 WSL 中实现过金融文本情绪分析。后续 AI 需要查 `WORKLOG.md` 和脚本输出确认哪些结果已经实际跑通。
- 2026-05-21 已验证：WSL 中 `HF_TOKEN` 已配置；`NousResearch/Llama-2-7b-hf` 和 `oliverwang15/FinGPT_v32_Llama2_Sentiment_Instruction_LoRA_FT` 在线访问检查均通过。本地 `.runtime/hf-home` cache 也可离线加载 base model + FinGPT LoRA adapter。`run_sentiment_inference.py --backend hf` 已完成一次 HF/LoRA 最小推理，输出合法情绪标签。
- 2026-05-21 已验证：`student_local/data/fpb_full` 含 Financial PhraseBank `sentences_50agree` 全量 4846 条；`student_local/data/fpb_mini` 为 `seed=42`、`test_size=0.2` 切分后截取的 128 条 train 和 32 条 test，字段为 `instruction/input/output`。
- 2026-05-21 已验证：`student_local/train_sentiment_qlora.py` 已完成一次最小 QLoRA sanity training，使用 `fpb_mini` 中 8 条训练样本和 4 条评估样本，输出目录为 `student_local/outputs/fpb_qlora_sanity_20260521_am`；脚本完成 tokenize、Trainer 训练、checkpoint/adapter 保存和 reload check。该结果只能证明训练闭环可运行，不能当作正式模型效果指标。
- 2026-05-22 已验证：`student_local/run_sentiment_benchmark.py` 已补齐 metrics JSON、confusion matrix CSV 和 error cases CSV 输出；HF FinGPT LoRA 在 Financial PhraseBank 固定 seed 测试切分前 32 条样本上的首版 benchmark 结果为 `accuracy=0.2500`、`f1_macro=0.2222`、`f1_weighted=0.3125`、`unparsed_predictions=11`，产物记录在 `student_local/results.md` 和 `student_local/outputs/fpb_benchmark_hf_32_20260522*`。该结果可作为首版真实评估证据，但也暴露出 prompt/输出解析仍需改进。
- 2026-05-25 已完成 D3 结果固化：`student_local/README.md` 已重写为复现说明入口；`student_local/results.md` 已补强结果索引、benchmark 解读、QLoRA sanity training 边界和面试口径；`student_local/error_cases_20_labeled.csv` 对前 20 条误判样本做人工错误类型标注；`student_local/error_analysis.md` 总结主要错误类型；`student_local/outputs/fpb_benchmark_hf_32_20260522_confusion_matrix.svg` 导出混淆矩阵图表。D3 产物基于已有 32 条 benchmark，不能扩写为大规模系统性实验。
- 2026-05-26 已新增新闻情绪因子 CSV 生成入口：`student_local/build_news_sentiment_factor.py` 读取 `student_local/news/raw_news.csv` 约定字段，输出逐条新闻 `student_local/outputs/news_sentiment_items.csv` 和日频因子 `student_local/outputs/news_sentiment_daily.csv`。已用 `student_local/news/raw_news_sample.csv` 的 8 条样例跑通 `lexicon` backend，验证输出为 8 条 item、6 条 daily，且 `sentiment_score = prob_positive - prob_negative`。当前样例验证只证明 CSV 契约和聚合逻辑可用，不代表真实 FinGPT 新闻推理质量。

## 目录约定

- `fingpt/`：上游 FinGPT 代码，尽量保持干净，只在明确需要时修改。
- `student_local/`：用户本地复现、训练、评估、学习说明、可提交脚本的主要区域。
- `student_local/news/`：新闻情绪因子输入约定与样例数据；真实输入默认使用 `raw_news.csv`，字段为 `symbol,published_at,title,summary,source,url`。
- `student_local/data/`：本地数据或切分结果，默认不提交。
- `student_local/outputs/`：实验输出、日志、checkpoint、图表，默认不提交。
- `AGENTS.md`：项目自动默认提示词入口。
- `AI_CONTEXT.md`：项目长期事实、目标和协作规则。
- `WORKLOG.md`：后续操作记录和每日进度。

## 运行与复现偏好

- 优先使用 WSL Ubuntu 执行 Python/训练相关命令。
- Windows PowerShell 仅作为环境检查、启动本地服务或备选路径。
- 默认优先复用 `student_local/README.md` 中的命令。
- Hugging Face gated 模型需要 `HF_TOKEN` 和模型访问权限；当前 WSL 已配置 token，后续仍不要把 token 写入仓库或日志。
- 当前 HF backend 可在线访问模型仓库，也可在已有本地 cache 条件下离线运行；若换机器、清空 cache 或更换模型，需要重新确认 `HF_TOKEN`、模型权限和下载能力。
- 如果显存不足，优先用小模型、短轮数、少样本 sanity check，而不是直接承诺完整训练。
- 所有结果必须来自脚本输出、日志或生成文件。

## 三天计划

### D1: FinGPT 环境与数据切分

- 上午前 2h：搭建总工程目录；创建 `FinGPT`、`QuantPlatform`、`PDFDemo`、`Career` 四个目录；写 README 骨架。
- 上午后 2h：盘点 FinGPT 环境；本地 GPU / Colab 二选一；锁定 `requirements.txt` 或 `environment.yml`。
- 下午前 2h：阅读 Hugging Face 文本分类、PEFT LoRA、bitsandbytes 4-bit 文档，整理命令模板。
- 下午后 2h：下载 Financial PhraseBank，写 `split_dataset.py`，固定随机种子和数据切分。
- 晚上 2h：建立 `WORKLOG.md`，记录今日问题、明日任务和不可写进简历的内容。

### D2: FinGPT 训练与评估闭环

- 上午前 2h：写 `train_fingpt.py`：数据加载、tokenize、Trainer、保存 checkpoint。
- 上午后 2h：跑通最小训练闭环；如果显存不足，先用小模型或短轮数 sanity check。
- 下午前 2h：写 `eval_fingpt.py`：accuracy、macro/weighted F1、confusion matrix。
- 下午后 2h：输出首版结果表，记录失败样本。
- 晚上 2h：用 AI 辅助解释报错和训练日志，但所有结果必须来自脚本输出。

### D3: FinGPT README、错误分析与结果固化

- 上午前 2h：重写 FinGPT README：项目目标、数据、环境、运行步骤。
- 上午后 2h：抽取 20 条误判样本，写 `error_cases.csv` 和错误类型总结。
- 下午前 2h：增加 `results.md`，对比不同参数或后端输出。
- 下午后 2h：统一日志与输出目录，导出图表。
- 晚上 2h：写“已知限制”：数据规模、split、硬件、模型选择、复现边界。

## 简历口径

只有已跑通并有记录的内容可以写成完成项。推荐口径先围绕：

- 复现 FinGPT 金融文本情绪分析流程。
- 基于 Financial PhraseBank 构建固定随机种子的数据切分。
- 使用 LoRA / QLoRA 思路完成小规模训练或 sanity check。
- 输出 accuracy、macro F1、weighted F1、confusion matrix 和错误样本分析。
- 沉淀可复现 README、命令模板和实验日志。

不要写：

- 没有跑通的完整大模型训练。
- 没有脚本输出支持的指标。
- 没有实际实现的 QuantPlatform、PDFDemo 或 Career 内容。

## 后续 AI 行为要求

- 开工前确认当前任务属于 D1、D2、D3 或其他维护任务。
- 优先推进最小可验证闭环，不要为了“完整”引入过多新框架。
- 每次修改后做窄验证；能跑脚本就跑脚本，不能跑要说明原因。
- 收尾时更新 `WORKLOG.md`；如果默认流程或项目事实改变，再更新本文件。
- 后续给用户代码或命令时，必须紧跟下一行解释该行或该命令的具体作用；默认不要只给可复制片段。
- 后续执行项目操作时，要明确说明做了什么、为什么这么做、对 FinGPT 复现闭环有什么用，并补充能帮助用户理解复现流程的必要背景。
- 后续默认使用“学习解释模式”：完成任务后需要列出关键代码/命令、解释每一步的作用、解释相关专有名词，并给出可用于面试但不夸大的项目表述。所有简历或面试口径必须基于脚本输出、日志或生成文件；结果偏低或失败点也要如实说明。
