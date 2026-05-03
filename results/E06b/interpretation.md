# Interpretation

Run: `E06b`  
Model: `Qwen/Qwen3-8B`  
Surface: `full`  
Pooling: `last`  
Real split: `family`  
Purpose: larger Qwen full-form robustness test against E05b.

## Lab-Head Summary

E06b is a strong full-form result. Qwen3-8B improves on the Qwen3-1.7B full/family run E05b while preserving the stricter grouped split:

```text
train_groups: 121
test_groups: 31
group_overlap: 0
```

The key result:

```text
real_templates_random: 0.931
n-gram baseline:       0.667
control:              0.069
```

So full real forms still expose template information under grouped splitting, and Qwen3-8B improves over Qwen3-1.7B.

## E06b Results

| Probe | Target | Split | Peak Layer | Probe Acc. | Control Acc. | Selectivity | N-Gram Acc. | Chance |
|---|---|---|---:|---:|---:|---:|---:|---:|
| `real_templates_random` | template | family | 6 | 0.931 | 0.069 | 0.861 | 0.667 | 0.077 |
| `nonce_templates_random` | template | item | 4 | 1.000 | 0.150 | 0.850 | 0.300 | 0.200 |
| `nonce_templates_heldout_roots` | template | held-out root | 8 | 1.000 | 0.150 | 0.850 | 0.600 | 0.200 |
| `train_real_test_nonce_overlap` | template | explicit | 6 | 0.890 | 0.180 | 0.710 | 0.590 | 0.200 |
| `train_nonce_test_real_overlap` | template | explicit | 5 | 0.907 | 0.253 | 0.653 | 0.753 | 0.200 |
| `nonce_roots_random` | root | item | 4 | 1.000 | 0.050 | 0.950 | 0.950 | 0.050 |
| `nonce_roots_heldout_templates` | root | held-out template | 1 | 1.000 | 0.000 | 1.000 | 0.950 | 0.050 |

`real_roots_random` was skipped because a clean grouped root split is not supported by the current real data.

## Direct Comparison To E05b

| Probe | E05b Qwen3-1.7B | E06b Qwen3-8B | Change |
|---|---:|---:|---:|
| `real_templates_random` | 0.903 | 0.931 | +0.028 |
| `nonce_templates_random` | 0.950 | 1.000 | +0.050 |
| `nonce_templates_heldout_roots` | 1.000 | 1.000 | 0.000 |
| `train_real_test_nonce_overlap` | 0.800 | 0.890 | +0.090 |
| `train_nonce_test_real_overlap` | 0.807 | 0.907 | +0.100 |
| `nonce_roots_random` | 1.000 | 1.000 | 0.000 |
| `nonce_roots_heldout_templates` | 1.000 | 1.000 | 0.000 |

The full-form scale effect is meaningful but not huge on real template random split. The clearer improvement is again transfer.

## What This Means

E06b strengthens the full-form robustness claim:

```text
Qwen3-8B recovers template information from affixed real forms
even when affixed sibling variants are grouped out of train/test leakage.
```

The n-gram baseline remains 0.667, while the model reaches 0.931. That gap is the important result.

## Full-Form Transfer

The strongest full-form improvement appears in transfer:

```text
train real full -> test nonce base:
E05b: 0.800
E06b: 0.890

train nonce base -> test real full:
E05b: 0.807
E06b: 0.907
```

This is important because transfer makes the result less like a closed-set classification artifact and more like evidence of generalizable template structure.

## Token Count

At peak layer for `real_templates_random`:

| Token Count | Test Items | Accuracy |
|---:|---:|---:|
| 1 | 2 | 0.500 |
| 2 | 18 | 0.944 |
| 3 | 42 | 0.929 |
| 4 | 9 | 1.000 |
| 5 | 1 | 1.000 |

There is no sign that 3-4 token full forms collapse under last pooling. The 1-token and 5-token groups are too small to interpret.

## Representation Geometry

The Qwen geometry issue persists:

```text
layers around 8-28: max activations around 13456-13904
90-95% variance mostly captured by one component
```

So Qwen3-8B is stronger behaviorally, but the layer-localization caution remains.

## Lab Decision

E06b should be the larger-Qwen full-form result. Together with E06, it shows that scaling Qwen from 1.7B to 8B strengthens template decodability, especially transfer, while preserving the main pattern from the smaller model.

Next step:

```text
run Fanar and ALLaM base/full-family
```

That is the key test for whether this is a general Arabic morphology representation story or a Qwen-family story.
