# Data Profiling

## Dataset overview

### Leads
- Rows: 123
- Columns: 6
- Date range: 2024-01-05 to 2024-10-31
- Distinct raw emails: 103
- Distinct normalized emails: 88

### Conversions
- Rows: 51
- Columns: 6
- Date range: 2024-01-16 to 2024-11-29
- Distinct raw emails: 43
- Distinct normalized emails: 41

## Data quality findings

| Issue | Severity | Planned handling |
|---|---|---|
| 3 missing `vertical` values | Medium | Preserve as null/unknown; do not invent a value |
| 5 missing `region` values | Low | Preserve as null/unknown |
| 3 missing conversion `lead_id` values | High | Attempt controlled fallback matching using normalized email and date |
| 6 conversion `lead_id` values do not exist in leads | High | Attempt controlled fallback matching using normalized email and date |
| 4 duplicated `lead_id` values | High | Canonicalize carefully and retain conflict flags |
| 1 exact duplicate conversion row | High | Deduplicate deterministically |
| Inconsistent email casing/whitespace | Medium | Normalize with trim + lowercase |
| Mixed date formats | Medium | Parse explicitly into a standard date |
| Status casing differs (`active`, `Active`, `ACTIVE`) | Low | Normalize to lowercase |
| Premium uses both `.` and `,` decimal separators | Medium | Normalize before numeric conversion |
| 2 missing premium values | Medium | Preserve as null |
| 2 negative premiums | High | Preserve and flag; business meaning requires clarification |
| 2 conversions have an email match only to future leads | High | Leave unmatched rather than create impossible attribution |