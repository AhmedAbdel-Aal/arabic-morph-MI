# Interpretation

Run: `E06`  
Model: `Qwen/Qwen3-8B`  
Surface: `base`  
Pooling: `last`  
Real split: `item`  
Purpose: larger Qwen comparison against the Qwen3-1.7B base/last reference run E03.

## Lab-Head Summary

E06 is a strong positive scaling result. Qwen3-8B improves over Qwen3-1.7B on the most important base-form template probes, especially transfer.

The core result is:

```text
Qwen3-8B recovers Arabic template information from base forms very strongly,
including nonce held-out roots and real/nonce transfer.
```

The result is not just high absolute accuracy. It beats the word-label control and character n-gram baseline by large margins on the template tasks.

## E06 Results

| Probe | Target | Peak Layer | Probe Acc. | Control Acc. | Selectivity | N-Gram Acc. | Chance |
|---|---|---:|---:|---:|---:|---:|---:|
| `real_templates_random` | template | 5 | 0.962 | 0.077 | 0.885 | 0.654 | 0.077 |
| `nonce_templates_random` | template | 4 | 1.000 | 0.150 | 0.850 | 0.300 | 0.200 |
| `nonce_templates_heldout_roots` | template | 8 | 1.000 | 0.150 | 0.850 | 0.600 | 0.200 |
| `train_real_test_nonce_overlap` | template | 5 | 0.870 | 0.280 | 0.590 | 0.580 | 0.200 |
| `train_nonce_test_real_overlap` | template | 3 | 0.980 | 0.120 | 0.860 | 0.780 | 0.200 |
| `real_roots_random` | root | 5 | 0.619 | 0.000 | 0.619 | 0.095 | 0.048 |
| `nonce_roots_random` | root | 4 | 1.000 | 0.000 | 1.000 | 0.950 | 0.050 |
| `nonce_roots_heldout_templates` | root | 1 | 1.000 | 0.050 | 0.950 | 0.950 | 0.050 |

## Direct Comparison To E03

| Probe | E03 Qwen3-1.7B | E06 Qwen3-8B | Change |
|---|---:|---:|---:|
| `real_templates_random` | 0.808 | 0.962 | +0.154 |
| `nonce_templates_random` | 0.950 | 1.000 | +0.050 |
| `nonce_templates_heldout_roots` | 1.000 | 1.000 | 0.000 |
| `train_real_test_nonce_overlap` | 0.710 | 0.870 | +0.160 |
| `train_nonce_test_real_overlap` | 0.880 | 0.980 | +0.100 |
| `real_roots_random` | 0.524 | 0.619 | +0.095 |
| `nonce_roots_random` | 1.000 | 1.000 | 0.000 |
| `nonce_roots_heldout_templates` | 1.000 | 1.000 | 0.000 |

The scale effect is clearest in real-template random split and transfer. The nonce held-out-root task was already saturated in Qwen3-1.7B, so Qwen3-8B cannot improve there.

## What This Means

E06 supports a model-scale hypothesis within Qwen:

```text
larger Qwen exposes Arabic template information more robustly,
especially when crossing between real and nonce forms.
```

The strongest improvement is not the already-saturated nonce held-out-root result. It is transfer:

```text
train real -> test nonce: 0.710 -> 0.870
train nonce -> test real: 0.880 -> 0.980
```

This matters because transfer is closer to the paper's generalization question than a simple random split.

## Root Probes

Root probing improves slightly for real roots:

```text
E03 real roots: 0.524
E06 real roots: 0.619
```

But the root interpretation remains secondary. Nonce root probing is still surface-solvable because the n-gram baseline is 0.950. We should not turn this into an abstract-root claim.

## Layer Behavior

The strongest template signals appear early:

```text
real templates peak: layer 5
nonce random templates peak: layer 4
real -> nonce transfer peak: layer 5
nonce -> real transfer peak: layer 3
```

The important point is not the exact layer number. It is that template information becomes available early after last-token aggregation over subword pieces.

## Representation Geometry

Qwen3-8B still shows the same kind of activation geometry issue as Qwen3-1.7B:

```text
layers around 8-28: max activations around 13472-13920
90-95% variance captured by one component
```

So scaling within Qwen does not remove the representation-collapse/outlier concern. We should still avoid claims like "layer 8 is the morphology layer."

## Lab Decision

E06 strengthens the main claim. Qwen3-8B gives stronger base-form template evidence than Qwen3-1.7B, especially for transfer.

Next, compare with Arabic-centric models:

```text
E07: Fanar base/last
E08: ALLaM base/last
```

These will tell us whether the effect is Qwen-specific or model-general.
