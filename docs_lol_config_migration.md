# LoL config migration guide

Mục tiêu sau cập nhật này là **một entrypoint duy nhất cho LoL**:

- `python main.py --game=lol`

Không tách `overlay mode` riêng nữa. `lol_overlay.py` chỉ giữ vai trò tương thích ngược.
Runtime chính được gom vào `temvision/lol/module.py` (LoLModule).

## 1) Config chuẩn

LoL dùng một file chính:

- `config/lol.yaml`

Các section chính:

- `overlay`: tần suất loop và hiển thị.
- `data_sources`: feature flags cho live/pre/post/ocr/minimap.
- `capture`, `vision`, `mapping`, `rules`: vẫn giữ cho pipeline chung.

## 2) Data source flags

```yaml
data_sources:
  live_api: true
  pre_game: true
  post_game: true
  ocr_fallback: true
  minimap_detector: true
```

## 3) Tương thích ngược

- `config/lol_overlay.yaml`: giữ lại để tham chiếu/backward compatibility.
- `lol_overlay.py`: wrapper deprecated, sẽ tự chuyển sang `main.py --game=lol`.

## 4) Hướng mở rộng đa game (TFT, Poker)

Để support game mới trong tương lai:

1. Giữ entrypoint chung `main.py --game=<game>`.
2. Mỗi game có module riêng trong `temvision/<game>/...` với data provider và adapter tương ứng.
3. Dùng chung hạ tầng cross-game:
   - config loader,
   - decision/rule engine,
   - HTTP client/retry,
   - output overlay.
