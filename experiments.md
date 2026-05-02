# Experiment Tracker

Use this table as the source of truth for what has been run, what changed, and where to read the interpretation.

| ID | Status | Date | Model | Surface | Purpose | Command | Output / Interpretation |
|---|---|---|---|---|---|---|---|
| E01 | done | 2026-05-02 | `Qwen/Qwen3-1.7B-Base` | `base` | First v2 smoke test on template probes only | historical run; superseded by E02 command | [interpretation](results/E01_Qwen3-1.7B-Base_base_template/interpretation.md) |
| E02 | done | 2026-05-02 | `Qwen/Qwen3-1.7B-Base` | `base` | Template + root baseline with last-token pooling | `MODEL=Qwen/Qwen3-1.7B-Base SURFACE=base POOLING=last BATCH_SIZE=4 bash scripts/colab_run.sh` | [interpretation](results/E02_Qwen3-1.7B-Base_base_template_root/interpretation.md) |
| E03 | code ready | TBD | `Qwen/Qwen3-1.7B-Base` | `base` | Tokenization diagnostics for layer-0 weakness and early-layer spike | `MODEL=Qwen/Qwen3-1.7B-Base SURFACE=base POOLING=last BATCH_SIZE=4 bash scripts/colab_run.sh` | TBD |
| E04a | code ready | TBD | `Qwen/Qwen3-1.7B-Base` | `base` | First-subword pooling ablation | `MODEL=Qwen/Qwen3-1.7B-Base SURFACE=base POOLING=first BATCH_SIZE=4 bash scripts/colab_run.sh` | TBD |
| E04b | code ready | TBD | `Qwen/Qwen3-1.7B-Base` | `base` | Mean-pooling ablation | `MODEL=Qwen/Qwen3-1.7B-Base SURFACE=base POOLING=mean BATCH_SIZE=4 bash scripts/colab_run.sh` | TBD |
| E05 | code ready | TBD | `Qwen/Qwen3-1.7B-Base` | `full` | Affixed-form stress test | `MODEL=Qwen/Qwen3-1.7B-Base SURFACE=full POOLING=last BATCH_SIZE=4 bash scripts/colab_run.sh` | TBD |
| E06 | code ready | TBD | `Qwen/Qwen3-8B` | `base` | Larger Qwen comparison | `MODEL=Qwen/Qwen3-8B SURFACE=base POOLING=last BATCH_SIZE=1 bash scripts/colab_run.sh` | TBD |
| E07 | code ready | TBD | `QCRI/Fanar-1-9B` | `base` | Arabic-centric Fanar comparison | `MODEL=QCRI/Fanar-1-9B SURFACE=base POOLING=last BATCH_SIZE=1 bash scripts/colab_run.sh` | TBD |
| E08 | code ready | TBD | `humain-ai/ALLaM-7B-Instruct-preview` | `base` | Arabic-centric ALLaM comparison | `MODEL=humain-ai/ALLaM-7B-Instruct-preview SURFACE=base POOLING=last BATCH_SIZE=1 bash scripts/colab_run.sh` | TBD |
| E09 | code ready | TBD | same model as current run | `base` | PCA/effective-dimensionality and activation outlier analysis | produced automatically by any command above as `representation_diagnostics.json` | TBD |
| E10 | todo | TBD | model set | `base` | Linear probe + MLP probe, selectivity gap | not implemented yet | TBD |

## Current Reading

The current strongest result is E02's template probing: Qwen3-1.7B recovers template labels above chance, control, and n-gram baselines, especially for nonce held-out roots. Root probes are highly accurate but are mostly surface-solvable in the nonce data because the root consonants remain visible.

The immediate next priority is E03/E04, not a larger model run. We need tokenization diagnostics and pooling ablations to understand whether the layer-0 weakness and early-layer spike are caused by final-subword extraction in a causal decoder.
