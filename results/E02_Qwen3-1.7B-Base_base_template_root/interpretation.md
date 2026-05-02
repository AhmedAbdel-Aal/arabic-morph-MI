# Interpretation

Run: `E02_Qwen3-1.7B-Base_base_template_root`  
Model: `Qwen/Qwen3-1.7B-Base`  
Input: isolated `base_form` words from `data/productivity_dataset.json`

## Summary

This run extends the first v2 experiment by adding root probes. The template results reproduce the earlier positive pattern: Qwen3-1.7B recovers Arabic root-pattern templates above chance, above the Hewitt-Liang word-type control, and above the character n-gram baseline.

The new root probes show that root identity is highly decodable, especially on nonce forms. However, the root result is less surprising than the template result because Arabic roots are largely visible in the surface consonants. The character n-gram baseline is also very high for nonce-root probes, reaching 0.95. So the root probes confirm that root identity is present in the representation, but they do not yet prove that the model adds much beyond surface spelling.

## Results By Probe

| Probe | Target | Labels | Peak Layer | Probe Acc. | Control Acc. | Selectivity | Char N-Gram | Chance |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `real_templates_random` | template | 13 | 1 | 0.808 | 0.000 | 0.808 | 0.654 | 0.077 |
| `nonce_templates_random` | template | 5 | 2 | 0.950 | 0.150 | 0.800 | 0.300 | 0.200 |
| `nonce_templates_heldout_roots` | template | 5 | 3 | 1.000 | 0.150 | 0.850 | 0.600 | 0.200 |
| `train_real_test_nonce_overlap` | template | 5 | 2 | 0.710 | 0.260 | 0.450 | 0.580 | 0.200 |
| `train_nonce_test_real_overlap` | template | 5 | 4 | 0.880 | 0.300 | 0.580 | 0.780 | 0.200 |
| `real_roots_random` | root | 21 | 5 | 0.524 | 0.000 | 0.524 | 0.095 | 0.048 |
| `nonce_roots_random` | root | 20 | 2 | 1.000 | 0.050 | 0.950 | 0.950 | 0.050 |
| `nonce_roots_heldout_templates` | root | 20 | 1 | 1.000 | 0.100 | 0.900 | 0.950 | 0.050 |

## Template Probes

The template probes remain the main evidence for derivational morphology. The strongest template result is `nonce_templates_heldout_roots`, where the model reaches 1.00 accuracy at layer 3. This is important because the probe is tested on roots that were not seen during training.

The two transfer probes are also positive. Training on real words and testing on nonce words reaches 0.710, above the n-gram baseline of 0.580. Training on nonce words and testing on real words reaches 0.880, above the n-gram baseline of 0.780. This suggests that the representation aligns real and nonce template structure to some degree.

## Root Probes

The real-root probe is only a diagnostic. The real dataset has many roots that occur once, so this probe uses only roots with at least two examples. That leaves 45 items and 21 root labels. The model reaches 0.524, which is well above chance, while n-grams are only 0.095. This is encouraging but not a strong final claim because the split is small and sparse.

The nonce-root probes are much cleaner structurally: 20 roots across 5 templates. The model reaches 1.00 on both random and held-out-template nonce-root probes. But the n-gram baseline is 0.95 in both cases. That means root identity is almost solved by character spelling alone. This is expected: the nonce root consonants remain visible across templates.

So the root result should be phrased carefully:

```text
Root identity is strongly recoverable from Qwen representations, but for this dataset it is also strongly recoverable from surface form.
```

## Main Interpretation

The template probes are the more interesting morphology result because templates are not simply a fixed consonant string. Qwen beats n-grams by large margins on nonce template classification, especially in the random split. It also beats n-grams in the held-out-root and real/nonce transfer settings.

The root probes behave differently. They confirm that root information is present, but they also show that root identity is mostly available from the visible letters. This is not a negative result. It tells us that future root-probing claims must be framed as root recoverability, not necessarily abstract root representation beyond spelling.

## Layer Pattern

The best layers are early: layers 1-5. This points to a strong morpho-orthographic signal. Later layers often remain above chance but usually decline from the early peak. For this first model, the morphology signal appears most linearly accessible near the bottom of the network.

## Next Step

Run the same full experiment on `Qwen/Qwen3-8B`, `QCRI/Fanar-1-9B`, and `humain-ai/ALLaM-7B-Instruct-preview`. The key comparison should focus on:

- template held-out roots
- real-to-nonce template transfer
- nonce-to-real template transfer
- nonce root held-out templates, interpreted together with the n-gram baseline
