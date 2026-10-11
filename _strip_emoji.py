"""从 build_v3.py 模板层移除所有装饰性 emoji 输出。
保留数据字段（em/ic 不删），只断开模板输出，功能符号（→ ☰ ✓ ↵ ⚿）不动。"""
import io

P = "build_v3.py"
s = io.open(P, encoding="utf-8").read()
orig = s

repls = [
    # 1+2. 作品卡 cover 的 emoji（首页 625 / projects 页 780，字符串相同，全替换）
    ('<div class="cover {x[\'cv\']}"><span class="st">{esc(x[\'status\'])}</span><span class="em">{x[\'em\']}</span></div>',
     '<div class="cover {x[\'cv\']}"><span class="st">{esc(x[\'status\'])}</span></div>'),
    # 3. 岗位卡 cover emoji
    ('<div class="cover {y[\'cv\']}" style="height:96px"><span class="em" style="font-size:34px">{y[\'em\']}</span></div>',
     '<div class="cover {y[\'cv\']}" style="height:96px"></div>'),
    # 4. 作品详情页封面 emoji
    ('cover = \'<div class="d-cover %s"><span class="em">%s</span></div>\' % (x["cv"], x["em"])',
     'cover = \'<div class="d-cover %s"></div>\' % x["cv"]'),
    # 5. 动态 photos 占位 emoji
    ('\'<div class="ph {cv}"><span>{em}</span><span class="cap">{esc(cap)}</span></div>\'',
     '\'<div class="ph {cv}"><span class="cap">{esc(cap)}</span></div>\''),
    # 6. 动态详情封面 emoji
    ('<div class="d-cover {a[\'cv\']}"><span class="em">{a[\'em\']}</span></div>',
     '<div class="d-cover {a[\'cv\']}"></div>'),
    # 7. 岗位详情封面 💼
    ('<div class="d-cover cv2"><span class="em">💼</span></div>',
     '<div class="d-cover cv2"></div>'),
    # 8. 方向区 bento 图标（647：动态拼装，模板含 %s 占位）
    ('\'<div class="bt %s rv"><span class="ic">%s</span><h3>%s</h3><p>%s</p><span class="no">%s</span></div>\'',
     '\'<div class="bt %s rv"><h3>%s</h3><p>%s</p><span class="no">%s</span></div>\''),
    # 9. 招新两卡 🎯🎁
    ('<div class="bt rv"><span class="ic">🎯</span><h3>报名要求</h3>',
     '<div class="bt rv"><h3>报名要求</h3>'),
    ('<div class="bt rv"><span class="ic">🎁</span><h3>你将获得</h3>',
     '<div class="bt rv"><h3>你将获得</h3>'),
    # 10. 联系区图标
    ('\'<div class="cc rv"><div class="ic">{e}</div><b>{esc(t)}</b><span>{esc(v)}</span></div>\'',
     '\'<div class="cc rv"><b>{esc(t)}</b><span>{esc(v)}</span></div>\''),
]

done, missed = 0, []
for old, new in repls:
    n = s.count(old)
    if n:
        s = s.replace(old, new)
        done += n
    else:
        missed.append(old[:60])

io.open(P, "w", encoding="utf-8").write(s)
print(f"替换 {done} 处")
if missed:
    print("未匹配（需人工检查）:")
    for m in missed:
        print("  -", m)

# 复查：模板中还剩哪些 emoji 输出（排除 →☰↑✓↵⚿←→✕ 与数据区定义）
import re
left = []
for i, line in enumerate(s.splitlines(), 1):
    if "em=" in line or "ic=" in line or '("📊"' in line:
        continue  # 数据区
    emoji = re.findall(r"[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF]", line)
    # 过滤功能符号
    emoji = [e for e in emoji if e not in "→←↑↓☰✓✕↵●"]
    if emoji:
        left.append((i, "".join(emoji), line.strip()[:70]))
print("模板剩余装饰 emoji:", len(left))
for i, e, t in left:
    print(f"  {i} {e} {t}")
