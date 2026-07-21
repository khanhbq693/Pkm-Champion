# -*- coding: utf-8 -*-
"""Thay khối USAGEDATA cũ (509 loài, data Smogon gen9 singles - SAI GAME)
bằng data Champions Reg M-B S3 thật từ Pikalytics (50 loài)."""
import io, re

P = r"d:/2. Pokemon/index.html"
src = io.open(P, encoding="utf-8").read()
new = io.open("usagedata.js", encoding="utf-8").read().strip()

banner = (
    "/* USAGEDATA - Pokemon Champions VGC 2026 Reg M-B S3 (ranked ladder), data 2026-05.\n"
    "   Nguon: Pikalytics https://www.pikalytics.com/pokedex/battledataregmbs3\n"
    "   Chi 50 loai cua meta Reg M-B. Loai ngoai danh sach -> usageOf() tra null va\n"
    "   guessSpread() doan tu base stat nhu cu.\n"
    "   Truong: m=4 chieu hay dung | a=ability #1 | n=nature #1 | sp=spread #1 (he SP\n"
    "   cua Champions: hp/atk/def/spa/spd/spe, cap 32) | u=%% cua spread do | it=item #1\n"
    "   (chi khi app biet item va >=20%%) | mg=dang Mega khi item #1 la da Mega.\n"
    "   Cap nhat: chay lai scraper, Pikalytics refresh hang thang. */\n"
)

m = re.search(r"const USAGEDATA=\{.*?\};", src, re.S)
assert m, "khong tim thay USAGEDATA"
old = m.group(0)
src = src[:m.start()] + banner + new + src[m.end():]
io.open(P, "w", encoding="utf-8", newline="").write(src)
print("Da thay: %d bytes -> %d bytes (giam %d)" % (len(old), len(new), len(old) - len(new)))
