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

## Colab

In a Colab cell:

```bash
!REPO_URL=https://github.com/AhmedAbdel-Aal/arabic-morph-MI.git \
MODEL=Qwen/Qwen3-1.7B-Base \
BATCH_SIZE=4 \
bash <(curl -fsSL https://raw.githubusercontent.com/AhmedAbdel-Aal/arabic-morph-MI/main/scripts/colab_run.sh)
```

The script prints each step, installs the repo, checks that `data/productivity_dataset.json` exists, runs the probes, and prints the output files.
