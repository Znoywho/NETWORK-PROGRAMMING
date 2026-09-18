# UDM_16 - Game Caro trực tuyến

## Thành viên

| STT | MSSV | Họ và tên | Vai trò |
|---:|---|---|---|
| 1 |089206010393| Lê Thiên Hạo | Leader |
| 2 |082306014560| Phạm Lê Ngọc Hân | Thành viên |
| 3 |067206003213| Trương Tấn Kiệt | Thành viên |
| 4 |077206000886| Ngô Minh Đăng Khoa| Thành viên|
| 5 |084206002822| Trầm Đồng Khởi| Thành viên|
| 6 |052206000320|Nguyễn Đình Duy Khương | Thành viên|

## Giới thiệu

UDM_16 là đồ án Game Caro trực tuyến cho phép nhiều người chơi kết nối đến server, xem danh sách người chơi đang online, mời đấu, tham gia trận đấu và đồng bộ trạng thái bàn cờ theo thời gian thực.

Mục tiêu của project là xây dựng một hệ thống chơi Caro theo mô hình client-server, trong đó server chịu trách nhiệm quản lý kết nối, phòng đấu, lượt chơi, trạng thái trận đấu, kết quả và lịch sử ván chơi.

## Kiến trúc hệ thống

- Mô hình: Client-Server.
- Server: Python, socket + `selectors` (một luồng duy nhất), SQLAlchemy, PostgreSQL.
- Client: C#/.NET — thư viện `CaroClient.Core`, giao diện WinForms `Caroclient.UI`, và một client dòng lệnh để kiểm thử.
- Shared: schema message dùng chung giữa client và server.
- Protocol: TCP. Mỗi message đóng khung bằng header 4 byte big-endian ghi độ dài, tiếp theo là thân JSON mã hoá UTF-8.
- Port mặc định của server: `8765`.
- Port PostgreSQL: `5432` trong Docker network, ánh xạ ra host là `5433`.

```text
NETPRO/
├── Code/
│   ├── Server/
│   │   ├── app/
│   │   │   ├── ai/              # chua co noi dung
│   │   │   ├── game/            # luat co caro, kiem tra thang thua
│   │   │   ├── handlers/        # xu ly tung loai message
│   │   │   ├── matchmaking/     # quan ly nguoi choi, phong, loi moi
│   │   │   ├── models/          # model SQLAlchemy + dataclass trong RAM
│   │   │   ├── network/         # socket, framing, vong lap selectors
│   │   │   ├── queue/           # hang doi ghi database + DB writer
│   │   │   ├── ui/              # man hinh theo doi server trong terminal
│   │   │   ├── config.py
│   │   │   ├── db.py
│   │   │   └── main.py
│   │   ├── migrations/init.sql
│   │   ├── notebook/
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── Client/
│   │   ├── CaroClient.Core/        # ket noi, framing, kieu message
│   │   ├── Caroclient.UI/          # giao dien WinForms
│   │   ├── CaroClient.ConsoleTest/ # client dong lenh de kiem thu
│   │   └── global.json
│   ├── Shared/
│   │   └── message-schema.json
│   ├── docker-compose.yml
│   └── requirements.md
├── DOCX/
├── PPTX/
└── Extra/
```

## Cấu trúc message

Client và server trao đổi dữ liệu bằng JSON qua TCP socket. Vì TCP là luồng byte chứ không phải luồng message, mỗi message được dán sẵn header 4 byte ghi độ dài phần thân:

```text
┌──────────────┬─────────────────────┐
│ 4 bytes (>I) │  N bytes JSON/UTF-8 │
└──────────────┴─────────────────────┘
```

Mỗi message có trường `type` xác định loại yêu cầu hoặc sự kiện.

Ví dụ:

```json
{
  "type": "make_move",
  "room_id": "12",
  "playerId": "3",
  "row": 7,
  "col": 8
}
```

Client gửi lên server:

- `login`, `create_user`: đăng nhập và đăng ký tài khoản.
- `online_players`: xin danh sách người chơi đang online.
- `invite`, `accept_invite`, `reject_invite`: mời đấu và trả lời lời mời.
- `make_move`: đánh một nước cờ.
- `spectate`: vào xem một trận đấu.
- `leave_room`: rời phòng.

Server gửi về client:

- `login`, `create_user`: kết quả đăng nhập / đăng ký kèm `playerId`.
- `online_players`: danh sách online (server tự broadcast mỗi khi danh sách đổi).
- `invite`: báo cho người được mời. `invite_result`, `invite_rejected`, `reject_invite_result`: kết quả lời mời.
- `game_state`: trạng thái bàn cờ hiện tại.
- `game_result`: thắng, thua hoặc hòa.
- `leave_room_result`: kết quả rời phòng.
- `error`: message không hợp lệ hoặc hành động bị từ chối.

Schema đầy đủ của từng message ở `Code/Shared/message-schema.json`. Giải thích chi tiết cách đóng khung và cách server chọn người nhận ở `Extra/network-protocol.md`.

## Yêu cầu môi trường

- Hệ điều hành: Windows, Linux hoặc macOS.
- Python: 3.12 trở lên.
- .NET SDK: 10.0 theo `Code/Client/global.json`.
- Docker và Docker Compose để chạy server kèm database.
- PostgreSQL 18 được chạy thông qua Docker Compose.

Dependency server (`Code/Server/requirements.txt`):

- sqlalchemy — ORM và quản lý connection pool
- psycopg2-binary, asyncpg — driver PostgreSQL
- bcrypt — băm mật khẩu
- python-dotenv — đọc file `.env`
- numpy, pandas, scikit-learn — phục vụ phần AI trong `notebook/`

## Cài đặt

Clone repository về máy:

```bash
git clone <repository-url>
cd NETPRO
```

Cài dependency cho server nếu chạy trực tiếp bằng Python:

```bash
cd Code/Server
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Trên Windows PowerShell:

```powershell
cd Code/Server
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Hướng dẫn chạy

### Server

File `docker-compose.yml` nằm ở thư mục `Code/`, không phải `Code/Server/`:

```bash
cd Code
docker compose up --build
```

Lệnh này dựng hai container: `caro-db` (PostgreSQL, tự chạy `migrations/init.sql` lần đầu khởi tạo) và `caro-server` (chỉ khởi động sau khi healthcheck của database qua).

Nếu chạy trực tiếp bằng Python, cần có sẵn một PostgreSQL đang chạy và biến `OUT_CARO_DATABASE_URL` trỏ đúng vào nó:

```bash
cd Code/Server
python -m app.main
```

Server lắng nghe ở `0.0.0.0:8765` (khai báo trong `app/main.py`).

### Client

Giao diện WinForms (chỉ chạy được trên Windows):

```bash
cd Code/Client/Caroclient.UI
dotnet run
```

Client dòng lệnh để kiểm thử kết nối:

```bash
cd Code/Client/CaroClient.ConsoleTest
dotnet run
```

## Cấu hình

Các tham số cấu hình bằng file `.env` trong `Code/Server/`. Không commit file `.env` lên repository.

```env
# Chuoi ket noi khi server chay trong Docker (host la ten service `db`)
CARO_DB_DOCKER=postgresql://<user>:<password>@db:5432/<database>

# Chuoi ket noi khi chay truc tiep bang Python tren may that
OUT_CARO_DATABASE_URL=postgresql://<user>:<password>@localhost:5433/<database>
```

Thay `<user>`, `<password>`, `<database>` bằng thông tin nhóm tự đặt trong `docker-compose.yml`. Không ghi mật khẩu thật vào tài liệu.

`app/config.py` chọn một trong hai dựa vào biến `RUNNING_IN_DOCKER`, biến này do `docker-compose.yml` tự đặt thành `true` nên không cần khai trong `.env`.

Thông tin database khai trong `docker-compose.yml` (mục `db.environment`):

- Database, user, password: xem trực tiếp trong `docker-compose.yml`
- Host: `db` khi chạy trong Docker network, `localhost` khi chạy ngoài
- Port: `5432` trong Docker network, ánh xạ ra host là `5433`

## Chức năng

- [x] Client kết nối đến server.
- [x] Hiển thị danh sách người chơi đang online.
- [x] Gửi lời mời thách đấu.
- [x] Chấp nhận hoặc từ chối lời mời.
- [x] Tạo phòng đấu và quản lý nhiều trận đấu đồng thời.
- [x] Đồng bộ trạng thái bàn cờ theo thời gian thực.
- [x] Kiểm tra tính hợp lệ của nước đi.
- [x] Kiểm tra kết quả thắng, thua hoặc hòa.
- [x] Lưu lịch sử và kết quả trận đấu.
- [x] Cho phép khán giả xem trận đấu đang diễn ra.
- [x] Phân biệt quyền của người chơi và khán giả.
- [ ] Giới hạn thời gian suy nghĩ cho mỗi lượt.
- [ ] Cho phép người chơi kết nối lại trong thời gian cho phép.
- [ ] Xem danh sách các trận đang diễn ra để chọn phòng khán giả.

## Kiểm thử

Test hiện có trong `Code/Server/`:

```bash
cd Code/Server
python -m unittest tests.test_message_handler   # dang unittest
python tests/test_room_cleanup.py               # dang script
python app/queue/test_queue.py
python app/queue/test_db_writer.py
```

Các nhóm kiểm thử dự kiến:

- Functional test: đăng nhập, mời đấu, đánh cờ, kết thúc trận.
- Test dữ liệu không hợp lệ: message sai format, đánh vào ô đã có quân, đánh sai lượt.
- Test mất kết nối: client mất kết nối, rời phòng.
- Stress test: nhiều client kết nối đồng thời.
- Performance test: đo thời gian phản hồi khi nhiều trận đấu diễn ra cùng lúc.

Bằng chứng kiểm thử, hình ảnh, video demo và log lưu tại `Extra/`.

## Tài liệu

| Tài liệu | Nội dung |
|---|---|
| `Extra/network-protocol.md` | Framing, vòng lặp selectors, vòng đời kết nối, cách chọn người nhận |
| `Extra/database-schema.md` | Ba bảng, ràng buộc, quan hệ, cách kết nối database |
| `Extra/queue-event-format.md` | Format event đi qua hàng đợi xuống DB Writer |
| `Extra/er-diagram-database.mmd` | Sơ đồ ER (mở bằng GitHub hoặc mermaid.live) |
| `Extra/queue-event-flow.mmd` | Sơ đồ luồng event qua hàng đợi |
| `Code/Shared/message-schema.json` | Schema JSON của toàn bộ message |
| `Code/requirements.md` | Yêu cầu đề bài |

## Demo

- Video demo: cập nhật sau.
- Slide thuyết trình: `PPTX/`.
- Báo cáo: `DOCX/`.

## Giới hạn hiện tại

- Chưa có giới hạn thời gian mỗi lượt và chưa cho phép kết nối lại: người chơi rớt mạng giữa trận thì đối thủ được xử thắng ngay.
- Chưa có message cho client lấy danh sách phòng đang chơi, nên muốn xem trận phải biết trước `room_id`.
- Chưa chặn trần độ dài frame và chưa có heartbeat — xem mục "Giới hạn hiện tại" trong `Extra/network-protocol.md`.
- Model `User` trong `app/models/user.py` lệch kiểu thời gian so với `migrations/init.sql`.
- Chưa có công cụ migration: đổi schema phải xoá volume và tạo lại database từ đầu.
- Test còn ít và phần lớn viết dạng script, chưa gom về một bộ chạy chung.
