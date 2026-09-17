# Format event qua Queue — Mục 6

Module 3: Database & Queue Writer — Nguyễn Đình Duy Khương

Tài liệu này mô tả cấu trúc dữ liệu đi qua hàng đợi trung gian giữa
handler và DB Writer. Sơ đồ luồng xem ở `queue-event-flow.mmd`.

---

## Vì sao cần hàng đợi

Server chạy trên một vòng lặp `selectors` duy nhất
(`app/network/server.py`). Nếu handler ngồi chờ database commit thì cả
server đứng hình với mọi client, chứ không riêng người vừa đánh.

Ngoài ra, nhiều thread cùng ghi trực tiếp vào database dễ gây race
condition và làm đảo thứ tự nước đi.

Giải pháp: handler bỏ "việc cần ghi" vào hàng đợi rồi đi tiếp ngay.
Một thread DB Writer duy nhất lấy từng việc ra ghi tuần tự.

---

## Cấu trúc event

Mỗi event là một `dict` gồm đúng hai trường:

```python
{
    "op":   "<loai thao tac>",   # str
    "data": { ... }              # dict, noi dung tuy theo op
}
```

Trường `op` cho DB Writer biết ghi vào bảng nào. Trường `data` chứa
tham số.

---

## Các loại `op`

### `insert_move` — ghi một nước đi

Handler gọi khi Game Logic đã xác nhận nước đi hợp lệ.

```python
db_queue.put(Op.INSERT_MOVE, {
    "match_id":   12,      # int, khoa ngoai -> matches.id
    "player_id":  3,       # int, khoa ngoai -> users.id
    "row_idx":    7,       # int, toa do dong, >= 0
    "col_idx":    7,       # int, toa do cot, >= 0
    "move_index": 1,       # int, thu tu nuoc di, bat dau tu 1
})
```

`move_index` lẻ là lượt X, chẵn là lượt O. Database có ràng buộc
`UNIQUE(match_id, move_index)` và `UNIQUE(match_id, row_idx, col_idx)`
nên không thể ghi trùng.

### `update_match_result` — kết thúc ván

Handler gọi khi Game Logic xác định thắng/thua/hòa.

```python
db_queue.put(Op.UPDATE_MATCH_RESULT, {
    "match_id":  12,
    "status":    "finished",      # waiting|playing|finished|aborted
    "result":    "x_win",         # x_win|o_win|draw|aborted
    "winner_id": 3,               # int hoac None neu hoa
    "ended_at":  datetime.now(),
})
```

`result` lưu `x_win`/`o_win` thay vì `win`/`lose`, vì win/lose phụ thuộc
góc nhìn người chơi — cùng một ván, X thấy win còn O thấy lose. Database
lưu sự thật khách quan, server tự quy đổi khi gửi message `game_result`.

---

## Đặc tính của hàng đợi

| Đặc tính | Giá trị |
|---|---|
| Kiểu | `queue.Queue` (thread-safe sẵn) |
| Thứ tự | FIFO — nước đi số 5 luôn ghi trước số 6 |
| `put()` | Trả về ngay, không chờ database |
| `get()` | Timeout 0.5s để DB Writer kiểm tra cờ dừng |
| Số thread ghi | Đúng 1 — tránh race condition |

---

## Xử lý khi ghi thất bại

DB Writer phân biệt hai loại lỗi vì cách xử lý khác nhau hoàn toàn:

**`IntegrityError`** — vi phạm ràng buộc (đánh trùng ô, `move_index`
trùng, khóa ngoại không tồn tại). Đây là dữ liệu sai, không phải
database sai. Thử lại bao nhiêu lần cũng hỏng, chỉ làm chậm những event
đứng sau. Bỏ ngay, ghi vào dead-letter.

**`OperationalError`** — mất kết nối, database đang khởi động lại, hết
connection. Lỗi tạm thời, thử lại có ích. Thử tối đa 3 lần, chờ tăng dần
0.5s → 1s → 2s. Mỗi lần thử phải tạo lại session vì session cũ đã hỏng.

Thread ngủ không làm treo server: handler vẫn `put()` vào hàng đợi bình
thường, người chơi không thấy gì khác.

---

## Dead-letter

Event không ghi được sau 3 lần sẽ được ghi ra `logs/db_failed.jsonl`,
mỗi dòng một JSON:

```json
{"thoi_diem": "2026-09-17 14:32:10", "op": "insert_move",
 "data": {"match_id": 12, "player_id": 3, "row_idx": 7,
          "col_idx": 7, "move_index": 1},
 "ly_do": "OperationalError: connection closed"}
```

Mất dữ liệu lặng lẽ là điều tệ nhất — ván đấu sẽ thiếu nước đi mà không
ai biết. File này để đối chiếu khi kiểm thử và khôi phục nếu cần.

---

## Giới hạn hiện tại

Hàng đợi chưa đặt `maxsize`. Nếu database chết kéo dài, event dồn vào
RAM không giới hạn. Cần cân nhắc đặt trần (ví dụ 1000 event) và bỏ event
mới khi đầy, để một sự cố database không kéo sập cả server.