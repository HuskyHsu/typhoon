# 颱風監測自動報告系統

每小時自動從[交通部中央氣象署](https://www.cwa.gov.tw)收集颱風資料，並部署成 GitHub Pages 報告網站。

## 功能

- 🌀 **自動偵測**：自動偵測目前颱風 ID 與最新時間戳
- 📸 **下載圖片**：路徑潛勢預報圖（120h / 72h）
- 📊 **爬取數值**：位置、氣壓、風速、暴風半徑等
- 🌐 **自動部署**：每小時更新 GitHub Pages 報告網站
- 📄 **可下載**：每份報告可從瀏覽器列印成 PDF

## 網站結構

```
https://{你的帳號}.github.io/{repo名稱}/
├── 首頁          ← 颱風事件清單
├── /typhoons/{颱風ID}/   ← 時間軸（每小時一筆）
└── /typhoons/{颱風ID}/{年月日時}/  ← 單小時詳細報告
```

## 本機測試

```bash
# 安裝相依套件
pip install -r requirements.txt

# 收集一次資料
python3 scripts/collect.py

# 建置靜態網站
python3 site/build.py

# 預覽網站（需要 Python）
cd public && python3 -m http.server 8080
# 然後開啟 http://localhost:8080
```

## 部署到 GitHub Pages

1. 在 GitHub 建立 public repo
2. 推送此專案
3. 進入 Settings → Pages → Source: **GitHub Actions**
4. 等第一次 workflow 執行完成

## 目錄結構

```
typhoon-monitor/
├── .github/workflows/
│   └── collect_and_deploy.yml   ← 每小時自動執行
├── scripts/
│   └── collect.py               ← 資料收集腳本
├── site/
│   └── build.py                 ← 靜態網站產生器
├── data/                        ← 收集到的原始資料（自動 commit）
│   ├── typhoon_list.json
│   └── {颱風ID}/
│       ├── event_index.json
│       └── {年月日時}/
│           ├── data.json
│           ├── track_120h.png
│           └── track_72h.png
├── public/                      ← 產生的靜態網站（部署到 Pages）
└── requirements.txt
```
