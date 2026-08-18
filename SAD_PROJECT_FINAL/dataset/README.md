# Portuguese Used Car Market

Used car listings for price, mileage, year, fuel, transmission, and regional analysis.

## Files

- Primary CSV/JSON data files are kept at the dataset root for simple Kaggle notebook access.
- `car_market_file_manifest.csv` describes every primary CSV file.
- `data_dictionary.csv` documents columns, types, units, and scope.
- `validation_report.csv` summarizes publication checks.

## Quick start

```python
import pandas as pd

manifest = pd.read_csv('/kaggle/input/portuguese-car-market/car_market_file_manifest.csv')
display(manifest.head())
```

## Notes

The files are analysis-ready snapshots from public or official source material. Treat them as research and education datasets; validate source values before operational or financial decisions.
