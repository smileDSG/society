#!/usr/bin/env bash
#
# 象罔官网 · Cloudflare HTTPS 隧道（Quick Tunnel）
# ============================================================
# 让站点有一个 https://xxx.trycloudflare.com 入口，无需域名、无需备案。
# 配合「端口只听 127.0.0.1」，它就是公网唯一入口。
#
# ⚠️ 先读这三条，再决定要不要用：
#   1. **地址不固定**。每次 cloudflared 重启都会换一个新的随机域名，
#      服务器重启、容器重启、隧道断线重连都可能换。换了你得重新问它要。
#      想地址固定，只能用「命名隧道 + 自己的域名」（见文件末尾说明）。
#   2. **这是一个公开地址**。它比 `IP:8085` 更好记、更好传播，
#      也就更容易被转发出去 —— 转发一次，掩盖层就白做了。
#      真实站仍然要 /<密钥>/ 才能进，但请把"别贴出去"当真。
#   3. **官方定位是测试用途**，不适合当生产站点长期依赖。免费、无 SLA。
#
# 和「掩盖层」的关系：
#   隧道指向 127.0.0.1:8085（整个站点），**不是**直接指向 /<密钥>/。
#   所以 https://<隧道域名>/          → 伪装站（和 IP 访问一样）
#      https://<隧道域名>/<密钥>/      → 真实站
#   这样掩盖层在 HTTPS 入口上同样成立。
#   ⚠️ 别改成指向 /<密钥>/ —— 那等于把 HTTPS 地址直接变成真实站大门。
#
# 用法（服务器上，root）：
#   bash /opt/xiangwang/deploy/setup-tunnel.sh        # 已存在就直接报当前地址
#   bash /opt/xiangwang/deploy/setup-tunnel.sh -f     # 重建（会换新地址）
#   bash /opt/xiangwang/deploy/setup-tunnel.sh -h
# ============================================================

set -u

CNAME="xw-tunnel"
IMG="cloudflare/cloudflared:latest"
ORIGIN="${XW_ORIGIN:-http://127.0.0.1:8085}"
SECRET_FILE="/etc/xiangwang/mask-secret"
URL_RE='https://[a-z0-9-]*\.trycloudflare\.com'

FORCE=""
for a in "$@"; do
    case "$a" in
        -f|--force) FORCE=1 ;;
        -h|--help)  sed -n '2,25p' "$0"; exit 0 ;;
    esac
done

say()  { printf '%s\n' "$*"; }
step() { printf '\n\033[1m[%s]\033[0m %s\n' "$1" "$2"; }
die()  { printf '\n  \033[31m错误：%s\033[0m\n\n' "$*"; exit 1; }
warn() { printf '  \033[33m! %s\033[0m\n' "$*"; }
ok()   { printf '  \033[32m✓\033[0m %s\n' "$*"; }

say "=============================================="
say " 象罔官网 · Cloudflare HTTPS 隧道"
say "=============================================="

# ---------------------------------------------------------------
step "1/5" "环境检查"

[ "$(id -u)" -eq 0 ] || die "请用 root 执行：sudo bash $0"
command -v docker >/dev/null 2>&1 || die "没有 docker"
ok "docker 就位"

# 源站要活着，否则隧道起来也是 502
if curl -s -o /dev/null --max-time 8 "$ORIGIN/" 2>/dev/null; then
    ok "源站可达：$ORIGIN"
else
    die "源站连不上：$ORIGIN
  先确认站点容器在跑：docker ps --filter name=xiangwang-site
  （如果端口不是 8085，用 XW_ORIGIN=http://127.0.0.1:<端口> 重跑）"
fi

[ -r "$SECRET_FILE" ] || warn "读不到 $SECRET_FILE —— 跳过真实站那一项验证（伪装页仍会验证）"
SECRET=""
[ -r "$SECRET_FILE" ] && SECRET="$(tr -d ' \t\r\n' < "$SECRET_FILE")"

# ---------------------------------------------------------------
step "2/5" "启动隧道容器"

# 已存在就先复用：quick tunnel 每次启动都换域名，能不换就不换
if [ -z "$FORCE" ] && docker inspect "$CNAME" >/dev/null 2>&1; then
    st="$(docker inspect -f '{{.State.Running}}' "$CNAME" 2>/dev/null)"
    if [ "$st" = "true" ]; then
        ok "隧道容器已在运行，直接复用它（不重建，地址不会变）"
    else
        docker start "$CNAME" >/dev/null 2>&1 || { docker rm -f "$CNAME" >/dev/null 2>&1; FORCE=1; }
    fi
fi

if [ -n "$FORCE" ] || ! docker inspect "$CNAME" >/dev/null 2>&1; then
    docker rm -f "$CNAME" >/dev/null 2>&1 || true
    say "  正在拉镜像（第一次会花点时间）…"
    if ! docker run -d --name "$CNAME" --restart always \
            --network host \
            "$IMG" tunnel --no-autoupdate --url "$ORIGIN" >/dev/null 2>&1; then
        die "容器起不来。常见原因：
  a) 拉不到镜像 cloudflare/cloudflared —— 换个源或改用二进制（见 -h 末尾的备用方案）
  b) --network host 在当前 Docker 版本不支持 —— 改用 -e ORIGIN 或把源站改成容器名
  看详细日志：docker logs $CNAME --tail 30"
    fi
    ok "隧道容器已启动"
fi

# ---------------------------------------------------------------
step "3/5" "等隧道分配域名（最多 60 秒）"

URL=""
for _ in $(seq 1 30); do
    URL="$(docker logs "$CNAME" 2>&1 | grep -oE "$URL_RE" | tail -1)"
    [ -n "$URL" ] && break
    sleep 2
done
[ -n "$URL" ] || die "60 秒没拿到域名。看日志：docker logs $CNAME --tail 50
  若看到大量 connection error / timeout，多半是出网被限制，
  在 docker run 里给 cloudflared 加 --protocol http2 试试（UDP 7844 不通时走 TCP 443）。"
ok "隧道域名：$URL"

# Cloudflare 边缘要几秒才开始路由，重试几次再判定
say "  等边缘生效…"
for _ in $(seq 1 10); do
    root_code="$(curl -s -o /dev/null -w '%{http_code}' --max-time 25 "$URL/" 2>/dev/null)"
    [ "$root_code" = "200" ] && break
    sleep 3
done

# ---------------------------------------------------------------
step "4/5" "验收"

failed=0

root_html="$(curl -s --max-time 25 "$URL/" 2>/dev/null)"
if [ "$root_code" = "200" ]; then ok "HTTPS 根路径可访问（200）"; else warn "HTTPS 根路径返回 ${root_code:-空}"; failed=$((failed+1)); fi

case "$root_html" in
    *笔记存档*) ok "根路径 = 伪装页（掩盖层在 HTTPS 上同样成立）" ;;
    *)          warn "根路径不是伪装页，内容可疑"; failed=$((failed+1)) ;;
esac

case "$root_html" in
    *象罔*) warn "根路径漏出了「象罔」字样 —— 掩盖层在 HTTPS 上失效"; failed=$((failed+1)) ;;
    *)      ok "根路径不含「象罔」字样" ;;
esac

if [ -n "$SECRET" ]; then
    real_html="$(curl -s --max-time 25 "$URL/$SECRET/login.html" 2>/dev/null)"
    case "$real_html" in
        *象罔*) ok "密钥路径能打开真实站" ;;
        *)      warn "密钥路径打不开真实站（$URL/$SECRET/login.html）"; failed=$((failed+1)) ;;
    esac
fi

# ---------------------------------------------------------------
step "5/5" "记下这个地址"

say ""
say "  =============================================="
say "   HTTPS 入口：  $URL/"
if [ -n "$SECRET" ]; then
say ""
say "   真实站（只发给社团成员）："
say "      $URL/$SECRET/"
say "      $URL/$SECRET/login.html"
fi
say "  =============================================="
say ""
say "  地址会不会变：会。以下情况都会换域名 ——"
say "    服务器重启 / docker restart $CNAME / 隧道断线重连 / 重跑本脚本加 -f"
say "  换地址后怎么查（不用重启，问它要）："
say "    docker logs $CNAME 2>&1 | grep -oE '$URL_RE' | tail -1"
say ""
say "  ⚠️ 这个地址是公开的。它比 IP:端口更好记也更好转发 ——"
say "     转发一次，掩盖层就白做了。只发给确定该给的人。"
say ""
say "  ⚠️ 登录态不互通：浏览器按「协议+域名+端口」隔离 localStorage，"
say "     在 IP:8085 登录过的人，走这个 HTTPS 地址要再登一次。"
say ""
say "  想要固定不变的地址？那要用「命名隧道 + 自己的域名」："
say "    1. 把域名 DNS 托管到 Cloudflare"
say "    2. cloudflared tunnel login && cloudflared tunnel create xw"
say "    3. cloudflared tunnel route dns xw <你的域名>"
say "    4. 把本脚本里的 quick tunnel 换成："
say "         cloudflared tunnel run --url $ORIGIN xw"
say "    需要 Cloudflare 账号 + 一个域名（约 ¥10/年起）。"
say ""
say "  备份方案（拉不到 Docker 镜像时）："
say "    curl -Lo /usr/local/bin/cloudflared \\"
say "      https://ghfast.top/https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"
say "    chmod +x /usr/local/bin/cloudflared"
say "    nohup /usr/local/bin/cloudflared tunnel --no-autoupdate --url $ORIGIN \\"
say "      >/var/log/xiangwang-tunnel.log 2>&1 &"
say "    grep -oE '$URL_RE' /var/log/xiangwang-tunnel.log | tail -1"
say ""

[ "$failed" -eq 0 ] || exit 1
exit 0
