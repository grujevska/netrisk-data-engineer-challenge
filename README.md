# Netrisk Data Engineer Candidate Challenge

## Overview

This project builds a clean and reproducible data model from two raw CSV datasets:

- `leads.csv` — lead interactions with comparison calculators
- `conversions.csv` — contracts linked to leads

The solution focuses on:

- profiling and documenting data quality issues;
- cleaning and standardizing inconsistent source data;
- resolving duplicate and unreliable identifiers;
- attributing conversions to leads;
- producing business-facing KPI and customer-level models;
- adding executable data quality checks;
- outlining how the solution could be automated in production.

The local implementation uses:

- Python / pandas for profiling;
- DuckDB as a lightweight local analytical database;
- dbt for transformations, testing and model structure.

The same logical design could be deployed to Snowflake and integrated with Netrisk's AWS/dbt data platform.

---

## Project structure

```text
netrisk-data-engineer-challenge/
│
├── README.md
├── dbt_project.yml
├── profiles.yml
│
├── seeds/
│   ├── leads.csv
│   └── conversions.csv
│
├── scripts/
│   └── profile_data.py
│
├── models/
│   ├── staging/
│   │   ├── stg_leads.sql
│   │   └── stg_conversions.sql
│   │
│   ├── intermediate/
│   │   ├── int_conversions_deduplicated.sql
│   │   ├── int_leads_canonical.sql
│   │   └── int_conversion_attribution.sql
│   │
│   └── marts/
│       ├── mart_lead_conversion.sql
│       ├── mart_monthly_conversion_kpi.sql
│       └── mart_customer.sql
│
├── tests/
│   └── assert_unique_conversion_ids.sql
│
└── docs/
    ├── profiling.md
    ├── architecture.md
    └── assumptions.md
```

---

## How to run

### 1. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install pandas duckdb dbt-duckdb
```

### 3. Load the CSV data into DuckDB

```bash
dbt seed --profiles-dir .
```

### 4. Run the models

```bash
dbt run --profiles-dir .
```

### 5. Run the data quality tests

```bash
dbt test --profiles-dir .
```

### 6. Run the profiling script

```bash
python scripts/profile_data.py
```

---

## Task 1 — Data Profiling & Data Quality

The raw datasets contain several quality issues that affect modelling.

Key findings include:

### Leads

- 123 raw rows
- 119 distinct `lead_id` values
- 4 duplicated `lead_id` values
- 3 missing `vertical` values
- 5 missing `region` values
- 103 raw distinct emails, reduced to 88 after normalization
- multiple date formats in `created_at`
- duplicated lead IDs contain conflicting attributes

### Conversions

- 51 raw rows
- 50 distinct `conversion_id` values
- 1 exact duplicated conversion row
- 3 missing `lead_id` values
- 6 non-null `lead_id` values that do not exist in the leads dataset
- 2 missing premium values
- 2 negative premium values
- inconsistent status casing
- mixed `.` and `,` decimal separators in premium
- multiple date formats in `signed_date`

The complete profiling findings and handling decisions are documented in:

`docs/profiling.md`

---

## Task 2 — Lead-to-Conversion Model

`lead_id` is not treated as an unquestioned join key.

The conversion attribution logic follows this hierarchy:

1. Match by `lead_id` when the ID exists, normalized emails agree, and the lead was created on or before the conversion date.
2. If this fails, fall back to normalized email.
3. For email fallback, use the latest lead created on or before the conversion date.
4. If no historical lead exists, leave the conversion unmatched.

After deduplication there are 50 unique conversions:

- 41 matched directly by `lead_id`
- 7 matched by normalized email plus temporal logic
- 2 left unmatched

The two unmatched conversions are deliberately preserved because the only leads with the same email occur after the contract was signed. Force-matching them would create chronologically impossible attribution.

The resulting lead mart contains:

- 119 canonical leads
- 40 converted leads
- 79 non-converted leads

All leads remain in the model, including those that never converted.

---

## Task 3 — KPI & Customer-Level Aggregation

### Conversion definition

For this solution:

- `active` counts as a historical conversion
- `cancelled` counts as a historical conversion
- `pending` does not count as a completed conversion

A cancelled contract still represents a contract that converted historically before being cancelled.

This is an assumption and should be confirmed with the business in production.

### Monthly KPI

The monthly KPI is grouped by:

- `vertical`
- `source`
- lead creation month

Metrics include:

- number of leads
- number of converted leads
- number of conversions
- conversion rate

Conversion rate is defined as:

```text
converted leads / total leads
```

rather than:

```text
number of contracts / number of leads
```

because one lead can produce multiple contracts.

### Customer definition

For this dataset, a customer is identified using:

```text
lower(trim(email))
```

This produces 88 customer-level records from 119 canonical leads.

The customer mart contains:

- number of leads
- number of conversions
- active contract count
- pending contract count
- total active premium
- active contract flag
- first lead date
- latest lead date

Email is used only because no durable customer identifier exists in the provided data.

At production scale I would prefer a stable CRM/customer identifier or an identity-resolution mapping layer, because email can change, be shared or be reused.

---

## Data quality testing

The project includes an executable dbt test:

```text
tests/assert_unique_conversion_ids.sql
```

It verifies that duplicate conversion IDs found in the raw data do not propagate beyond the deduplication layer.

The test passes when the query returns zero rows.

Run it with:

```bash
dbt test --select assert_unique_conversion_ids --profiles-dir .
```

---

## Architecture & Automation

The proposed production design uses a layered architecture:

```text
Raw
  ↓
Staging
  ↓
Intermediate
  ↓
Marts
  ↓
BI / Analytics
```

A Netrisk production implementation could map this to:

```text
AWS / source systems
        ↓
Snowflake
        ↓
dbt
        ↓
BI / Analytics
```

The detailed proposal, including scheduling, failure handling, traceability and documentation, is available in:

`docs/architecture.md`

---

## Assumptions & Trade-offs

Non-obvious modelling decisions are documented separately in:

`docs/assumptions.md`

These include:

- customer identity;
- email normalization;
- conversion attribution;
- temporal fallback matching;
- treatment of unmatched conversions;
- duplicate handling;
- conversion definition;
- KPI cohort definition;
- active premium calculation;
- handling of negative premiums;
- attribution-window trade-offs.

---

## Open questions

The main questions I would validate with business or source-system owners before productionizing this solution are:

1. Does `pending` count as a conversion for any reporting use case?
2. Do negative premiums represent refunds/corrections, or are they invalid source values?
3. Is there an approved attribution window between lead creation and contract signing?
4. Is there a stable customer or CRM identifier available upstream?
5. When duplicated `lead_id` records disagree on attributes such as source or region, is there a trusted source or precedence rule that should determine the canonical value?
