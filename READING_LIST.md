# Reading List For The Arabic Morphology Interpretability Study

Date: 2026-05-08

This is not a general interpretability bibliography. It is the reading list needed to turn the current Arabic root-pattern probing work into a defensible paper.

## Reading Strategy

Read in this order:

1. probing methodology and its limits
2. representation geometry
3. causal/mechanistic analysis
4. morphology and Arabic-specific context
5. steering and patching as future work

The goal is to sharpen the paper's claim:

```text
Arabic derivational template information is linearly recoverable from LLM word representations, but recoverability is not the same as causal use.
```

## Tier 0: Must Read First

These papers directly determine whether our current study is methodologically defensible.

### 1. Hewitt and Liang, 2019: Designing and Interpreting Probes with Control Tasks

Link: https://aclanthology.org/D19-1275/

Why it matters:

- This is the basis for the shuffled-label control we already use.
- It explains why probe accuracy alone is not enough.
- It gives us the language of selectivity: high task accuracy and low control accuracy.

What to extract for our paper:

- Report selectivity, not only accuracy.
- Justify shuffled-label controls explicitly.
- Avoid saying "the model knows morphology" based only on high probe scores.

### 2. Belinkov, 2022: Probing Classifiers: Promises, Shortcomings, and Advances

Link: https://aclanthology.org/2022.cl-1.7/

Why it matters:

- Best short overview of what probing can and cannot prove.
- Useful for the related work and limitations section.

What to extract:

- Framing: probes test information availability, not necessarily model use.
- Use this to position our study as representational analysis, not behavioral proof.

### 3. Amini et al., 2023: Naturalistic Causal Probing for Morpho-Syntax

Link: https://aclanthology.org/2023.tacl-1.23/

Why it matters:

- Directly relevant to morphology.
- Shows that correlational probes can overestimate linguistic information.
- Provides the right caution for our nonce/template probing.

What to extract:

- Our current probes are correlational.
- Future stronger work should use interventions or controlled counterfactuals.
- This paper supports our decision to be cautious about the 1.000 nonce held-out-root result.

### 4. Timkey and van Schijndel, 2021: All Bark and No Bite

Link: https://aclanthology.org/2021.emnlp-main.372/

Why it matters:

- We observed severe representation geometry issues in Qwen and ALLaM.
- This paper explains how a few rogue dimensions can dominate similarity and obscure representation quality.

What to extract:

- Geometry diagnostics are not cosmetic; they are necessary.
- If we do clustering, cosine similarity, or nearest neighbors, we must standardize/center or account for rogue dimensions.

### 5. Alakeel et al., 2026: Morphemes Without Borders

Link: https://arxiv.org/abs/2603.15773

Why it matters:

- This is the closest Arabic root-pattern LLM paper.
- Their work tests tokenizer alignment and generation behavior.
- Their limitation opens our contribution: generation may mix morphology with instruction following.

What to extract:

- We are complementary: they study output behavior; we study hidden representations.
- Their finding that tokenizer alignment is not necessary/sufficient matches our irregular model results.

## Tier 1: Probing Design And Interpretation

### 6. Pimentel et al., 2020: Information-Theoretic Probing for Linguistic Structure

Link: https://aclanthology.org/2020.acl-main.420/

Why it matters:

- Gives a different view of probing as estimating mutual information.
- Challenges the simple belief that only simple probes are valid.

What to extract:

- Accuracy is only one operationalization.
- If we later add MLP probes, this paper helps explain what a higher-capacity probe does and does not mean.

### 7. Voita and Titov, 2020: Information-Theoretic Probing with Minimum Description Length

Link: https://aclanthology.org/2020.emnlp-main.14/

Why it matters:

- MDL probing asks how efficiently a representation supports learning a label.
- Useful if reviewers ask why peak accuracy is enough.

What to extract:

- A stronger version of our paper could report data efficiency / description length.
- Not necessary for the current pipeline, but good for paper framing.

### 8. Elazar et al., 2021: Amnesic Probing

Link: https://direct.mit.edu/tacl/article/doi/10.1162/tacl_a_00359/98091/Amnesic-Probing-Behavioral-Explanation-with

Why it matters:

- Makes the key distinction between encoded information and behavioral use.
- Uses counterfactual removal of information.

What to extract:

- This is a bridge from probing to causal claims.
- If we remove template information and output behavior changes, that would be a stronger future result.

### 9. Ravfogel et al., 2020: Null It Out

Link: https://aclanthology.org/2020.acl-main.647/

Why it matters:

- Introduces Iterative Nullspace Projection for removing linearly encoded information.
- Relevant to testing whether template information is localized in a linear subspace.

What to extract:

- Possible future experiment: remove template subspace and test whether template probing collapses while other information remains.

### 10. Hewitt and Manning, 2019: A Structural Probe for Finding Syntax

Link: https://aclanthology.org/N19-1419/

Why it matters:

- Shows how linguistic structure can be studied through geometry, not only class labels.
- Good conceptual model for template geometry.

What to extract:

- We can ask whether same-template forms become close under a learned projection.
- This may inspire a template-geometry probe beyond classification.

## Tier 2: Representation Geometry

### 11. Ethayarajh, 2019: How Contextual Are Contextualized Word Representations?

Link: https://aclanthology.org/D19-1006/

Why it matters:

- Establishes anisotropy as a core property of contextual embeddings.
- Relevant to our layer-wise geometry diagnostics.

What to extract:

- Do not interpret distances or similarities naively.
- Contextual representation geometry changes by layer.

### 12. Elhage et al., 2022: Toy Models of Superposition

Link: https://transformer-circuits.pub/2022/toy_model/

Why it matters:

- Explains why features may be represented in superposition rather than clean neurons or axes.
- Important background before claiming template subspaces are simple.

What to extract:

- Template information may be distributed.
- Failure to find single neurons/features does not mean absence of morphology.

### 13. Bricken et al., 2023: Towards Monosemanticity

Link: https://transformer-circuits.pub/2023/monosemantic-features/

Why it matters:

- Sparse autoencoders can decompose activations into more interpretable features.
- This is not needed for paper 1, but it is relevant if we later want deeper mechanistic claims.

What to extract:

- Future work: train or use SAEs to look for Arabic template/root features.
- Do not start here; this is a later-stage mechanistic route.

## Tier 3: Causal And Mechanistic Analysis

### 14. Elhage et al., 2021: A Mathematical Framework for Transformer Circuits

Link: https://transformer-circuits.pub/2021/framework/index.html

Why it matters:

- Core mechanistic interpretability reference.
- Explains residual stream, attention heads, path expansion, and subspace communication.

What to extract:

- Use precise language: residual stream, layer, component, activation, intervention.
- Helps avoid vague "mechanistic" claims.

### 15. Vig et al., 2020: Investigating Gender Bias Using Causal Mediation Analysis

Link: https://papers.neurips.cc/paper_files/paper/2020/hash/92650b2e92217715fe312e6fa7b90d82-Abstract.html

Why it matters:

- Clear example of moving from "information exists" to "which components mediate behavior."
- Causal mediation is a possible future template for morphology.

What to extract:

- If we want to claim causal use, we need mediation or patching, not just probes.

### 16. Finlayson et al., 2021: Causal Analysis of Syntactic Agreement Mechanisms

Link: https://aclanthology.org/2021.acl-long.144/

Why it matters:

- Closest model for linguistic mechanism work.
- Studies grammatical inflection with causal mediation.

What to extract:

- A template-morphology intervention paper could follow this structure.
- Good example of testing mechanisms across syntactic contexts and model sizes.

### 17. Geiger et al., 2023: Causal Abstraction for Faithful Model Interpretation

Link: https://arxiv.org/abs/2301.04709

Why it matters:

- Gives a formal framework for mapping high-level variables onto model internals.
- Relevant if we later want to say "template" is a causal variable in the model.

What to extract:

- Template, root, affix, and surface form could be high-level variables.
- Interventions are the path from recoverability to mechanism.

### 18. Zhang and Nanda, 2023: Towards Best Practices of Activation Patching

Link: https://arxiv.org/abs/2309.16042

Why it matters:

- Activation patching is tempting, but fragile.
- This paper warns that metrics and corruption choices can change conclusions.

What to extract:

- If we do patching, define the metric first.
- Use multiple corruption controls.
- Do not overinterpret one patching heatmap.

## Tier 4: Morphology, Arabic, And Generalization

### 19. Weissweiler et al., 2023: Counting the Bugs in ChatGPT's Wugs

Link: https://aclanthology.org/2023.emnlp-main.401/

Why it matters:

- Multilingual wug-test style evaluation of morphology.
- Good background for nonce forms and morphology generalization.

What to extract:

- Nonce testing is standard, but scoring and contamination are hard.
- Helps justify our nonce subset.

### 20. Hofmann et al., 2025: Derivational Morphology Reveals Analogical Generalization in LLMs

Link: https://pmc.ncbi.nlm.nih.gov/articles/PMC12088417/

Why it matters:

- Directly about derivational morphology and LLM generalization.
- Argues for analogical mechanisms rather than simple rules.

What to extract:

- Our results may be explainable as analogical/template-shape generalization.
- This helps us avoid overclaiming "rule learning."

### 21. Obeid et al., 2020: CAMeL Tools

Link: https://aclanthology.org/2020.lrec-1.868/

Why it matters:

- The toolkit behind our Arabic morphology processing.
- Needed for data-generation and validation credibility.

What to extract:

- Cite for Arabic NLP tooling and morphological analysis.

### 22. Khairallah et al., 2024: Camel Morph MSA

Link: https://aclanthology.org/2024.lrec-main.240/

Why it matters:

- Large-scale open-source morphological analyzer/generator for MSA.
- Relevant if we build the larger dataset.

What to extract:

- Use for data expansion and validation.
- Cite when explaining CAMEL-backed dataset construction.

## Tier 5: Steering And Patching As Future Work

These are not needed for the first paper, but they define the follow-up idea: can template representations be patched or steered to change generated forms?

### 23. Turner et al., 2023: Steering Language Models with Activation Engineering

Link: https://arxiv.org/abs/2308.10248

Why it matters:

- Introduces activation addition as a simple steering method.
- Relevant to future template-vector steering.

What to extract:

- Template vectors could be built from contrastive template examples.
- Start with candidate scoring before free generation.

### 24. Zou et al., 2023: Representation Engineering

Link: https://arxiv.org/abs/2310.01405

Why it matters:

- Frames population-level representation reading and control.
- Conceptually close to "template as a direction/subspace."

What to extract:

- Steering can be framed as representation control, not just probing.

### 25. Rimsky et al., 2023: Steering Llama 2 via Contrastive Activation Addition

Link: https://arxiv.org/abs/2312.06681

Why it matters:

- More practical contrastive activation steering setup.
- Useful if we later compare "template A vs template B" activations.

What to extract:

- Build paired datasets carefully.
- Sweep layer and coefficient.
- Evaluate target behavior and side effects.

## Suggested Reading Order

### Week 1: Probing Validity

Read:

1. Hewitt and Liang 2019
2. Belinkov 2022
3. Amini et al. 2023
4. Pimentel et al. 2020

Deliverable:

```text
Revise paper claims around "recoverability", "selectivity", and "correlational probing".
```

### Week 2: Geometry

Read:

1. Ethayarajh 2019
2. Timkey and van Schijndel 2021
3. Toy Models of Superposition

Deliverable:

```text
Decide how to report anisotropy, rogue dimensions, effective dimensionality, and layer-wise stability.
```

### Week 3: Causal Mechanisms

Read:

1. Vig et al. 2020
2. Finlayson et al. 2021
3. Geiger et al. 2023
4. Zhang and Nanda 2023

Deliverable:

```text
Decide whether the current paper remains probing-only or adds one causal/mechanistic analysis.
```

### Week 4: Morphology And Arabic Framing

Read:

1. Alakeel et al. 2026
2. Weissweiler et al. 2023
3. Hofmann et al. 2025
4. CAMeL Tools and Camel Morph MSA papers

Deliverable:

```text
Finalize dataset expansion plan and Arabic NLP contribution framing.
```

## What We Should Cite In The First Paper

Must cite:

- Hewitt and Liang 2019
- Belinkov 2022
- Amini et al. 2023
- Timkey and van Schijndel 2021
- Ethayarajh 2019
- Alakeel et al. 2026
- CAMeL Tools / Camel Morph MSA
- Weissweiler et al. 2023 or Hofmann et al. 2025 for nonce/derivational morphology context

Likely cite if we add deeper analysis:

- Vig et al. 2020
- Finlayson et al. 2021
- Geiger et al. 2023
- Zhang and Nanda 2023

Keep for future-work section:

- Turner et al. 2023
- Zou et al. 2023
- Rimsky et al. 2023
- Bricken et al. 2023

## Practical Consequences For Our Study

After reading this list, the study should become sharper in five ways:

1. Stop treating probe accuracy as the main result; report accuracy, selectivity, n-gram gap, and split type together.
2. Treat nonce held-out-root saturation as template-shape recoverability, not proof of abstract productive morphology.
3. Make full-form family split and real/nonce transfer central.
4. Add geometry diagnostics as part of the result, especially because Qwen and ALLaM show collapse/outliers.
5. Keep steering/patching as future work unless we design a careful candidate-scoring intervention.
