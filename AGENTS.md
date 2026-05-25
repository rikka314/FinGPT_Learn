# FinGPT Project Agent Instructions

本文件是本仓库的默认提示词入口。新对话进入 `D:\Learn\20_Projects\FinGPT-github` 时，AI 应自动阅读本文件，不需要用户手动调用任何 skill。

## Startup Order

1. 先读本文件。
2. 再读 `AI_CONTEXT.md`，把它当作项目长期事实和当前复现目标。
3. 如涉及实际执行、训练、评估、README 或简历素材，读 `WORKLOG.md`，确认哪些已经完成、哪些只是计划。
4. 再按任务读取最小必要代码或文档，不要先全仓库递归扫描。

## Working Language

- 默认使用简洁中文回复。
- 文件名、命令、Python API、模型名、指标名保留英文。
- 区分“计划”“已实现”“已验证”。没有脚本输出或日志证据时，不要把结果写成已完成。
- 后续给出代码或命令时，必须在下一行用简洁中文解释该行或该命令的具体作用，帮助用户理解而不是只复制运行。
- 后续执行操作时，要说明具体做了什么、为什么这么做、对项目复现有什么用；必要时补充能增进用户理解的背景知识。

## Learning Explanation Mode

用户是在复现项目的同时学习项目。后续每次完成代码、训练、评估、日志、README 或简历相关任务时，默认使用“学习解释模式”收尾，而不是只给结果。

回答应包含：

- 本次实际完成了什么，哪些是已验证结果，哪些仍只是计划或未验证。
- 涉及的关键文件和产物路径。
- 关键命令或关键代码块，并紧跟解释：这段代码/命令做什么、为什么需要它、对 FinGPT 复现闭环有什么用。
- 专有名词解释，例如 tokenizer、token、label、loss、checkpoint、adapter、LoRA、QLoRA、accuracy、macro F1、weighted F1、confusion matrix、error cases、unparsed 等。
- 面试可讲口径：只能基于脚本输出、日志或生成文件，不能夸大为完整大模型训练、高分结果或系统性错误分析。
- 若结果不好看，也要如实解释原因和下一步改进方向；不要为了简历包装而隐藏失败点。

## Project Goal

用户克隆本仓库的主要目的不是维护上游 FinGPT，而是复现、研究并沉淀成可写入简历的项目经历。当前重点是 FinGPT 金融文本情绪分析，后续扩展到训练评估闭环、README、错误分析和结果固化。

## Local Work Boundary

- 上游代码和文档尽量保持可追踪，避免无关改动。
- 用户自己的复现脚本、数据准备、训练评估、输出和学习说明优先放在 `student_local/` 或明确的项目文档中。
- 大模型权重、数据集缓存、checkpoint、实验输出不要提交进仓库。
- 修改前先看现有 `student_local/README.md` 和相关脚本，复用已有路径和命令。

## Logging Rule

每次完成实质操作后更新 `WORKLOG.md`：

- 记录日期、目标、实际做了什么、关键命令、产物路径、失败点和下一步。
- 如果改变了项目级事实、默认流程、目录约定、运行方式或简历口径，同步更新 `AI_CONTEXT.md`。
- 训练、评估和图表结果必须来自脚本输出、日志或生成文件；不要只凭口头推测写入结果。

## Three-Day Execution Target

按 `AI_CONTEXT.md` 中的 D1-D3 计划推进。优先完成可验证的最小闭环：环境检查、Financial PhraseBank 数据切分、训练脚本、评估脚本、结果表、错误样本和 README。
