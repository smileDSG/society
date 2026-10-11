# -*- coding: utf-8 -*-
"""git 检出复原后的补丁重放：清理假数据 + 封面实拍图。幂等。"""
import re, glob, io

ROOT = r"E:/workbuddy/2026-09-14-20-48-27/club-site/v3"
EMAIL = "yangtianlong407@gmail.com"
ROOM = "气象谷2号楼201"

def load(p):
    with io.open(p, "r", encoding="utf-8", newline="") as f:
        return f.read()
def save(p, s):
    with io.open(p, "w", encoding="utf-8", newline="") as f:
        f.write(s)

changed = []

# 1) 全站：删导航「2026 秋招进行中」
nav_re = re.compile(r'^[ \t]*<span class="nav-status"><i></i>2026 秋招进行中</span>[ \t]*\r?\n', re.M)
for p in glob.glob(ROOT + "/*.html"):
    s = load(p); s2 = nav_re.sub("", s)
    if s2 != s:
        save(p, s2); changed.append((p.split("/")[-1], "nav"))

# 2) index.html
ip = ROOT + "/index.html"; s = load(ip); o = s
s = re.sub(r'^[ \t]*<div class="hero-stats rv">.*\r?\n', "", s, count=1, flags=re.M)
s = re.sub(r'<div class="quote-grid">.*?</div></div>\r?\n(?=[ \t]*<div class="mem-grid")', "", s, count=1, flags=re.S)
s = s.replace("MEMBERS · 先听听他们说", "MEMBERS · 核心成员")
s = s.replace("<h2>成员，18 种来这儿的理由</h2>", "<h2>先认识这些人</h2>")
s = re.sub(r'^[ \t]*<h2 style="margin:54px 0 6px;font-size:22px">招新时间线</h2>[ \t]*\r?\n', "", s, flags=re.M)
s = re.sub(r'^[ \t]*<ol class="steps rv"><li><p class="t">09\.15.*?</ol>[ \t]*\r?\n', "", s, flags=re.M)
new_contact = ('    <div class="contact-grid">'
    '<div class="cc rv"><div class="ic">📮</div><b>合作邮箱</b><span>' + EMAIL + '</span></div>'
    '<div class="cc rv"><div class="ic">📍</div><b>活动室</b><span>' + ROOM + '</span></div></div>\n')
if '招新 QQ 群' in s:
    s = re.sub(r'^[ \t]*<div class="contact-grid">.*</div>[ \t]*\r?\n', new_contact, s, count=1, flags=re.M)
if s != o:
    save(ip, s); changed.append(("index.html", "clean"))

# 3) job-j1..j4
for p in sorted(glob.glob(ROOT + "/job-j*.html")):
    s = load(p); o = s
    s = re.sub(r'[ \t]*<h2>报名流程</h2>\r?\n[ \t]*<ol class="steps">.*?</ol>\r?\n', "", s, count=1, flags=re.S)
    s = re.sub(r'<a href="index\.html#contact"><span>招新 QQ 群</span><span class="ar">[^<]*</span></a>\r?\n', "", s)
    s = s.replace('<a href="index.html#contact"><span>合作邮箱</span><span class="ar">→</span></a>',
                  '<a href="mailto:' + EMAIL + '"><span>合作邮箱</span><span class="ar">→</span></a>\n        <a href="index.html#contact"><span>活动室</span><span class="ar">' + ROOM + '</span></a>')
    if s != o:
        save(p, s); changed.append((p.split("/")[-1], "job"))

# 4) life-a*.html / area.html
for p in glob.glob(ROOT + "/life-a*.html") + glob.glob(ROOT + "/area.html"):
    s = load(p); o = s
    s = s.replace("工科楼 A-302（占位）", ROOM).replace("工科楼 A-302", ROOM)
    s = s.replace("· A-302</span>", "· " + ROOM + "</span>").replace("全体组会 @ 工科楼 A-302", "全体组会 @ " + ROOM)
    if s != o:
        save(p, s); changed.append((p.split("/")[-1], "room"))

# 5) member-yuyue 假引语（若存在）
p = ROOT + "/member-yuyue.html"
if glob.glob(p):
    s = load(p); o = s
    s = re.sub(r'^[ \t]*<p style="font-size:19px;margin-top:18px;[^>]*>“写完第一个能上线的接口.*?</p>[ \t]*\r?\n', "", s, flags=re.M)
    if s != o:
        save(p, s); changed.append(("member-yuyue.html", "quote"))

# 6) 封面实拍图（index + projects）
IMG = '<img class="cov-img" src="assets/works/{src}" alt="{alt}" loading="lazy">'
covers = [
    ("📚", "w2-01.png", "智眸无界平台实拍：互动课堂界面"),
    ("🔬", "w6-01.png", "ARISAI 科研智能体平台实拍"),
    ("⚖️", "w7-01.png", "法枢 LexHub 平台实拍：合同审查"),
    ("🖥️", "w8-01.png", "AFCP 算力调度网关平台实拍"),
]
for fname in ("index.html", "projects.html"):
    p = ROOT + "/" + fname; s = load(p); o = s
    for emoji, src, alt in covers:
        old = '<span class="em">' + emoji + '</span>'
        if old in s:
            s = s.replace(old, IMG.format(src=src, alt=alt), 1)
    # 用户已删 emoji 的空 cover：按状态行补图
    for st, src, alt in [
        ("已部署运行", "w7-01.png", "法枢 LexHub 平台实拍：合同审查"),
        ("可完整跑通", "w8-01.png", "AFCP 算力调度网关平台实拍"),
    ]:
        empty = '<div class="cover cv3"><span class="st">' + st + '</span></div>'
        if empty in s and src == "w7-01.png":
            s = s.replace(empty, '<div class="cover cv3"><span class="st">' + st + '</span>' + IMG.format(src=src, alt=alt) + '</div>', 1)
        empty1 = '<div class="cover cv1"><span class="st">' + st + '</span></div>'
        if empty1 in s and src == "w8-01.png":
            s = s.replace(empty1, '<div class="cover cv1"><span class="st">' + st + '</span>' + IMG.format(src=src, alt=alt) + '</div>', 1)
    if s != o:
        save(p, s); changed.append((fname, "covers"))

# 7) site.css cov-img 样式
p = ROOT + "/assets/site.css"; s = load(p)
if "cov-img" not in s:
    s += "\n/* ---- 作品卡封面实拍图 ---- */\n.wk .cover img.cov-img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:top;display:block;z-index:1}\n"
    save(p, s); changed.append(("site.css", "cov-img"))

for f, w in changed:
    print("OK", f, "<-", w)

# 校验
bad = []
pat = re.compile("秋招进行中|招新 QQ 群|123-456-789|xiangwang@club\\.edu|工科楼|A-302|招新时间线|hero-stats|quote-grid|18 种")
for p in glob.glob(ROOT + "/*.html"):
    if pat.search(load(p)):
        bad.append(p.split("/")[-1])
print("RESIDUE:", bad if bad else "none")
for f in ("index.html", "projects.html"):
    print(f, "cov-img:", load(ROOT + "/" + f).count("cov-img"))
