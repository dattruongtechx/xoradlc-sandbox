# xoradlc-sandbox

Repo mẫu để team thử **Xora DLC platform** và các plugin trong [TechX-Corp/xoradlc-plugin](https://github.com/TechX-Corp/xoradlc-plugin): plugin `xora-dev` (Claude Code / Kiro) và plugin AI-DLC `techx-dlc`.

Bối cảnh giả lập: backend **Mobile Banking** nhỏ đã "chạy trong sản xuất", cùng 10 work order (WO) mới cần làm. Mọi dữ liệu trong repo là **dữ liệu giả**; đừng đưa dữ liệu thật của khách hàng hay dự án vào đây vì repo là public.

## Có gì trong repo

| Đường dẫn | Là gì | Dùng để thử |
|---|---|---|
| `work-orders/WO-MB-001…010-*.md` | 10 work order (bối cảnh, phạm vi, REQ kèm tiêu chí chấp nhận, luật nghiệp vụ, phân loại dữ liệu, câu hỏi mở) | Tạo WO trên Xora DLC, skill `implement`, scope `techx-dlc-feature` |
| `mbank/` | Code Python thuần (chỉ thư viện chuẩn): `accounts`, `transfers` (hạn mức ngày, idempotency key), `cards`, `transactions`, `errors`, `masking` | Chỗ để agent đọc và sửa; scope `techx-dlc-onboard` (reverse-engineering) |
| `tests/` | Test `unittest` cho chuyển khoản | `build-and-test`, kiểm agent không làm hỏng luồng cũ |
| `convention.md` | Convention của dự án, có khối luật JSON cho sensor | Sensor convention của `xora-dev` |

`mbank/cards.py` cố ý còn một vi phạm cũ (`print(...)`, luật `LOG-003`) để thử việc sensor **không** báo code cũ khi chỉ kiểm dòng đã đổi, nhưng báo khi chạy `--full`.

## Chuẩn bị

Cần `python3` (3.10+) và `git`; thêm `claude` nếu dùng Claude Code, hoặc Kiro CLI.

```bash
git clone https://github.com/dattruongtechx/xoradlc-sandbox.git && cd xoradlc-sandbox
python3 -m unittest discover -s tests -t .   # phải OK trước khi bắt đầu

# Cài plugin xora-dev
curl -fsSL https://raw.githubusercontent.com/TechX-Corp/xoradlc-plugin/main/install.sh | sh -s -- claude project   # Claude Code
curl -fsSL https://raw.githubusercontent.com/TechX-Corp/xoradlc-plugin/main/install.sh | sh -s -- kiro .           # Kiro
```

Lần đầu: trong Claude Code gõ `/mcp` và đăng nhập Xora DLC; Kiro tự mở trình duyệt.

**Mỗi người làm trên nhánh riêng** (`git switch -c <tên>/<WO>`), mở PR vào `main` để cả team xem được kết quả agent sinh ra. Không push thẳng vào `main`.

## Kịch bản thử gợi ý

| # | Thử gì | Cách làm | Kỳ vọng |
|---|---|---|---|
| 1 | MCP `xora_ask` | Hỏi: "Việc của tôi hôm nay là gì?", "Tóm tắt WO-MB-006" | Trả lời có trích dẫn, đúng người đăng nhập |
| 2 | `implement` cho WO nhỏ | "Làm WO-MB-002" (cỡ S) hoặc WO-MB-001 phần backend | Code + test mới, test cũ vẫn OK |
| 3 | `implement` chạm tiền | "Làm WO-MB-006 hạn mức tự đặt" (sửa `mbank/transfers.py`) | Giữ idempotency, có test luồng sai trước, không log số tài khoản rõ |
| 4 | Sensor convention | Nhờ agent thêm `print(...)` hoặc `log.info("... %s", account_number)` | Cảnh báo `LOG-003` / `PII-001`, agent tự sửa |
| 5 | Sensor code cũ | `python3 ~/.xora/plugin/agents-plugin/dev/sensor/convention_sensor.py --full mbank/*.py` | Báo `LOG-003` ở `mbank/cards.py`; chạy không `--full` thì không báo |
| 6 | Câu hỏi mở | Làm WO-MB-007 (có Q-01 về giao dịch định kỳ) | Agent hỏi lại / ghi open question thay vì tự đoán |
| 7 | `changeset` | "Lập changeset cho nhánh này" | Mô tả PR ghi rõ phần do AI sinh, map REQ ↔ code ↔ test |
| 8 | `upload-tech-doc` | "Lưu tài liệu thiết kế WO-MB-006 vào KB" | Hỏi xác nhận trước khi lưu |
| 9 | AI-DLC onboard / feature | `techx-dlc-onboard` một lần cho repo, rồi `techx-dlc-feature` cho một WO | Xem README của `aidlc-plugin/` |

Gặp lỗi hoặc kết quả sai: mở issue ở repo này, ghi kịch bản số mấy, công cụ (Claude Code / Kiro), câu đã hỏi và kết quả.

## Danh sách work order

| Mã | Tên | Cỡ |
|---|---|---|
| WO-MB-001 | Ẩn / hiện số dư trên màn hình chính | S |
| WO-MB-002 | Đặt tên gợi nhớ cho tài khoản / thẻ | S |
| WO-MB-003 | Lưu người thụ hưởng yêu thích | M |
| WO-MB-004 | Tìm kiếm và lọc lịch sử giao dịch | M |
| WO-MB-005 | Chia sẻ biên lai giao dịch dạng ảnh | S |
| WO-MB-006 | Tự đặt hạn mức chuyển khoản trong ngày | M |
| WO-MB-007 | Khoá / mở khoá thẻ tạm thời | M |
| WO-MB-008 | Nhắc lịch thanh toán hoá đơn | M |
| WO-MB-009 | Cấu hình thời gian tự đăng xuất khi không hoạt động | S |
| WO-MB-010 | Tạo mã QR nhận tiền kèm số tiền và nội dung | S |
