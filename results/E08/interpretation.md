# Interpretation

Run: `E08`  
Model: `humain-ai/ALLaM-7B-Instruct-preview`  
Surface: `base`  
Pooling: `last`  
Real split: `item`  
Purpose: Arabic-centric ALLaM base-form comparison.

## Lab-Head Summary

E08 is a mixed result. ALLaM performs strongly on controlled nonce template tasks but weakly on real-template and transfer tasks.

The key split:

```text
nonce held-out roots: 1.000 vs n-gram 0.600
real templates:       0.692 vs n-gram 0.654
real -> nonce:        0.630 vs n-gram 0.580
nonce -> real:        0.580 vs n-gram 0.780
```

This means ALLaM can expose template information in the controlled nonce setting, but it does not bridge real and nonce morphology well. Its `nonce -> real` transfer is below the n-gram baseline, which is a serious weakness.

## Results

| Probe | Target | Peak Layer | Probe Acc. | Control Acc. | Selectivity | N-Gram Acc. | Chance |
|---|---|---:|---:|---:|---:|---:|---:|
| `real_templates_random` | template | 13 | 0.692 | 0.038 | 0.654 | 0.654 | 0.077 |
| `nonce_templates_random` | template | 4 | 0.950 | 0.100 | 0.850 | 0.300 | 0.200 |
| `nonce_templates_heldout_roots` | template | 4 | 1.000 | 0.100 | 0.900 | 0.600 | 0.200 |
| `train_real_test_nonce_overlap` | template | 4 | 0.630 | 0.170 | 0.460 | 0.580 | 0.200 |
| `train_nonce_test_real_overlap` | template | 1 | 0.580 | 0.120 | 0.460 | 0.780 | 0.200 |
| `real_roots_random` | root | 2 | 0.381 | 0.000 | 0.381 | 0.095 | 0.048 |
| `nonce_roots_random` | root | 4 | 1.000 | 0.000 | 1.000 | 0.950 | 0.050 |
| `nonce_roots_heldout_templates` | root | 4 | 1.000 | 0.100 | 0.900 | 0.950 | 0.050 |

## Comparison To Other Base Runs

| Probe | Qwen3-1.7B E03 | Qwen3-8B E06 | Fanar E07 | ALLaM E08 |
|---|---:|---:|---:|---:|
| `real_templates_random` | 0.808 | 0.962 | 0.885 | 0.692 |
| `nonce_templates_random` | 0.950 | 1.000 | 0.950 | 0.950 |
| `nonce_templates_heldout_roots` | 1.000 | 1.000 | 1.000 | 1.000 |
| `train_real_test_nonce_overlap` | 0.710 | 0.870 | 0.820 | 0.630 |
| `train_nonce_test_real_overlap` | 0.880 | 0.980 | 0.940 | 0.580 |

ALLaM matches the other models on nonce held-out-root templates, but it is clearly weaker on real and transfer probes. This is a major cross-model finding: Arabic-centric labeling alone does not guarantee stronger morphology representations under this probe.

## Tokenization

ALLaM tokenizes the dataset much less finely:

```text
mean tokens: 1.90
71 / 230 texts are one token
```

This is the opposite of Fanar. But fewer tokens do not translate into better morphology probing. That tells us tokenization length alone is not enough to explain performance.

## Representation Geometry

ALLaM has a severe geometry issue:

```text
from around layer 3 onward, 90-95% variance collapses into one component
max activations around 160-1694 in sampled layers
```

This resembles the Qwen collapse pattern more than Fanar's clean geometry, though the scale of activation outliers is different.

## Lab Decision

E08 is scientifically useful because it is a counterexample to a simplistic claim:

```text
Arabic-centric model = better Arabic morphology representation
```

ALLaM is strong on nonce template recognition but weak on real/nonce transfer. In the paper, this should be framed as model-specific variation, not a failure of the study.
