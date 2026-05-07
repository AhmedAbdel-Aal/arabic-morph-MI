# Cross-Model Summary

Generated from saved `results.json`, `tokenization_diagnostics.json`, and `representation_diagnostics.json` files.

## Paper Contribution Framing

Alakeel et al. evaluate Arabic root-pattern morphology through prompt-based generation, and they note that some model differences may reflect instruction-following behavior rather than morphology alone. This study is complementary: it asks whether template information is recoverable from hidden word representations when no prompt is being followed and no output text is being parsed.

The probe result should still be stated carefully. It shows linear recoverability of template information, not a causal proof that the model uses this feature during generation.

Source paper: https://arxiv.org/pdf/2603.15773

## Base-Form Main Runs

| Run | Model | Real templates | Nonce held-out roots | Real -> nonce | Nonce -> real | Mean n-gram gap |
| --- | --- | --- | --- | --- | --- | --- |
| E03 | Qwen3-1.7B | 0.808 | 1.000 | 0.710 | 0.880 | 0.287 |
| E06 | Qwen3-8B | 0.962 | 1.000 | 0.870 | 0.980 | 0.380 |
| E07 | Fanar-1-9B | 0.885 | 1.000 | 0.820 | 0.940 | 0.336 |
| E08 | ALLaM-7B | 0.692 | 1.000 | 0.630 | 0.580 | 0.188 |

## Full-Form Family Runs

| Run | Model | Real templates | Real n-gram | Real -> nonce | Nonce -> real | Mean n-gram gap |
| --- | --- | --- | --- | --- | --- | --- |
| E05b | Qwen3-1.7B | 0.903 | 0.667 | 0.800 | 0.807 | 0.310 |
| E06b | Qwen3-8B | 0.931 | 0.667 | 0.890 | 0.907 | 0.363 |
| E07b | Fanar-1-9B | 0.944 | 0.667 | 0.770 | 0.860 | 0.323 |
| E08b | ALLaM-7B | 0.806 | 0.667 | 0.700 | 0.587 | 0.226 |

## Tokenization

| Run | Model | Surface | Mean tokens | Max tokens | One-token fraction |
| --- | --- | --- | --- | --- | --- |
| E03 | Qwen3-1.7B | base | 2.522 | 4 | 0.074 |
| E06 | Qwen3-8B | base | 2.522 | 4 | 0.074 |
| E07 | Fanar-1-9B | base | 3.639 | 5 | 0.000 |
| E08 | ALLaM-7B | base | 1.896 | 4 | 0.309 |
| E05b | Qwen3-1.7B | full | 2.865 | 5 | 0.037 |
| E06b | Qwen3-8B | full | 2.865 | 5 | 0.037 |
| E07b | Fanar-1-9B | full | 3.892 | 6 | 0.000 |
| E08b | ALLaM-7B | full | 1.924 | 4 | 0.294 |

## Representation Geometry

| Run | Model | Surface | Min edim90 | Min edim90 layer | Collapsed layers | Max abs activation |
| --- | --- | --- | --- | --- | --- | --- |
| E03 | Qwen3-1.7B | base | 1 | 3 | 24 | 12736.0 |
| E06 | Qwen3-8B | base | 1 | 7 | 29 | 13920.0 |
| E07 | Fanar-1-9B | base | 72 | 42 | 0 | 509.0 |
| E08 | ALLaM-7B | base | 1 | 3 | 29 | 1694.0 |
| E05b | Qwen3-1.7B | full | 1 | 3 | 21 | 12736.0 |
| E06b | Qwen3-8B | full | 1 | 7 | 29 | 13904.0 |
| E07b | Fanar-1-9B | full | 116 | 42 | 0 | 539.0 |
| E08b | ALLaM-7B | full | 1 | 3 | 29 | 1694.0 |

## Reading

The strongest paper-level signal is template recoverability, especially the nonce held-out-root condition. All main models reach saturated accuracy there, so the result is not a one-model artifact.

The model comparison is irregular in the same broad sense as Alakeel et al.: tokenizer compactness and Arabic-centric status do not produce a simple performance ordering. Qwen3-8B is strongest on transfer, Fanar is strongest on full-form family-split real templates and has the cleanest geometry, while ALLaM is compactly tokenized but weak on real/nonce transfer.

The root probes should remain diagnostic. In the nonce condition, character n-grams nearly solve root identity, so root accuracy is not the main evidence for abstract morphology.

## Generated Files

- `probe_metrics.csv`: one row per probe per run.
- `token_count_accuracy.csv`: token-count accuracy at each probe peak.
- `tokenization_summary.csv`: tokenizer diagnostics per run.
- `geometry_summary.csv`: representation geometry diagnostics per run.
- `base_template_comparison.png`: base-form template probe comparison.
- `full_family_comparison.png`: full-form family-split comparison.
- `transfer_comparison.png`: real/nonce transfer comparison.
- `ngram_gap_comparison.png`: mean template advantage over n-grams.
- `selectivity_comparison.png`: mean template selectivity over shuffled-label control.
- `tokenization_by_model.png`: tokenization comparison.
- `geometry_effective_dims.png`: geometry comparison.
- `pooling_ablation_qwen17b.png`: Qwen3-1.7B pooling control.
