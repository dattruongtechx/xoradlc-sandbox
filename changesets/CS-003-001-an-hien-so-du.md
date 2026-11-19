---
id: WO-2026-003/changeset-001
version: 1
status: draft
produced_by: xora-dev
inputs:
  - path: BRD-An-hien-so-du-WO-2026-003
    version: v2.0 (draft, chưa duyệt, BA chưa chỉnh sửa)
  - path: Thiet-ke-An-hien-so-du-WO-2026-003 (OUT-003-02)
    version: không rõ (chưa đọc được nội dung, AAP trả rỗng hai lần)
  - path: work-orders/WO-MB-001-an-hien-so-du-tren-man-hinh-chinh.md
    version: commit 2ced180 (tệp gốc, mâu thuẫn với BRD v2.0)
commits: [63939ab]
approved_by: null
approved_at: null
---

# Changeset: Ẩn / hiện số dư trên màn hình chính (WO-2026-003)

Nhánh: `admin/WO-2026-003` (đã map WO bằng `xdlc link`). PR: chưa tạo.

## 1. Truy vết

| REQ (BRD v2.0) | Nội dung | Trạng thái trong changeset | Code | Test |
|---|---|---|---|---|
| REQ-001 | Mặc định ẩn | Làm `[GIẢ ĐỊNH]` theo BRD v2.0 | `home_balances(hidden=True)` | `test_default_is_hidden` |
| REQ-002 | Hiện số dư bằng một thao tác | Phần backend: `hidden=False` trả số dư thật | `home_balances` | `test_shown_returns_real_balances` |
| REQ-003 | Ẩn lại bằng một thao tác | Phần backend: `hidden=True` | `home_balances` | `test_one_switch_masks_all_balances` |
| REQ-004 | Thay số dư bằng `******` khi ẩn | Làm | `BALANCE_MASK` | `test_hidden_state_never_exposes_balance_value` |
| REQ-005 | Một công tắc chung | Làm: một tham số `hidden` cho mọi số dư | `home_balances` | `test_one_switch_masks_all_balances` |
| REQ-006 | Ghi nhớ lựa chọn | **Không làm.** Cờ lưu cục bộ trên thiết bị (WO-MB-001 mục 5), không có API mới | - | - |
| REQ-007 | Báo lỗi khi không tải được số dư | Làm: ném `ACCOUNT_BALANCE_LOAD_FAILED` | `home_balances` | `test_load_failure_when_shown_*` |
| NFR-001 | Không lộ số dư khi ẩn | Làm | `home_balances` | `test_hidden_state_never_exposes_balance_value` |

Việc bấm nút, đổi biểu tượng và lưu cờ thuộc client, không nằm trong repo này. Chưa có WO nào khác trong repo phục vụ phần đó.

Commit: `63939ab` (`feat(accounts): ẩn/hiện số dư trên màn hình chính [WO-2026-003]`).

## 2. Phạm vi thay đổi

| File | Thay đổi |
|---|---|
| `mbank/accounts.py` | Thêm `BALANCE_MASK`; `home_balances(repo, owner_id, hidden=True)`; thêm trường `hidden` vào mỗi dòng kết quả; đổi lỗi đọc repo thành `BankError(BALANCE_LOAD_FAILED)` |
| `mbank/errors.py` | Thêm `BALANCE_LOAD_FAILED = "ACCOUNT_BALANCE_LOAD_FAILED"` |
| `tests/test_accounts.py` | File mới, 7 test |
| `changesets/CS-003-001-an-hien-so-du.md` | File này |

Không đụng cấu hình, migration CSDL hay file khác.

## 3. Phần do AI sinh

| File / vùng | Nguồn gốc | Developer đã đọc kỹ? | Ghi chú |
|---|---|---|---|
| `mbank/accounts.py` (`home_balances`, `BALANCE_MASK`) | AI sinh | Chưa xác nhận | Cần đọc kỹ khối `try/except Exception`: bắt lỗi chung rồi ném lại thành mã lỗi chuẩn, giữ nguyên nhân gốc |
| `mbank/errors.py` (1 dòng) | AI sinh | Chưa xác nhận | Tên mã lỗi `ACCOUNT_BALANCE_LOAD_FAILED` theo mẫu `<MIỀN>_<LÝ_DO>` |
| `tests/test_accounts.py` | AI sinh | Chưa xác nhận | Dữ liệu test là dữ liệu bịa (số tài khoản 10 chữ số, owner `u1`/`u2`) |
| `changesets/CS-003-001-an-hien-so-du.md` | AI sinh | Chưa xác nhận | |

Không có phần nào do người viết. Cột "đã đọc kỹ" để `Chưa xác nhận` vì Developer chưa nói đã đọc.

## 4. Thay đổi cấu hình

Không áp dụng: không có tham số cấu hình mới. Không có secret trong hồ sơ.

## 5. Migration và rollback

Không áp dụng: không có migration CSDL. Rollback: revert commit `63939ab`.

## 6. Kết quả kiểm tại chỗ

| Việc kiểm | Lệnh | Kết quả |
|---|---|---|
| Unit test | `python3 -m unittest discover -s tests -t .` | Ran 11 tests, OK (4 test cũ, 7 test mới) |
| Sensor convention | `xdlc sensor` | Lệnh chỉ in bộ luật, không tự chấm. Tôi đối chiếu bằng tay các luật SEC-01, SEC-02, LOG-02, PII-01..03, ERR-01: không thấy vi phạm. Chưa có kết quả chấm tự động |
| Build | - | Chưa chạy: repo Python thuần, không có bước build |
| Lint | - | Chưa chạy: repo không có cấu hình linter |
| Độ phủ | - | Chưa chạy: repo không có công cụ đo độ phủ |

## 7. Quét bảo mật

Chưa chạy SAST, quét phụ thuộc và quét secret: repo không có công cụ này và tôi chưa chạy công cụ nào khác. Chỉ có đối chiếu thủ công regex của sensor ở mục 6.

## 8. Tương thích ngược

`home_balances()` đổi hành vi: mặc định ẩn nên giá trị `balance` mặc định là `"******"` thay vì số, và mỗi dòng có thêm trường `hidden`. Lỗi đọc repo nay là `BankError`. Tìm trong repo, hàm này chưa có nơi gọi. Client hay service nằm ngoài repo (nếu có) chưa được kiểm.

## 9. Audit log và giám sát

Không áp dụng: không chạm tiền, không ghi PII. Thay đổi không thêm log. Số dư (mức Hạn chế) không được ghi log.

## 10. Feature flag

Không áp dụng: không có feature flag. Tham số `hidden` do client truyền vào, không phải cờ cấu hình.

## 11. Hướng dẫn kiểm thử thủ công

Chạy `python3 -m unittest discover -s tests -t . -v` và xem 7 test trong `tests.test_accounts`. Kiểm tay trong Python: tạo `AccountRepo` với dữ liệu bịa, gọi `home_balances(repo, "u1")` thì mọi `balance` là `"******"`, gọi với `hidden=False` thì ra số thật. Chưa có kiểm thử trên màn hình thật vì không có client trong repo.

## 12. Nợ kỹ thuật cố ý

- Không mô phỏng "quá thời gian". `except Exception` bắt mọi lỗi từ `list_by_owner`; khi có repo thật cần thu hẹp loại lỗi.
- Không có comment `TODO`, `FIXME` hay `convention-ignore` mới.

## 13. Giới hạn đã biết

- BRD v2.0 là draft, chưa duyệt. Nó mâu thuẫn với `WO-MB-001` ở mặc định (Ẩn so với Hiện), phạm vi ghi nhớ (thiết bị so với người dùng + thiết bị), yêu cầu ẩn khi app chuyển nền và NFR (<100ms, screen reader). Nếu BRD đổi theo tệp gốc, REQ-001, REQ-006, ADR-01 (DEC-002), ADR-05 (DEC-003) và thiết kế liên quan phải làm lại. Với code này, đổi mặc định là đổi `hidden=True` thành `False` và sửa test.
- Chưa đọc được thiết kế OUT-003-02. Toàn bộ code dựa trên BRD v2.0 và `WO-MB-001`.
- Q-01 (có cần sinh trắc học khi chuyển từ ẩn sang hiện) chưa có đáp án, chưa làm.
- REQ-004 của tệp gốc (ẩn khi chuyển nền) chưa làm.
- Governance của BRD (G-001, G-002) và bước Thiết kế (G-052..G-055) có rà soát FAILED. Tech lead đã chấp nhận đi tiếp theo AAP.
- Tên nhánh `admin/WO-2026-003` khác quy ước `feature/<mã-wo>-<mô-tả>` của convention.

## Sai khác so với chuẩn

| Mục chuẩn | Mức | Tình trạng | Người chấp nhận | Thời điểm | Lý do |
|---|---|---|---|---|---|
| 3. Phần do AI sinh (cột đã đọc kỹ) | 🔴 | chưa phản hồi | | | Developer chưa xác nhận đã đọc |
| 6. Kết quả kiểm tại chỗ (build, lint, độ phủ) | 🔴 | chưa phản hồi | | | Repo không có công cụ tương ứng; sensor chưa có kết quả chấm tự động |
| 7. Quét bảo mật | 🔴 | chưa phản hồi | | | Chưa chạy SAST, quét phụ thuộc, quét secret |
| 8. Tương thích ngược | 🔴 | chưa phản hồi | | | Chưa kiểm được nơi gọi ngoài repo |
| 11. Hướng dẫn kiểm thử thủ công | 🟡 | chưa phản hồi | | | Không có client để kiểm trên màn hình |

## Nhật ký thay đổi

- v1: bản đầu, `status: draft`.
