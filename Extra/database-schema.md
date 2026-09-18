# Cấu trúc database

Module 3: Database & Queue Writer — Nguyễn Đình Duy Khương

Tài liệu này mô tả ba bảng trong PostgreSQL, các ràng buộc và lý do chọn
từng ràng buộc. Sơ đồ quan hệ xem `er-diagram-database.mmd`, cách dữ liệu
đi từ handler xuống database xem `queue-event-format.md`.

Nguồn chuẩn là `Code/Server/migrations/init.sql` — file này được
PostgreSQL tự chạy lần đầu khởi tạo container (mount vào
`/docker-entrypoint-initdb.d/`). Các model SQLAlchemy trong
`app/models/` ánh xạ 1-1 với nó.

---

## Vì sao khoá chính là BIGSERIAL

Bản thiết kế đầu dùng UUID. Sau đổi sang `BIGSERIAL` — số nguyên tăng dần
do Postgres cấp — vì ba lý do:

- **Dễ đọc khi debug.** `match_id = 12` gõ tay được trong `psql`, còn
  `a3f2...-9c81` thì phải copy paste và vẫn dễ nhầm.
- **Index gọn hơn.** 8 byte thay vì 16, và số tăng dần nên B-tree luôn
  chèn vào cuối, không làm phân mảnh trang.
- **Không cần ứng dụng tự sinh id.** Postgres cấp thì chắc chắn không
  trùng. Nếu để server tự sinh, hai luồng cùng sinh một lúc là phải nghĩ
  tới chuyện đụng nhau.

Đánh đổi: id đoán được (biết `match_id=12` thì đoán ra 13). Với đồ án
trong mạng LAN thì không thành vấn đề.

---

## Bảng `users`

Lưu tài khoản người chơi. `id` chính là `playerId` trong message JSON
(gửi đi dưới dạng chuỗi số).

| Cột | Kiểu | Ghi chú |
|---|---|---|
| `id` | `BIGSERIAL` PK | Postgres cấp |
| `username` | `VARCHAR(32)` NOT NULL UNIQUE | tối thiểu 3 ký tự |
| `password_hash` | `VARCHAR(255)` | cho phép NULL |
| `ranking` | `INT` | mặc định 0 |
| `created_at` | `TIMESTAMPTZ` NOT NULL | mặc định `now()` |
| `last_login_at` | `TIMESTAMPTZ` | NULL khi chưa đăng nhập lần nào |

Cột tên là `password_hash` chứ không phải `password` — đặt tên như vậy để
không ai vô tình gán mật khẩu gốc vào. Server băm bằng bcrypt trước khi
ghi (`hash_password` trong `app/handlers/message_handlers.py`).

Ràng buộc `chk_users_username_len` bắt `char_length(username) >= 3`.
Client đã kiểm tra rồi, nhưng client có thể bị sửa hoặc bị bỏ qua — chốt
thêm ở tầng database thì dữ liệu bẩn không lọt vào được bằng đường nào.

---

## Bảng `matches`

Lịch sử các ván đấu. `id` tương ứng `matchId` / `room_id` trong message.

| Cột | Kiểu | Ghi chú |
|---|---|---|
| `id` | `BIGSERIAL` PK | dùng luôn làm `room_id` bên RoomManager |
| `player_x_id` | `BIGINT` FK → `users.id` | người đi X |
| `player_o_id` | `BIGINT` FK → `users.id` | người đi O |
| `status` | `VARCHAR(16)` NOT NULL | `waiting`/`playing`/`finished`/`aborted` |
| `result` | `VARCHAR(16)` | `x_win`/`o_win`/`draw`/`aborted`, NULL khi chưa xong |
| `winner_id` | `BIGINT` FK → `users.id` | NULL nếu hoà hoặc chưa kết thúc |
| `board_rows` / `board_cols` | `SMALLINT` | mặc định 15 |
| `win_condition` | `SMALLINT` | mặc định 5 quân liên tiếp |
| `created_at` | `TIMESTAMPTZ` NOT NULL | mặc định `now()` |
| `started_at` | `TIMESTAMPTZ` | NULL khi còn `waiting` |
| `ended_at` | `TIMESTAMPTZ` | NULL khi chưa kết thúc |

Hàng `matches` được INSERT **đồng bộ** ngay lúc chấp nhận lời mời, khác
với `moves` và kết quả (đi qua hàng đợi). Lý do: cả ván đấu phụ thuộc vào
`id` mà Postgres trả về, không thể vừa tạo phòng vừa chờ id tới sau. Bù
lại, mỗi ván chỉ chạy đúng một lần nên không nghẽn vòng lặp đáng kể.

Lưu `board_rows`, `board_cols`, `win_condition` vào từng ván thay vì
hằng số toàn cục: ván cũ phát lại vẫn đúng luật lúc nó diễn ra, kể cả sau
này nhóm đổi bàn cờ sang 19×19.

### Vì sao `result` là `x_win`/`o_win` chứ không phải `win`/`lose`

`win`/`lose` phụ thuộc góc nhìn — cùng một ván, X thấy win còn O thấy
lose. Database lưu sự thật khách quan, server tự quy đổi khi gửi message
`game_result` cho từng người.

### Các ràng buộc CHECK

| Ràng buộc | Chặn điều gì |
|---|---|
| `chk_matches_diff_players` | `player_x_id <> player_o_id` — không tự đấu với chính mình |
| `chk_matches_status` | status ngoài 4 giá trị hợp lệ (khớp `RoomStatus` module 4) |
| `chk_matches_result` | result ngoài 4 giá trị hợp lệ |
| `chk_matches_finished_has_result` | ván `finished` mà thiếu `result` hoặc `ended_at` |
| `chk_matches_winner_consistency` | có người thắng nhưng `winner_id` rỗng |
| `chk_matches_time_order` | `ended_at` sớm hơn `started_at` |

Bốn ràng buộc cuối là loại dễ bị bỏ sót nhất: chúng không chặn dữ liệu
sai định dạng, mà chặn dữ liệu *mâu thuẫn*. Một ván ghi `finished` nhưng
`result` rỗng sẽ không làm gì hỏng ngay — nó chỉ làm sai thống kê vài
tuần sau, lúc đã không còn lần ra nguyên nhân.

---

## Bảng `moves`

Từng nước đi theo thứ tự, dùng để phát lại ván và để reconnect dựng lại
bàn cờ.

| Cột | Kiểu | Ghi chú |
|---|---|---|
| `id` | `BIGSERIAL` PK | |
| `match_id` | `BIGINT` FK → `matches.id` | ON DELETE CASCADE |
| `player_id` | `BIGINT` FK → `users.id` | ON DELETE RESTRICT |
| `row_idx` | `SMALLINT` NOT NULL | toạ độ dòng, `>= 0` |
| `col_idx` | `SMALLINT` NOT NULL | toạ độ cột, `>= 0` |
| `move_index` | `INTEGER` NOT NULL | thứ tự nước đi, bắt đầu từ 1 |
| `created_at` | `TIMESTAMPTZ` NOT NULL | mặc định `now()` |

Tên cột là `row_idx`/`col_idx` chứ không phải `row`/`col` vì `ROW` là từ
khoá của SQL, không dùng làm tên cột được.

`move_index` lẻ là lượt X, chẵn là lượt O. Nhờ vậy không cần lưu thêm cột
"quân nào" — suy ra được từ số thứ tự, và không bao giờ lệch.

### Hai ràng buộc UNIQUE

| Ràng buộc | Chặn điều gì |
|---|---|
| `uq_moves_match_order` — `(match_id, move_index)` | hai nước cùng số thứ tự trong một ván |
| `uq_moves_match_cell` — `(match_id, row_idx, col_idx)` | đánh hai lần vào cùng một ô |

Game Engine đã kiểm tra ô trống trước khi chấp nhận nước đi, nên về lý
thuyết hai ràng buộc này không bao giờ chạm tới. Giữ lại vì chúng là
lưới an toàn cuối: nếu logic có lỗi hoặc có race condition, database từ
chối ghi và event rơi vào dead-letter — thấy được ngay, thay vì âm thầm
làm hỏng ván đấu.

UNIQUE tự tạo index nên không cần khai báo index riêng cho hai cặp cột
này.

---

## Quan hệ và hành vi xoá

| Quan hệ | ON DELETE | Vì sao |
|---|---|---|
| `moves.match_id` → `matches.id` | `CASCADE` | Xoá một ván thì các nước đi của nó vô nghĩa, xoá theo là đúng |
| `moves.player_id` → `users.id` | `RESTRICT` | Chặn xoá user còn nước đi trong lịch sử — mất người chơi là ván đấu mất luôn ý nghĩa |
| `matches.player_x_id` / `player_o_id` | `RESTRICT` | Như trên |
| `matches.winner_id` | `SET NULL` | Người thắng mất đi vẫn không xoá cả ván; chỉ bỏ trống ô người thắng |

Ba hành vi khác nhau vì ba câu hỏi khác nhau: "dữ liệu con còn ý nghĩa
khi cha mất không?" Nước đi thì không (CASCADE), ván đấu thì có
(RESTRICT), còn tham chiếu người thắng chỉ là thông tin phụ (SET NULL).

---

## Index

```sql
CREATE INDEX idx_matches_status ON matches (status)
    WHERE status IN ('waiting', 'playing');
```

Đây là **partial index** — chỉ đánh chỉ mục các ván đang diễn ra, phục vụ
màn hình cho khán giả chọn trận. Các ván `finished` chiếm đa số theo thời
gian nhưng không bao giờ xuất hiện trong truy vấn này, nên loại chúng ra
giữ index nhỏ và nhanh.

---

## Kết nối tới database

`app/config.py` chọn chuỗi kết nối theo môi trường:

```python
IS_DOCKER = os.getenv("RUNNING_IN_DOCKER", "false").lower() == "true"
DATABASE_URL = os.getenv("CARO_DB_DOCKER") if IS_DOCKER \
               else os.getenv("OUT_CARO_DATABASE_URL")
```

Khác nhau ở phần host: trong Docker network là `db`, chạy local là
`localhost`. Cả hai đọc từ `.env`, không hard-code vào source.

`app/db.py` dựng engine dùng chung:

| Tham số | Tác dụng |
|---|---|
| `pool_pre_ping=True` | Ping thử trước khi dùng lại connection trong pool, tránh gặp connection đã chết |
| `pool_recycle=1800` | Bỏ connection sau 30 phút, tránh bị Postgres hoặc firewall cắt giữa chừng |
| `scoped_session` | Mỗi thread có session riêng — cần thiết vì DB Writer chạy ở thread khác vòng lặp selectors |

---

## Giới hạn hiện tại

**Model `User` lệch so với `init.sql`.** `created_at` và `last_login_at`
khai `DateTime` (không timezone) trong khi SQL là `TIMESTAMPTZ`, và
`last_login_at` thiếu `nullable=True` dù SQL cho phép NULL. Hai model
`Match` và `Move` thì đã khớp. Hiện chưa gây lỗi vì bảng do `init.sql`
tạo chứ không phải `init_db()`, nhưng ai gọi `init_db()` trên database
trống sẽ nhận schema khác.

**`echo=True` đang bật.** Mọi câu SQL bị in ra stdout — tiện lúc debug,
nhưng lúc demo thì log nước đi trộn lẫn với log server. Nên chuyển thành
biến môi trường.

**Chưa có công cụ migration.** `init.sql` chỉ chạy đúng lần đầu tạo
container. Đổi schema sau đó phải xoá volume và chạy lại từ đầu, mất hết
dữ liệu. Với đồ án thì chấp nhận được, nhưng cần biết để không mất dữ
liệu kiểm thử ngoài ý muốn.
