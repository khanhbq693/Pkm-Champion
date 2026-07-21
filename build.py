# -*- coding: utf-8 -*-
"""raw.json (Pikalytics, Champions Reg M-B S3) -> khối USAGEDATA mới cho index.html.

Giữ 2 trường cũ (m, a) để code hiện có chạy tiếp, thêm:
  n  = nature phổ biến nhất
  sp = spread phổ biến nhất [hp,atk,def,spa,spd,spe]  (hệ SP của Champions, cap 32)
  u  = % của spread đó
  it = item phổ biến nhất MÀ app biết, và chỉ khi >= NGƯỠNG
  mg = dạng Mega, khi item top là đá Mega (app không mô hình đá Mega bằng ô item
       cho đối thủ — nó có nút MEGA riêng trên card)
"""
import io, re, json

MIN_ITEM_PCT = 20.0   # dưới ngưỡng này coi như không đoán được item -> để trống

raw = json.load(io.open("raw.json", encoding="utf-8"))
src = io.open(r"d:/2. Pokemon/index.html", encoding="utf-8").read()

MOVES = set(re.findall(r'"([^"]+)":\{"t":"[A-Za-z]+","c":"(?:phys|spec|stat)"', src))
# chú ý: KHÔNG dùng ^ + re.M — mỗi dòng có nhiều item, sẽ chỉ bắt được cái đầu dòng.
ITEMS = set(re.findall(r"'([^']+)':\{",
            re.search(r"const ITEMS=\{(.*?)\n\};", src, re.S).group(1)))
NATURES = set(re.findall(r"(\w+):\['", re.search(r"const NATURES=\{(.*?)\};", src, re.S).group(1)))
DEXNAMES = set(re.findall(r'"([^"]+)":\[\["', src))

STONE = re.compile(r"ite( [XY])?$")   # Swampertite, Charizardite Y, Mawilite

def mega_forme(species, item):
    """Đá Mega -> tên dạng Mega trong Pokédex của app, hoặc None."""
    m = STONE.search(item)
    if not m:
        return None
    suffix = " (Mega%s)" % (m.group(1) or "")
    for base in (species, species.split("-")[0]):
        if base + suffix in DEXNAMES:
            return base + suffix
    return None

rep = {"move_skip": set(), "item_low": [], "stone_nodex": [], "nat_skip": set()}
out = {}

for name, d in sorted(raw.items()):
    e = {}

    mv = []
    for n, p in d["moves"]:
        if n in MOVES: mv.append(n)
        else: rep["move_skip"].add(n)
        if len(mv) == 4: break
    if mv: e["m"] = mv

    if d["abilities"]:
        e["a"] = d["abilities"][0][0]

    for n, p in d["natures"]:
        if n in NATURES: e["n"] = n; break
        rep["nat_skip"].add(n)

    # item: chỉ xét cái #1. Là đá Mega -> ghi dạng Mega. Không thì phải app biết + đủ ngưỡng.
    if d["items"]:
        top, pct = d["items"][0]
        mg = mega_forme(name, top)
        if mg:
            e["mg"] = mg
        elif STONE.search(top):
            rep["stone_nodex"].append("%s:%s" % (name, top))
        elif top in ITEMS and pct >= MIN_ITEM_PCT and top != "Nothing":
            e["it"] = top
        else:
            rep["item_low"].append("%s:%s %.1f%%" % (name, top, pct))

    if d["spreads"]:
        e["sp"] = d["spreads"][0][0]
        e["u"] = d["spreads"][0][1]

    out[name] = e

js = "const USAGEDATA=" + json.dumps(out, ensure_ascii=False, separators=(",", ":")) + ";"
io.open("usagedata.js", "w", encoding="utf-8").write(js)

print("Loai: %d | %d bytes" % (len(out), len(js)))
print("Chieu app khong co :", sorted(rep["move_skip"])[:8] or "khong")
print("Nature app khong co:", sorted(rep["nat_skip"]) or "khong")
print("Da Mega thieu Pokedex:", rep["stone_nodex"] or "khong")
print("Item bo (thap/la):", len(rep["item_low"]), rep["item_low"][:5])
print("\nCo dang Mega (%d con):" % sum(1 for v in out.values() if "mg" in v))
for k, v in out.items():
    if "mg" in v: print("   %-16s -> %s" % (k, v["mg"]))
print("\nSwampert:", json.dumps(out["Swampert"], ensure_ascii=False))
print("Garchomp:", json.dumps(out["Garchomp"], ensure_ascii=False))
