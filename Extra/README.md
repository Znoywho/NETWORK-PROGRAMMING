# Extra

## Tài liệu kỹ thuật

| File | Nội dung |
|---|---|
| `network-protocol.md` | Module 1 — framing 4 byte + JSON, vòng lặp `selectors`, vòng đời kết nối, đồng hồ lượt và hạn kết nối lại, cách server chọn người nhận |
| `database-schema.md` | Module 3 — ba bảng `users`/`matches`/`moves`, ràng buộc, quan hệ, cách kết nối database |
| `queue-event-format.md` | Module 3 — format event đi qua hàng đợi xuống DB Writer, xử lý lỗi và dead-letter |
| `er-diagram-database.mmd` | Sơ đồ ER của database |
| `queue-event-flow.mmd` | Sơ đồ luồng event từ handler qua hàng đợi xuống database |

File `.mmd` là sơ đồ Mermaid. Xem bản render bằng cách mở file trên GitHub, hoặc dán nội dung vào mermaid.live.

## Bằng chứng kiểm thử

Thư mục `test-evidence/` lưu:

- Ảnh chụp màn hình.
- Log kiểm thử.
- Dữ liệu test.
- Kết quả stress test và performance test.

Không lưu password, secret hoặc dữ liệu cá nhân thật.
