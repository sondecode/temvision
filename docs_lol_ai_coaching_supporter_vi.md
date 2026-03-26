# LoL AI Coaching Supporter – Use cases & hướng dẫn sử dụng

Tài liệu này mô tả cách dùng Temvision như một **AI coaching supporter** cho League of Legends theo runtime thống nhất:

```bash
python main.py --game=lol
```

---

## 1) AI Coaching Supporter là gì?

Temvision không chơi game hộ. Hệ thống đóng vai trò trợ lý realtime:

- đọc state trận đấu từ Live Client API + tín hiệu màn hình,
- phát hiện sự kiện quan trọng (missing, power spike, objective windows),
- đưa gợi ý chiến thuật ngắn gọn qua overlay.

Mục tiêu: hỗ trợ quyết định nhanh, không thay thế tư duy người chơi.

---

## 2) Use cases chính

### Use case A – Solo rank (laning + macro)

**Mục tiêu:** giảm sai lầm early/mid game.

- Cảnh báo enemy missing/gank risk.
- Gợi ý khi có lợi thế level/gold.
- Nhắc objective timing (dragon/baron).

**Giá trị:** giúp giữ nhịp trận và giảm các pha over-extend.

### Use case B – Champ select chuẩn bị trước trận

**Mục tiêu:** vào trận với thông tin rõ ràng.

- đọc dữ liệu pre-game từ LCU,
- hiển thị context đội hình/champ,
- (tuỳ config) enrich thêm thông tin rank.

**Giá trị:** chuẩn bị runes/build tốt hơn trước khi loading vào game.

### Use case C – Post-game review nhanh

**Mục tiêu:** feedback loop sau mỗi trận.

- lưu post-game stats,
- hiển thị report ngắn để biết điểm cần cải thiện,
- theo dõi tiến bộ qua match history.

**Giá trị:** học theo dữ liệu thực chiến thay vì cảm tính.

### Use case D – Máy yếu / API chập chờn

**Mục tiêu:** vẫn duy trì hỗ trợ cơ bản.

- bật OCR fallback,
- tắt minimap detector hoặc các nguồn nặng,
- giữ overlay gợi ý tối thiểu.

**Giá trị:** hệ thống degrade mềm thay vì dừng hoàn toàn.

---

## 3) Cách chạy nhanh

### Bước 1: cài dependencies

```bash
pip install -r requirements.txt
```

### Bước 2: chạy LoL module

```bash
python main.py --game=lol
```

### Bước 3: tùy chọn logging

```bash
python main.py --game=lol --verbose
```

---

## 4) Cấu hình quan trọng trong `config/lol.yaml`

### 4.1 Data sources

```yaml
data_sources:
  live_api: true
  pre_game: true
  post_game: true
  ocr_fallback: true
  minimap_detector: true
```

- `live_api`: nguồn realtime chính.
- `pre_game`: bật phân tích champion select.
- `post_game`: bật phân tích/lưu dữ liệu sau trận.
- `ocr_fallback`: fallback khi API lỗi.
- `minimap_detector`: detector minimap (có thể tắt để giảm tải).

### 4.2 Overlay cadence

```yaml
overlay:
  update_interval: 1.0
  fast_interval: 0.25
  slow_interval: 1.0
```

- `fast_interval`: cập nhật tín hiệu nhanh (event/combat).
- `slow_interval`: cập nhật phân tích nặng hơn.

---

## 5) Presets gợi ý

### Preset: Competitive

- `live_api: true`
- `pre_game: true`
- `post_game: true`
- `ocr_fallback: true`
- `minimap_detector: true`

Phù hợp: máy ổn, cần đầy đủ coaching.

### Preset: Low-resource

- `live_api: true`
- `pre_game: false`
- `post_game: false`
- `ocr_fallback: true`
- `minimap_detector: false`

Phù hợp: laptop yếu, ưu tiên ổn định FPS.

### Preset: OCR-only debug

- `live_api: false`
- `pre_game: false`
- `post_game: false`
- `ocr_fallback: true`
- `minimap_detector: false`

Phù hợp: debug pipeline OCR riêng.

---

## 6) Mở rộng sang game khác (TFT, Poker)

Temvision giữ entrypoint chung:

```bash
python main.py --game=<game>
```

Để thêm game mới:

1. tạo module runtime riêng (ví dụ `temvision/tft/module.py`),
2. thêm config `config/tft.yaml`,
3. tái sử dụng decision engine + output + http/client infra.

---

## 7) Lưu ý compliance

- Không inject process game.
- Không đọc memory game.
- Ưu tiên API chính thức/local endpoint được công bố.
