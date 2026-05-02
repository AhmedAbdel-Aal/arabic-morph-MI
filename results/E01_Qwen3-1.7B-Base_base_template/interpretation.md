# Interpretation

Run: `E01_Qwen3-1.7B-Base_base_template`  
Model: `Qwen/Qwen3-1.7B-Base`  
Input: isolated `base_form` words from `data/productivity_dataset.json`

## Summary

This first v2 run is a positive smoke-test result. Qwen3-1.7B encodes enough information in isolated word representations to recover Arabic root-pattern template labels well above chance, above the Hewitt-Liang word-type control task, and above a character n-gram baseline in every probe.

The strongest result is on nonce roots with held-out roots: the probe reaches 1.00 accuracy at layer 3, while the character n-gram baseline is 0.60 and the control task is 0.15 at the peak layer. This suggests that the model representation is not only memorizing real lexical items. It also carries productive template information for unseen nonce roots.

## Results By Probe

| Probe | Labels | Peak Layer | Probe Acc. | Control Acc. | Selectivity | Char N-Gram | Chance |
|---|---:|---:|---:|---:|---:|---:|---:|
| `real_templates_random` | 13 | 1 | 0.808 | 0.000 | 0.808 | 0.654 | 0.077 |
| `nonce_templates_random` | 5 | 2 | 0.950 | 0.150 | 0.800 | 0.300 | 0.200 |
| `nonce_templates_heldout_roots` | 5 | 3 | 1.000 | 0.150 | 0.850 | 0.600 | 0.200 |
| `train_real_test_nonce_overlap` | 5 | 2 | 0.710 | 0.260 | 0.450 | 0.580 | 0.200 |
| `train_nonce_test_real_overlap` | 5 | 4 | 0.880 | 0.300 | 0.580 | 0.780 | 0.200 |

## Main Reading

The real-template random probe reaches 0.808 on a 13-way task, compared with 0.654 for character n-grams. This is useful, but it is the least clean evidence because the random split can still exploit lexical and surface regularities in real Arabic words.

The nonce probes are more important. On nonce random split, Qwen reaches 0.950 while n-grams reach only 0.300. On nonce held-out roots, Qwen reaches 1.000 while n-grams reach 0.600. The held-out-root result is especially relevant because the test roots are unseen during probe training.

The transfer probes are the best first test of real/nonce alignment. Training on real words and testing on nonce words reaches 0.710, above n-grams at 0.580. Training on nonce and testing on real reaches 0.880, above n-grams at 0.780. The asymmetry is expected: real-to-nonce is harder because the real overlap subset has only 50 training examples, while nonce-to-real trains on 100 examples.

## Confusions

The real-to-nonce transfer probe shows the clearest failure mode. `استفعل`, `فاعل`, and `مفعول` transfer well. The main weakness is `فعول`, where many examples are predicted as `مفعول`; this is plausible because both include a long `و`, and `مفعول` adds a salient `م` prefix that can attract related representations.

The nonce-to-real transfer probe is cleaner. `استفعل`, `فاعل`, and `مفعول` are perfect in the confusion matrix. Remaining errors mostly involve `فعول` being predicted as `فاعل`, and a smaller number of `فعال` examples being predicted as `فاعل`.

## Caveats

This is still an initial small-model run. Qwen3-1.7B is the development model, not the main comparison model for the study.

The base-form setup is intentionally clean: no affixed forms and no sentence context. It tests isolated word representations only.

The peak layers are early, mostly layers 1-4. This may mean the signal is strongly morpho-orthographic rather than deeply semantic. That is not a flaw, but it should shape the claim: the current evidence supports recoverable root-pattern information in the representation, not necessarily abstract grammatical reasoning.

## Next Step

Run the same setup on `Qwen/Qwen3-8B`, then Fanar and ALLaM. If the same pattern holds across Arabic-centric models and remains above both control and n-gram baselines, the result becomes much stronger.
