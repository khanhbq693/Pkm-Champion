# -*- coding: utf-8 -*-
"""Dua usagedata.js (ladder Pikalytics moi) vao khoi USAGEDATA cua index.html.

MAC DINH LA GOP, KHONG DE. Ly do: tu Dot 14, USAGEDATA khong con la ban chup Pikalytics
nua — no la 226 set curated lay tu paste, va quyet dinh da ghi ro "paste la nguon tin cay
hon". Neu apply.py thay ca khoi nhu ban cu thi 176 loai ngoai top-50 bien mat va 50 loai
con lai bi ladder de len set curated — tuc la lang le dao nguoc quyet dinh do.

Nen ban nay:
  - Loai CHUA co  -> them nguyen entry ladder (co u = %% spread).
  - Loai DA co    -> giu set curated, chi gan co meta=1 (dang trong top-50 ladder) va gan u
                     khi spread curated TRUNG spread top cua ladder (trung thi con so %% moi
                     noi dung ve spread dang hien).
  - Loai rot khoi top-50 -> go co meta.
  - Ghi USAGEMETA (reg / ngay / so loai) de app hien duoc do tuoi cua du lieu.

Chay:  python apply.py              gop (mac dinh)
       python apply.py --overwrite  cho ladder de len set curated cua 50 loai do
"""
import io, re, json, sys, datetime

IDX = r"d:/2. Pokemon/index.html"
FMT = "battledataregmbs3"
REG = "M-B"
OVERWRITE = "--overwrite" in sys.argv

src = io.open(IDX, encoding="utf-8").read()
new = json.loads(re.search(r"const USAGEDATA=(\{.*?\});",
                           io.open("usagedata.js", encoding="utf-8").read(), re.S).group(1))

m_old = re.search(r"const USAGEDATA=(\{.*?\});", src, re.S)
assert m_old, "khong tim thay USAGEDATA trong index.html"
cur = json.loads(m_old.group(1))

added, marked, diverged, unmarked = [], [], [], []

for name, e in new.items():
    if name not in cur:
        cur[name] = dict(e, meta=1)
        added.append(name)
        continue
    if OVERWRITE:
        cur[name] = dict(e, meta=1)
        marked.append(name)
        continue
    old = cur[name]
    old["meta"] = 1
    marked.append(name)
    # % spread chi dung khi spread dang hien CHINH LA spread top cua ladder
    if e.get("sp") and old.get("sp") == e["sp"] and e.get("u"):
        old["u"] = e["u"]
    elif e.get("sp") and old.get("sp") != e.get("sp"):
        diverged.append((name, old.get("sp"), e.get("sp"), e.get("u")))

for name, e in cur.items():
    if name not in new and e.pop("meta", None):
        unmarked.append(name)

meta = {
    "reg": REG, "fmt": FMT,
    "date": datetime.date.today().strftime("%Y-%m"),
    "ladder": len(new), "total": len(cur),
    "src": "Pikalytics (ladder) + champ-sets/paste (set curated)",
}

banner = (
    "/* USAGEDATA - Pokemon Champions VGC 2026 Reg %s, data %s.\n"
    "   2 nguon, phan biet bang co:\n"
    "     meta=1 -> loai dang nam trong top-%d cua ladder Pikalytics (%s)\n"
    "     s=1    -> set curated tu paste (khong phai thong ke usage)\n"
    "     u      -> %%%% tran dung dung spread dang hien (chi gan khi spread trung ladder)\n"
    "   Loai ngoai bang -> usageOf() tra null, guessSpread() doan tu base stat.\n"
    "   Truong: m=4 chieu | a=ability | n=nature | sp=[hp,atk,def,spa,spd,spe] cap 32\n"
    "   | it=item | mg=dang Mega khi item la da Mega.\n"
    "   Cap nhat: python scrape.py && python build.py && python apply.py (xem README-data.md) */\n"
) % (REG, meta["date"], len(new), FMT)

block = (banner
         + "const USAGEMETA=" + json.dumps(meta, ensure_ascii=False, separators=(",", ":")) + ";\n"
         + "const USAGEDATA=" + json.dumps(cur, ensure_ascii=False, separators=(",", ":")) + ";")

# xoa banner + USAGEMETA cu (neu co) ngay truoc khoi, roi thay ca cum
head = src[:m_old.start()]
head = re.sub(r"const USAGEMETA=\{.*?\};\s*$", "", head, flags=re.S)
head = re.sub(r"/\* USAGEDATA[^*]*(?:\*(?!/)[^*]*)*\*/\s*$", "", head, flags=re.S)
src = head + block + src[m_old.end():]
io.open(IDX, "w", encoding="utf-8", newline="").write(src)

print("Che do:", "DE (overwrite)" if OVERWRITE else "GOP (giu set curated)")
print("Them moi          : %d %s" % (len(added), added[:8]))
print("Danh dau meta=1   : %d loai" % len(marked))
print("Go meta (roi top) : %d %s" % (len(unmarked), unmarked[:8]))
print("Tong USAGEDATA    : %d loai" % len(cur))
if diverged:
    print("\nSet curated LECH voi spread top cua ladder (%d loai) — xem lai neu muon theo ladder:" % len(diverged))
    for n, o, w, u in diverged[:15]:
        print("   %-16s curated %-22s ladder %-22s (%s%%)" % (n, str(o), str(w), u))
