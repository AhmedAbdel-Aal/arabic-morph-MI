# Representation Analysis Conclusions

This report is generated from saved pooled hidden states in `results/REP01_*`.

## Experiment 00: Layer-Wise Anisotropy

The explicit anisotropy analysis is in `00_anisotropy/ANISOTROPY.md`. The main question is whether hidden states are spread across many directions or collapse into a few dominant directions.

The headline result is sharp: Qwen3-1.7B, Qwen3-8B, and ALLaM have many collapsed layers, while Fanar has none under the current threshold. This is why Fanar's cosine and centroid geometry is easier to interpret, and why Qwen/ALLaM probe results need PC-removal and nuisance checks.

## Experiment 01: Geometry Metrics

Metrics:

- `top_pc_variance_ratio`: fraction of variance explained by the first principal component.
- `edim90_fraction`: fraction of available PCA rank needed to explain 90% variance.
- `effective_rank_fraction`: entropy-based effective rank divided by rank.
- `mean_pairwise_cosine`: average cosine similarity across word vectors.

### Base Geometry Summary

| Model | Max top-PC ratio | Min edim90 fraction | Mean edim90 fraction | Layers edim90 <= 2% |
|---|---:|---:|---:|---:|
| Qwen3-1.7B | 1.000 | 0.004 | 0.051 | 25 |
| Qwen3-8B | 1.000 | 0.004 | 0.103 | 29 |
| Fanar-1-9B | 0.423 | 0.313 | 0.564 | 0 |
| ALLaM-7B | 1.000 | 0.004 | 0.058 | 29 |

### Full Geometry Summary

| Model | Max top-PC ratio | Min edim90 fraction | Mean edim90 fraction | Layers edim90 <= 2% |
|---|---:|---:|---:|---:|
| Qwen3-1.7B | 1.000 | 0.002 | 0.039 | 22 |
| Qwen3-8B | 1.000 | 0.002 | 0.072 | 29 |
| Fanar-1-9B | 0.322 | 0.237 | 0.401 | 0 |
| ALLaM-7B | 1.000 | 0.002 | 0.046 | 29 |

## Experiment 02: Probe-Geometry Overlay

This joins the original layer-wise probe curves with anisotropy metrics. It is mainly a visual diagnostic: high probe accuracy should be read together with the layer's geometry, because a classifier can exploit dominant directions that may also encode token count or source/domain structure.

## Experiment 03: PC-Removal Robustness

The key test is whether peak template-probe accuracy survives after removing dominant PCA directions.

### Base: Real Templates

| Model | raw | remove 1 | remove 5 | remove 10 | remove10 - raw |
|---|---:|---:|---:|---:|---:|
| Qwen3-1.7B | 0.808 | 0.769 | 0.808 | 0.500 | -0.308 |
| Qwen3-8B | 0.962 | 0.923 | 0.731 | 0.692 | -0.269 |
| Fanar-1-9B | 0.885 | 0.885 | 0.769 | 0.615 | -0.269 |
| ALLaM-7B | 0.692 | 0.731 | 0.731 | 0.654 | -0.038 |

### Base: Nonce Held-Out Roots

| Model | raw | remove 1 | remove 5 | remove 10 | remove10 - raw |
|---|---:|---:|---:|---:|---:|
| Qwen3-1.7B | 1.000 | 1.000 | 1.000 | 1.000 | +0.000 |
| Qwen3-8B | 1.000 | 1.000 | 0.950 | 0.900 | -0.100 |
| Fanar-1-9B | 1.000 | 1.000 | 0.950 | 0.900 | -0.100 |
| ALLaM-7B | 1.000 | 1.000 | 1.000 | 1.000 | +0.000 |

### Full: Real Templates

| Model | raw | remove 1 | remove 5 | remove 10 | remove10 - raw |
|---|---:|---:|---:|---:|---:|
| Qwen3-1.7B | 0.903 | 0.875 | 0.778 | 0.597 | -0.306 |
| Qwen3-8B | 0.931 | 0.931 | 0.833 | 0.486 | -0.444 |
| Fanar-1-9B | 0.944 | 0.931 | 0.833 | 0.597 | -0.347 |
| ALLaM-7B | 0.806 | 0.806 | 0.736 | 0.625 | -0.181 |

### Full: Nonce -> Real

| Model | raw | remove 1 | remove 5 | remove 10 | remove10 - raw |
|---|---:|---:|---:|---:|---:|
| Qwen3-1.7B | 0.807 | 0.813 | 0.600 | 0.567 | -0.240 |
| Qwen3-8B | 0.907 | 0.887 | 0.740 | 0.567 | -0.340 |
| Fanar-1-9B | 0.860 | 0.847 | 0.733 | 0.547 | -0.313 |
| ALLaM-7B | 0.587 | 0.700 | 0.673 | 0.613 | +0.027 |

## Experiment 04: Variance Decomposition

This asks a simpler question than probing: how much of the raw representation variance is organized by template, by real-vs-nonce source, by affix status, and by token count.

### Base

| Model | max overlap-template eta2 | max source eta2 | max real-template eta2 | max affix eta2 | max source eta2 on PC1 | max token-count R2 on PC1 |
|---|---:|---:|---:|---:|---:|---:|
| Qwen3-1.7B | 0.113 | 0.158 | 0.287 | nan | 0.289 | 0.665 |
| Qwen3-8B | 0.118 | 0.160 | 0.282 | nan | 0.215 | 0.441 |
| Fanar-1-9B | 0.117 | 0.234 | 0.275 | nan | 0.762 | 0.555 |
| ALLaM-7B | 0.064 | 0.543 | 0.235 | nan | 0.461 | 0.768 |

### Full

| Model | max overlap-template eta2 | max source eta2 | max real-template eta2 | max affix eta2 | max source eta2 on PC1 | max token-count R2 on PC1 |
|---|---:|---:|---:|---:|---:|---:|
| Qwen3-1.7B | 0.099 | 0.068 | 0.189 | 0.081 | 0.139 | 0.223 |
| Qwen3-8B | 0.102 | 0.070 | 0.167 | 0.083 | 0.227 | 0.286 |
| Fanar-1-9B | 0.102 | 0.246 | 0.191 | 0.045 | 0.600 | 0.239 |
| ALLaM-7B | 0.065 | 0.226 | 0.179 | 0.073 | 0.379 | 0.761 |

## Experiment 05: Real/Nonce Template-Centroid Alignment

This avoids fitting a classifier. For each shared template, it compares the real-template centroid with the nonce-template centroid. A high nearest-template score means the geometry itself aligns real and nonce templates.

### Base

| Model | best centered margin | layer | best nearest-template accuracy | layer |
|---|---:|---:|---:|---:|
| Qwen3-1.7B | 0.316 | 1 | 0.800 | 1 |
| Qwen3-8B | 0.523 | 6 | 1.000 | 6 |
| Fanar-1-9B | 0.473 | 5 | 1.000 | 4 |
| ALLaM-7B | 0.123 | 32 | 0.700 | 1 |

### Full

| Model | best centered margin | layer | best nearest-template accuracy | layer |
|---|---:|---:|---:|---:|
| Qwen3-1.7B | 0.317 | 28 | 0.700 | 1 |
| Qwen3-8B | 0.511 | 4 | 0.900 | 4 |
| Fanar-1-9B | 0.455 | 5 | 1.000 | 4 |
| ALLaM-7B | 0.122 | 1 | 0.600 | 3 |

## Experiment 06: Affix Invariance

This uses only full-surface real words. It checks whether a base word is closer to its own affixed variants than to other affixed words with the same template.

| Model | within-family cosine at best family layer | best family margin | layer | best template margin among affixed forms | layer |
|---|---:|---:|---:|---:|---:|
| Qwen3-1.7B | 0.544 | 0.475 | 1 | 0.146 | 28 |
| Qwen3-8B | 0.540 | 0.454 | 2 | 0.130 | 4 |
| Fanar-1-9B | 0.604 | 0.528 | 9 | 0.138 | 28 |
| ALLaM-7B | 0.465 | 0.379 | 31 | 0.142 | 4 |

## Experiment 07: Layer Concordance

This joins the probe curves, centroid alignment, and nuisance/domain metrics layer by layer. The `best balanced` layer is a triage heuristic, not a statistical test: it rewards transfer and centroid alignment while penalizing real-vs-nonce source separation and token-count dominance.

### Base

| Model | layer | transfer mean | centroid nearest | centroid margin | source eta2 | token-count R2 on PC1 |
|---|---:|---:|---:|---:|---:|---:|
| Qwen3-1.7B | 1 | 0.710 | 0.800 | 0.316 | 0.029 | 0.665 |
| Qwen3-8B | 6 | 0.855 | 1.000 | 0.523 | 0.033 | 0.390 |
| Fanar-1-9B | 5 | 0.880 | 1.000 | 0.473 | 0.029 | 0.234 |
| ALLaM-7B | 1 | 0.495 | 0.700 | 0.111 | 0.047 | 0.768 |

### Full

| Model | layer | transfer mean | centroid nearest | centroid margin | source eta2 | token-count R2 on PC1 |
|---|---:|---:|---:|---:|---:|---:|
| Qwen3-1.7B | 1 | 0.592 | 0.700 | 0.232 | 0.031 | 0.117 |
| Qwen3-8B | 6 | 0.888 | 0.900 | 0.499 | 0.037 | 0.000 |
| Fanar-1-9B | 5 | 0.808 | 1.000 | 0.455 | 0.032 | 0.079 |
| ALLaM-7B | 0 | 0.373 | 0.500 | 0.106 | 0.021 | 0.162 |

## Scientific Read

The representation evidence is not just another probe result. It separates three effects: morphology signal, real-vs-nonce/domain separation, and global representation geometry.

1. Qwen and ALLaM have severe dominant-direction geometry, while Fanar is much broader. This makes raw cosine and raw PCA plots dangerous unless centered or stress-tested.
2. Template probing survives on nonce held-out roots even after removing top PCs. That supports a surface/template-shape interpretation for nonce, not yet a strong claim about abstract morphology.
3. Real and transfer probes often lose accuracy after removing top PCs. This does not mean the result is fake; it means useful template information is partly carried by high-variance directions.
4. ALLaM is the exception: removing a small number of PCs can improve real/nonce transfer. Its dominant directions look more like nuisance/domain structure than useful morphology structure.
5. Qwen3-8B and Fanar have the cleanest real/nonce template alignment. Their centroid-nearest scores reach 0.9-1.0, which means the geometry itself often maps real and nonce examples of the same template together without training a classifier.
6. ALLaM remains the weak case. It can probe template labels, but the centroid alignment is poor and source/token-count effects are large. I would not use ALLaM as evidence for abstract template representations yet.
7. Affixation does not destroy family identity: base forms are closer to their own affixed variants than to other forms. However, this mostly says lexical-family information survives affixation; it is not by itself proof of template abstraction.

## Files

- `00_anisotropy/ANISOTROPY.md`
- `00_anisotropy/anisotropy_summary.csv`
- `00_anisotropy/anisotropy_dashboard.png`
- `01_geometry/geometry_metrics.csv`
- `02_probe_geometry/probe_geometry_by_layer.csv`
- `03_pc_removal/pc_removal_probe_summary.csv`
- `04_variance_decomposition/variance_decomposition.csv`
- `04_variance_decomposition/top_pc_label_effects.csv`
- `05_centroid_alignment/template_centroid_alignment.csv`
- `06_affix_invariance/affix_invariance.csv`
- `07_layer_concordance/layer_concordance.csv`
- `07_layer_concordance/best_layers_by_run.csv`
