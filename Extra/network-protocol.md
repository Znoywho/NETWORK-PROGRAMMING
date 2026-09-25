# Format message qua Socket — Module 1: Network

Module 1: Network & Protocol — Lê Thiên Hạo

Tài liệu này mô tả cách client và server trao đổi dữ liệu qua TCP:
cách một message được đóng gói, vòng lặp xử lý kết nối, và cách server
quyết định gửi trả cho ai. Code tương ứng nằm ở `app/network/`.

Phần ghi xuống database xem `queue-event-format.md`.

---

## Vì sao cần đóng khung message

TCP là luồng byte, không phải luồng message. Bên gửi gọi `send()` ba
lần không có nghĩa bên nhận sẽ `recv()` được đúng ba lần.

Một lần `sock.recv(4096)` có thể trả về:

- đúng một message — trường hợp may mắn,
- hai message dính liền nhau trong cùng một lần đọc,
- hoặc nửa message, phần còn lại nằm ở lần đọc sau.

JSON không tự phân định ranh giới giúp ta được: `json.loads` trên nửa
chuỗi chỉ ném lỗi, không cho biết còn thiếu bao nhiêu byte.

Giải pháp: mỗi message được dán sẵn một header ghi rõ độ dài phần thân.
Bên nhận đọc 4 byte đầu là biết phải chờ thêm bao nhiêu byte nữa.

---

## Cấu trúc frame

```text
┌──────────────┬─────────────────────┐
│ 4 bytes (>I) │  N bytes JSON/UTF-8 │
│   N = len    │      payload        │
└──────────────┴─────────────────────┘
```

| Thành phần | Chi tiết |
|---|---|
| Header | 4 byte, unsigned 32-bit, big-endian (`struct.pack(">I", n)`) |
| Body | JSON, mã hoá UTF-8, `ensure_ascii=False` nên tiếng Việt giữ nguyên |

Big-endian (`>`) là thứ tự byte quy ước của mạng. Chọn nó để client C#
và server Python hiểu giống nhau mà không phụ thuộc kiến trúc CPU.

`app/network/protocol.py` chỉ làm đúng hai việc, hoàn toàn không đụng
tới socket:

```python
encode_frame(payload: dict) -> bytes
decode_frames(buffer: bytearray) -> tuple[list[dict], bytearray]
```

Vì tách rời như vậy nên cùng một quy ước dùng được cho cả hai phía, và
kiểm thử được mà không cần mở socket thật.

`decode_frames` trả về **hai** thứ: danh sách message đã đọc trọn, và
phần byte thừa chưa đủ một frame. Phần thừa được giữ lại trong buffer,
chờ lần `recv` sau ghép tiếp — đây chính là chỗ xử lý message bị cắt
đôi.

---

## Vòng lặp selectors

Server chạy trên **một luồng duy nhất** với `selectors.DefaultSelector`
(`app/network/server.py`). Không tạo thread cho mỗi client.

```python
while True:
    events = self.sel.select(timeout=TICK_INTERVAL_SECONDS)
    for key, mask in events:
        if key.data is None:
            self._accept(key.fileobj)      # socket lang nghe
        else:
            self._handle_client(key.data, mask)   # socket client

    self._dispatch(self.message_handler.tick())   # dong ho cac phong
```

`select` có `timeout` chứ không chờ vô hạn: mỗi giây vòng lặp thức dậy
một lần để `tick()` đối chiếu đồng hồ của các phòng. Hết giờ suy nghĩ
hay hết hạn kết nối lại đều là sự kiện *không* có client nào gửi gì
lên, nên nếu ngồi chờ socket thì không bao giờ phát hiện được.

Cách phân biệt: socket lắng nghe được đăng ký với `data=None`, socket
client được đăng ký kèm đối tượng `Connection`. Nhìn `key.data` là biết
sự kiện thuộc loại nào.

| Sự kiện | Server làm gì |
|---|---|
| `EVENT_READ` trên listener | `accept()`, đặt non-blocking, đăng ký vào selector |
| `EVENT_READ` trên client | `recv()` → giải frame → đưa từng message cho handler |
| `EVENT_WRITE` trên client | `flush()` phần còn tồn trong buffer gửi |
| `recv()` ném `RuntimeError` | client đã đóng → dọn phòng, huỷ đăng ký, đóng socket |

Vì sao một luồng: toàn bộ trạng thái phòng và người chơi nằm trong RAM
của đúng luồng đó, nên không cần khoá và không có race condition. Đổi
lại, không được phép làm việc gì chậm ngay trong vòng lặp — việc chậm
nhất là ghi database, và nó đã được đẩy sang hàng đợi.

---

## Connection — vòng đời một client

Mỗi client có một `Connection` (`app/network/connection.py`) giữ socket,
địa chỉ, hai buffer và `player_id` sau khi đăng nhập.

**`recv()`** — đọc tối đa 4096 byte.

- `BlockingIOError`: chưa có dữ liệu, trả về danh sách rỗng.
- Nhận được `b""`: peer đã đóng, ném `RuntimeError("Peer closed.")`.
- `ConnectionError` / `OSError` (TCP reset — client bị kill, rút dây):
  đổi thành `RuntimeError("Peer connection lost.")`. Nếu để lỗi gốc bay
  lên thì `_handle_client` không bắt được và cả vòng lặp selector chết
  theo một client. Test: `tests/test_connection_disconnect.py`.
- Ngược lại: nối vào `_recv_buff`, gọi `decode_frames`, trả về các
  message đọc trọn.

**`send(payload)`** — *không* ghi thẳng ra socket. Frame được nối vào
`_send_buff`, và nếu buffer vừa từ rỗng chuyển sang có dữ liệu thì bật
thêm `EVENT_WRITE` để selector nhắc lại khi socket sẵn sàng ghi.

**`flush()`** — `sock.send()` trả về số byte *thực sự* gửi được, có thể
ít hơn buffer. Phần chưa gửi giữ nguyên, chờ vòng sau. Lỗi kết nối thì
đóng luôn.

Vì sao phải đệm: socket non-blocking khi bộ đệm kernel đầy sẽ từ chối
nhận thêm. Nếu ngồi chờ ghi cho bằng được thì cả server đứng hình vì một
client mạng yếu.

**`close()`** — có cờ `closed` chống gọi hai lần, huỷ đăng ký khỏi
selector rồi đóng socket. Cả hai bước đều bọc try/except vì socket có
thể đã bị đóng từ phía kia.

---

## Luồng một message đi hết vòng

Lấy một nước cờ làm ví dụ, đi từ byte trên dây mạng tới byte trả về:

```text
  CLIENT ──► [4B len][{"type":"make_move",...}] ──► TCP
                                                    │
 ┌──────────────────────────────────────────────────▼──────────────────┐
 │ TẦNG MẠNG — app/network/                                            │
 │                                                                     │
 │  server.py   sel.select() báo EVENT_READ trên socket này            │
 │      │                                                              │
 │  connection.py  recv()  đọc ≤4096 byte, nối vào _recv_buff          │
 │      │                                                              │
 │  protocol.py  decode_frames()  cắt buffer thành list[dict]          │
 │      │          (thiếu byte → giữ lại chờ lần recv sau)             │
 └──────┼──────────────────────────────────────────────────────────────┘
        ▼  dict thuần, không còn dấu vết socket
 ┌─────────────────────────────────────────────────────────────────────┐
 │ TẦNG LUẬT — app/handlers/message_handlers.py                        │
 │                                                                     │
 │  handle(msg, sock) → tra player_id → _make_move_handler()           │
 │      │  kiểm tra lượt, ô trống, trong bàn cờ                        │
 │      │  đẩy nước đi vào hàng đợi DB (không chờ commit)  ──────┐     │
 │      │  _start_turn() nạp lại đồng hồ                        │     │
 │      ▼                                                       │     │
 │  trả về [{"targets": ["3","7"], "payload": {...}}]           │     │
 └──────┼───────────────────────────────────────────────────────┼─────┘
        ▼  chỉ là danh sách dict                                ▼
 ┌──────────────────────────────────────────────┐      ┌───────────────┐
 │ TẦNG MẠNG (chiều ra) — server.py             │      │ DBWriter      │
 │                                              │      │ (thread riêng)│
 │  _dispatch()  đọc targets → tra PlayerManager│      │ commit vào    │
 │      │        lấy Connection tương ứng       │      │ PostgreSQL    │
 │  connection.py  send() → nối vào _send_buff  │      └───────────────┘
 │      │          bật thêm EVENT_WRITE         │
 │  flush()  khi socket sẵn sàng ghi ──────────────► TCP ──► CLIENT
 └──────────────────────────────────────────────┘
```

Bốn điều đáng chú ý:

1. **Không tầng nào nhảy cóc.** `protocol.py` không biết socket,
   `message_handlers.py` không biết socket, `server.py` không biết luật
   cờ. Mỗi tầng chỉ nói chuyện với tầng kề.
2. **Handler không tự gửi.** Nó trả về "delivery", `_dispatch` mới là
   nơi duy nhất chạm vào socket. Nhờ vậy test luật chơi bằng dict thuần,
   không cần dựng server thật.
3. **Ghi database không nằm trên đường trả lời.** Handler đẩy event vào
   hàng đợi rồi đi tiếp, client nhận nước cờ trước khi DB commit xong.
4. **Chiều ra là bất đồng bộ.** `send()` chỉ xếp byte vào buffer; byte
   thật sự ra dây ở `flush()`, có thể ở vòng lặp sau.

---

## Quản lý connection — ai giữ cái gì

Một người chơi được ba nơi khác nhau ghi nhớ, mỗi nơi một mục đích:

```text
        ┌──────────────────────────────────────────────┐
        │ selectors            fd → Connection         │
        │   biết socket nào vừa có dữ liệu             │
        └───────────────────┬──────────────────────────┘
                            │ data=
                            ▼
        ┌──────────────────────────────────────────────┐
        │ Connection           socket + 2 buffer       │
        │   đọc/ghi byte, đóng khung, đóng socket      │
        └───────────────────▲──────────────────────────┘
                            │ .connection
        ┌───────────────────┴──────────────────────────┐
        │ PlayerManager        player_id → Player      │
        │   ai đang online, đang ở phòng nào           │
        └───────────────────▲──────────────────────────┘
                            │ tra ngược khi cần gửi
        ┌───────────────────┴──────────────────────────┐
        │ RoomManager          room_id → Room          │
        │   Room chỉ giữ player_id, KHÔNG giữ socket   │
        └──────────────────────────────────────────────┘
```

| Sổ ghi | Khoá → giá trị | Ai ghi vào | Ai xoá đi |
|---|---|---|---|
| `selectors.DefaultSelector` | file descriptor → `Connection` | `_accept()` khi có client mới | `Connection.close()` |
| `PlayerManager._players` | `player_id` → `Player` (có `.connection`) | `_login_handler` → `add_player` | `MessageHandler.disconnect()` |
| `Room.player_x` / `player_o` / `spectators` | chỉ lưu `player_id` | `accept_invite`, `spectate` | `_end_game_deliveries`, `leave_room` |
| `MessageHandler._awaiting_reconnect` | `player_id` → `room_id` | `disconnect()` khi đang trong ván | `_resume_after_reconnect` hoặc khi ván kết thúc |

**Ba bất biến của cách chia này:**

1. **Phòng không bao giờ giữ socket.** `Room` chỉ lưu `player_id` dạng
   chuỗi. Nhờ vậy người chơi rớt mạng rồi vào lại bằng một socket hoàn
   toàn mới mà phòng không cần sửa gì — chỉ `PlayerManager` đổi con trỏ
   `connection`. Nếu phòng giữ socket thì mỗi lần kết nối lại phải đi
   vá tất cả nơi đang tham chiếu tới nó.
2. **Chỉ `_dispatch` chạm vào socket.** Tầng luật nói "gửi cho
   player 3 và 7", tầng mạng lo chuyện người đó còn online hay không
   (`_room_recipients` lọc sẵn người đã offline).
3. **Một `player_id` tối đa một kết nối sống.** `_login_handler` chặn
   bằng lỗi `ALREADY_ONLINE`, nên không có chuyện hai socket cùng đánh
   thay một người.

**Định danh gắn vào lúc nào.** Socket vừa `accept` là vô danh — server
chỉ biết địa chỉ IP. Phải tới message `login` thành công thì cặp
`player_id ↔ connection` mới được ghi vào `PlayerManager`. Vì vậy
`handle()` tra ngược socket → `player_id` bằng
`find_player_by_socket()`; tra không ra thì chỉ `login` và `create_user`
được chạy, mọi type khác nhận `UNAUTHENTICATED`.

Hàm tra ngược đó quét tuyến tính qua danh sách người online. Với quy mô
đồ án thì không đáng kể; muốn gọn hơn thì giữ thêm một dict
`connection → player_id`. (Field `Connection.player_id` được khai báo
sẵn cho mục đích này nhưng hiện chưa dùng tới — định danh đang nằm
hoàn toàn ở `PlayerManager`.)

**Vòng đời một danh tính:**

| Mốc | `selectors` | `PlayerManager` | `Room` |
|---|---|---|---|
| Client kết nối | thêm `Connection` | — | — |
| `login` thành công | không đổi | thêm `player_id → Player` | — |
| Vào phòng đấu | không đổi | status = `playing` | thêm `player_id` |
| Rớt kết nối | huỷ đăng ký, đóng socket | **xoá** `player_id` | **giữ nguyên** |
| `login` lại (socket mới) | thêm `Connection` mới | thêm lại `player_id`, trỏ tới socket mới | không đổi |

Hàng áp chót là điểm mấu chốt của tính năng kết nối lại: người chơi biến
mất khỏi danh sách online nhưng phòng vẫn nhớ họ, nên chỉ cần đăng nhập
lại là ghép về đúng ván đang dở. Chi tiết đồng hồ 60 giây xem
`dong-ho-tran-dau.md`.

---

## Đồng hồ — phần tầng mạng cần biết

Vòng lặp `selectors` gọi `tick()` ở cuối mỗi vòng (`sel.select(timeout=1.0)`
nên vòng lặp tự thức dậy mỗi giây kể cả khi không ai gửi gì). `tick()` là nơi
duy nhất thời gian trôi qua trở thành message: nó trả về delivery y như một
handler bình thường, nên `_dispatch` không cần biết message sinh ra từ đâu —
chỉ có điều delivery từ `tick()` không bao giờ dùng `targets = []` vì không có
socket nào "vừa gửi".

Client **không** nhận một message mỗi giây. `game_state` mang sẵn
`turnTimeLeft` và `turnTimeLimit`, client tự đếm ngược tại chỗ; khán giả vào
giữa trận cũng nhận đúng hai trường đó nên đồng hồ hiện lên khớp ngay. Cách
này giữ đúng tinh thần "chỉ gửi khi trạng thái đổi" thay vì biến server thành
máy phát nhịp.

Toàn bộ luật thời gian — hai hằng số 30/60 giây, việc tạm dừng đồng hồ khi mất
kết nối, bảng chuyển trạng thái, luồng kết nối lại và các trường hợp biên —
nằm ở `dong-ho-tran-dau.md`.

---

## Chọn người nhận — `_dispatch`

Handler **không** tự gửi message. Nó trả về danh sách "delivery":

```python
{
    "targets": None | [] | ["3", "7"],   # ai nhan
    "payload": { "type": "...", ... },   # gui cai gi
}
```

`ServerHandler._dispatch` đọc `targets` và quyết định:

| `targets` | Ý nghĩa | Dùng khi |
|---|---|---|
| `None` | Phát cho mọi người đang online | Danh sách online thay đổi |
| `[]` | Chỉ trả lời đúng socket vừa gửi | `login`, `error`, các `*_result` |
| `["3", "7"]` | Gửi đích danh theo `player_id` | `invite`, `game_state`, `game_result` |

Vì sao tách: handler chỉ lo luật chơi, không cần biết socket nào đang
mở. Nhờ vậy test handler được bằng dict thuần, không cần dựng server.

---

## Các message type hiện có

| Client gửi lên | Server trả về |
|---|---|
| `login`, `create_user` | `login`, `create_user` |
| `online_players` | `online_players` |
| `invite` | `invite_result`, `invite` (cho người được mời) |
| `accept_invite` | `game_state` |
| `reject_invite` | `reject_invite_result`, `invite_rejected` |
| `make_move` | `game_state`, `game_result` |
| `match_list` | `match_list` |
| `spectate` | `game_state` |
| `leave_room` | `leave_room_result` |
| — | `player_disconnected`, `player_reconnected` |
| — | `error` |

`match_list` trả về các trận đang `playing` kèm tên hai người chơi, số
nước đã đánh, số khán giả và thời gian còn lại của lượt — đủ để client
dựng màn hình chọn phòng mà không bắt người dùng gõ tay `room_id`.

`player_disconnected` và `player_reconnected` do server tự gửi cho
những người còn lại trong phòng, không phải trả lời cho request nào.

Schema đầy đủ của từng message ở `Code/Shared/message-schema.json`.

Ba tầng kiểm tra đầu vào trong `MessageHandler.handle`:

1. Không phải `dict` (kể cả frame hỏng JSON được `decode_frames` trả về
   `None`) → `error` mã `INVALID_MESSAGE`.
2. Thiếu trường `type` hoặc `type` không phải chuỗi → `INVALID_MESSAGE`.
3. Chưa đăng nhập mà gọi hành động cần đăng nhập → `UNAUTHENTICATED`.
   Type lạ → `UNKNOWN_MESSAGE_TYPE`.

Một message sai không bao giờ làm chết vòng lặp — nó chỉ đổi thành một
message `error` gửi ngược lại.

---

## Giới hạn hiện tại

**Chưa chặn trần độ dài frame.** Header 4 byte cho phép khai báo tới
4 GB. Một client lỗi (hoặc cố tình) khai độ dài khổng lồ là `_recv_buff`
phình theo cho tới khi hết RAM. Nên đặt trần (ví dụ 1 MB) và đóng kết
nối khi vượt.

**Chưa có heartbeat.** Client rút mạng đột ngột không gửi gói FIN, nên
`recv()` không trả về `b""`. Server vẫn coi người đó đang online cho tới
khi TCP tự phát hiện, có thể mất vài phút — nghĩa là đồng hồ
`reconnect_deadline` chỉ bắt đầu chạy từ lúc đó chứ không phải từ lúc
dây mạng bị rút. Đóng kết nối "sạch" (client thoát, đóng socket) thì
phát hiện ngay. Muốn chính xác trong mọi trường hợp thì cần ping định
kỳ.

**Phiên gắn với tài khoản, không có token.** Kết nối lại nghĩa là đăng
nhập lại bằng username/password; server nhìn `player_id` để ghép người
chơi về đúng phòng đang dở. Đủ dùng cho đồ án, nhưng một session token
sẽ an toàn hơn vì client không phải giữ mật khẩu trong bộ nhớ để tự
đăng nhập lại.

**Buffer gửi không giới hạn.** Client nhận chậm khiến `_send_buff` dồn
mãi mà không có cảnh báo hay log nào.
