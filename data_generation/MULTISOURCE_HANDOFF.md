# Multi-Source Interim Handoff

This document records the current reviewed multi-source state.
It is an interim dataset, not the final large dataset, because the source pool still has an audited `فعلان` coverage gap.

## Sources Included

```text
oserikov/arabic_billion_words:Almasryalyoum
oserikov/arabic_billion_words:Alittihad
oserikov/arabic_billion_words:Sabanews
oserikov/arabic_billion_words:Techreen
```

`Alittihad` was sampled and extracted as:

```text
data_generation/runs/abw_multisource_v1/sources/Alittihad/sentences.jsonl
data_generation/runs/abw_multisource_v1/sources/Alittihad/candidates.jsonl
data_generation/runs/abw_multisource_v1/sources/Alittihad/views/type_level.jsonl
```

The same source-local structure exists for:

```text
data_generation/runs/abw_multisource_v1/sources/Sabanews/
data_generation/runs/abw_multisource_v1/sources/Techreen/
```

Alittihad source-gate counts:

```text
sentences: 10,000
token candidates: 33,231
type candidates: 6,554
unique roots: 1,004
فعلان type candidates: 99
مفعال type candidates: 16
family-ready groups: 666
recommendation: merge_candidate_pool_after_audit
```

Sabanews source-gate counts:

```text
sentences: 10,000
token candidates: 38,064
type candidates: 5,464
unique roots: 815
فعلان type candidates: 74
مفعال type candidates: 13
family-ready groups: 518
recommendation: merge_candidate_pool_after_audit
```

Techreen source-gate counts:

```text
sentences: 10,000
token candidates: 28,791
type candidates: 7,012
unique roots: 1,059
فعلان type candidates: 119
مفعال type candidates: 31
family-ready groups: 701
recommendation: merge_candidate_pool_after_audit
```

Currently unavailable:

```text
Alqabas: HF mirror 404; original URL returned HTML instead of RAR.
Ryiadh: HF mirror unavailable; original URL returned HTML instead of RAR.
```

## Combined Candidate Pool

```text
data_generation/runs/abw_multisource_v1/combined/candidates.jsonl
data_generation/runs/abw_multisource_v1/combined/views/type_level.jsonl
```

Combined counts:

```text
token candidates: 134,575
type candidates: 13,685
فعلان type candidates: 246
مفعال type candidates: 43
```

## Reviewed Multi-Source Dataset

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
missing sentence fields: 0
missing source fields: 0
```

Source distribution:

```text
Alittihad: 426
Almasryalyoum: 204
Techreen: 101
Sabanews: 68
```

Template distribution:

```text
افتعال: 120
استفعل: 117
انفعل: 97
فعالة: 89
مفتعل: 75
مفعول: 70
فعلاء: 48
فعيل: 48
فاعل: 47
فعول: 44
فعال: 36
مفعال: 8
```

Rejected after second-pass review:

```text
وخادم       فاعل   rejected as lexicalized honorific title: خادم الحرمين
بالمرصاد   مفعال  rejected as lexicalized fixed expression
```

## Family-Balanced Multi-Source Dataset

```text
data_generation/runs/abw_multisource_v1/audit_v1/review_pass_001/decision_applied_001/family_balanced/productivity_dataset_family_balanced_reviewed.json
```

Counts:

```text
rows: 276
families: 92
roots: 75
templates: 6
missing sentence fields: 0
missing source fields: 0
```

Source distribution:

```text
Alittihad: 160
Almasryalyoum: 75
Techreen: 28
Sabanews: 13
```

## Scientific Judgment

The multi-source dataset is cleaner and more diverse than the Almasryalyoum-only pilot.
It improves row count, root count, and family-balanced families.

However, it still has a major coverage issue:

```text
Raw combined candidates include فعلان=246.
Reviewed accepted dataset still has no clean فعلان row.
```

A focused audit was added here:

```text
data_generation/runs/abw_multisource_v1/audit_v1/f3lan_audit/f3lan_audit_report.md
data_generation/runs/abw_multisource_v1/audit_v1/f3lan_audit/f3lan_audit_decisions.csv
data_generation/runs/abw_multisource_v1/audit_v1/f3lan_audit/f3lan_audit_decisions.jsonl
data_generation/runs/abw_multisource_v1/audit_v1/f3lan_audit/f3lan_audit_summary.json
```

The audit reviewed all 246 `فعلان` type rows:

```text
accepted: 0
rejected: 246
pos distribution: adj=32, noun=198, verb=16
```

The apparent candidates are mostly nisba forms such as `عقلاني` and `عمراني`, proper names/places such as `عجلان`, `فرحان`, `الفردان`, and `نبهان`, lexical nouns such as `فلتان`, or colloquial-register rows such as `زعلانين`.

This means the next sources or a targeted construction pass are still necessary if `فعلان` must be represented. Do not weaken the audit just to force `فعلان`.

Possible later sources:

```text
Almustaqbal
SaudiYoum
Youm7
Echoroukonline
```

`Echoroukonline` has since been sampled, tested, audited, and promoted in a separate v2 expansion run. See:

```text
data_generation/V2_ECHOROUK_EXPANSION.md
```

Summary: it adds useful breadth and improves the family-balanced candidate view, but its 118 audited `فعلان` rows still yield zero clean accepted `فعلان` examples.

Current best reviewed v2 handoff:

```text
data_generation/runs/abw_multisource_v2/audit_v1/review_pass_001/decision_applied_001/productivity_dataset_reviewed.json
```

Current best reviewed v2 family-balanced handoff:

```text
data_generation/runs/abw_multisource_v2/audit_v1/review_pass_001/decision_applied_001/family_balanced/productivity_dataset_family_balanced_reviewed.json
```

v2 counts:

```text
accepted reviewed rows: 831
rejected reviewed rows: 10
remaining review queue: 0
roots: 205
templates: 12
sources: 5
```

For experiments that need all 13 target templates, use the v3 handoff with a controlled `فعلان` supplement:

```text
data_generation/V3_CONTROLLED_F3LAN_HANDOFF.md
data_generation/runs/abw_multisource_v3_controlled_f3lan/productivity_dataset_reviewed_with_controlled_f3lan.json
```

v3 counts:

```text
accepted rows: 849
roots: 211
templates: 13
controlled فعلان rows: 18
missing sentence/source fields: 0
```

The controlled rows are marked with:

```text
source_dataset=controlled_manual:f3lan_v1
```

Report analyses both with and without this controlled source when `فعلان` matters.

## Balanced50 v1

For the next probing round, use the balanced all-template export:

```text
data_generation/runs/balanced50_v1/productivity_dataset_balanced50.json
```

Counts:

```text
rows: 650
templates: 13
rows per template: 50
roots: 215
nonce rows: 0
```

Balanced50 v1 selects from the reviewed v3 rows first, then adds controlled CAMEL-validated rows only where a template has fewer than 50 rows. It is the current experiment-ready file for fair cross-template probing.

See:

```text
data_generation/BALANCED50_HANDOFF.md
```

After each later source:

```text
sample sentences
extract candidates
make views
run source_expansion_summary
merge only useful source pools
rerun audit prep, curated selection, second-pass review, and explicit decisions
```
