# Results Log

## 2026-05-02: `E01_Qwen3-1.7B-Base_base_template`

Model: `Qwen/Qwen3-1.7B-Base`  
Dataset: `data/productivity_dataset.json`  
Input: isolated base forms  
Output folder: `results/E01_Qwen3-1.7B-Base_base_template`

This is the first v2 smoke-test run on the Alakeel productivity dataset. It uses isolated base forms and runs five template-probing experiments: real random split, nonce random split, nonce held-out roots, real-to-nonce transfer, and nonce-to-real transfer.

Summary:

| Probe | Peak Acc. | Control Acc. | Selectivity | N-Gram Acc. | Chance |
|---|---:|---:|---:|---:|---:|
| real templates random | 0.808 | 0.000 | 0.808 | 0.654 | 0.077 |
| nonce templates random | 0.950 | 0.150 | 0.800 | 0.300 | 0.200 |
| nonce templates held-out roots | 1.000 | 0.150 | 0.850 | 0.600 | 0.200 |
| train real, test nonce | 0.710 | 0.260 | 0.450 | 0.580 | 0.200 |
| train nonce, test real | 0.880 | 0.300 | 0.580 | 0.780 | 0.200 |

Interpretation: the run is positive. Qwen3-1.7B beats chance, the Hewitt-Liang word-type control task, and character n-gram baselines in all probes. The strongest evidence is the nonce held-out-root result, where the model reaches perfect accuracy at the peak layer. Treat this as development evidence before running the main model set.

## 2026-05-02: `E02_Qwen3-1.7B-Base_base_template_root`

Model: `Qwen/Qwen3-1.7B-Base`  
Dataset: `data/productivity_dataset.json`  
Input: isolated base forms  
Output folder: `results/E02_Qwen3-1.7B-Base_base_template_root`

This run extends the first v2 run by adding root probes in addition to template probes.

Summary:

| Probe | Target | Peak Acc. | Control Acc. | Selectivity | N-Gram Acc. | Chance |
|---|---|---:|---:|---:|---:|---:|
| real templates random | template | 0.808 | 0.000 | 0.808 | 0.654 | 0.077 |
| nonce templates random | template | 0.950 | 0.150 | 0.800 | 0.300 | 0.200 |
| nonce templates held-out roots | template | 1.000 | 0.150 | 0.850 | 0.600 | 0.200 |
| train real, test nonce | template | 0.710 | 0.260 | 0.450 | 0.580 | 0.200 |
| train nonce, test real | template | 0.880 | 0.300 | 0.580 | 0.780 | 0.200 |
| real roots random | root | 0.524 | 0.000 | 0.524 | 0.095 | 0.048 |
| nonce roots random | root | 1.000 | 0.050 | 0.950 | 0.950 | 0.050 |
| nonce roots held-out templates | root | 1.000 | 0.100 | 0.900 | 0.950 | 0.050 |

Interpretation: template probing remains the main positive morphology result because Qwen beats n-grams and control tasks across nonce and transfer settings. Root identity is also highly decodable, but the nonce-root n-gram baseline is already 0.95, so root recoverability is mostly surface-solvable in this dataset.

## 2026-05-03: `E03`

Model: `Qwen/Qwen3-1.7B-Base`  
Dataset: `data/productivity_dataset.json`  
Input: isolated base forms  
Pooling: last token  
Output folder: `results/E03`

This run reproduces E02 with tokenization and representation diagnostics.

Summary:

- Probe metrics reproduce E02.
- 213 out of 230 unique strings are multi-token.
- Layer 0 weakness is likely partly caused by last-token pooling in a causal decoder: at layer 0, the final subword cannot yet attend to previous subwords.
- Layers 3-20 show severe activation outlier / dimensional-collapse behavior in Qwen3-1.7B: 90-95% variance is captured by one component.

Interpretation: the early-layer morphology spike is real in the probe curves, but E03 shows it must be interpreted through tokenization and representation geometry. The next required check is pooling ablation: last vs first vs mean.

## 2026-05-03: `E04a`

Model: `Qwen/Qwen3-1.7B-Base`  
Dataset: `data/productivity_dataset.json`  
Input: isolated base forms  
Pooling: first token  
Output folder: `results/E04a`

This run is the first-subword pooling ablation.

Summary:

- First pooling is much weaker than last pooling on almost every important probe.
- Template probes drop sharply: nonce random templates fall from 0.950 to 0.400, and nonce held-out-root templates fall from 1.000 to 0.650.
- Root probing shows the strongest collapse: nonce held-out-template root probing falls from 1.000 to 0.100.
- This supports the interpretation that last-token pooling gives a composed word representation in a causal decoder, while first-token pooling often sees only a partial prefix/subword.

Interpretation: E04a does not invalidate E03. It clarifies that the successful E03 representation depends on extracting a vector that can aggregate over subword pieces. Mean pooling is the next required ablation.
