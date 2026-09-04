"""Core data-cleaning rules."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import pandas as pd

from data_cleaning.config import CleaningConfig

EMAIL_PATTERN = re.compile(r"^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$", re.IGNORECASE)

STATUS_MAP = {
    "1": "active",
    "true": "active",
    "yes": "active",
    "y": "active",
    "active": "active",
    "0": "inactive",
    "false": "inactive",
    "no": "inactive",
    "n": "inactive",
    "inactive": "inactive",
    "pending": "pending",
}

CITY_MAP = {
    "beijing": "Beijing",
    "peking": "Beijing",
    "shanghai": "Shanghai",
    "guangzhou": "Guangzhou",
    "shenzhen": "Shenzhen",
    "hangzhou": "Hangzhou",
}


@dataclass(frozen=True)
class CleanResult:
    """Cleaned data plus a machine-readable report."""

    data: pd.DataFrame
    report: dict[str, Any]


def clean_customer_data(raw: pd.DataFrame, config: CleaningConfig | None = None) -> CleanResult:
    """Clean customer-like tabular data with explicit validation rules."""

    config = config or CleaningConfig()
    df = raw.copy()
    report: dict[str, Any] = {
        "input_rows": int(len(df)),
        "input_columns": list(df.columns),
        "actions": [],
        "invalid_counts": {},
        "output_rows": 0,
        "output_columns": [],
    }

    df.columns = [_normalize_column_name(column) for column in df.columns]
    report["actions"].append("normalized_column_names")

    df = _trim_strings(df)
    report["actions"].append("trimmed_string_values")

    before_exact_dedup = len(df)
    df = df.drop_duplicates().reset_index(drop=True)
    exact_duplicate_rows = before_exact_dedup - len(df)
    report["invalid_counts"]["exact_duplicate_rows_removed"] = int(exact_duplicate_rows)

    df = _ensure_columns(
        df,
        required=[
            "customer_id",
            "name",
            "email",
            "phone",
            "age",
            "signup_date",
            "city",
            "status",
            "amount",
            "comment",
        ],
    )

    df["customer_id"] = df["customer_id"].map(_normalize_customer_id)
    df["name"] = df["name"].map(_collapse_spaces)
    df["comment"] = df["comment"].map(_collapse_spaces)

    before_key_dedup = len(df)
    keyed_rows = df["customer_id"].notna()
    df = pd.concat(
        [
            df.loc[keyed_rows].drop_duplicates(subset=["customer_id"], keep="first"),
            df.loc[~keyed_rows],
        ],
        ignore_index=True,
    )
    customer_id_duplicates = before_key_dedup - len(df)
    report["invalid_counts"]["duplicate_customer_id_rows_removed"] = int(customer_id_duplicates)

    df["email"] = df["email"].str.lower().map(_clean_missing_text)
    email_valid = df["email"].map(_is_valid_email)
    report["invalid_counts"]["invalid_email"] = int((~email_valid).sum())
    df.loc[~email_valid, "email"] = pd.NA

    df["phone"] = df["phone"].map(_normalize_phone)
    phone_valid = df["phone"].notna()
    report["invalid_counts"]["invalid_phone"] = int((~phone_valid).sum())

    raw_age = pd.to_numeric(df["age"], errors="coerce")
    age_valid = raw_age.between(config.min_age, config.max_age)
    report["invalid_counts"]["invalid_age"] = int((~age_valid).sum())
    df["age"] = raw_age.where(age_valid)
    median_age = df["age"].median(skipna=True)
    if pd.notna(median_age):
        df["age"] = df["age"].fillna(round(float(median_age))).astype("Int64")
        report["actions"].append(f"filled_missing_age_with_median_{round(float(median_age))}")

    parsed_dates = pd.to_datetime(df["signup_date"], errors="coerce", format="mixed")
    report["invalid_counts"]["invalid_signup_date"] = int(parsed_dates.isna().sum())
    df["signup_date"] = parsed_dates.dt.strftime("%Y-%m-%d")
    df.loc[parsed_dates.isna(), "signup_date"] = pd.NA

    df["city"] = df["city"].str.lower().map(_clean_missing_text).map(_standardize_city)
    df["status"] = df["status"].str.lower().map(_clean_missing_text).map(_standardize_status)

    amount = df["amount"].map(_strip_number_text)
    amount = pd.to_numeric(amount, errors="coerce")
    amount_valid = amount.notna() & (amount >= 0)
    report["invalid_counts"]["invalid_amount"] = int((~amount_valid).sum())
    df["amount"] = amount.where(amount_valid, 0).round(2)

    df["needs_review"] = (
        df[["email", "phone", "signup_date"]].isna().any(axis=1)
        | df["status"].eq("unknown")
        | amount_valid.eq(False)
    )

    df = df.sort_values(["customer_id", "signup_date"], na_position="last").reset_index(drop=True)

    report["output_rows"] = int(len(df))
    report["output_columns"] = list(df.columns)
    report["review_rows"] = int(df["needs_review"].sum())
    report["actions"].append("created_needs_review_flag")

    return CleanResult(data=df, report=report)


def _normalize_column_name(column: object) -> str:
    text = str(column).strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")


def _trim_strings(df: pd.DataFrame) -> pd.DataFrame:
    return df.map(lambda value: value.strip() if isinstance(value, str) else value)


def _ensure_columns(df: pd.DataFrame, required: list[str]) -> pd.DataFrame:
    for column in required:
        if column not in df.columns:
            df[column] = pd.NA
    return df[required]


def _clean_missing_text(value: object) -> object:
    if pd.isna(value):
        return pd.NA

    text = str(value).strip()
    if text.lower() in {"", "n/a", "na", "none", "null", "unknown"}:
        return pd.NA
    return text


def _collapse_spaces(value: object) -> object:
    value = _clean_missing_text(value)
    if pd.isna(value):
        return pd.NA
    return re.sub(r"\s+", " ", str(value)).strip()


def _normalize_customer_id(value: object) -> object:
    value = _clean_missing_text(value)
    if pd.isna(value):
        return pd.NA

    text = re.sub(r"\s+", "", str(value))
    return text.zfill(3) if text.isdigit() else text


def _is_valid_email(value: object) -> bool:
    return not pd.isna(value) and bool(EMAIL_PATTERN.match(str(value)))


def _normalize_phone(value: object) -> object:
    value = _clean_missing_text(value)
    if pd.isna(value):
        return pd.NA

    digits = re.sub(r"\D", "", str(value))
    if digits.startswith("86") and len(digits) == 13:
        digits = digits[2:]

    if len(digits) == 11 and digits.startswith("1"):
        return digits
    if len(digits) >= 7:
        return digits
    return pd.NA


def _strip_number_text(value: object) -> object:
    value = _clean_missing_text(value)
    if pd.isna(value):
        return pd.NA
    return str(value).replace(",", "")


def _standardize_city(value: object) -> object:
    if pd.isna(value):
        return "Unknown"
    text = str(value).strip().lower()
    return CITY_MAP.get(text, text.title())


def _standardize_status(value: object) -> str:
    if pd.isna(value):
        return "unknown"
    return STATUS_MAP.get(str(value).strip().lower(), "unknown")

