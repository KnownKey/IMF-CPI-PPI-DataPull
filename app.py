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

st.markdown(
    """
    <style>
        .stApp, .main {
            background-color: #f4f5f7;
        }
        .block-container {
            padding-top: 1rem;
            padding-left: 2rem;
            padding-right: 2rem;
        }
        .stDownloadButton>button {
            width: 100% !important;
            max-width: 100% !important;
            display: block !important;
            min-height: 3.2rem !important;
            font-size: 1rem !important;
        }
        table.dataframe {
            border: 1px solid #888 !important;
            background-color: white;
        }
        table.dataframe th,
        table.dataframe td {
            border: 1px solid #888 !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

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

    # Filter to remove rows before 1950
    filtered_result = []
    for idx in df_rebased_indexed.index:
        try:
            # Try to parse as year-month format
            year = int(idx.split("-")[0]) if "-" in str(idx) else int(idx)
            if year >= 1950:
                filtered_result.append(idx)
        except (ValueError, IndexError, AttributeError):
            # If parsing fails, include the row (e.g., for "Most Recent Data")
            filtered_result.append(idx)
    
    df_rebased_indexed = df_rebased_indexed.loc[filtered_result]
    
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
            lambda x: f"{x:.4f}" if isinstance(x, (int, float, np.integer, np.floating)) and not pd.isna(x) else ""
        )
    return formatted


def render_html_table(df):
    html_df = df.copy()
    for col in html_df.columns:
        html_df[col] = html_df[col].apply(
            lambda x: f"{x:.4f}" if isinstance(x, (int, float, np.integer, np.floating)) and not pd.isna(x) else ("" if pd.isna(x) else x)
        )

    html_df.index = html_df.index.astype(str)
    html_df.index = html_df.index.map(lambda x: f"<i>{x}</i>" if x == "Most Recent Data" else x)

    if not html_df.empty:
        first_row = html_df.index[0]
        html_df.loc[first_row] = html_df.loc[first_row].apply(
            lambda x: f"<i>{x}</i>" if not (isinstance(x, str) and x.startswith("<i>")) else x
        )

    html = html_df.to_html(escape=False, index=True, index_names=False)
    html = html.replace(
        '<table border="1" class="dataframe">',
        '<table style="width:auto;border-collapse:collapse;border:1px solid #888; background-color:white;">'
    )
    html = html.replace(
        '<th>',
        '<th style="padding:8px 12px;white-space:nowrap;text-align:center;border:1px solid #888;background:#f2f2f2; color:#111;">'
    )
    html = html.replace(
        '<td>',
        '<td style="padding:8px 12px;white-space:nowrap;text-align:center;border:1px solid #888;">'
    )
    return f"<div style='overflow-x:auto;'>{html}</div>"


# -----------------------------
# SIDEBAR
# -----------------------------
st.sidebar.header("Selection")

us_column = get_us_column(raw_reversed.columns)

def find_country_by_code(columns, code):
    for col in columns:
        if col.strip().endswith(f"({code})"):
            return col
    return None

default_country_codes = ["GBR", "ESP", "CHN"]
default_countries = [find_country_by_code(raw_reversed.columns, code) for code in default_country_codes]
default_countries = [c for c in default_countries if c is not None]

countries = st.sidebar.multiselect(
    "Select Countries",
    options=raw_reversed.columns.tolist(),
    default=default_countries if len(default_countries) == 3 else raw_reversed.columns[:3].tolist()
)

# Valuation period inputs
current_year = datetime.now().year
current_month = datetime.now().month
months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
month_map = {m: f"M{i+1:02d}" for i, m in enumerate(months)}
year_options = list(range(1950, current_year + 1))

# Ensure year selection cannot go before 1950
year_input = st.sidebar.selectbox("Year", options=year_options, index=len(year_options)-1)
year_input = max(1950, year_input)  # Ensure year never goes below 1950
month_options = months if year_input < current_year else months[:current_month]
default_month_index = max(0, current_month - 4)
month_input = st.sidebar.selectbox("Month", options=month_options, index=min(default_month_index, len(month_options)-1))

valuation_period = f"{year_input}-{month_map[month_input]}"


# -----------------------------
# MAIN DATA FILTER
# -----------------------------
df = raw_reversed[countries].copy()


# -----------------------------
# RUN MODEL
# -----------------------------
# Title row
title_col = st.columns([1])[0]
with title_col:
    st.title("IMF CPI Indexing (Index = 2010)")

# Two-column layout for How to Use and Methodology with headings on same row
how_col, method_col = st.columns([3, 2])

with how_col:
    st.markdown(
        """
<div style='background:#ffffff;border:1px solid #dfe3ea;border-radius:12px;padding:20px;'>
<h3 style='margin-top:0;'>How to Use</h3>
<ol style='margin:0;padding-left:18px;'>
<li>Select the countries you want to analyze from the sidebar.</li>
<li>Choose the valuation year and month (up to the current date).</li>
<li>Click "Run Model" to generate the rebased CPI index.</li>
<li>View the results in the table below and download the Excel files.</li>
</ol>
</div>
""",
        unsafe_allow_html=True,
    )

with method_col:
    st.markdown(
        """
<div style='background:#ffffff;border:1px solid #dfe3ea;border-radius:12px;padding:20px;'>
<h3 style='margin-top:0;'>Methodology</h3>
<p style='margin:0;'>In this example, with a valuation year of 2025, represents the underlying CPI model calculation, represented in blue.</p>
</div>
""",
        unsafe_allow_html=True,
    )
    st.latex(r"""
\small
\text{i.e.,} \quad
\text{Spain RCN}_{2000} =
\text{Spain Cost}_{2000} \times
\frac{\text{US M\&E Index}_{2025}}{\text{US M\&E Index}_{2000}} \times \\
\textcolor{blue}{\left[ \frac{\text{Spain PPI Index}_{2025}}{\text{Spain PPI Index}_{2000}} \middle/ \frac{\text{US PPI Index}_{2025}}{\text{US PPI Index}_{2000}} \right]}
""")

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

            success_col, download_col = st.columns([4, 1])
            
            with success_col:
                st.success("Model successfully executed")
            
            # Prepare data for downloads - use raw selected data for the most recent date
            most_recent_row = add_most_recent_row(df)
            result_with_summary = pd.concat([most_recent_row, result])
            display_result = result_with_summary.drop(columns=[us_col]) if us_col and us_col in result_with_summary.columns else result_with_summary
            display_df = display_result.reset_index().rename(columns={"index": "Time"}).set_index("Time")
            display_df.index.name = None
            html_table = render_html_table(display_df)

            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                result_with_summary.to_excel(writer, sheet_name="Rebased")
                df_dynamic.to_excel(writer, sheet_name="Dynamic Dataset")
                raw_full.to_excel(writer, sheet_name="Original Order")
                raw_reversed.to_excel(writer, sheet_name="Reversed Order")

            # Prepare selected countries data for download
            selected_countries_df = result_with_summary.copy()
            selected_countries_buffer = io.BytesIO()
            with pd.ExcelWriter(selected_countries_buffer, engine="openpyxl") as writer:
                selected_countries_df.to_excel(writer, sheet_name="Selected Countries")
            
            # Add Download Selected Countries button next to success message
            with download_col:
                st.download_button(
                    label="📥 Download Selected Countries",
                    data=selected_countries_buffer.getvalue(),
                    file_name="imf_cpi_selected_countries.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )
            
            st.markdown(html_table, unsafe_allow_html=True)


# -----------------------------
# FOOTER
# -----------------------------
st.markdown("---")

st.markdown(
    f"""
    <div style='text-align: center; color: gray; font-size: 12px;'>
        © {datetime.now().year} SC<br>
        Last Updated: {APP_LAST_UPDATED}
    </div>
    """,
    unsafe_allow_html=True
)