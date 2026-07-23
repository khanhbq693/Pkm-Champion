# Cập nhật usage data (Champions Reg M-B)

`USAGEDATA` trong `index.html` gồm **226 loài**, 2 nguồn trộn lại, phân biệt bằng cờ:

| Cờ | Nghĩa |
|---|---|
| `meta:1` | loài đang nằm trong **top-50 ladder** Pikalytics của reg hiện tại |
| `s:1` | set curated lấy từ paste (không phải thống kê usage) |
| `u` | % số trận dùng **đúng spread đang hiển thị** — chỉ gắn khi spread curated trùng spread top của ladder |

`USAGEMETA` ngay trên khối đó ghi reg / tháng / số loài; app hiện nó ở panel **Đối thủ**
và tự chuyển sang cảnh báo vàng khi dữ liệu quá 2 tháng.

## Chạy lại

```bash
python scrape.py      # tải 50 loài của meta -> raw.json  (~40s, nghỉ 0.7s/request)
python build.py       # raw.json -> usagedata.js, in ra thứ app không khớp
python apply.py       # GỘP vào USAGEDATA + ghi USAGEMETA (mặc định KHÔNG đè set curated)
```

Chạy `scrape.py 3` để thử 3 loài trước cho nhanh.

### apply.py: gộp, không đè

Từ Đợt 14, `USAGEDATA` không còn là ảnh chụp Pikalytics — nó là 226 set curated từ paste,
với quyết định đã ghi rõ *"paste là nguồn tin cậy hơn"*. Nếu `apply.py` thay cả khối như
bản cũ thì 176 loài ngoài top-50 biến mất, và 50 loài còn lại bị ladder đè lên set curated
— tức là lặng lẽ đảo ngược quyết định đó. Nên hành vi mặc định là:

- loài **chưa có** → thêm nguyên entry ladder (kèm `u`);
- loài **đã có** → giữ set curated, chỉ gắn `meta:1`, và gắn `u` khi spread trùng ladder;
- loài **rớt khỏi top-50** → gỡ `meta`.

Cuối lần chạy, script in ra danh sách loài mà **set curated lệch spread top của ladder**
(lần chạy 2026-07: 19 loài) để tự quyết. Muốn theo ladder thì:

```bash
python apply.py --overwrite    # ladder đè lên set curated của 50 loài đó
```

## Nguồn

- **Pikalytics** — `pikalytics.com/pokedex/battledataregmbs3/<name>`
  Format: Pokémon Champions VGC 2026 Reg M-B (ranked ladder).
  `robots.txt` của họ cho phép crawl và mời riêng AI bot vào `/ai/`.
  Scraper nghỉ 0.7s giữa các request và khai báo User-Agent rõ danh tính.

Ghi công: số liệu usage thuộc về Pikalytics.

## Nguồn phụ: champ-sets.json

`champ-sets.json` = set curated (1 build/loài), hiện phủ đủ 226 loài. Gộp vào `USAGEDATA`:

```bash
python merge_sets.py    # chỉ thêm loài CHƯA có trong USAGEDATA, đánh dấu s=1
python update_pkm.py --write   # ghi đè set từ paste.txt (paste là nguồn tin cậy hơn)
```

## Cần để ý khi chạy lại

- **Meta đổi thì danh sách 50 loài đổi.** `scrape.py` tự lấy danh sách từ index nên tự bắt kịp,
  nhưng loài mới có thể mang chiêu/item mà Pokédex trong app chưa có — `build.py` sẽ in ra
  danh sách đó, kiểm tra trước khi apply.
- **`build.py` đọc bảng item của app từ 3 chỗ**: literal `const ITEMS={…}`, `TYPE_ITEMS` và
  `RESIST_BERRY`. Hai bảng sau được nạp vào `ITEMS` bằng vòng lặp lúc chạy nên không nằm
  trong literal — trước khi vá, build tưởng app "không biết" Fairy Feather / Sharp Beak /
  Colbur / Roseli và ném luôn item usage thật (Sylveon 89.6% Fairy Feather bị bỏ).
- **Endpoint `/ai/` lỗi nature** (trả `a **** nature`) nên scraper đọc trang HTML thường.
- **Chỉ lấy build #1** của mỗi loài. Spread top thường chỉ ~30% số trận.
- Đá Mega map sang `mg` (dạng Mega) chứ không phải ô item — xem Implementation-notes.
