from __future__ import annotations

import pandas as pd

from data_cleaning.cleaner import clean_customer_data


def test_clean_customer_data_standardizes_common_dirty_values() -> None:
    raw = pd.DataFrame(
        [
            {
                " Customer ID ": " 1 ",
                "Name": " Alice   Zhang ",
                "Email": " ALICE@EXAMPLE.COM ",
                "Phone": " +86 138 0013 8000 ",
                "Age": "28",
                "Signup Date": "2026/08/01",
                "City": "beijing",
                "Status": "YES",
                "Amount": "1,200.50",
                "Comment": " good  customer ",
            },
            {
                " Customer ID ": " 1 ",
                "Name": " Alice   Zhang ",
                "Email": " ALICE@EXAMPLE.COM ",
                "Phone": " +86 138 0013 8000 ",
                "Age": "28",
                "Signup Date": "2026/08/01",
                "City": "beijing",
                "Status": "YES",
                "Amount": "1,200.50",
                "Comment": " good  customer ",
            },
            {
                " Customer ID ": "2",
                "Name": "Bob",
                "Email": "bad-email",
                "Phone": "N/A",
                "Age": "200",
                "Signup Date": "not a date",
                "City": "",
                "Status": "maybe",
                "Amount": "-3",
                "Comment": "",
            },
        ]
    )

    result = clean_customer_data(raw)
    clean = result.data

    assert len(clean) == 2
    assert clean.loc[0, "customer_id"] == "001"
    assert clean.loc[0, "name"] == "Alice Zhang"
    assert clean.loc[0, "email"] == "alice@example.com"
    assert clean.loc[0, "phone"] == "13800138000"
    assert clean.loc[0, "city"] == "Beijing"
    assert clean.loc[0, "status"] == "active"
    assert clean.loc[0, "amount"] == 1200.5

    assert pd.isna(clean.loc[1, "email"])
    assert clean.loc[1, "city"] == "Unknown"
    assert clean.loc[1, "status"] == "unknown"
    assert clean.loc[1, "amount"] == 0
    assert bool(clean.loc[1, "needs_review"]) is True

    assert result.report["invalid_counts"]["exact_duplicate_rows_removed"] == 1
    assert result.report["invalid_counts"]["duplicate_customer_id_rows_removed"] == 0
    assert result.report["review_rows"] == 1

