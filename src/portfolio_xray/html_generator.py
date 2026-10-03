"""
Standalone HTML Dashboard Generator for Portfolio X-Ray and Deep Thesis.
Renders self-contained, publication-grade ReOrc FinTech HTML reports.
"""

from __future__ import annotations

import json
from typing import Dict


def generate_portfolio_html_report(xray_data: dict) -> str:
    """
    Builds a standalone HTML dashboard report for Portfolio X-Ray mode.
    """
    summary = xray_data.get("summary", {})
    assets = xray_data.get("assets", [])
    look_through = xray_data.get("look_through", {})
    overlap = xray_data.get("overlap", {})
    concentration = xray_data.get("concentration", {})
    risk_return = xray_data.get("risk_return", {})
    port_stats = risk_return.get("portfolio", {})
    bench_stats = risk_return.get("benchmark", {})
    corr_data = risk_return.get("correlation", {})

    port_val = risk_return.get("portfolio_value", 1_000_000)
    currency = risk_return.get("currency", "THB")
    eq_warning = xray_data.get("equal_weight_warning")

    # Dates and series for charting
    dates_json = json.dumps(port_stats.get("dates", []))
    wealth_json = json.dumps(port_stats.get("wealth_index", []))
    bench_wealth_json = json.dumps(bench_stats.get("wealth_index", []))
    drawdown_json = json.dumps(port_stats.get("drawdown_curve", []))

    # Top holdings for bar chart
    top_holdings = look_through.get("top_holdings", [])[:8]
    holding_labels = json.dumps([h["symbol"] for h in top_holdings])
    holding_values = json.dumps([h["effective_pct"] for h in top_holdings])

    html = f"""<!DOCTYPE html>
<html lang="th">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI Portfolio X-Ray Report | ReOrc FinTech</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,600;12..96,700&family=JetBrains+Mono:wght@400;500;600&family=Noto+Sans+Thai:wght@300;400;500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    :root {{
      --bg-cream: #fbfbf9;
      --card-bg: #ffffff;
      --border-color: #e2e8f0;
      --border-subtle: #f1f5f9;
      --text-main: #0f172a;
      --text-muted: #64748b;
      --text-soft: #94a3b8;
      --emerald-accent: #059669;
      --emerald-light: #ecfdf5;
      --rose-accent: #e11d48;
      --rose-light: #fff1f2;
      --amber-accent: #d97706;
      --amber-light: #fffbeb;
      --indigo-accent: #4f46e5;
      --font-display: 'Bricolage Grotesque', sans-serif;
      --font-body: 'Plus Jakarta Sans', 'Noto Sans Thai', sans-serif;
      --font-mono: 'JetBrains Mono', monospace;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background-color: var(--bg-cream);
      color: var(--text-main);
      font-family: var(--font-body);
      line-height: 1.6;
      padding: 32px 20px;
    }}
    .container {{
      max-width: 1200px;
      margin: 0 auto;
    }}
    .header {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 28px;
      padding-bottom: 20px;
      border-bottom: 1px solid var(--border-color);
    }}
    .brand-tag {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-family: var(--font-mono);
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--emerald-accent);
      background: var(--emerald-light);
      padding: 3px 8px;
      border-radius: 4px;
      font-weight: 600;
      margin-bottom: 8px;
    }}
    .title {{
      font-family: var(--font-display);
      font-size: 28px;
      font-weight: 700;
      letter-spacing: -0.02em;
    }}
    .subtitle {{
      color: var(--text-muted);
      font-size: 14px;
      margin-top: 4px;
    }}
    .alert-banner {{
      background: var(--amber-light);
      border: 1px solid #fde68a;
      color: #92400e;
      padding: 12px 16px;
      border-radius: 8px;
      font-size: 13px;
      margin-bottom: 24px;
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .kpi-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 16px;
      margin-bottom: 28px;
    }}
    .kpi-card {{
      background: var(--card-bg);
      border: 1px solid var(--border-color);
      border-radius: 10px;
      padding: 18px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.02);
    }}
    .kpi-label {{
      font-size: 12px;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.05em;
      font-weight: 600;
    }}
    .kpi-value {{
      font-family: var(--font-mono);
      font-size: 26px;
      font-weight: 700;
      margin: 6px 0;
      color: var(--text-main);
    }}
    .kpi-subtext {{
      font-size: 12px;
      color: var(--text-muted);
    }}
    .card {{
      background: var(--card-bg);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      padding: 24px;
      margin-bottom: 24px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.02);
    }}
    .card-title {{
      font-family: var(--font-display);
      font-size: 18px;
      font-weight: 700;
      margin-bottom: 16px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .chart-container {{
      position: relative;
      width: 100%;
      height: 280px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }}
    th {{
      background: #f8fafc;
      text-align: left;
      padding: 10px 14px;
      font-weight: 600;
      color: var(--text-muted);
      border-bottom: 1px solid var(--border-color);
      text-transform: uppercase;
      font-size: 11px;
      letter-spacing: 0.05em;
    }}
    td {{
      padding: 12px 14px;
      border-bottom: 1px solid var(--border-subtle);
    }}
    tr:last-child td {{ border-bottom: none; }}
    .badge {{
      display: inline-block;
      padding: 2px 7px;
      border-radius: 4px;
      font-size: 11px;
      font-family: var(--font-mono);
      font-weight: 600;
    }}
    .badge-core {{ background: #eff6ff; color: #1d4ed8; }}
    .badge-growth {{ background: #fdf2f8; color: #be185d; }}
    .badge-income {{ background: #f0fdf4; color: #15803d; }}
    .badge-hedge {{ background: #fefce8; color: #a16207; }}
    .grid-2 {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 24px;
    }}
    @media(max-width: 860px) {{
      .grid-2 {{ grid-template-columns: 1fr; }}
    }}
    .callout {{
      background: #f8fafc;
      border-left: 3px solid var(--indigo-accent);
      padding: 12px 16px;
      border-radius: 0 6px 6px 0;
      font-size: 13px;
      margin-top: 14px;
    }}
  </style>
</head>
<body>
  <div class="container">
    <header class="header">
      <div>
        <div class="brand-tag">● AI Portfolio X-Ray Pro</div>
        <h1 class="title">Institutional Portfolio Analysis</h1>
        <div class="subtitle">วิเคราะห์เชิงลึก: Look-Through, Overlap, Concentration, และ Risk Breakdown</div>
      </div>
      <div style="text-align: right;">
        <div style="font-family: var(--font-mono); font-size: 13px; font-weight: 600;">Portfolio: {port_val:,.0f} {currency}</div>
        <div style="font-size: 12px; color: var(--text-muted);">As of: {risk_return.get('end_date', 'Latest')}</div>
      </div>
    </header>

    {f'<div class="alert-banner">⚠️ <strong>ข้อความระวัง:</strong> {eq_warning}</div>' if eq_warning else ''}

    <!-- KPI Metric Cards -->
    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-label">Annualized Return (CAGR)</div>
        <div class="kpi-value" style="color: {'var(--emerald-accent)' if port_stats.get('cagr_pct', 0) >= 0 else 'var(--rose-accent)'};">
          {port_stats.get('cagr_pct', 0):+.2f}%
        </div>
        <div class="kpi-subtext">Benchmark (S&P 500): {bench_stats.get('cagr_pct', 0):+.2f}%</div>
      </div>

      <div class="kpi-card">
        <div class="kpi-label">Max Drawdown (สถิติลดลงสูงสุด)</div>
        <div class="kpi-value" style="color: var(--rose-accent);">
          {port_stats.get('max_drawdown_pct', 0):.2f}%
        </div>
        <div class="kpi-subtext">เงินลดลงจริงสูงสุด: {port_stats.get('real_cash_loss', 0):,.0f} {currency}</div>
      </div>

      <div class="kpi-card">
        <div class="kpi-label">Risk-Adjusted (Sharpe / Sortino)</div>
        <div class="kpi-value">
          {port_stats.get('sharpe_ratio', 0):.2f} <span style="font-size: 16px; color: var(--text-muted);">/ {port_stats.get('sortino_ratio', 0):.2f}</span>
        </div>
        <div class="kpi-subtext">Calmar Ratio: {port_stats.get('calmar_ratio', 0):.2f}</div>
      </div>

      <div class="kpi-card">
        <div class="kpi-label">Concentration (Effective Bets)</div>
        <div class="kpi-value">
          {concentration.get('effective_positions', 'N/A')} <span style="font-size: 14px; font-weight: normal; color: var(--text-muted);">Bets</span>
        </div>
        <div class="kpi-subtext">{concentration.get('verdict', '')}</div>
      </div>
    </div>

    <!-- Charts Row -->
    <div class="grid-2">
      <div class="card">
        <div class="card-title">
          <span>Cumulative Wealth Growth (vs S&P 500)</span>
          <span style="font-size: 12px; font-weight: normal; color: var(--text-muted);">Base 1.0</span>
        </div>
        <div class="chart-container">
          <canvas id="wealthChart"></canvas>
        </div>
      </div>

      <div class="card">
        <div class="card-title">
          <span>Look-Through Top Effective Holdings</span>
          <span style="font-size: 12px; font-weight: normal; color: var(--text-muted);">Aggregate Exposure %</span>
        </div>
        <div class="chart-container">
          <canvas id="holdingsChart"></canvas>
        </div>
      </div>
    </div>

    <!-- Portfolio Stated Holdings Table -->
    <div class="card">
      <div class="card-title">Stated Asset Allocation & Roles</div>
      <table>
        <thead>
          <tr>
            <th>Symbol</th>
            <th>Name</th>
            <th>Asset Class</th>
            <th>Role</th>
            <th>Stated Weight</th>
            <th>Current Value</th>
            <th>Expense Ratio</th>
          </tr>
        </thead>
        <tbody>
          {''.join([f'''
          <tr>
            <td><strong style="font-family: var(--font-mono);">{a['symbol']}</strong></td>
            <td>{a.get('name', a['symbol'])}</td>
            <td>{a.get('asset_class', 'Asset')}</td>
            <td><span class="badge badge-core">{a.get('role', 'CORE')}</span></td>
            <td style="font-family: var(--font-mono); font-weight: 600;">{a.get('weight_pct', 0):.1f}%</td>
            <td style="font-family: var(--font-mono);">{port_val * (a.get('weight', 0)):,.0f} {currency}</td>
            <td style="font-family: var(--font-mono);">{a.get('expense_ratio', 0) * 100:.2f}%</td>
          </tr>
          ''' for a in assets])}
        </tbody>
      </table>
    </div>

    <!-- Overlap & Concentration Analysis Row -->
    <div class="grid-2">
      <div class="card">
        <div class="card-title">Overlap Redundancy Check</div>
        {''.join([f'''
        <div class="callout" style="border-left-color: {'var(--rose-accent)' if p['severity'] == 'HIGH' else 'var(--amber-accent)'}; margin-bottom: 12px;">
          <strong>{p['asset_a']} ↔ {p['asset_b']} ทับซ้อน {p['overlap_pct']}%</strong>
          <div style="font-size: 12px; color: var(--text-muted); margin-top: 4px;">{p['explanation']}</div>
        </div>
        ''' for p in overlap.get('redundant_pairs', [])]) if overlap.get('redundant_pairs') else '<div style="color: var(--text-muted); font-size: 13px;">ไม่พบสินทรัพย์ที่มีการทับซ้อนกันเกินเกณฑ์ (>25%) พอร์ตมีการแบ่งบทบาทได้ดี</div>'}
      </div>

      <div class="card">
        <div class="card-title">Underwater Drawdown Curve</div>
        <div class="chart-container">
          <canvas id="drawdownChart"></canvas>
        </div>
      </div>
    </div>

  </div>

  <script>
    const dates = {dates_json};
    const wealthData = {wealth_json};
    const benchWealth = {bench_wealth_json};
    const ddData = {drawdown_json};

    // Wealth Chart
    new Chart(document.getElementById('wealthChart'), {{
      type: 'line',
      data: {{
        labels: dates,
        datasets: [
          {{
            label: 'Portfolio Total Return',
            data: wealthData,
            borderColor: '#059669',
            backgroundColor: 'rgba(5, 150, 105, 0.05)',
            borderWidth: 2,
            pointRadius: 0,
            fill: true
          }},
          {{
            label: 'S&P 500 (VOO)',
            data: benchWealth,
            borderColor: '#94a3b8',
            borderWidth: 1.5,
            borderDash: [4, 4],
            pointRadius: 0,
            fill: false
          }}
        ]
      }},
      options: {{
        responsive: true,
        maintainAspectRatio: false,
        plugins: {{ legend: {{ position: 'top', labels: {{ font: {{ family: 'Plus Jakarta Sans', size: 11 }} }} }} }},
        scales: {{
          x: {{ display: false }},
          y: {{ grid: {{ color: '#f1f5f9' }} }}
        }}
      }}
    }});

    // Holdings Bar Chart
    new Chart(document.getElementById('holdingsChart'), {{
      type: 'bar',
      data: {{
        labels: {holding_labels},
        datasets: [{{
          label: 'Effective Weight %',
          data: {holding_values},
          backgroundColor: '#4f46e5',
          borderRadius: 4
        }}]
      }},
      options: {{
        responsive: true,
        maintainAspectRatio: false,
        plugins: {{ legend: {{ display: false }} }},
        scales: {{
          x: {{ grid: {{ display: false }} }},
          y: {{ grid: {{ color: '#f1f5f9' }} }}
        }}
      }}
    }});

    // Drawdown Chart
    new Chart(document.getElementById('drawdownChart'), {{
      type: 'line',
      data: {{
        labels: dates,
        datasets: [{{
          label: 'Drawdown %',
          data: ddData,
          borderColor: '#e11d48',
          backgroundColor: 'rgba(225, 29, 72, 0.1)',
          borderWidth: 1.5,
          pointRadius: 0,
          fill: true
        }}]
      }},
      options: {{
        responsive: true,
        maintainAspectRatio: false,
        plugins: {{ legend: {{ display: false }} }},
        scales: {{
          x: {{ display: false }},
          y: {{ grid: {{ color: '#f1f5f9' }} }}
        }}
      }}
    }});
  </script>
</body>
</html>"""
    return html


def generate_thesis_html_report(thesis_data: dict) -> str:
    """
    Builds a standalone HTML dashboard report for Deep Thesis mode.
    """
    sym = thesis_data.get("symbol", "N/A")
    name = thesis_data.get("name", sym)
    summary = thesis_data.get("summary", "")
    fin = thesis_data.get("financials", {})
    mult = thesis_data.get("multiples", {})
    dcf = thesis_data.get("reverse_dcf", {})
    scenarios = dcf.get("scenarios", {})
    moats = thesis_data.get("moat_analysis", [])
    pre_mortem = thesis_data.get("pre_mortem", [])

    cur_p = thesis_data.get("current_price", 0.0)
    implied_g = dcf.get("implied_fcf_growth_pct", "N/A")

    html = f"""<!DOCTYPE html>
<html lang="th">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Deep Thesis & Reverse DCF: {sym} | ReOrc FinTech</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,600;12..96,700&family=JetBrains+Mono:wght@400;500;600&family=Noto+Sans+Thai:wght@300;400;500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg-cream: #fbfbf9;
      --card-bg: #ffffff;
      --border-color: #e2e8f0;
      --border-subtle: #f1f5f9;
      --text-main: #0f172a;
      --text-muted: #64748b;
      --emerald-accent: #059669;
      --rose-accent: #e11d48;
      --amber-accent: #d97706;
      --indigo-accent: #4f46e5;
      --font-display: 'Bricolage Grotesque', sans-serif;
      --font-body: 'Plus Jakarta Sans', 'Noto Sans Thai', sans-serif;
      --font-mono: 'JetBrains Mono', monospace;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background-color: var(--bg-cream);
      color: var(--text-main);
      font-family: var(--font-body);
      line-height: 1.6;
      padding: 36px 20px;
    }}
    .container {{ max-width: 1100px; margin: 0 auto; }}
    .header {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 24px;
      padding-bottom: 20px;
      border-bottom: 1px solid var(--border-color);
    }}
    .brand-tag {{
      display: inline-block;
      font-family: var(--font-mono);
      font-size: 11px;
      color: var(--indigo-accent);
      background: #eef2ff;
      padding: 3px 8px;
      border-radius: 4px;
      font-weight: 600;
      margin-bottom: 8px;
    }}
    .title {{ font-family: var(--font-display); font-size: 32px; font-weight: 700; }}
    .subtitle {{ color: var(--text-muted); font-size: 14px; margin-top: 4px; }}
    .kpi-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 16px;
      margin-bottom: 28px;
    }}
    .kpi-card {{
      background: var(--card-bg);
      border: 1px solid var(--border-color);
      border-radius: 10px;
      padding: 18px;
    }}
    .kpi-label {{ font-size: 12px; color: var(--text-muted); text-transform: uppercase; font-weight: 600; }}
    .kpi-value {{ font-family: var(--font-mono); font-size: 26px; font-weight: 700; margin: 4px 0; }}
    .card {{
      background: var(--card-bg);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      padding: 24px;
      margin-bottom: 24px;
    }}
    .card-title {{ font-family: var(--font-display); font-size: 18px; font-weight: 700; margin-bottom: 16px; }}
    .scenario-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr 1fr;
      gap: 16px;
      margin-top: 16px;
    }}
    .scenario-box {{
      padding: 16px;
      border-radius: 8px;
      border: 1px solid var(--border-color);
      background: #fafaf9;
    }}
    .tag {{
      display: inline-block;
      background: #f1f5f9;
      color: #334155;
      padding: 4px 10px;
      border-radius: 20px;
      font-size: 12px;
      margin-right: 6px;
      margin-bottom: 6px;
    }}
  </style>
</head>
<body>
  <div class="container">
    <header class="header">
      <div>
        <div class="brand-tag">● Deep Thesis & Valuation</div>
        <h1 class="title">{name} ({sym})</h1>
        <div class="subtitle">{thesis_data.get('sector', '')} | {thesis_data.get('industry', '')}</div>
      </div>
      <div style="text-align: right;">
        <div style="font-family: var(--font-mono); font-size: 28px; font-weight: 700;">${cur_p:,.2f}</div>
        <div style="font-size: 12px; color: var(--text-muted);">Market Cap: ${thesis_data.get('market_cap', 0)/1e9:,.1f}B</div>
      </div>
    </header>

    <!-- Key Metrics -->
    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-label">Market Implied FCF Growth</div>
        <div class="kpi-value" style="color: var(--indigo-accent);">{implied_g}%</div>
        <div style="font-size: 12px; color: var(--text-muted);">10-yr CAGR to justify price</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Trailing / Fwd P/E</div>
        <div class="kpi-value">{mult.get('trailing_pe', 'N/A')} <span style="font-size: 16px; color: var(--text-muted);">/ {mult.get('forward_pe', 'N/A')}</span></div>
        <div style="font-size: 12px; color: var(--text-muted);">EV/EBITDA: {mult.get('ev_to_ebitda', 'N/A')}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Gross / Operating Margin</div>
        <div class="kpi-value">{fin.get('gross_margin_pct', 0):.1f}% <span style="font-size: 16px; color: var(--text-muted);">/ {fin.get('operating_margin_pct', 0):.1f}%</span></div>
        <div style="font-size: 12px; color: var(--text-muted);">FCF Margin: {fin.get('fcf_margin_pct', 0):.1f}%</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">ROE / Capital Efficiency</div>
        <div class="kpi-value">{fin.get('roe_pct', 0):.1f}%</div>
        <div style="font-size: 12px; color: var(--text-muted);">Beta: {thesis_data.get('beta', 1.0)}</div>
      </div>
    </div>

    <!-- Reverse DCF Analysis -->
    <div class="card">
      <div class="card-title">Reverse DCF — What Expectations are Baked In?</div>
      <p style="font-size: 14px; margin-bottom: 12px;">{dcf.get('reality_check', '')}</p>

      <div class="scenario-grid">
        <div class="scenario-box">
          <strong style="color: var(--rose-accent);">Bear Case</strong>
          <div style="font-size: 12px; color: var(--text-muted); margin-top: 4px;">FCF Growth: {scenarios.get('bear', {}).get('assumed_growth_pct', 0)}%</div>
          <div style="font-family: var(--font-mono); font-size: 20px; font-weight: 700; margin: 8px 0;">${scenarios.get('bear', {}).get('target_price', 0):.2f}</div>
          <div style="font-size: 12px; color: var(--rose-accent);">{scenarios.get('bear', {}).get('upside_downside_pct', 0):+.1f}% vs current</div>
        </div>

        <div class="scenario-box" style="border-color: var(--indigo-accent); background: #fdfefe;">
          <strong style="color: var(--indigo-accent);">Base Case</strong>
          <div style="font-size: 12px; color: var(--text-muted); margin-top: 4px;">FCF Growth: {scenarios.get('base', {}).get('assumed_growth_pct', 0)}%</div>
          <div style="font-family: var(--font-mono); font-size: 20px; font-weight: 700; margin: 8px 0;">${scenarios.get('base', {}).get('target_price', 0):.2f}</div>
          <div style="font-size: 12px; color: {'var(--emerald-accent)' if scenarios.get('base', {}).get('upside_downside_pct', 0) >= 0 else 'var(--rose-accent)'};">
            {scenarios.get('base', {}).get('upside_downside_pct', 0):+.1f}% vs current
          </div>
        </div>

        <div class="scenario-box">
          <strong style="color: var(--emerald-accent);">Bull Case</strong>
          <div style="font-size: 12px; color: var(--text-muted); margin-top: 4px;">FCF Growth: {scenarios.get('bull', {}).get('assumed_growth_pct', 0)}%</div>
          <div style="font-family: var(--font-mono); font-size: 20px; font-weight: 700; margin: 8px 0;">${scenarios.get('bull', {}).get('target_price', 0):.2f}</div>
          <div style="font-size: 12px; color: var(--emerald-accent);">{scenarios.get('bull', {}).get('upside_downside_pct', 0):+.1f}% vs current</div>
        </div>
      </div>
    </div>

    <!-- Moat & Pre-Mortem -->
    <div class="card">
      <div class="card-title">Competitive Moat Analysis</div>
      <div>
        {''.join([f'<span class="tag">🛡️ {m}</span>' for m in moats])}
      </div>
    </div>

    <div class="card">
      <div class="card-title" style="color: var(--rose-accent);">Pre-Mortem — อะไรทำให้ Thesis นี้ล้มเหลว?</div>
      {''.join([f'<div style="font-size: 13px; margin-bottom: 8px; color: #475569;">{item}</div>' for item in pre_mortem])}
    </div>
  </div>
</body>
</html>"""
    return html
