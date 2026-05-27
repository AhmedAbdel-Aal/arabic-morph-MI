# V3 Handoff: Reviewed ABW + Controlled فعلان

This is the current best experiment handoff if we want all 13 target templates represented.

## Why v3 Exists

The reviewed ABW v2 dataset is clean and fully audited, but natural-source `فعلان` remained absent after focused audits:

```text
v1 four-source فعلان audit: 246 type rows, 0 accepted
Echoroukonline فعلان audit: 118 type rows, 0 accepted
```

The natural candidates were mostly nouns, verbs, nisba forms, proper names/places, colloquial rows, or analysis artifacts. Rather than weakening the audit, v3 adds a small controlled supplement.

## Main Dataset

```text
data_generation/runs/abw_multisource_v3_controlled_f3lan/productivity_dataset_reviewed_with_controlled_f3lan.json
```

Counts:

```text
rows: 849
roots: 211
templates: 13
missing sentence fields: 0
missing source_dataset fields: 0
```

Template counts:

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
فعلان: 18
مفعال: 7
```

Source counts:

```text
Alittihad: 410
Almasryalyoum: 196
Echoroukonline: 105
Techreen: 75
Sabanews: 45
controlled_manual:f3lan_v1: 18
```

## Family-Balanced Dataset

```text
data_generation/runs/abw_multisource_v3_controlled_f3lan/family_balanced/productivity_dataset_family_balanced_with_controlled_f3lan.json
```

Counts:

```text
rows: 324
families: 108
roots: 90
templates: 7
```

Family-balanced template counts:

```text
افتعال: 90
استفعل: 69
انفعل: 54
مفتعل: 48
مفعول: 42
فعلان: 18
مفعال: 3
```

## Controlled فعلان Supplement

```text
data_generation/runs/controlled_f3lan_v1/accepted_controlled_f3lan.jsonl
data_generation/runs/controlled_f3lan_v1/controlled_f3lan_report.json
```

Counts:

```text
rows: 18
roots: 6
families: 6
forms per family: base + ال-prefixed + و-prefixed
```

Base forms:

```text
عطشان
غضبان
سكران
نعسان
لهفان
فرحان
```

Acceptance rule:

```text
manual MSA context
CAMEL root agrees with intended root
local root-template matcher returns فعلان
source_dataset is controlled_manual:f3lan_v1
```

## Scientific Use

Use v3 when the experiment needs all 13 target templates represented.

Use v2 when the experiment must be strictly natural-source only:

```text
data_generation/runs/abw_multisource_v2/audit_v1/review_pass_001/decision_applied_001/productivity_dataset_reviewed.json
```

In analysis, always report whether `controlled_manual:f3lan_v1` is included. This lets us separate:

```text
natural-source result
natural-source + controlled فعلان result
```

This is the cleanest current compromise: we do not force noisy ABW `فعلان` rows into the dataset, but we also keep the planned template inventory testable.

