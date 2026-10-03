# Thai SMC Dashboard

Standalone dashboard for Thai-market Smart Money Concept research.

- **Live Production URL:** [https://thai-smc-dashboard.onrender.com/](https://thai-smc-dashboard.onrender.com/)
- **UI Design System:** ReOrc-inspired Editorial FinTech Theme (Dual Light/Dark support)
- **New Feature:** AI Portfolio X-Ray Pro & Deep Thesis Mode (Look-Through, Overlap Matrix, Real Currency Drawdown, Reverse DCF Implied Growth)

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
- Keeps `RR >= 1:2` as the trade-quality filter.
- **AI Portfolio X-Ray Pro & Deep Thesis:**
  - Decomposes ETF holdings (Look-Through exposure) to reveal hidden Big Tech concentration.
  - Overlap Matrix $\sum \min(w_A, w_B)$ alerting on redundancies (>25% overlap) + Educational "Overlap vs Correlation" guide.
  - Translates Maximum Drawdown into real currency values (e.g. -119,559 THB on 1M THB portfolio).
  - Cross-Asset Weekly Correlation Matrix aligning 24/7 Crypto (BTC) with 5D US Equities.
  - Variance Attribution / Risk Contribution (%RC) identifying volatility drivers.
  - Position Sizing & Rebalancing Action Plan with actionable cash/weight adjustments.
  - Blended Portfolio Expense Ratio (Fee Drag) & Macro Stress Test Matrix simulating 4 crisis scenarios (Tech de-rating, Rate spike, Global recession, Stagflation).
  - Deep Thesis Mode for single assets with Reverse DCF 10-Yr FCF CAGR solver and Bull/Base/Bear scenarios.
  - Wall Street Analyst Consensus, rating distributions, price target ranges (Mean/High/Low), and Upside %.
  - Investment Verdict & Strategic Action (ACCUMULATE / HOLD / WAIT) with Base Case Fair Value.
  - TAM & S-Curve Lifecycle Analysis and 3-Year Historical Financial Statement Trends.
  - Standalone single-file HTML report export and one-click structured Markdown copy.

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
- `POST /api/xray/analyze` — Portfolio X-Ray & Deep Thesis JSON API
- `POST /api/xray/export-html` — Standalone HTML report export

## Notes

The VCP, CANSLIM, Dip Buy, and Momentum buckets are local proxy screeners. They are intended to create a clean standalone candidate universe before SMC analysis, not to exactly reproduce the previous project's reports.

This is research tooling only, not financial advice or an automated trading signal.
