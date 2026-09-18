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
    events = self.sel.select(timeout=None)
    for key, mask in events:
        if key.data is None:
            self._accept(key.fileobj)      # socket lang nghe
        else:
            self._handle_client(key.data, mask)   # socket client
```

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
| `spectate` | `game_state` |
| `leave_room` | `leave_room_result` |
| — | `error` |

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
khi TCP tự phát hiện, có thể mất vài phút. Muốn reconnect đúng hạn thì
cần ping định kỳ và mốc thời gian chờ rõ ràng.

**Buffer gửi không giới hạn.** Client nhận chậm khiến `_send_buff` dồn
mãi mà không có cảnh báo hay log nào.
