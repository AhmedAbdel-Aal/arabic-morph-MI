# Layer-Wise Anisotropy Analysis

This is the explicit anisotropy analysis we discussed. It is computed from saved pooled hidden states, using the geometry metrics in `rep_analysis/results/01_geometry/geometry_metrics.csv`.

## What Was Measured

- `pc1_anisotropy`: variance share of the first principal component. High values mean the representations are dominated by one direction.
- `edim90_fraction`: fraction of available rank needed to explain 90% variance. Low values mean the representation is effectively low-dimensional.
- `effective_rank_fraction`: entropy-based effective rank divided by rank. Low values mean variance is concentrated in few directions.
- `mean_pairwise_cosine`: average raw cosine similarity between examples. High values mean vectors occupy a narrow cone.

I mark a layer as `collapsed` when `pc1_anisotropy >= 0.90` or `edim90_fraction <= 0.02`.

## Summary

| Model | Surface | max PC1 | mean PC1 | min edim90 | mean edim90 | collapsed layers | first collapsed | last collapsed |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Qwen3-1.7B | base | 1.000 | 0.881 | 0.004 | 0.051 | 25 | 3 | 27 |
| Qwen3-8B | base | 1.000 | 0.822 | 0.004 | 0.103 | 29 | 7 | 35 |
| Fanar-1-9B | base | 0.423 | 0.105 | 0.313 | 0.564 | 0 |  |  |
| ALLaM-7B | base | 1.000 | 0.910 | 0.004 | 0.058 | 29 | 3 | 31 |
| Qwen3-1.7B | full | 1.000 | 0.857 | 0.002 | 0.039 | 22 | 3 | 24 |
| Qwen3-8B | full | 1.000 | 0.805 | 0.002 | 0.072 | 29 | 7 | 35 |
| Fanar-1-9B | full | 0.322 | 0.077 | 0.237 | 0.401 | 0 |  |  |
| ALLaM-7B | full | 1.000 | 0.908 | 0.002 | 0.046 | 29 | 3 | 31 |

## Interpretation

1. Qwen3-1.7B, Qwen3-8B, and ALLaM show severe anisotropy/collapse in many layers. In those layers, one principal direction can explain almost all variance and edim90 drops near zero.
2. Fanar is qualitatively different. It never reaches the collapse threshold in these runs; its variance remains distributed across many more directions.
3. This does not mean Fanar is automatically more morphological. It means Fanar's representation space is less dominated by a global common direction, so cosine/centroid analyses are easier to trust.
4. For Qwen and ALLaM, probe accuracy must be read together with PC-removal and nuisance analyses. A high probe score in a collapsed layer may reflect morphology, tokenization, source/domain structure, or a mixture.
5. The important contrast is therefore not just `which model probes best`; it is `which model has recoverable template information in layers whose geometry is not dominated by nuisance directions`.

## Files

- `anisotropy_by_layer.csv`: layer-wise metrics and collapse labels.
- `anisotropy_summary.csv`: model/surface summary table.
- `anisotropy_dashboard.png`: all anisotropy metrics in one figure.
- `pc1_anisotropy_by_layer.png`: PC1 variance share by layer.
- `edim90_fraction_by_layer.png`: effective dimensionality by layer.
- `effective_rank_fraction_by_layer.png`: entropy effective-rank by layer.
- `mean_pairwise_cosine_by_layer.png`: raw cone anisotropy by layer.
