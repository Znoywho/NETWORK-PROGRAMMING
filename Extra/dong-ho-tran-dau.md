# Đồng hồ trận đấu — hết giờ lượt, mất kết nối, kết nối lại

Tài liệu này gom về một chỗ toàn bộ phần "thời gian" của ván đấu: đồng hồ
suy nghĩ mỗi lượt, hạn kết nối lại sau khi rớt mạng, và cách hai đồng hồ
đó ảnh hưởng lẫn nhau. Code nằm ở `Code/Server/app/handlers/message_handlers.py`
(luật) và `Code/Server/app/network/server.py` (nhịp kiểm tra).

Phần đóng khung message và vòng lặp `selectors` xem `network-protocol.md`.

---

## 1. Ba con số của hệ thống

| Đồng hồ | Hằng số | Mặc định | Nơi khai báo | Hết hạn thì sao |
|---|---|---|---|---|
| Suy nghĩ mỗi lượt | `TURN_TIME_LIMIT_SECONDS` | 30 giây | `message_handlers.py` | Người đang tới lượt **thua** (`reason = "timeout"`, **có** tính Elo) |
| Chờ kết nối lại | `RECONNECT_GRACE_SECONDS` | 60 giây | `message_handlers.py` | Đối thủ **thắng** (`reason = "disconnect"`, **không** tính Elo) |
| Nhịp đối chiếu đồng hồ | `TICK_INTERVAL_SECONDS` | 1.0 giây | `network/server.py` | Không phải luật chơi — là độ phân giải: mọi mốc trên sai số tối đa ~1 giây |

Hai hằng số đầu là luật nhóm công bố. Hằng số thứ ba là chi tiết kỹ thuật:
`sel.select(timeout=1.0)` khiến vòng lặp tự thức dậy mỗi giây kể cả khi
không client nào gửi gì, nhờ vậy `tick()` mới có dịp phát hiện hết giờ.

Cả hai mốc thời gian đo bằng `time.monotonic()` chứ không phải `time.time()`:
đồng hồ đơn điệu không nhảy khi máy đổi giờ hệ thống hay đồng bộ NTP giữa ván.

---

## 2. Trạng thái thời gian của một phòng

Toàn bộ trạng thái nằm trong ba trường của `Room`
(`app/models/matchmaking_models.py`) cộng một dict của handler:

| Nơi lưu | Ý nghĩa |
|---|---|
| `room.turn_deadline` | Thời điểm người đang tới lượt hết giờ. `None` = đồng hồ suy nghĩ **không chạy** |
| `room.disconnected_player` | `player_id` đang mất kết nối, `None` nếu cả hai đang online |
| `room.reconnect_deadline` | Hạn chót để người đó đăng nhập lại. `None` = không chờ ai |
| `MessageHandler._awaiting_reconnect` | `player_id → room_id`, để lần `login` sau biết đưa họ về phòng nào |

Ba tổ hợp hợp lệ, không có tổ hợp thứ tư:

```text
                    ┌──────────────────────────────────────────┐
                    │  login lại kịp hạn → cấp trọn 1 lượt mới │
                    ▼                                          │
 accept_invite ┌────────────┐   rớt kết nối   ┌─────────────┐  │
 ────────────► │ ĐANG ĐÁNH  │ ──────────────► │  TẠM DỪNG   │ ─┘
 mỗi nước đi   │ turn : t+30│                 │ turn : None │
 nạp lại lượt  │ recon: None│                 │ recon: t+60 │
               └────────────┘                 └─────────────┘
                     │ hết giờ lượt (tick)          │ quá hạn (tick)
                     │ thắng / hoà trên bàn cờ      │ → đối thủ thắng
                     │ leave_room                   │
                     ▼                              ▼
               ┌──────────────────────────────────────────────┐
               │ ĐÃ KẾT THÚC — turn: None, recon: None        │
               │ status = FINISHED, bàn cờ bị khoá            │
               └──────────────────────────────────────────────┘
```

**Hai đồng hồ không bao giờ chạy cùng lúc.** Lúc chờ người rớt mạng quay
lại, `turn_deadline` bị đặt `None` — đồng hồ suy nghĩ tạm dừng. Nếu để nó
chạy tiếp thì mạng chập chờn ăn mất lượt của người chơi hai lần: một lần vì
rớt mạng, một lần vì hết giờ.

---

## 3. Bảng chuyển trạng thái

Đọc theo hàng: sự kiện nào đặt lại đồng hồ nào.

| Sự kiện | Hàm xử lý | `turn_deadline` | `reconnect_deadline` | `disconnected_player` |
|---|---|---|---|---|
| Nhận lời mời, ván bắt đầu | `_accept_invite_handler` → `_start_turn` | `now + 30` | — | — |
| Đánh một nước hợp lệ, chưa ai thắng | `_make_move_handler` → `_start_turn` | `now + 30` (nạp lại cho đối thủ) | — | — |
| Người chơi rớt kết nối | `disconnect()` | `None` (tạm dừng) | `now + 60` | `player_id` |
| Người đó đăng nhập lại kịp hạn | `_resume_after_reconnect` | `now + 30` (trọn vẹn lượt mới) | `None` | `None` |
| Quá hạn kết nối lại | `tick()` → `_end_game_deliveries` | `None` | `None` | `None` |
| Hết giờ suy nghĩ | `tick()` → `_end_game_deliveries` | `None` | — | — |
| Thắng / hoà trên bàn cờ | `_make_move_handler` → `_end_game_deliveries` | `None` | `None` | `None` |
| Chủ động rời phòng | `_leave_room_handler` → `_end_game_deliveries` | `None` | `None` | `None` |
| Khán giả rớt kết nối | `disconnect()` | không đổi | không đổi | không đổi |

Mọi đường kết thúc ván đều đi qua đúng một hàm `_end_game_deliveries()`, nên
không đường nào quên tắt đồng hồ, xoá `_awaiting_reconnect`, khoá bàn cờ, ghi
kết quả xuống DB và trả người chơi về `idle`.

---

## 4. Xử lý mất kết nối, từng bước

```text
client rớt (thoát app / đóng socket / TCP reset)
        │
        ▼
Connection.recv()  nhận b"" hoặc ConnectionResetError
        │  ném RuntimeError("Peer closed.")
        ▼
ServerHandler._handle_client  bắt RuntimeError
        ▼
ServerHandler._handle_disconnect  →  MessageHandler.disconnect(sock)
        │
        ├─ Không ở trong ván (đang ở sảnh)  → xoá khỏi PlayerManager, broadcast online_players
        ├─ Là khán giả                      → rời khỏi room.spectators, ván chạy tiếp bình thường
        └─ Là người chơi, phòng PLAYING     → GIỮ PHÒNG, tạm dừng đồng hồ, mở hạn 60 giây
                                               gửi player_disconnected cho đối thủ + khán giả
        ▼
conn.close()  huỷ đăng ký khỏi selector, đóng socket
```

Điểm quan trọng: **người rớt mạng không bị xử thua ngay.** Phòng vẫn
`PLAYING`, bàn cờ giữ nguyên, chỉ đồng hồ đổi trạng thái. Người đó bị xoá
khỏi `PlayerManager` (nên biến mất khỏi danh sách online) nhưng `player_id`
của họ được ghi vào `_awaiting_reconnect` để lần đăng nhập sau nhận ra.

Message đối thủ nhận được:

```json
{ "type": "player_disconnected", "room_id": "42", "playerId": "7", "reconnectTimeLeft": 60 }
```

Nếu **cả hai** cùng rớt (người thứ hai rớt khi đang chờ người thứ nhất quay
lại) thì không còn ai để xử thắng: ván kết thúc ngay với `winner = None`.

---

## 5. Kết nối lại kịp hạn

Không có message `reconnect` riêng. Client mở socket mới và `login` lại như
bình thường; `_login_handler` gọi `_resume_after_reconnect(player_id)`:

1. Tra `_awaiting_reconnect` — không có thì đây là lần đăng nhập bình thường, trả về rỗng.
2. Kiểm tra phòng còn `PLAYING` và vẫn đang chờ đúng người này.
3. Xoá `disconnected_player` và `reconnect_deadline`.
4. `_start_turn(room)` — **cấp trọn vẹn 30 giây mới**, không tính phần đã trôi trước khi rớt.
5. Gửi `player_reconnected` cho những người còn lại, rồi gửi `game_state` đầy đủ cho cả phòng, kể cả người vừa quay lại.

Vì sao cấp trọn lượt mới thay vì trả lại đúng số giây còn dư: người vừa quay
lại phải mở lại app, đăng nhập, nhìn lại bàn cờ. Trả họ về với 3 giây còn sót
thì hạn kết nối lại trở thành vô nghĩa.

Hệ quả của việc dùng chính `login`: kết nối lại là đăng nhập lại bằng
username/password, không có session token. Đủ dùng cho đồ án — xem phần
"Giới hạn hiện tại" của `network-protocol.md`.

---

## 6. Hết hạn — `tick()`

`tick()` là **nơi duy nhất** thời gian trôi qua trở thành một message. Server
gọi nó cuối mỗi vòng lặp selector (`server.py`), nó duyệt các phòng `PLAYING`:

```python
if room.reconnect_deadline is not None:
    if now >= room.reconnect_deadline:
        # đối thủ thắng, reason = "disconnect"
    continue                      # đang tạm dừng, không xét đồng hồ lượt

if room.turn_deadline is not None and now >= room.turn_deadline:
    # người đang tới lượt thua, reason = "timeout"
```

Thứ tự `if` chính là luật "hai đồng hồ không chạy cùng lúc": phòng đang chờ
kết nối lại thì `continue`, không bao giờ rơi xuống nhánh hết giờ lượt.

`tick()` trả về delivery y như một handler bình thường nên `_dispatch` không
cần biết message sinh ra từ đâu. Chỉ có điều delivery từ `tick()` không bao
giờ dùng `targets = []`, vì không có socket nào "vừa gửi".

Khác biệt giữa hai lý do kết thúc:

| | `reason = "timeout"` | `reason = "disconnect"` |
|---|---|---|
| Ai thắng | Đối thủ của người đang tới lượt | Đối thủ của người rớt mạng |
| Elo | Có tính (`score_player`) | Không đổi |
| `matches.result` trong DB | `x_win` / `o_win` | `x_win` / `o_win`, hoặc `aborted` nếu cả hai cùng rớt |

---

## 7. Đồng hồ đi tới client như thế nào

Server **không** phát một message mỗi giây. Nó gửi mốc thời gian kèm theo
message trạng thái, client tự đếm ngược tại chỗ.

| Message | Trường thời gian | Gửi khi |
|---|---|---|
| `game_state` | `turnTimeLimit`, `turnTimeLeft` | Mỗi nước đi, vào phòng, vào xem, quay lại sau khi rớt |
| `game_state` (đang tạm dừng) | thêm `waitingForPlayerId`, `reconnectTimeLeft` | Khi phòng đang chờ ai đó kết nối lại |
| `player_disconnected` | `reconnectTimeLeft` | Ngay khi phát hiện rớt kết nối |
| `match_list` | `turnTimeLeft` mỗi phòng | Khi người dùng xin danh sách trận để vào xem |
| `game_result` | `reason` = `timeout` / `disconnect` / `forfeit` | Khi ván kết thúc |

Phía client (`Code/Client/Caroclient.UI/Form1.cs`): một
`System.Windows.Forms.Timer` chu kỳ 1000 ms trừ dần biến đếm tại chỗ và vẽ
label. `TurnClockTick` chọn đúng một đồng hồ để trừ — đang chờ ai đó quay lại
thì trừ `reconnectSecondsLeft`, ngược lại trừ `turnSecondsLeft` — đúng bằng
quy tắc bên server. Mỗi `game_state` mới ghi đè cả hai biến, nên client lệch
bao nhiêu cũng được kéo về đúng ở nước đi kế tiếp.

**Server là nguồn sự thật duy nhất.** Số trên màn hình chỉ để hiển thị; ván
thắng thua do `tick()` quyết định, không do đồng hồ của client.

---

## 8. Các trường hợp biên

| Tình huống | Server xử lý |
|---|---|
| Rớt mạng khi **không** tới lượt mình | Vẫn mở hạn 60 giây và tạm dừng đồng hồ — đối thủ cũng không bị trừ giờ trong lúc chờ |
| Cả hai cùng rớt | Kết thúc ngay, không ai thắng; client nhận `result = "draw"`, DB ghi `aborted` |
| Khán giả rớt | Chỉ rời `room.spectators`, không ảnh hưởng đồng hồ hay kết quả |
| Rớt khi ván đã `FINISHED` | Không có gì xảy ra, chỉ cập nhật danh sách online |
| Quay lại **sau** khi đã bị xử thua | `_resume_after_reconnect` thấy phòng không còn `PLAYING` → đăng nhập bình thường về sảnh (xem Giới hạn) |
| Chủ động `leave_room` giữa ván | Xử thua ngay, `reason = "forfeit"`, **không** có ân hạn 60 giây |
| Khán giả vào phòng đang tạm dừng | `game_state` mang sẵn `waitingForPlayerId` và `reconnectTimeLeft` nên hiển thị đúng ngay |
| Phòng đang tạm dừng trong `match_list` | Vẫn hiện (status vẫn `playing`) với `turnTimeLeft = 0` |
| Đánh cờ khi phòng đang tạm dừng | `NOT_YOUR_TURN` hoặc `GAME_NOT_ACTIVE`; bàn cờ bị khoá ngay khi ván kết thúc |

---

## 9. Test tương ứng

Handler nhận đồng hồ qua tham số `clock` (mặc định `time.monotonic`), nên test
tiêm đồng hồ giả và "tua" thời gian thay vì ngồi chờ 30 giây thật.

| Test | Kiểm tra |
|---|---|
| `test_turn_timeout_awards_the_win_to_the_opponent` | Chưa hết giờ thì `tick()` im lặng; hết giờ thì đối thủ thắng và Elo đổi |
| `test_each_move_refills_the_thinking_clock` | Mỗi nước đi nạp lại trọn 30 giây |
| `test_disconnect_holds_the_room_and_pauses_the_clock` | Phòng vẫn `PLAYING`, `turn_deadline` về `None`, đối thủ nhận `reconnectTimeLeft` |
| `test_player_reconnects_in_time_and_keeps_playing` | Đăng nhập lại bằng socket mới, nhận đúng bàn cờ đang dở và trọn một lượt mới |
| `test_reconnect_deadline_expires_and_opponent_wins` | Quá hạn thì đối thủ thắng với `reason = "disconnect"` |
| `test_timeout_also_locks_the_board` | Hết giờ thì bàn cờ bị khoá, nước đi sau đó bị từ chối |

Sáu test trên nằm trong `tests/test_message_handler.py`. Ngoài ra:

| Test | Kiểm tra |
|---|---|
| `tests/test_connection_disconnect.py` | TCP reset thành tín hiệu disconnect chứ không làm chết vòng lặp server |
| `tests/demo_live_match.py --scenario reconnect` / `disconnect` | Hai kịch bản chạy một mạch trên TCP thật + PostgreSQL thật |
| `tests/demo_manual.py` | Bảng điều khiển tay: tự gõ lệnh cho hai bot rớt mạng / vào lại, xem từng bản tin tới |

```bash
cd Code/Server
python -m unittest tests.test_message_handler
python -m tests.test_connection_disconnect
```

---

## 10. Giới hạn hiện tại

**Sai số 1 giây.** `tick()` chạy mỗi giây nên người chơi có thể được thêm tối
đa gần 1 giây so với mốc lý thuyết. Chấp nhận được với luật 30/60 giây; muốn
chính xác hơn thì phải đặt timeout của `select()` theo deadline gần nhất.

**Chưa có heartbeat.** Rút dây mạng đột ngột không gửi gói FIN, nên `recv()`
không trả về `b""` và server vẫn coi người đó đang online cho tới khi TCP tự
phát hiện. Nghĩa là đồng hồ 60 giây bắt đầu chạy từ lúc đó chứ không phải từ
lúc rớt mạng thật. Thoát app "sạch" thì phát hiện ngay.

**Người bị xử thua do quá hạn không nhận được `game_result`.** Lúc ván kết
thúc họ đang offline, mà `_room_recipients` chỉ gửi cho người đang online. Khi
đăng nhập lại họ về thẳng sảnh, không có thông báo nào về ván vừa thua. Muốn
sửa thì cần lưu kết quả chưa đọc theo `player_id` và gửi lại lúc `login`.

**Cả hai cùng rớt: DB và client nói khác nhau.** DB ghi `result = "aborted"`
nhưng client nhận `result = "draw"` vì message chỉ có ba giá trị win/lose/draw.
Không sai kết quả, chỉ là thiếu một từ để diễn tả "ván bị bỏ dở".

**Phòng đã kết thúc không được dọn khỏi RAM.** `RoomManager.cleanup_if_done`
chỉ được gọi từ `app/handlers/matchmaking_handlers.py`, mà file đó hiện không
được server nạp. `tick()` vẫn bỏ qua các phòng `FINISHED` ngay từ dòng đầu nên
không ảnh hưởng luật chơi, nhưng chạy lâu thì danh sách phòng phình dần.
