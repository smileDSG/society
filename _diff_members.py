"""对比 学生信息采集.xlsx 与 build_v3.py MEMBERS 的字段差异。"""
import io
import re
import openpyxl
import warnings
warnings.filterwarnings("ignore")

XL = r"C:/Users/lenovo/Desktop/学生信息采集.xlsx"
PY = r"E:\workbuddy\2026-09-14-20-48-27\club-site\build_v3.py"

# ---------- 读表格 ----------
wb = openpyxl.load_workbook(XL, data_only=True)
ws = wb.active
rows = list(ws.iter_rows(values_only=True))
hdr = rows[1]
xl = {}
for r in rows[2:]:
    if not r or not r[1] or str(r[0] or "").startswith("总计"):
        continue
    name = str(r[2] or "").strip()
    m = re.match(r"^([\u4e00-\u9fa5]{2,4})", name)
    real = m.group(1) if m else name
    xl[real] = {
        "nick": str(r[1] or "").strip(),
        "raw_name": name,
        "dir": str(r[3] or "").strip(),
        "bio": str(r[4] or "").strip(),
        "quote": str(r[5] or "").strip(),
        "skills": str(r[6] or "").strip(),
        "works": str(r[7] or "").strip(),
        "why": str(r[9] or "").strip(),
        "advice": str(r[10] or "").strip(),
        "joined": str(r[12] or "").strip(),
    }

# ---------- 读生成器 MEMBERS ----------
s = io.open(PY, encoding="utf-8").read()
start = s.index("MEMBERS = [")
end = s.index("\n]\n", start)
block = s[start:end]

gens = {}
for mm in re.finditer(
        r'dict\(id="([\w-]+)", name="([^"]+)".*?quote="([^"]*)",\s*\n\s*bio="([^"]*)"', block, re.S):
    gens[mm.group(2)] = {"id": mm.group(1), "quote": mm.group(3), "bio": mm.group(4)}

print(f"表格 {len(xl)} 人 / 生成器 {len(gens)} 人\n")
print("=" * 70)
print("一、表格中的人在生成器里的状态")
print("=" * 70)
for name, x in xl.items():
    g = gens.get(name)
    if not g:
        print(f"  [缺失] {name}（昵称 {x['nick']}）—— 表格有数据但生成器无此人")
        continue
    # 关键字段粗对比
    diffs = []
    q_x = re.sub(r"\s", "", x["quote"])
    q_g = re.sub(r"\s", "", g["quote"])
    if q_x and q_g and q_x[:10] not in q_g and q_g[:10] not in q_x:
        diffs.append("quote")
    b_x = re.sub(r"\s", "", x["bio"])[:12]
    b_g = re.sub(r"\s", "", g["bio"])
    if b_x and b_x not in b_g:
        diffs.append("bio")
    flag = " ~ " + ",".join(diffs) if diffs else " ✓"
    print(f"  {name:<5}{flag}")

print()
print("=" * 70)
print("二、生成器里没有表格数据的人（仍占位）")
print("=" * 70)
for name, g in gens.items():
    if name not in xl:
        print(f"  [占位] {name} (id={g['id']})")
