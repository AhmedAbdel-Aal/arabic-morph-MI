# Data Audit Status

Current source:

```text
Arabic Billion Words / Almasryalyoum
```

Current broad extraction:

```text
data_generation/runs/abw_10k_broad/
```

Counts:

```text
sentences: 10,000
token-level candidates: 34,489
type-level candidates: 6,599
```

The type-level view now preserves one example CAMEL analysis per item, including pattern, lex, gloss, source, and ambiguity.

## Audit Preparation

Prepared audit files:

```text
data_generation/runs/abw_10k_audit_v1/type_level_audit_prep.jsonl
data_generation/runs/abw_10k_audit_v1/audit_sample_500.jsonl
data_generation/runs/abw_10k_audit_v1/audit_prep_report.json
```

Audit-prep distribution:

```text
high_review:   2,521
medium_review: 3,961
low_review:      117
```

Suggested morphology classes:

```text
target_active_participle:         881
target_passive_participle:        390
target_form_viii_participle:      228
target_form_x_verb:                77
target_form_vii_verb:              59
target_verbal_noun:             1,076
target_intensive_adjective:       397
target_instrument_noun:            13
proper_name_or_place:               6
unsure:                         3,472
```

The 500-row sample is balanced by audit bucket:

```text
high_review:   200
medium_review: 200
low_review:    100
```

## Conservative Seed

A narrow seed dataset was produced here:

```text
data_generation/runs/abw_10k_audit_v1/conservative_seed/main_target_seed.jsonl
data_generation/runs/abw_10k_audit_v1/conservative_seed/productivity_dataset_seed.json
```

Seed size:

```text
accepted rows: 114
unique roots: 58
templates: استفعل, انفعل
```

This seed only accepts derived-verb rows where CAMEL and the tagger agree on a verb reading, ambiguity is below 10, and no name/place signal was found. It is intentionally conservative and is not the final dataset.

## Curated Batch 001

A first diversified accepted batch was produced here:

```text
data_generation/runs/abw_10k_audit_v1/curated_batch_001/accepted_batch_001.jsonl
data_generation/runs/abw_10k_audit_v1/curated_batch_001/productivity_dataset_batch_001.json
data_generation/runs/abw_10k_audit_v1/curated_batch_001/batch_001_report.json
```

Batch size:

```text
accepted rows: 625
unique roots: 163
target templates: 12/13
target base families: 215
```

Accepted rows by template:

```text
استفعل: 62
افتعال: 119
انفعل: 52
فاعل: 43
فعال: 27
فعالة: 71
فعلاء: 32
فعول: 41
فعيل: 39
مفتعل: 66
مفعال: 6
مفعول: 67
```

The batch is rule-assisted but intentionally explicit: accepted rows come from a hand-written base-form allowlist per target pattern class, and rows with POS mismatch, high CAMEL ambiguity, obvious nisba/template mismatch, CAMEL-pattern mismatch, target-class/POS incompatibility, or explicit primitive lexical exclusions are not accepted.

The latest review removed context and analysis failures that had passed earlier rules:

```text
مصباح قطب      -> proper name in context, not instrument noun
وسليمان سعد    -> proper name in context, not فعيل adjective
محيي الدين الغريب -> family name in context, not target adjective
للعالمين       -> عالَم "world", not فاعِل active participle
وشاهدت/وشاهدوا -> verbs, not active participles
```

The later review also removed `صالح` from the active-participle allowlist in this pilot batch. The observed rows were fixed expressions such as `لصالح الفريق` and `للصالح العام`, which are better treated as lexicalized expressions than clean active-participle examples.

The broken-plural/verbal-noun pass removed additional context failures:

```text
بكتابه          -> singular "his book", not كتاب "writers"
بالكتاب والسنة  -> singular/fixed religious expression, not كتاب "writers"
انتصار حسين    -> person name, not verbal noun "victory"
ببلاده          -> context is "his country" but CAMEL selected بلادة "stupidity"
```

`فعلان` is not present in this strict batch. The Almasryalyoum sample contains `فعلان` candidates, but the clean candidates are mostly colloquial, named-entity-like, dual/plural artifacts, POS mismatches, or high-ambiguity forms. Do not force them into the clean batch; fill this class from additional sources or targeted manual review.

## Family-Balanced View

A stricter Akeel-style family view was produced here:

```text
data_generation/runs/abw_10k_audit_v1/family_balanced_001/family_balanced_rows.jsonl
data_generation/runs/abw_10k_audit_v1/family_balanced_001/productivity_dataset_family_balanced_001.json
data_generation/runs/abw_10k_audit_v1/family_balanced_001/family_balanced_report.json
```

Family-balanced size:

```text
selected rows: 198
selected families: 66
unique roots: 57
templates: استفعل, افتعال, انفعل, مفتعل, مفعال, مفعول
```

This view requires one unaffixed base row plus two affixed variants per root-template-base family. Many otherwise valid noun/adjective families are incomplete in this single 10k-sentence source sample because only affixed or only unaffixed variants appear.

## Second-Pass Review 001

A reviewer pass was added on top of `curated_batch_001`:

```text
data_generation/runs/abw_10k_audit_v1/review_pass_001/
```

This pass labels every accepted row with explicit review flags and separates the immediately usable low-risk subset from rows that still need item-level review.

Current counts:

```text
input rows:        625
low-risk rows:    519
review queue:     106
manual decisions: 106 total
accepted after review decisions: 623
rejected after review decisions:   2
remaining review queue:            0
```

Current best reviewed pilot export:

```text
data_generation/runs/abw_10k_audit_v1/review_pass_001/decision_applied_002/productivity_dataset_reviewed.json
```

The manual accepts include context-valid homograph cases where CAMEL selected an incorrect lexical reading, but the sentence supports the intended target word:

```text
الدراسة / للدراسة / بالدراسة / بدراستها
مبتكرة / المبتكرين / والمبتكرين
```

Two rows were rejected after second-pass review:

```text
وخادم       -> lexicalized honorific title: خادم الحرمين
بالمرصاد   -> lexicalized fixed expression
```

## Multi-Source Interim State

The available priority ABW sources `Alittihad`, `Sabanews`, and `Techreen` have been sampled, extracted, merged with the Almasryalyoum pilot, and reviewed.
`Alqabas` and `Ryiadh` were attempted but are currently unavailable through the HF mirror/original archive path in this environment.

Current multi-source handoff:

```text
data_generation/runs/abw_multisource_v1/audit_v1/review_pass_001/decision_applied_001/productivity_dataset_reviewed.json
```

Counts:

```text
accepted rows: 799
rejected rows: 2
remaining review queue: 0
roots: 195
templates: 12
sources: Alittihad + Almasryalyoum + Sabanews + Techreen
```

Current multi-source family-balanced handoff:

```text
data_generation/runs/abw_multisource_v1/audit_v1/review_pass_001/decision_applied_001/family_balanced/productivity_dataset_family_balanced_reviewed.json
```

Counts:

```text
rows: 276
families: 92
roots: 75
templates: 6
```

See:

```text
data_generation/MULTISOURCE_HANDOFF.md
```

The major coverage issue remains `فعلان`: the combined raw candidate pool has `فعلان=246` type rows, but none have survived into the reviewed accepted dataset.

A focused `فعلان` audit was produced here:

```text
data_generation/runs/abw_multisource_v1/audit_v1/f3lan_audit/f3lan_audit_report.md
data_generation/runs/abw_multisource_v1/audit_v1/f3lan_audit/f3lan_audit_summary.json
data_generation/runs/abw_multisource_v1/audit_v1/f3lan_audit/f3lan_audit_decisions.csv
```

Focused audit result:

```text
فعلان type rows audited: 246
accepted: 0
rejected: 246
pos distribution: adj=32, noun=198, verb=16
```

Conclusion: do not add `فعلان` from the current four-source pool. The apparent candidates are mostly nisba forms, proper names/places, lexical nouns, colloquial rows, or analysis artifacts.

## Echoroukonline v2 Expansion

`Echoroukonline` was sampled after the four-source handoff and tracked separately:

```text
data_generation/V2_ECHOROUK_EXPANSION.md
```

Key result:

```text
source type rows: 6,712
source raw فعلان type rows: 118
source audited clean فعلان rows: 0
v2 curated accepted rows before decisions: 841
v2 explicit review decisions: 137
v2 accepted after decisions: 831
v2 rejected after decisions: 10
v2 remaining review queue: 0
v2 reviewed family-balanced rows: 306
```

Current best reviewed handoff:

```text
data_generation/runs/abw_multisource_v2/audit_v1/review_pass_001/decision_applied_001/productivity_dataset_reviewed.json
```

Current best family-balanced handoff:

```text
data_generation/runs/abw_multisource_v2/audit_v1/review_pass_001/decision_applied_001/family_balanced/productivity_dataset_family_balanced_reviewed.json
```

Judgment: v2 is now better than v1 for experiments that must stay natural-source only, because it adds Echoroukonline breadth and has zero remaining review queue.

## v3 Controlled فعلان Handoff

Because natural-source `فعلان` stayed noisy after focused audits, a small controlled supplement was added without weakening the ABW audit:

```text
data_generation/runs/controlled_f3lan_v1/accepted_controlled_f3lan.jsonl
```

The controlled rows are manually written MSA contexts and are accepted only when CAMEL and the local root-template matcher agree on the intended root and `فعلان` template.

Current best all-template handoff:

```text
data_generation/runs/abw_multisource_v3_controlled_f3lan/productivity_dataset_reviewed_with_controlled_f3lan.json
```

Current best all-template family-balanced handoff:

```text
data_generation/runs/abw_multisource_v3_controlled_f3lan/family_balanced/productivity_dataset_family_balanced_with_controlled_f3lan.json
```

Counts:

```text
v3 rows: 849
v3 roots: 211
v3 templates: 13
v3 controlled فعلان rows: 18
v3 family-balanced rows: 324
v3 family-balanced families: 108
```

See:

```text
data_generation/V3_CONTROLLED_F3LAN_HANDOFF.md
```

## Next Work

The current balanced all-template probing file is:

```text
data_generation/runs/balanced50_v1/productivity_dataset_balanced50.json
```

Balanced50 v1 contains 650 real contextual rows: 13 templates with exactly 50 rows per template. It uses reviewed natural rows first and controlled CAMEL-validated rows only to fill template deficits.

See:

```text
data_generation/BALANCED50_HANDOFF.md
```

Important reporting caveat: `فعلان` is fully controlled and `مفعال` is mostly controlled in Balanced50 v1, so analyses for these templates should be reported as controlled-source-sensitive.

1. For natural-source-only experiments, use v2 and explicitly report that `فعلان` is absent.
2. For balanced all-template experiments, use Balanced50 v1 and explicitly report the controlled source counts.
3. If more disk or a remote machine is available, retry remaining HF sources (`Almustaqbal`, `SaudiYoum`, `Youm7`) and only replace controlled rows if clean natural-source rows survive the same audit.
4. Keep accepted `primitive_lexical` rows separate as a secondary/control dataset.
