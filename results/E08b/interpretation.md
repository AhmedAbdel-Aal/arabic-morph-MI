# Interpretation

Run: `E08b`  
Model: `humain-ai/ALLaM-7B-Instruct-preview`  
Surface: `full`  
Pooling: `last`  
Real split: `family`  
Purpose: ALLaM full-form family-split robustness test.

## Lab-Head Summary

E08b is better than E08 on real full-form template classification, but ALLaM remains weak on transfer.

The key full-form result:

```text
real_templates_random: 0.806
n-gram baseline:       0.667
control:              0.028
```

This is a real signal above n-grams and controls, but it is weaker than Qwen3-8B and Fanar:

```text
Qwen3-8B E06b: 0.931
Fanar E07b:    0.944
ALLaM E08b:    0.806
```

Most importantly, `nonce -> real full` transfer remains poor:

```text
ALLaM E08b: 0.587
n-gram:     0.753
```

## Results

| Probe | Target | Split | Peak Layer | Probe Acc. | Control Acc. | Selectivity | N-Gram Acc. | Chance |
|---|---|---|---:|---:|---:|---:|---:|---:|
| `real_templates_random` | template | family | 2 | 0.806 | 0.028 | 0.778 | 0.667 | 0.077 |
| `nonce_templates_random` | template | item | 4 | 0.950 | 0.100 | 0.850 | 0.300 | 0.200 |
| `nonce_templates_heldout_roots` | template | held-out root | 4 | 1.000 | 0.100 | 0.900 | 0.600 | 0.200 |
| `train_real_test_nonce_overlap` | template | explicit | 4 | 0.700 | 0.160 | 0.540 | 0.590 | 0.200 |
| `train_nonce_test_real_overlap` | template | explicit | 3 | 0.587 | 0.193 | 0.393 | 0.753 | 0.200 |
| `nonce_roots_random` | root | item | 4 | 1.000 | 0.050 | 0.950 | 0.950 | 0.050 |
| `nonce_roots_heldout_templates` | root | held-out template | 4 | 1.000 | 0.000 | 1.000 | 0.950 | 0.050 |

`real_roots_random` is skipped under grouped splitting, as expected.

## Comparison To Other Full/Family Runs

| Probe | Qwen3-1.7B E05b | Qwen3-8B E06b | Fanar E07b | ALLaM E08b |
|---|---:|---:|---:|---:|
| `real_templates_random` | 0.903 | 0.931 | 0.944 | 0.806 |
| `train_real_test_nonce_overlap` | 0.800 | 0.890 | 0.770 | 0.700 |
| `train_nonce_test_real_overlap` | 0.807 | 0.907 | 0.860 | 0.587 |
| `nonce_templates_heldout_roots` | 1.000 | 1.000 | 1.000 | 1.000 |

ALLaM is the weakest of the model set on full/family transfer, especially nonce-to-real.

## Tokenization

ALLaM full forms are tokenized compactly:

```text
mean tokens: 1.92
144 / 490 texts are one token
```

This compact tokenization does not produce the strongest results. Fanar has heavier tokenization but better full-form template accuracy. So the main driver is not simply "fewer subword pieces."

## Representation Geometry

ALLaM again shows severe mid-layer collapse:

```text
layers around 3-30: 90-95% variance mostly captured by one component
max activations around 160-1694 in sampled layers
```

This makes exact layer interpretation risky.

## Lab Decision

E08b is a useful negative/contrastive result. ALLaM does encode template information enough to beat n-grams on real full-form family split, but it is not competitive with Qwen3-8B or Fanar on transfer.

For the paper, ALLaM should be used to show model variation:

```text
the template signal is robust in nonce settings across models,
but real/nonce transfer quality differs substantially by model.
```
