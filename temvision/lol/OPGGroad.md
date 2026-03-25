Đánh giá hiện trạng vs OP.GG

Temvision đã có: phase-gating (CLOSED/CLIENT_OPEN/IN_GAME), pipeline capture → vision → state → rule/skill → overlay; LiveClient API (ingame) + LoL detector; rule-based events (enemy missing, power spikes, HP/combat, jungle risk), objective timers (dragon/baron/herald), suggestion engine (HP/gold/level/CS/team), feature extraction (gold/level/CS/kills/team strength), post-game analyzer (KDA, CS/min, performance score), Riot API client stub (chưa dùng), overlay console/GUI.
Temvision chưa có so với OP.GG: pre-game champ select insights (rank/WR/match-up), rune/item/build gợi ý + auto-import, lane threat scoring, summoner spell timers, item/spell cooldown tracking, scoreboard & minimap OCR (vị trí tướng/ward), runes/items từ LCU, history UI & recent games, community data, desktop launcher/auto-start.
Khoảng trống chính cần lấp để “clone” OP.GG 1:1

Pre-game (champ select/lobby)
LCU API hoặc OCR champ select để lấy team comps, bans, lane assign.
Riot API sử dụng thực tế: rank, champion mastery, recent winrate, match-up WR theo lane/champion.
Gợi ý rune/item/build per champion+lane; nút auto-copy/import (LCU runes import hoặc file).
In-game overlay
OCR HUD: vàng, CS, K/D/A, level, summoner spells & cooldowns, item actives, objective timers on-screen; minimap detection (YOLO/template) vị trí tướng/ward.
Summoner spell timer tracking (flash/teleport/ignite) cho ally/enemy; death/respawn timers.
Lane threat & power spike theo item/rune; wave state (minimap), vision score, jungle tracking nâng cao.
Overlay UX: panel theo lane (ally/enemy), objective blocks, compact vs detail mode.
Post-game & history
Lưu trận (sqlite) với timeline CS/gold/objectives; lịch sử + filter; so sánh với rank-tier benchmarks; xuất report.
Reliability/UX
Watchdog LiveClient API + degrade sang OCR-only; cache/template/OCR threshold config; telemetry local (fps/latency).
Desktop launcher / auto-start with LoL, hotkeys.
Lộ trình đề xuất (ưu tiên OCR để vượt OP.GG)

Pha 1: Parity tối thiểu in-game
Thêm OCR HUD (vàng/CS/KDA/level), summoner spell CD, item actives; minimap YOLO/template cho vị trí tướng.
Summoner spell timer logic + overlay indicators; refine objective timers bằng OCR khi LiveClient thiếu.
UX overlay dạng thẻ lane + objective panel.
Pha 2: Champ select & pre-game
Tích hợp LCU API cho champ select; fallback OCR champ select.
Riot API thực thi: rank/WR/mastery, match-up stats; build/rune gợi ý + auto-import.
Pha 3: Post-game & lịch sử
Ghi trận vào sqlite; view history, filter; so sánh benchmark; báo cáo đề xuất cải thiện.
Pha 4: ML & ưu thế OCR
Model threat/suggestion offline dùng feature_engine + OCR minimap/spell CD; giảm phụ thuộc API.
Nâng minimap/ward detection (YOLOv8 tiny) để vượt OP.GG ở tracking thời gian thực.
Pha 5: Polishing
Desktop launcher/hotkey; cấu hình per-champion; tối ưu hiệu năng capture/OCR.
Mốc kiểm thử

Unit: phase detection, adapter get_phase, OCR parsers, suggestion/objective rules, Riot API (mock).
Integration: mock LiveClient/LCU + sample OCR frames → overlay text đúng; degrade path khi API down.
Manual: run python main.py --game=lol qua 3 phase; verify không cảnh báo trước trận, overlay hiển thị timers/suggestions khi in-game.