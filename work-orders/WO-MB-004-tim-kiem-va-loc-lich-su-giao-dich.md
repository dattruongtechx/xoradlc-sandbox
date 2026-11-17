# WO-MB-004 – Tìm kiếm và lọc lịch sử giao dịch

| Thuộc tính | Giá trị |
|---|---|
| Loại | Cải tiến tính năng hiện có |
| Ưu tiên | Must |
| Cỡ | M |
| Người yêu cầu | Product Owner – Tài khoản |

**1. Bối cảnh và mục tiêu**
Lịch sử giao dịch chỉ cuộn theo thời gian, người dùng khó tìm một khoản cụ thể. Mục tiêu: tìm được giao dịch trong ≤ 3 thao tác; giảm cuộc gọi hỗ trợ tra soát 15% (đề xuất).

**2. Phạm vi**
- Trong phạm vi: tìm theo từ khoá (nội dung, tên người nhận); lọc theo khoảng ngày, loại (tiền vào / tiền ra), khoảng số tiền; xoá bộ lọc.
- Ngoài phạm vi: xuất sao kê, lọc theo danh mục chi tiêu.

**3. Yêu cầu chức năng**

| Mã | Yêu cầu | Ưu tiên | Tiêu chí chấp nhận |
|---|---|---|---|
| REQ-001 | Ô tìm kiếm ở đầu màn lịch sử | Must | Cho màn lịch sử giao dịch, Khi nhập ≥ 2 ký tự, Thì danh sách chỉ còn giao dịch có nội dung hoặc tên người nhận khớp, không phân biệt hoa thường và dấu |
| REQ-002 | Lọc theo khoảng ngày | Must | Cho bộ lọc, Khi chọn từ ngày – đến ngày, Thì chỉ hiện giao dịch trong khoảng đó, tối đa 12 tháng |
| REQ-003 | Lọc theo loại giao dịch | Must | Cho bộ lọc, Khi chọn "Tiền vào" hoặc "Tiền ra", Thì chỉ hiện đúng loại đã chọn |
| REQ-004 | Lọc theo khoảng số tiền | Should | Cho bộ lọc, Khi nhập số tiền từ – đến, Thì chỉ hiện giao dịch trong khoảng đó |
| REQ-005 | Hiện các bộ lọc đang áp dụng và nút xoá | Must | Cho danh sách đang lọc, Khi xem màn hình, Thì thấy nhãn bộ lọc và nút "Xoá bộ lọc" đưa danh sách về mặc định |

**4. Luật nghiệp vụ và ngoại lệ**
- BR-01: Kết hợp nhiều bộ lọc theo điều kiện VÀ.
- BR-02: Phân trang 20 giao dịch mỗi lần tải.
- EX-01: Khi không có kết quả, hiện "Không tìm thấy giao dịch phù hợp" kèm nút xoá bộ lọc.
- EX-02: Khi chọn khoảng ngày vượt 12 tháng, báo lỗi và không gọi API.

**5. Dữ liệu**

| Dữ liệu | Mức phân loại | Ghi chú |
|---|---|---|
| Lịch sử giao dịch, số tiền | Hạn chế | Không lưu bộ nhớ đệm không mã hoá; không ghi log |
| Từ khoá tìm kiếm | Bảo mật | Có thể chứa tên người; không ghi vào log, không gửi qua URL |

**6. Phi chức năng**: kết quả tìm / lọc trả về < 2 giây với 12 tháng dữ liệu; từ khoá gửi trong body (POST), không trong tham số truy vấn.

**7. Phụ thuộc**: API lịch sử giao dịch cần bổ sung tham số lọc (Backend); nếu chưa có thì lọc phía app trên dữ liệu đã tải (xem Q-01).

**8. Câu hỏi mở**
- Q-01: Tìm kiếm thực hiện phía server hay phía app? (Hỏi: Architecture Design)

---

> Quy ước: mức phân loại dữ liệu theo tài liệu "Phân loại dữ liệu và quy tắc xử lý dữ liệu nhạy cảm" v1.0. Các con số đánh dấu "đề xuất" chưa được xác nhận. Ví dụ dùng dữ liệu giả.
