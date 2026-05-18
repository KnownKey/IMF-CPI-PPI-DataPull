# IMF & BLS CPI/PPI Raw Export

Command-line exporter for raw monthly index data from the IMF and BLS. The script pulls observations and writes them directly to a styled Excel workbook.

## Output

The workbook contains three sheets:

- `CPI Raw Data` from IMF dataflow `CPI`
- `PPI Raw Data` from IMF dataflow `PPI`
- `BLS PPI Raw Data` from BLS PPI series `WPUFD4` (Final Demand)

### Excel Structure & Styling
Each sheet follows a consistent professional layout:
- **Metadata**: Header rows with data source links and generation timestamps.
- **Headers (Row 3)**: Bold, light gray headers displaying full **Country Names**.
- **Summary Row (Row 4)**: Bold, italic, light gray row displaying 3-letter **Country Codes** (ISO3).
- **Summary Row (Row 5)**: `Most Recent Data` row showing the latest available period per country.
- **Year Column**: A dedicated column on the far left displaying the year for all data rows.
- **Data Formatting**: Centered values, four-decimal numeric precision, and formatted month labels (e.g., "January 2024").

The default filename is based on the current date:
```bash
IMF_CPI_PPI_Raw_20260518.xlsx
```

## Install

```bash
pip install -r requirements.txt
```

## Run

Export all available IMF countries (and USA for BLS):

```bash
python app.py
```

Export specific countries:

```bash
python app.py --countries USA,CAN,GBR
```

Limit the date range:

```bash
python app.py --start-period 2000-M01 --end-period 2026-M03
```

## Tests

```bash
PYTHONPATH=. pytest
```

The tests cover data fetching (mocked), pivoting, structural layout, and Excel formatting for both IMF and BLS sources.

## Data Sources

- IMF CPI: https://data.imf.org/en/datasets/IMF.STA:CPI
- IMF PPI: https://data.imf.org/en/datasets/IMF.STA:PPI
- BLS PPI: https://www.bls.gov/ppi/ (Series WPUFD4)
