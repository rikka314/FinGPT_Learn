# FinGPT Local Learning Guide

This folder is the smallest path from "I can read Python" to "I can reproduce a FinGPT sentiment workflow on my own machine."

## The Five Concepts To Learn First

`tokenizer`
- Turns text into integer IDs so the model can process it.
- In this project, the prompt template matters because different prompts create different token sequences.

`causal LM`
- A causal language model predicts the next token from left to right.
- FinGPT sentiment classification is still implemented as text generation: the model generates `positive`, `neutral`, or `negative`.

`LoRA`
- LoRA does not retrain every model weight.
- It adds small trainable matrices on top of a frozen base model, which is why local fine-tuning is possible on one consumer GPU.

`quantization`
- Quantization stores model weights with fewer bits, such as 4-bit instead of 16-bit.
- This lowers VRAM usage enough for a 7B model to fit on your RTX 5070 12GB in a practical local setup.

`F1`
- F1 balances precision and recall.
- FinGPT papers and notebooks emphasize weighted F1 because sentiment datasets are often imbalanced.

## Suggested Order

1. Run `student_local/check_env.py` and make sure WSL, Python, Torch, and CUDA all work.
2. Run `student_local/run_sentiment_inference.py` and confirm the model returns legal labels.
3. Run `student_local/run_sentiment_benchmark.py --max-samples 32` and read accuracy and weighted F1.
4. Run `student_local/prepare_sentiment_subset.py`.
5. Run `student_local/train_sentiment_qlora.py` with the default small FPB dataset.

## Why Start With Sentiment Instead Of Forecaster

- Sentiment has a short path: `text -> prompt -> label`.
- Forecaster has a longer path: `prices + news + financials -> prompt assembly -> long generation`.
- If you understand the sentiment workflow first, the Forecaster code becomes much easier to read.

## How This Maps To The Original Repository

- Official sentiment notebooks live in `fingpt/FinGPT_Sentiment_Analysis_v3`.
- This local folder replaces notebook-only steps with scripts that are easier to rerun and debug on a single machine.
- The logic still follows the same idea as the original FinGPT v3 workflow: instruction prompt, Llama-family base model, LoRA adapter, and benchmark evaluation.
