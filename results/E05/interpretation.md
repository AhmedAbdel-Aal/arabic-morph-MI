# Interpretation

Run: `E05`  
Model: `Qwen/Qwen3-1.7B-Base`  
Surface: `full`  
Pooling: `last`  
Purpose: affixed-form stress test against E03 base-form last-token pooling.

## Lab-Head Summary

E05 is useful, but it is not a clean win. It shows that the probe can still recover template and root labels when real Arabic forms include prefixes and suffixes. However, the real-form random splits become much less diagnostic because affixed variants of the same base/root-template family can appear across train and test.

The most important result is the transfer setting:

```text
train real full forms -> test nonce base forms: 0.800
```

This is stronger than E03's base-form result of 0.710 and clearly above the n-gram baseline of 0.590. That supports the claim that real full forms still carry a recoverable template signal that transfers to nonce words.

The reverse transfer is weaker:

```text
train nonce base forms -> test real full forms: 0.807
```

This is above control and chance, but only slightly above the n-gram baseline of 0.753. So the model has some generalization to affixed real forms, but the margin over surface character information is not large.

## Important Design Caveat

In the current code, `surface=full` applies to the real subset only. The nonce subset is still loaded as base forms:

```text
real: full forms
nonce: base forms
```

So E05 is not a full nonce-affix experiment. The nonce-only results are effectively the same base-form tests as E03. The real and real-to-nonce / nonce-to-real transfer tasks are the parts that matter here.

## E05 Results

| Probe | Target | Peak Layer | Probe Acc. | Control Acc. | Selectivity | N-Gram Acc. | Chance |
|---|---|---:|---:|---:|---:|---:|---:|
| `real_templates_random` | template | 5 | 0.962 | 0.077 | 0.885 | 1.000 | 0.077 |
| `nonce_templates_random` | template | 2 | 0.950 | 0.150 | 0.800 | 0.300 | 0.200 |
| `nonce_templates_heldout_roots` | template | 3 | 1.000 | 0.150 | 0.850 | 0.600 | 0.200 |
| `train_real_test_nonce_overlap` | template | 3 | 0.800 | 0.120 | 0.680 | 0.590 | 0.200 |
| `train_nonce_test_real_overlap` | template | 4 | 0.807 | 0.233 | 0.573 | 0.753 | 0.200 |
| `real_roots_random` | root | 6 | 0.877 | 0.009 | 0.868 | 0.642 | 0.009 |
| `nonce_roots_random` | root | 2 | 1.000 | 0.050 | 0.950 | 0.950 | 0.050 |
| `nonce_roots_heldout_templates` | root | 1 | 1.000 | 0.100 | 0.900 | 0.950 | 0.050 |

## Direct Comparison To E03

| Probe | E03 Base Last | E05 Full Last | Change |
|---|---:|---:|---:|
| `real_templates_random` | 0.808 | 0.962 | +0.154 |
| `nonce_templates_random` | 0.950 | 0.950 | 0.000 |
| `nonce_templates_heldout_roots` | 1.000 | 1.000 | 0.000 |
| `train_real_test_nonce_overlap` | 0.710 | 0.800 | +0.090 |
| `train_nonce_test_real_overlap` | 0.880 | 0.807 | -0.073 |
| `real_roots_random` | 0.524 | 0.877 | +0.353 |
| `nonce_roots_random` | 1.000 | 1.000 | 0.000 |
| `nonce_roots_heldout_templates` | 1.000 | 1.000 | 0.000 |

The unchanged nonce numbers are expected because nonce forms did not become affixed in E05.

## Template Probes

`real_templates_random` looks excellent at 0.962, but the n-gram baseline is 1.000. This means the surface strings are enough to solve the task in this split. I would not use this result as central evidence for learned morphology.

The better evidence is transfer:

- `train_real_test_nonce_overlap`: 0.800 vs 0.590 n-gram baseline.
- `train_nonce_test_real_overlap`: 0.807 vs 0.753 n-gram baseline.

The first result is strong. Training on real full forms and testing on nonce base forms works well. The second result is weaker but still positive. Training on nonce base forms and testing on real full forms survives affixes, but the model's margin over n-grams is small.

My read: affixes do not destroy the template signal, but the current real-full setup makes it hard to separate genuine morphological abstraction from surface regularities.

## Root Probes

`real_roots_random` jumps from 0.524 in E03 to 0.877 in E05. This looks dramatic, but it is not a clean abstract-root result. In the full real data, each root-pattern pair appears as multiple surface variants. The split can train on one variant and test on another related variant. That makes the root probe much easier.

The n-gram baseline also rises from 0.095 in E03 to 0.642 in E05, confirming that surface characters carry much more of the answer in this setting.

The nonce root probes are unchanged and remain surface-solvable:

```text
probe = 1.000
n-gram = 0.950
```

So root probing remains diagnostic for pooling and token access, but it is not yet strong evidence for abstract root representation.

## Layer Behavior

The full-form transfer probes peak early:

- real -> nonce transfer peaks at layer 3.
- nonce -> real transfer peaks at layer 4.
- real root probing peaks around layers 6-8.

This fits the earlier pooling story. Full forms are longer: E05 has 490 unique strings, with a mean of 2.87 tokens and up to 5 tokens. With last-token pooling, layer 0 often sees only the final subword or suffix-like material. After a few layers, the final token can attend backward and collect more of the word.

But we should not overinterpret exact peak layers. The Qwen representation geometry issue remains:

```text
layers 3-20: 90-95% variance mostly captured by one component
max activations around 12488-12600
```

The safe claim is early availability of the signal, not a precise layer-localization story.

## What Checks Out

E05 supports these claims:

```text
1. Template information remains recoverable when real forms include affixes.
2. Real full forms can train a probe that transfers to nonce base forms.
3. Last-token pooling still produces a useful word representation for longer Arabic forms after early attention layers.
```

## What Does Not Check Out Yet

E05 does not yet support these stronger claims:

```text
1. The model has abstract affix-invariant morphology.
2. Real random-split results are clean evidence of morphology.
3. Root probing on this dataset proves abstract root representation.
```

The main reason is split leakage through affixed variants and high character n-gram baselines.

## Lab Decision

Keep E05 as a useful stress test, but do not make it the central evidence. The central evidence is still template generalization, especially nonce held-out roots and real/nonce transfer, with E04a/E04b establishing the pooling story.

Before scaling E05 to larger models, we should add a stricter full-form experiment:

```text
E05b: grouped split by base/root-template family, so affixed variants of the same family cannot appear in both train and test.
```

If we want a true affixed nonce test, we also need nonce affixed variants. Current nonce rows are base-only.
