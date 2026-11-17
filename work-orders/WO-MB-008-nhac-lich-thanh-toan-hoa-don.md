# WO-MB-008 – Nhắc lịch thanh toán hoá đơn

| Thuộc tính | Giá trị |
|---|---|
| Loại | Tính năng mới |
| Ưu tiên | Could |
| Cỡ | M |
| Người yêu cầu | Product Owner – Thanh toán |

**1. Bối cảnh và mục tiêu**
Người dùng hay quên hạn thanh toán điện, nước, internet và bị phạt chậm trả. Mục tiêu: tăng tỷ lệ thanh toán đúng hạn; chỉ số đo: ≥ 60% nhắc lịch dẫn tới thanh toán trong 24 giờ (đề xuất).

**2. Phạm vi**
- Trong phạm vi: tạo nhắc lịch cho nhà cung cấp và mã khách hàng đã dùng; chọn tần suất (hằng tháng) và ngày nhắc; gửi push; mở thẳng màn thanh toán từ thông báo; tạm dừng và xoá nhắc lịch.
- Ngoài phạm vi: tự động trừ tiền; lấy số tiền hoá đơn tự động (chỉ nhắc, không hiện số tiền ở bản đầu tiên).

**3. Yêu cầu chức năng**

| Mã | Yêu cầu | Ưu tiên | Tiêu chí chấp nhận |
|---|---|---|---|
| REQ-001 | Tạo nhắc lịch từ màn kết quả thanh toán hoá đơn thành công | Must | Cho thanh toán hoá đơn thành công, Khi bấm "Nhắc tôi tháng sau", Thì tạo nhắc lịch với ngày nhắc mặc định = ngày thanh toán hiện tại |
| REQ-002 | Sửa ngày nhắc và giờ nhắc | Must | Cho nhắc lịch đã tạo, Khi sửa ngày (1–28) và giờ, Thì lần nhắc kế tiếp theo giá trị mới |
| REQ-003 | Gửi push đúng hẹn | Must | Cho nhắc lịch đang bật, Khi đến ngày giờ đã chọn, Thì gửi push "Đến hạn thanh toán <tên nhà cung cấp>", không chứa mã khách hàng đầy đủ |
| REQ-004 | Chạm vào push mở màn thanh toán | Should | Cho người dùng nhận push, Khi chạm, Thì app mở màn thanh toán của nhà cung cấp đó sau khi đăng nhập |
| REQ-005 | Quản lý danh sách nhắc lịch | Should | Cho màn "Nhắc lịch của tôi", Khi xem, Thì có thể bật / tắt, sửa, xoá từng nhắc lịch |

**4. Luật nghiệp vụ và ngoại lệ**
- BR-01: Tối đa 10 nhắc lịch mỗi khách hàng (đề xuất).
- BR-02: Ngày nhắc chỉ 1–28 để tránh tháng ngắn.
- BR-03: Không gửi nhắc nếu người dùng đã thanh toán nhà cung cấp đó trong 3 ngày gần nhất.
- EX-01: Khi người dùng tắt quyền thông báo của hệ điều hành, hiện biểu ngữ hướng dẫn bật lại.
- EX-02: Khi nhà cung cấp ngừng hỗ trợ, tự tắt nhắc lịch và thông báo cho người dùng.

**5. Dữ liệu**

| Dữ liệu | Mức phân loại | Ghi chú |
|---|---|---|
| Mã khách hàng nhà cung cấp (mã hợp đồng điện, nước) | Bảo mật | Mã hoá khi lưu; che khi hiển thị; không đưa vào nội dung push |
| Nhà cung cấp, ngày giờ nhắc | Nội bộ | |
| Token thiết bị nhận push | Bảo mật | Xoá khi đăng xuất / gỡ thiết bị |

**6. Phi chức năng**: lịch nhắc chạy ở server (không phụ thuộc app đang mở); sai lệch giờ gửi ≤ 5 phút; nhật ký gửi push.

**7. Phụ thuộc**: dịch vụ push (FCM / APNs); danh mục nhà cung cấp hoá đơn hiện có.

**8. Câu hỏi mở**
- Q-01: Có gửi cả SMS / Zalo ngoài push không? (Hỏi: PO)
- Q-02: Giờ nhắc mặc định là mấy giờ? (đề xuất 08:00) (Hỏi: PO)

---

> Quy ước: mức phân loại dữ liệu theo tài liệu "Phân loại dữ liệu và quy tắc xử lý dữ liệu nhạy cảm" v1.0. Các con số đánh dấu "đề xuất" chưa được xác nhận. Ví dụ dùng dữ liệu giả.
