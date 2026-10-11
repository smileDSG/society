#!/usr/bin/env bash
#
# 由 cron 每 5 分钟调用一次：从 GitHub 拉取最新代码并同步到部署目录。
#
# 为什么不直接用 git pull：
#   这台服务器直连 github.com 会 TCP 超时（不是配置问题，是线路不通），
#   所以改为依次尝试 deploy/mirrors.txt 里的国内镜像，谁先通用谁。
#
# 行为：
#   - 每次运行都刷新"心跳"文件（一行时间戳），看时间就知道有没有在跑
#   - 全部镜像都失败时才写日志，方便排查
#   - 成功时用 reset --hard 让部署目录与仓库严格一致
#     （本目录是纯部署目标，不放手工修改的文件，所以这样是安全的）
#
# 手动执行一次看看效果：bash /opt/xiangwang/deploy/autopull.sh
# 它会静默成功；想看到过程就加 -v：bash /opt/xiangwang/deploy/autopull.sh -v

set -u

REPO_DIR="/opt/xiangwang"
MIRROR_FILE="$REPO_DIR/deploy/mirrors.txt"
OWNER_REPO="smileDSG/society.git"
BRANCH="main"

LOG_FILE="/var/log/xiangwang-autodeploy.log"
BEAT_FILE="/var/log/xiangwang-autodeploy.lastrun"
LOG_MAX_BYTES=1048576          # 日志超过 1MB 时自动瘦身

VERBOSE=""
[ "${1:-}" = "-v" ] && VERBOSE=1

log() { [ -n "$VERBOSE" ] && echo "$@"; return 0; }

# 心跳：每次运行都覆盖写入当前时间（内容极小，不会增长）
date '+%F %T' > "$BEAT_FILE" 2>/dev/null || true

if [ ! -f "$MIRROR_FILE" ]; then
    echo "[$(date '+%F %T')] 找不到镜像列表：$MIRROR_FILE" >> "$LOG_FILE"
    exit 1
fi

if ! cd "$REPO_DIR" 2>/dev/null; then
    echo "[$(date '+%F %T')] 目录不存在：$REPO_DIR" >> "$LOG_FILE"
    exit 1
fi

# --- 依次尝试各镜像，第一个成功的就算成功 ---------------------------
winner=""
while IFS= read -r base; do
    [ -z "$base" ] && continue
    case "$base" in \#*) continue ;; esac

    url="$base/$OWNER_REPO"
    log "  尝试 $base ..."

    # timeout 防止像直连 GitHub 那样卡住两分钟
    if timeout 90 git fetch --prune "$url" "$BRANCH" >/dev/null 2>&1; then
        winner="$base"
        log "  成功：$base"
        break
    fi
    log "  失败"
done < "$MIRROR_FILE"

# --- 全部失败：记日志退出 ------------------------------------------
if [ -z "$winner" ]; then
    {
        echo "----------------------------------------"
        echo "[$(date '+%F %T')] 所有镜像都拉取失败，站点保持旧版本"
        echo "已尝试的地址："
        grep -v '^#' "$MIRROR_FILE" | grep -v '^$' | sed 's/^/  - /'
    } >> "$LOG_FILE"

    if [ "$(wc -c < "$LOG_FILE" 2>/dev/null || echo 0)" -gt "$LOG_MAX_BYTES" ]; then
        tail -n 200 "$LOG_FILE" > "$LOG_FILE.tmp" && mv "$LOG_FILE.tmp" "$LOG_FILE"
    fi
    exit 1
fi

# --- 同步到该提交 --------------------------------------------------
before="$(git rev-parse --short HEAD 2>/dev/null || echo '???????')"

if ! git reset --hard FETCH_HEAD >/dev/null 2>&1; then
    echo "[$(date '+%F %T')] 已取到代码但 reset 失败（镜像：$winner）" >> "$LOG_FILE"
    exit 1
fi

after="$(git rev-parse --short HEAD)"

if [ "$before" = "$after" ]; then
    log "  已是最新（$after），无需更新"
else
    log "  已更新：$before → $after"
fi

# 把成功使用的镜像记成 origin，方便以后手工 git pull 也能用
git remote set-url origin "$winner/$OWNER_REPO" 2>/dev/null || true

exit 0
