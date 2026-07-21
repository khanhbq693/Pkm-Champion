# -*- coding: utf-8 -*-
"""Cap nhat chi so pkm tu paste Showdown (SPs system, cap 32).
Ghi de trung (species) — paste la nguon tin cay hon.
  - champ-sets.json: overwrite theo species (giu id cu) / them moi.
  - index.html USAGEDATA: overwrite entry cua cac species do (dung logic merge_sets.py),
    ke ca entry Pikalytics (s=None) — theo yeu cau ghi de.
Chay:  python update_pkm.py            (dry-run, chi bao cao)
       python update_pkm.py --write    (ghi file)
"""
import io, re, json, sys, uuid, os

ROOT = os.path.dirname(os.path.abspath(__file__))
PASTE = sys.argv[sys.argv.index("--paste")+1] if "--paste" in sys.argv else os.path.join(ROOT, "paste.txt")
IDX = os.path.join(ROOT, "index.html")
CS  = os.path.join(ROOT, "champ-sets.json")
WRITE = "--write" in sys.argv

src = io.open(IDX, encoding="utf-8").read()
MOVES = set(re.findall(r'"([^"]+)":\{"t":"[A-Za-z]+","c":"(?:phys|spec|stat)"', src))
ITEMS = set(re.findall(r"'([^']+)':\{", re.search(r"const ITEMS=\{(.*?)\n\};", src, re.S).group(1)))
NATURES = set(re.findall(r"(\w+):\['", re.search(r"const NATURES=\{(.*?)\};", src, re.S).group(1)))
DEX = set(re.findall(r'"([^"]+)":\[\["', src))
USA = json.loads(re.search(r"const USAGEDATA=(\{.*?\});", src, re.S).group(1))
sets = json.load(io.open(CS, encoding="utf-8"))

def key(s): return re.sub(r"[^a-z0-9]", "", s.lower())
MOVE_BY = {key(m): m for m in MOVES}
SPK = ["hp", "atk", "def", "spa", "spd", "spe"]
SPMAP = {"hp":"hp","atk":"atk","def":"def","spa":"spa","spd":"spd","spe":"spe"}

def norm_species(sp):
    sp = re.sub(r"-Breed$", "", sp)           # Tauros-Paldea-*-Breed -> -*
    return sp

def in_dex(sp):
    for a in (sp, re.sub(r"-(Mega.*)$", r" (\1)", sp),
              re.sub(r"-([A-Za-z-]+)$", lambda m: " (" + m.group(1) + ")", sp)):
        if a in DEX: return True
    return False

# ---- parse paste ----
def parse(text):
    out = []
    for block in re.split(r"\n\s*\n", text.strip()):
        lines = [l.rstrip() for l in block.splitlines() if l.strip()]
        if not lines: continue
        head = lines[0]
        m = re.match(r"^(.*?)\s*@\s*(.*)$", head)
        species, item = (m.group(1).strip(), m.group(2).strip()) if m else (head.strip(), "")
        ability = nature = None; evs = {}; moves = []
        for l in lines[1:]:
            if l.startswith("Ability:"): ability = l.split(":",1)[1].strip()
            elif l.startswith("Level:"): pass
            elif l.startswith("SPs:") or l.startswith("EVs:"):
                for part in l.split(":",1)[1].split("/"):
                    part = part.strip()
                    mm = re.match(r"(\d+)\s+(\w+)", part)
                    if mm:
                        val, stat = int(mm.group(1)), mm.group(2).lower()
                        if stat in SPMAP: evs[SPMAP[stat]] = val
            elif l.endswith("Nature"): nature = l.rsplit(" ",1)[0].strip()
            elif l.startswith("- "): moves.append(l[2:].strip())
        out.append({"species": species, "item": item, "ability": ability,
                    "nature": nature, "evs": evs, "moves": moves})
    return out

parsed = parse(io.open(PASTE, encoding="utf-8").read())

# ---- normalize + report ----
rep = {"bad_move": {}, "bad_item": [], "bad_nat": [], "no_dex": [], "bad_species_norm": []}
def norm_move(mv):
    if not mv: return ""
    k = key(mv)
    return MOVE_BY.get(k, None)

STONE = re.compile(r"ite( [XY])?$")
def mega_forme(species, item):
    m = STONE.search(item or "")
    if not m: return None
    suf = " (Mega%s)" % (m.group(1) or "")
    for base in (species, species.split("-")[0]):
        if base + suf in DEX: return base + suf
    return None

norm = []
for e in parsed:
    sp = norm_species(e["species"])
    if not in_dex(sp): rep["no_dex"].append(sp)
    mvs = []
    for mv in e["moves"]:
        if not mv: continue
        nm = norm_move(mv)
        if nm is None: rep["bad_move"].setdefault(mv, []).append(sp)
        else: mvs.append(nm)
    nat = e["nature"]
    if nat and nat not in NATURES and nat != "Hardy": rep["bad_nat"].append("%s:%s"%(sp,nat))
    it = e["item"]
    if it and not mega_forme(sp, it) and not STONE.search(it) and it not in ITEMS and it != "Nothing":
        rep["bad_item"].append("%s:%s"%(sp,it))
    norm.append({"raw": e, "species": sp, "moves": mvs})

print("=== PASTE:", len(parsed), "mons ===")
print("Khong co trong DEX:", rep["no_dex"] or "khong")
print("Nature la:", rep["bad_nat"] or "khong")
print("Item app khong biet (USAGEDATA se bo it):", rep["bad_item"] or "khong")
print("Chieu khong khop MOVES:")
for mv, sps in rep["bad_move"].items(): print("   ", repr(mv), "->", sps)
if not rep["bad_move"]: print("    khong")

# ---- build updates ----
cs_by_sp = {}
for i, s in enumerate(sets): cs_by_sp.setdefault(s["species"], i)

cs_over, cs_new, usa_over, usa_new = [], [], [], []
for n in norm:
    e = n["raw"]; sp = n["species"]
    evs = {k: int(e["evs"].get(k, 0)) for k in SPK}
    moves4 = (n["moves"] + ["", "", "", ""])[:4]
    # champ-sets entry
    cs_entry = {"species": sp, "item": e["item"], "nature": e["nature"] or "Hardy",
                "ability": e["ability"] or "None", "evs": evs, "moves": moves4}
    if sp in cs_by_sp:
        idx = cs_by_sp[sp]; cs_entry["id"] = sets[idx]["id"]
        sets[idx] = {"id": cs_entry["id"], **{k: cs_entry[k] for k in ("species","item","nature","ability","evs","moves")}}
        cs_over.append(sp)
    else:
        cs_entry = {"id": "cs-" + uuid.uuid4().hex[:12], **cs_entry}
        sets.append(cs_entry); cs_by_sp[sp] = len(sets)-1; cs_new.append(sp)
    # USAGEDATA entry (merge_sets.py logic)
    ent = {}
    if n["moves"]: ent["m"] = n["moves"][:4]
    if e["ability"] and e["ability"] != "None": ent["a"] = e["ability"]
    if sum(evs.values()) != 0:
        if (e["nature"] or "") in NATURES: ent["n"] = e["nature"]
        ent["sp"] = [evs[k] for k in SPK]
    mg = mega_forme(sp, e["item"])
    if mg: ent["mg"] = mg
    elif STONE.search(e["item"] or ""): pass
    elif e["item"] in ITEMS and e["item"] != "Nothing": ent["it"] = e["item"]
    ent["s"] = 1
    (usa_over if sp in USA else usa_new).append(sp)
    USA[sp] = ent

print("\n=== champ-sets.json ===")
print("Ghi de:", len(cs_over), "| Them moi:", len(cs_new), sorted(cs_new))
print("=== USAGEDATA ===")
pika_over = [s for s in usa_over if s in USA]  # all; distinguish by prior flag
print("Ghi de:", len(usa_over), "| Them moi:", len(usa_new), sorted(usa_new))

if not WRITE:
    print("\n(DRY-RUN — them --write de ghi file)")
    sys.exit(0)

# ---- write champ-sets.json ----
io.open(CS, "w", encoding="utf-8", newline="\n").write(json.dumps(sets, ensure_ascii=False, indent=1) + "\n")
# ---- write USAGEDATA (giu banner) ----
newjs = "const USAGEDATA=" + json.dumps(USA, ensure_ascii=False, separators=(",", ":")) + ";"
m = re.search(r"const USAGEDATA=\{.*?\};", src, re.S)
src2 = src[:m.start()] + newjs + src[m.end():]
io.open(IDX, "w", encoding="utf-8", newline="").write(src2)
print("\nDa ghi champ-sets.json va index.html. Tong USAGEDATA:", len(USA))
