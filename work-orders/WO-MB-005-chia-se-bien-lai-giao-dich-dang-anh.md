# WO-MB-005 – Chia sẻ biên lai giao dịch dạng ảnh

| Thuộc tính | Giá trị |
|---|---|
| Loại | Tính năng mới |
| Ưu tiên | Should |
| Cỡ | S |
| Người yêu cầu | Product Owner – Chuyển khoản |

**1. Bối cảnh và mục tiêu**
Người dùng thường chụp màn hình để gửi bằng chứng chuyển tiền, ảnh chụp không đồng nhất và có thể lộ thông tin thừa. Mục tiêu: cung cấp biên lai chuẩn hoá, che thông tin nhạy cảm; chỉ số đo: ≥ 25% giao dịch thành công có thao tác chia sẻ (đề xuất).

**2. Phạm vi**
- Trong phạm vi: tạo ảnh biên lai từ màn kết quả và chi tiết giao dịch; chia sẻ qua menu chia sẻ của hệ điều hành; lưu về thư viện ảnh.
- Ngoài phạm vi: biên lai PDF, gửi trực tiếp qua email trong app.

**3. Yêu cầu chức năng**

| Mã | Yêu cầu | Ưu tiên | Tiêu chí chấp nhận |
|---|---|---|---|
| REQ-001 | Nút "Chia sẻ biên lai" ở màn kết quả và chi tiết giao dịch thành công | Must | Cho giao dịch trạng thái thành công, Khi bấm nút, Thì app tạo ảnh biên lai và mở menu chia sẻ |
| REQ-002 | Nội dung biên lai | Must | Cho ảnh biên lai, Khi xem, Thì có: mã giao dịch, thời gian, số tiền, tên và ngân hàng người nhận, nội dung, logo ngân hàng |
| REQ-003 | Che thông tin nhạy cảm | Must | Cho ảnh biên lai, Khi tạo, Thì số tài khoản người gửi và người nhận chỉ hiện 4 số cuối; không hiện số dư |
| REQ-004 | Lưu ảnh về thiết bị | Should | Cho ảnh biên lai, Khi chọn "Lưu ảnh" và đã cấp quyền, Thì ảnh có trong thư viện; nếu chưa cấp quyền thì xin quyền với lời giải thích |

**4. Luật nghiệp vụ và ngoại lệ**
- BR-01: Chỉ cho chia sẻ giao dịch ở trạng thái thành công.
- EX-01: Khi tạo ảnh lỗi, hiện "Không tạo được biên lai, vui lòng thử lại".
- EX-02: Khi người dùng từ chối quyền thư viện ảnh, vẫn cho chia sẻ qua menu hệ điều hành, chỉ ẩn nút lưu.

**5. Dữ liệu**

| Dữ liệu | Mức phân loại | Ghi chú |
|---|---|---|
| Số tài khoản người gửi / nhận | Hạn chế | Che giữ 4 số cuối trong ảnh |
| Tên người nhận, số tiền, nội dung | Bảo mật | Nằm trong ảnh người dùng chủ động chia sẻ |
| Mã giao dịch | Nội bộ | |

**6. Phi chức năng**: ảnh sinh ở thiết bị, không tải lên server; không lưu ảnh trong bộ nhớ tạm sau khi chia sẻ xong; tạo ảnh < 1 giây.

**7. Phụ thuộc**: không có API mới.

**8. Câu hỏi mở**
- Q-01: Có chèn watermark / mã xác thực biên lai để chống giả mạo không? (Hỏi: An toàn thông tin)

---

> Quy ước: mức phân loại dữ liệu theo tài liệu "Phân loại dữ liệu và quy tắc xử lý dữ liệu nhạy cảm" v1.0. Các con số đánh dấu "đề xuất" chưa được xác nhận. Ví dụ dùng dữ liệu giả.
