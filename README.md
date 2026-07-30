# UDM_16 - Game Caro trực tuyến

## Thành viên

| STT | MSSV | Họ và tên | Vai trò |
|---:|---|---|---|
| 1 |089206010393| Lê Thiên Hạo | Leader |
| 2 |082306014560| Phạm Lê Ngọc Hân | Thành viên |
| 3 |067206003213| Trương Tuấn Kiệt | Thành viên |
| 4 |077206000886| Ngô Minh Đăng Khoa| Thành viên|
| 5 |084206002822| Trầm Đồng Khởi| Thành viên|
| 6 |052206000320|Nguyễn Đình Duy Khương | Thành viên|

## Giới thiệu

UDM_16 là đồ án Game Caro trực tuyến cho phép nhiều người chơi kết nối đến server, xem danh sách người chơi đang online, mời đấu, tham gia trận đấu và đồng bộ trạng thái bàn cờ theo thời gian thực.

Mục tiêu của project là xây dựng một hệ thống chơi Caro theo mô hình client-server, trong đó server chịu trách nhiệm quản lý kết nối, phòng đấu, lượt chơi, trạng thái trận đấu, kết quả và lịch sử ván chơi.

## Kiến trúc hệ thống

- Mô hình: Client-Server.
- Server: Python, WebSocket, PostgreSQL.
- Client: C#/.NET console client trong giai đoạn kiểm thử.
- Shared: Lưu cấu trúc message/protocol dùng chung giữa client và server.
- Protocol: WebSocket message dạng JSON.
- Port mặc định của server: `8765`.
- Port mặc định của PostgreSQL: `5432`.

```text
NETPRO/
├── Code/
│   ├── Server/
│   │   ├── app/
│   │   ├── migrations/
│   │   ├── Dockerfile
│   │   ├── docker-compose.yml
│   │   └── requirements.txt
│   ├── Client/
│   │   ├── CaroClient.Core/
│   │   └── CaroClient.ConsoleTest/
│   └── Shared/
│       └── message-schema.json
├── DOCX/
├── PPTX/
└── Extra/
```

## Cấu trúc message

Client và server trao đổi dữ liệu bằng JSON thông qua WebSocket. Mỗi message nên có trường `type` để xác định loại yêu cầu hoặc sự kiện.

Ví dụ:

```json
{
  "type": "make_move",
  "matchId": "match-001",
  "playerId": "player-001",
  "row": 7,
  "col": 8
}
```

Một số loại message dự kiến:

- `login`: người chơi đăng nhập vào server.
- `online_players`: server trả danh sách người chơi đang online.
- `invite`: gửi lời mời thách đấu.
- `accept_invite`: chấp nhận lời mời.
- `reject_invite`: từ chối lời mời.
- `make_move`: người chơi đánh một nước cờ.
- `game_state`: server gửi trạng thái bàn cờ hiện tại.
- `game_result`: server thông báo kết quả thắng, thua hoặc hòa.
- `spectate`: khán giả tham gia xem một trận đấu.
- `leave_room`: người chơi hoặc khán giả rời phòng.
- `error`: server trả lời khi message không hợp lệ.

Chi tiết schema dự kiến lưu tại `Code/Shared/message-schema.json`.

## Yêu cầu môi trường

- Hệ điều hành: Windows, Linux hoặc macOS.
- Python: 3.12 trở lên.
- .NET SDK: 10.0 theo `Code/Client/global.json`.
- Docker và Docker Compose để chạy server kèm database.
- PostgreSQL được chạy thông qua Docker Compose.

Dependency server hiện tại:

- `websockets`
- `asyncpg`
- `python-dotenv`

## Cài đặt

Clone repository về máy:

```bash
git clone <repository-url>
cd NETPRO
```

Cài dependency cho server nếu chạy trực tiếp bằng Python:

```bash
cd Code/Server
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Trên Windows PowerShell:

```powershell
cd Code/Server
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Hướng dẫn chạy

### Server

Server dự kiến chạy bằng Docker Compose:

```bash
cd Code/Server
docker compose up --build
```

Lưu ý: server hiện đang trong giai đoạn khởi tạo. Cần bổ sung source trong `Code/Server/app/` và đảm bảo `docker-compose.yml` trỏ đúng đường dẫn build, file `.env`, và file migration trước khi chạy hoàn chỉnh.

Nếu chạy trực tiếp bằng Python:

```bash
cd Code/Server
python -m app.main
```

### Client

Client console dùng .NET:

```bash
cd Code/Client/CaroClient.ConsoleTest
dotnet run
```

Hiện tại client mới ở mức project mẫu để kiểm thử kết nối, chưa hoàn thiện giao diện và luồng chơi.

## Cấu hình

Các tham số nên cấu hình bằng file `.env` trong `Code/Server/`. Không commit file `.env` lên repository.

Ví dụ biến môi trường:

```env
SERVER_HOST=0.0.0.0
SERVER_PORT=8765
DATABASE_URL=postgresql://caro_user:caro_pass@db:5432/caro_db
```

Thông tin database mặc định trong Docker Compose:

- Database: `caro_db`
- User: `caro_user`
- Password: `caro_pass`
- Host khi chạy trong Docker network: `db`
- Port: `5432`

## Chức năng

- [ ] Client kết nối đến server.
- [ ] Hiển thị danh sách người chơi đang online.
- [ ] Gửi lời mời thách đấu.
- [ ] Chấp nhận hoặc từ chối lời mời.
- [ ] Tạo phòng đấu và quản lý nhiều trận đấu đồng thời.
- [ ] Đồng bộ trạng thái bàn cờ theo thời gian thực.
- [ ] Kiểm tra tính hợp lệ của nước đi.
- [ ] Kiểm tra kết quả thắng, thua hoặc hòa.
- [ ] Giới hạn thời gian suy nghĩ cho mỗi lượt.
- [ ] Cho phép người chơi kết nối lại trong thời gian cho phép.
- [ ] Lưu lịch sử và kết quả trận đấu.
- [ ] Cho phép khán giả xem trận đấu đang diễn ra.
- [ ] Phân biệt quyền của người chơi và khán giả.

## Kiểm thử

Các nhóm kiểm thử dự kiến:

- Functional test: kiểm tra đăng nhập, mời đấu, đánh cờ, kết thúc trận.
- Test dữ liệu không hợp lệ: message sai format, đánh vào ô đã có quân, đánh sai lượt.
- Test mất kết nối: client mất kết nối, kết nối lại, rời phòng.
- Stress test: nhiều client kết nối đồng thời.
- Performance test: đo thời gian phản hồi khi nhiều trận đấu diễn ra cùng lúc.

Bằng chứng kiểm thử, hình ảnh, video demo và log có thể lưu tại `Extra/`.

## Demo

- Video demo: cập nhật sau.
- Slide thuyết trình: `PPTX/`.
- Báo cáo: `DOCX/`.
- Tài liệu bổ sung và bằng chứng kiểm thử: `Extra/`.

## Giới hạn hiện tại

- Server chưa có source chính trong `Code/Server/app/`.
- Client hiện mới là console project mẫu.
- Schema message trong `Code/Shared/message-schema.json` chưa hoàn thiện.
- Migration database trong `Code/Server/migrations/init.sql` chưa có cấu trúc bảng.
- Chưa có giao diện người dùng hoàn chỉnh.
- Chưa có test tự động.
