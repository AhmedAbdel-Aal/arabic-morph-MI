# Interpretation

Run: `E05b`  
Model: `Qwen/Qwen3-1.7B-Base`  
Surface: `full`  
Pooling: `last`  
Real split: `family`  
Purpose: grouped full-form split to prevent affixed sibling leakage.

## Lab-Head Summary

E05b is a strong and important correction to E05. The grouped split did what it was supposed to do:

```text
train_groups: 121
test_groups: 31
group_overlap: 0
```

This means affixed variants of the same `(root, template, base_form)` family no longer appear in both train and test for the real-template random split.

The result is scientifically better than E05. Accuracy drops, as expected, but remains high:

```text
E05 real_templates_random:  0.962, n-gram 1.000
E05b real_templates_random: 0.903, n-gram 0.667
```

This is exactly the pattern we wanted. E05 looked too easy because the surface n-gram baseline solved the task perfectly. E05b removes the sibling leakage, and the model still substantially beats the n-gram baseline.

## E05b Results

| Probe | Target | Split | Peak Layer | Probe Acc. | Control Acc. | Selectivity | N-Gram Acc. | Chance |
|---|---|---|---:|---:|---:|---:|---:|---:|
| `real_templates_random` | template | family | 4 | 0.903 | 0.083 | 0.819 | 0.667 | 0.077 |
| `nonce_templates_random` | template | item | 2 | 0.950 | 0.150 | 0.800 | 0.300 | 0.200 |
| `nonce_templates_heldout_roots` | template | held-out root | 3 | 1.000 | 0.150 | 0.850 | 0.600 | 0.200 |
| `train_real_test_nonce_overlap` | template | explicit | 3 | 0.800 | 0.110 | 0.690 | 0.590 | 0.200 |
| `train_nonce_test_real_overlap` | template | explicit | 4 | 0.807 | 0.233 | 0.573 | 0.753 | 0.200 |
| `nonce_roots_random` | root | item | 2 | 1.000 | 0.050 | 0.950 | 0.950 | 0.050 |
| `nonce_roots_heldout_templates` | root | held-out template | 1 | 1.000 | 0.050 | 0.950 | 0.950 | 0.050 |

`real_roots_random` was skipped:

```text
Each label needs at least two family groups for a grouped split.
```

This is the correct behavior. Running a grouped real-root split when most root labels do not have independent families would either fail or reintroduce leakage.

## Direct Comparison To E05

| Probe | E05 Acc. | E05 N-Gram | E05b Acc. | E05b N-Gram | Interpretation |
|---|---:|---:|---:|---:|---|
| `real_templates_random` | 0.962 | 1.000 | 0.903 | 0.667 | The key correction; still strong after removing sibling leakage. |
| `nonce_templates_random` | 0.950 | 0.300 | 0.950 | 0.300 | Unchanged; nonce remains base-only. |
| `nonce_templates_heldout_roots` | 1.000 | 0.600 | 1.000 | 0.600 | Unchanged; nonce remains base-only. |
| `train_real_test_nonce_overlap` | 0.800 | 0.590 | 0.800 | 0.590 | Essentially unchanged; explicit train/test transfer was already separate. |
| `train_nonce_test_real_overlap` | 0.807 | 0.753 | 0.807 | 0.753 | Essentially unchanged. |
| `real_roots_random` | 0.877 | 0.642 | skipped | skipped | Correctly removed under grouped split. |

The only major intended change is `real_templates_random`, and it behaves exactly as a serious control should behave: the easy surface baseline collapses, but the model remains strong.

## What This Means

E05b strengthens the affixed-form story. E05 alone could not support much because its real random split was surface-solvable:

```text
E05 n-gram = 1.000
```

After grouped splitting:

```text
E05b n-gram = 0.667
E05b probe = 0.903
```

So the probe is not merely learning affixed sibling variants or shallow character n-grams. It is recovering template information from full real forms under a stricter split.

This does not prove full affix-invariant morphology yet, because the test examples are still real words and the dataset is small. But E05b is now a legitimate piece of evidence, unlike the E05 random split by itself.

## Layer Behavior

`real_templates_random` peaks at layer 4:

```text
layer 0: 0.444
layer 1: 0.667
layer 2: 0.736
layer 3: 0.778
layer 4: 0.903
```

This is consistent with the earlier last-pooling story. Full forms are often multi-token and may end in suffix-like material. At layer 0, the final subword sees only itself. By early layers, the final position can attend backward and gather more of the word.

Do not overinterpret layer 4 specifically. Qwen's activation geometry issue remains:

```text
layers 3-20: 90-95% variance mostly captured by one component
max activations around 12488-12600
```

The safe claim is early availability after causal aggregation, not a precise morphology layer.

## Token Count

At the peak layer for `real_templates_random`:

| Token Count | Test Items | Accuracy |
|---:|---:|---:|
| 1 | 2 | 1.000 |
| 2 | 18 | 1.000 |
| 3 | 42 | 0.857 |
| 4 | 9 | 0.889 |
| 5 | 1 | 1.000 |

There is no evidence that multi-token full forms collapse under last pooling. The 3-token and 4-token groups remain strong, though small group sizes mean we should not make fine-grained token-count claims.

## What Checks Out

E05b supports these claims:

```text
1. The E05 full-form result was partly inflated, but not entirely explained, by sibling leakage.
2. Full real forms still expose template information after grouping affixed variants by family.
3. The model beats both the word-label control and character n-gram baseline under the stricter full-form split.
```

## What Still Does Not Check Out

E05b still does not prove:

```text
1. abstract root representation
2. full affix-invariant morphology
3. generalization to affixed nonce forms
4. model-family generality
```

The nonce subset is still base-only. So E05b improves the real full-form test, but it does not replace the need for nonce affix augmentation if we want a true affix-invariance experiment.

## Lab Decision

E05b should replace E05 as the main full-form evidence. E05 remains useful historically because it motivated the grouped split, but E05b is the result we would cite.

The next step can now be model scaling for the clean base setup:

```text
E06: Qwen3-8B, surface=base, pooling=last
E07: Fanar, surface=base, pooling=last
E08: ALLaM, surface=base, pooling=last
```

E05c remains optional and requires new data, because nonce affixed forms are not present in the current dataset.
