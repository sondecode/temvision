# League of Legends - Hướng Dẫn Toàn Diện

## Condition
- game == lol
- phase == champion_select OR phase == in_game OR phase == pre_game

## Action
- alert: "📋 Tham khảo hướng dẫn LoL bên dưới"
- priority: normal

## Hướng Dẫn Lên Đồ (Item Build)

### Trang Web Tra Cứu Build

- **U.GG** (https://u.gg): Trang web hàng đầu tra cứu build theo rank, role, patch hiện tại. Chọn tướng → xem core build, rune, skill order, summoner spell. Lọc theo rank (Iron → Challenger) để xem build phù hợp trình độ.
- **OP.GG** (https://op.gg): Tra cứu build phổ biến nhất và tỷ lệ thắng cao nhất. Vào mục Champions → chọn tướng → xem Item Build, Rune, Skill Order. Hỗ trợ xem theo server (KR, NA, EUW, VN).
- **Lolalytics** (https://lolalytics.com): Phân tích dữ liệu chi tiết nhất, thống kê từ hàng triệu trận đấu. Xem winrate theo từng item, rune combination, matchup cụ thể.
- **Blitz.gg** (https://blitz.gg): App desktop tự động import build vào client LoL. Gợi ý build real-time trong trận đấu, tự cập nhật theo patch.
- **Mobafire** (https://mobafire.com): Hướng dẫn build chi tiết do cộng đồng viết. Phù hợp cho người mới, có giải thích lý do chọn item.

### Cách Đọc Build Hiệu Quả

- Luôn kiểm tra **patch hiện tại** — build cũ có thể đã bị nerf.
- Ưu tiên build có **sample size lớn** (trên 1000 trận) để đảm bảo độ tin cậy.
- So sánh **winrate** vs **pickrate** — item có winrate cao nhưng pickrate thấp có thể chỉ dùng trong trường hợp đặc biệt.
- Xem **Mythic item** (hoặc core item mùa hiện tại) phù hợp với matchup, không chỉ build mặc định.
- Điều chỉnh build theo tình huống: đối thủ nhiều AP → mua Magic Resist sớm; đối thủ nhiều AD → mua Armor.

---

## Khắc Chế Theo Meta Game Hiện Tại

### Trang Web Tra Cứu Counter

- **U.GG Counters** (https://u.gg/lol/champions): Vào trang tướng → tab Counters → xem danh sách counter pick chính xác theo rank và patch.
- **OP.GG Counter** (https://op.gg): Mục Champions → chọn tướng → tab Counter → xem tỷ lệ thắng matchup.
- **CounterStats** (https://counterstats.net): Chuyên trang counter pick, giao diện đơn giản, dễ dùng trong lúc ban/pick.
- **Mobalytics** (https://mobalytics.gg): Phân tích chi tiết matchup với gợi ý cách chơi counter.

### Nguyên Tắc Counter Pick

- **Counter theo lane**: Chọn tướng thắng thế ở giai đoạn laning (ví dụ: chọn Darius counter Nasus top).
- **Counter theo teamfight**: Chọn tướng có kit khắc chế khi teamfight (ví dụ: chọn Malzahar counter assassin).
- **Counter theo scaling**: Nếu đối thủ chọn tướng late game, chọn tướng early game mạnh để snowball (ví dụ: Draven counter Vayne).
- **Counter theo CC**: Đối thủ thiếu CC → chọn tướng cơ động. Đối thủ nhiều CC → chọn tướng có Cleanse hoặc QSS.
- **Meta tier list**: Luôn kiểm tra tier list hiện tại trên U.GG hoặc OP.GG để biết tướng nào đang mạnh nhất (S-tier, A-tier).

### Cách Áp Dụng Trong Trận

- Kiểm tra đội hình đối thủ: nhiều AD → tập trung armor; nhiều AP → tập trung MR.
- Xem đối thủ có tướng one-trick nào không → cấm hoặc counter pick trực tiếp.
- Điều chỉnh rune theo matchup: ví dụ chọn Bone Plating nếu đối phương chơi combo burst.

---

## Xem Lịch Sử Đối Thủ

### Trang Web Tra Cứu Lịch Sử

- **OP.GG** (https://op.gg): Nhập tên summoner → xem lịch sử trận đấu, rank, tướng hay chơi, tỷ lệ thắng. Xem chi tiết từng trận: KDA, CS, ward, damage.
- **U.GG Profile** (https://u.gg): Tìm kiếm theo tên summoner + server → xem match history, champion pool.
- **Porofessor** (https://porofessor.gg): Hiển thị thông tin real-time khi vào trận. Cho biết đối thủ là main gì, winrate gần đây, có đang thua streak không.
- **Blitz.gg** (https://blitz.gg): Auto hiện thông tin đối thủ trong loading screen, không cần tab ra ngoài.
- **OPGG Desktop App**: Cài đặt app desktop để tự động tra cứu khi vào game.

### Thông Tin Cần Chú Ý

- **Champion Pool**: Đối thủ hay chơi tướng nào → dự đoán pick và counter sẵn.
- **Winrate gần đây**: Đối thủ đang winning streak hay losing streak → đánh giá tâm lý.
- **Rank và LP**: Elo thật vs elo hiện tại → biết trình độ thật.
- **Preferred Role**: Main role nào → nếu bị autofill sẽ yếu hơn.
- **KDA trung bình**: Chỉ số KDA thấp = hay chơi aggressive hoặc hay chết → gank sẽ hiệu quả.
- **Ward score**: Ward score thấp = ít đặt ward → dễ gank hơn.
- **CS per minute**: CS/phút thấp = khả năng farming kém → có thể deny farm để tạo lợi thế.

---

## Meta Cấm Chọn (Ban/Pick)

### Chiến Lược Cấm Tướng (Ban Phase)

- **Ban theo meta**: Cấm tướng S-tier đang có winrate và pickrate cao nhất patch hiện tại (kiểm tra trên U.GG, OP.GG).
- **Ban theo one-trick đối thủ**: Nếu biết đối thủ là one-trick → cấm tướng main của họ để ép họ chơi tướng không quen.
- **Ban theo counter bản thân**: Nếu đã biết mình muốn chơi gì → cấm tướng counter mạnh nhất (ví dụ: muốn chơi Yasuo → cấm Malzahar hoặc Renekton).
- **Ban theo team comp đối thủ**: Nếu đối thủ đang build comp engage → cấm engage tool chính (ví dụ: cấm Amumu, Malphite).
- **Không cấm tướng winrate thấp**: Tướng có winrate dưới 48% không cần cấm trừ khi đối thủ là one-trick.

### Chiến Lược Chọn Tướng (Pick Phase)

- **First pick**: Ưu tiên chọn tướng **flex pick** có thể chơi nhiều lane (ví dụ: Aurora, Yone, Ambessa).
- **Blind pick safe**: Nếu pick sớm, chọn tướng ít bị counter (ví dụ: Orianna mid, Ezreal ADC).
- **Counter pick cuối**: Giữ pick cuối cho lane quan trọng nhất để counter pick đối thủ.
- **Synergy team**: Chọn tướng có synergy với đội (ví dụ: có Yasuo → chọn Malphite hoặc Diana jungle cho knock-up combo).
- **Tránh one-trick rõ ràng**: Nếu team không có backup pick → không nên pick quá sớm để đối thủ counter.

### Trang Web Theo Dõi Meta Ban/Pick

- **U.GG Tier List** (https://u.gg/lol/tier-list): Tier list cập nhật theo từng patch, lọc theo rank và role.
- **OP.GG Statistics** (https://op.gg/statistics): Thống kê ban rate, pick rate, win rate tổng hợp.
- **Lolalytics Tier List** (https://lolalytics.com/lol/tierlist): Phân tích chi tiết nhất với biểu đồ xu hướng meta.
- **League of Graphs** (https://leagueofgraphs.com): Thống kê toàn diện về meta, champion trends, player statistics.

---

## Gợi Ý Trong Trận (In-Game Tips)

### Early Game (0-14 phút)

- Kiểm tra minimap mỗi 5 giây — nếu không thấy enemy jungler → cẩn thận gank.
- Ward river và pixel brush lúc 2:30-3:00 để phòng gank đầu tiên.
- Nếu đối thủ dùng summoner spell quan trọng (Flash, TP) → ghi nhớ thời gian cooldown (Flash: 5 phút, TP: 6 phút).
- Ưu tiên CS hơn trade nếu không chắc thắng 1v1.
- Ping SS (enemy missing) ngay khi mất tầm nhìn đối thủ lane.

### Mid Game (14-25 phút)

- Theo dõi objective timer: Dragon, Rift Herald, Baron.
- Group khi có số lượng ưu thế — không đánh 50/50.
- Ward sâu vào jungle đối thủ nếu đang kiểm soát map.
- Split push khi team có tướng split mạnh (Fiora, Jax, Tryndamere) — còn lại chơi 4v4 giữ mid.

### Late Game (25 phút+)

- Không chết một mình — respawn timer rất dài.
- Baron là win condition chính — ưu tiên vision quanh Baron pit.
- Đợi đối thủ sai lầm trước — không force fight khi không có vision.
- Nếu thua teamfight → stall game, farm side lane, chờ scaling.

---

## Macro Strategies

### Wave Management

- **Freeze lane**: Giữ wave gần tháp mình để bắt đối thủ overextend → jungler gank dễ.
- **Slow push**: Để minion tích 2-3 wave → dive tháp hoặc roam khi wave đến tháp đối thủ.
- **Fast push**: Clear wave nhanh nhất có thể → roam hoặc recall mua đồ.
- **Khi nào reset**: Sau khi push wave vào tháp đối thủ → recall. Không recall khi wave đang đẩy về phía mình.

### Jungle Pathing

- Kiểm tra starting item đối thủ jungler → đoán hướng clear (ví dụ: Red buff start → có thể gank bot lúc 3 phút).
- Counter jungle khi biết vị trí đối thủ jungler (ví dụ: thấy enemy jungler ở top → lấy bot side jungle đối thủ).
- Ưu tiên objective > gank nếu có cơ hội (Dragon/Herald timer gần).

### Vision Control

- **Ward quan trọng**: River brush, pixel brush, objective pit, enemy jungle entrance.
- **Control ward**: Luôn mang ít nhất 1 control ward — đặt ở vị trí team thường xoay qua.
- **Sweeper**: Đổi sang sweeper khi đã có đủ ward từ support — clear vision đối thủ trước objective.
