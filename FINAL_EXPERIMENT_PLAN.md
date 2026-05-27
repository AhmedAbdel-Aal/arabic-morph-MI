# Final Experiment Plan

## Decision

The existing E03-E08b runs are pilot/model-selection runs. They are useful for interpretation and method development, but the final paper results should be rerun under one standardized protocol because the dataset changed.

Final main dataset:

```text
data/productivity_dataset_natural_almost100.json
```

Properties:

```text
natural-only rows: 1050
templates: 11
nonce rows: 0
synthetic rows: 0
```

Template counts:

```text
استفعل   100
افتعال   100
انفعل    100
فاعل     100
فعال      73
فعالة    100
فعلاء     85
فعول      92
فعيل     100
مفتعل    100
مفعول    100
```

## Current Completed Runs

Completed pilot runs:

```text
E03-E05b: Qwen3-1.7B method/pooling/full-form pilots
E06/E06b: Qwen3-8B
E07/E07b: Fanar-1-9B
E08/E08b: ALLaM-7B-Instruct-preview
REP01_*: representation-saving reruns for geometry analysis
```

These runs used the earlier Akeel-style dataset. They should not be mixed as final quantitative results with the new natural dataset.

## Nonce Policy

Run nonce only once per model, using the Akeel dataset.

Reason: the nonce rows are the same Akeel nonce rows. Re-running the same nonce subset under the natural dataset would be redundant because the natural dataset has no nonce rows. If we later want a real-to-nonce transfer comparison from our larger real set, that should be a separate explicitly named transfer experiment, not part of the main matrix.

## Final Model Set

Core model set:

```text
Qwen/Qwen3-1.7B-Base
Qwen/Qwen3-8B
QCRI/Fanar-1-9B
humain-ai/ALLaM-7B-Instruct-preview
```

Rationale:

```text
Qwen3-1.7B: small multilingual baseline, cheap enough for iteration
Qwen3-8B: larger multilingual comparison
Fanar-1-9B: Arabic-centric tokenizer/model comparison
ALLaM-7B: Arabic-centric instruction model comparison
```

Extended decoder candidates:

```text
meta-llama/Meta-Llama-3-8B
FreedomIntelligence/AceGPT-7B
inceptionai/jais-13b
```

Rationale:

```text
Llama-3-8B: strong general multilingual decoder baseline.
AceGPT-7B: Arabic-localized LLaMA-family decoder.
Jais-13B: Arabic-English bilingual decoder-only model trained with substantial Arabic data.
```

The extended set is valuable but not required for the first final run. Run it after the core matrix succeeds, because Jais may require `trust_remote_code` behavior/model-specific dependencies and is larger.

## Final Runs

Main runs per model:

```text
AKEEL30_<model>_full_last_family
NATURAL100_<model>_full_last_family
```

Both use:

```text
surface=full
pooling=last
real_split=family
save_representations=true
```

Akeel provides the controlled small real set and the shared nonce subset. Natural100 provides the larger natural corpus-attested real set. This is the main scientific comparison.

Optional base-form diagnostics:

```text
surface=base
pooling=last
real_split=item
```

These are not part of the main result. With the new natural dataset, base-form filtering keeps only unaffixed rows, so the base condition is much smaller and covers fewer templates.

## Commands

Run the core matrix:

```bash
bash scripts/run_final_experiments.sh
```

Useful RunPod settings:

```bash
BATCH_SIZE=1
OUTPUT_DIR=results/final
```

Hidden representations are saved by default because geometry analysis and later steering work need them.

To skip representation saving:

```bash
SAVE_REPRESENTATIONS=0 bash scripts/run_final_experiments.sh
```

Run optional base diagnostics:

```bash
RUN_BASE_DIAGNOSTICS=1 bash scripts/run_final_experiments.sh
```

Run extended decoder candidates after the core matrix succeeds:

```bash
MODEL_SET=extended bash scripts/run_final_experiments.sh
```

Run core and extended together only on a fresh output directory:

```bash
MODEL_SET=all OUTPUT_DIR=results/final_all bash scripts/run_final_experiments.sh
```

## Expected Outputs

```text
results/final/AKEEL30_qwen17b_full_last_family/
results/final/NATURAL100_qwen17b_full_last_family/
results/final/AKEEL30_qwen8b_full_last_family/
results/final/NATURAL100_qwen8b_full_last_family/
results/final/AKEEL30_fanar9b_full_last_family/
results/final/NATURAL100_fanar9b_full_last_family/
results/final/AKEEL30_allam7b_full_last_family/
results/final/NATURAL100_allam7b_full_last_family/
```

Each run writes:

```text
results.json
curves.png
tokenization_diagnostics.json
representation_diagnostics.json
hidden_representations.npz
```

## What Is Left

1. Run the final matrix on RunPod.
2. Summarize final results separately from pilot results.
3. Generate final cross-model plots from `results/final`.
4. Run extended decoder candidates only if the core matrix is clean and the GPU budget is still available.
