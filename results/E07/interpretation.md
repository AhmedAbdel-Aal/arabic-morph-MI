# Interpretation

Run: `E07`  
Model: `QCRI/Fanar-1-9B`  
Surface: `base`  
Pooling: `last`  
Real split: `item`  
Purpose: Arabic-centric Fanar base-form comparison.

## Lab-Head Summary

E07 is a strong positive result. Fanar recovers Arabic template information from base forms across real, nonce, and transfer probes. It is clearly above controls and n-gram baselines on the central template tasks.

The most important result is that Fanar behaves like a serious morphology model, not merely a surface baseline:

```text
nonce held-out roots: 1.000 vs n-gram 0.600
real -> nonce:       0.820 vs n-gram 0.580
nonce -> real:       0.940 vs n-gram 0.780
```

Compared with Qwen3-8B, Fanar is slightly weaker on base-form template transfer. Compared with Qwen3-1.7B, it is stronger on transfer and real root probing.

## Results

| Probe | Target | Peak Layer | Probe Acc. | Control Acc. | Selectivity | N-Gram Acc. | Chance |
|---|---|---:|---:|---:|---:|---:|---:|
| `real_templates_random` | template | 5 | 0.885 | 0.077 | 0.808 | 0.654 | 0.077 |
| `nonce_templates_random` | template | 4 | 0.950 | 0.150 | 0.800 | 0.300 | 0.200 |
| `nonce_templates_heldout_roots` | template | 3 | 1.000 | 0.100 | 0.900 | 0.600 | 0.200 |
| `train_real_test_nonce_overlap` | template | 5 | 0.820 | 0.180 | 0.640 | 0.580 | 0.200 |
| `train_nonce_test_real_overlap` | template | 5 | 0.940 | 0.300 | 0.640 | 0.780 | 0.200 |
| `real_roots_random` | root | 6 | 0.714 | 0.000 | 0.714 | 0.095 | 0.048 |
| `nonce_roots_random` | root | 4 | 1.000 | 0.000 | 1.000 | 0.950 | 0.050 |
| `nonce_roots_heldout_templates` | root | 2 | 1.000 | 0.050 | 0.950 | 0.950 | 0.050 |

## Comparison To Qwen

| Probe | Qwen3-1.7B E03 | Qwen3-8B E06 | Fanar E07 |
|---|---:|---:|---:|
| `real_templates_random` | 0.808 | 0.962 | 0.885 |
| `nonce_templates_random` | 0.950 | 1.000 | 0.950 |
| `nonce_templates_heldout_roots` | 1.000 | 1.000 | 1.000 |
| `train_real_test_nonce_overlap` | 0.710 | 0.870 | 0.820 |
| `train_nonce_test_real_overlap` | 0.880 | 0.980 | 0.940 |
| `real_roots_random` | 0.524 | 0.619 | 0.714 |

Fanar sits between Qwen3-1.7B and Qwen3-8B on most template probes. It has the strongest real-root number, but that task is small and should remain secondary.

## Tokenization

Fanar tokenizes these words more finely than Qwen:

```text
Fanar base: mean 3.64 tokens, min 2, max 5
Qwen base:  mean 2.52 tokens, min 1, max 4
```

Despite more subword fragmentation, last-token pooling still works. That supports the decision to keep last-token pooling as the default word representation.

## Representation Geometry

Fanar has much cleaner representation geometry than Qwen:

```text
effective dimensions remain high across layers
no Qwen-style collapse to one component
max activations are moderate, roughly 25-240 in sampled layers
```

This is important. Fanar may give more interpretable layer curves than Qwen, where mid-layer outliers dominate the representation diagnostics.

## Lab Decision

E07 supports the paper's model-general claim. Arabic template information is not just a Qwen artifact. Fanar exposes the same template signal, with strong nonce and transfer performance and cleaner geometry.

The next question is whether Fanar's advantage becomes clearer in full affixed forms, which E07b tests.
