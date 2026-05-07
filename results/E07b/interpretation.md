# Interpretation

Run: `E07b`  
Model: `QCRI/Fanar-1-9B`  
Surface: `full`  
Pooling: `last`  
Real split: `family`  
Purpose: Fanar full-form family-split robustness test.

## Lab-Head Summary

E07b is a very strong full-form result. Fanar gives the best `real_templates_random` full/family accuracy so far:

```text
Fanar E07b: 0.944
Qwen3-8B E06b: 0.931
Qwen3-1.7B E05b: 0.903
n-gram baseline: 0.667
```

The grouped split is clean:

```text
train_groups: 121
test_groups: 31
group_overlap: 0
```

This means Fanar is highly effective at recovering template labels from affixed real forms when sibling leakage is removed.

## Results

| Probe | Target | Split | Peak Layer | Probe Acc. | Control Acc. | Selectivity | N-Gram Acc. | Chance |
|---|---|---|---:|---:|---:|---:|---:|---:|
| `real_templates_random` | template | family | 7 | 0.944 | 0.083 | 0.861 | 0.667 | 0.077 |
| `nonce_templates_random` | template | item | 4 | 0.950 | 0.150 | 0.800 | 0.300 | 0.200 |
| `nonce_templates_heldout_roots` | template | held-out root | 3 | 1.000 | 0.100 | 0.900 | 0.600 | 0.200 |
| `train_real_test_nonce_overlap` | template | explicit | 5 | 0.770 | 0.230 | 0.540 | 0.590 | 0.200 |
| `train_nonce_test_real_overlap` | template | explicit | 6 | 0.860 | 0.193 | 0.667 | 0.753 | 0.200 |
| `nonce_roots_random` | root | item | 4 | 1.000 | 0.050 | 0.950 | 0.950 | 0.050 |
| `nonce_roots_heldout_templates` | root | held-out template | 2 | 1.000 | 0.000 | 1.000 | 0.950 | 0.050 |

`real_roots_random` is skipped, as in the other family-split runs, because a clean grouped root split is not supported by the current real data.

## Comparison To Other Full/Family Runs

| Probe | Qwen3-1.7B E05b | Qwen3-8B E06b | Fanar E07b |
|---|---:|---:|---:|
| `real_templates_random` | 0.903 | 0.931 | 0.944 |
| `train_real_test_nonce_overlap` | 0.800 | 0.890 | 0.770 |
| `train_nonce_test_real_overlap` | 0.807 | 0.907 | 0.860 |
| `nonce_templates_heldout_roots` | 1.000 | 1.000 | 1.000 |

The pattern is mixed but informative:

```text
Fanar is best on affixed real template classification.
Qwen3-8B is better on real/nonce transfer.
```

So Fanar seems very strong on real Arabic full forms, while Qwen3-8B is stronger at bridging between real and nonce domains.

## Tokenization

Fanar full forms are heavily split:

```text
mean tokens: 3.89
median: 4
max: 6
```

This is more fragmented than Qwen and ALLaM. Yet Fanar still reaches 0.944 on full-form family split. That is good evidence that last-token pooling remains viable even under heavier subword fragmentation.

## Representation Geometry

Fanar again has cleaner geometry than Qwen and ALLaM:

```text
effective dimensions remain broad across layers
no mid-layer collapse to one component
max activations stay moderate relative to Qwen/ALLaM outlier behavior
```

This makes Fanar a valuable model for layer-curve analysis. It may be the best model in this set for interpreting where the signal is available, not just whether it is decodable.

## Lab Decision

E07b strongly supports the affixed real-form part of the paper. If we cite one full-form Arabic-centric model result, this is the one.

The caveat is transfer: Fanar's real-to-nonce transfer is lower than Qwen3-8B. So the final paper should not simply say "Arabic-centric models are better." The more accurate claim is:

```text
Fanar is strongest on affixed real forms; Qwen3-8B is strongest on real/nonce transfer.
```
