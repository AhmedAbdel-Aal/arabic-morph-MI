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


def encode_last_token(texts: list[str], tokenizer, model, input_device: str, batch_size: int) -> dict[str, np.ndarray]:
    unique_texts = sorted(set(texts))
    out: dict[str, np.ndarray] = {}

    for start in range(0, len(unique_texts), batch_size):
        batch_texts = unique_texts[start : start + batch_size]
        batch = tokenizer(batch_texts, return_tensors="pt", padding=True).to(input_device)
        with torch.no_grad():
            outputs = model(**batch, output_hidden_states=True, use_cache=False)

        last = batch["attention_mask"].sum(dim=1) - 1
        rows = torch.arange(len(batch_texts), device=last.device)
        layers = [hidden[rows, last, :].detach().cpu() for hidden in outputs.hidden_states]
        hidden = torch.stack(layers, dim=1).float().numpy()

        for text, vector in zip(batch_texts, hidden):
            out[text] = vector
        print(f"encoded {min(start + batch_size, len(unique_texts))}/{len(unique_texts)} texts")

    return out
