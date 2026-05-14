import pandas as pd

from app import (
    add_most_recent_row,
    build_dynamic_dataset,
    get_us_column,
    rebase,
)


def test_get_us_column_finds_usa_suffix():
    columns = ["Spain (ESP)", "United States (USA)", "Canada (CAN)"]

    assert get_us_column(columns) == "United States (USA)"


def test_build_dynamic_dataset_keeps_newer_months_and_annualizes_older_rows():
    df = pd.DataFrame(
        {
            "Spain (ESP)": [130.0, 120.0, 110.0, 100.0],
            "United States (USA)": [260.0, 240.0, 220.0, 200.0],
        },
        index=["2025-M02", "2025-M01", "2024-M12", "2024-M11"],
    )

    result = build_dynamic_dataset(df, "2024-M12")

    assert list(result.index) == ["2025-M02", "2025-M01", "2024"]
    assert result.loc["2024", "Spain (ESP)"] == 105.0
    assert result.loc["2024", "United States (USA)"] == 210.0


def test_rebase_uses_base_values_divided_by_each_period():
    df = pd.DataFrame(
        {
            "Spain (ESP)": [240.0, 220.0, 200.0],
            "United States (USA)": [120.0, 110.0, 100.0],
        },
        index=["2025-M02", "2025-M01", "2024"],
    )

    result = rebase(df, "2025-M01")

    assert result.loc["2025-M01", "Spain (ESP)"] == 1.0
    assert result.loc["2024", "Spain (ESP)"] == 1.1
    assert result.loc["2024", "United States (USA)"] == 1.1


def test_add_most_recent_row_formats_latest_available_period_per_column():
    df = pd.DataFrame(
        {
            "Spain (ESP)": [None, 1.0, 2.0],
            "United States (USA)": [3.0, 4.0, None],
        },
        index=["2025-M02", "2025-M01", "2024"],
    )

    result = add_most_recent_row(df)

    assert result.loc["Most Recent Data", "Spain (ESP)"] == "January 2025"
    assert result.loc["Most Recent Data", "United States (USA)"] == "February 2025"
