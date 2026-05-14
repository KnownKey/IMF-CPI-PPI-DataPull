import streamlit as st
import pandas as pd
import numpy as np
import sdmx
import io
import requests
from datetime import datetime
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

# -----------------------------
# CONFIG
# -----------------------------
APP_STYLES = """
    <style>
        :root {
            --app-bg: #181a1f;
            --surface: #20232a;
            --surface-raised: #272b33;
            --surface-muted: #2e3340;
            --border: #3d4350;
            --border-strong: #596273;
            --text: #f4f6f8;
            --text-muted: #c2c8d2;
            --accent: #2fbf8f;
            --accent-strong: #42d7a5;
            --accent-soft: rgba(47, 191, 143, 0.14);
            --warning: #e3b341;
        }
        .stApp, .main {
            background:
                radial-gradient(circle at top left, rgba(47, 191, 143, 0.08), transparent 30rem),
                var(--app-bg);
            color: var(--text);
        }
        .block-container {
            padding-top: 1.5rem;
            padding-left: 2rem;
            padding-right: 2rem;
            padding-bottom: 2rem;
            max-width: 1440px;
        }
        h1, h2, h3, h4, h5, h6,
        .stMarkdown, .stText, label, p, li {
            color: var(--text);
        }
        h1 {
            letter-spacing: 0;
            margin-bottom: 0.25rem;
        }
        [data-testid="stSidebar"] {
            background: #1d2026;
            border-right: 1px solid var(--border);
        }
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] .stMarkdown {
            color: var(--text);
        }
        [data-testid="stSidebar"] [data-baseweb="select"] > div,
        [data-testid="stSidebar"] [data-baseweb="select"] input {
            background-color: var(--surface-raised);
            color: var(--text);
            border-color: var(--border);
        }
        [data-testid="stSidebar"] [data-baseweb="tag"] {
            background-color: var(--accent-soft);
            color: var(--text);
            border: 1px solid rgba(47, 191, 143, 0.3);
        }
        div[data-testid="stButton"] > button,
        div[data-testid="stDownloadButton"] > button {
            border-radius: 8px;
            border: 1px solid rgba(47, 191, 143, 0.5);
            background: linear-gradient(180deg, var(--accent-strong), var(--accent));
            color: #061411;
            font-weight: 700;
            box-shadow: 0 12px 24px rgba(47, 191, 143, 0.16);
            transition: transform 120ms ease, box-shadow 120ms ease, border-color 120ms ease;
        }
        div[data-testid="stButton"] > button:hover,
        div[data-testid="stDownloadButton"] > button:hover {
            border-color: var(--accent-strong);
            color: #061411;
            transform: translateY(-1px);
            box-shadow: 0 16px 30px rgba(47, 191, 143, 0.24);
        }
        div[data-testid="stButton"] > button:focus,
        div[data-testid="stDownloadButton"] > button:focus {
            box-shadow: 0 0 0 0.2rem rgba(47, 191, 143, 0.25);
        }
        .stDownloadButton>button {
            width: 100% !important;
            max-width: 100% !important;
            display: block !important;
            min-height: 3.2rem !important;
            font-size: 1rem !important;
        }
        div[data-testid="stAlert"] {
            background: rgba(47, 191, 143, 0.12);
            border: 1px solid rgba(47, 191, 143, 0.36);
            border-radius: 8px;
            color: var(--text);
        }
        .cpi-titlebar {
            margin-bottom: 1rem;
            padding-bottom: 0.8rem;
            border-bottom: 1px solid var(--border);
        }
        .cpi-subtitle {
            color: var(--text-muted);
            margin: 0.15rem 0 0;
            max-width: 760px;
        }
        .cpi-card {
            min-height: 170px;
            background: linear-gradient(180deg, var(--surface-raised), var(--surface));
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 18px 20px;
            box-shadow: 0 16px 40px rgba(0, 0, 0, 0.18);
        }
        .cpi-card h3 {
            margin: 0 0 0.65rem;
            font-size: 1.05rem;
        }
        .cpi-card ol,
        .cpi-card p {
            color: var(--text-muted);
            margin-bottom: 0;
        }
        .cpi-card li {
            color: var(--text-muted);
            margin-bottom: 0.32rem;
        }
        .cpi-card strong,
        .cpi-card .accent {
            color: var(--accent-strong);
        }
        .katex, .katex-display {
            color: var(--text);
        }
        .cpi-table-wrap {
            overflow-x: auto;
            margin-top: 0.75rem;
            border: 1px solid var(--border);
            border-radius: 8px;
            background: var(--surface);
            box-shadow: 0 14px 36px rgba(0, 0, 0, 0.18);
        }
        .cpi-table-wrap table {
            width: auto;
            min-width: 100%;
            border-collapse: collapse;
            border: 0;
            background-color: var(--surface);
            color: var(--text);
        }
        .cpi-table-wrap th,
        .cpi-table-wrap td {
            padding: 9px 12px;
            white-space: nowrap;
            text-align: center;
            border: 1px solid var(--border);
        }
        .cpi-table-wrap th {
            position: sticky;
            top: 0;
            z-index: 1;
            background: var(--surface-muted);
            color: var(--text);
            font-weight: 700;
        }
        .cpi-table-wrap tbody tr:nth-child(even) {
            background: rgba(255, 255, 255, 0.035);
        }
        .cpi-table-wrap tbody tr:hover {
            background: rgba(47, 191, 143, 0.1);
        }
        .cpi-table-wrap tbody tr:first-child td,
        .cpi-table-wrap tbody tr:first-child th {
            color: var(--warning);
            background: rgba(227, 179, 65, 0.08);
        }
        .cpi-footer {
            text-align: center;
            color: var(--text-muted);
            font-size: 12px;
            margin-top: 0.5rem;
        }
        hr {
            border-color: var(--border);
        }
    </style>
    """
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


# -----------------------------
# IMF DATA LOAD
# -----------------------------
@st.cache_data
def load_imf_data(country_mapping):
    key = ".CPI._T.SRP_IX.M"
    imf = sdmx.Client("IMF_DATA")

    data = imf.data("CPI", key=key, params={})
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


def render_html_table(df):
    html_df = df.copy().astype(object)
    for col in html_df.columns:
        html_df[col] = html_df[col].apply(
            lambda x: f"{x:.4f}" if isinstance(x, (int, float, np.integer, np.floating)) and not pd.isna(x) else ("" if pd.isna(x) else x)
        )

    html_df.index = html_df.index.astype(str)
    html_df.index = html_df.index.map(lambda x: f"<i>{x}</i>" if x == "Most Recent Data" else x)

    if not html_df.empty:
        first_row = html_df.iloc[0].apply(
            lambda x: f"<i>{x}</i>" if not (isinstance(x, str) and x.startswith("<i>")) else x
        ).tolist()
        html_df.iloc[0, :] = first_row

    html = html_df.to_html(escape=False, index=True, index_names=False)
    html = html.replace(
        '<table border="1" class="dataframe">',
        '<table class="dataframe">'
    )
    return f"<div class='cpi-table-wrap'>{html}</div>"


def get_column_letter(col_num):
    """Convert column number to Excel column letter (1=A, 2=B, ..., 27=AA, etc.)"""
    letter = ""
    while col_num > 0:
        col_num -= 1
        letter = chr(65 + (col_num % 26)) + letter
        col_num //= 26
    return letter


def create_styled_excel(df, raw_data, valuation_period, selected_countries=None):
    """Create an Excel file with formatting matching the HTML table, including underlying data tab"""
    buffer = io.BytesIO()
    
    def format_valuation_period(valuation_period):
        try:
            parsed = datetime.strptime(valuation_period, "%Y-M%m")
            return parsed.strftime("%B %Y")
        except ValueError:
            try:
                parsed = datetime.strptime(valuation_period, "%Y")
                return parsed.strftime("%Y")
            except ValueError:
                return valuation_period

    valuation_label = f"Valuation Period: {format_valuation_period(valuation_period)}"

    # Create a copy and format the data
    excel_df = df.copy()
    if selected_countries is not None:
        selected_columns = [col for col in selected_countries if col in excel_df.columns]
        excel_df = excel_df[selected_columns]
    excel_df = excel_df.reset_index().rename(columns={"index": "Time"})
    
    # Prepare underlying data (monthly raw data for all countries)
    underlying_df = pd.concat([add_most_recent_row(raw_data), raw_data.copy()])
    underlying_df = underlying_df.reset_index().rename(columns={"index": "Time"})
    
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        excel_df.to_excel(writer, sheet_name="Selected Countries", index=False, startrow=2)
        underlying_df.to_excel(writer, sheet_name="Underlying Data", index=False, startrow=2)
        
        # Get both worksheets
        ws_selected = writer.sheets["Selected Countries"]
        ws_underlying = writer.sheets["Underlying Data"]
        
        # Add metadata row at the top for both sheets
        today_date = datetime.now().strftime("%B %d, %Y")
        metadata_text = f'Data from IMF website (https://data.imf.org/en/datasets/IMF.STA.CPI) as of "{today_date}". See Github Repo for underlying calculations (https://github.com/KnownKey/imf-cpi-app)'
        
        for ws in [ws_selected, ws_underlying]:
            ws['A1'] = metadata_text
            ws['A1'].font = Font(italic=True, size=9)
            ws['A2'] = valuation_label
            ws['A2'].font = Font(italic=True, size=9)
        
        # Color the Underlying Data tab gray
        ws_underlying.sheet_properties.tabColor = "D3D3D3"
        
        # Define styles
        header_font = Font(bold=True, size=11)
        header_fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
        header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        border = Border(
            left=Side(style="thin"),
            right=Side(style="thin"),
            top=Side(style="thin"),
            bottom=Side(style="thin")
        )
        
        center_alignment = Alignment(horizontal="center", vertical="center")
        bold_font = Font(bold=True)
        italic_font = Font(italic=True)
        
        # Format both sheets
        for ws, data_df, is_underlying in [(ws_selected, excel_df, False), (ws_underlying, underlying_df, True)]:
            # Format header row (row 3)
            for col_num, value in enumerate(data_df.columns, 1):
                cell = ws.cell(row=3, column=col_num)
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = header_alignment
                cell.border = border
                # Remove "Time" text from first column header
                if col_num == 1:
                    cell.value = ""
            
            # Format data rows (starting from row 4)
            for row_num, row in enumerate(data_df.values, 4):
                is_most_recent_row = row[0] == "Most Recent Data"
                for col_num, value in enumerate(row, 1):
                    cell = ws.cell(row=row_num, column=col_num)
                    cell.border = border
                    
                    # Format first column (Time) - CENTER aligned
                    if col_num == 1:
                        cell.font = bold_font
                        cell.alignment = center_alignment
                        # Italicize "Most Recent Data"
                        if is_most_recent_row:
                            cell.font = Font(bold=True, italic=True)
                        # Format dates in Underlying Data sheet (convert "2026-M03" to "March 2026")
                        elif is_underlying and isinstance(value, str) and "-M" in value:
                            try:
                                year, month_str = value.split("-M")
                                month_num = int(month_str)
                                months_list = ["January", "February", "March", "April", "May", "June", 
                                             "July", "August", "September", "October", "November", "December"]
                                if 1 <= month_num <= 12:
                                    cell.value = f"{months_list[month_num - 1]} {year}"
                            except (ValueError, IndexError):
                                pass
                    else:
                        if is_most_recent_row:
                            cell.font = italic_font
                        # Format numeric cells with 4 decimal places and center alignment
                        if isinstance(value, (int, float, np.integer, np.floating)) and not pd.isna(value):
                            cell.value = round(value, 4)
                            cell.number_format = '0.0000'
                        
                        cell.alignment = center_alignment
            
            # Adjust column widths - different for each sheet
            ws.column_dimensions['A'].width = 20
            col_width = 15 if is_underlying else 30
            for col_num in range(2, len(data_df.columns) + 1):
                ws.column_dimensions[get_column_letter(col_num)].width = col_width
            
            # Set row heights for better text wrapping visibility
            ws.row_dimensions[3].height = 40
    
    buffer.seek(0)
    return buffer.getvalue()



def find_country_by_code(columns, code):
    for col in columns:
        if col.strip().endswith(f"({code})"):
            return col
    return None


def init_session_state():
    defaults = {
        "model_run": False,
        "last_html_table": None,
        "last_selected_countries_data": None,
        "last_selected_countries": None,
        "last_raw_reversed": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def main():
    st.set_page_config(page_title="IMF CPI Model", page_icon="📈", layout="wide")
    st.markdown(APP_STYLES, unsafe_allow_html=True)
    init_session_state()

    country_mapping = load_country_mapping()
    _, raw_reversed = load_imf_data(country_mapping)

    # -----------------------------
    # SIDEBAR
    # -----------------------------
    st.sidebar.header("Selection")

    us_column = get_us_column(raw_reversed.columns)
    default_country_codes = ["GBR", "ESP", "CHN"]
    default_countries = [find_country_by_code(raw_reversed.columns, code) for code in default_country_codes]
    default_countries = [country for country in default_countries if country is not None]

    countries = st.sidebar.multiselect(
        "Select Countries",
        options=raw_reversed.columns.tolist(),
        default=default_countries if len(default_countries) == 3 else raw_reversed.columns[:3].tolist()
    )

    current_year = datetime.now().year
    current_month = datetime.now().month
    months = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]
    month_map = {month: f"M{i+1:02d}" for i, month in enumerate(months)}
    year_options = list(range(1950, current_year + 1))

    year_input = st.sidebar.selectbox("Year", options=year_options, index=len(year_options) - 1)
    month_options = months if year_input < current_year else months[:current_month]
    default_month_index = max(0, current_month - 4)
    month_input = st.sidebar.selectbox(
        "Month",
        options=month_options,
        index=min(default_month_index, len(month_options) - 1),
    )

    valuation_period = f"{year_input}-{month_map[month_input]}"

    # Keep the US series in the working dataset so every selected country can be
    # divided by the US rebased CPI, even when the user did not select USA.
    calculation_countries = list(countries)
    if us_column and us_column not in calculation_countries:
        calculation_countries.append(us_column)

    df = raw_reversed[calculation_countries].copy()

    # -----------------------------
    # RUN MODEL
    # -----------------------------
    st.markdown(
        """
<div class="cpi-titlebar">
    <h1>IMF CPI Indexing</h1>
    <p class="cpi-subtitle">Rebased CPI comparisons with selected countries normalized against the United States CPI series.</p>
</div>
""",
        unsafe_allow_html=True,
    )

    how_col, method_col = st.columns([3, 2])

    with how_col:
        st.markdown(
            """
<div class="cpi-card">
<h3 style='margin-top:0;'>How to Use</h3>
<ol style='margin:0;padding-left:18px;'>
<li>Select the countries you want to analyze from the sidebar.</li>
<li>Choose the valuation year and month (up to the current date).</li>
<li>Click "Run Model" to generate the rebased CPI index.</li>
<li>Review the night-mode table below and download the Excel workbook.</li>
</ol>
</div>
""",
            unsafe_allow_html=True,
        )

    with method_col:
        st.markdown(
            """
<div class="cpi-card">
<h3 style='margin-top:0;'>Methodology</h3>
<p style='margin:0;'>The selected-country rebased CPI is divided by the US rebased CPI. The highlighted term below represents that relative CPI adjustment.</p>
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
        df_dynamic = build_dynamic_dataset(df, valuation_period)

        if df_dynamic is None:
            st.error("Invalid valuation period format")
        else:
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

                most_recent_row = add_most_recent_row(df)
                result_with_summary = pd.concat([most_recent_row, result])
                display_result = (
                    result_with_summary.drop(columns=[us_col])
                    if us_col and us_col in result_with_summary.columns
                    else result_with_summary
                )
                display_df = display_result.reset_index().rename(columns={"index": "Time"}).set_index("Time")
                display_df.index.name = None

                st.session_state.model_run = True
                st.session_state.last_html_table = render_html_table(display_df)
                st.session_state.last_selected_countries_data = result_with_summary.copy()
                st.session_state.last_selected_countries = list(countries)
                st.session_state.last_raw_reversed = raw_reversed.copy()

    if st.session_state.model_run:
        success_col, download_col = st.columns([4, 1])

        with success_col:
            st.success("Model successfully executed")

        today_date = datetime.now().strftime("%Y%m%d")
        filename = f"IMF_CPI_Output_{today_date}.xlsx"
        excel_data = create_styled_excel(
            st.session_state.last_selected_countries_data,
            st.session_state.last_raw_reversed,
            valuation_period,
            st.session_state.last_selected_countries or list(countries),
        )

        with download_col:
            st.download_button(
                label="📥 Download Selected Countries",
                data=excel_data,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

        st.markdown(st.session_state.last_html_table, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(
        f"""
        <div class='cpi-footer'>
            © {datetime.now().year} SC<br>
            Last Updated: {APP_LAST_UPDATED}
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
