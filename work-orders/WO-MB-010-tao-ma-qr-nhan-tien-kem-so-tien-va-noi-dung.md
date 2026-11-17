# WO-MB-010 – Tạo mã QR nhận tiền kèm số tiền và nội dung

| Thuộc tính | Giá trị |
|---|---|
| Loại | Tính năng mới |
| Ưu tiên | Should |
| Cỡ | S |
| Người yêu cầu | Product Owner – Chuyển khoản |

**1. Bối cảnh và mục tiêu**
Người dùng muốn nhận tiền nhanh mà không đọc số tài khoản, và muốn bên chuyển điền sẵn số tiền, nội dung. Mục tiêu: giảm sai sót khi nhập tay; chỉ số đo: ≥ 20% lượt mở màn "Nhận tiền" tạo mã có số tiền (đề xuất).

**2. Phạm vi**
- Trong phạm vi: tạo QR theo chuẩn VietQR cho tài khoản thanh toán của người dùng; tuỳ chọn số tiền và nội dung; chia sẻ / lưu ảnh QR.
- Ngoài phạm vi: QR động có thời hạn; theo dõi trạng thái thanh toán của QR.

**3. Yêu cầu chức năng**

| Mã | Yêu cầu | Ưu tiên | Tiêu chí chấp nhận |
|---|---|---|---|
| REQ-001 | Màn "Nhận tiền" hiện QR của tài khoản mặc định | Must | Cho người dùng mở "Nhận tiền", Khi màn hình tải xong, Thì hiện mã QR, tên chủ tài khoản và số tài khoản đã che |
| REQ-002 | Nhập số tiền và nội dung tuỳ chọn | Must | Cho màn Nhận tiền, Khi nhập số tiền hợp lệ và nội dung, Thì QR được tạo lại chứa các giá trị đó |
| REQ-003 | Chọn tài khoản nhận | Should | Cho người dùng có nhiều tài khoản thanh toán, Khi chọn tài khoản khác, Thì QR đổi theo tài khoản đó |
| REQ-004 | Chia sẻ / lưu ảnh QR | Should | Cho QR đang hiển thị, Khi bấm chia sẻ hoặc lưu, Thì ảnh gồm QR, tên chủ tài khoản, số tiền và nội dung được xuất ra |

**4. Luật nghiệp vụ và ngoại lệ**
- BR-01: Số tiền là số nguyên dương, tối thiểu 1.000 VND, tối đa theo quy định VietQR.
- BR-02: Nội dung tối đa 50 ký tự, không dấu khi mã hoá vào QR theo chuẩn.
- EX-01: Khi số tiền không hợp lệ, hiện lỗi dưới ô nhập và giữ nguyên QR trước đó.
- EX-02: Khi tài khoản đang bị khoá / đóng, không tạo QR và hiện lý do.

**5. Dữ liệu**

| Dữ liệu | Mức phân loại | Ghi chú |
|---|---|---|
| Số tài khoản trong mã QR | Hạn chế | QR chủ động chia sẻ ra ngoài; người dùng được cảnh báo trước khi chia sẻ; màn hình hiển thị số tài khoản che 4 số cuối |
| Tên chủ tài khoản | Bảo mật | |
| Số tiền, nội dung chuyển khoản | Bảo mật | Không ghi log |

**6. Phi chức năng**: tạo QR phía app, không gửi nội dung QR lên server; tuân thủ đặc tả VietQR phiên bản hiện hành (cần xác nhận); độ tương phản QR đủ để máy quét đọc được ở độ sáng thấp.

**7. Phụ thuộc**: thư viện tạo QR / đặc tả VietQR của NAPAS; danh sách tài khoản của người dùng.

**8. Câu hỏi mở**
- Q-01: Ngân hàng có cho phép mã QR chứa số tài khoản đầy đủ khi chia sẻ ra ngoài không? (Hỏi: An toàn thông tin, Pháp chế)

---

> Quy ước: mức phân loại dữ liệu theo tài liệu "Phân loại dữ liệu và quy tắc xử lý dữ liệu nhạy cảm" v1.0. Các con số đánh dấu "đề xuất" chưa được xác nhận. Ví dụ dùng dữ liệu giả.
