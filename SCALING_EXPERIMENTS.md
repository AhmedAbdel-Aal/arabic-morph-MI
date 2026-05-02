# Scaling Experiment Runs

## Why This Needs To Change

Running one command at a time in Colab is fine for early debugging, but it does not scale to the study we actually need.

The experimental grid is already larger than a single notebook workflow:

- multiple models
- base vs affixed surfaces
- last / first / mean pooling
- tokenization diagnostics
- representation diagnostics
- repeated seeds
- eventually linear vs MLP probes

The goal should be to move from manual command execution to a repeatable batch runner on a rented GPU machine. Colab can remain useful for quick checks, but it should not be the main experiment engine.

## Desired Run Unit

Each run should still be a simple command with explicit settings:

```bash
MODEL=Qwen/Qwen3-1.7B-Base \
SURFACE=base \
POOLING=last \
RUN_ID=E03 \
BATCH_SIZE=4 \
bash scripts/colab_run.sh
```

This is good because every run is inspectable and reproducible. The scaling layer should not hide the command. It should only generate and execute a list of these commands.

## Experiment Matrix

The first serious matrix should be:

| Axis | Values |
|---|---|
| Models | `Qwen/Qwen3-1.7B-Base`, `Qwen/Qwen3-8B`, `QCRI/Fanar-1-9B`, `humain-ai/ALLaM-7B-Instruct-preview` |
| Surface | `base`, `full` |
| Pooling | `last`, `first`, `mean` |
| Seeds | start with `42`; later add `43`, `44`, `45`, `46` |

This gives:

```text
4 models x 2 surfaces x 3 pooling modes = 24 runs
```

With five seeds:

```text
24 x 5 = 120 runs
```

Do not start with 120. Start with the 24-run matrix, inspect failure modes, then add seeds.

## Run IDs

Manual IDs like `E03` are good for early experiments, but they are too coarse for a model matrix.

For batch runs, use structured run IDs:

```text
E06_qwen3_8b_base_last_s42
E06_qwen3_8b_base_first_s42
E06_qwen3_8b_base_mean_s42
E07_fanar_9b_base_last_s42
E08_allam_7b_full_last_s42
```

The ID should encode:

- experiment family
- model
- surface
- pooling
- seed

This makes the result folders readable without opening JSON.

## Colab Role

Keep Colab for:

- quick smoke tests
- debugging one failed model
- checking a new code path
- running the small Qwen model when away from a rented GPU

Do not use Colab for:

- full model matrix
- repeated seeds
- long runs with 8B/9B models
- final result production

Colab sessions are too easy to interrupt and too annoying for credential/state management.

## RunPod Role

RunPod should become the main execution environment.

Recommended setup:

1. Start a GPU pod with enough VRAM.
   - For Qwen3-1.7B: any modest GPU is fine.
   - For 7B-9B models: prefer at least 24 GB VRAM.
   - If running 8B/9B models comfortably with larger batches, prefer 40 GB or 48 GB.

2. Use a persistent volume.
   - Store the repo, model cache, and results on persistent storage.
   - This avoids redownloading models every time.

3. Clone the repo.

```bash
git clone https://github.com/AhmedAbdel-Aal/arabic-morph-MI.git
cd arabic-morph-MI
```

4. Install once.

```bash
python -m pip install --upgrade pip
python -m pip install -e .
```

5. Set Hugging Face cache on the persistent volume.

```bash
export HF_HOME=/workspace/hf_cache
export TRANSFORMERS_CACHE=/workspace/hf_cache
```

6. Authenticate if needed.

```bash
huggingface-cli login
```

This matters for gated models such as Llama and possibly other model repos.

## Batch Execution Strategy

Create a plain-text command list first. Example:

```text
MODEL=Qwen/Qwen3-8B SURFACE=base POOLING=last RUN_ID=E06_qwen3_8b_base_last_s42 BATCH_SIZE=1 bash scripts/colab_run.sh
MODEL=Qwen/Qwen3-8B SURFACE=base POOLING=first RUN_ID=E06_qwen3_8b_base_first_s42 BATCH_SIZE=1 bash scripts/colab_run.sh
MODEL=Qwen/Qwen3-8B SURFACE=base POOLING=mean RUN_ID=E06_qwen3_8b_base_mean_s42 BATCH_SIZE=1 bash scripts/colab_run.sh
```

Then execute line by line in a loop.

Important behavior:

- If one run fails, log the failure and continue only if the failure is model-specific.
- If the code fails generally, stop the batch.
- Never overwrite an existing result folder.
- Keep stdout/stderr logs per run.

The eventual batch runner should write:

```text
batch_logs/<run_id>.log
batch_logs/<run_id>.status
```

Status values:

```text
running
done
failed
skipped_existing
```

## Results Sync

For final work, results should be committed back to GitHub.

Recommended pattern:

1. Run batch.
2. Inspect result folders.
3. Add/update `results/README.md`.
4. Add/update `experiments.md`.
5. Commit result JSON, diagnostics, curves, and interpretations.

Commands:

```bash
git add results experiments.md
git commit -m "Add batch morphology probe results"
git push
```

If result folders become too large, switch to one of:

- Git LFS for images/large diagnostics
- store heavy outputs externally and commit summaries
- keep JSON summaries in git and archive raw files on Drive/S3

For now, the result files are small enough to commit.

## Interpretation Workflow

Do not interpret each run independently by hand forever. For batch results, we need a summary script that reads all `results/*/results.json` files and produces one table:

```text
run_id
model
surface
pooling
probe
peak_accuracy
peak_layer
peak_normalized_depth
control_accuracy
selectivity
ngram_accuracy
model_minus_ngram
chance
```

This table should become the main source for comparing models.

Then interpretation should happen at three levels:

1. Per run: short `interpretation.md`.
2. Per model: model-level summary across surfaces/pooling.
3. Cross-model: final study-level interpretation.

## Scientific Priorities

The next batch should answer these questions in order:

1. Is the layer-0 weakness a final-subword artifact?
   - Compare `last`, `first`, and `mean` pooling.

2. Does template information survive affixation?
   - Compare `surface=base` vs `surface=full`.

3. Do Arabic-centric models differ from Qwen?
   - Compare Fanar and ALLaM to Qwen3-8B.

4. Is the signal stable across seeds?
   - Add repeated seeds after the first model/pooling matrix is stable.

5. Are layer curves tied to representation geometry?
   - Use `representation_diagnostics.json` to inspect effective dimensions and activation outliers.

## Immediate Plan

1. Finish E03/E04/E05 on Qwen3-1.7B.
2. Add a small batch-runner script.
3. Test the batch runner locally on dry/small commands.
4. Move to RunPod.
5. Run the 24-run matrix with seed 42.
6. Summarize into a single CSV/Markdown table.
7. Decide whether to add seeds or larger/gated models.

This keeps the project from becoming a pile of isolated result folders.
