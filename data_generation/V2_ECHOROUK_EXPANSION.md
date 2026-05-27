# Echoroukonline Expansion Notes

This records the first post-v1 source expansion attempt.

## Source

```text
oserikov/arabic_billion_words:Echoroukonline
```

Sampled output:

```text
data_generation/runs/abw_multisource_v1/sources/Echoroukonline/sentences.jsonl
```

Extraction output:

```text
data_generation/runs/abw_multisource_v1/sources/Echoroukonline/candidates.jsonl
data_generation/runs/abw_multisource_v1/sources/Echoroukonline/views/type_level.jsonl
```

Counts:

```text
sentences: 10,000
token candidates: 36,390
type candidates: 6,712
unique roots: 957
family-ready groups: 699
raw فعلان type rows: 118
raw مفعال type rows: 20
```

Source-gate recommendation:

```text
merge_candidate_pool_after_audit
```

## Focused فعلان Check

Focused audit:

```text
data_generation/runs/abw_multisource_v1/sources/Echoroukonline/audit/f3lan_audit/f3lan_audit_report.md
```

Result:

```text
فعلان rows audited: 118
accepted: 0
rejected: 118
```

Judgment: Echoroukonline does not solve the clean `فعلان` gap. The apparent candidates are again nouns, verbs, nisba forms, and proper names such as `عبد الرحمان`, `عمراني`, `علماني`, and `فرحان`.

## v2 Candidate Pool

A separate v2 pool was created so v1 remains intact:

```text
data_generation/runs/abw_multisource_v2/combined/candidates.jsonl
data_generation/runs/abw_multisource_v2/combined/views/type_level.jsonl
```

Merged sources:

```text
Almasryalyoum
Alittihad
Sabanews
Techreen
Echoroukonline
```

Combined counts:

```text
token candidates: 170,965
type candidates: 15,370
```

Curated selector output:

```text
data_generation/runs/abw_multisource_v2/audit_v1/curated_batch_001/accepted_batch_001.jsonl
```

Counts:

```text
accepted curated rows: 841
rejected rows: 76
```

Accepted curated rows by source:

```text
Alittihad: 413
Almasryalyoum: 197
Echoroukonline: 110
Techreen: 76
Sabanews: 45
```

Second-pass review:

```text
data_generation/runs/abw_multisource_v2/audit_v1/review_pass_001/
```

Counts:

```text
all reviewed rows: 841
low-risk rows: 704
review queue: 137
```

The review queue was audited and explicit decisions were applied:

```text
data_generation/runs/abw_multisource_v2/audit_v1/review_pass_001/manual_review_decisions_001.jsonl
data_generation/runs/abw_multisource_v2/audit_v1/review_pass_001/decision_applied_001/productivity_dataset_reviewed.json
```

Decision counts:

```text
accepted after review: 831
rejected after review: 10
remaining review queue: 0
```

Accepted reviewed rows by source:

```text
Alittihad: 410
Almasryalyoum: 196
Echoroukonline: 105
Techreen: 75
Sabanews: 45
```

Accepted reviewed rows by template:

```text
استفعل: 138
افتعال: 120
انفعل: 108
فعالة: 91
مفتعل: 78
مفعول: 69
فاعل: 48
فعلاء: 48
فعيل: 46
فعول: 44
فعال: 34
مفعال: 7
```

Rejected rows:

```text
وخادم       -> خادم الحرمين honorific title
فسابقي      -> false surface/analysis artifact
لكتاب       -> singular book/culture context, not writers
الكتاب      -> singular book context, not writers
لشقيقتها    -> kinship noun "her sister", not adjective target
وصغير       -> person name in list
لكريم       -> person name
بالمرصاد   -> fixed expression
ومفتاح      -> person name
مجروحة      -> fixed expression: شهادتي فيها مجروحة
```

Family-balanced reviewed v2:

```text
data_generation/runs/abw_multisource_v2/audit_v1/review_pass_001/decision_applied_001/family_balanced/productivity_dataset_family_balanced_reviewed.json
```

Counts:

```text
rows: 306
families: 102
roots: 84
```

## Judgment

Echoroukonline is useful for breadth and family coverage, but it does not fix the missing `فعلان` target class. After the v2 review queue was audited, v2 becomes the current best reviewed handoff for experiments that do not require `فعلان`.

Previous safest v1 dataset:

```text
data_generation/runs/abw_multisource_v1/audit_v1/review_pass_001/decision_applied_001/productivity_dataset_reviewed.json
```

Current best reviewed v2 dataset:

```text
data_generation/runs/abw_multisource_v2/audit_v1/review_pass_001/decision_applied_001/productivity_dataset_reviewed.json
```

Current best reviewed v2 family-balanced dataset:

```text
data_generation/runs/abw_multisource_v2/audit_v1/review_pass_001/decision_applied_001/family_balanced/productivity_dataset_family_balanced_reviewed.json
```

Remaining limitation: `فعلان` remains absent after focused audits of both v1 and Echoroukonline.
