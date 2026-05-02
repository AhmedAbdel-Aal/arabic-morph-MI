# Interpretation

Run: `E03`  
Model: `Qwen/Qwen3-1.7B-Base`  
Surface: `base`  
Pooling: `last`  
Purpose: rerun E02 with tokenization and representation diagnostics.

## Lab-Head Summary

E03 reproduces the E02 probe results, but the new diagnostics substantially improve the interpretation. The layer-0 weakness and early-layer spike are not mysterious anymore: most Arabic words in this dataset are split into multiple tokens, and the run uses last-token pooling in a causal decoder. At layer 0, the last token only has its own embedding; after the first transformer block, it can attend to earlier subword tokens and gather the whole word.

The strongest scientific result remains the template probes, especially nonce held-out roots. Root probes are still highly accurate, but nonce-root n-gram accuracy is 0.95, so root identity remains mostly surface-solvable.

## Probe Summary

| Probe | Target | Peak Layer | Normalized Depth | Probe Acc. | Control Acc. | Selectivity | N-Gram Acc. | Chance |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `real_templates_random` | template | 1 | 0.036 | 0.808 | 0.000 | 0.808 | 0.654 | 0.077 |
| `nonce_templates_random` | template | 2 | 0.071 | 0.950 | 0.150 | 0.800 | 0.300 | 0.200 |
| `nonce_templates_heldout_roots` | template | 3 | 0.107 | 1.000 | 0.150 | 0.850 | 0.600 | 0.200 |
| `train_real_test_nonce_overlap` | template | 2 | 0.071 | 0.710 | 0.260 | 0.450 | 0.580 | 0.200 |
| `train_nonce_test_real_overlap` | template | 4 | 0.143 | 0.880 | 0.300 | 0.580 | 0.780 | 0.200 |
| `real_roots_random` | root | 5 | 0.179 | 0.524 | 0.000 | 0.524 | 0.095 | 0.048 |
| `nonce_roots_random` | root | 2 | 0.071 | 1.000 | 0.050 | 0.950 | 0.950 | 0.050 |
| `nonce_roots_heldout_templates` | root | 1 | 0.036 | 1.000 | 0.100 | 0.900 | 0.950 | 0.050 |

## Tokenization Finding

The dataset has 230 unique probed strings.

| Number of tokens | Count |
|---:|---:|
| 1 | 17 |
| 2 | 88 |
| 3 | 113 |
| 4 | 12 |

Most words are multi-token: 213 out of 230 strings have more than one token. This matters because the current representation is the last token representation.

For a causal decoder:

```text
Layer 0 last-token vector = final subword embedding only.
Layer 1+ last-token vector = final subword can attend to previous subwords.
```

So the low layer-0 accuracy followed by a sharp early spike is expected under this extraction setup. It likely reflects early subword aggregation rather than a sudden emergence of deep morphology.

This is clearest in root probing:

| Probe | Layer 0 | Early Peak |
|---|---:|---:|
| `nonce_roots_random` | 0.55 | 1.00 at layer 2 |
| `nonce_roots_heldout_templates` | 0.65 | 1.00 at layer 1 |

Layer 0 is not empty, but it is incomplete. The early transformer layers make the whole word/root much more linearly accessible.

## Token Count And Accuracy

At peak layers, token count does not explain failures in the strongest nonce probes:

- `nonce_templates_heldout_roots`: perfect across 2-, 3-, and 4-token test items.
- `nonce_roots_random`: perfect across 2-, 3-, and 4-token test items.
- `nonce_roots_heldout_templates`: perfect across 2-, 3-, and 4-token test items.

The transfer probes show more structure:

- `train_real_test_nonce_overlap`: 2-token items are weaker at 0.545; 4-token items are strongest at 0.917.
- `train_nonce_test_real_overlap`: 1-token items are weak at 0.455, while 2- and 3-token items are perfect.

This means token count alone is not the whole story. Token identity and template-specific segmentation matter too.

## Representation Geometry

The representation diagnostics show a major Qwen-specific geometry issue.

Layers 3 through 20 are dominated by extreme activation values and a near one-dimensional variance structure:

```text
layer 3 max_abs_activation: 12488
layer 3 effective dimensions for 90% variance: 1
layer 20 max_abs_activation: 12576
layer 20 effective dimensions for 90% variance: 1
```

This looks like an activation outlier or dimensional-collapse phenomenon. It means mid-layer probe behavior should be interpreted cautiously. A classifier can still work, but the geometry is dominated by an outlier direction.

The early peak is therefore even more important: the best morphology results occur before the extreme mid-layer collapse fully dominates the representation.

## Scientific Interpretation

The strongest claim after E03 is:

```text
Qwen3-1.7B makes Arabic template information linearly recoverable in early layers after subword aggregation.
```

The result is consistent with prior probing work where surface and morpho-orthographic features are often most accessible in lower layers. It is also consistent with work warning that final-subword extraction in decoder models can affect layerwise interpretations.

The result should not be framed as high-level abstract morphology yet. The current evidence points to early morpho-orthographic organization.

## What Checks Out

- E03 reproduces E02 exactly on probe metrics.
- Template probes beat n-grams and control tasks.
- Nonce held-out-root template probing remains the strongest result.
- Tokenization explains why layer 0 is weaker than layers 1-5.
- Diagnostics support the need for pooling ablations.

## What Needs Caution

- Last-token pooling is likely shaping the layer-0 result.
- Root identity is mostly surface-solvable in nonce data.
- Mid-layer Qwen representations show severe activation geometry issues.
- Real-root probing remains sparse and should stay diagnostic.

## Next Step

E04 is now essential. We need to compare:

```text
last pooling vs first pooling vs mean pooling
```

If first or mean pooling reduces the layer-0 weakness, then the original layer-0 result was partly an extraction artifact. If all pooling strategies show the same early-layer spike, then the effect is more likely a genuine early-layer organization phenomenon.
