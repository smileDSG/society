"""删除 area 页 JS 对象里的 ic 字段（emoji 源头），并重新生成验证。"""
import io
import re
import subprocess
import sys
from pathlib import Path

BASE = Path(r"E:\workbuddy\2026-09-14-20-48-27\club-site")
P = BASE / "build_v3.py"

s = io.open(P, encoding="utf-8").read()
s2, n = re.subn(r"ic: '[^']*', h:", "h:", s)
io.open(P, "w", encoding="utf-8").write(s2)
print(f"删除 ic 字段: {n} 处")

# 重新生成
r = subprocess.run([sys.executable, str(P)], capture_output=True, text=True,
                   cwd=str(BASE))
print(r.stdout.strip()[-60:] or r.stderr.strip()[-200:])

# 残留检查（排除功能符号 →←↑↓☰✓✕↵●⚿）
fun = set("→←↑↓☰✓✕↵●⚿")
bad = {}
for f in (BASE / "v3").glob("*.html"):
    txt = f.read_text(encoding="utf-8", errors="ignore")
    for m in re.finditer(r"[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF]", txt):
        ch = m.group(0)
        if ch in fun:
            continue
        bad.setdefault(ch, set()).add(f.name)
print("残留 emoji:", {k: len(v) for k, v in bad.items()} or "无 ✅")
