import argparse
import inspect
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import torch
from datasets import DatasetDict, load_from_disk
from peft import LoraConfig, PeftModel, get_peft_model, prepare_model_for_kbit_training
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    DataCollatorForSeq2Seq,
    Trainer,
    TrainingArguments,
)

from student_local.common import (
    DEFAULT_BASE_MODEL,
    DEFAULT_INSTRUCTION,
    get_compute_dtype,
    get_hf_token,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a small local QLoRA sentiment fine-tune.")
    parser.add_argument("--base-model", default=DEFAULT_BASE_MODEL)
    parser.add_argument("--hf-token", default=None)
    parser.add_argument("--dataset-dir", default="student_local/data/fpb_mini")
    parser.add_argument("--output-dir", default="student_local/outputs/fpb_qlora_adapter")
    parser.add_argument("--max-length", type=int, default=256)
    parser.add_argument("--num-train-epochs", type=float, default=1.0)
    parser.add_argument("--learning-rate", type=float, default=2e-4)
    parser.add_argument("--train-batch-size", type=int, default=1)
    parser.add_argument("--eval-batch-size", type=int, default=1)
    parser.add_argument("--gradient-accumulation-steps", type=int, default=8)
    parser.add_argument("--logging-steps", type=int, default=5)
    parser.add_argument("--max-train-samples", type=int, default=None)
    parser.add_argument("--max-eval-samples", type=int, default=None)
    parser.add_argument("--skip-reload-check", action="store_true")
    parser.add_argument("--instruction", default=DEFAULT_INSTRUCTION)
    return parser.parse_args()


def get_quantization_config() -> BitsAndBytesConfig:
    return BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=get_compute_dtype(),
    )


def format_prompt(example: dict, instruction: str) -> str:
    return f"Instruction: {instruction}\nInput: {example['input']}\nAnswer: "


def tokenize_example(example: dict, tokenizer, instruction: str, max_length: int) -> dict:
    prompt = format_prompt(example, instruction=instruction)
    completion = f"{example['output']}{tokenizer.eos_token}"
    prompt_tokens = tokenizer(prompt, add_special_tokens=False)
    full_tokens = tokenizer(prompt + completion, add_special_tokens=False, truncation=True, max_length=max_length)

    prompt_len = min(len(prompt_tokens["input_ids"]), len(full_tokens["input_ids"]))
    labels = [-100] * prompt_len + full_tokens["input_ids"][prompt_len:]
    labels = labels[: len(full_tokens["input_ids"])]

    return {
        "input_ids": full_tokens["input_ids"],
        "attention_mask": full_tokens["attention_mask"],
        "labels": labels,
    }


def limit_dataset(dataset: DatasetDict, max_train_samples: int | None, max_eval_samples: int | None) -> DatasetDict:
    limits = {
        "train": max_train_samples,
        "test": max_eval_samples,
    }
    limited = {}
    for split_name, split in dataset.items():
        limit = limits.get(split_name)
        if limit is None:
            limited[split_name] = split
            continue
        limited[split_name] = split.select(range(min(limit, len(split))))
    return DatasetDict(limited)


def build_training_args(args: argparse.Namespace) -> TrainingArguments:
    training_kwargs = {
        "output_dir": args.output_dir,
        "learning_rate": args.learning_rate,
        "num_train_epochs": args.num_train_epochs,
        "per_device_train_batch_size": args.train_batch_size,
        "per_device_eval_batch_size": args.eval_batch_size,
        "gradient_accumulation_steps": args.gradient_accumulation_steps,
        "logging_steps": args.logging_steps,
        "save_strategy": "epoch",
        "save_total_limit": 2,
        "load_best_model_at_end": False,
        "report_to": "none",
        "bf16": torch.cuda.is_available() and torch.cuda.is_bf16_supported(),
        "fp16": torch.cuda.is_available() and not torch.cuda.is_bf16_supported(),
        "remove_unused_columns": False,
        "optim": "paged_adamw_8bit",
    }
    signature = inspect.signature(TrainingArguments.__init__)
    if "eval_strategy" in signature.parameters:
        training_kwargs["eval_strategy"] = "epoch"
    else:
        training_kwargs["evaluation_strategy"] = "epoch"
    return TrainingArguments(**training_kwargs)


def main() -> None:
    args = parse_args()
    hf_token = get_hf_token(args.hf_token)

    dataset = load_from_disk(args.dataset_dir)
    dataset = limit_dataset(dataset, args.max_train_samples, args.max_eval_samples)
    tokenizer = AutoTokenizer.from_pretrained(args.base_model, trust_remote_code=True, token=hf_token)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    tokenized = dataset.map(
        lambda row: tokenize_example(
            row,
            tokenizer=tokenizer,
            instruction=args.instruction,
            max_length=args.max_length,
        ),
        remove_columns=dataset["train"].column_names,
    )

    model = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        trust_remote_code=True,
        token=hf_token,
        device_map="auto",
        quantization_config=get_quantization_config(),
    )
    model.config.use_cache = False
    model.gradient_checkpointing_enable()
    model = prepare_model_for_kbit_training(model)

    lora_config = LoraConfig(
        r=8,
        lora_alpha=16,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "v_proj"],
    )
    model = get_peft_model(model, lora_config)

    training_args = build_training_args(args)

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized["train"],
        eval_dataset=tokenized["test"],
        data_collator=DataCollatorForSeq2Seq(tokenizer=tokenizer, model=model, padding=True),
    )
    trainer.train()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    print(f"saved adapter to: {output_dir}")
    if args.skip_reload_check:
        print("reload check skipped")
        return

    del trainer, model
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    # Sanity check: reload the saved adapter and run one short prediction.
    reloaded_base = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        trust_remote_code=True,
        token=hf_token,
        device_map="auto",
        quantization_config=get_quantization_config(),
    )
    reloaded = PeftModel.from_pretrained(reloaded_base, str(output_dir))
    reloaded.eval()

    sample_text = dataset["test"][0]["input"]
    prompt = format_prompt({"input": sample_text}, instruction=args.instruction)
    encoded = tokenizer(prompt, return_tensors="pt")
    if torch.cuda.is_available():
        encoded = {key: value.to("cuda") for key, value in encoded.items()}
    generated = reloaded.generate(
        **encoded,
        do_sample=False,
        max_new_tokens=12,
        pad_token_id=tokenizer.eos_token_id,
    )
    new_tokens = generated[:, encoded["input_ids"].shape[1] :]
    decoded = tokenizer.decode(new_tokens[0], skip_special_tokens=True).strip()
    print(f"reload check output: {decoded}")


if __name__ == "__main__":
    main()
