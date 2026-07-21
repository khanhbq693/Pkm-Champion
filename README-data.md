# Cập nhật usage data (Champions Reg M-B)

`USAGEDATA` trong `index.html` là **ảnh chụp** số liệu ladder — data hiện tại: **2026-05**.
Pikalytics refresh hàng tháng, nên chạy lại 3 lệnh sau để cập nhật:

```bash
python scrape.py      # tải 50 loài của meta -> raw.json  (~40s, có nghỉ 0.7s/request)
python build.py       # raw.json -> usagedata.js, in ra thứ app không khớp
python apply.py       # thay khối USAGEDATA trong index.html
```

`apply.py` không kèm sẵn — nó chỉ là 3 dòng thay chuỗi; xem `Implementation-notes.html` (Đợt 8).
Chạy `scrape.py 3` để thử 3 loài trước cho nhanh.

## Nguồn

- **Pikalytics** — `pikalytics.com/pokedex/battledataregmbs3/<name>`
  Format: Pokémon Champions VGC 2026 Reg M-B S3 (ranked ladder).
  `robots.txt` của họ cho phép crawl và mời riêng AI bot vào `/ai/`.
  Scraper nghỉ 0.7s giữa các request và khai báo User-Agent rõ danh tính.

Ghi công: số liệu usage thuộc về Pikalytics.

## Nguồn phụ: champ-sets.json (36 loài)

`champ-sets.json` = các set gợi ý (1 build/loài), bổ sung cho những loài Pikalytics chưa phủ.
Gộp vào `USAGEDATA` bằng:

```bash
python merge_sets.py    # chỉ thêm loài CHƯA có trong USAGEDATA, đánh dấu s=1
```

Khác Pikalytics: không có % usage (là set gợi ý, không phải thống kê). Trong tool hiện nhãn
**· set** và tô vàng như Pikalytics, nhưng người dùng biết đây là 1 build tham khảo.
Muốn thêm/sửa set: sửa `champ-sets.json` rồi chạy lại `merge_sets.py`.
Loài đã có trong Pikalytics sẽ được GIỮ (merge không đè).

## Cần để ý khi chạy lại

- **Meta đổi thì danh sách 50 loài đổi.** `scrape.py` tự lấy danh sách từ index nên tự bắt kịp,
  nhưng loài mới có thể mang chiêu/item mà Pokédex trong app chưa có — `build.py` sẽ in ra
  danh sách đó, kiểm tra trước khi apply.
- **Endpoint `/ai/` lỗi nature** (trả `a **** nature`) nên scraper đọc trang HTML thường.
  Nếu Pikalytics sửa lỗi đó thì dùng `/ai/` sẽ gọn hơn.
- **Chỉ lấy build #1** của mỗi loài. Spread top thường chỉ ~30% số trận.
- Đá Mega map sang `mg` (dạng Mega) chứ không phải ô item — xem Implementation-notes.
