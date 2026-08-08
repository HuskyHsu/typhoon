#!/usr/bin/env python3
"""
collect.py
==========
收集中央氣象署颱風路徑潛勢預報資料
資料來源：TY_WARN-Data.js（包含颱風 ID、時間戳、完整 accordion HTML）

Usage:
    python3 scripts/collect.py
"""

import re
import json
import warnings
import requests
import datetime
from pathlib import Path
from bs4 import BeautifulSoup

# 氣象署憑證有已知問題（Missing Subject Key Identifier），暫時停用 SSL 驗證
warnings.filterwarnings("ignore", message="Unverified HTTPS request")

# ─── 設定 ──────────────────────────────────────────────────────────────────────
CWA_BASE   = "https://www.cwa.gov.tw"
DATA_JS_URL = f"{CWA_BASE}/Data/js/typhoon/TY_WARN-Data.js"
DATA_DIR    = Path(__file__).parent.parent / "data"

# 一般請求用 header（取 JS 檔）
HEADERS_BASE = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.cwa.gov.tw/",
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
}

# 下載 PTA 圖片需要帶上 PTA 頁面的 Referer
HEADERS_IMG = {
    **HEADERS_BASE,
    "Referer": f"{CWA_BASE}/V8/C/P/Typhoon/PTA.html",
    "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
}


# ─── 工具函數 ──────────────────────────────────────────────────────────────────

def fetch_text(url: str, headers: dict = None) -> str:
    h = headers or HEADERS_BASE
    resp = requests.get(url, headers=h, timeout=30, verify=False)
    resp.raise_for_status()
    return resp.content.decode("utf-8", errors="replace")


def fetch_bytes(url: str, headers: dict = None) -> bytes:
    h = headers or HEADERS_BASE
    resp = requests.get(url, headers=h, timeout=30, verify=False)
    resp.raise_for_status()
    return resp.content


# ─── 從 TY_WARN-Data.js 解析颱風資訊 ──────────────────────────────────────────

def parse_data_js(js_text: str) -> dict:
    """
    從 TY_WARN-Data.js 解析：
    - File_Time / PTA_InitTime（時間戳，格式 YYYYMMDDHHII）
    - PTA_TYPHOON（颱風英文名，例如 DOLPHIN）
    - accordion HTML 片段（路徑潛勢預報文字數值）
    - 颱風中文名、警報等級

    回傳 dict，包含 typhoon_id、timestamp、accordion_html、meta 等欄位
    """
    result = {}

    # 時間戳
    m = re.search(r"PTA_InitTime\s*=\s*'(\d+)'", js_text)
    if not m:
        m = re.search(r"File_Time\s*=\s*'(\d+)'", js_text)
    result["timestamp"] = m.group(1) if m else None

    # 颱風英文名
    m2 = re.search(r"PTA_TYPHOON\s*=\s*'([A-Z]+)'", js_text)
    result["typhoon_id"] = m2.group(1) if m2 else None

    # 颱風中文名 + 等級（例如「中度颱風 白海豚」）
    m3 = re.search(r"<h3>([^<]*颱風[^<]*)</h3>", js_text)
    if m3:
        result["typhoon_name_zh"] = m3.group(1).strip()

    # 發布時間
    m4 = re.search(r"發布時間：(\d+/\d+\s+\d+:\d+)", js_text)
    if m4:
        result["issued_at"] = m4.group(1)

    # 警報報號
    m5 = re.search(r"第(\d+)報", js_text)
    if m5:
        result["report_no"] = m5.group(1)

    # accordion-1 HTML（路徑潛勢預報各時段）
    # 這個 accordion 以 JavaScript 字串形式嵌在 JS 檔案內
    # 例如: var TY13_PTA_Data_C = '...' + '...' ;
    # 我們找含有 accordion-1 的那段字串，把所有 JS string concat 拼起來
    acc_start = js_text.find("accordion-1")
    if acc_start >= 0:
        # 往前找 var 宣告的開始
        var_start = js_text.rfind("\nvar ", 0, acc_start)
        if var_start < 0:
            var_start = 0
        # 往後找 ; 結尾（簡單取後面 8000 字元做解析就夠）
        segment = js_text[var_start:acc_start + 8000]

        # 把所有 JS 字串拼接（移除 '+' 和換行，提取引號內容）
        # 策略：直接把 segment 裡的 HTML 標籤拼起來
        # 移除 JS 語法後剩下 HTML
        html_parts = re.findall(r"'([^']*)'", segment)
        accordion_html = "".join(html_parts)
        result["accordion_html"] = accordion_html
    else:
        result["accordion_html"] = ""

    return result


# ─── 解析 accordion 的文字數值 ─────────────────────────────────────────────────

def parse_forecasts(accordion_html: str) -> list:
    """
    解析 accordion HTML 中的各時段預報數值
    回傳 list of dict
    """
    if not accordion_html:
        return []

    soup = BeautifulSoup(accordion_html, "html.parser")
    results = []

    # 找所有 panel
    panels = soup.find_all("div", class_="panel")

    for panel in panels:
        # 取 heading 文字
        heading = panel.find("a", class_="accordion-toggle")
        body    = panel.find("div", class_=lambda c: c and "collapse" in c.split())

        if not heading:
            continue

        title_text = heading.get_text(strip=True)
        raw_text   = body.get_text(separator="\n", strip=True) if body else ""

        # 解析時段
        period_m = re.search(r"預測\s+([\d\-]+)\s+小時", title_text)
        period   = period_m.group(1) + " 小時" if period_m else title_text

        def extract(pattern, text, default="—"):
            m = re.search(pattern, text)
            return m.group(1).strip() if m else default

        entry = {
            "period":           period,
            "direction_speed":  extract(r"([^\n]*時速\s*[\d\.]+\s*公里)", raw_text),
            "forecast_time":    extract(r"預測\s+(\d+月\d+日\d+時)", raw_text),
            "lat":              extract(r"北緯\s*([\d\.]+)\s*度", raw_text),
            "lon":              extract(r"東經\s*([\d\.]+)\s*度", raw_text),
            "pressure_hpa":     extract(r"中心氣壓(\d+)百帕", raw_text),
            "max_wind_ms":      extract(r"最大風速每秒\s*([\d\.]+)\s*公尺", raw_text),
            "gust_ms":          extract(r"陣風每秒\s*([\d\.]+)\s*公尺", raw_text),
            "radius_7":         extract(r"七級風暴風半徑\s*([\d]+)\s*公里", raw_text),
            "radius_10":        extract(r"十級風暴風半徑\s*([\d]+)\s*公里", raw_text),
            "prob_radius":      extract(r"70%機率半徑\s*([\d]+)\s*公里", raw_text),
            "raw_text":         raw_text,
        }
        # 過濾掉沒有「小時」標記的格子（例如英文 'valid at' 欄位）
        if not period_m:
            continue
        results.append(entry)

    # 如果 BeautifulSoup 解析失敗（JS 字串拼接的 HTML 結構可能不完整），
    # 改用 regex 直接從原始文字抽取
    if not results:
        results = _fallback_parse(accordion_html)

    return results


def _fallback_parse(text: str) -> list:
    """備援：用 regex 直接從 accordion HTML 字串抓各時段文字"""
    results = []
    # 找所有 collapse-A* 區塊
    blocks = re.findall(
        r'id=\\"collapse-A(\d+)\\"[^>]*>(.*?)(?=id=\\"collapse-A|\Z)',
        text, re.DOTALL
    )
    for block_id, block_text in blocks:
        # 清除 HTML 標籤
        clean = re.sub(r"<[^>]+>", " ", block_text)
        clean = re.sub(r"\s+", " ", clean).strip()

        def extract(pattern, default="—"):
            m = re.search(pattern, clean)
            return m.group(1).strip() if m else default

        entry = {
            "period":        f"{block_id}h 時段",
            "raw_text":      clean,
            "lat":           extract(r"北緯\s*([\d\.]+)\s*度"),
            "lon":           extract(r"東經\s*([\d\.]+)\s*度"),
            "pressure_hpa":  extract(r"中心氣壓(\d+)百帕"),
            "max_wind_ms":   extract(r"最大風速每秒\s*([\d\.]+)\s*公尺"),
            "gust_ms":       extract(r"陣風每秒\s*([\d\.]+)\s*公尺"),
        }
        results.append(entry)
    return results


# ─── 主流程 ────────────────────────────────────────────────────────────────────

def collect():
    now      = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
    run_time = now.strftime("%Y-%m-%d %H:%M CST")
    print(f"[{run_time}] 開始收集颱風資料...")

    # 1. 下載 TY_WARN-Data.js
    print(f"  → 下載 {DATA_JS_URL}")
    try:
        js_text = fetch_text(DATA_JS_URL)
    except Exception as e:
        print(f"  ✗ 無法取得 Data.js：{e}")
        return None

    # 2. 解析颱風基本資訊
    info = parse_data_js(js_text)
    typhoon_id = info.get("typhoon_id")
    timestamp  = info.get("timestamp")

    if not typhoon_id or not timestamp:
        print("  ✗ 找不到颱風資料（目前可能無颱風警報）")
        no_dir = DATA_DIR / "no_typhoon" / now.strftime("%Y%m%d%H")
        no_dir.mkdir(parents=True, exist_ok=True)
        (no_dir / "data.json").write_text(
            json.dumps({"status": "no_typhoon", "collected_at": run_time},
                       ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        return None

    print(f"  ✓ 颱風：{info.get('typhoon_name_zh', typhoon_id)} ({typhoon_id})")
    print(f"  ✓ 時間戳：{timestamp}，發布：{info.get('issued_at', '—')}，第 {info.get('report_no', '—')} 報")

    # 3. 儲存路徑
    hour_key = now.strftime("%Y%m%d%H")
    save_dir = DATA_DIR / typhoon_id / hour_key
    save_dir.mkdir(parents=True, exist_ok=True)

    # 4. 下載 PTA 路徑預報圖
    # URL 格式：PTA_{時間戳}-{預報時數}_{颱風英文名}_zhtw.png
    # 預報時數：72 = 72小時路徑預報圖（含未來路徑），120 = 120小時
    # -0 只是現況圖，不包含預報路徑，不是我們要的

    # B20.png：颱風動態圖（TY_WARN 頁面的主要地圖）
    img_url_b20 = f"{CWA_BASE}/Data/typhoon/TY_WARN/B20.png?T={timestamp}"

    # 嘗試下載 72h 和 120h 預報圖（後綴是預報時數，不是序號）
    img_url_72h  = f"{CWA_BASE}/Data/typhoon/TY_WARN/PTA_{timestamp}-72_{typhoon_id}_zhtw.png"
    img_url_120h = f"{CWA_BASE}/Data/typhoon/TY_WARN/PTA_{timestamp}-120_{typhoon_id}_zhtw.png"

    for label, url, filename in [
        ("PTA 72h 路徑預報圖",  img_url_72h,  "track_72h.png"),
        ("PTA 120h 路徑預報圖", img_url_120h, "track_120h.png"),
        ("B20 動態圖",          img_url_b20,  "typhoon_map.png"),
    ]:
        path = save_dir / filename
        if path.exists():
            print(f"  ↩ {filename} 已存在，跳過")
            continue
        try:
            data = fetch_bytes(url, headers=HEADERS_IMG)
            path.write_bytes(data)
            print(f"  ✓ 已下載 {filename}（{len(data)//1024} KB）")
        except Exception as e:
            # 120h 圖不一定存在，404 是正常的
            print(f"  - {filename} 無法取得（可能氣象署未發布此時數）")

    # 5. 解析 accordion 文字數值
    forecasts = parse_forecasts(info.get("accordion_html", ""))
    print(f"  ✓ 解析到 {len(forecasts)} 個預報時段")

    # 6. 儲存 JSON
    meta = {
        "collected_at":      run_time,
        "typhoon_id":        typhoon_id,
        "typhoon_name_zh":   info.get("typhoon_name_zh", ""),
        "cwa_timestamp":     timestamp,
        "issued_at":         info.get("issued_at", ""),
        "report_no":         info.get("report_no", ""),
        "img_url_72h":       img_url_72h,
        "img_url_120h":      img_url_120h,
        "img_url_b20":       img_url_b20,
        "forecasts":         forecasts,
    }
    (save_dir / "data.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"  ✓ 已儲存 data.json")

    # 7. 更新颱風事件 index
    event_index_path = DATA_DIR / typhoon_id / "event_index.json"
    if event_index_path.exists():
        event_index = json.loads(event_index_path.read_text(encoding="utf-8"))
    else:
        event_index = {"typhoon_id": typhoon_id, "typhoon_name_zh": info.get("typhoon_name_zh", ""), "hours": []}

    if hour_key not in event_index["hours"]:
        event_index["hours"].append(hour_key)
        event_index["hours"].sort()
    event_index["last_updated"] = run_time
    event_index_path.write_text(
        json.dumps(event_index, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"  ✓ 更新 event_index.json（共 {len(event_index['hours'])} 筆）")

    # 8. 更新全域颱風清單
    global_index_path = DATA_DIR / "typhoon_list.json"
    if global_index_path.exists():
        global_index = json.loads(global_index_path.read_text(encoding="utf-8"))
    else:
        global_index = {"typhoons": []}
    if typhoon_id not in global_index["typhoons"]:
        global_index["typhoons"].append(typhoon_id)
    global_index["last_updated"] = run_time
    global_index_path.write_text(
        json.dumps(global_index, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"[{run_time}] ✅ 收集完成！→ {save_dir}")
    return save_dir


if __name__ == "__main__":
    result = collect()
    if result is None:
        exit(1)
