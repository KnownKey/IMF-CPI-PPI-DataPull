# IMF CPI App

Streamlit app for building IMF CPI-based relative indexing tables and exporting the results to Excel.

## What It Does

- Downloads CPI series from the IMF data service.
- Lets you select countries and a valuation period.
- Rebases CPI values to the selected period.
- Normalizes selected-country CPI movement against the United States CPI series.
- Exports the selected country output plus underlying data to an Excel workbook.

## Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

The app opens on Streamlit's default local port, usually `http://localhost:8501`.

## Tests

```bash
python -m pytestpytest
```

The tests cover the pure calculation helpers and do not call the IMF network data load.

## Data Source

CPI data is retrieved from the IMF CPI dataset:
https://data.imf.org/en/datasets/IMF.STA.CPI
