# WO-MB-006 – Tự đặt hạn mức chuyển khoản trong ngày

| Thuộc tính | Giá trị |
|---|---|
| Loại | Tính năng mới |
| Ưu tiên | Should |
| Cỡ | M |
| Người yêu cầu | An toàn thông tin / Product Owner – Bảo mật |

**1. Bối cảnh và mục tiêu**
Hạn mức chuyển khoản do ngân hàng quy định chung, người dùng không tự giảm được. Nếu điện thoại bị lộ, thiệt hại có thể lớn. Mục tiêu: cho khách hàng chủ động hạ hạn mức; chỉ số đo: ≥ 10% người dùng đặt hạn mức riêng sau 6 tháng (đề xuất).

**2. Phạm vi**
- Trong phạm vi: xem hạn mức hiện hành; đặt hạn mức riêng thấp hơn hoặc bằng hạn mức của ngân hàng; áp dụng cho chuyển khoản đi trong ngày.
- Ngoài phạm vi: tăng hạn mức vượt mức ngân hàng quy định; hạn mức theo từng giao dịch riêng lẻ.

**3. Yêu cầu chức năng**

| Mã | Yêu cầu | Ưu tiên | Tiêu chí chấp nhận |
|---|---|---|---|
| REQ-001 | Màn "Hạn mức chuyển khoản" trong Cài đặt bảo mật | Must | Cho người dùng đã đăng nhập, Khi mở màn hình, Thì thấy hạn mức ngân hàng, hạn mức tự đặt và số đã dùng trong ngày |
| REQ-002 | Đặt hạn mức tự chọn | Must | Cho hạn mức nhập ≤ hạn mức ngân hàng, Khi xác nhận bằng OTP / sinh trắc, Thì hạn mức mới có hiệu lực ngay cho giao dịch tiếp theo |
| REQ-003 | Chặn giao dịch vượt hạn mức tự đặt | Must | Cho tổng chuyển đi trong ngày + giao dịch mới > hạn mức tự đặt, Khi người dùng xác nhận chuyển, Thì giao dịch bị từ chối và báo còn lại bao nhiêu |
| REQ-004 | Hạ hạn mức có hiệu lực ngay; tăng hạn mức (nhưng vẫn ≤ mức ngân hàng) có hiệu lực sau 24 giờ | Should | Cho người dùng nâng hạn mức tự đặt, Khi xác nhận, Thì giá trị cũ vẫn áp dụng trong 24 giờ và app hiện thời điểm hiệu lực |
| REQ-005 | Thông báo khi đổi hạn mức | Should | Cho thay đổi hạn mức thành công, Khi hoàn tất, Thì gửi push và SMS thông báo |

**4. Luật nghiệp vụ và ngoại lệ**
- BR-01: Hạn mức tự đặt ≥ 0 và ≤ hạn mức ngân hàng; bước nhảy 100.000 VND (đề xuất).
- BR-02: Ngày tính theo múi giờ Việt Nam, đặt lại lúc 00:00.
- BR-03: Hạn mức tự đặt không áp dụng cho thanh toán thẻ / hoá đơn đã đặt lịch trước (xem Q-01).
- EX-01: Khi xác thực thất bại 3 lần, khoá thao tác đổi hạn mức 30 phút.
- EX-02: Khi hạn mức ngân hàng bị giảm sau đó (do quy định), hạn mức tự đặt tự hạ theo.

**5. Dữ liệu**

| Dữ liệu | Mức phân loại | Ghi chú |
|---|---|---|
| Hạn mức, số tiền đã dùng trong ngày | Hạn chế | Mã hoá khi lưu; không ghi log giá trị |
| Lịch sử thay đổi hạn mức | Bảo mật | Giữ ít nhất theo thời gian lưu nhật ký của ngân hàng |

**6. Phi chức năng**: kiểm tra hạn mức thực hiện ở server, không tin dữ liệu từ app; nhật ký kiểm toán cho mọi lần đổi (ai, khi nào, giá trị cũ / mới, thiết bị); kiểm tra hạn mức thêm không quá 50 ms vào luồng chuyển khoản.

**7. Phụ thuộc**: Core Banking / hệ thống quản lý hạn mức; dịch vụ OTP / sinh trắc; dịch vụ thông báo.

**8. Câu hỏi mở**
- Q-01: Hạn mức tự đặt có áp dụng cho thanh toán QR và thanh toán hoá đơn không? (Hỏi: PO, An toàn thông tin)
- Q-02: Quy tắc trễ 24 giờ khi tăng hạn mức có phù hợp quy định của NHNN và chính sách nội bộ không? (Hỏi: Pháp chế)

---

> Quy ước: mức phân loại dữ liệu theo tài liệu "Phân loại dữ liệu và quy tắc xử lý dữ liệu nhạy cảm" v1.0. Các con số đánh dấu "đề xuất" chưa được xác nhận. Ví dụ dùng dữ liệu giả.
