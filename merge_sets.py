# -*- coding: utf-8 -*-
"""Gộp champ-sets.json vào USAGEDATA — CHỈ các loài chưa có (giữ Pikalytics cho phần trùng).
Đánh dấu nguồn set gợi ý bằng cờ "s":1 (không có % usage, khác Pikalytics)."""
import io, re, json

P = r"d:/2. Pokemon/index.html"
src = io.open(P, encoding="utf-8").read()
sets = json.load(io.open(r"d:/2. Pokemon/champ-sets.json", encoding="utf-8"))

MOVES = set(re.findall(r'"([^"]+)":\{"t":"[A-Za-z]+","c":"(?:phys|spec|stat)"', src))
ITEMS = set(re.findall(r"'([^']+)':\{", re.search(r"const ITEMS=\{(.*?)\n\};", src, re.S).group(1)))
NATURES = set(re.findall(r"(\w+):\['", re.search(r"const NATURES=\{(.*?)\};", src, re.S).group(1)))
DEX = set(re.findall(r'"([^"]+)":\[\["', src))
USA = json.loads(re.search(r"const USAGEDATA=(\{.*?\});", src, re.S).group(1))

STONE = re.compile(r"ite( [XY])?$")
def mega_forme(species, item):
    m = STONE.search(item)
    if not m: return None
    suf = " (Mega%s)" % (m.group(1) or "")
    for base in (species, species.split("-")[0]):
        if base + suf in DEX: return base + suf
    return None

SPK = ["hp","atk","def","spa","spd","spe"]
rep = {"skip_have": [], "skip_junk": [], "no_move": set(), "no_item": [], "no_nat": [], "added": [], "placeholder_spread": [], "no_dex": []}
add = {}

def in_dex(sp):
    for a in (sp, re.sub(r"-(Mega.*)$", r" (\1)", sp),
              re.sub(r"-([A-Za-z-]+)$", lambda m: " (" + m.group(1) + ")", sp)):
        if a in DEX: return True
    return False

for e in sets:
    sp = e["species"]
    moves_ok = [m for m in e.get("moves", []) if m and m in MOVES]
    # rỗng: không chiêu, hoặc không item (None / "")
    if not [m for m in e.get("moves", []) if m] or e.get("item") in ("None", ""):
        rep["skip_junk"].append(sp); continue
    if not in_dex(sp):
        rep["no_dex"].append(sp); continue   # app không có loài này -> bỏ
    # đã có usage (Pikalytics hoặc đã merge trước) -> giữ nguyên, bỏ qua
    if sp in USA:
        rep["skip_have"].append(sp); continue
    for m in e.get("moves", []):
        if m and m not in MOVES: rep["no_move"].add(m)

    ent = {}
    if moves_ok: ent["m"] = moves_ok[:4]
    if e.get("ability") and e["ability"] != "None": ent["a"] = e["ability"]
    evs = e.get("evs", {})
    nat = e.get("nature")
    # Spread rỗng (0 SP toàn bộ, thường kèm nature Hardy = template mặc định): BỎ sp & nature,
    # để guessSpread đoán từ base stat. Vẫn giữ chiêu/ability/item.
    if sum(int(v) for v in evs.values()) == 0:
        rep["placeholder_spread"].append(sp)
    else:
        if nat in NATURES: ent["n"] = nat
        elif nat and nat != "Hardy": rep["no_nat"].append("%s:%s" % (sp, nat))
        ent["sp"] = [int(evs.get(k, 0)) for k in SPK]
    it = e.get("item", "")
    mg = mega_forme(sp, it)
    if mg: ent["mg"] = mg
    elif STONE.search(it or ""): pass  # đá Mega nhưng Pokédex không có dạng -> bỏ
    elif it in ITEMS and it != "Nothing": ent["it"] = it
    elif it: rep["no_item"].append("%s:%s" % (sp, it))
    ent["s"] = 1  # cờ: set gợi ý (champ-sets), không phải thống kê usage
    add[sp] = ent
    rep["added"].append(sp)

# gộp vào USAGEDATA, viết lại
merged = dict(USA); merged.update(add)
# giữ thứ tự: Pikalytics trước, set gợi ý sau (đã sort tên)
ordered = {k: USA[k] for k in USA}
for k in sorted(add): ordered[k] = add[k]
newjs = "const USAGEDATA=" + json.dumps(ordered, ensure_ascii=False, separators=(",", ":")) + ";"

m = re.search(r"const USAGEDATA=\{.*?\};", src, re.S)
src2 = src[:m.start()] + newjs + src[m.end():]
io.open(P, "w", encoding="utf-8", newline="").write(src2)

print("Them:", len(rep["added"]), "loai moi | Tong USAGEDATA:", len(ordered))
print("Bo qua (da co):", len(rep["skip_have"]))
print("Bo qua (set rong):", rep["skip_junk"])
print("Bo qua (khong co trong DEX):", rep["no_dex"] or "khong")
print("Spread rong -> dung heuristic (giu chieu/item):", rep["placeholder_spread"] or "khong")
print("Nature app khong co:", rep["no_nat"] or "khong")
print("Item app khong co (de trong):", rep["no_item"])
print("Chieu app khong co:", sorted(rep["no_move"]) or "khong")
megas = [k for k in add if "mg" in add[k]]
print("Tu bat Mega (%d):" % len(megas), ", ".join(sorted(megas)) or "khong")
