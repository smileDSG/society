#!/usr/bin/env bash
#
# 组装对外发布目录 —— 容器真正挂载的那个目录。
#
# 布局：
#   /var/www/xw-pub/            陌生人看到的（伪装站，来自仓库 mask/）
#   /var/www/xw-pub/<密钥>/     真实站（来自仓库 v3/）
#
# 密钥存在 /etc/xiangwang/mask-secret，只在这台服务器上，不进任何仓库、不进任何日志。
#
# 每次 autopull.sh 同步完代码后会自动调用一次；也可以手工跑：
#   bash /opt/xiangwang/deploy/publish.sh
#
# ⚠️ 关键约束：必须是「原地增量同步」。
#    /var/www/xw-pub 是容器的 bind mount，把整个目录 rm 掉再建一个新的，
#    等于换了个 inode，容器会继续指向旧目录，网站直接变成 404。
#    所以这里用 rsync（没有 rsync 时退化成"清空内容再拷"）。

set -u

# 路径可以被子进程用环境变量覆盖 —— 只是为了让这个脚本能脱离服务器在本地跑一遍验证。
# 服务器上永远用默认值（setup-mask.sh / autopull.sh 都不会传这些变量）。
REPO_DIR="${XW_REPO_DIR:-/opt/xiangwang}"
PUB_DIR="${XW_PUB_DIR:-/var/www/xw-pub}"
SECRET_FILE="${XW_SECRET_FILE:-/etc/xiangwang/mask-secret}"
LOG_FILE="${XW_MASK_LOG:-/var/log/xiangwang-mask.log}"

log() {
    echo "[$(date '+%F %T')] $*" >> "$LOG_FILE" 2>/dev/null || true
    # 超过 256KB 只留最后 200 行
    if [ "$(wc -c < "$LOG_FILE" 2>/dev/null || echo 0)" -gt 262144 ]; then
        tail -n 200 "$LOG_FILE" > "$LOG_FILE.tmp" && mv "$LOG_FILE.tmp" "$LOG_FILE"
    fi
}

fail() { log "失败：$*"; exit 1; }

# ---- 1. 取密钥 -------------------------------------------------
[ -r "$SECRET_FILE" ] || fail "读不到 $SECRET_FILE —— 先在服务器上跑 deploy/setup-mask.sh"

SECRET="$(tr -d ' \t\r\n' < "$SECRET_FILE")"
[ -n "$SECRET" ] || fail "$SECRET_FILE 是空的"

# 只允许安全字符，防止密钥被当成路径或通配符（本文件会被 root 执行）
case "$SECRET" in
    */*|*..*|.*)              fail "密钥含非法字符或形状（不得含 / 、不得以点开头）" ;;
    *[!A-Za-z0-9_-]*)         fail "密钥含非法字符（只允许字母、数字、- _）" ;;
esac
[ "${#SECRET}" -ge 6 ] || fail "密钥太短（至少 6 位，默认 8 位）"

# ---- 2. 检查源码 ----------------------------------------------
[ -d "$REPO_DIR/mask" ] || fail "找不到 $REPO_DIR/mask（伪装站）—— 服务器上代码太旧，先 git pull"
[ -d "$REPO_DIR/v3" ]   || fail "找不到 $REPO_DIR/v3（真实站）"
[ -f "$REPO_DIR/mask/index.html" ] || fail "$REPO_DIR/mask/index.html 不存在"

mkdir -p "$PUB_DIR" || fail "建不了 $PUB_DIR"

# ---- 3. 同步 ---------------------------------------------------
# 注意 exclude 用 "/$SECRET/" 精确锚定根目录下那一个，别误伤别处同名目录
if command -v rsync >/dev/null 2>&1; then
    rsync -a --delete --exclude="/$SECRET/" "$REPO_DIR/mask/" "$PUB_DIR/" \
        || fail "同步伪装站失败（rsync）"

    mkdir -p "$PUB_DIR/$SECRET" || fail "建不了 $PUB_DIR/$SECRET"
    # 真实站源码里混着开发用的脚本和内部清单，不该对外提供
    rsync -a --delete --exclude='_*' --exclude='*.py' --exclude='__pycache__' \
        "$REPO_DIR/v3/" "$PUB_DIR/$SECRET/" \
        || fail "同步真实站失败（rsync）"
else
    # 退化路径：清空内容再拷。目录本身保留，inode 不变，bind mount 不会断。
    find "$PUB_DIR" -mindepth 1 -maxdepth 1 -exec rm -rf {} + || fail "清空 $PUB_DIR 失败"
    cp -a "$REPO_DIR/mask/." "$PUB_DIR/"          || fail "复制伪装站失败"
    mkdir -p "$PUB_DIR/$SECRET"                   || fail "建不了 $PUB_DIR/$SECRET"
    cp -a "$REPO_DIR/v3/." "$PUB_DIR/$SECRET/"    || fail "复制真实站失败"
fi

# 兜底清理：两种分支都过一遍，保证开发用文件不对外暴露
find "$PUB_DIR/$SECRET" -mindepth 1 -maxdepth 1 \
     \( -name '_*' -o -name '*.py' -o -name '__pycache__' \) \
     -exec rm -rf {} + 2>/dev/null || true

# ---- 4. 兜底检查 ----------------------------------------------
[ -f "$PUB_DIR/index.html" ]            || fail "根目录没有 index.html —— error_page 会指空，根路径直接 500"
[ -f "$PUB_DIR/$SECRET/index.html" ]    || fail "密钥目录里没有 index.html"

chmod -R a+rX "$PUB_DIR" 2>/dev/null || true

# 日志里只记数量，不记密钥
log "组装完成：伪装站 $(find "$REPO_DIR/mask" -type f | wc -l | tr -d ' ') 个文件铺在根；真实站 $(find "$REPO_DIR/v3" -type f | wc -l | tr -d ' ') 个文件铺进密钥目录"
exit 0
