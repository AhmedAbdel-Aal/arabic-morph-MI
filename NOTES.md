# Notes

## Model Plan

Initial development and smoke-test experiments use:

```text
Qwen/Qwen3-1.7B-Base
```

This model is small enough to iterate on quickly. Results from this model are engineering evidence first; the main study should use the larger comparison set below.

Main Alakeel-aligned representation-probing models:

```text
Qwen/Qwen3-8B
QCRI/Fanar-1-9B
humain-ai/ALLaM-7B-Instruct-preview
meta-llama/Meta-Llama-3-8B
```

These correspond to the open-weight or accessible-weight models from the Alakeel et al. comparison. GPT-4 and GPT-4o are excluded from representation probing because their hidden states are not available. Cohere Command R7B is lower priority because access and licensing are more restrictive.

For most runs, changing `--model` should be enough:

```bash
../.venv/bin/python scripts/run_probes.py \
  --data data/productivity_dataset.json \
  --model Qwen/Qwen3-1.7B-Base \
  --surface base
```

Llama 3 may require Hugging Face access approval and a valid local HF token. Larger models may require reducing `--batch-size`.
