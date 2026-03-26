# LoL feature matrix (giữ / bỏ / refactor)

Mục tiêu: hợp nhất runtime LoL vào module LoL (không tách mode riêng), nhưng vẫn tối ưu cho mở rộng đa game trong tương lai.

## 1) Nên giữ ngay (core value)

1. **Live Client API ingestion**
   - Giá trị cao nhất cho realtime in-game.
   - Dùng cho state chuẩn, giảm phụ thuộc OCR.

2. **Event + Suggestion engine**
   - Là lõi tactical coaching.
   - Nên giữ rule-based để ổn định và dễ test.

3. **Objective tracker + spell/item tracker + threat scorer**
   - Tạo signal hữu ích trực tiếp cho quyết định (macro/micro).

4. **Pre-game + Post-game pipelines**
   - Pre-game: champion select context.
   - Post-game: feedback loop học theo match history.

5. **Data-source flags**
   - Giúp degrade linh hoạt khi API lỗi/máy yếu.

## 2) Nên refactor/chuẩn hoá (giữ nhưng cần cải tiến)

1. **Overlay presentation layer**
   - Giữ overlay nhưng tách rõ `data -> view model -> render`.

2. **Config model**
   - Giữ 1 config chính `config/lol.yaml`.
   - Dọn key legacy khi đã migrate ổn định.

3. **Provider contract**
   - Chuẩn hoá thêm metadata (timestamp/source/confidence) để reuse cho game khác.

4. **Module boundary cho đa game**
   - LoLModule đang là chuẩn đầu tiên.
   - Tạo interface tương tự cho TFT/Poker sau này.

## 3) Nên bỏ dần (hoặc chuyển legacy)

1. **Chạy `lol_overlay.py` như entrypoint chính**
   - Chỉ giữ backward compatibility.
   - Official command: `python main.py --game=lol`.

2. **Config `lol_overlay.yaml` làm nguồn cấu hình chính**
   - Chuyển thành legacy/reference.
   - Tránh lệch config giữa 2 file.

3. **Logic networking rải rác trong từng module**
   - Đã gom về HttpClient, tiếp tục loại bỏ đoạn gọi raw requests còn sót.

## 4) Ưu tiên triển khai tiếp theo

### P1 (ngắn hạn)
- Stabilize LoLModule API.
- Bổ sung test cho LoLModule (mock runtime).
- Đánh dấu rõ các feature `stable/experimental`.

### P2 (trung hạn)
- Trích xuất `BaseGameModule` để chuẩn bị TFT/Poker.
- Tách tactical signals thành schema chung cross-game.

### P3 (dài hạn)
- Mỗi game có module riêng:
  - `temvision/tft/module.py`
  - `temvision/poker/module.py`
- Reuse chung: decision engine, output, http/client infra.
