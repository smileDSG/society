#!/usr/bin/env bash
#
# 象罔官网 ·「直连阿里云」一键部署（方案 A）
# ============================================================
# 为什么要有这个脚本：
#   原来的公网入口是 Cloudflare 免费 quick tunnel（*.trycloudflare.com）。
#   Cloudflare 在大陆没有节点，校园网/宽带经常连不上，导致国内打不开官网。
#   本脚本把入口换成「直连阿里云 IP + 证书」，大陆访问稳。
#
# 做了什么（不破坏原有伪装层）：
#   1. 生成证书：默认自签 IP 证书（零依赖，立刻能用，浏览器会提示"不安全"）；
#      传 -d 域名 -m 邮箱 则用 Let's Encrypt 自动签发干净证书（无警告）。
#   2. 重建 nginx 容器：对外暴露 0.0.0.0:80 和 0.0.0.0:443，
#      挂载 container-tls.conf + 证书目录；并停掉旧的 Cloudflare 隧道
#      （它的 8085 源站端口不再暴露，留着只会 502）。
#   3. 写 /etc/xiangwang/direct-mode 标记，让 setup-mask.sh 以后重建时也走 TLS。
#
# 伪装层完全不变：根目录仍是假站，/<密钥>/ 仍是真实站，安全边界不变。
#
# 用法（服务器上，root）：
#   bash /opt/xiangwang/deploy/setup-direct.sh                 # 自签 IP 证书，立刻生效
#   bash /opt/xiangwang/deploy/setup-direct.sh -d xw.duckdns.org -m you@x.com
#                                                              # Let's Encrypt 干净证书
#   bash /opt/xiangwang/deploy/setup-direct.sh -h
#
# 之后还要做（脚本会提醒，但改不了阿里云控制台）：
#   阿里云 ECS → 安全组 → 入方向 → 允许 TCP 80 和 443，源 0.0.0.0/0。
#   （旧隧道 xw-tunnel 已在本脚本中停止；它的 8085 源站端口不再暴露。）
# ============================================================

set -u

REPO_DIR="/opt/xiangwang"
CONF_DIR="/etc/xiangwang"
PUB_DIR="/var/www/xw-pub"
TLS_DIR="$CONF_DIR/tls"
ACME_DIR="/var/www/acme"
SECRET_FILE="$CONF_DIR/mask-secret"
DEPLOY_DIR="$REPO_DIR/deploy"
CNAME="xiangwang-site"
IMG="nginx:alpine"

DOMAIN=""
EMAIL=""
while [ $# -gt 0 ]; do
    case "$1" in
        -d|--domain) DOMAIN="${2:-}"; shift ;;
        -m|--email)  EMAIL="${2:-}";  shift ;;
        -h|--help)   sed -n '2,30p' "$0"; exit 0 ;;
    esac
    shift
done

say()  { printf '%s\n' "$*"; }
step() { printf '\n\033[1m[%s]\033[0m %s\n' "$1" "$2"; }
die()  { printf '\n  \033[31m错误：%s\033[0m\n\n' "$*"; exit 1; }
warn() { printf '  \033[33m! %s\033[0m\n' "$*"; }
ok()   { printf '  \033[32m✓\033[0m %s\n' "$*"; }

say "=============================================="
say " 象罔官网 · 直连阿里云部署（方案 A）"
say "=============================================="

# ---------------------------------------------------------------
step "1/6" "环境检查"
[ "$(id -u)" -eq 0 ] || die "请用 root 执行：sudo bash $0"
command -v docker >/dev/null 2>&1 || die "没有 docker"
ok "docker 就位"

[ -r "$SECRET_FILE" ] || die "读不到 $SECRET_FILE —— 先跑过 setup-mask.sh 生成密钥"
SECRET="$(tr -d ' \t\r\n' < "$SECRET_FILE")"
[ -n "$SECRET" ] || die "$SECRET_FILE 是空的"
ok "密钥就位：$SECRET"

[ -d "$PUB_DIR" ] && [ -f "$PUB_DIR/index.html" ] && [ -f "$PUB_DIR/$SECRET/index.html" ] \
    || die "发布目录还没组装好 —— 先跑 bash $DEPLOY_DIR/publish.sh"

# ---------------------------------------------------------------
step "2/6" "确定对外地址与证书"
IP="$(curl -s --max-time 6 https://api.ipify.org 2>/dev/null || true)"
[ -n "$IP" ] || IP="47.99.180.48"
if [ -n "$DOMAIN" ]; then
    [ -n "$EMAIL" ] || die "用了 -d 域名就必须带 -m 邮箱（Let's Encrypt 需要）"
    say "  对外域名：$DOMAIN（证书走 Let's Encrypt）"
else
    DOMAIN="$IP"
    say "  暂无域名 → 对外地址用 IP：$IP（自签证书，浏览器会提示不安全）"
    warn "  想要无警告的干净证书：先去 duckdns.org 免费注册一个 <名字>.duckdns.org，"
    warn "        A 记录指向 $IP，再重跑本脚本加 -d <名字>.duckdns.org -m 你的邮箱"
fi

mkdir -p "$TLS_DIR" "$ACME_DIR" || die "建不了 $TLS_DIR / $ACME_DIR"
chmod 700 "$TLS_DIR"
chmod 755 "$ACME_DIR"

# ---------------------------------------------------------------
step "3/6" "准备证书"
if [ -n "$EMAIL" ]; then
    # ---- Let's Encrypt（certbot 官方镜像，不污染宿主机）----
    say "  用 certbot 申请证书（webroot 模式，需要 80 端口此刻可达）…"
    docker run --rm \
        -v "$TLS_DIR:/etc/letsencrypt" \
        -v "$ACME_DIR:/var/www/acme" \
        certbot/certbot:latest certonly --webroot -w /var/www/acme \
        -d "$DOMAIN" --non-interactive --agree-tos -m "$EMAIL" \
        --keep-until-expiring >/dev/null 2>&1 \
        || die "certbot 失败。常见原因：
   a) 域名 $DOMAIN 没解析到本机 IP（$IP），或阿里云安全组没开 80
   b) 拉不到 certbot/certbot 镜像
   先确认：dig +short $DOMAIN 应返回 $IP；排好后再重跑。"
    LIVE="$TLS_DIR/live/$DOMAIN"
    cp "$LIVE/fullchain.pem" "$TLS_DIR/fullchain.pem" 2>/dev/null \
        && cp "$LIVE/privkey.pem"  "$TLS_DIR/privkey.pem"  2>/dev/null \
        || die "证书拷贝失败：$LIVE 下没找到 fullchain.pem / privkey.pem"
    ok "Let's Encrypt 证书已签发并放到 $TLS_DIR"
else
    # ---- 自签 IP 证书 ----
    if [ -f "$TLS_DIR/fullchain.pem" ] && [ -f "$TLS_DIR/privkey.pem" ]; then
        ok "已存在自签证书，复用（要重签先删 $TLS_DIR/*.pem）"
    else
        SAN="IP:$IP"
        openssl req -x509 -newkey rsa:2048 -nodes \
            -keyout "$TLS_DIR/privkey.pem" -out "$TLS_DIR/fullchain.pem" \
            -days 825 -subj "/CN=$IP" -addext "subjectAltName=$SAN" >/dev/null 2>&1 \
            || die "自签证书生成失败（openssl 缺失？）"
        ok "自签证书已生成（有效期 ~2 年）"
    fi
fi
chmod 600 "$TLS_DIR/privkey.pem" 2>/dev/null || true

# ---------------------------------------------------------------
step "4/6" "标记直连模式，重建容器"
touch "$CONF_DIR/direct-mode"
ok "已写入 $CONF_DIR/direct-mode（以后 setup-mask.sh 重建也走 TLS）"

docker rm -f "$CNAME" >/dev/null 2>&1 || true

# 旧 Cloudflare 隧道已不再需要（它的 8085 源站端口本脚本不再暴露，留着会 502）
if docker inspect xw-tunnel >/dev/null 2>&1; then
    docker stop xw-tunnel >/dev/null 2>&1 || true
    ok "已停止旧的 Cloudflare 隧道容器（入口已换成直连）"
fi

docker run -d --name "$CNAME" --restart always \
    -p 0.0.0.0:80:80 \
    -p 0.0.0.0:443:443 \
    -v "$PUB_DIR:/usr/share/nginx/html:ro" \
    -v "$DEPLOY_DIR/container-tls.conf:/etc/nginx/conf.d/default.conf:ro" \
    -v "$TLS_DIR:/etc/nginx/tls:ro" \
    -v "$ACME_DIR:/var/www/acme:ro" \
    "$IMG" >/dev/null || die "容器起不来，检查：docker logs $CNAME --tail 50"

# 等监听
up=""
for _ in $(seq 1 20); do
    if curl -s -o /dev/null --max-time 2 "http://127.0.0.1:8085/" 2>/dev/null; then up=1; break; fi
    sleep 0.5
done
[ -n "$up" ] || die "容器起来了但 8085 不通，看日志：docker logs $CNAME --tail 50"

docker exec "$CNAME" nginx -t >/dev/null 2>&1 || die "nginx 配置语法有错：docker exec $CNAME nginx -t"
ok "容器运行中，nginx 配置校验通过"

# ---------------------------------------------------------------
step "5/6" "验收"
passed=0; failed=0
chk() { if [ "$2" = "1" ]; then ok "$1"; passed=$((passed+1)); else warn "不通过：$1"; failed=$((failed+1)); fi; }

# HTTPS 根路径
https_root_code="$(curl -s -o /dev/null -w '%{http_code}' --max-time 15 "https://$DOMAIN/" 2>/dev/null)"
# 自签证书 curl 会报 cert 错，用 -k 再探一次拿到状态码
[ "$https_root_code" = "200" ] || https_root_code="$(curl -sk -o /dev/null -w '%{http_code}' --max-time 15 "https://$DOMAIN/" 2>/dev/null)"
[ "$https_root_code" = "200" ] && chk "HTTPS 根路径可访问（200）" 1 || chk "HTTPS 根路径可访问（当前 ${https_root_code:-空}）" 0

root_html="$(curl -sk --max-time 15 "https://$DOMAIN/" 2>/dev/null)"
case "$root_html" in *笔记存档*) chk "根路径 = 伪装页" 1 ;; *) chk "根路径 = 伪装页" 0 ;; esac
case "$root_html" in *象罔*)      chk "根路径不含「象罔」字样" 0 ;; *) chk "根路径不含「象罔」字样" 1 ;; esac

real_html="$(curl -sk --max-time 15 "https://$DOMAIN/$SECRET/login.html" 2>/dev/null)"
case "$real_html" in *象罔*) chk "密钥路径能打开真实站" 1 ;; *) chk "密钥路径能打开真实站" 0 ;; esac

say "     通过 $passed 项，失败 $failed 项"

# ---------------------------------------------------------------
step "6/6" "善后与对外地址"
say ""
say "  =============================================="
say "   对外（给陌生人看的）：  https://$DOMAIN/"
say ""
say "   真实站入口（只发给社团成员）："
say "      https://$DOMAIN/$SECRET/"
say "      https://$DOMAIN/$SECRET/login.html"
say "  =============================================="
say ""
if [ -z "$EMAIL" ]; then
    warn "当前是自签证书：浏览器首次打开会提示「连接不安全」，点「继续访问」即可。"
    warn "想去掉提示：注册 duckdns.org 免费域名并带 -d/-m 重跑本脚本。"
fi
say ""
say "  ⚠️ 还差一步（脚本改不了阿里云控制台）："
say "     登录阿里云 → ECS → 安全组 → 入方向 → 允许 TCP 80 和 443，源 0.0.0.0/0。"
say "     同时把 8085 那条入方向规则删掉（双保险，端口本就只听 127.0.0.1）。"
say ""
say "  ⚠️ 旧 Cloudflare 隧道 xw-tunnel 已在本脚本中停止（它的 8085 源站端口不再暴露）。"
say "     若要回退到隧道模式：先 docker start xw-tunnel，再删掉 $CONF_DIR/direct-mode 后跑 setup-mask.sh。"
say ""
say "  以后轮换密钥 / 重铺：bash $DEPLOY_DIR/setup-mask.sh   （会自动沿用 TLS + 80/443）"
say "  退回隧道模式：       删掉 $CONF_DIR/direct-mode 后再跑 setup-mask.sh"
say ""
[ "$failed" -eq 0 ] || { say "  有项目没通过，先别发链接，把上面的告警贴给我看。"; exit 1; }
exit 0
