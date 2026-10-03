# Thai SMC Dashboard

Standalone dashboard for Thai-market Smart Money Concept research.

- **Live Production URL:** [https://thai-smc-dashboard.onrender.com/](https://thai-smc-dashboard.onrender.com/)
- **UI Design System:** ReOrc-inspired Editorial FinTech Theme (Dual Light/Dark support)

## Scope

- Runs independently from `tong_trading`.
- Generates its own local universe from Thai tickers.
- Builds four standalone source buckets:
  - `VCP`
  - `CANSLIM`
  - `DIP_BUY`
  - `MOMENTUM`
- Sends candidates from those buckets into the SMC analyzer.
- Shows each candidate's source bucket before SMC scoring.
- Keeps `RR >= 1:3` as the trade-quality filter.
- Uses fallback sample OHLCV data when live data cannot be reached.

## Run

```powershell
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install -e .
python dashboard\app.py
```

Open:

```text
http://127.0.0.1:5080/
```

Or use:

```powershell
.\run_dashboard.bat
```

## API

- `GET /api/scan`
- `GET /api/scan?symbols=PTT,AOT,CPALL`
- `GET /api/sources`
- `GET /api/symbol/PTT`

## Notes

The VCP, CANSLIM, Dip Buy, and Momentum buckets are local proxy screeners. They are intended to create a clean standalone candidate universe before SMC analysis, not to exactly reproduce the previous project's reports.

This is research tooling only, not financial advice or an automated trading signal.
