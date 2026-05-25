import json
import os
import re
from typing import Iterator, List, Sequence
from urllib import error, request

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig


DEFAULT_BACKEND = os.environ.get("FINGPT_BACKEND", "hf")
DEFAULT_BASE_MODEL = os.environ.get("FINGPT_BASE_MODEL", "NousResearch/Llama-2-7b-hf")
DEFAULT_ADAPTER_MODEL = os.environ.get(
    "FINGPT_ADAPTER_MODEL",
    "oliverwang15/FinGPT_v32_Llama2_Sentiment_Instruction_LoRA_FT",
)
DEFAULT_OLLAMA_MODEL = os.environ.get("FINGPT_OLLAMA_MODEL", "qwen3.5:9b")
DEFAULT_OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11435")
DEFAULT_INSTRUCTION = (
    "What is the sentiment of this news? Please choose an answer from "
    "{negative/neutral/positive}."
)
LABELS = ("negative", "neutral", "positive")
LABEL_PATTERN = re.compile(r"\b(negative|neutral|positive)\b", re.IGNORECASE)
TOKEN_PATTERN = re.compile(r"[A-Za-z]+|[-+]?\d+|[+=-]")
LABEL_ALIASES = {
    "+": "positive",
    "plus": "positive",
    "pos": "positive",
    "positive": "positive",
    "bullish": "positive",
    "-": "negative",
    "minus": "negative",
    "neg": "negative",
    "negative": "negative",
    "bearish": "negative",
    "=": "neutral",
    "neutral": "neutral",
    "neu": "neutral",
    "flat": "neutral",
}
DEFAULT_DIGIT_LABEL_MAP = os.environ.get("FINGPT_DIGIT_LABEL_MAP", "0:negative,1:neutral,2:positive")


def batched(items: Sequence[str], batch_size: int) -> Iterator[Sequence[str]]:
    for start in range(0, len(items), batch_size):
        yield items[start : start + batch_size]


def build_prompt(text: str, instruction: str = DEFAULT_INSTRUCTION) -> str:
    return f"Instruction: {instruction}\nInput: {text}\nAnswer: "


def build_ollama_prompt(text: str, instruction: str = DEFAULT_INSTRUCTION) -> str:
    return (
        "You are a financial sentiment classifier.\n"
        f"{instruction}\n"
        "Return exactly one word from: negative, neutral, positive.\n"
        f"Text: {text}\n"
        "Label: "
    )


def parse_digit_label_map(mapping_text: str | None = DEFAULT_DIGIT_LABEL_MAP) -> dict[str, str]:
    if not mapping_text:
        return {}
    mapping: dict[str, str] = {}
    for item in mapping_text.split(","):
        item = item.strip()
        if not item or ":" not in item:
            continue
        key, value = item.split(":", 1)
        key = key.strip()
        value = value.strip().lower()
        if key and value in LABELS:
            mapping[key] = value
    return mapping


def normalize_label_token(token: str) -> str:
    return token.strip().strip("`'\"[](){}.,:;!?").lower()


def extract_label(text: str, digit_label_map: dict[str, str] | None = None) -> str:
    digit_label_map = digit_label_map if digit_label_map is not None else parse_digit_label_map()
    tail = text.split("Answer:", 1)[-1].strip()
    search_spaces = [tail] if tail else []
    if tail != text.strip():
        search_spaces.append(text.strip())

    for candidate in search_spaces:
        match = LABEL_PATTERN.search(candidate)
        if match:
            return match.group(1).lower()

    for candidate in search_spaces:
        normalized = normalize_label_token(candidate)
        if normalized in LABEL_ALIASES:
            return LABEL_ALIASES[normalized]
        if normalized in digit_label_map:
            return digit_label_map[normalized]
        for token in TOKEN_PATTERN.findall(candidate):
            normalized_token = normalize_label_token(token)
            if normalized_token in LABEL_ALIASES:
                return LABEL_ALIASES[normalized_token]
            if normalized_token in digit_label_map:
                return digit_label_map[normalized_token]
    return "unparsed"


def get_compute_dtype() -> torch.dtype:
    if not torch.cuda.is_available():
        return torch.float32
    if torch.cuda.is_bf16_supported():
        return torch.bfloat16
    return torch.float16


def get_quantization_config(load_in_4bit: bool) -> BitsAndBytesConfig | None:
    if not load_in_4bit or not torch.cuda.is_available():
        return None
    return BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=get_compute_dtype(),
    )


def load_tokenizer(base_model: str, hf_token: str | None = None):
    tokenizer = AutoTokenizer.from_pretrained(
        base_model,
        trust_remote_code=True,
        token=hf_token,
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "left"
    return tokenizer


def load_model_and_tokenizer(
    base_model: str = DEFAULT_BASE_MODEL,
    adapter_model: str | None = DEFAULT_ADAPTER_MODEL,
    hf_token: str | None = None,
    load_in_4bit: bool = True,
):
    tokenizer = load_tokenizer(base_model=base_model, hf_token=hf_token)
    model = AutoModelForCausalLM.from_pretrained(
        base_model,
        trust_remote_code=True,
        token=hf_token,
        device_map="auto" if torch.cuda.is_available() else None,
        torch_dtype=None if torch.cuda.is_available() else torch.float32,
        quantization_config=get_quantization_config(load_in_4bit=load_in_4bit),
    )
    if adapter_model:
        model = PeftModel.from_pretrained(model, adapter_model, token=hf_token)
    model.eval()
    return tokenizer, model


def move_batch_to_runtime_device(batch: dict) -> dict:
    if not torch.cuda.is_available():
        return batch
    return {key: value.to("cuda") for key, value in batch.items()}


@torch.inference_mode()
def predict_sentiments(
    texts: Sequence[str],
    tokenizer,
    model,
    instruction: str = DEFAULT_INSTRUCTION,
    batch_size: int = 4,
    max_input_length: int = 384,
    max_new_tokens: int = 12,
) -> List[dict]:
    results: List[dict] = []
    for batch_texts in batched(list(texts), batch_size):
        prompts = [build_prompt(text=text, instruction=instruction) for text in batch_texts]
        tokenized = tokenizer(
            prompts,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=max_input_length,
        )
        tokenized = move_batch_to_runtime_device(tokenized)
        generated = model.generate(
            **tokenized,
            do_sample=False,
            max_new_tokens=max_new_tokens,
            pad_token_id=tokenizer.eos_token_id,
        )
        new_tokens = generated[:, tokenized["input_ids"].shape[1] :]
        decoded = tokenizer.batch_decode(new_tokens, skip_special_tokens=True)
        for text, prompt, output in zip(batch_texts, prompts, decoded):
            results.append(
                {
                    "input": text,
                    "prompt": prompt,
                    "raw_output": output.strip(),
                    "prediction": extract_label(output),
                }
            )
    return results


def get_hf_token(explicit_token: str | None = None) -> str | None:
    return explicit_token or os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")


def normalize_ollama_host(host: str) -> str:
    if host.startswith("http://") or host.startswith("https://"):
        return host.rstrip("/")
    return f"http://{host.rstrip('/')}"


def ollama_generate(
    prompt: str,
    model: str = DEFAULT_OLLAMA_MODEL,
    host: str = DEFAULT_OLLAMA_HOST,
    request_timeout: int = 180,
) -> str:
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "think": False,
        "options": {
            "temperature": 0,
            "num_predict": 12,
        },
    }
    url = f"{normalize_ollama_host(host)}/api/generate"
    req = request.Request(
        url=url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=request_timeout) as response:
            body = response.read().decode("utf-8")
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Ollama request failed with HTTP {exc.code}: {detail}") from exc
    except error.URLError as exc:
        raise RuntimeError(
            f"Could not reach Ollama at {normalize_ollama_host(host)}. "
            "Start `ollama serve` and verify OLLAMA_HOST."
        ) from exc
    parsed = json.loads(body)
    return str(parsed.get("response", "")).strip()


def predict_sentiments_ollama(
    texts: Sequence[str],
    model: str = DEFAULT_OLLAMA_MODEL,
    host: str = DEFAULT_OLLAMA_HOST,
    instruction: str = DEFAULT_INSTRUCTION,
    request_timeout: int = 180,
) -> List[dict]:
    results: List[dict] = []
    for text in texts:
        prompt = build_ollama_prompt(text=text, instruction=instruction)
        output = ollama_generate(
            prompt=prompt,
            model=model,
            host=host,
            request_timeout=request_timeout,
        )
        results.append(
            {
                "input": text,
                "prompt": prompt,
                "raw_output": output,
                "prediction": extract_label(output),
            }
        )
    return results
