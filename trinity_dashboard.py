"""Trinity dashboard — combine each god's *_curve.json into one HTML page.

Reads:
  - cache/oracle_curve.json
  - cache/delphi_curve.json
  - cache/achilles_curve.json

Each curve file is a list of [{"date": "YYYY-MM-DD", "equity": float}, ...].

Writes:
  - cache/trinity_dashboard.html (and optionally an --out path)

Colors: Oracle gold (#D4AF37), Achilles purple (#9C27B0), Delphi cyan (#00BCD4).
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
)


def _load_curve(path: str) -> list[dict]:
    if not os.path.exists(path):
        return []
    try:
        with open(path) as f:
            data = json.load(f)
        if isinstance(data, dict) and "points" in data:
            return data["points"]
        if isinstance(data, list):
            return data
        return []
    except (json.JSONDecodeError, OSError):
        return []


def _series_for(god: str, cache_dir: str) -> list[dict]:
    return _load_curve(os.path.join(cache_dir, f"{god}_curve.json"))


def build_html(cache_dir: str = "cache") -> str:
    """Return the dashboard HTML as a string."""
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

    payload = {"labels": dates, "datasets": chart_datasets}
    payload_json = json.dumps(payload)
    generated = datetime.utcnow().isoformat() + "Z"

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Trinity — Oracle / Achilles / Delphi</title>
<style>
  body {{ font-family: -apple-system, system-ui, sans-serif; background: #0e0f12; color: #ddd; margin: 0; padding: 24px; }}
  h1 {{ margin: 0 0 6px 0; font-weight: 500; letter-spacing: 0.04em; }}
  .meta {{ color: #888; font-size: 12px; margin-bottom: 24px; }}
  .chart-wrap {{ background: #16181d; padding: 16px; border-radius: 8px; height: 70vh; }}
  canvas {{ height: 100% !important; }}
  footer {{ color: #555; font-size: 11px; margin-top: 16px; }}
</style>
</head>
<body>
<h1>Trinity</h1>
<div class="meta">Generated {generated} — Oracle / Achilles / Delphi equity curves</div>
<div class="chart-wrap"><canvas id="c"></canvas></div>
<footer>cache/{{god}}_curve.json — three gods, one chart.</footer>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<script>
const ctx = document.getElementById('c').getContext('2d');
const cfg = {{
  type: 'line',
  data: {payload_json},
  options: {{
    responsive: true,
    maintainAspectRatio: false,
    plugins: {{
      legend: {{ labels: {{ color: '#ccc' }} }},
      tooltip: {{ mode: 'index', intersect: false }},
    }},
    scales: {{
      x: {{ ticks: {{ color: '#888' }}, grid: {{ color: '#23262d' }} }},
      y: {{ ticks: {{ color: '#888' }}, grid: {{ color: '#23262d' }} }},
    }},
  }},
}};
new Chart(ctx, cfg);
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
