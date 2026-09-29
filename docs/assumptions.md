# Assumptions & Trade-offs

| Decision | Alternative considered | Why rejected |
|---|---|---|
| Use normalized email as the customer identifier for this exercise | Use `lead_id` as the customer identifier | `lead_id` represents lead interactions, is duplicated in the source, and does not reliably identify a person across multiple leads |
| Normalize emails using trim + lowercase | Match using raw email values | Raw emails differ in casing and whitespace, which would cause legitimate matches to be missed |
| Match conversions first by valid `lead_id`, then fall back to normalized email plus chronology | Match only by `lead_id` | 9 conversion rows have either missing or invalid `lead_id` values, even though their email exists in the leads dataset |
| For email fallback, choose the latest lead created on or before the conversion date | Match any lead sharing the same email | This could attribute a conversion to a lead that did not yet exist |
| Leave conversions unmatched if no prior lead exists | Force-match to the closest lead by email | Two conversions occur before every lead with the same email, so forcing a match would create chronologically impossible attribution |
| Deduplicate exact duplicate conversion records before modelling | Keep all source conversion rows | The duplicate would inflate conversion counts and downstream KPIs |
| Canonicalize duplicated `lead_id` values and set conflicting attributes to null | Arbitrarily choose one duplicate row | There is no evidence that one conflicting source row is more correct than another |
| Count `active` and `cancelled` contracts as historical conversions, but exclude `pending` | Count every conversion row as a conversion | A pending contract does not clearly represent a completed conversion, while a cancelled contract was historically converted before cancellation |
| Use lead creation month for the `(vertical, source, month)` KPI | Use conversion signed month | Using conversion month would mix lead acquisition cohorts and make the denominator and numerator describe different populations |
| Calculate conversion rate as converted leads / total leads | Calculate conversions / leads | One lead can produce multiple contracts, so raw conversion count could produce misleading rates above 100% |
| Sum premium only for active contracts in active premium metrics | Sum premiums from all statuses | Cancelled and pending contracts should not contribute to currently active premium |
| Preserve negative premium values rather than changing them | Convert negatives to positive values or drop them | Their business meaning is unclear; changing them without confirmation would alter source semantics |
| Do not introduce an arbitrary attribution window | Require email fallback to occur within 30/60/90 days | No attribution window was provided, so inventing one would impose an unsupported business rule |