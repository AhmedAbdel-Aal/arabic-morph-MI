# Next Goals For A Strong Paper

Date: 2026-05-04

This document separates the immediate paper-building goals from longer-term ideas. The current paper should stay focused: stronger data, stronger controls, and one credible mechanistic analysis.

## Goal 1: Build A Larger Dataset

The current Alakeel productivity subset is good for kickoff experiments, but too small for a strong paper by itself. The next dataset should be larger, balanced, and explicitly designed for probing.

Target properties:

- substantially more real Arabic root-template forms
- balanced template labels where possible
- base forms and affixed full forms
- family identifiers for `(root, template, base_form)` so affixed siblings stay together in grouped splits
- root-frequency metadata
- CAMEL-backed extraction and validation
- nonce roots checked to avoid valid Arabic roots
- nonce forms across the same templates as real forms
- nonce affixed forms, if we want a stronger affix robustness result

Main purpose:

```text
Move from a promising pilot to a dataset large enough for stable, reviewer-facing claims.
```

## Goal 2: Add A Mechanistic Analysis

The current evidence is mainly linear probing. That is valid, but if the paper uses mechanistic language, it needs at least one deeper representational analysis.

Candidate analyses:

- layer-wise template recoverability across normalized depth
- representation geometry and effective-dimensionality diagnostics
- nearest-neighbor or clustering analysis by template versus root
- subspace analysis for template information
- token-count stratified results to separate morphology from tokenizer effects

The safest near-term mechanistic direction is:

```text
Show where template information becomes recoverable, how stable it is across layers, and whether that pattern is distorted by representation geometry.
```

This is stronger than reporting only peak probe accuracy, but still feasible with the current pipeline.

## Later Idea: Steering Or Patching

This is a later-stage idea, not a current paper commitment.

Question:

```text
If we patch or steer the representation associated with a derivational template, can we change the generated form of a given root?
```

Example intuition:

```text
root representation + template intervention -> different derived surface form
```

Why it matters:

- It would move beyond recoverability toward causal use.
- It would connect internal representations to generation behavior.
- It could become a stronger mechanistic follow-up paper.

Why it should stay later:

- It requires careful generation setup.
- It needs causal intervention design, not only probing.
- It can distract from the current paper's clearer contribution.

Current decision:

```text
Do not make steering a deliverable for the first paper. Keep it as a discussion/future-work direction.
```
