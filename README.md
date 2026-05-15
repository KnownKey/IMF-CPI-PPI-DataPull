# IMF CPI/PPI Raw Export

Command-line exporter for raw monthly IMF CPI and PPI index data. There is no Streamlit app and no rebasing/model interface: the script pulls IMF observations and writes them directly to a styled Excel workbook.

## Output

The workbook contains two sheets:

- `CPI Raw Data` from IMF dataflow `CPI`, key `.CPI._T.SRP_IX.M`
- `PPI Raw Data` from IMF dataflow `PPI`, key `.PPI.IX.M`

Each sheet keeps the prior Excel styling pattern: metadata rows, blank first header cell, gray bold headers, centered values, four-decimal numeric formatting, formatted month labels, and a `Most Recent Data` row showing the latest available observation per country.

The default filename is based on the latest observation period in the downloaded data, for example:

```bash
IMF_CPI_PPI_Raw_202603.xlsx
```

## Install

```bash
pip install -r requirements.txt
```

## Run

Export all available IMF countries:

```bash
python app.py
```

Export specific countries:

```bash
python app.py --countries USA,CAN,GBR
```

Limit the IMF date range:

```bash
python app.py --start-period 2000-M01 --end-period 2026-M03
```

Choose an output path:

```bash
python app.py --output output/imf_raw.xlsx
```

## Tests

```bash
python -m pytest
```

The tests cover key construction, period/date handling, raw pivoting, output filename dating, and Excel workbook formatting. They do not call the IMF API.

## Data Sources

- CPI: https://data.imf.org/en/datasets/IMF.STA:CPI
- PPI: https://data.imf.org/en/datasets/IMF.STA:PPI
