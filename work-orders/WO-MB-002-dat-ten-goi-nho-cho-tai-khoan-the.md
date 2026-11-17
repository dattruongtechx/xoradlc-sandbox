# WO-MB-002 – Đặt tên gợi nhớ cho tài khoản / thẻ

| Thuộc tính | Giá trị |
|---|---|
| Loại | Tính năng mới |
| Ưu tiên | Could |
| Cỡ | S |
| Người yêu cầu | Product Owner – Kênh số |

**1. Bối cảnh và mục tiêu**
Khách hàng có nhiều tài khoản / thẻ nhưng chỉ nhìn thấy số tài khoản, khó phân biệt. Mục tiêu: giúp nhận diện nhanh; chỉ số đo: giảm thao tác chọn nhầm tài khoản nguồn (khiếu nại liên quan) 20% (đề xuất).

**2. Phạm vi**
- Trong phạm vi: đặt, sửa, xoá tên gợi nhớ cho tài khoản thanh toán, tiết kiệm và thẻ; hiển thị tên gợi nhớ ở danh sách tài khoản và màn chọn tài khoản nguồn.
- Ngoài phạm vi: đổi tên tài khoản chính thức trên sao kê; đồng bộ tên gợi nhớ giữa nhiều thiết bị khác tài khoản đăng nhập (xem Q-01).

**3. Yêu cầu chức năng**

| Mã | Yêu cầu | Ưu tiên | Tiêu chí chấp nhận |
|---|---|---|---|
| REQ-001 | Người dùng đặt tên gợi nhớ từ màn chi tiết tài khoản / thẻ | Must | Cho người dùng ở chi tiết tài khoản, Khi nhập tên hợp lệ và bấm Lưu, Thì tên hiển thị ngay ở mọi danh sách tài khoản |
| REQ-002 | Kiểm tra tên nhập | Must | Cho ô nhập tên, Khi nhập quá 30 ký tự hoặc chứa ký tự đặc biệt không cho phép, Thì hiện lỗi dưới ô nhập và không cho Lưu |
| REQ-003 | Xoá tên gợi nhớ | Should | Cho tài khoản đã có tên gợi nhớ, Khi xoá tên, Thì hiển thị lại tên mặc định (loại tài khoản + 4 số cuối) |

**4. Luật nghiệp vụ và ngoại lệ**
- BR-01: Tên 1–30 ký tự; cho phép chữ, số, dấu cách và `-`, `_`.
- BR-02: Cho phép trùng tên giữa các tài khoản.
- EX-01: Khi lưu thất bại do mất mạng, giữ nguyên nội dung đã nhập và báo "Chưa lưu được, vui lòng thử lại".

**5. Dữ liệu**

| Dữ liệu | Mức phân loại | Ghi chú |
|---|---|---|
| Tên gợi nhớ | Bảo mật | Do người dùng tự nhập, có thể chứa thông tin cá nhân; không ghi giá trị vào log |
| Số tài khoản / số thẻ (hiển thị kèm) | Hạn chế | Che theo quy tắc (giữ 4 số cuối) |

**6. Phi chức năng**: lưu trên server theo định danh khách hàng; truyền bằng TLS 1.2 trở lên; kiểm tra đầu vào cả phía client và server (chống chèn mã).

**7. Phụ thuộc**: API cập nhật thuộc tính hiển thị tài khoản (cần xác nhận với Core Banking / Backend app).

**8. Câu hỏi mở**
- Q-01: Lưu tên ở server (đồng bộ nhiều thiết bị) hay chỉ lưu cục bộ? (Hỏi: Architecture Design)

---

> Quy ước: mức phân loại dữ liệu theo tài liệu "Phân loại dữ liệu và quy tắc xử lý dữ liệu nhạy cảm" v1.0. Các con số đánh dấu "đề xuất" chưa được xác nhận. Ví dụ dùng dữ liệu giả.
