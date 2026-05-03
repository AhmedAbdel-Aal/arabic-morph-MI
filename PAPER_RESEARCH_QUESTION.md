# Paper Research Question

## Main Research Question

```text
Do decoder-only LLMs encode Arabic derivational template information in word-level representations, beyond surface-form and memorization baselines?
```

This is the cleanest paper question. It is specific, testable, and matches the strongest evidence in the current experiments.

## Subquestion 1: Generalization

```text
Does template information generalize to nonce roots and real/nonce transfer settings?
```

Why this matters: it separates morphology from memorized vocabulary.

Relevant probes:

```text
nonce_templates_heldout_roots
train_real_test_nonce_overlap
train_nonce_test_real_overlap
```

## Subquestion 2: Robustness To Affixes

```text
Does template information remain recoverable in affixed real forms when sibling variants are grouped out of the train/test split?
```

Why this matters: base forms are clean, but real Arabic includes prefixes and suffixes.

Relevant setup:

```text
surface=full
pooling=last
real_split=family
```

## Subquestion 3: Model Differences

```text
Do Arabic-centric models expose this information more strongly than a general multilingual model?
```

Why this matters: it makes the study more than a single-model probing result.

Compare:

```text
Qwen/Qwen3-8B
QCRI/Fanar-1-9B
humain-ai/ALLaM-7B-Instruct-preview
```

against the development reference:

```text
Qwen/Qwen3-1.7B-Base
```

## Not The Main Paper Question

These are secondary or methodological, not the main paper question:

```text
Do models encode roots?
Does pooling matter?
Which exact layer is morphology stored in?
Do sentence contexts preserve morphology?
```

Root probing is currently too surface-solvable. Pooling is resolved and justified by prior work. Exact layer localization is risky because of representation-geometry issues. Sentence contexts are better as a later ecological-validity experiment.

## Paper Framing

```text
We investigate whether Arabic derivational template information is linearly recoverable from decoder-only LLM word representations under controlled real/nonce and affixed-form evaluations.
```

## Contributions

```text
1. Controlled probing of Arabic root-pattern template representations.
2. Nonce and transfer tests against memorization.
3. Affixed-form grouped split against sibling leakage.
4. Cross-model comparison between general multilingual and Arabic-centric LLMs.
```
