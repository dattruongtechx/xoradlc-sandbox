# WO-MB-001 – Ẩn / hiện số dư trên màn hình chính

| Thuộc tính | Giá trị |
|---|---|
| Loại | Tính năng mới (cải tiến) |
| Ưu tiên | Should |
| Cỡ | S |
| Người yêu cầu | Product Owner – Kênh số |

**1. Bối cảnh và mục tiêu**
Khách hàng thường mở app ở nơi đông người và không muốn lộ số dư. Hiện số dư luôn hiển thị ngay khi vào màn hình chính.
Mục tiêu: giảm lo ngại về quyền riêng tư; chỉ số đo: tỷ lệ người dùng bật chế độ ẩn ≥ 30% sau 3 tháng (đề xuất).

**2. Phạm vi**
- Trong phạm vi: nút con mắt ở thẻ số dư màn hình chính; ghi nhớ lựa chọn của người dùng; áp dụng cho số dư các tài khoản thanh toán, tiết kiệm trên màn hình chính.
- Ngoài phạm vi: ẩn số dư trên màn hình chi tiết tài khoản, ẩn số tiền trong lịch sử giao dịch.

**3. Yêu cầu chức năng**

| Mã | Yêu cầu | Ưu tiên | Tiêu chí chấp nhận |
|---|---|---|---|
| REQ-001 | Màn hình chính có nút ẩn / hiện số dư ở mỗi thẻ số dư | Must | Cho người dùng ở màn hình chính, Khi bấm nút con mắt, Thì số dư chuyển thành `••••••` và biểu tượng đổi trạng thái; bấm lại thì hiện số dư |
| REQ-002 | Ghi nhớ lựa chọn giữa các lần mở app | Must | Cho người dùng đã chọn ẩn, Khi thoát hoàn toàn rồi mở lại app, Thì số dư vẫn đang ẩn |
| REQ-003 | Mặc định theo cài đặt của người dùng; người dùng mới mặc định hiện | Should | Cho người dùng mới cài app, Khi đăng nhập lần đầu, Thì số dư hiện; có thể đổi trong Cài đặt > Hiển thị |
| REQ-004 | Ẩn số dư khi app chuyển nền (hiện ở màn hình app switcher) | Could | Cho người dùng đang hiện số dư, Khi chuyển app sang nền, Thì ảnh chụp app trong trình chuyển ứng dụng không lộ số dư |

**4. Luật nghiệp vụ và ngoại lệ**
- BR-01: Trạng thái ẩn / hiện lưu theo người dùng và theo thiết bị.
- EX-01: Khi tải số dư lỗi hoặc quá thời gian, hiển thị "Không tải được" và không hiện `••••••`.

**5. Dữ liệu**

| Dữ liệu | Mức phân loại | Ghi chú |
|---|---|---|
| Số dư tài khoản | Hạn chế | Che khi hiển thị theo lựa chọn; không ghi log |
| Cờ ẩn / hiện (boolean) | Nội bộ | Lưu cục bộ trên thiết bị, không chứa số dư |

**6. Phi chức năng**: phản hồi thao tác bấm < 100 ms; hỗ trợ trình đọc màn hình (nhãn "Ẩn số dư" / "Hiện số dư").

**7. Phụ thuộc**: không có API mới.

**8. Câu hỏi mở**
- Q-01: Có cần yêu cầu xác thực (sinh trắc học) khi chuyển từ ẩn sang hiện không? (Hỏi: PO, An toàn thông tin)

---

> Quy ước: mức phân loại dữ liệu theo tài liệu "Phân loại dữ liệu và quy tắc xử lý dữ liệu nhạy cảm" v1.0. Các con số đánh dấu "đề xuất" chưa được xác nhận. Ví dụ dùng dữ liệu giả.
