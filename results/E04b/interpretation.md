# Interpretation

Run: `E04b`  
Model: `Qwen/Qwen3-1.7B-Base`  
Surface: `base`  
Pooling: `mean`  
Purpose: mean-pooling ablation against E03 last-token pooling and E04a first-token pooling.

## Lab-Head Summary

E04b is a strong result. Mean pooling restores most of the signal that collapsed under first-token pooling. This means the central pooling story is now clearer:

```text
first pooling fails because it often sees only part of the word
last pooling succeeds because the final token can aggregate earlier tokens in a causal decoder
mean pooling succeeds because it directly averages all token pieces
```

So the E03 result is not a fragile last-token-only artifact. The stronger interpretation is that Arabic morphological information is linearly accessible when the extracted vector has access to the whole surface form.

But there is an important caveat: mean pooling at layer 0 already has access to all subword pieces because we average them outside the model. Therefore high layer-0 accuracy under mean pooling is not evidence that the transformer has composed the word internally. It is evidence that whole-word subword information is sufficient for the probe.

## E04b Results

| Probe | Target | Peak Layer | Probe Acc. | Control Acc. | Selectivity | N-Gram Acc. | Chance |
|---|---|---:|---:|---:|---:|---:|---:|
| `real_templates_random` | template | 0 | 0.692 | 0.038 | 0.654 | 0.654 | 0.077 |
| `nonce_templates_random` | template | 21 | 0.850 | 0.100 | 0.750 | 0.300 | 0.200 |
| `nonce_templates_heldout_roots` | template | 2 | 0.950 | 0.100 | 0.850 | 0.600 | 0.200 |
| `train_real_test_nonce_overlap` | template | 5 | 0.640 | 0.150 | 0.490 | 0.580 | 0.200 |
| `train_nonce_test_real_overlap` | template | 1 | 0.840 | 0.220 | 0.620 | 0.780 | 0.200 |
| `real_roots_random` | root | 1 | 0.429 | 0.048 | 0.381 | 0.095 | 0.048 |
| `nonce_roots_random` | root | 0 | 1.000 | 0.100 | 0.900 | 0.950 | 0.050 |
| `nonce_roots_heldout_templates` | root | 0 | 0.950 | 0.050 | 0.900 | 0.950 | 0.050 |

## Direct Comparison

| Probe | E03 Last | E04a First | E04b Mean |
|---|---:|---:|---:|
| `real_templates_random` | 0.808 | 0.385 | 0.692 |
| `nonce_templates_random` | 0.950 | 0.400 | 0.850 |
| `nonce_templates_heldout_roots` | 1.000 | 0.650 | 0.950 |
| `train_real_test_nonce_overlap` | 0.710 | 0.580 | 0.640 |
| `train_nonce_test_real_overlap` | 0.880 | 0.720 | 0.840 |
| `real_roots_random` | 0.524 | 0.476 | 0.429 |
| `nonce_roots_random` | 1.000 | 0.750 | 1.000 |
| `nonce_roots_heldout_templates` | 1.000 | 0.100 | 0.950 |

Mean pooling is much closer to last pooling than first pooling. The most important case is `nonce_roots_heldout_templates`: first pooling was near chance at 0.100, while mean pooling returns to 0.950. That is the cleanest evidence that the first-pooling collapse was caused by missing later subword pieces.

## What This Means

E04b supports a whole-word-access hypothesis:

```text
Arabic root and template information becomes probe-accessible when the representation includes all subword pieces of the word.
```

This is not the same as proving abstract morphology. It means the representation has enough information for a linear classifier to recover the labels. For template probing, that is encouraging because the model beats the n-gram baseline in nonce and held-out-root settings. For root probing, the interpretation is weaker because the nonce root task is almost fully surface-solvable: the n-gram baseline is already 0.950.

## Layer-0 Interpretation

Mean pooling changes how we should read layer 0.

With last pooling in E03, layer 0 was weak because the final subword embedding only represented the final subword. After attention layers, the final subword could attend backward and gather earlier subwords.

With first pooling in E04a, the vector stayed weak because the first subword cannot attend forward to later subwords in a causal decoder.

With mean pooling in E04b, layer 0 can be strong because the experimenter averages all subword embeddings before any attention has happened. This is useful as a whole-word extraction baseline, but it is not evidence of transformer composition.

So if the question is:

```text
Can a whole-word vector expose morphology?
```

then E04b is positive.

If the question is:

```text
At which transformer layer does the model compose morphology?
```

then E03 last pooling is more informative than E04b mean pooling.

## Template Probes

The template results are mostly positive:

- `nonce_templates_heldout_roots` reaches 0.950 against 0.600 n-gram accuracy.
- `nonce_templates_random` reaches 0.850 against 0.300 n-gram accuracy.
- `train_nonce_test_real_overlap` reaches 0.840 against 0.780 n-gram accuracy.
- `train_real_test_nonce_overlap` reaches 0.640 against 0.580 n-gram accuracy.

The strongest scientific evidence remains nonce template generalization, especially held-out roots. The real-template random split is less clean because the n-gram baseline is also high at 0.654 and the probe is only slightly above it.

## Root Probes

Root probing remains scientifically mixed:

- `real_roots_random` is underpowered: 45 items across 21 labels.
- `nonce_roots_random` is perfect, but n-gram accuracy is already 0.950.
- `nonce_roots_heldout_templates` is 0.950, but n-gram accuracy is also 0.950.

This does not mean root probing is useless. It means this dataset is not enough to claim abstract root representation from root accuracy alone. The root labels are too directly recoverable from the surface form.

The value of root probing in E04b is instead diagnostic: mean pooling recovers the root signal that first pooling lost.

## What Does Not Fully Check Out

The peak for `nonce_templates_random` is at layer 21. I would not interpret that as "template information emerges late." The same run shows strong performance much earlier, and the representation diagnostics still show severe activation geometry problems:

```text
layers 3-21: 90-95% variance captured by one component
max activations around 12488-12600
```

So late peaks inside this collapsed region should be treated as unstable. The safer claim is that the template signal is available under mean pooling, not that layer 21 has special morphological status.

## Lab Decision

Use E03 last pooling as the primary decoder-only probing setup. Use E04a and E04b as required controls:

```text
E04a shows partial-token extraction is insufficient.
E04b shows whole-word extraction restores the signal.
E03 shows the final token in a causal decoder can become a useful word representation after attention.
```

The next scientific step is not another pooling ablation. It is E05: run the same setup on `surface=full` to test whether the signal survives affixed forms.
