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
  --surface base \
  --pooling last
```

The script runs template and root probes:

- real templates, random split
- nonce templates, random split
- nonce templates, held-out roots
- train real, test nonce on overlapping templates
- train nonce, test real on overlapping templates
- real roots, random split
- nonce roots, random split
- nonce roots, held-out templates

Each probe also includes:

- a Hewitt-Liang-style control task: each word type is assigned a random label from the current target label set, and the same probe is trained on that control task
- selectivity: real probe accuracy minus control-task accuracy
- a character n-gram baseline on the same split

Each run writes:

```text
results/<timestamp>_<model>_<surface>_<pooling>/results.json
results/<timestamp>_<model>_<surface>_<pooling>/curves.png
```

## Colab

In Colab, use separate cells. First clone the repo:

```bash
!git clone https://github.com/AhmedAbdel-Aal/arabic-morph-MI.git
```

Then run the script:

```bash
%cd /content/arabic-morph-MI
!MODEL=Qwen/Qwen3-1.7B-Base SURFACE=base POOLING=last BATCH_SIZE=4 bash scripts/colab_run.sh
```

The script prints each step, installs the repo, checks that `data/productivity_dataset.json` exists, runs the probes, and prints the output files.

Useful ablation runs:

```bash
!MODEL=Qwen/Qwen3-1.7B-Base SURFACE=base POOLING=first BATCH_SIZE=4 bash scripts/colab_run.sh
!MODEL=Qwen/Qwen3-1.7B-Base SURFACE=base POOLING=mean BATCH_SIZE=4 bash scripts/colab_run.sh
!MODEL=Qwen/Qwen3-1.7B-Base SURFACE=full POOLING=last BATCH_SIZE=4 bash scripts/colab_run.sh
```

Each run writes `tokenization_diagnostics.json`, `representation_diagnostics.json`, `results.json`, and `curves.png`.
