# WO-MB-009 – Cấu hình thời gian tự đăng xuất khi không hoạt động

| Thuộc tính | Giá trị |
|---|---|
| Loại | Tính năng mới (cải tiến bảo mật) |
| Ưu tiên | Should |
| Cỡ | S |
| Người yêu cầu | An toàn thông tin |

**1. Bối cảnh và mục tiêu**
App hiện dùng thời gian hết phiên cố định, một số khách hàng muốn ngắn hơn khi dùng thiết bị chung hoặc dài hơn khi dùng cá nhân. Mục tiêu: tăng sự kiểm soát cho người dùng mà vẫn giữ ngưỡng an toàn của ngân hàng.

**2. Phạm vi**
- Trong phạm vi: chọn thời gian tự đăng xuất trong Cài đặt bảo mật; đếm ngược cảnh báo trước khi đăng xuất; đăng xuất và xoá dữ liệu phiên.
- Ngoài phạm vi: thay đổi thời hạn của token phía server; quản lý thiết bị đăng nhập.

**3. Yêu cầu chức năng**

| Mã | Yêu cầu | Ưu tiên | Tiêu chí chấp nhận |
|---|---|---|---|
| REQ-001 | Chọn thời gian tự đăng xuất: 1, 3, 5 phút | Must | Cho màn Cài đặt bảo mật, Khi chọn một giá trị, Thì giá trị lưu và áp dụng từ phiên hiện tại; mặc định 3 phút |
| REQ-002 | Cảnh báo đếm ngược trước khi đăng xuất | Must | Cho người dùng không thao tác, Khi còn 30 giây, Thì hiện hộp thoại đếm ngược với nút "Tiếp tục sử dụng" |
| REQ-003 | Tự đăng xuất khi hết giờ | Must | Cho hộp thoại đếm ngược, Khi hết 30 giây không phản hồi, Thì app đăng xuất, xoá dữ liệu nhạy cảm đang hiển thị và về màn đăng nhập |
| REQ-004 | Không đếm giờ khi đang xử lý giao dịch chờ kết quả | Should | Cho giao dịch đang chờ kết quả, Khi đang chờ, Thì bộ đếm tạm dừng đến khi có kết quả hoặc quá thời gian của giao dịch |

**4. Luật nghiệp vụ và ngoại lệ**
- BR-01: Giá trị tối đa 5 phút theo chính sách an toàn thông tin (đề xuất), người dùng không chọn dài hơn.
- BR-02: App chuyển nền quá 1 phút thì yêu cầu xác thực lại khi quay lại.
- EX-01: Khi đang nhập OTP mà hết giờ, huỷ giao dịch chưa xác nhận và báo "Phiên đã hết hạn".

**5. Dữ liệu**

| Dữ liệu | Mức phân loại | Ghi chú |
|---|---|---|
| Giá trị cài đặt thời gian | Nội bộ | Lưu cục bộ hoặc theo tài khoản |
| Dữ liệu đang hiển thị (số dư, giao dịch) | Hạn chế | Phải xoá khỏi bộ nhớ khi đăng xuất |

**6. Phi chức năng**: huỷ token phiên phía server khi đăng xuất; không ghi dữ liệu nhạy cảm vào bộ nhớ đệm hay ảnh chụp màn hình khi đăng xuất.

**7. Phụ thuộc**: API đăng xuất / huỷ phiên hiện có.

**8. Câu hỏi mở**
- Q-01: Chính sách tối đa thực tế là bao nhiêu phút? (Hỏi: An toàn thông tin)

---

> Quy ước: mức phân loại dữ liệu theo tài liệu "Phân loại dữ liệu và quy tắc xử lý dữ liệu nhạy cảm" v1.0. Các con số đánh dấu "đề xuất" chưa được xác nhận. Ví dụ dùng dữ liệu giả.
