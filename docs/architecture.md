# Architecture & Automation

## Proposed production architecture

The local solution uses CSV seeds, DuckDB and dbt to keep the challenge reproducible and easy to run. In production, I would keep the same logical layer structure while replacing the local storage with the company's production data platform.

```text
External sources
CRM / tracking / CSV / APIs
        |
        v
RAW
Immutable source data
+ ingestion metadata
        |
        v
STAGING
Type conversion
Normalization
Basic data quality checks
        |
        v
INTERMEDIATE
Deduplication
Lead canonicalization
Conversion attribution
Business rules
        |
        v
MARTS
Lead-to-conversion
Monthly KPI
Customer view
        |
        v
BI / Analytics
```

For Netrisk's stack, this could map naturally to AWS for ingestion and storage, Snowflake as the analytical warehouse, and dbt for transformations, testing and documentation.

## Layer responsibilities

### Raw

The raw layer should preserve source data as received, without business transformations.

Typical metadata added during ingestion:

- ingestion timestamp;
- source system or file name;
- pipeline run ID;
- load date.

Keeping raw data immutable makes it possible to trace downstream results back to the original source.

### Staging

The staging layer standardizes source fields into consistent technical formats while preserving important raw values for traceability.

Examples from this challenge:

- normalize email casing and whitespace;
- standardize status casing;
- parse multiple date formats into a single date type;
- convert premium values with mixed decimal separators into numeric values;
- preserve raw source columns where useful for investigation.

### Intermediate

The intermediate layer contains reusable business logic that should not be repeated across marts.

In this solution it includes:

- conversion deduplication;
- lead canonicalization;
- conflict flags for duplicated lead IDs;
- conversion-to-lead attribution;
- fallback matching using normalized email and temporal logic;
- match method and match quality fields.

### Marts

The mart layer contains business-facing datasets with clearly defined grain and metrics.

This challenge produces:

- a lead-to-conversion mart with one row per canonical lead;
- a monthly KPI mart by vertical, source and lead month;
- a customer-level mart with one row per normalized customer email.

## Data quality

Data quality checks should sit as close as possible to the layer where the rule becomes valid.

Examples:

### Staging checks

- accepted values for status;
- successful date parsing;
- valid numeric premium parsing;
- required identifiers not null where expected.

### Intermediate checks

- unique conversion IDs after deduplication;
- one canonical row per lead ID;
- no duplicate conversion-to-lead attribution rows;
- match quality and match method consistency.

### Mart checks

- uniqueness of the declared business grain;
- non-negative counts;
- conversion rate between 0 and 1;
- one row per customer in the customer mart.

Critical failures should block downstream publication of unreliable marts. Lower-severity issues can be surfaced as warnings for monitoring and later investigation.

The project includes an executable dbt test:

`tests/assert_unique_conversion_ids.sql`

This verifies that duplicate conversion IDs found in the raw source do not propagate past the deduplication layer.

## Scheduling and failure handling

For this use case I would initially schedule the pipeline daily, after all expected source files or upstream loads have arrived.

A production run would follow this order:

```text
Ingest source data
        |
        v
Load raw data
        |
        v
Run staging models
        |
        v
Run intermediate models
        |
        v
Run data quality checks
        |
        v
Build marts
        |
        v
Publish to BI / analytics
```

If a critical step fails:

1. retain the previous successful mart tables;
2. stop downstream publication if a critical test fails;
3. alert the responsible data owner with the failing model, test and run metadata;
4. investigate using source data and lineage information;
5. rerun from the failed stage after the issue is corrected.

The frequency could later be increased from daily to intraday if business reporting SLAs require fresher data.

## Traceability and documentation

Traceability should be designed into the pipeline rather than added later.

I would use:

- immutable raw data;
- ingestion timestamps;
- source file or source system metadata;
- pipeline run IDs;
- dbt lineage;
- dbt model and column documentation;
- dbt test results;
- Git history and pull requests;
- explicit business-rule fields in transformed data.

For example, this solution exposes fields such as:

- `match_method`;
- `match_quality`;
- `was_duplicated`;
- `has_attribute_conflict`.

These fields make it easier for both engineers and business users to understand how records were produced and where uncertainty exists.

## Production implementation

A production implementation for Netrisk could use:

```text
AWS / source systems
        |
        v
Snowflake raw layer
        |
        v
dbt staging
        |
        v
dbt intermediate
        |
        v
dbt marts
        |
        v
Power BI / other BI tooling
```

Airflow, dbt Cloud or Netrisk's existing orchestration platform could schedule and monitor the pipeline.

The main principle would be to keep ingestion, normalization, business logic and reporting layers clearly separated so that KPI definitions and data quality rules remain reusable and consistent across subsidiaries.
