"""逐人并排对比：表格原文 vs 生成器字段（以生成器人名为锚点匹配）。"""
import io
import re
import openpyxl
import warnings
warnings.filterwarnings("ignore")

XL = r"C:/Users/lenovo/Desktop/学生信息采集1.xlsx"
PY = r"E:\workbuddy\2026-09-14-20-48-27\club-site\build_v3.py"

# 玉玨表格漏填姓名（此前已确认=饶宇轩）
NICK2NAME = {"玉玨": "饶宇轩"}

wb = openpyxl.load_workbook(XL, data_only=True)
ws = wb.active
rows = list(ws.iter_rows(values_only=True))
xl = {}
for r in rows[2:]:
    if not r or not r[1] or str(r[0] or "").startswith("总计"):
        continue
    nick = str(r[1] or "").strip()
    raw = str(r[2] or "").strip()
    name = NICK2NAME.get(nick)
    if not name:
        # 用生成器人名反查 raw_name
        for cn in ["杨添龙", "孙迦勒", "蔡僮", "陈明睿", "郑子鑫", "蔡泉佑", "朱芫枚",
                   "陈致明", "何泓全", "丁博", "张洪铖", "饶宇轩"]:
            if cn in raw:
                name = cn
                break
    if name:
        xl[name] = {
            "nick": nick, "raw": raw,
            "dir": str(r[3] or "").strip(), "bio": str(r[4] or "").strip(),
            "quote": str(r[5] or "").strip(), "skills": str(r[6] or "").strip(),
            "works": str(r[7] or "").strip(), "why": str(r[9] or "").strip(),
            "advice": str(r[10] or "").strip(), "joined": str(r[12] or "").strip(),
        }
    else:
        print(f"[无法映射] 昵称={nick} raw={raw}")

s = io.open(PY, encoding="utf-8").read()
start = s.index("MEMBERS = [")
end = s.index("\n]\n", start)
block = s[start:end]

# 按人切块
chunks = re.split(r'(?=dict\(id=")', block)
gen = {}
for c in chunks:
    m = re.match(r'dict\(id="([\w-]+)", name="([^"]+)"', c)
    if m:
        gen[m.group(2)] = c

FOCUS = ["饶宇轩", "郑子鑫", "杨添龙", "孙迦勒"]
for name in FOCUS:
    x = xl.get(name)
    g = gen.get(name, "")
    print("=" * 72)
    print(f"■ {name}（昵称 {x['nick']}）")
    print(f"  表格方向: {x['dir']}")
    gd = re.search(r'dir=\[([^\]]*)\]', g)
    print(f"  生成器dir: {gd.group(1) if gd else '—'}")
    print(f"  表格技能: {x['skills'][:80]}")
    gs = re.search(r'skills=\[([^\]]*)\]', g)
    print(f"  生成器skills: {gs.group(1)[:110] if gs else '—'}")
    print(f"  表格做过: {x['works'][:90]}")
    gex = re.findall(r'\("([^"]+)",\s*"([^"]+)"\)', g)
    print(f"  生成器exp: {gex[:3]}")
    qx = x["quote"]
    gq = re.search(r'quote="([^"]*)"', g)
    print(f"  表格一句话: {qx[:60]}")
    print(f"  生成器quote: {gq.group(1)[:60] if gq else '—'}")
    print(f"  表格why/advice: {x['why'][:40]} / {x['advice'][:40]}")
    gqa = re.search(r'qa=\[(.*?)\]\)', g, re.S)
    print(f"  生成器qa: {re.sub(chr(10), ' ', gqa.group(1))[:120] if gqa else '—'}")
