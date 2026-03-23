# 🔥 Temvision

> AI Vision Framework for Real-Time Game Decision Support

Temvision là một **AI desktop assistant chạy local**, có khả năng:

* 👁️ Đọc màn hình game (real-time)
* 🧠 Phân tích trạng thái trận đấu
* 🎯 Đưa ra quyết định cho game thủ
* 🔌 Mở rộng bằng config + skill (.md)

---

## 🚀 Demo Concept

```
Game Screen → Vision → State → AI → Decision → Overlay
```

Ví dụ:

* ⚠️ "Enemy missing"
* 🎯 "Take dragon"
* 🛑 "Back off now"

---

## ✨ Features

* 🖥️ **Local-first** – không cần backend
* 🎮 **Multi-game support** (config-based)
* 🧠 **AI-powered decision engine**
* 🔌 **Plugin system bằng Markdown (.md)**
* 🤖 **Multi-LLM support**

  * OpenAI
  * Claude
  * Gemini
* 🪟 **Overlay popup real-time**
* 🔊 **TTS (premium feature)**

---

## 🧬 Architecture

```
[Screen Capture]
      ↓
[Vision Engine]
      ↓
[Game Adapter]
      ↓
[Game State]
      ↓
[Skill (.md)]
      ↓
[Decision Engine]
      ↓
[Overlay / TTS]
```

---

## ⚙️ Tech Stack

| Layer  | Tech                     |
| ------ | ------------------------ |
| Core   | Python 3.10+             |
| GUI    | PySide6 (Qt)             |
| Vision | OpenCV, mss, YOLOv8      |
| OCR    | Tesseract                |
| AI     | OpenAI / Claude / Gemini |
| Config | YAML                     |

---

## 📦 Installation

```bash
git clone https://github.com/sondecode/temvision.git
cd temvision

pip install -r requirements.txt
```

---

## ▶️ Usage

```bash
python main.py --game=lol
```

---

## 🎮 Multi-game via Config

Temvision hỗ trợ nhiều game thông qua file config.

Ví dụ:

```
config/lol.yaml
config/valorant.yaml
```

---

### 🧩 Example Config

```yaml
game: lol

capture:
  minimap_region: [1600, 800, 300, 300]

vision:
  detect:
    - enemy_icon

mapping:
  enemy_icon: enemy

rules:
  - name: enemy_missing
    condition: "enemy_visible == false"
    action: "⚠️ Enemy missing"
```

---

## 📜 Skill System (.md)

Bạn có thể định nghĩa logic bằng Markdown:

```
# Enemy Missing

## Condition
- enemy_visible == false

## Action
- alert: "⚠️ Cẩn thận bị gank"
- priority: high
```

---

## 🧠 Decision Engine

* ⚡ Rule-based (fast, offline)
* 🤖 LLM-based (advanced reasoning)

---

## 🔊 Output

### Free

* Popup overlay

### Premium (planned)

* Voice coach (TTS)

---

## 🧪 MVP Scope

* 1 game (LoL)
* Minimap detection
* Enemy missing alert
* Overlay popup

---

## 🗺️ Roadmap

### Phase 1

* Basic vision + rule engine

### Phase 2

* Multi-skill system
* LLM integration

### Phase 3

* Multi-game support
* Plugin marketplace

### Phase 4

* Vision model fine-tuning

---

## 🤝 Contributing

Chúng tôi rất welcome đóng góp:

* 🧠 Skill (.md)
* 🎮 Game adapter mới
* 👁️ Vision improvements
* ⚡ Performance optimization

---

## ⚠️ Disclaimer

Temvision:

* Không inject vào game
* Chỉ đọc màn hình
* Không vi phạm anti-cheat (intended)

---

## ⭐ Why Temvision?

> Không phải tool → mà là framework

* Build AI cho game
* Extend dễ dàng
* Open ecosystem

---

## 📢 Call for Contributors

Nếu bạn:

* thích AI
* thích game
* thích build framework

👉 Đây là project dành cho bạn

---

## 📄 License

MIT License

---

## 🔥 Vision

> “Make AI understand games like humans do”
