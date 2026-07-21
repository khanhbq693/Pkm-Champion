# -*- coding: utf-8 -*-
"""Lấy usage data thật của Pokemon Champions Reg M-B S3 từ Pikalytics.
Nguồn: https://www.pikalytics.com/pokedex/battledataregmbs3/<name>
robots.txt của họ cho phép crawl (và mời riêng AI bot vào /ai/).
Có nghỉ giữa các request để không dội tải.
"""
import io, re, json, time, sys
import urllib.request

FMT = "battledataregmbs3"
UA = "ChampionsCoVan/1.0 (personal team-builder tool; contact via github.com/khanhbq693)"

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.read().decode("utf-8", "replace")

def flat(h):
    return re.sub(r"\s+", " ", h.replace("\n", " "))

def block(html, wid):
    """Cắt khối theo id=... cho tới wrapper kế tiếp."""
    m = re.search(r'id="%s"(.*?)(?=id="[a-z_]*wrapper")' % re.escape(wid), html, re.S)
    return m.group(1) if m else ""

# moves/abilities/natures dùng class ...-text-offset, còn items dùng ...-text (không hậu tố).
# `">` ngay sau tên class để không dính nhầm ...-text-muted (ô hiện hệ của chiêu).
ENTRY = re.compile(
    r'pokedex-inline-text(?:-offset)?">([^<]*)</div>.*?pokedex-inline-right">([\d.]+)%</div>', re.S)

def pairs(html, wid):
    """[(tên, %), ...] theo thứ tự xuất hiện = thứ tự usage giảm dần."""
    out = []
    for name, pct in ENTRY.findall(block(html, wid)):
        name = name.strip()
        if name:
            out.append((name, float(pct)))
    return out

SPREAD_ROW = re.compile(
    r'pokedex-move-entry-new">\s*<div class="pokedex-inline-text-offset">\s*</div>\s*'
    r'((?:<div class="pokedex-inline-text">[\d]+/?</div>\s*){6})'
    r'.*?pokedex-inline-right">([\d.]+)%</div>', re.S)

def spreads(html):
    """[([hp,atk,def,spa,spd,spe], %), ...]"""
    out = []
    for cells, pct in SPREAD_ROW.findall(block(html, "dex_spreads_wrapper")):
        nums = [int(x) for x in re.findall(r'">(\d+)/?</div>', cells)]
        if len(nums) == 6:
            out.append((nums, float(pct)))
    return out

def scrape(name):
    html = flat(get("https://www.pikalytics.com/pokedex/%s/%s" % (FMT, name)))
    return {
        "moves":     pairs(html, "moves_wrapper"),
        "abilities": pairs(html, "abilities_wrapper"),
        "items":     pairs(html, "items_wrapper"),
        "natures":   pairs(html, "dex_natures_wrapper"),
        "spreads":   spreads(html),
    }

def species_list():
    """Danh sách loài của format, lấy thẳng từ index -> không cần file kèm."""
    idx = get("https://www.pikalytics.com/ai/pokedex/%s" % FMT)
    seen, out = set(), []
    for n in re.findall(r"/ai/pokedex/%s/([A-Za-z0-9-]+)" % FMT, idx):
        if n not in seen:
            seen.add(n); out.append(n)
    return out

if __name__ == "__main__":
    names = species_list()
    print("Index co %d loai\n" % len(names))
    if len(sys.argv) > 1:
        names = names[:int(sys.argv[1])]
    data, fails = {}, []
    for i, n in enumerate(names, 1):
        try:
            d = scrape(n)
            if not d["moves"] and not d["spreads"]:
                fails.append(n + "(rong)")
            else:
                data[n] = d
            print("%2d/%d %-18s moves=%-2d abil=%d item=%-2d nat=%-2d spread=%d"
                  % (i, len(names), n, len(d["moves"]), len(d["abilities"]),
                     len(d["items"]), len(d["natures"]), len(d["spreads"])))
        except Exception as e:
            fails.append("%s(%s)" % (n, e))
            print("%2d/%d %-18s LOI: %s" % (i, len(names), n, e))
        time.sleep(0.7)   # lịch sự với server
    io.open("raw.json", "w", encoding="utf-8").write(
        json.dumps(data, ensure_ascii=False, indent=1))
    print("\nXong: %d loai. Loi: %s" % (len(data), fails or "khong"))
