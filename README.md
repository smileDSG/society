# 象罔社团官网 · XIANGWANG CLUB

南京信息工程大学「象罔社团」官方网站。科技风静态站（多页 HTML），带邀请码准入的注册 / 登录 / 页面门禁。

> 知索不得，象罔得之。

---

## 一、项目结构

```
society/
├─ v3/                      ← ★ 构建产物：真正要部署的静态站（纯 HTML/CSS/JS）
│  ├─ index.html            首页
│  ├─ login.html            登录 / 注册（唯一不设门禁的页面）
│  ├─ area.html             成员专区（内部页）
│  ├─ members.html          成员总览   → member-*.html（18 位成员独立详情页）
│  ├─ projects.html         作品列表   → work-w1 ~ w6.html
│  ├─ life.html             社团动态   → life-a1 ~ a6.html
│  ├─ job-j1 ~ j4.html      招新岗位详情
│  └─ assets/               site.css / site.js / auth.css / auth.js / logo.png
│
├─ src/                     TypeScript 源码（首页交互：粒子星域/打字机/3D 倾斜/数字滚动…）
├─ redesign/                首页重设计稿
├─ dist/                    早期 v2 构建产物（保留备查，不参与部署）
├─ build_v3.py              ★ v3 静态站生成器（数据 + 模板都在里面）
├─ deploy/nginx.conf        Nginx 站点配置（给「宿主机直装 Nginx」那条路用）
├─ .github/workflows/       自动部署流水线（推送 main 即在服务器上 git pull，见第九节）
├─ Dockerfile               静态站镜像（可选，见第四节备注）
├─ .gitattributes           强制 LF 换行（服务器是 Linux，别让 CRLF 漏进去）
└─ .gitignore
```

**技术形态：零构建依赖的纯静态站。** 所有资源都用相对路径引用，因此**既能部署在域名根目录，也能放在子路径（如 `/club/`）下**。

---

## 二、本地预览

```bash
# 任选一种（都要在仓库根目录执行）
python -m http.server 8777 --directory v3
npx serve v3 -l 8777
```

浏览器打开 http://localhost:8777/login.html

**演示账号**：用户名 `demo`，口令 `xw2026`，身份是管理员。

> 该账号由 `v3/assets/auth.js` 顶部的 **`DEMO_FORCE`** 控制：
> `true` = 任何地址都能用（**当前值**，线上也能用「一键进入」）；
> `false` = 只在本地地址启用（`localhost` / `127.0.0.1` / `file://`），公网访问时自动失效、
> 登录页上的相关入口也会被摘掉。

---

## 三、重新生成站点

页面的文案、成员、作品、岗位等数据都写在 `build_v3.py` 顶部的数据区（`WORKS` / `MEMBERS` / `ACTIVITIES` / `JOBS`），改完重跑即可全量重生成 `v3/`：

```bash
python build_v3.py
```

`build_v3.py` 顶部有两个开关：

```python
SITE_GATE = True   # True = 全站门禁；False = 只锁「成员专区」area.html
```

> **改文案请改生成器，不要直接改 `v3/*.html`** —— 重跑会全部覆盖。
> 例外：`v3/assets/` 下的 css / js 是手写的静态资源，不由生成器产出，直接改即可。

---

## 四、部署到阿里云 ECS（Docker 方式 · 推荐 · 已实测）

适合服务器上**已经装了 Docker**的情况。好处是不用在宿主机装任何东西、不碰系统配置、
`--restart always` 开机自启，而且**把仓库目录直接挂进容器**，以后更新只需一条 `git pull`。

### 0. 前置

| 项 | 说明 |
|---|---|
| 实例 | 阿里云 ECS，1 核 1G 起足够（静态站不吃资源） |
| 系统 | Ubuntu 22.04 已实测通过 |
| 安全组 | 入方向放行 **22（SSH）** + **你要用的那个端口** |
| 域名 | 不需要。**用「IP + 端口」访问完全不涉及备案** |

**先挑一个没被占用的端口**（示例用 `8085`）：

```bash
ss -lntp        # 看 8085 有没有人监听；被占了就换一个
```

### 1. 安全组放行端口

ECS 控制台 → 实例 → 安全组 → 配置规则 → **入方向** → 手动添加：

| 项 | 填 |
|---|---|
| 协议类型 | 自定义 TCP |
| 端口范围 | `8085/8085` |
| 授权对象 | `0.0.0.0/0` |

**不加这条，服务器本机能访问、外面永远连不上。**

### 2. 拉代码

```bash
apt install -y git        # 没有才需要
git clone https://github.com/ikun1111111111/society.git /opt/xiangwang
```

> 私有仓库改用带 token 的地址：
> `https://<用户名>:<PersonalAccessToken>@github.com/ikun1111111111/society.git`

### 3. 起容器

```bash
docker run -d --name xiangwang-site --restart always \
  -p 8085:80 \
  -v /opt/xiangwang/v3:/usr/share/nginx/html:ro \
  nginx:alpine
```

关键点：**挂载的是仓库里的 `v3/` 目录，不是打包进镜像**。所以改文件立刻生效，不用重建容器。

### 4. 验证

```bash
docker ps --filter name=xiangwang-site          # 状态应为 Up
curl -I http://127.0.0.1:8085/                  # 必须返回 HTTP/1.1 200 OK
systemctl is-enabled docker                     # 确认开机自启，否则重启后站点不会自己起来
```

然后浏览器访问 `http://<服务器公网IP>:8085/login.html`。

> **如果 `curl` 返回 403 Forbidden**：说明挂载点里是空的 —— 检查 `/opt/xiangwang/v3/` 里有没有 `index.html`。
> Docker 在 bind mount 的路径不存在时会**静默建一个空目录**，把镜像自带的首页盖掉，于是 403。
> 补上 `git clone` 即可，不用重启容器。

### 5. 以后更新 —— 只有一条命令

```bash
cd /opt/xiangwang && git pull
```

挂载是实时的，文件一更新网站就是新的。**不用重建容器、不用 reload。**

> 配好第九节的自动部署之后，这一步连手动都不用做了：推送 `main` 就会自动拉取。

### 6. 常用运维

```bash
docker logs xiangwang-site --tail 50     # 看日志
docker restart xiangwang-site            # 重启
docker rm -f xiangwang-site              # 删掉（不影响别的容器）
```

> **`Dockerfile` 那套 `docker build` 的写法本项目暂时不用**：构建镜像会把静态文件固化进镜像，
> 每次改文案都要重新 build + 重建容器，比挂载目录麻烦。留着备查而已。

---

## 五、部署到阿里云 ECS（宿主机直装 Nginx）

服务器上**没有 Docker**、或者本来就用 Nginx 托管别的站时用这条。

```bash
# 1. 装环境（Ubuntu）
apt update && apt install -y nginx git

# 2. 拉代码
git clone https://github.com/ikun1111111111/society.git /opt/society

# 3. 静态站放到网站目录
mkdir -p /var/www/xiangwang
cp -r /opt/society/v3/. /var/www/xiangwang/
chown -R www-data:www-data /var/www/xiangwang     # CentOS/阿里云 Linux 用 nginx，并补一条 restorecon

# 4. 配 Nginx
cp /opt/society/deploy/nginx.conf /etc/nginx/conf.d/xiangwang.conf
nginx -t && systemctl reload nginx
```

`deploy/nginx.conf` 里 `listen 80;`、`server_name _;`、`root /var/www/xiangwang;` 按需改：

- **这台机器上还有别的站** → 把 `server_name _;` 改成真实域名。
  `_` 是「兜底站点」，会接住所有没匹配上的请求；**一台机器上只能有一个兜底，多了会互相覆盖。**
- **只想挂在子路径**（`http://IP/club/`）→ 别单独写 server，把这段加进已有的 80 端口 server 里：

```nginx
location ^~ /club/ { alias /var/www/xiangwang/; index index.html; }
location = /club { return 301 /club/; }
```

（本站在子路径下能正常工作：所有跳转都是相对路径，`next` 回跳参数也只接受裸文件名。）

**常见坑**：Ubuntu 上 `/etc/nginx/sites-enabled/default` 会抢在前面，需要 `rm -f /etc/nginx/sites-enabled/default`；
改任何配置前先 `nginx -t`，语法错时 `reload` 会拒绝并保留旧配置继续跑；**用 `reload` 不用 `restart`**（restart 会瞬断所有站）。

---

## 六、部署到阿里云 OSS（无服务器，最便宜）

1. OSS 控制台建 Bucket，**读写权限设为公共读**。
2. 基础设置 → 静态页面：默认首页 `index.html`，子目录首页 `index.html`；**错误文档填 `index.html`**（多页结构，避免空白 404）。
3. 上传 `v3/` 全部文件到 Bucket 根目录（保持 `assets/` 层级）。
4. 用 Bucket 绑定的外网域名访问。

**注意**：OSS 静态托管**没法给目录做访问控制**，`auth.js` 的门禁在浏览器里跑，别人直接访问 `member-*.html` 的 URL 就能看。见下节。

---

## 七、⚠️ 上线安全说明（请认真读）

### 1. 预置测试账号

`v3/assets/auth.js` 里内置了一个 `demo` 管理员账号（口令 `xw2026`），
由顶部的 **`DEMO_FORCE`** 开关控制生效范围：

- **`true`（当前值）**：任何地址都能用，公网访问时登录页有「一键进入」按钮
- `false`：只在 `localhost` / `127.0.0.1` / `file://` 下可用，公网自动失效并摘掉入口

⚠️ **口令写死在源码里，而仓库是公开的，所以谁都能看到。**
需要知道的是：本仓库里本来就有**可无限次使用的管理员邀请码**（`XW2026-DEMO`、`XW2026-ADMIN`），
所以公开这个口令并不额外增加多少风险。想收紧就把 `DEMO_FORCE` 改成 `false` 重新部署。

### 2. 但它仍然不是「安全」

`v3/assets/auth.js` 是**纯前端准入**：邀请码表、账号表、会话全部存在浏览器 `localStorage` 里。
**这类前端门禁拦不住真正想进来的人。** 原因：

- 邀请码表明文写在 `auth.js` 里 → 打开 F12 就能看到全部邀请码（包括 `XW2026-ADMIN` 这种管理员码）；
- 手写一条 `localStorage` 记录就能伪造管理员会话，无需任何口令；
- 直接请求 `member-xxx.html` 等 URL 就能绕过页面门禁。

**结论：它适合「演示」和「让入口看起来正规」，不适合存放任何真实敏感信息**
（学号、手机号、成绩、内部文档、密钥等一律不要放）。

### 3. 真要拦住人，就得有后端

把三个接口搬到服务端，邀请码和账号落库：

```
POST /api/register  { code, name, u, pw }   → 后端校验邀请码，签发 token
POST /api/login     { u, pw }               → 校验口令，返回 token
GET  /api/me                                → 校验 token，未登录返回 401
```

`auth.js` 头部的注释里已写清迁移思路：把前端的 `checkCode() / register() / login()` 换成 `fetch` 调用，
其余页面逻辑基本不用动。后端可用 Node（Express / Fastify）或 Python（FastAPI），
数据落 SQLite / RDS，再让 Nginx 或容器反代 `/api` 到本机端口。

---

## 八、常见问题（含实际踩过的坑）

| 现象 | 原因 / 解法 |
|---|---|
| 浏览器报 `HTTP ERROR 502`，页面是 Chrome 自己的错误模板 | **多半是你本机代理（clash 等）返回的**，不是服务器问题。判据：代理报错会显示 Chrome 自己的错误页；源站的 502 会显示源站自己的正文。关掉系统代理，或本机 `curl.exe -I --noproxy "*" http://<IP>:<端口>/` 绕过代理直连验证 |
| 访问一直转圈、最后超时 | 安全组没放行该端口 |
| `403 Forbidden`，但 `Server: nginx` 有响应 | 挂载点/网站根目录里是空的（没 `git clone`，或只传了 HTML 没传 `assets/`） |
| `git clone` 报 `destination path already exists and is not an empty directory` | 目标目录被 Docker 之类的程序抢先建了个空目录。换个路径克隆，或确认目录内容为空后 `rmdir` 掉（`rmdir` 只删空目录，非空会拒绝，比 `rm -rf` 安全） |
| 页面能开但样式全丢 | 只传了 HTML 没传 `assets/`，或 `root` 指到了上一层 |
| 一直跳回登录页 | 浏览器禁用了 localStorage（无痕模式），或换了访问地址导致旧会话不匹配（会话按「协议+域名+端口」隔离） |
| 文件名/内容出现奇怪的 `^M` | 换行被转成了 CRLF。本仓库 `.gitattributes` 已设 `* text=auto eol=lf`，别把该文件删掉 |
| 服务器上 `git clone` 卡住 | 服务器访问 GitHub 慢，配置代理或用 Gitee 镜像中转 |

---

## 九、自动部署

> ### ⚠️ 先看这里：本项目**实际启用**的是第 5 小节的方案
>
> 下面第 1~4 小节（GitHub Actions 推送即上线）**目前是关闭状态**，保留作备用。
> 原因是硬伤：**这台服务器直连 `github.com` 是 TCP 层超时**
> （实测 `Failed to connect to github.com port 443 after 129843 ms: Connection timed out`），
> 所以工作流里"在服务器上 `git pull`"这一步必然失败，配 HTTP/1.1 之类参数也救不了。
>
> **实际在用的方案 = 第 5 小节：服务器定时轮询国内镜像。**
> 一键启用：`bash /opt/xiangwang/deploy/setup-autodeploy.sh`
>
> 工作流文件的 `push` 触发已注释掉，避免每次推送都跑一次、失败后发邮件打扰。
> 想恢复：解开 `push` 注释，并先解决服务器到 GitHub 的网络问题。

### （备用方案一）GitHub Actions · 推送即上线

推到 `main` 后，GitHub 会自动 SSH 进服务器执行 `git pull`，站点随即更新。
工作流在 `.github/workflows/deploy.yml`，一共三步：装载密钥 → 服务器上 `git pull` → 从公网 `curl` 探测站点。

### 1. 在本地准备一把专用部署密钥

**不要复用你平时登录用的私钥** —— 单独生成一把，将来要作废直接删掉就行。

```bash
# ① 在你自己的电脑上生成（问 passphrase 就直接回车，别设密码，否则 Actions 用不了）
ssh-keygen -t ed25519 -f ~/.ssh/deploy_xiangwang -N "" -C "github-actions-deploy"

# ② 把公钥装到服务器上（推荐这条，一条命令搞定，不用手动复制粘贴）
ssh-copy-id -i ~/.ssh/deploy_xiangwang.pub root@<服务器IP>

# ③ 打印私钥全文，第 2 步要粘进 GitHub
cat ~/.ssh/deploy_xiangwang
```

> **没有 `ssh-copy-id`（Windows 原生 PowerShell 可能没有）时**，用下面这条手动方式 ——
> 注意把 `<公钥>` 换成 `cat ~/.ssh/deploy_xiangwang.pub` 输出的那一整行，
> **不要把尖括号或说明文字一起粘进去**，否则会往授权文件里写进一行垃圾：
>
> ```bash
> # 在服务器上执行
> echo '<公钥>' >> ~/.ssh/authorized_keys
> tail -1 ~/.ssh/authorized_keys | cut -c1-40     # 应显示 ssh-ed25519 AAAA...
> ```
>
> **更省事的替代**：把 `~/.ssh/deploy_xiangwang.pub` 整个文件用文本编辑器打开，复制里面那一行，
> 再用 `nano ~/.ssh/authorized_keys` 粘贴到末尾保存 —— 这样不会把提示文字误当命令执行。

### 2. 在 GitHub 仓库里加一条 Secret

仓库 → **Settings → Secrets and variables → Actions → New repository secret**：

| Name | Value |
|---|---|
| `SSH_PRIVATE_KEY` | 上一步复制的**私钥全文**（要含 `-----BEGIN…` 和 `-----END…` 两行） |

**只需要这一条**（那个按钮点一次加一条，加一条就够了）。
服务器 IP、SSH 用户名、端口、站点端口都直接写在 `.github/workflows/deploy.yml` 顶部的 `env:` 里，
换服务器改那一段即可 —— 公网 IP 本身谁都能扫到、`root` 也是默认用户名，写进文件能省掉两次配置。

> 如果你**不希望服务器 IP 出现在公开仓库**里，就在 Secrets 里再加一条 `SSH_HOST`，
> 然后把工作流 `env:` 里的 `DEPLOY_HOST: 47.99.180.48` 改成 `DEPLOY_HOST: ${{ secrets.SSH_HOST }}`。

### 3. 验证

随便改点东西 push 到 `main`，然后看仓库的 **Actions** 标签：
三步全绿就算成功。第三步会从 GitHub 的机器上真实访问一次
`http://<IP>:<WEB_PORT>/login.html`，返回 200 才通过 —— 所以它验证的是"网站真的能打开"，不是"命令跑完了"。

### 4.（可选但推荐）把密钥权限收紧到只能干这一件事

在服务器 `~/.ssh/authorized_keys` 里，把部署公钥那一行**改成**下面这样（前面加一段限制）：

```
command="cd /opt/xiangwang && git pull --ff-only",no-pty,no-port-forwarding,no-agent-forwarding,no-X11-forwarding ssh-ed25519 AAAA...你的公钥... github-actions-deploy
```

这样即使私钥泄露，对方也只能触发一次 `git pull`，拿不到 shell、也不能转发端口。

### 5. 本项目的实际方案：服务器定时轮询 + 国内镜像（推荐）

上面 1~4 步要开 GitHub 网页、配密钥、点按钮。本项目**没有走那条路**，原因有二：

1. 配 GitHub Secret 那套网页操作对非技术成员门槛偏高，容易卡住；
2. 更关键的——**这台服务器直连 `github.com` 是 TCP 层超时**
   （实测 `Failed to connect to github.com port 443 after 129843 ms: Connection timed out`），
   所以任何"服务器自己 `git pull` GitHub"的方案都跑不通，调 HTTP/1.1 之类的参数也没用。

因此改为：**服务器依次尝试 `deploy/mirrors.txt` 里的国内镜像**。

一键脚本（在服务器上执行）：

```bash
bash /opt/xiangwang/deploy/setup-autodeploy.sh
```

脚本做四件事：

1. 逐个探测 `deploy/mirrors.txt` 里的镜像，把**第一个能用的**设为本仓库的 `origin`
   （每个探测都带 `timeout 30`，不会再出现卡两分钟的情况）
2. 装一条定时任务 `*/5 * * * * /opt/xiangwang/deploy/autopull.sh`
   （可重复执行，不会产生重复条目；也不会动你原有的其它 cron 条目）
3. **立刻拉取一次并当场汇报结果**，不用等 5 分钟才知道通不通
4. 清理 `~/.ssh/authorized_keys` 里遗留的垃圾行和已废弃的部署公钥（先备份）

`deploy/autopull.sh` 是 cron 真正调用的脚本：

- 按 `mirrors.txt` 顺序逐个尝试 `git fetch`，谁先通用谁；全部失败才写日志
- 成功后 `git reset --hard FETCH_HEAD`，让部署目录与仓库**严格一致**
  （本目录是纯部署目标、不放手工修改的文件，所以这样安全）
- **成功静默，失败才追加日志** `/var/log/xiangwang-autodeploy.log`（超 1MB 自动只留最后 200 行）
- 每次运行都刷新心跳文件 `/var/log/xiangwang-autodeploy.lastrun`，
  看它的时间戳就知道定时任务有没有在跑
- 每个 fetch 都带 `timeout 90`，避免网络僵住时卡死

手工跑一次看过程（会打印试了哪些镜像、成功没有）：

```bash
bash /opt/xiangwang/deploy/autopull.sh -v
```

想改成每分钟拉一次，编辑 `setup-autodeploy.sh` 顶部的 `INTERVAL="*"` 后重跑即可。

> ⚠️ **关于镜像的取舍**：这些是第三方代理，只解决"连不上"的问题 ——
> 它们能看到、也能改写传输内容。本项目是公开仓库、内容为社团官网，风险可接受；
> 但若在意，正路是**用 Gitee（码云）做国内中转**：在 Gitee 导入本仓库，
> 然后把 `mirrors.txt` 换成 Gitee 地址即可。以后要长期稳定运行，建议换过去。

> **提示**：手工写 crontab 时务必确认 `*/5` 与后面的 `*` **之间有一个空格**。
> 少一个空格写成 `*/5* * * *`，cron 会认不出来、静默不执行
> （本项目就踩过这个坑）。脚本用 `printf` 生成该行，就是为了避开它。

> 如果想改回 GitHub Actions（方案一），前提是**先把服务器到 GitHub 的网络打通**，
> 否则工作流里那步 `git pull` 一样会失败。

---

## 十、掩盖部署（伪装站 + 隐秘入口）

> 面向的场景：站点挂在公网 IP 上，扫描器和好奇的人会直接摸到 `/login.html`。
> 目的不是"加固"，而是**让陌生人根本不觉得这里有东西值得动手**。

### 做完之后长什么样

| 访问路径 | 结果 |
|---|---|
| `http://<IP>:8085/` | 一个平平无奇的个人笔记站（`mask/`，伪造的） |
| `http://<IP>:8085/login.html` | 还是那个笔记站，够不到真实站 |
| `http://<IP>:8085/<密钥>/` | 真实社团站 |
| `http://<IP>:8085/<密钥>/login.html` | 真实登录页 |

「密钥」是一串 8 位随机字符（例如 `k7m2p9qv`，字符集刻意剔掉 `0`/`O`/`1`/`l`/`I`，方便口述和手打），
**只存在服务器上**（`/etc/xiangwang/mask-secret`），不在仓库里、不在日志里。
32 个字符取 8 位 ≈ 1.1 万亿种组合，字典猜不中、穷举也不现实。
所以即使有人看了这个公开仓库，也猜不到入口在哪。

想自己指定一个：`bash deploy/setup-mask.sh -s <你想要的>`（至少 6 位，脚本会拦常用词）。
想换一把：`bash deploy/setup-mask.sh -r`。

### 组成

| 文件 | 作用 |
|---|---|
| `mask/` | 伪装站。刻意做得很朴素——零脚本、零外链、不出现「登录」「社团」字样 |
| `deploy/container.conf` | 容器内 Nginx 配置：抹掉版本号、关目录列表、拦点文件、**猜错的路径一律返回伪装首页（200）** |
| `deploy/publish.sh` | 组装对外目录 `/var/www/xw-pub`：`mask/` 铺根，`v3/` 铺进 `<密钥>/` |
| `deploy/setup-mask.sh` | 服务器一键安装：生成密钥、组装、重建容器、五项自检 |

`publish.sh` 必须是**原地增量同步**（rsync）——`/var/www/xw-pub` 是容器的 bind mount，
整个目录换掉等于换了 inode，容器会继续指向旧目录，网站立刻 404。

容器挂载由 `v3/` 改成组装出来的 `/var/www/xw-pub`：

```bash
docker run -d --name xiangwang-site --restart always \
  -p 8085:80 \
  -v /var/www/xw-pub:/usr/share/nginx/html:ro \
  -v /opt/xiangwang/deploy/container.conf:/etc/nginx/conf.d/default.conf:ro \
  nginx:alpine
```

### 部署

```bash
# 本地：提交推送（注意 mask/ 和 deploy/ 必须一起提交，服务器要靠它们组装）
git add mask deploy && git commit -m "feat(mask): 伪装站 + 隐秘入口" && git push

# 服务器：先更新代码，再一键安装
cd /opt/xiangwang && bash deploy/autopull.sh -v
bash /opt/xiangwang/deploy/setup-mask.sh
```

`setup-mask.sh` 会自检五项——根路径是不是伪装页、有没有漏出「象罔」、旧 `/login.html` 还能不能进真实站、
响应头还泄不泄露 nginx 版本号、`.git` 有没有被挡住——全过才提示你可以把链接发出去。
退回旧状态：`bash /etc/xiangwang/rollback.sh`。

### 维护

- 换密钥：`bash /opt/xiangwang/deploy/setup-mask.sh -r`（旧链接立即失效，要重新发给成员）
- 忘了密钥：`cat /etc/xiangwang/entry-path.txt`
- 以后推代码照旧。`autopull.sh` 末尾已接上 `publish.sh`，每 5 分钟自动拉取并重铺对外目录

### 端口不对外（推荐）

默认情况下站点容器**只绑 `127.0.0.1:8085`**，不对公网开放：

```bash
# 新容器用 -p 127.0.0.1:8085:80，而不是 -p 8085:80
docker inspect -f '{{json .HostConfig.PortBindings}}' xiangwang-site
```

效果：`47.99.180.48:8085` 从外网**连接被拒**，扫描器连"这里有个网站"都发现不了。
公网唯一入口是 Cloudflare 隧道。**建议顺手把阿里云安全组里那条 8085 入方向规则删掉**（双保险，只留 22 给 SSH）。

> ⚠️ 代价：隧道挂了 = 站点从外网消失，得 SSH 上服务器救。图省心可加 `--public` 恢复端口对外：
> `bash deploy/setup-mask.sh --public`

### （可选）Cloudflare HTTPS 入口

站点原本只有 `http://IP:8085`。想多一个免域名、免备案的 HTTPS 地址，用 Cloudflare 快速隧道：

```bash
bash /opt/xiangwang/deploy/setup-tunnel.sh          # 已建过就直接报当前地址
bash /opt/xiangwang/deploy/setup-tunnel.sh -f       # 重建（会换新地址）
```

它跑一个 `cloudflare/cloudflared` 容器指向 `127.0.0.1:8085`，因此掩盖层在 HTTPS 上同样成立：

| 访问 | 结果 |
|---|---|
| `https://<随机域名>.trycloudflare.com/` | 伪装站 |
| `https://<随机域名>.trycloudflare.com/<密钥>/` | 真实站 |

**三个必须知道的限制**：

1. **地址不固定。** 每次 cloudflared 重启（服务器重启、容器重启、隧道重连）都会换一个新的随机域名。查当前地址：
   `docker logs xw-tunnel 2>&1 | grep -oE 'https://[a-z0-9-]*\.trycloudflare\.com' | tail -1`
   想要固定地址只能上「命名隧道 + 自己的域名」，需要 Cloudflare 账号和一个域名。
2. **它是公开地址**，比 `IP:端口` 更好记也更好转发——转发一次，掩盖层就白做了一半。
3. **登录态不互通。** 浏览器按「协议+域名+端口」隔离 `localStorage`，在 `IP:8085` 登录过的人，走 HTTPS 地址要再登一次。

> 隧道**不要**直接指向 `/<密钥>/`，那等于把 HTTPS 地址本身变成真实站的大门。

### ⚠️ 这层掩盖挡不住什么

它挡的是**扫描器、爬虫、撞库脚本和好奇的人**。挡不住：

1. **看过这个仓库的人。** 站点正文和 `v3/assets/auth.js` 里的邀请码表都在公开仓库里，
   管理员码 `XW2026-ADMIN` / `XW2026-DEMO` 就在里面。拿到密钥链接 ≈ 拿到管理员码。
2. **把链接转发出去的人。** 密钥链接一旦贴到公开群里，这层掩盖等于没有。
3. **纯前端门禁本身。** 打开 F12 手写一条 `localStorage` 就能伪造管理员会话。

结论不变：**别把学号、手机号、成绩、内部文档放上去。**
真要拦住人，见第七节第 3 条——把校验搬到后端。

---

## 十一、许可

社团内部项目，未开源授权，请勿外传。
