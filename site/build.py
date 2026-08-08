#!/usr/bin/env python3
"""
build.py
========
從 data/ 目錄讀取所有收集到的資料，
產生靜態網站到 public/ 目錄（供 GitHub Pages 使用）

Design System: ui-ux-pro-max
  Style: Executive Dashboard × Clean Minimal
  Palette: White bg #F8FAFC, Navy #1E3A8A, Blue #1E40AF, Amber #D97706
  Type: Fira Code (data values) + Fira Sans (labels/body)
  Motion: Variance 2, Motion 2 — no animations, hover only

Usage:
    python3 site/build.py
"""

import json
import shutil
import datetime
from pathlib import Path

ROOT_DIR   = Path(__file__).parent.parent
DATA_DIR   = ROOT_DIR / "data"
PUBLIC_DIR = ROOT_DIR / "public"

# ─── Design Tokens ─────────────────────────────────────────────────────────────
BASE_CSS = """
<style>
  @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600&family=Fira+Sans:wght@300;400;500;600&family=Noto+Sans+TC:wght@300;400;500;600&display=swap');

  :root {
    --color-primary:    #1E40AF;
    --color-foreground: #1E3A8A;
    --color-secondary:  #3B82F6;
    --color-accent:     #D97706;
    --color-bg:         #F8FAFC;
    --color-surface:    #FFFFFF;
    --color-muted:      #EFF3F9;
    --color-border:     #DBEAFE;
    --color-text:       #111827;
    --color-text-2:     #4B5563;
    --color-text-3:     #9CA3AF;
    --color-danger:     #DC2626;
    --color-ok:         #16A34A;

    --font-mono: 'Fira Code', 'Courier New', monospace;
    --font-body: 'Fira Sans', 'Noto Sans TC', system-ui, sans-serif;

    --space-1: 4px;
    --space-2: 8px;
    --space-3: 12px;
    --space-4: 16px;
    --space-5: 24px;
    --space-6: 32px;
    --space-7: 48px;

    --radius-sm: 4px;
    --radius-md: 6px;
    --radius-lg: 8px;

    --shadow-sm: 0 1px 2px rgba(0,0,0,0.06);
    --shadow-md: 0 2px 8px rgba(0,0,0,0.08);
  }

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    font-family: var(--font-body);
    font-size: 14px;
    background: var(--color-bg);
    color: var(--color-text);
    line-height: 1.6;
    -webkit-font-smoothing: antialiased;
  }

  /* ── Header ── */
  .site-header {
    background: var(--color-surface);
    border-bottom: 1px solid var(--color-border);
    padding: var(--space-3) var(--space-5);
    display: flex;
    align-items: center;
    gap: var(--space-4);
    position: sticky;
    top: 0;
    z-index: 10;
  }

  .site-header .logo {
    font-family: var(--font-body);
    font-size: 13px;
    font-weight: 600;
    color: var(--color-primary);
    letter-spacing: 0.02em;
    text-transform: uppercase;
    white-space: nowrap;
  }

  .site-header .sep {
    color: var(--color-border);
    font-size: 16px;
    font-weight: 300;
  }

  .breadcrumb {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    font-size: 13px;
    color: var(--color-text-2);
    flex-wrap: wrap;
  }
  .breadcrumb a {
    color: var(--color-primary);
    text-decoration: none;
  }
  .breadcrumb a:hover { text-decoration: underline; }
  .breadcrumb .sep { color: var(--color-text-3); font-size: 11px; }

  /* ── Layout ── */
  .container {
    max-width: 960px;
    margin: 0 auto;
    padding: var(--space-6) var(--space-5);
  }

  /* ── Page heading ── */
  .page-title {
    font-size: 20px;
    font-weight: 600;
    color: var(--color-foreground);
    margin-bottom: var(--space-1);
    letter-spacing: -0.02em;
  }

  .page-meta {
    font-size: 12px;
    color: var(--color-text-3);
    margin-bottom: var(--space-6);
  }

  .section-label {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--color-text-3);
    margin-bottom: var(--space-3);
    padding-bottom: var(--space-2);
    border-bottom: 1px solid var(--color-border);
  }

  /* ── Cards / surface ── */
  .card {
    background: var(--color-surface);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-lg);
    padding: var(--space-5);
    margin-bottom: var(--space-4);
    box-shadow: var(--shadow-sm);
    transition: border-color 0.15s;
  }
  .card:hover { border-color: var(--color-secondary); }

  .card-link {
    text-decoration: none;
    color: inherit;
    display: block;
  }

  /* ── Status badge ── */
  .badge {
    display: inline-flex;
    align-items: center;
    gap: var(--space-1);
    padding: 2px var(--space-2);
    border-radius: var(--radius-sm);
    font-size: 11px;
    font-weight: 500;
    letter-spacing: 0.03em;
  }
  .badge-active {
    background: #DCFCE7;
    color: var(--color-ok);
    border: 1px solid #BBF7D0;
  }
  .badge-active::before {
    content: '';
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--color-ok);
    display: block;
  }

  /* ── KPI row ── */
  .kpi-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: var(--space-3);
    margin-bottom: var(--space-5);
  }
  @media (max-width: 640px) { .kpi-row { grid-template-columns: 1fr 1fr; } }

  .kpi-card {
    background: var(--color-surface);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    padding: var(--space-4);
    border-left: 3px solid var(--color-primary);
  }

  .kpi-card .kpi-value {
    font-family: var(--font-mono);
    font-size: 22px;
    font-weight: 600;
    color: var(--color-foreground);
    line-height: 1.2;
  }

  .kpi-card .kpi-unit {
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--color-text-3);
    margin-left: 2px;
  }

  .kpi-card .kpi-label {
    font-size: 11px;
    color: var(--color-text-3);
    margin-top: var(--space-1);
  }

  /* ── Timeline list ── */
  .timeline {
    display: flex;
    flex-direction: column;
    gap: 1px;
    background: var(--color-border);
    border-radius: var(--radius-lg);
    overflow: hidden;
    border: 1px solid var(--color-border);
  }

  .timeline-row {
    display: grid;
    grid-template-columns: 160px 1fr 80px;
    align-items: center;
    gap: var(--space-4);
    padding: var(--space-3) var(--space-4);
    background: var(--color-surface);
    text-decoration: none;
    color: var(--color-text);
    transition: background 0.1s;
  }
  .timeline-row:hover { background: var(--color-muted); }

  .timeline-row .ts {
    font-family: var(--font-mono);
    font-size: 12px;
    color: var(--color-primary);
    white-space: nowrap;
  }

  .timeline-row .summary {
    font-size: 12px;
    color: var(--color-text-2);
  }

  .timeline-row .chevron {
    font-size: 14px;
    color: var(--color-text-3);
    text-align: right;
    line-height: 1;
  }

  .timeline-header {
    display: grid;
    grid-template-columns: 160px 1fr 80px;
    gap: var(--space-4);
    padding: var(--space-2) var(--space-4);
    background: var(--color-muted);
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--color-text-3);
    border-bottom: 1px solid var(--color-border);
  }

  /* ── Image container ── */
  .img-wrap {
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    overflow: hidden;
    background: #f0f4f8;
    margin-bottom: var(--space-4);
  }
  .img-wrap img {
    display: block;
    max-width: 100%;
    height: auto;
    margin: 0 auto;
  }

  .img-wrap-half {
    max-width: 50%;
    margin-left: auto;
    margin-right: auto;
  }
  @media (max-width: 640px) {
    .img-wrap-half { max-width: 100%; }
  }

  .grid-2 {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: var(--space-4);
    margin-bottom: var(--space-4);
  }
  .grid-2 .img-wrap {
    margin-bottom: 0;
  }
  @media (max-width: 640px) {
    .grid-2 { grid-template-columns: 1fr; }
  }

  .img-caption {
    font-size: 11px;
    color: var(--color-text-3);
    padding: var(--space-2) var(--space-3);
    border-top: 1px solid var(--color-border);
    background: var(--color-muted);
  }

  /* ── Data table ── */
  .data-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 12px;
  }

  .data-table thead th {
    padding: var(--space-2) var(--space-3);
    text-align: left;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.07em;
    text-transform: uppercase;
    color: var(--color-text-3);
    background: var(--color-muted);
    border-bottom: 1px solid var(--color-border);
    white-space: nowrap;
  }

  .data-table tbody td {
    padding: var(--space-2) var(--space-3);
    border-bottom: 1px solid var(--color-border);
    vertical-align: middle;
    color: var(--color-text-2);
  }

  .data-table tbody tr:last-child td { border-bottom: none; }
  .data-table tbody tr:hover td { background: var(--color-muted); }

  .data-table .period-cell {
    font-size: 11px;
    font-weight: 500;
    color: var(--color-foreground);
    white-space: nowrap;
  }

  .data-table .mono {
    font-family: var(--font-mono);
    font-size: 12px;
    color: var(--color-primary);
    font-weight: 500;
  }

  .data-table .na {
    color: var(--color-text-3);
  }

  /* ── Buttons ── */
  .btn-row {
    display: flex;
    gap: var(--space-3);
    flex-wrap: wrap;
    margin-bottom: var(--space-5);
  }

  .btn {
    display: inline-flex;
    align-items: center;
    gap: var(--space-2);
    padding: var(--space-2) var(--space-4);
    border-radius: var(--radius-md);
    font-size: 12px;
    font-weight: 500;
    cursor: pointer;
    text-decoration: none;
    border: 1px solid transparent;
    transition: background 0.15s, border-color 0.15s;
    line-height: 1;
  }

  .btn svg { width: 14px; height: 14px; flex-shrink: 0; }

  .btn-primary {
    background: var(--color-primary);
    color: #fff;
    border-color: var(--color-primary);
  }
  .btn-primary:hover { background: var(--color-foreground); }

  .btn-outline {
    background: var(--color-surface);
    color: var(--color-primary);
    border-color: var(--color-border);
  }
  .btn-outline:hover { border-color: var(--color-primary); background: var(--color-muted); }

  /* ── Typhoon event card on index ── */
  .event-card {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: var(--space-4);
  }

  .event-card .event-title {
    font-size: 15px;
    font-weight: 600;
    color: var(--color-foreground);
    margin-bottom: 2px;
  }

  .event-card .event-meta {
    font-size: 12px;
    color: var(--color-text-3);
  }

  .event-card .event-count {
    font-family: var(--font-mono);
    font-size: 22px;
    font-weight: 600;
    color: var(--color-primary);
    text-align: right;
    white-space: nowrap;
  }

  .event-card .event-count-label {
    font-size: 10px;
    color: var(--color-text-3);
    text-align: right;
    text-transform: uppercase;
    letter-spacing: 0.06em;
  }

  /* ── Divider ── */
  .divider { height: 1px; background: var(--color-border); margin: var(--space-5) 0; }

  /* ── Empty state ── */
  .empty {
    text-align: center;
    padding: var(--space-7);
    color: var(--color-text-3);
    font-size: 13px;
  }

  /* ── Footer ── */
  footer {
    border-top: 1px solid var(--color-border);
    padding: var(--space-4) var(--space-5);
    text-align: center;
    font-size: 11px;
    color: var(--color-text-3);
    margin-top: var(--space-7);
  }
  footer a { color: var(--color-primary); text-decoration: none; }
  footer a:hover { text-decoration: underline; }

  .section-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: var(--space-3);
    padding-bottom: var(--space-2);
    border-bottom: 1px solid var(--color-border);
  }
  .section-header .section-label {
    margin-bottom: 0;
    padding-bottom: 0;
    border-bottom: none;
  }
  .btn-xs {
    padding: 3px 8px;
    font-size: 11px;
  }

  .section-actions {
    display: flex;
    align-items: center;
    gap: var(--space-2);
  }

  /* ── Print (Portrait Default) ── */
  @page {
    size: portrait;
    margin: 15mm;
  }

  @media print {
    .site-header, .btn-row, .section-copy-btn, .section-link-btn, footer { display: none !important; }
    body { background: white; font-size: 11px; }
    .card { box-shadow: none; border: 1px solid #ccc; break-inside: avoid; }
    .img-wrap { break-inside: avoid; }
    .timeline-row { break-inside: avoid; }
  }

  /* ── Responsive ── */
  @media (max-width: 640px) {
    .container { padding: var(--space-4); }
    .timeline-row, .timeline-header { grid-template-columns: 120px 1fr; }
    .timeline-row .chevron, .timeline-header .col-chevron { display: none; }
  }
</style>
"""

SITE_HEADER_TPL = """
<header class="site-header">
  <span class="logo">颱風監測系統</span>
  <span class="sep">|</span>
  <nav class="breadcrumb">{breadcrumb}</nav>
</header>
"""

PRINT_ICON = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 6 2 18 2 18 9"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect x="6" y="14" width="12" height="8"/></svg>'
COPY_ICON  = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>'
LINK_ICON  = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>'
BACK_ICON  = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg>'
HOME_ICON  = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>'


# ─── Helpers ───────────────────────────────────────────────────────────────────

def format_ts(hour_key: str) -> str:
    try:
        dt = datetime.datetime.strptime(hour_key, "%Y%m%d%H")
        return dt.strftime("%Y/%m/%d %H:00")
    except Exception:
        return hour_key


def val_cell(v, unit=""):
    if v in ("—", "", None):
        return '<span class="na">—</span>'
    u = f'<span style="font-size:10px;color:var(--color-text-3);margin-left:1px">{unit}</span>' if unit else ""
    return f'<span class="mono">{v}</span>{u}'


def html_page(title: str, body: str, breadcrumb: str = "") -> str:
    header = SITE_HEADER_TPL.format(breadcrumb=breadcrumb)
    return f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} — 颱風監測系統</title>
  <meta name="description" content="台灣中央氣象署颱風監測自動報告">
  {BASE_CSS}
  <script src="https://cdn.jsdelivr.net/npm/html2canvas@1.4.1/dist/html2canvas.min.js"></script>
</head>
<body>
{header}
<div class="container">
{body}
</div>
<footer>
  資料來源：<a href="https://www.cwa.gov.tw" target="_blank" rel="noopener">交通部中央氣象署</a>
  &nbsp;·&nbsp; 每小時自動更新
</footer>
<script>
async function copySectionAsPng(elementId, btn) {{
  const el = document.getElementById(elementId);
  if (!el) return;

  const origText = btn.innerHTML;
  btn.innerHTML = '⏳ 處理中...';
  btn.disabled = true;

  try {{
    const canvas = await html2canvas(el, {{
      scale: 2,
      useCORS: true,
      backgroundColor: '#F8FAFC',
      logging: false
    }});

    canvas.toBlob(async (blob) => {{
      if (!blob) {{
        btn.innerHTML = '❌ 失敗';
        setTimeout(() => {{ btn.innerHTML = origText; btn.disabled = false; }}, 2000);
        return;
      }}
      try {{
        await navigator.clipboard.write([
          new ClipboardItem({{ 'image/png': blob }})
        ]);
        btn.innerHTML = '✓ 已複製圖片！';
      }} catch (err) {{
        const a = document.createElement('a');
        a.download = elementId + '.png';
        a.href = URL.createObjectURL(blob);
        a.click();
        btn.innerHTML = '✓ 已下載 PNG';
      }}
      setTimeout(() => {{ btn.innerHTML = origText; btn.disabled = false; }}, 2000);
    }}, 'image/png');
  }} catch (e) {{
    console.error(e);
    btn.innerHTML = '❌ 錯誤';
    setTimeout(() => {{ btn.innerHTML = origText; btn.disabled = false; }}, 2000);
  }}
}}
</script>
</body>
</html>
"""


# ─── Page builders ─────────────────────────────────────────────────────────────

def build_index(typhoon_list: list, last_updated: str) -> str:
    cards = ""
    for tid in reversed(typhoon_list):
        eidx_path = DATA_DIR / tid / "event_index.json"
        count, last_ts, zh_name = 0, "", tid
        if eidx_path.exists():
            ei = json.loads(eidx_path.read_text(encoding="utf-8"))
            count   = len(ei.get("hours", []))
            last_ts = format_ts(ei.get("hours", [""])[-1]) if ei.get("hours") else ""
            zh_name = ei.get("typhoon_name_zh", tid)

        cards += f"""
<div class="card">
  <a class="card-link" href="typhoons/{tid}/index.html">
    <div class="event-card">
      <div>
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">
          <span class="event-title">{zh_name}</span>
          <span class="badge badge-active">監測中</span>
        </div>
        <div class="event-meta">
          國際命名：{tid}&nbsp;
          {f'· 最新報告：{last_ts}' if last_ts else ''}
        </div>
      </div>
      <div>
        <div class="event-count">{count}</div>
        <div class="event-count-label">小時記錄</div>
      </div>
    </div>
  </a>
</div>
"""

    body = f"""
<h1 class="page-title">颱風監測報告</h1>
<p class="page-meta">最後更新：{last_updated}</p>

<div class="section-label">颱風事件</div>
{cards if cards else '<div class="empty">目前無進行中的颱風事件</div>'}
"""
    return html_page("首頁", body, breadcrumb="<span>首頁</span>")


def build_typhoon_index(tid: str, event_index: dict) -> str:
    hours       = event_index.get("hours", [])
    last_updated = event_index.get("last_updated", "")
    zh_name     = event_index.get("typhoon_name_zh", tid)

    # latest data for KPI
    latest, f0 = {}, {}
    if hours:
        lp = DATA_DIR / tid / hours[-1] / "data.json"
        if lp.exists():
            latest = json.loads(lp.read_text(encoding="utf-8"))
            fc = latest.get("forecasts", [])
            f0 = fc[0] if fc else {}

    kpi_html = ""
    if f0:
        kpi_html = f"""
<div class="kpi-row">
  <div class="kpi-card">
    <div class="kpi-value">{f0.get('pressure_hpa','—')}<span class="kpi-unit">hPa</span></div>
    <div class="kpi-label">中心氣壓</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-value">{f0.get('max_wind_ms','—')}<span class="kpi-unit">m/s</span></div>
    <div class="kpi-label">最大風速</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-value">{f0.get('lat','—')}<span class="kpi-unit">°N</span></div>
    <div class="kpi-label">中心緯度</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-value">{f0.get('lon','—')}<span class="kpi-unit">°E</span></div>
    <div class="kpi-label">中心經度</div>
  </div>
</div>
"""

    rows = ""
    for hk in reversed(hours):
        dp = DATA_DIR / tid / hk / "data.json"
        summary = ""
        if dp.exists():
            d  = json.loads(dp.read_text(encoding="utf-8"))
            fc = d.get("forecasts", [])
            f  = fc[0] if fc else {}
            parts = []
            ds = f.get("direction_speed", "—")
            if ds != "—" and ds:
                parts.append(ds)
            p = f.get("pressure_hpa", "—")
            if p != "—" and p:
                parts.append(f"氣壓 {p} hPa")
            summary = "  ·  ".join(parts)

        rows += f"""
<a class="timeline-row" href="{hk}/index.html">
  <span class="ts">{format_ts(hk)}</span>
  <span class="summary">{summary or '—'}</span>
  <span class="chevron">›</span>
</a>
"""

    body = f"""
<h1 class="page-title">{zh_name}</h1>
<p class="page-meta">國際命名：{tid}&nbsp;·&nbsp;共 {len(hours)} 筆&nbsp;·&nbsp;最後更新：{last_updated}</p>

{kpi_html}

<div class="section-label">每小時報告</div>
<div class="timeline">
  <div class="timeline-header">
    <span>時間</span>
    <span>移向 / 氣壓</span>
    <span class="col-chevron"></span>
  </div>
{rows if rows else '<div class="empty">尚無資料</div>'}
</div>
"""
    bc = f'<a href="../../index.html">{HOME_ICON}&nbsp;首頁</a><span class="sep">›</span><span>颱風 {tid}</span>'
    return html_page(f"颱風 {tid}", body, breadcrumb=bc)
def build_hour_report(tid: str, hour_key: str, data: dict) -> str:
    forecasts     = data.get("forecasts", [])
    collected     = data.get("collected_at", "")
    zh_name       = data.get("typhoon_name_zh", tid)
    report_no     = data.get("report_no", "")
    issued_at     = data.get("issued_at", "")
    news_img_name = data.get("news_img_name", "")
    present_items = data.get("present_items", [])
    forecast_text = data.get("forecast_text", "")

    img_dir   = DATA_DIR / tid / hour_key
    has_72h   = (img_dir / "track_72h.png").exists()
    has_120h  = (img_dir / "track_120h.png").exists()
    has_news  = (img_dir / "news_track.png").exists()
    has_sheet = (img_dir / "warning_sheet.png").exists()

    imgs_html = ""
    if has_72h:
        imgs_html += f"""
<div class="img-wrap">
  <img src="track_72h.png" alt="颱風路徑潛勢預報 72小時">
  <div class="img-caption">警報路徑潛勢預報圖（72 小時）· 資料時間：{issued_at}</div>
</div>"""
    if has_120h:
        imgs_html += f"""
<div class="img-wrap" style="margin-top:var(--space-3)">
  <img src="track_120h.png" alt="颱風路徑潛勢預報 120小時">
  <div class="img-caption">警報路徑潛勢預報圖（120 小時）</div>
</div>"""

    # 颱風消息圖片
    if has_news:
        fn_text = f"（檔名：{news_img_name}）" if news_img_name else ""
        news_html = f"""
<div class="img-wrap">
  <img src="news_track.png" alt="颱風消息 路徑潛勢預報">
  <div class="img-caption">颱風消息 ➔ 路徑潛勢預報圖 {fn_text}</div>
</div>"""
    else:
        news_html = '<div class="empty">尚無颱風消息圖檔</div>'

    # 定量降水預報 12小時預報圖 (5張)
    has_qpf = (img_dir / "qpf_qzj.jpg").exists() or (img_dir / "qpf_12_12.png").exists()
    if has_qpf:
        qpf_qzj_html = ""
        if (img_dir / "qpf_qzj.jpg").exists():
            qpf_qzj_html = """
<div class="img-wrap img-wrap-half">
  <img src="qpf_qzj.jpg" alt="最新雨量累積圖">
  <div class="img-caption">最新雨量累積圖</div>
</div>"""

        grid_imgs = []
        for fn, title in [
            ("qpf_12_12.png", "定量降水預報（Ⅰ）"),
            ("qpf_12_24.png", "定量降水預報（Ⅱ）"),
            ("qpf_12_36.png", "定量降水預報（Ⅲ）"),
            ("qpf_12_48.png", "定量降水預報（Ⅳ）"),
        ]:
            if (img_dir / fn).exists():
                grid_imgs.append(f"""
<div class="img-wrap">
  <img src="{fn}" alt="{title}">
  <div class="img-caption">{title}</div>
</div>""")

        grid_html = f'<div class="grid-2">{"".join(grid_imgs)}</div>' if grid_imgs else ""
        qpf_html = f"{qpf_qzj_html}{grid_html}"
    else:
        qpf_html = '<div class="empty">尚無定量降水預報圖檔</div>'

    # 海上颱風警報 現況與預測 HTML
    has_b20 = (img_dir / "typhoon_map.png").exists()
    b20_html = """
<div class="img-wrap" style="margin-bottom:0">
  <img src="typhoon_map.png" alt="颱風動態圖">
  <div class="img-caption">颱風動態圖（B20.png）</div>
</div>""" if has_b20 else '<div class="empty">無颱風動態圖</div>'

    now_items_li = "".join([f'<li style="margin-bottom:6px;font-size:13px;color:var(--color-text-2)">{it}</li>' for it in present_items])
    now_list_html = f'<ul style="padding-left:16px;margin-bottom:12px">{now_items_li}</ul>' if present_items else '<div class="empty">無現況文字</div>'
    pred_html = f'<h4 style="font-size:13px;font-weight:600;color:var(--color-primary);margin-top:12px;margin-bottom:4px">颱風預測</h4><p style="font-size:13px;color:var(--color-text-2)">{forecast_text}</p>' if forecast_text else ''

    status_card_html = f"""
<div class="card" style="margin-bottom:0;height:100%">
  <h4 style="font-size:13px;font-weight:600;color:var(--color-primary);margin-bottom:8px">颱風現況</h4>
  {now_list_html}
  {pred_html}
</div>"""

    sea_warn_html = f"""
<div class="grid-2" style="align-items:start">
  {b20_html}
  {status_card_html}
</div>"""

    # 警報單 HTML
    if has_sheet:
        sheet_html = """
<div class="img-wrap">
  <img src="warning_sheet.png" alt="颱風警報單">
  <div class="img-caption">颱風警報單（I10.png）</div>
</div>"""
    else:
        sheet_html = '<div class="empty">無警報單圖檔</div>'

    # table
    table_rows = ""
    for fc in forecasts:
        period = fc.get("period", "")
        if not any('\u4e00' <= char <= '\u9fff' for char in period):
            continue
            
        ftime  = fc.get("forecast_time", "—")
        dirsp  = fc.get("direction_speed", "—")
        lat    = fc.get("lat", "—")
        lon    = fc.get("lon", "—")
        pres   = fc.get("pressure_hpa", "—")
        wind   = fc.get("max_wind_ms", "—")
        gust   = fc.get("gust_ms", "—")
        r7     = fc.get("radius_7", "—")
        r10    = fc.get("radius_10", "—")
        prob_r = fc.get("prob_radius", "—")

        table_rows += f"""<tr>
  <td class="period-cell">{period}</td>
  <td>{val_cell(ftime)}</td>
  <td style="font-size:12px;color:var(--color-text-2)">{dirsp if dirsp != '—' else '<span class="na">—</span>'}</td>
  <td>{val_cell(lat, '°N')}</td>
  <td>{val_cell(lon, '°E')}</td>
  <td>{val_cell(pres, ' hPa')}</td>
  <td>{val_cell(wind, ' m/s')}</td>
  <td>{val_cell(gust, ' m/s')}</td>
  <td>{val_cell(r7, ' km')}</td>
  <td>{val_cell(r10, ' km')}</td>
  <td>{val_cell(prob_r, ' km')}</td>
</tr>"""

    report_label = f"第 {report_no} 報" if report_no else ""
    formatted_ts = format_ts(hour_key)

    body = f"""
<div id="report-content">
  <h1 class="page-title">{zh_name}</h1>
  <p class="page-meta">
    {formatted_ts}&nbsp;·&nbsp;{report_label}&nbsp;·&nbsp;收集時間：{collected}
  </p>

  <div class="btn-row">
    <button class="btn btn-primary" onclick="window.print()">{PRINT_ICON}&nbsp;列印 / 存成 PDF (直式)</button>
    <button class="btn btn-outline" onclick="copySectionAsPng('report-content', this)">{COPY_ICON}&nbsp;複製整份報告圖片</button>
    <a class="btn btn-outline" href="../index.html">{BACK_ICON}&nbsp;回到時間軸</a>
    <a class="btn btn-outline" href="../../index.html">{HOME_ICON}&nbsp;首頁</a>
  </div>

  <div class="section-header">
    <div class="section-label">海上颱風警報 ➔ 颱風現況與預測</div>
    <div class="section-actions">
      <a href="https://www.cwa.gov.tw/V8/C/P/Typhoon/TY_WARN.html" target="_blank" rel="noopener" class="btn btn-xs btn-outline section-link-btn">{LINK_ICON}&nbsp;氣象署原網頁</a>
      <button class="btn btn-xs btn-outline section-copy-btn" onclick="copySectionAsPng('sec-sea-warn', this)">{COPY_ICON}&nbsp;複製區塊圖片</button>
    </div>
  </div>
  <div id="sec-sea-warn">
    {sea_warn_html}
  </div>

  <div class="divider"></div>

  <div class="section-header">
    <div class="section-label">警報颱風（{zh_name}）路徑潛勢預報</div>
    <div class="section-actions">
      <a href="https://www.cwa.gov.tw/V8/C/P/Typhoon/PTA.html" target="_blank" rel="noopener" class="btn btn-xs btn-outline section-link-btn">{LINK_ICON}&nbsp;氣象署原網頁</a>
      <button class="btn btn-xs btn-outline section-copy-btn" onclick="copySectionAsPng('sec-warn', this)">{COPY_ICON}&nbsp;複製區塊圖片</button>
    </div>
  </div>
  <div id="sec-warn">
    {imgs_html if imgs_html else '<div class="empty">圖片不可用</div>'}

    <div class="card" style="padding:0;overflow:auto;margin-top:var(--space-4)">
      <table class="data-table">
        <thead>
          <tr>
            <th>預報時段</th>
            <th>預測時間</th>
            <th>移向移速</th>
            <th>北緯</th>
            <th>東經</th>
            <th>氣壓</th>
            <th>最大風速</th>
            <th>最大陣風</th>
            <th>七級半徑</th>
            <th>十級半徑</th>
            <th>70%機率半徑</th>
          </tr>
        </thead>
        <tbody>
          {table_rows if table_rows else '<tr><td colspan="11" class="empty">無數值資料</td></tr>'}
        </tbody>
      </table>
    </div>
  </div>

  <div class="divider"></div>

  <div class="section-header">
    <div class="section-label">颱風消息 ➔ 路徑潛勢預報</div>
    <div class="section-actions">
      <a href="https://www.cwa.gov.tw/V8/C/P/Typhoon/TY_NEWS.html" target="_blank" rel="noopener" class="btn btn-xs btn-outline section-link-btn">{LINK_ICON}&nbsp;氣象署原網頁</a>
      <button class="btn btn-xs btn-outline section-copy-btn" onclick="copySectionAsPng('sec-news', this)">{COPY_ICON}&nbsp;複製區塊圖片</button>
    </div>
  </div>
  <div id="sec-news">
    {news_html}
  </div>

  <div class="divider"></div>

  <div class="section-header">
    <div class="section-label">定量降水預報 ➔ 12小時預報圖</div>
    <div class="section-actions">
      <a href="https://www.cwa.gov.tw/V8/C/P/QPF.html" target="_blank" rel="noopener" class="btn btn-xs btn-outline section-link-btn">{LINK_ICON}&nbsp;氣象署原網頁</a>
      <button class="btn btn-xs btn-outline section-copy-btn" onclick="copySectionAsPng('sec-qpf', this)">{COPY_ICON}&nbsp;複製區塊圖片</button>
    </div>
  </div>
  <div id="sec-qpf">
    {qpf_html}
  </div>

  <div class="divider"></div>

  <div class="section-header">
    <div class="section-label">警報單</div>
    <div class="section-actions">
      <a href="https://www.cwa.gov.tw/V8/C/P/Typhoon/TY_WARN.html" target="_blank" rel="noopener" class="btn btn-xs btn-outline section-link-btn">{LINK_ICON}&nbsp;氣象署原網頁</a>
      <button class="btn btn-xs btn-outline section-copy-btn" onclick="copySectionAsPng('sec-sheet', this)">{COPY_ICON}&nbsp;複製區塊圖片</button>
    </div>
  </div>
  <div id="sec-sheet">
    {sheet_html}
  </div>
</div>
"""
    bc = (
        f'<a href="../../index.html">{HOME_ICON}&nbsp;首頁</a>'
        f'<span class="sep">›</span>'
        f'<a href="../index.html">颱風 {tid}</a>'
        f'<span class="sep">›</span>'
        f'<span>{formatted_ts}</span>'
    )
    return html_page(f"{zh_name} {formatted_ts}", body, breadcrumb=bc)


# ─── Main build ────────────────────────────────────────────────────────────────

def build():
    print("開始建置靜態網站...")

    if PUBLIC_DIR.exists():
        shutil.rmtree(PUBLIC_DIR)
    PUBLIC_DIR.mkdir(parents=True)

    gi_path = DATA_DIR / "typhoon_list.json"
    if not gi_path.exists():
        typhoon_list = []
        last_updated = "—"
    else:
        gi = json.loads(gi_path.read_text(encoding="utf-8"))
        typhoon_list = gi.get("typhoons", [])
        last_updated = gi.get("last_updated", "—")

    (PUBLIC_DIR / "index.html").write_text(
        build_index(typhoon_list, last_updated), encoding="utf-8"
    )
    print(f"  ✓ index.html（{len(typhoon_list)} 個颱風）")

    for tid in typhoon_list:
        eidx_path = DATA_DIR / tid / "event_index.json"
        if not eidx_path.exists():
            continue

        event_index = json.loads(eidx_path.read_text(encoding="utf-8"))
        hours = event_index.get("hours", [])

        ty_dir = PUBLIC_DIR / "typhoons" / tid
        ty_dir.mkdir(parents=True, exist_ok=True)

        (ty_dir / "index.html").write_text(
            build_typhoon_index(tid, event_index), encoding="utf-8"
        )
        print(f"  ✓ 颱風 {tid}（{len(hours)} 筆）")

        for hk in hours:
            dp = DATA_DIR / tid / hk / "data.json"
            if not dp.exists():
                continue
            data     = json.loads(dp.read_text(encoding="utf-8"))
            hour_dir = ty_dir / hk
            hour_dir.mkdir(exist_ok=True)

            qpf_imgs = ["qpf_qzj.jpg", "qpf_12_12.png", "qpf_12_24.png", "qpf_12_36.png", "qpf_12_48.png"]
            all_imgs = ["track_72h.png", "track_120h.png", "typhoon_map.png", "news_track.png", "warning_sheet.png"] + qpf_imgs
            for fname in all_imgs:
                src = DATA_DIR / tid / hk / fname
                dst = hour_dir / fname
                if src.exists() and not dst.exists():
                    shutil.copy2(src, dst)

            (hour_dir / "index.html").write_text(
                build_hour_report(tid, hk, data), encoding="utf-8"
            )

        print(f"  ✓ 完成 {len(hours)} 份報告")

    print(f"建置完成 → {PUBLIC_DIR}")


if __name__ == "__main__":
    build()
