from __future__ import annotations

import numpy as np
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


def load_model(model_name: str, dtype: str):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    torch_dtype = torch.float32
    if device == "cuda" and dtype in {"auto", "float16", "fp16"}:
        torch_dtype = torch.float16
    if device == "cuda" and dtype in {"bfloat16", "bf16"}:
        torch_dtype = torch.bfloat16

    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch_dtype,
        device_map="auto" if device == "cuda" else None,
        trust_remote_code=True,
    )
    model.eval()
    input_device = str(next(model.parameters()).device)
    return tokenizer, model, input_device


def tokenization_diagnostics(texts: list[str], tokenizer) -> dict:
    rows = []
    counts = []
    for text in sorted(set(texts)):
        ids = tokenizer(text, add_special_tokens=True)["input_ids"]
        tokens = tokenizer.convert_ids_to_tokens(ids)
        counts.append(len(ids))
        rows.append(
            {
                "text": text,
                "n_tokens": len(ids),
                "token_ids": ids,
                "tokens": tokens,
            }
        )

    count_values, count_counts = np.unique(np.array(counts), return_counts=True)
    return {
        "n_texts": len(rows),
        "min_tokens": int(np.min(counts)),
        "max_tokens": int(np.max(counts)),
        "mean_tokens": float(np.mean(counts)),
        "median_tokens": float(np.median(counts)),
        "token_count_distribution": {
            str(int(value)): int(count) for value, count in zip(count_values, count_counts)
        },
        "items": rows,
    }


def encode_texts(
    texts: list[str],
    tokenizer,
    model,
    input_device: str,
    batch_size: int,
    pooling: str,
) -> dict[str, np.ndarray]:
    if pooling not in {"last", "first", "mean"}:
        raise ValueError("pooling must be one of: last, first, mean")

    unique_texts = sorted(set(texts))
    out: dict[str, np.ndarray] = {}

    for start in range(0, len(unique_texts), batch_size):
        batch_texts = unique_texts[start : start + batch_size]
        batch = tokenizer(batch_texts, return_tensors="pt", padding=True).to(input_device)
        with torch.no_grad():
            outputs = model(**batch, output_hidden_states=True, use_cache=False)

        mask = batch["attention_mask"]
        lengths = mask.sum(dim=1)
        rows = torch.arange(len(batch_texts), device=mask.device)

        layers = []
        for hidden in outputs.hidden_states:
            if pooling == "last":
                selected = hidden[rows, lengths - 1, :]
            elif pooling == "first":
                selected = hidden[rows, torch.zeros_like(lengths), :]
            else:
                selected = (hidden * mask.unsqueeze(-1)).sum(dim=1) / lengths.unsqueeze(-1)
            layers.append(selected.detach().cpu())
        hidden = torch.stack(layers, dim=1).float().numpy()

        for text, vector in zip(batch_texts, hidden):
            out[text] = vector
        print(f"encoded {min(start + batch_size, len(unique_texts))}/{len(unique_texts)} texts with {pooling} pooling")

    return out
