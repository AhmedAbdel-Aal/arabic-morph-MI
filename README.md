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

Each probe also includes:

- a Hewitt-Liang-style control task: each word type is assigned a random template label, and the same probe is trained on that control task
- selectivity: real probe accuracy minus control-task accuracy
- a character n-gram baseline on the same split

Each run writes:

```text
results/<timestamp>_<model>_<surface>/results.json
results/<timestamp>_<model>_<surface>/curves.png
```

## Colab

In Colab, use separate cells. First clone the repo:

```bash
!git clone https://github.com/AhmedAbdel-Aal/arabic-morph-MI.git
```

Then run the script:

```bash
%cd /content/arabic-morph-MI
!MODEL=Qwen/Qwen3-1.7B-Base BATCH_SIZE=4 bash scripts/colab_run.sh
```

The script prints each step, installs the repo, checks that `data/productivity_dataset.json` exists, runs the probes, and prints the output files.
