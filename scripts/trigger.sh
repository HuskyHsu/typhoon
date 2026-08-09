#!/bin/bash

# ── 颱風資料收集 Mac 本機定時觸發腳本 ──
# 作用：每小時 10 分自動透過 GitHub API 秒級啟動 GitHub Actions 收集與部署

TOKEN="${GH_TOKEN:-""}"

if [ -z "$TOKEN" ]; then
  echo "⚠️  尚未設定 GitHub Token！"
  echo "請輸入您的 GitHub Personal Access Token (需有 repo 權限):"
  read -r TOKEN
fi

REPO="HuskyHsu/typhoon"
URL="https://api.github.com/repos/${REPO}/actions/workflows/collect_and_deploy.yml/dispatches"

echo "=================================================="
echo "🌀 颱風監測 Mac 定時觸發器已啟動"
echo "🎯 目標 儲存庫: ${REPO}"
echo "⏰ 觸發時間: 每小時第 10 分鐘"
echo "☕ 已啟用 caffeinate 防止 Mac 系統睡眠..."
echo "=================================================="

# 背景啟用 caffeinate 防止 Mac 系統睡眠
caffeinate -s -i &
CAFF_PID=$!

trap "kill $CAFF_PID 2>/dev/null; echo -e '\n已停止觸發器。'; exit 0" INT TERM

trigger_github() {
  NOW=$(date "+%Y-%m-%d %H:%M:%S")
  echo "🚀 [$NOW] 發送觸發請求至 GitHub Actions..."

  HTTP_CODE=$(curl -s -o /tmp/gh_trigger_resp.json -w "%{http_code}" \
    -X POST \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Accept: application/vnd.github.v3+json" \
    -H "User-Agent: Mac-Trigger-Script" \
    "${URL}" \
    -d '{"ref":"main"}')

  if [ "$HTTP_CODE" -eq 204 ]; then
    echo "  ✅ 觸發成功 (HTTP 204)！GitHub Actions 已秒級啟動！"
  else
    echo "  ❌ 觸發失敗 (HTTP $HTTP_CODE)"
    cat /tmp/gh_trigger_resp.json
    echo ""
  fi
}

while true; do
  CURRENT_MIN=$(date +%-M)
  CURRENT_SEC=$(date +%-S)

  TARGET_MIN=10
  if [ "$CURRENT_MIN" -lt "$TARGET_MIN" ]; then
    MINS_TO_WAIT=$((TARGET_MIN - CURRENT_MIN))
  else
    MINS_TO_WAIT=$((60 - CURRENT_MIN + TARGET_MIN))
  fi

  SECONDS_TO_WAIT=$((MINS_TO_WAIT * 60 - CURRENT_SEC))

  NEXT_RUN=$(date -v +${SECONDS_TO_WAIT}S "+%H:%M:%S")
  echo "⏳ 目前時間: $(date '+%H:%M:%S')，下一次觸發時間: ${NEXT_RUN} (約 ${MINS_TO_WAIT} 分鐘後)"

  sleep "$SECONDS_TO_WAIT"

  trigger_github

  sleep 60
done
