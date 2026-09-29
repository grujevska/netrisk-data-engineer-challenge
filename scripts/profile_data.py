import pandas as pd
import re
from datetime import datetime

leads = pd.read_csv("seeds/leads.csv")
conversions = pd.read_csv("seeds/conversions.csv")

#convert the messy dates into real dates

def parse_mixed_date(value):
    if pd.isna(value):
        return pd.NaT

    value = str(value).strip()

    formats = [
        "%Y-%m-%d",
        "%d.%m.%Y",
        "%m/%d/%Y",
    ]

    for date_format in formats:
        try:
            return datetime.strptime(value, date_format)
        except ValueError:
            pass

    return pd.NaT

print("LEADS")
print("Rows:", len(leads))
print("Columns:", len(leads.columns))
print(leads.columns.tolist())

print("\nCONVERSIONS")
print("Rows:", len(conversions))
print("Columns:", len(conversions.columns))
print(conversions.columns.tolist())

#missing values

print("\nMISSING VALUES - LEADS")
print(leads.isna().sum())

print("\nMISSING VALUES - CONVERSIONS")
print(conversions.isna().sum())

#dups

print("\nDUPLICATE ROWS - LEADS")
print(leads.duplicated().sum())

print("\nDUPLICATE ROWS - CONVERSIONS")
print(conversions.duplicated().sum())

print("\nDUPLICATE LEAD IDS")
print(leads["lead_id"].duplicated().sum())

print("\nDUPLICATE CONVERSION IDS")
print(conversions["conversion_id"].duplicated().sum())

#inspect dups

print("\nROWS WITH DUPLICATE LEAD IDS")
duplicate_leads = leads[
    leads["lead_id"].duplicated(keep=False)
].sort_values("lead_id")

print(duplicate_leads.to_string(index=False))

print("\nROWS WITH DUPLICATE CONVERSION IDS")
duplicate_conversions = conversions[
    conversions["conversion_id"].duplicated(keep=False)
].sort_values("conversion_id")

print(duplicate_conversions.to_string(index=False))

#inspect sus category values

print("\nVERTICAL VALUES")
print(leads["vertical"].value_counts(dropna=False))

print("\nSOURCE VALUES")
print(leads["source"].value_counts(dropna=False))

print("\nREGION VALUES")
print(leads["region"].value_counts(dropna=False))

print("\nSTATUS VALUES")
print(conversions["status"].value_counts(dropna=False))

print("\nPREMIUM RAW VALUES")
print(conversions["premium"].to_string(index=False))

#inspect date formats

def get_date_format(value):
    value = str(value)

    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return "YYYY-MM-DD"

    if re.fullmatch(r"\d{2}\.\d{2}\.\d{4}", value):
        return "DD.MM.YYYY"

    if re.fullmatch(r"\d{2}/\d{2}/\d{4}", value):
        return "MM/DD/YYYY"

    return "OTHER"


print("\nLEAD DATE FORMATS")
print(leads["created_at"].apply(get_date_format).value_counts())

print("\nCONVERSION DATE FORMATS")
print(conversions["signed_date"].apply(get_date_format).value_counts())

#inspect email consistency

leads["email_normalized"] = (
    leads["email"]
    .str.strip()
    .str.lower()
)

conversions["email_normalized"] = (
    conversions["email"]
    .str.strip()
    .str.lower()
)

print("\nLEAD EMAIL COUNTS")
print("Raw unique emails:", leads["email"].nunique())
print("Normalized unique emails:", leads["email_normalized"].nunique())

print("\nCONVERSION EMAIL COUNTS")
print("Raw unique emails:", conversions["email"].nunique())
print("Normalized unique emails:", conversions["email_normalized"].nunique())

#check whether conversion lead_id values actually exist in leads

valid_lead_ids = set(leads["lead_id"])

conversions["lead_id_exists"] = conversions["lead_id"].isin(valid_lead_ids)

print("\nCONVERSION LEAD ID MATCHING")
print("Missing lead_id:", conversions["lead_id"].isna().sum())

print(
    "Non-missing lead_id not found in leads:",
    (
        conversions["lead_id"].notna()
        & ~conversions["lead_id_exists"]
    ).sum()
)

print(
    "Valid lead_id found in leads:",
    (
        conversions["lead_id"].notna()
        & conversions["lead_id_exists"]
    ).sum()
)

#inspect those 9 problematic conversions

problem_conversions = conversions[
    conversions["lead_id"].isna()
    | ~conversions["lead_id_exists"]
]

print("\nPROBLEM CONVERSIONS")
print(
    problem_conversions[
        [
            "conversion_id",
            "lead_id",
            "email",
            "email_normalized",
            "signed_date"
        ]
    ].to_string(index=False)
)

#check whether those problem conversions have an email match in leads

lead_emails = set(leads["email_normalized"])

problem_conversions["email_exists_in_leads"] = (
    problem_conversions["email_normalized"].isin(lead_emails)
)

print("\nPROBLEM CONVERSIONS - EMAIL FALLBACK")
print(
    problem_conversions[
        [
            "conversion_id",
            "lead_id",
            "email_normalized",
            "email_exists_in_leads",
            "signed_date"
        ]
    ].to_string(index=False)
)

#convert the messy dates into real dates

leads["created_date"] = leads["created_at"].apply(parse_mixed_date)

conversions["signed_date_parsed"] = (
    conversions["signed_date"].apply(parse_mixed_date)
)

print("\nDATE PARSING CHECK")
print("Unparsed lead dates:", leads["created_date"].isna().sum())
print(
    "Unparsed conversion dates:",
    conversions["signed_date_parsed"].isna().sum()
)

#check whether the email fallback makes chronological sense

problem_conversions_temporal = conversions[
    conversions["lead_id"].isna()
    | ~conversions["lead_id_exists"]
].copy()

print("\nEMAIL FALLBACK TEMPORAL CHECK")

for _, conversion in problem_conversions_temporal.iterrows():

    matching_leads = leads[
        leads["email_normalized"] == conversion["email_normalized"]
    ]

    prior_leads = matching_leads[
        matching_leads["created_date"]
        <= conversion["signed_date_parsed"]
    ]

    print(
        conversion["conversion_id"],
        conversion["email_normalized"],
        "prior matching leads:",
        len(prior_leads)
    )

#UNRESOLVED EMAIL FALLBACK CASES

print("\nUNRESOLVED EMAIL FALLBACK CASES")

for conversion_id in [5048, 5049]:
    conversion = conversions[
        conversions["conversion_id"] == conversion_id
    ].iloc[0]

    matching_leads = leads[
        leads["email_normalized"] == conversion["email_normalized"]
    ][
        ["lead_id", "email_normalized", "created_date"]
    ]

    print(
        f"\nConversion {conversion_id} signed on "
        f"{conversion['signed_date_parsed'].date()}"
    )

    print(matching_leads.to_string(index=False))

#check whether the 42 “valid” lead_id matches also have matching emails

valid_matches = conversions[
    conversions["lead_id"].notna()
    & conversions["lead_id_exists"]
].merge(
    leads[["lead_id", "email_normalized"]],
    on="lead_id",
    how="left",
    suffixes=("_conversion", "_lead")
)

valid_matches["email_agrees"] = (
    valid_matches["email_normalized_conversion"]
    == valid_matches["email_normalized_lead"]
)

print("\nVALID LEAD ID - EMAIL AGREEMENT")
print(valid_matches["email_agrees"].value_counts(dropna=False))

print("\nVALID LEAD ID - EMAIL MISMATCHES")
print(
    valid_matches[
        ~valid_matches["email_agrees"]
    ][
        [
            "conversion_id",
            "lead_id",
            "email_normalized_conversion",
            "email_normalized_lead"
        ]
    ].to_string(index=False)
)

#find which conversion gets duplicated by the join

print("\nCONVERSIONS MULTIPLIED BY LEAD JOIN")

join_counts = (
    valid_matches
    .groupby("conversion_id")
    .size()
)

print(join_counts[join_counts > 1])

#inspect these two conversions and their lead IDs

print("\nDETAILS FOR MULTIPLIED CONVERSIONS")

for conversion_id in [5020, 5037]:
    print(f"\nConversion {conversion_id}")

    conversion_rows = conversions[
        conversions["conversion_id"] == conversion_id
    ]

    print("Conversion rows:")
    print(conversion_rows.to_string(index=False))

    lead_ids = conversion_rows["lead_id"].dropna().unique()

    for lead_id in lead_ids:
        print(f"\nMatching lead rows for lead_id {lead_id}:")
        print(
            leads[
                leads["lead_id"] == lead_id
            ].to_string(index=False)
        )

#turn premium into a real number and inspect its range

conversions["premium_numeric"] = pd.to_numeric(
    conversions["premium"]
    .astype("string")
    .str.replace(",", ".", regex=False),
    errors="coerce"
)

print("\nPREMIUM SUMMARY")
print(conversions["premium_numeric"].describe())

print("\nNEGATIVE PREMIUMS")
print(
    conversions[
        conversions["premium_numeric"] < 0
    ][
        ["conversion_id", "premium", "premium_numeric", "status"]
    ].to_string(index=False)
)

#check the date ranges

print("\nDATE RANGES")

print(
    "Lead created:",
    leads["created_date"].min().date(),
    "to",
    leads["created_date"].max().date()
)

print(
    "Conversion signed:",
    conversions["signed_date_parsed"].min().date(),
    "to",
    conversions["signed_date_parsed"].max().date()
)