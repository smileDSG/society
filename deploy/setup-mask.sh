#!/usr/bin/env bash
#
# 象罔官网 ·「掩盖」一键部署
# ============================================================
# 做完之后：
#   http://<IP>:8085/                    陌生人只会看到一个平平无奇的笔记站
#   http://<IP>:8085/login.html          不存在（返回伪装首页）
#   http://<IP>:8085/<密钥>/             真实社团站
#   http://<IP>:8085/<密钥>/login.html   真实登录页
#
# 用法（在服务器上，root 身份执行）：
#   bash /opt/xiangwang/deploy/setup-mask.sh              # 会先问一句再动
#   bash /opt/xiangwang/deploy/setup-mask.sh -y           # 不问，直接干
#   bash /opt/xiangwang/deploy/setup-mask.sh -r           # 换一把新密钥（旧链接立即失效）
#   bash /opt/xiangwang/deploy/setup-mask.sh -s k7m2p9qv  # 自己指定一个短密钥
#   bash /opt/xiangwang/deploy/setup-mask.sh -h           # 看这段说明
#
# 密钥默认是一串 8 位随机字符，例如 k7m2p9qv。
#   够短 —— 能在群里打字发、能口述；
#   也够难猜 —— 从「不含 0/O/1/l/I」的 32 个字符里取，32^8 ≈ 1.1 万亿种组合，
#   字典猜不中，穷举也不现实。
#   想再短不拦着，但别用成短的英文单词（friend/team/club 这种一猜就中）。
#
# 可以重复执行：密钥不会变，容器会重建一次（约 1 秒不可用）。
# 重建前会在 /etc/xiangwang/rollback.sh 留下退回脚本。
#
# ⚠️ 安全边界（务必读）
#   本脚本只做「藏入口」这一件事 —— 属于"别让人注意到"的层面。
#   真实站仍然是纯前端门禁：邀请码、账号、会话全在浏览器 localStorage 里，
#   而这些内容明文写在**公开仓库**的 v3/assets/auth.js 中。
#   也就是说：仓库里已经有 XW2026-ADMIN 这种管理员码，谁都看得到。
#   藏入口能挡住扫描器、好奇的人和自动爆破脚本，
#   挡不住"看过这个仓库的人"。学号、手机号、成绩之类一律不要放上去。
# ============================================================

set -u

REPO_DIR="/opt/xiangwang"
PUB_DIR="/var/www/xw-pub"
CONF_DIR="/etc/xiangwang"
SECRET_FILE="$CONF_DIR/mask-secret"
CNAME="xiangwang-site"
IMG="nginx:alpine"
DEFAULT_PORT="8085"

ASSUME_YES=""
REGEN=""
CUSTOM=""
while [ $# -gt 0 ]; do
    case "$1" in
        -y|--yes)        ASSUME_YES=1 ;;
        -r|--regenerate) REGEN=1 ;;
        -s|--secret)     CUSTOM="${2:-}"; shift ;;
        -h|--help)       sed -n '2,34p' "$0"; exit 0 ;;
    esac
    shift
done

say()  { printf '%s\n' "$*"; }
step() { printf '\n\033[1m[%s]\033[0m %s\n' "$1" "$2"; }
die()  { printf '\n  \033[31m错误：%s\033[0m\n\n' "$*"; exit 1; }
warn() { printf '  \033[33m! %s\033[0m\n' "$*"; }
ok()   { printf '  \033[32m✓\033[0m %s\n' "$*"; }

say "=============================================="
say " 象罔官网 · 掩盖部署"
say "=============================================="

# ---------------------------------------------------------------
step "1/7" "环境检查"

[ "$(id -u)" -eq 0 ] || die "请用 root 执行：sudo bash $0"

command -v docker >/dev/null 2>&1 || die "这台机器上没有 docker。
  本项目线上用的是「Docker + nginx:alpine 挂载目录」那条路。
  如果你其实是宿主机直装 Nginx，请改用 deploy/nginx.conf，
  并把 root 指向 /var/www/xw-pub、按 README 第五节挂好。"
ok "docker 就位"

[ -d "$REPO_DIR" ] || die "找不到仓库目录 $REPO_DIR"
[ -d "$REPO_DIR/v3" ]   || die "$REPO_DIR/v3 不存在（真实站源码）"
[ -d "$REPO_DIR/mask" ] || die "$REPO_DIR/mask 不存在（伪装站）。
  服务器上的代码太旧了，先更新：
    cd $REPO_DIR && bash deploy/autopull.sh -v
  如果还是拉不到，就手工把最新代码弄上来（见 README 第九节）。"
ok "仓库目录就位"

[ -f "$REPO_DIR/deploy/container.conf" ] || die "找不到 deploy/container.conf"
[ -f "$REPO_DIR/deploy/publish.sh" ]     || die "找不到 deploy/publish.sh"

if grep -q 'publish.sh' "$REPO_DIR/deploy/autopull.sh" 2>/dev/null; then
    ok "自动部署已接入 publish.sh（每次拉代码后会自动重铺）"
else
    warn "deploy/autopull.sh 里还没有调用 publish.sh"
    warn "  后果：以后你推新代码，网站内容不会自动更新，需要手工跑一次"
    warn "        bash $REPO_DIR/deploy/publish.sh"
    warn "  解决：把最新代码拉下来即可（新版 autopull.sh 已包含这一步）"
fi

# ---------------------------------------------------------------
step "2/7" "确定隐秘目录名"

# 8 位随机字符。字符集刻意剔掉 0/O/1/l/I —— 免得在群里口述时听错、
# 手打时看错。32 个字符取 8 位 ≈ 1.1 万亿种组合，猜不中。
gen_secret() {
    head -c 2048 /dev/urandom 2>/dev/null | tr -dc 'a-hjkmnp-z2-9' | head -c 8
}

mkdir -p "$CONF_DIR" || die "建不了 $CONF_DIR"
chmod 700 "$CONF_DIR"

NEW=""
if [ -n "$CUSTOM" ]; then
    NEW=1
elif [ -n "$REGEN" ]; then
    NEW=1
elif [ ! -s "$SECRET_FILE" ]; then
    NEW=1
fi

if [ -n "$NEW" ]; then
    if [ -n "$CUSTOM" ]; then
        SECRET="$CUSTOM"
        [ "${#SECRET}" -ge 6 ] || die "自定的密钥太短了，至少 6 位（建议 8 位）"
        case "$SECRET" in
            */*|*..*|.*|*[!A-Za-z0-9_-]*) die "自定的密钥含非法字符（只允许字母、数字、- _，不能含 / 和 ..）" ;;
        esac
        case "$SECRET" in
            [Ff]riend|[Tt]eam|[Cc]lub|[Rr]eal|[Ii]n|[Gg]o|[Ll]ogin|[Aa]dmin|[Hh]idden|[Ss]ecret|[Xx][Ww])
                warn "你自定的「$SECRET」很像常用词，被猜中的概率不低。" ;;
        esac
        ok "已按你指定的值设置密钥"
    else
        SECRET="$(gen_secret)"
        [ -n "$SECRET" ] || die "生成密钥失败"
        if [ -n "$REGEN" ]; then
            ok "已换新密钥（旧链接从现在起全部失效）"
        else
            ok "已生成密钥"
        fi
    fi
    umask 077
    printf '%s\n' "$SECRET" > "$SECRET_FILE" || die "写不了 $SECRET_FILE"
    chmod 600 "$SECRET_FILE"
else
    ok "沿用现有密钥（没变）"
fi

SECRET="$(tr -d ' \t\r\n' < "$SECRET_FILE")"
[ -n "$SECRET" ] || die "$SECRET_FILE 是空的"
case "$SECRET" in
    */*|*..*|.*|*[!A-Za-z0-9_-]*) die "密钥含非法字符，删掉 $SECRET_FILE 重跑本脚本" ;;
esac

# 顺手留一份给管理员备忘（只有 root 能读）
printf '%s\n' "$SECRET" > "$CONF_DIR/entry-path.txt"
chmod 600 "$CONF_DIR/entry-path.txt"
say "     密钥：$SECRET"
say "     （同时写在 $SECRET_FILE 和 $CONF_DIR/entry-path.txt，别外传）"

# ---------------------------------------------------------------
step "3/7" "组装对外发布目录 $PUB_DIR"

sed -i 's/\r$//' "$REPO_DIR/deploy/publish.sh" 2>/dev/null || true

if ! command -v rsync >/dev/null 2>&1; then
    say "  正在装 rsync（增量同步，避免每次重铺时短暂空站）..."
    (apt-get update -qq && apt-get install -y -qq rsync) >/dev/null 2>&1 || \
        warn "装 rsync 失败，将退化为「清空再拷」的方式，功能不受影响"
fi

bash "$REPO_DIR/deploy/publish.sh" || die "组装失败，详见 /var/log/xiangwang-mask.log"

[ -f "$PUB_DIR/index.html" ]         || die "$PUB_DIR/index.html 不存在"
[ -f "$PUB_DIR/$SECRET/index.html" ] || die "$PUB_DIR/$SECRET/index.html 不存在"
ok "伪装站在根目录，真实站在 $SECRET/ 下"

# ---------------------------------------------------------------
step "4/7" "读取当前容器参数，留一份退回脚本"

PORT="$DEFAULT_PORT"
OLD_SRC="$REPO_DIR/v3"

if docker inspect "$CNAME" >/dev/null 2>&1; then
    p="$(docker port "$CNAME" 80/tcp 2>/dev/null | head -1 | sed 's/.*://')"
    [ -n "$p" ] && PORT="$p"

    s="$(docker inspect -f '{{range .Mounts}}{{.Source}}{{"\n"}}{{end}}' "$CNAME" 2>/dev/null | head -1)"
    [ -n "$s" ] && OLD_SRC="$s"

    say "  当前容器：端口 $PORT，挂载 $OLD_SRC"
else
    warn "没有找到名为 $CNAME 的容器，将按默认端口 $PORT 新建"
fi

umask 077
cat > "$CONF_DIR/rollback.sh" <<EOF
#!/usr/bin/env bash
# 退回「掩盖」之前的状态：站点内容直接挂在根目录。
# 由 setup-mask.sh 自动生成于 $(date '+%F %T')
set -u
docker rm -f $CNAME 2>/dev/null || true
docker run -d --name $CNAME --restart always \\
  -p $PORT:80 \\
  -v $OLD_SRC:/usr/share/nginx/html:ro \\
  $IMG
echo "已退回旧状态（根目录直接是真实站）：http://<IP>:$PORT/"
EOF
chmod 700 "$CONF_DIR/rollback.sh"
umask 022
ok "退回脚本：bash $CONF_DIR/rollback.sh"

# ---------------------------------------------------------------
step "5/7" "重启容器，挂上新目录与新配置"

if [ -z "$ASSUME_YES" ]; then
    say "  接下来会删掉旧容器 $CNAME 并按新挂载重建，约 1 秒不可访问。"
    printf '  继续？[Y/n] '
    read -r ans || true
    case "$ans" in
        n|N|no|NO) die "已取消，什么都没改" ;;
    esac
fi

docker rm -f "$CNAME" >/dev/null 2>&1 || true

docker run -d --name "$CNAME" --restart always \
    -p "$PORT:80" \
    -v "$PUB_DIR:/usr/share/nginx/html:ro" \
    -v "$REPO_DIR/deploy/container.conf:/etc/nginx/conf.d/default.conf:ro" \
    "$IMG" >/dev/null || die "容器起不来，用 bash $CONF_DIR/rollback.sh 退回"

# 等它监听上
up=""
for _ in $(seq 1 20); do
    if curl -s -o /dev/null --max-time 2 "http://127.0.0.1:$PORT/" 2>/dev/null; then up=1; break; fi
    sleep 0.5
done
[ -n "$up" ] || die "容器起来了但端口 $PORT 不通，看日志：docker logs $CNAME --tail 50"

docker exec "$CNAME" nginx -t >/dev/null 2>&1 || die "容器内 nginx 配置语法有错：docker exec $CNAME nginx -t"
ok "容器运行中，nginx 配置校验通过"

# ---------------------------------------------------------------
step "6/7" "验收（这一步最关键，别跳过）"

BASE="http://127.0.0.1:$PORT"
passed=0
failed=0
chk() {  # chk <说明> <条件0/1>
    if [ "$2" = "1" ]; then ok "$1"; passed=$((passed+1)); else warn "不通过：$1"; failed=$((failed+1)); fi
}

root_html="$(curl -s --max-time 8 "$BASE/" 2>/dev/null)"
case "$root_html" in *笔记存档*) chk "根路径 = 伪装页" 1 ;; *) chk "根路径 = 伪装页" 0 ;; esac
case "$root_html" in *象罔*)      chk "根路径不含「象罔」字样" 0 ;; *) chk "根路径不含「象罔」字样" 1 ;; esac

old_login="$(curl -s --max-time 8 "$BASE/login.html" 2>/dev/null)"
case "$old_login" in *象罔*) chk "旧的 /login.html 已够不到真实站" 0 ;; *) chk "旧的 /login.html 已够不到真实站" 1 ;; esac

new_login="$(curl -s --max-time 8 "$BASE/$SECRET/login.html" 2>/dev/null)"
case "$new_login" in *象罔*) chk "密钥路径能打开真实站" 1 ;; *) chk "密钥路径能打开真实站" 0 ;; esac

srv="$(curl -sI --max-time 8 "$BASE/" 2>/dev/null | tr -d '\r' | awk -F': ' 'tolower($1)=="server"{print $2}')"
[ "$srv" = "nginx" ] && chk "响应头不再泄露 nginx 版本号" 1 || chk "响应头不再泄露 nginx 版本号（当前：${srv:-空}）" 0

hit404="$(curl -s --max-time 8 "$BASE/.git/config" 2>/dev/null)"
case "$hit404" in *象罔*) chk ".git 等敏感路径已被挡住" 0 ;; *) chk ".git 等敏感路径已被挡住" 1 ;; esac

say ""
say "     通过 $passed 项，失败 $failed 项"

# ---------------------------------------------------------------
step "7/7" "记住这个地址"

IP="$(curl -s --max-time 5 https://api.ipify.org 2>/dev/null || true)"
[ -n "$IP" ] || IP="47.99.180.48"

say ""
say "  =============================================="
say "   对外（给陌生人看的）：  http://$IP:$PORT/"
say ""
say "   真实站入口（只发给社团成员）："
say "       http://$IP:$PORT/$SECRET/"
say "       http://$IP:$PORT/$SECRET/login.html"
say "  =============================================="
say ""
say "  三件事别忘："
say "   1. 把新入口发到社团群里。原来流传的"
say "      http://$IP:$PORT/login.html 从现在起打不开真实站了。"
say "   2. 别再在任何公开地方贴新入口 —— 贴出来就等于没有。"
say "   3. 密钥在 $SECRET_FILE。换一把："
say "      bash $0 -r"
say ""
say "  以后推代码：照旧推 GitHub 就行，服务器每 5 分钟自动拉取并重铺，"
say "  伪装站和真实站都会跟着更新，你什么都不用做。"
say ""
say "  退回旧状态： bash $CONF_DIR/rollback.sh"
say "  看容日志：   docker logs $CNAME --tail 50"
say ""

[ "$failed" -eq 0 ] || { say "  有项目没通过，先别急着把链接发出去，把上面的告警贴给我看。"; exit 1; }
exit 0
