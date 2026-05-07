# Cross-Study Interpretation

Date: 2026-05-03  
Models studied: `Qwen/Qwen3-1.7B-Base`, `Qwen/Qwen3-8B`, `QCRI/Fanar-1-9B`, `humain-ai/ALLaM-7B-Instruct-preview`  
Dataset: Alakeel productivity dataset copied to `data/productivity_dataset.json`

Updated cross-model synthesis: [cross_model_interpretation.md](cross_model_interpretation.md)

## Executive Lab Judgment

This study is worth completing. The current experiments are not just producing random probe wins. They are beginning to reveal a coherent mechanism:

```text
Arabic root-pattern information is linearly recoverable when the extracted representation has access to the whole word.
```

That sounds simple, but it matters. Arabic root-pattern morphology is non-concatenative: the root is distributed through the word, and the template is interleaved with the root. For decoder-only LLMs, the choice of extraction position is not neutral. The final subword can attend backward over the word; the first subword cannot attend forward. The experiments show exactly that.

The strongest result so far is not "root probing is high." Root probing is often surface-solvable. The strongest result is:

```text
template probing generalizes to nonce words and held-out roots,
and this survives controls better than character n-grams.
```

That is the core scientific signal.

## The Main Research Gap

The study is targeting a real gap. Most probing and mechanistic morphology work has focused on English-like concatenative morphology, general POS/inflectional features, or broad multilingual probes. Arabic derivational morphology is different because the important structure is root-pattern interdigitation, not just suffixes and prefixes.

The gap is not merely "does the model know Arabic morphology?" The better question is:

```text
Where, and under what representation choices, does a decoder-only LLM expose Arabic root-pattern structure?
```

This is a real mechanistic question because the answer depends on tokenization, causal attention direction, pooling, surface baselines, and split design.

## Experiments So Far

| Run | Purpose | Main Takeaway |
|---|---|---|
| E01 | Template-only smoke test | Positive first signal; template labels were recoverable above controls. |
| E02 | Template + root baseline | Template probes are the meaningful result; root probes are high but often surface-solvable. |
| E03 | Last-token baseline with diagnostics | Primary decoder-only setup; strong template results, layer-0 weakness explained by tokenization/causal pooling. |
| E04a | First-token pooling ablation | Signal collapses, especially root held-out-template. First token is a poor word representation. |
| E04b | Mean-pooling ablation | Signal mostly returns. Whole-word subword access is the key factor. |
| E05 | Full-form/affixed real stress test | Template signal survives affixed real forms, but random real splits become surface-solvable. |

## What We Are Seeing Across Runs

### 1. Template Signal Is The Central Positive Result

The base-form last-token run E03 gives the cleanest current template evidence:

| Probe | E03 Acc. | Control | N-Gram | Chance |
|---|---:|---:|---:|---:|
| real templates random | 0.808 | 0.000 | 0.654 | 0.077 |
| nonce templates random | 0.950 | 0.150 | 0.300 | 0.200 |
| nonce templates held-out roots | 1.000 | 0.150 | 0.600 | 0.200 |
| train real -> test nonce | 0.710 | 0.260 | 0.580 | 0.200 |
| train nonce -> test real | 0.880 | 0.300 | 0.780 | 0.200 |

The most important one is `nonce_templates_heldout_roots`: the model reaches 1.000 while the n-gram baseline is 0.600. This says the probe is not just identifying a memorized root string. It can recover template labels for nonce roots that were held out.

The transfer results are also important, but less clean. They show movement between real and nonce forms. `train_nonce -> test_real` is high, but n-grams are also high. `train_real -> test_nonce` has a smaller but meaningful margin.

Lab conclusion:

```text
Template probing is the main publishable phenomenon so far.
```

### 2. Root Probing Is Informative, But Not Yet Main Evidence

Root probes often look spectacular:

| Probe | E03 Acc. | N-Gram |
|---|---:|---:|
| real roots random | 0.524 | 0.095 |
| nonce roots random | 1.000 | 0.950 |
| nonce roots held-out templates | 1.000 | 0.950 |

The real-root result is underpowered: 45 items across 21 labels. The nonce-root result is mostly surface-solvable: the root consonants are visible in the string, and the n-gram baseline already reaches 0.950.

This does not make root probing useless. It changes its role. Root probing is useful as a diagnostic for whether the representation has access to the whole word. E04a and E04b make that clear:

| Probe | E03 Last | E04a First | E04b Mean |
|---|---:|---:|---:|
| nonce roots held-out templates | 1.000 | 0.100 | 0.950 |

That is an extremely informative contrast. The surface string contains the root, and the n-gram baseline can recover it. But the first-token representation cannot. So the representation extraction choice controls whether root information is available.

Lab conclusion:

```text
Root probing is a mechanistic diagnostic right now, not the strongest morphology claim.
```

### 3. Pooling Is Not A Technical Detail; It Is Part Of The Mechanism

E04a and E04b are decisive. They explain why E03 behaves the way it does.

| Probe | E03 Last | E04a First | E04b Mean |
|---|---:|---:|---:|
| real templates random | 0.808 | 0.385 | 0.692 |
| nonce templates random | 0.950 | 0.400 | 0.850 |
| nonce templates held-out roots | 1.000 | 0.650 | 0.950 |
| train real -> test nonce | 0.710 | 0.580 | 0.640 |
| train nonce -> test real | 0.880 | 0.720 | 0.840 |
| nonce roots held-out templates | 1.000 | 0.100 | 0.950 |

This pattern strongly supports the whole-word-access account:

```text
first pooling = partial prefix-like representation
last pooling = final token can aggregate previous subwords through causal attention
mean pooling = external whole-word average over all subword pieces
```

For a decoder-only model, this is exactly what we should expect. The first token cannot attend to later pieces. The last token can attend backward. Mean pooling can access all pieces even at layer 0 because we average all token embeddings ourselves.

Lab conclusion:

```text
The pooling ablations are not side analyses. They are central to the mechanistic argument.
```

### 4. The Layer-0 Story Is Now Clearer

The early question was why layer 0 was weak and then accuracy spiked in layers 2-5. The answer is probably not "morphology suddenly appears from nowhere." It is token access.

In E03 last-token pooling:

```text
layer 0 final subword only knows itself
early transformer layers let it attend backward over earlier subwords
```

In E04a first-token pooling:

```text
first subword cannot see later subwords in a causal decoder
signal collapses
```

In E04b mean pooling:

```text
layer 0 can already average all subword embeddings
signal returns early
```

So the layer-0 weakness in E03 is not a failure. It is consistent with causal decoder mechanics.

Lab conclusion:

```text
For decoder-only LLMs, layer curves must be interpreted jointly with tokenization and extraction position.
```

### 5. E05 Shows Robustness, But Also Warns Us About Split Leakage

E05 uses full real forms, including affixed variants, while nonce remains base-only.

Important dataset fact:

```text
real: 390 rows = 130 unaffixed + 260 affixed
nonce: 100 rows = base-only
```

E05 results:

| Probe | E03 Base Last | E05 Full Last | E05 N-Gram |
|---|---:|---:|---:|
| real templates random | 0.808 | 0.962 | 1.000 |
| train real -> test nonce | 0.710 | 0.800 | 0.590 |
| train nonce -> test real | 0.880 | 0.807 | 0.753 |
| real roots random | 0.524 | 0.877 | 0.642 |

The good news:

```text
train real full -> test nonce base improves to 0.800
```

This suggests affixed real forms still expose template information that transfers to nonce examples.

The caution:

```text
real_templates_random has n-gram = 1.000
```

That makes it surface-solvable. Also, real full forms contain sibling variants of the same base/root-template family. A random split can put one sibling in train and another in test. That inflates random-split results.

Lab conclusion:

```text
E05 is a useful robustness stress test, not central evidence yet.
```

## What We Can Conclude Now

### Claim 1: Qwen3-1.7B exposes Arabic template information in its representations.

Status: supported.

The support is strongest for base-form template probes, especially nonce held-out roots, where the model beats chance, word-type controls, and character n-grams.

### Claim 2: The signal depends on whole-word access across subword pieces.

Status: strongly supported.

E04a and E04b show that first-token extraction destroys much of the signal, while mean pooling restores it. This lines up with causal decoder attention.

### Claim 3: Last-token pooling is a reasonable primary extraction method for decoder-only LLMs.

Status: supported.

Last-token pooling is not arbitrary here. It is the token position that can aggregate previous subword pieces. E04b shows that the success is not only a last-token artifact; mean pooling also works.

### Claim 4: The model has abstract root representations.

Status: not yet supported strongly.

Root information is recoverable, but nonce root tasks are surface-solvable and real root random split is underpowered or leakage-prone. We can say root identity is decodable, but we should not yet call it abstract root morphology.

### Claim 5: The model has affix-invariant morphology.

Status: promising, not proven.

E05 suggests affixes do not destroy the signal. But the real-full random split is too easy, and nonce does not contain affixed variants. We need grouped splits and nonce affixed forms.

## What We Should Not Claim Yet

Do not claim:

```text
1. Qwen has human-like Arabic morphology.
2. High root probing proves abstract root representation.
3. Layer 3 is "the morphology layer."
4. Full-form random-split accuracy proves affix-invariance.
5. The current result generalizes across model families.
```

The current evidence is promising, but the paper-level claim must be sharper and more conservative.

## Representation Geometry Concern

Across E03, E04a, E04b, and E05, Qwen3-1.7B shows severe activation geometry issues:

```text
layers 3-20 often have max activations around 12488-12936
90-95% variance can collapse into one principal component
```

This does not invalidate the probing results, but it does mean exact layer localization is risky. We can discuss early-layer availability, but we should avoid overclaiming that a specific layer is mechanistically special.

This also makes model comparison important. If Fanar, ALLaM, and Qwen3-8B do not show the same geometry, their layer curves may be more interpretable.

## Relationship To Prior Work

The current pattern fits a broader story from representation probing work:

```text
surface and lexical information is often highly recoverable early;
morphosyntactic and inflectional information can remain linearly decodable;
controls are needed because probes can exploit memorization and surface form.
```

Our contribution is narrower and more Arabic-specific:

```text
for non-concatenative Arabic morphology, subword access and causal direction are central to whether root-pattern information is recoverable.
```

That is a worthwhile extension beyond generic morphology probing.

## Direction Of The Study

The study should move from "can we get high probe accuracy?" to:

```text
under what controls does Arabic root-pattern information remain decodable?
```

The next phase should be organized around three axes:

```text
1. Better splits
2. More models
3. Stronger controls
```

## Immediate Next Steps

### 1. Add E05b: grouped full-form split

Goal:

```text
prevent affixed siblings of the same base/root-template family from appearing in both train and test
```

This is the most important next code/data improvement. It directly addresses the biggest E05 weakness.

### 2. Add nonce affixed variants or synthetic affix augmentation

Current nonce is base-only. To test affix-invariant generalization properly, we need:

```text
nonce base
nonce + prefix
nonce + suffix
```

This can be done carefully with a small controlled affix set, manually checked if necessary.

### 3. Scale the model set

Run the core configuration first:

```text
surface=base
pooling=last
```

on:

```text
Qwen/Qwen3-8B
QCRI/Fanar-1-9B
humain-ai/ALLaM-7B-Instruct-preview
```

The goal is not just bigger numbers. The goal is to see whether:

```text
1. template decodability is model-general
2. Arabic-centric models differ from Qwen
3. activation geometry differs by model
4. the early-layer pattern survives
```

### 4. Keep E04 pooling controls as required reporting

Any serious report should include:

```text
last pooling = primary decoder-only setup
first pooling = partial-token negative control
mean pooling = whole-word access control
```

This is one of the strongest parts of the current study design.

### 5. Separate root and template claims

The paper should not blur them. Template probing is the central claim. Root probing is secondary unless we create stricter root experiments.

Potential stricter root experiments:

```text
1. evaluate root recovery across held-out templates with harder surface controls
2. compare to consonant-position baselines
3. create nonce roots where root consonants are less trivially captured by n-grams
4. test whether representation similarity clusters by root after controlling template
```

## Proposed Paper-Level Hypothesis

The clean hypothesis is:

```text
Decoder-only LLMs encode Arabic derivational template information in word-level representations, including for nonce forms, but this information is only reliably exposed when the extracted representation has access to all subword pieces of the word.
```

Secondary hypothesis:

```text
Root identity is decodable, but current root probes are strongly entangled with surface orthography; stricter controls are required before interpreting root decodability as abstract morphological representation.
```

Affix hypothesis:

```text
Affixes do not eliminate template decodability, but current full-form results need grouped-split controls before supporting affix-invariance claims.
```

## Final Lab Verdict

Continue the study.

The topic is real, the current results are coherent, and the experiments have already exposed nontrivial structure:

```text
the morphology signal is not just high accuracy;
it changes predictably with causal attention direction and subword access.
```

That is exactly the kind of mechanistic pattern worth pursuing.

The study is not ready for strong claims about abstract roots or affix-invariant morphology. But it is ready for a more rigorous second phase focused on grouped splits, nonce affix augmentation, and multi-model comparison.

The shortest honest conclusion right now is:

```text
Qwen3-1.7B linearly exposes Arabic template information in whole-word representations.
The effect generalizes to nonce forms and survives pooling controls.
Root results are decodable but not yet abstract.
Affixed real forms are promising but require stricter split design.
```
