# Cross-Model Interpretation

Date: 2026-05-03  
Models: `Qwen/Qwen3-1.7B-Base`, `Qwen/Qwen3-8B`, `QCRI/Fanar-1-9B`, `humain-ai/ALLaM-7B-Instruct-preview`

## Lab-Head Summary

The study is now clearly worth completing. The central result survives model scaling and cross-model comparison:

```text
Arabic derivational template information is linearly recoverable from decoder-only LLM word representations.
```

But the stronger and more interesting finding is model variation:

```text
Qwen3-8B is strongest on real/nonce transfer.
Fanar is strongest on affixed real full-form family split and has the cleanest representation geometry.
ALLaM is strong on nonce template probes but weak on real/nonce transfer.
```

This means the paper should not say "Arabic-centric models are simply better." The evidence is more nuanced.

## Base-Form Template Comparison

| Run | Model | Real Templates | Nonce Templates | Nonce Held-Out Roots | Real -> Nonce | Nonce -> Real |
|---|---|---:|---:|---:|---:|---:|
| E03 | Qwen3-1.7B | 0.808 | 0.950 | 1.000 | 0.710 | 0.880 |
| E06 | Qwen3-8B | 0.962 | 1.000 | 1.000 | 0.870 | 0.980 |
| E07 | Fanar-1-9B | 0.885 | 0.950 | 1.000 | 0.820 | 0.940 |
| E08 | ALLaM-7B | 0.692 | 0.950 | 1.000 | 0.630 | 0.580 |

The key finding is that all models reach 1.000 on nonce held-out-root template probing. That is strong cross-model evidence for template decodability in the controlled nonce setting.

The differentiator is transfer:

```text
Qwen3-8B > Fanar > Qwen3-1.7B > ALLaM
```

This ranking is clearest on `nonce -> real`, where ALLaM falls below the n-gram baseline.

## Full-Form Family-Split Comparison

| Run | Model | Real Templates Family | N-Gram | Real -> Nonce | Nonce -> Real |
|---|---|---:|---:|---:|---:|
| E05b | Qwen3-1.7B | 0.903 | 0.667 | 0.800 | 0.807 |
| E06b | Qwen3-8B | 0.931 | 0.667 | 0.890 | 0.907 |
| E07b | Fanar-1-9B | 0.944 | 0.667 | 0.770 | 0.860 |
| E08b | ALLaM-7B | 0.806 | 0.667 | 0.700 | 0.587 |

The full-form family split is one of the strongest parts of the study. It closes the E05 sibling-leakage loophole and still gives high template accuracy for Qwen and Fanar.

Fanar is best on `real_templates_random` under family split:

```text
Fanar: 0.944
Qwen3-8B: 0.931
Qwen3-1.7B: 0.903
ALLaM: 0.806
```

Qwen3-8B is best on transfer:

```text
real -> nonce: 0.890
nonce -> real: 0.907
```

ALLaM remains weak, especially nonce-to-real transfer:

```text
ALLaM E08b nonce -> real: 0.587
n-gram baseline:          0.753
```

## Tokenization

The models tokenize Arabic very differently:

| Model | Base Mean Tokens | Full Mean Tokens | Interpretation |
|---|---:|---:|---|
| Qwen3 | 2.52 | 2.87 | Moderate fragmentation. |
| Fanar | 3.64 | 3.89 | Heavy fragmentation. |
| ALLaM | 1.90 | 1.92 | Compact tokenization. |

Performance does not reduce to token count. Fanar is heavily fragmented but strong. ALLaM is compact but weaker on real/transfer. This supports the conclusion that tokenization matters, but it is not the whole explanation.

## Representation Geometry

The representation diagnostics now matter for the paper.

Qwen3-1.7B and Qwen3-8B:

```text
mid-layer activation outliers
90-95% variance often collapses into one component
```

ALLaM:

```text
also shows severe mid-layer collapse
```

Fanar:

```text
cleaner geometry
effective dimensions remain broad across layers
no severe one-component collapse
```

This makes Fanar especially useful for interpreting layer curves. Qwen may be behaviorally strongest, but Fanar may be geometrically cleaner.

## Root Probes

Root probing remains secondary. Across models, nonce root accuracy is saturated:

```text
probe: 1.000
n-gram: 0.950
```

That is not enough for an abstract-root claim. Real-root random probing varies, but the task is small and not the paper's main target.

The paper should keep root probes as diagnostics, not the central contribution.

## Main Conclusions

### Claim 1: Template information is recoverable across models.

Supported. All models recover nonce held-out-root templates at 1.000 and beat controls/n-grams.

### Claim 2: Larger Qwen improves template transfer.

Supported. Qwen3-8B improves over Qwen3-1.7B most clearly on real/nonce transfer.

### Claim 3: Arabic-centric models are not uniformly better.

Supported. Fanar is strong and geometrically clean; ALLaM is weak on transfer.

### Claim 4: Affixed real forms retain template signal under grouped splitting.

Supported for Qwen and Fanar, weaker but still above n-gram for ALLaM real-template family split.

### Claim 5: Exact morphology-layer localization is not safe yet.

Supported. Qwen and ALLaM geometry issues make exact layer claims risky. Fanar may support more careful layer analysis, but that should be framed cautiously.

## Paper-Level Answer

The paper can now answer:

```text
Decoder-only LLMs expose Arabic derivational template information in word-level representations.
The signal generalizes robustly to nonce held-out-root forms across all tested models.
Real/nonce transfer and affixed-form robustness vary substantially by model.
Qwen3-8B is strongest on transfer; Fanar is strongest on affixed real forms and has the cleanest representation geometry; ALLaM is weaker despite being Arabic-centric.
```

This is a real result. It is no longer just a Qwen3-1.7B pilot.

## Next Lab Step

At this point, the main experiment set is complete enough for a draft. The generated summary tables and plots are now in [summary/cross_model_summary.md](summary/cross_model_summary.md).

The next work should be:

```text
1. decide whether to add nonce affixed forms as a final robustness experiment
2. write the paper narrative around template probing, not root probing
3. use the summary plots as the paper's first result figures
```

Do not add many more model runs before drafting. The current set is already sufficient to support the central research question.
