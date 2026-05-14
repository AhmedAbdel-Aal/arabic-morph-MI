# Representation Analysis

This folder contains local CPU analyses over saved pooled hidden representations from RunPod.

Inputs:

- `results/REP01_*/hidden_representations.npz`
- matching `results/REP01_*/results.json`
- `data/productivity_dataset.json`

Outputs are organized as:

- `results/00_anisotropy/`: explicit layer-wise anisotropy analysis
- `results/01_geometry/`: anisotropy, effective rank, edim90, pairwise cosine
- `results/02_probe_geometry/`: layer-wise probe accuracy joined with geometry metrics
- `results/03_pc_removal/`: probe robustness after removing top PCA directions
- `results/04_variance_decomposition/`: label variance and what the dominant PC tracks
- `results/05_centroid_alignment/`: real-vs-nonce template centroid alignment without a classifier
- `results/06_affix_invariance/`: whether base words stay close to their affixed variants
- `results/07_layer_concordance/`: layer-level synthesis of transfer, centroid alignment, and nuisance metrics

The goal is exploratory: decide whether template recoverability is robust, whether it aligns real and nonce forms geometrically, and whether dominant directions are carrying morphology or nuisance/domain structure.
