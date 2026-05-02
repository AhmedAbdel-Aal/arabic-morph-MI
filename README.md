# Arabic Morph MI

Clean probing code for Arabic root-pattern morphology.

The expected dataset is Alakeel et al.'s `productivity_dataset.json`.
Put it at:

```text
data/productivity_dataset.json
```

Run:

```bash
../.venv/bin/python scripts/run_probes.py \
  --data data/productivity_dataset.json \
  --model Qwen/Qwen3-1.7B-Base \
  --surface base
```

The script runs five direct probes:

- real templates, random split
- nonce templates, random split
- nonce templates, held-out roots
- train real, test nonce on overlapping templates
- train nonce, test real on overlapping templates

Each run writes:

```text
results/<timestamp>_<model>_<surface>/results.json
results/<timestamp>_<model>_<surface>/curves.png
```
