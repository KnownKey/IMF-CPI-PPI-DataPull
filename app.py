import streamlit as st
import pandas as pd
import numpy as np
import sdmx
import io
import requests
from datetime import datetime

# -----------------------------
# CONFIG
# -----------------------------
st.set_page_config(page_title="IMF CPI Model", layout="wide")

IMF = sdmx.Client("IMF_DATA")
APP_LAST_UPDATED = datetime.now().strftime("%Y-%m-%d")


# -----------------------------
# COUNTRY MAPPING
# -----------------------------
@st.cache_data
def load_country_mapping():
    url = "https://raw.githubusercontent.com/lukes/ISO-3166-Countries-with-Regional-Codes/master/all/all.csv"
    r = requests.get(url)
    r.raise_for_status()
    df = pd.read_csv(io.StringIO(r.text))
    return df.set_index("alpha-3")["name"].to_dict()


country_mapping = load_country_mapping()


# -----------------------------
# IMF DATA LOAD
# -----------------------------
@st.cache_data
def load_imf_data():
    key = ".CPI._T.SRP_IX.M"

    data = IMF.data("CPI", key=key, params={})
    df = sdmx.to_pandas(data).reset_index()

    df["COUNTRY_FULL"] = df["COUNTRY"].map(country_mapping)

    raw = df.pivot_table(
        index="TIME_PERIOD",
        columns=["COUNTRY_FULL", "COUNTRY"],
        values="value"
    ).sort_index()

    raw.columns = [f"{c[0]} ({c[1]})" for c in raw.columns]

    raw_reversed = raw.iloc[::-1]

    return raw, raw_reversed


raw_full, raw_reversed = load_imf_data()


def get_us_column(columns):
    for col in columns:
        if col.strip().endswith("(USA)"):
            return col
    return None


# -----------------------------
# DYNAMIC DATASET (THIS FIXES COLAB LOGIC GAP)
# -----------------------------
def build_dynamic_dataset(df, valuation_period):
    df = df.copy()

    # Convert index to datetime
    df.index = pd.to_datetime(df.index, format="%Y-M%m", errors="coerce")

    # Parse valuation period
    vp = pd.to_datetime(valuation_period, format="%Y-M%m", errors="coerce")
    monthly_valuation = True
    if pd.isna(vp):
        vp = pd.to_datetime(valuation_period, format="%Y", errors="coerce")
        monthly_valuation = False

    if pd.isna(vp):
        return None

    # Split dataset
    if monthly_valuation:
        monthly_part = df[df.index > vp].copy()
        yearly_part = df[df.index <= vp].copy()
    else:
        monthly_part = df[df.index >= vp].copy()
        yearly_part = df[df.index < vp].copy()

    # Annualize older data - compatible with older pandas versions
    yearly_avg = yearly_part.groupby(yearly_part.index.year).mean()
    yearly_avg.index = yearly_avg.index.astype(str)

    # Format monthly index
    monthly_part.index = monthly_part.index.strftime("%Y-M%m")

    # Combine
    combined = pd.concat([monthly_part, yearly_avg])
    combined = combined.sort_index(ascending=False)

    return combined


# -----------------------------
# REBASING (CORE MATH)
# -----------------------------
def rebase(df, base_period):
    """
    Rebase CPI data to a specific valuation period.
    Uses the correct mathematical formula: base_values / df
    """
    df_rebased = df.copy()

    # Ensure the valuation_period exists in the index
    if base_period not in df_rebased.index:
        if isinstance(base_period, str) and "M" in base_period:
            try:
                fallback_year = datetime.strptime(base_period, "%Y-M%m").year
                base_period = str(fallback_year)
            except ValueError:
                pass

    if base_period not in df_rebased.index:
        return None

    # Get the values for the valuation period to use as the base
    base_values = df_rebased.loc[base_period]

    # Identify columns where the base_values itself is NaN
    cols_with_nan_base = base_values[base_values.isna()].index

    # Initialize a dictionary to store custom messages for these columns
    custom_nan_messages = {}
    for col in cols_with_nan_base:
        # Find the most recent non-NaN value for this column from the base period onwards
        temp_series = df_rebased[col].loc[df_rebased.index <= base_period]
        first_valid_idx_in_slice = temp_series.first_valid_index()

        if first_valid_idx_in_slice:
            custom_nan_messages[col] = f"N/A-Data Available ONLY in {first_valid_idx_in_slice}"
        else:
            custom_nan_messages[col] = "N/A-No Data Available"

    # Perform the re-basing division: base / data
    df_rebased_indexed = df_rebased.rdiv(base_values, axis=1)

    # Convert the DataFrame to object dtype to allow mixed types (floats and strings)
    df_rebased_indexed = df_rebased_indexed.astype(object)

    # Filter to keep only from base period onwards (descending order)
    df_rebased_indexed = df_rebased_indexed.loc[base_period:]

    # For columns that had NaN at the base period, replace their entire column
    # with the custom message
    for col, msg in custom_nan_messages.items():
        df_rebased_indexed.loc[:, col] = msg

    return df_rebased_indexed


def format_most_recent_label(value):
    if isinstance(value, str):
        try:
            parsed = datetime.strptime(value, "%Y-M%m")
            return parsed.strftime("%B %Y")
        except ValueError:
            try:
                parsed = datetime.strptime(value, "%Y")
                return parsed.strftime("%Y")
            except ValueError:
                return value
    return value


def parse_date_index(value):
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.strptime(value, "%Y-M%m")
        except ValueError:
            try:
                return datetime.strptime(value, "%Y")
            except ValueError:
                return None
    return None


def add_most_recent_row(df, label="Most Recent Data"):
    summary = {}

    for col in df.columns:
        col_series = df[col].dropna()
        if not col_series.empty:
            best_index = None
            best_date = None
            for idx in col_series.index:
                parsed = parse_date_index(idx)
                if parsed is not None:
                    if best_date is None or parsed > best_date:
                        best_date = parsed
                        best_index = idx
                elif best_index is None:
                    best_index = idx
            summary[col] = format_most_recent_label(best_index) if best_index is not None else None
        else:
            summary[col] = None

    summary_df = pd.DataFrame([summary], index=[label])
    return summary_df


def format_display(df):
    formatted = df.copy()
    for col in formatted.columns:
        formatted[col] = formatted[col].apply(
            lambda x: f"{x:.4f}" if isinstance(x, (int, float, np.integer, np.floating)) and not pd.isna(x) else x
        )
    return formatted


# -----------------------------
# SIDEBAR
# -----------------------------
st.sidebar.header("Settings")

us_column = get_us_column(raw_reversed.columns)

countries = st.sidebar.multiselect(
    "Select Countries",
    options=raw_reversed.columns.tolist(),
    default=raw_reversed.columns[:5].tolist()
)

if us_column and us_column not in countries:
    countries.append(us_column)

valuation_period = st.sidebar.text_input(
    "Valuation Period (e.g. 2020 or 2025-M01)",
    value="2020"
)


# -----------------------------
# MAIN DATA FILTER
# -----------------------------
df = raw_reversed[countries].copy()


# -----------------------------
# RUN MODEL
# -----------------------------
st.title("IMF CPI Rebased Index Tool")
st.write("Hybrid IMF CPI model (monthly + annual structure + rebasing)")

if st.button("Run Model"):

    # STEP 1: build Colab-equivalent dataset
    df_dynamic = build_dynamic_dataset(df, valuation_period)

    if df_dynamic is None:
        st.error("Invalid valuation period format")
    else:

        # STEP 2: apply correct rebasing math
        result = rebase(df_dynamic, valuation_period)

        if result is None:
            st.error("Valuation period not found in dataset")
        else:
            us_col = get_us_column(result.columns)
            if us_col and len(result.columns) > 1:
                us_values = pd.to_numeric(result[us_col], errors="coerce")
                if us_values.notna().any():
                    for col in result.columns:
                        if col == us_col:
                            continue
                        col_values = pd.to_numeric(result[col], errors="coerce")
                        ratio = col_values.div(us_values)
                        result[col] = ratio.where(col_values.notna() & us_values.notna(), result[col])

            st.success("Model successfully executed")

            most_recent_row = add_most_recent_row(df)
            result_with_summary = pd.concat([most_recent_row, result])
            display_result = result_with_summary.drop(columns=[us_col]) if us_col and us_col in result_with_summary.columns else result_with_summary
            st.dataframe(format_display(display_result), use_container_width=True)

            # -----------------------------
            # EXPORT
            # -----------------------------
            buffer = io.BytesIO()

            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                result_with_summary.to_excel(writer, sheet_name="Rebased")
                df_dynamic.to_excel(writer, sheet_name="Dynamic Dataset")
                raw_full.to_excel(writer, sheet_name="Original Order")
                raw_reversed.to_excel(writer, sheet_name="Reversed Order")

            st.download_button(
                label="Download Excel",
                data=buffer.getvalue(),
                file_name="imf_cpi_model.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )


# -----------------------------
# FOOTER
# -----------------------------
st.markdown("---")

st.markdown(
    f"""
    <div style='text-align: center; color: gray; font-size: 12px;'>
        © {datetime.now().year} SC — All Rights Reserved<br>
        Last Updated: {APP_LAST_UPDATED}
    </div>
    """,
    unsafe_allow_html=True
)