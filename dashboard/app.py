import json
import time
import math
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()
ROOT_DIR = BASE_DIR.parent.resolve()
if str(ROOT_DIR / "src") not in sys.path:
    sys.path.insert(0, str(ROOT_DIR / "src"))
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from flask import Flask, render_template, request, jsonify
from th_smc.engine import scan_symbols, collect_candidate_sources
from db import SessionLocal, Scan, ScanResult, Base, engine

app = Flask(__name__)

# Create tables
Base.metadata.create_all(bind=engine)

_SCAN_CACHE = {}

def clean_nan(obj):
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    elif isinstance(obj, dict):
        return {k: clean_nan(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_nan(v) for v in obj]
    return obj


def _load_scan_cache(min_rr: float, market: str) -> dict | None:
    key = f"{market}_{min_rr}"
    if key in _SCAN_CACHE:
        data = _SCAN_CACHE[key]["data"]
        if data.get("count", 0) > 0 and len(data.get("results", [])) > 0:
            return data
        else:
            del _SCAN_CACHE[key]
        
    with SessionLocal() as session:
        scan = (
            session.query(Scan)
            .filter(Scan.market == market, Scan.min_rr == min_rr, Scan.count > 0)
            .order_by(Scan.created_at.desc())
            .first()
        )
        if not scan or not scan.results:
            return None
            
        data = {
            "generated_at": scan.created_at.strftime("%Y-%m-%d %H:%M:%S") if scan.created_at else None,
            "universe_meta": scan.universe_meta,
            "source_summary": scan.source_summary,
            "passed_counts": scan.passed_counts,
            "selected_counts": scan.selected_counts,
            "count": scan.count,
            "armed_count": scan.armed_count,
            "fallback_used": scan.fallback_used,
            "data_policy": scan.data_policy,
            "source_reports": scan.source_reports,
            "results": [
                {
                    "symbol": r.symbol,
                    "name": r.name,
                    "sector": r.sector,
                    "decision": r.decision,
                    "side": r.side,
                    "score": r.score,
                    "rr": r.rr,
                    **(r.details or {})
                } for r in scan.results
            ]
        }
        if len(data["results"]) == 0:
            return None
        _SCAN_CACHE[key] = {"data": data, "at": scan.created_at.timestamp()}
        return data


def _save_scan_cache(data: dict, min_rr: float, market: str) -> None:
    if not data or data.get("count", 0) == 0 or len(data.get("results", [])) == 0:
        return
    data = clean_nan(data)
    with SessionLocal() as session:
        scan = Scan(
            market=market,
            min_rr=min_rr,
            universe_meta=data.get("universe_meta", {}),
            source_summary=data.get("source_summary", {}),
            passed_counts=data.get("passed_counts", {}),
            selected_counts=data.get("selected_counts", {}),
            count=data.get("count", 0),
            armed_count=data.get("armed_count", 0),
            fallback_used=data.get("fallback_used", False),
            data_policy=data.get("data_policy", ""),
            source_reports=data.get("source_reports", {}),
        )
        for res in data.get("results", []):
            details = {k: v for k, v in res.items() if k not in ["symbol", "name", "sector", "decision", "side", "score", "rr"]}
            r = ScanResult(
                symbol=res.get("symbol"),
                name=res.get("name"),
                sector=res.get("sector"),
                decision=res.get("decision"),
                side=res.get("side"),
                score=res.get("score"),
                rr=res.get("rr"),
                details=details
            )
            scan.results.append(r)
        
        session.add(scan)
        session.commit()
        
    _SCAN_CACHE[f"{market}_{min_rr}"] = {"data": data, "at": time.time()}


@app.get("/")
def index():
    return render_template("dashboard.html")


@app.get("/api/scan")
def api_scan():
    raw = request.args.get("symbols", "")
    symbols = [part.strip() for part in raw.split(",") if part.strip()] if raw else None
    refresh = request.args.get("refresh") == "1"
    min_rr_str = request.args.get("min_rr", "2.0")
    market = request.args.get("market", "TH").upper()
    if market not in ["TH", "US", "GOLD", "US_MEDIUM_TERM"]:
        market = "TH"
    
    try:
        min_rr = float(min_rr_str)
    except ValueError:
        min_rr = 2.0

    if symbols:
        data = clean_nan(scan_symbols(symbols, min_rr=min_rr, market=market))
        return jsonify(data)

    cached = _load_scan_cache(min_rr, market)
    if cached and not refresh and cached.get("count", 0) > 0 and len(cached.get("results", [])) > 0:
        return jsonify(clean_nan(cached))

    try:
        data = scan_symbols(None, min_rr=min_rr, market=market)
        data = clean_nan(data)
        if data.get("count", 0) > 0 and len(data.get("results", [])) > 0:
            _save_scan_cache(data, min_rr, market)
        return jsonify(data)
    except Exception as e:
        if cached:
            return jsonify(clean_nan(cached))
        return jsonify({"error": str(e)}), 500


@app.get("/api/sources")
def api_sources():
    market = request.args.get("market", "TH").upper()
    if market not in ["TH", "US", "GOLD", "US_MEDIUM_TERM"]:
        market = "TH"
    return jsonify(clean_nan(collect_candidate_sources(market=market)))


@app.post("/api/xray/analyze")
def api_xray_analyze():
    from portfolio_xray import analyze as xray_analyze
    body = request.get_json(silent=True) or {}
    raw_input = body.get("input", "").strip()
    if not raw_input:
        return jsonify({"error": "Missing input string"}), 400

    try:
        portfolio_val = float(body.get("portfolio_value", 1_000_000))
    except (ValueError, TypeError):
        portfolio_val = 1_000_000.0

    currency = str(body.get("currency", "THB")).upper()
    period = str(body.get("period", "3y"))
    benchmark = str(body.get("benchmark", "VOO")).upper()

    try:
        result = xray_analyze(
            raw_input=raw_input,
            portfolio_value=portfolio_val,
            currency=currency,
            period=period,
            benchmark_symbol=benchmark,
        )
        return jsonify(clean_nan(result))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.post("/api/xray/export-html")
def api_xray_export_html():
    from portfolio_xray import analyze as xray_analyze
    body = request.get_json(silent=True) or {}
    raw_input = body.get("input", "").strip()
    if not raw_input:
        return "Missing input string", 400

    try:
        portfolio_val = float(body.get("portfolio_value", 1_000_000))
    except (ValueError, TypeError):
        portfolio_val = 1_000_000.0

    currency = str(body.get("currency", "THB")).upper()
    period = str(body.get("period", "3y"))
    benchmark = str(body.get("benchmark", "VOO")).upper()

    try:
        result = xray_analyze(
            raw_input=raw_input,
            portfolio_value=portfolio_val,
            currency=currency,
            period=period,
            benchmark_symbol=benchmark,
        )
        html_content = result.get("html_report", "<!DOCTYPE html><html><body>No report generated</body></html>")
        mode = result.get("mode", "portfolio")
        return html_content, 200, {
            "Content-Type": "text/html; charset=utf-8",
            "Content-Disposition": f"attachment; filename=xray_report_{mode}.html"
        }
    except Exception as e:
        return f"Error generating HTML report: {e}", 500


if __name__ == "__main__":
    app.run(debug=True, port=5080)

