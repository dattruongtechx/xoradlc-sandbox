# WO-MB-003 – Lưu người thụ hưởng yêu thích

| Thuộc tính | Giá trị |
|---|---|
| Loại | Tính năng mới |
| Ưu tiên | Should |
| Cỡ | M |
| Người yêu cầu | Product Owner – Chuyển khoản |

**1. Bối cảnh và mục tiêu**
Người dùng thường chuyển cho cùng một số người nhưng phải chọn lại ngân hàng và nhập lại số tài khoản. Mục tiêu: rút ngắn thời gian chuyển khoản lặp lại; chỉ số đo: thời gian chuyển cho người đã lưu giảm ≥ 40% so với nhập tay (đề xuất).

**2. Phạm vi**
- Trong phạm vi: lưu người thụ hưởng sau chuyển khoản thành công; đánh dấu yêu thích; chọn từ danh sách khi chuyển; sửa tên gợi nhớ; xoá.
- Ngoài phạm vi: lưu thụ hưởng cho thanh toán hoá đơn; nhập danh bạ hàng loạt.

**3. Yêu cầu chức năng**

| Mã | Yêu cầu | Ưu tiên | Tiêu chí chấp nhận |
|---|---|---|---|
| REQ-001 | Gợi ý lưu người thụ hưởng ở màn chuyển khoản thành công | Must | Cho giao dịch thành công tới người nhận chưa lưu, Khi hiện màn kết quả, Thì có nút "Lưu người nhận" kèm ô tên gợi nhớ |
| REQ-002 | Danh sách yêu thích ở màn chuyển khoản | Must | Cho người dùng ở màn chuyển khoản, Khi mở "Người nhận đã lưu", Thì thấy danh sách có tên gợi nhớ, ngân hàng và số tài khoản đã che |
| REQ-003 | Chọn người đã lưu tự điền thông tin | Must | Cho danh sách người nhận, Khi chọn một người, Thì ngân hàng, số tài khoản và tên người nhận được điền sẵn, chỉ cần nhập số tiền |
| REQ-004 | Sửa tên gợi nhớ và xoá người nhận | Should | Cho người nhận đã lưu, Khi vuốt và chọn Xoá rồi xác nhận, Thì người nhận biến khỏi danh sách |
| REQ-005 | Tìm kiếm trong danh sách | Could | Cho danh sách có hơn 10 người, Khi nhập từ khoá, Thì danh sách lọc theo tên gợi nhớ hoặc tên người nhận |

**4. Luật nghiệp vụ và ngoại lệ**
- BR-01: Tối đa 50 người nhận đã lưu cho mỗi khách hàng (đề xuất).
- BR-02: Không lưu trùng cặp (ngân hàng, số tài khoản).
- BR-03: Khi chuyển tới người đã lưu, vẫn thực hiện xác thực giao dịch (OTP / sinh trắc) như thường; không bỏ qua bước xác thực.
- EX-01: Khi tên người nhận trả về từ tra cứu khác tên đã lưu, hiện cảnh báo và yêu cầu người dùng xác nhận.
- EX-02: Khi đạt giới hạn 50, thông báo và gợi ý xoá bớt.

**5. Dữ liệu**

| Dữ liệu | Mức phân loại | Ghi chú |
|---|---|---|
| Số tài khoản người nhận | Hạn chế | Lưu mã hoá ở mức trường; che 4 số cuối khi hiển thị |
| Tên người nhận, tên gợi nhớ | Bảo mật | Không ghi giá trị vào log |
| Ngân hàng thụ hưởng | Nội bộ | |

**6. Phi chức năng**: phân quyền theo khách hàng (không đọc được danh sách của người khác); ghi nhật ký thêm / xoá; tải danh sách < 1 giây với 50 bản ghi.

**7. Phụ thuộc**: API quản lý người thụ hưởng (mới); API tra cứu tên tài khoản liên ngân hàng (hiện có).

**8. Câu hỏi mở**
- Q-01: Có cho chuyển nhanh không cần OTP tới người đã lưu với số tiền nhỏ không? (Hỏi: An toàn thông tin)
- Q-02: Giới hạn 50 người có phù hợp không? (Hỏi: PO)

---

> Quy ước: mức phân loại dữ liệu theo tài liệu "Phân loại dữ liệu và quy tắc xử lý dữ liệu nhạy cảm" v1.0. Các con số đánh dấu "đề xuất" chưa được xác nhận. Ví dụ dùng dữ liệu giả.
