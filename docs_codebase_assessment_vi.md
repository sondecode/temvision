# Đánh giá nhanh codebase Temvision (03/2026)

## 1) Tổng quan kiến trúc hiện tại

Luồng chính đang đi theo đúng hướng `capture -> vision -> adapter -> state -> decision -> overlay`:

- `main.py` parse CLI và khởi tạo `TemvisionApp`.
- `TemvisionApp` điều phối vòng lặp capture/detect/decide/show.
- Nhánh LoL đã có 3 nguồn dữ liệu chính:
  - **Screen vision/OCR**: OpenCV + Tesseract (`vision`, `minimap_detector`, `hud_ocr`).
  - **Live Client API localhost:2999**: dữ liệu in-game realtime (`client_api.py`).
  - **LCU lockfile/local API**: dữ liệu pre-game/champ select (`lcu_client.py`, `pre_game.py`).

## 2) Đánh giá tính nhất quán mã nguồn

### Điểm nhất quán tốt

- Có cấu trúc package rõ ràng theo domain (`temvision/lol`, `temvision/vision`, `temvision/decision`).
- Có bộ test khá đầy đủ theo module (nhiều file `tests/test_*.py`).
- Dataclass được dùng xuyên suốt cho model và event/suggestion.
- Config YAML tách riêng theo game và feature.

### Điểm chưa nhất quán / cần chuẩn hoá

1. **Hai nhánh vận hành LoL song song**
   - `TemvisionApp` đang dùng pipeline generic từ `config/lol.yaml`.
   - Đồng thời repo có `lol_overlay.py` + `config/lol_overlay.yaml` cho pipeline LoL chuyên sâu.
   - Cần chọn 1 “entrypoint chính” và ghi rõ khi nào dùng mỗi nhánh.

2. **Nguồn dữ liệu chiến thuật chưa đồng nhất**
   - Build recommender đang dùng dữ liệu bundled JSON.
   - Có ghi “extensible later to OP.GG/community APIs”, nhưng chưa có adapter chuẩn hoá source.
   - Nên thêm interface data provider (official API / cache / external provider).

3. **Mức độ đóng gói HTTP client chưa đồng bộ**
   - Một số nơi dùng session + helper tốt (`RiotAPI`, `LiveClientAPI`).
   - `RuneImporter` vẫn gọi private method của `LCUClient` và tự mở `requests` trong method.
   - Nên gom về 1 lớp client thống nhất (GET/POST/DELETE + retry + error policy).

4. **Khác biệt naming/config giữa generic và LoL chuyên sâu**
   - Có `config/lol.yaml` và `config/lol_overlay.yaml` cùng chứa phần overlap.
   - Dễ gây lệch cấu hình khi mở rộng tính năng.

## 3) Trả lời câu hỏi: dữ liệu detect có thể lấy trực tiếp từ source game Liên Minh?

**Không nên và thực tế không thể theo nghĩa “lấy từ source game”** vì League là mã nguồn đóng/proprietary.

Hướng đúng (đang có sẵn trong repo):

- **Live Client Data API (localhost:2999)**: dữ liệu trận đang chơi (player, score, events...).
- **LCU API qua lockfile**: dữ liệu client/champ select, rune pages.
- **Riot Developer API**: match history/rank/account theo key chính thức.
- **Vision/OCR từ màn hình**: lớp fallback/bổ sung cho tín hiệu không có trong API.

=> Nếu mục tiêu là bền vững + compliance, nên ưu tiên API chính thức/local endpoint công khai, không reverse-engineer binary/process memory.

## 4) Dữ liệu chiến thuật: nên code từ API nào hay crawl?

### Nguồn nên ưu tiên theo thứ tự

1. **Riot Developer API**
   - Match-v5, League-v4, Spectator-v5 (tuỳ use case).
   - Dùng cho thống kê dài hạn, pre-game scouting, champion tendencies.

2. **Live Client API + LCU API (local official endpoints)**
   - Dùng cho realtime in-game và champ select.

3. **Dữ liệu curated nội bộ (JSON/versioned)**
   - Build/rune baseline để đảm bảo hệ thống vẫn chạy khi external source lỗi.

### Về crawl (OP.GG/u.gg/...) 

- **Chỉ nên dùng khi điều khoản cho phép rõ ràng** và có chiến lược chống lệ thuộc.
- Nếu crawl:
  - cần lớp `provider` tách biệt,
  - cache + TTL,
  - schema normalization,
  - circuit breaker/fallback về dữ liệu bundled.
- Khuyến nghị thực tế: ưu tiên nguồn có API/public data hợp lệ trước, crawl là phương án phụ.

## 5) Định hướng kỹ thuật đề xuất

### Ngắn hạn (1-2 sprint)

- Chuẩn hoá “data source layer”: `IDataProvider` cho live/pre-game/post-game.
- Hợp nhất config LoL (hoặc ghi rõ 2 mode, có migration guide).
- Tách shared HTTP client + retry/backoff/logging chuẩn.
- Bổ sung “feature flags” bật/tắt từng nguồn dữ liệu.

### Trung hạn (3-6 sprint)

- Event bus nội bộ: mỗi nguồn đẩy `GameSignal`, engine hợp nhất theo timestamp/confidence.
- Scoring pipeline cho tactical suggestions (rule + statistical priors).
- Offline dataset builder từ match history để tuning thresholds.

### Dài hạn

- Chuẩn hoá plugin/provider marketplace.
- Version hoá schema state/decision để tránh breaking khi mở rộng game khác.

## 6) Có cần cập nhật README không?

**Có, nên cập nhật ngay.**

README hiện tại mô tả tổng quan tốt nhưng chưa nêu rõ:

- 2 đường chạy LoL (generic app vs overlay app).
- Các nguồn dữ liệu LoL đang dùng (Live API, LCU, Riot API, OCR).
- Chính sách dữ liệu/compliance (không inject, không đọc memory, không reverse-engineering).
- Trạng thái feature (stable/experimental/planned) theo module.

Nên bổ sung một mục “LoL Data Sources & Compliance” + “Run modes”.
