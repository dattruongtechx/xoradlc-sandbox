# WO-MB-007 – Khoá / mở khoá thẻ tạm thời

| Thuộc tính | Giá trị |
|---|---|
| Loại | Tính năng mới |
| Ưu tiên | Must |
| Cỡ | M |
| Người yêu cầu | Product Owner – Thẻ |

**1. Bối cảnh và mục tiêu**
Khi nghi ngờ thất lạc thẻ, khách hàng phải gọi tổng đài để khoá, mất thời gian và dễ phát sinh giao dịch trái phép. Mục tiêu: khoá thẻ trong ≤ 30 giây từ app; chỉ số đo: giảm 30% cuộc gọi yêu cầu khoá thẻ tạm thời (đề xuất).

**2. Phạm vi**
- Trong phạm vi: khoá và mở khoá tạm thời thẻ ghi nợ / tín dụng; hiển thị trạng thái thẻ; thông báo khi đổi trạng thái.
- Ngoài phạm vi: khoá vĩnh viễn và phát hành lại thẻ; khoá theo kênh (chỉ ATM, chỉ online).

**3. Yêu cầu chức năng**

| Mã | Yêu cầu | Ưu tiên | Tiêu chí chấp nhận |
|---|---|---|---|
| REQ-001 | Công tắc "Khoá thẻ tạm thời" ở chi tiết thẻ | Must | Cho thẻ đang hoạt động, Khi người dùng bật khoá và xác nhận, Thì trạng thái thẻ chuyển "Đang khoá tạm thời" |
| REQ-002 | Chặn giao dịch khi thẻ khoá | Must | Cho thẻ đang khoá, Khi phát sinh giao dịch rút tiền, thanh toán hoặc online, Thì giao dịch bị từ chối với mã lý do "thẻ bị khoá" |
| REQ-003 | Mở khoá yêu cầu xác thực | Must | Cho thẻ đang khoá, Khi người dùng mở khoá và xác thực OTP / sinh trắc thành công, Thì thẻ hoạt động lại |
| REQ-004 | Khoá không cần xác thực mạnh (chỉ xác nhận một bước) | Should | Cho thẻ đang hoạt động, Khi bật khoá, Thì chỉ cần bấm xác nhận, không cần OTP, để khoá nhanh nhất có thể |
| REQ-005 | Thông báo khi đổi trạng thái | Must | Cho thay đổi trạng thái thành công, Khi hoàn tất, Thì gửi push và SMS tới số điện thoại đăng ký |

**4. Luật nghiệp vụ và ngoại lệ**
- BR-01: Giao dịch định kỳ đã uỷ quyền (phí thường niên, trả góp tự động) vẫn được xử lý hay không: xem Q-01.
- BR-02: Thẻ đã bị khoá vĩnh viễn hoặc hết hạn không hiện công tắc.
- EX-01: Khi hệ thống thẻ không phản hồi, hiện "Chưa khoá được, vui lòng thử lại hoặc gọi tổng đài" kèm số tổng đài.
- EX-02: Khi trạng thái hiển thị khác trạng thái thực ở hệ thống thẻ, lấy trạng thái từ hệ thống thẻ làm chuẩn và làm mới màn hình.

**5. Dữ liệu**

| Dữ liệu | Mức phân loại | Ghi chú |
|---|---|---|
| Số thẻ | Hạn chế | Hiện 6 số đầu và 4 số cuối; không ghi log |
| Trạng thái thẻ | Bảo mật | |
| Nhật ký đổi trạng thái (thời gian, thiết bị, IP) | Bảo mật | Lưu theo quy định lưu nhật ký của ngân hàng |

**6. Phi chức năng**: trạng thái khoá có hiệu lực ở hệ thống thẻ trong ≤ 5 giây; sẵn sàng 99,9% (đề xuất); không lưu CVV / PIN; ghi nhật ký kiểm toán.

**7. Phụ thuộc**: API khoá / mở khoá của hệ thống quản lý thẻ (Card Management System); dịch vụ thông báo; dịch vụ OTP.

**8. Câu hỏi mở**
- Q-01: Giao dịch định kỳ có bị chặn khi thẻ khoá tạm thời không? (Hỏi: PO – Thẻ)
- Q-02: Cho phép khoá không cần xác thực có đáp ứng chính sách an toàn thông tin không? (Hỏi: An toàn thông tin)

---

> Quy ước: mức phân loại dữ liệu theo tài liệu "Phân loại dữ liệu và quy tắc xử lý dữ liệu nhạy cảm" v1.0. Các con số đánh dấu "đề xuất" chưa được xác nhận. Ví dụ dùng dữ liệu giả.
