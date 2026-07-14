#!/bin/bash
# 03_auto_scrape.sh — 自动增量抓取入口（由 launchd 定时/开机/唤醒触发，也可手动执行）
#
# 功能：读取 accounts.txt，检测各账号最近 7 天是否有尚未发送过的新推文，
#       有则抓图、生成报告并发送邮件；无则静默结束。

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR" || exit 1

# 防止重复运行（macOS 无 flock，用目录锁）
LOCKDIR="$DIR/.scrape.lock"
if ! mkdir "$LOCKDIR" 2>/dev/null; then
    echo "$(date '+%F %T') 已有任务在运行，本次跳过。"
    exit 0
fi
trap 'rm -rf "$LOCKDIR"' EXIT

mkdir -p "$DIR/logs"
LOG="$DIR/logs/auto_scrape.log"

# 短节流：距上次运行不足 3 小时则快速跳过（不开浏览器）。
# launchd 每小时触发一次检查点（睡眠唤醒后立即补跑），
# 节流只避免清醒时频繁弹浏览器；睡眠/关机超过 3 小时后唤醒必查。
MARKER="$DIR/.last_auto_run"
INTERVAL=10800   # 3 小时（秒）
NOW=$(date +%s)
if [ -f "$MARKER" ]; then
    LAST=$(stat -f %m "$MARKER")
    if [ $((NOW - LAST)) -lt "$INTERVAL" ]; then
        LEFT=$(( (INTERVAL - (NOW - LAST)) / 60 ))
        echo "$(date '+%F %T') 距上次检查不足 3 小时（还剩约 ${LEFT} 分钟），本次跳过。" >> "$LOG"
        exit 0
    fi
fi

echo "==================== $(date '+%F %T') 开始自动检查 ====================" >> "$LOG"

# 优先使用已安装 selenium 的 conda 环境 Python
PY="/opt/anaconda3/envs/kimi.code/bin/python3"
[ -x "$PY" ] || PY="$(command -v python3)"

# 注意：按用户要求，自动流程不做翻译（--translate 仅供手动使用）
"$PY" -u "$DIR/01_x_following_scraper.py" \
    --incremental --translate --images --report >> "$LOG" 2>&1
CODE=$?

echo "==================== $(date '+%F %T') 结束 (exit=$CODE) ====================" >> "$LOG"
[ "$CODE" -eq 0 ] && touch "$MARKER"   # 成功则记录运行时间
exit $CODE
