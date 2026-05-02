# Interpretation

Run: `E04a`  
Model: `Qwen/Qwen3-1.7B-Base`  
Surface: `base`  
Pooling: `first`  
Purpose: first-subword pooling ablation against E03 last-token pooling.

## Lab-Head Summary

E04a is a decisive ablation. First-subword pooling performs much worse than last-token pooling for nearly every important morphology probe. This strongly supports the interpretation that the successful E03 last-token results depend on the causal decoder's ability to aggregate information across the whole word by the early transformer layers.

The result does **not** mean the E03 result was invalid. It means E03 was measuring a composed word representation at the final subword. E04a shows that the first subword alone is usually a poor substitute for the full word representation in this setup.

## E04a Results

| Probe | Target | Peak Layer | Probe Acc. | Control Acc. | Selectivity | N-Gram Acc. | Chance |
|---|---|---:|---:|---:|---:|---:|---:|
| `real_templates_random` | template | 0 | 0.385 | 0.038 | 0.346 | 0.654 | 0.077 |
| `nonce_templates_random` | template | 0 | 0.400 | 0.100 | 0.300 | 0.300 | 0.200 |
| `nonce_templates_heldout_roots` | template | 0 | 0.650 | 0.200 | 0.450 | 0.600 | 0.200 |
| `train_real_test_nonce_overlap` | template | 0 | 0.580 | 0.210 | 0.370 | 0.580 | 0.200 |
| `train_nonce_test_real_overlap` | template | 4 | 0.720 | 0.160 | 0.560 | 0.780 | 0.200 |
| `real_roots_random` | root | 2 | 0.476 | 0.048 | 0.429 | 0.095 | 0.048 |
| `nonce_roots_random` | root | 3 | 0.750 | 0.000 | 0.750 | 0.950 | 0.050 |
| `nonce_roots_heldout_templates` | root | 2 | 0.100 | 0.000 | 0.100 | 0.950 | 0.050 |

## Direct Comparison To E03

| Probe | E03 Last Pooling | E04a First Pooling | Change |
|---|---:|---:|---:|
| `real_templates_random` | 0.808 | 0.385 | -0.423 |
| `nonce_templates_random` | 0.950 | 0.400 | -0.550 |
| `nonce_templates_heldout_roots` | 1.000 | 0.650 | -0.350 |
| `train_real_test_nonce_overlap` | 0.710 | 0.580 | -0.130 |
| `train_nonce_test_real_overlap` | 0.880 | 0.720 | -0.160 |
| `real_roots_random` | 0.524 | 0.476 | -0.048 |
| `nonce_roots_random` | 1.000 | 0.750 | -0.250 |
| `nonce_roots_heldout_templates` | 1.000 | 0.100 | -0.900 |

The largest collapse is `nonce_roots_heldout_templates`: last-token pooling was perfect, while first-subword pooling is near chance. This is exactly the kind of pattern we would expect if last-token pooling is assembling root information from across subword pieces, while first-subword pooling only captures the beginning of the word.

## What This Means For Layer 0

E03 showed weak layer-0 accuracy followed by a sharp early-layer spike. E04a clarifies that this is not simply because "the model already knows morphology at embeddings." If we use the first subword instead of the last subword, the probes are much weaker and often peak at layer 0 without meaningful later improvement.

For decoder-only models, the final subword has a privileged role: after one or more transformer layers, it can attend to all earlier subwords in the word. The first subword cannot attend to later subwords. Therefore:

```text
last pooling = potentially whole-word representation
first pooling = partial prefix representation
```

This is especially important for Arabic roots, because root consonants are distributed through the word. A first subword often does not contain the whole root.

## Template Probes

Template probing gets much weaker under first pooling:

- real templates drop from 0.808 to 0.385
- nonce random templates drop from 0.950 to 0.400
- nonce held-out-root templates drop from 1.000 to 0.650

The template signal is not gone, but it is much less linearly accessible. This supports the view that the strong E03 template results use composed word-level information rather than isolated prefix/subword information.

## Root Probes

Root probing is the clearest demonstration. `nonce_roots_heldout_templates` collapses from 1.000 to 0.100. Since the n-gram baseline is still 0.950, the first-subword representation is failing to expose root identity even though the full surface string contains it.

This is a useful result: it shows that "the characters contain the root" is not enough. The specific model representation we extract must actually have access to the relevant characters. First-subword pooling often does not.

## Token Count Pattern

At the E04a peak:

- `nonce_roots_heldout_templates` is 0.083 on 3-token items and 0.000 on 4-token items.
- `nonce_roots_random` is better on 3-token items than 4-token items.

This is consistent with first-subword pooling losing information as more of the word lies outside the first token.

## Representation Geometry

The same Qwen geometry issue appears in E04a:

```text
layers 3-20: 90-95% variance captured by one component
max activations around 12824-12912
```

This confirms that the activation-outlier/dimensional-collapse issue is not specific to last-token pooling. It is a model/layer geometry issue.

## Scientific Interpretation

E04a strengthens, rather than weakens, the E03 story:

```text
The strong early morphology signal appears when the extracted vector can compose over the word's subword pieces.
```

The correct next framing is not "last-token pooling is an artifact." The better framing is:

```text
For decoder-only models, final-subword pooling is a reasonable word representation because it can aggregate previous subwords. First-subword pooling is a negative control showing that partial subword representations are insufficient.
```

## Next Step

Run E04b with mean pooling. Mean pooling is the important middle case:

- If mean pooling resembles last pooling, the result is robust to word-level pooling choice.
- If mean pooling resembles first pooling, the last-token result depends strongly on decoder-final-token aggregation.
- If mean pooling is between them, we can report a graded pooling effect.
