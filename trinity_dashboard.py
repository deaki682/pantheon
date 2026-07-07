"""Trinity dashboard — PWA-ready, mobile-first equity + positions view.

Reads:
  - cache/{god}_curve.json   (equity history)
  - cache/{god}_sleeve.json  (current positions + cash)

Writes:
  - cache/trinity_dashboard.html

Colors: Oracle gold (#D4AF37), Achilles purple (#9C27B0), Delphi cyan (#00BCD4), Nemesis green (#2E7D32),
        Midas crimson (#DC143C), Proteus sea-blue (#1565C0).
"""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime
from typing import Optional


GODS = (
    ("oracle", "#D4AF37"),
    ("achilles", "#9C27B0"),
    ("delphi", "#00BCD4"),
    ("midas", "#DC143C"),   # live retired 2026-07-04; shown until the wind-down sweep completes
    ("nemesis", "#2E7D32"),
    ("proteus", "#1565C0"),
    ("plutus", "#FF6F00"),  # live since 2026-07-06
    ("hermes", "#00897B"),  # live since 2026-07-05
)


def _load_json(path: str, default=None):
    if not os.path.exists(path):
        return default if default is not None else {}
    try:
        with open(path) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return default if default is not None else {}


def _load_curve(path: str) -> list[dict]:
    data = _load_json(path, [])
    if isinstance(data, dict) and "points" in data:
        return data["points"]
    if isinstance(data, list):
        return data
    return []


def _series_for(god: str, cache_dir: str) -> list[dict]:
    return _load_curve(os.path.join(cache_dir, f"{god}_curve.json"))


def _load_positions(god: str, cache_dir: str) -> list[dict]:
    """Load positions from a sleeve JSON. Returns list of {symbol, shares, avg_price, entry_date}."""
    sleeve = _load_json(os.path.join(cache_dir, f"{god}_sleeve.json"), {})
    out = []
    # Midas: single "position" field (dict or None)
    single_pos = sleeve.get("position")
    if isinstance(single_pos, dict) and single_pos.get("symbol"):
        out.append({
            "symbol": single_pos["symbol"],
            "shares": single_pos.get("shares", 0),
            "avg_price": single_pos.get("avg_price", single_pos.get("entry_price", 0)),
            "entry_date": single_pos.get("entry_date", ""),
        })
        return out
    # Oracle/Delphi/Achilles: "positions" dict keyed by symbol or event_id
    positions = sleeve.get("positions", {})
    for key, pos in positions.items():
        if isinstance(pos, dict):
            sym = pos.get("symbol", key)
            out.append({
                "symbol": sym,
                "shares": pos.get("shares", 0),
                "avg_price": pos.get("avg_price", pos.get("entry_price", 0)),
                "entry_date": pos.get("entry_date", ""),
            })
    return sorted(out, key=lambda p: p["symbol"])


def _load_sleeve_summary(god: str, cache_dir: str) -> dict:
    sleeve = _load_json(os.path.join(cache_dir, f"{god}_sleeve.json"), {})
    return {
        "cash": sleeve.get("cash", 0),
        "realized_pnl": sleeve.get("realized_pnl", 0),
        "halted": sleeve.get("halted", False),
        "trades_count": sleeve.get("trades_count", 0),
    }


def build_html(cache_dir: str = "cache") -> str:
    """Return the dashboard HTML as a string."""
    # ── Chart data ──
    datasets = []
    all_dates: set[str] = set()
    for god, color in GODS:
        pts = _series_for(god, cache_dir)
        for p in pts:
            d = p.get("date")
            if d:
                all_dates.add(d)
        datasets.append((god, color, pts))

    dates = sorted(all_dates)

    chart_datasets = []
    for god, color, pts in datasets:
        by_date = {p["date"]: p.get("equity") for p in pts if "date" in p}
        data = [by_date.get(d) for d in dates]
        chart_datasets.append({
            "label": god.capitalize(),
            "data": data,
            "borderColor": color,
            "backgroundColor": color + "40",
            "tension": 0.2,
            "spanGaps": True,
        })

    chart_payload = json.dumps({"labels": dates, "datasets": chart_datasets})

    # ── Position + sleeve data ──
    god_sections = []
    total_equity = 0.0
    for god, color in GODS:
        positions = _load_positions(god, cache_dir)
        summary = _load_sleeve_summary(god, cache_dir)
        curve = _series_for(god, cache_dir)
        latest_equity = curve[-1]["equity"] if curve else summary["cash"]
        total_equity += latest_equity

        pos_rows = ""
        for p in positions:
            pos_value = p["shares"] * p["avg_price"]
            pos_rows += f"""<tr>
              <td>{p['symbol']}</td>
              <td>{p['shares']:.4f}</td>
              <td>${p['avg_price']:.2f}</td>
              <td>${pos_value:.2f}</td>
              <td>{p['entry_date']}</td>
            </tr>"""

        halted_badge = '<span class="badge halt">HALTED</span>' if summary["halted"] else ""

        god_sections.append(f"""
        <div class="god-card" style="border-color: {color}">
          <div class="god-header">
            <span class="god-name" style="color: {color}">{god.capitalize()}</span>
            {halted_badge}
          </div>
          <div class="god-stats">
            <div class="stat"><span class="stat-label">Equity</span><span class="stat-value">${latest_equity:,.2f}</span></div>
            <div class="stat"><span class="stat-label">Cash</span><span class="stat-value">${summary['cash']:,.2f}</span></div>
            <div class="stat"><span class="stat-label">Realized</span><span class="stat-value {'neg' if summary['realized_pnl'] < 0 else 'pos'}">${summary['realized_pnl']:+,.2f}</span></div>
            <div class="stat"><span class="stat-label">Trades</span><span class="stat-value">{summary['trades_count']}</span></div>
          </div>
          {'<table class="positions"><thead><tr><th>Symbol</th><th>Shares</th><th>Avg Price</th><th>Value</th><th>Entry</th></tr></thead><tbody>' + pos_rows + '</tbody></table>' if pos_rows else '<div class="no-positions">No open positions</div>'}
        </div>""")

    positions_html = "\n".join(god_sections)
    generated = datetime.utcnow().isoformat() + "Z"

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#0e0f12">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Pantheon">
<meta http-equiv="refresh" content="900">
<title>Pantheon</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{
    font-family: -apple-system, system-ui, 'SF Pro', sans-serif;
    background: #0e0f12; color: #ddd;
    margin: 0; padding: 16px;
    padding-top: max(16px, env(safe-area-inset-top));
    padding-bottom: max(16px, env(safe-area-inset-bottom));
    -webkit-font-smoothing: antialiased;
  }}
  h1 {{ margin: 0 0 2px 0; font-size: 22px; font-weight: 600; letter-spacing: 0.03em; }}
  .header {{
    display: flex; justify-content: space-between; align-items: baseline;
    margin-bottom: 12px;
  }}
  .total {{ color: #fff; font-size: 28px; font-weight: 700; }}
  .meta {{ color: #666; font-size: 11px; }}
  .chart-wrap {{
    background: #16181d; padding: 12px; border-radius: 10px;
    height: 35vh; min-height: 200px; margin-bottom: 16px;
  }}
  canvas {{ height: 100% !important; }}
  .god-card {{
    background: #16181d; border-radius: 10px; padding: 14px;
    margin-bottom: 12px; border-left: 3px solid;
  }}
  .god-header {{ display: flex; align-items: center; gap: 8px; margin-bottom: 10px; }}
  .god-name {{ font-size: 16px; font-weight: 600; }}
  .badge {{ font-size: 10px; padding: 2px 6px; border-radius: 4px; font-weight: 600; }}
  .badge.halt {{ background: #d32f2f; color: #fff; }}
  .god-stats {{
    display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px;
    margin-bottom: 10px;
  }}
  @media (max-width: 400px) {{ .god-stats {{ grid-template-columns: repeat(2, 1fr); }} }}
  .stat {{ text-align: center; }}
  .stat-label {{ display: block; font-size: 10px; color: #888; text-transform: uppercase; letter-spacing: 0.05em; }}
  .stat-value {{ display: block; font-size: 15px; font-weight: 600; margin-top: 2px; }}
  .stat-value.pos {{ color: #4caf50; }}
  .stat-value.neg {{ color: #ef5350; }}
  .positions {{
    width: 100%; border-collapse: collapse; font-size: 12px;
  }}
  .positions th {{
    text-align: left; color: #888; font-weight: 500; font-size: 10px;
    text-transform: uppercase; letter-spacing: 0.05em;
    padding: 4px 6px; border-bottom: 1px solid #23262d;
  }}
  .positions td {{
    padding: 5px 6px; border-bottom: 1px solid #1a1d22;
    font-variant-numeric: tabular-nums;
  }}
  .no-positions {{ color: #555; font-size: 12px; font-style: italic; }}
  footer {{ color: #444; font-size: 10px; margin-top: 8px; text-align: center; }}
</style>
</head>
<body>
<div class="header">
  <div>
    <h1>Pantheon</h1>
    <div class="meta">Updated {generated}</div>
  </div>
  <div class="total">${total_equity:,.2f}</div>
</div>
<div class="chart-wrap"><canvas id="c"></canvas></div>
{positions_html}
<footer>Auto-refreshes every 15 min</footer>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<script>
const ctx = document.getElementById('c').getContext('2d');
new Chart(ctx, {{
  type: 'line',
  data: {chart_payload},
  options: {{
    responsive: true,
    maintainAspectRatio: false,
    plugins: {{
      legend: {{ labels: {{ color: '#ccc', font: {{ size: 11 }} }} }},
      tooltip: {{ mode: 'index', intersect: false }},
    }},
    scales: {{
      x: {{ ticks: {{ color: '#888', maxRotation: 45, font: {{ size: 10 }} }}, grid: {{ color: '#23262d' }} }},
      y: {{ ticks: {{ color: '#888', font: {{ size: 10 }}, callback: v => '$' + v.toLocaleString() }}, grid: {{ color: '#23262d' }} }},
    }},
  }},
}});
// PWA manifest (inline to avoid a separate file)
const m = {{name:"Pantheon",short_name:"Pantheon",display:"standalone",background_color:"#0e0f12",theme_color:"#0e0f12",start_url:"."}};
const link = document.createElement('link');
link.rel = 'manifest';
link.href = URL.createObjectURL(new Blob([JSON.stringify(m)], {{type:'application/json'}}));
document.head.appendChild(link);
</script>
</body>
</html>
"""


def write_dashboard(out_path: str, cache_dir: str = "cache") -> str:
    html = build_html(cache_dir)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    tmp = out_path + ".tmp"
    with open(tmp, "w") as f:
        f.write(html)
    os.replace(tmp, out_path)
    return out_path


def append_curve_point(cache_dir: str, god: str, equity: float, date: Optional[str] = None) -> None:
    """Append a curve point for `god`. Overwrites the day's value if one exists."""
    os.makedirs(cache_dir, exist_ok=True)
    path = os.path.join(cache_dir, f"{god}_curve.json")
    date = date or datetime.utcnow().strftime("%Y-%m-%d")
    pts = _load_curve(path)
    pts = [p for p in pts if p.get("date") != date]
    pts.append({"date": date, "equity": float(equity)})
    pts.sort(key=lambda p: p.get("date", ""))
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(pts, f, indent=2)
    os.replace(tmp, path)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Build trinity dashboard")
    parser.add_argument("--cache", default="cache", help="cache directory")
    parser.add_argument("--out", default="cache/trinity_dashboard.html", help="output HTML path")
    args = parser.parse_args(argv)
    p = write_dashboard(args.out, cache_dir=args.cache)
    print(p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
