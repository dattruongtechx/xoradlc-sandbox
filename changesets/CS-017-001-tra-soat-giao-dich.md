---
id: WO-2026-017/changeset-001
version: 2
status: draft
produced_by: xora-dev
inputs:
  - path: BRD-Tra-soat-giao-dich-WO-2026-017 (OUT-017-01)
    version: v0.1 (nháp do AI soạn, BA chưa chỉnh sửa; evidence_review FAILED G-069)
  - path: Thiet-ke-Tra-soat-giao-dich-WO-2026-017 (OUT-017-02)
    version: v0.2 (nháp; Security & Compliance có 4 cảnh báo đỏ G-070..G-073)
  - path: coding_convention (KB) v1.0, convention.md (repo) v1
commits: [6429e8d]
approved_by: null
approved_at: null
---

# Changeset: Gửi yêu cầu tra soát giao dịch (WO-2026-017)

Nhánh: `feature/WO-2026-017-tra-soat-giao-dich`, tạo từ `main` tại `43d0feb` và đã map WO bằng `xdlc link`. PR: chưa tạo. Nhánh chưa push.

BRD và thiết kế đều là bản nháp, nên changeset này có thể phải làm lại khi hai tài liệu được duyệt.

## 1. Truy vết

| REQ / luật | Nội dung | Trạng thái | Code (`mbank/disputes.py`) | Test (`tests/test_disputes.py`) |
|---|---|---|---|---|
| REQ-001 (Must) | Nút "Tra soát" chỉ có với loại hợp lệ, trong 90 ngày | Làm phần backend | `is_eligible` | `EligibilityTest` (4 test) |
| REQ-002 (Must) | Chọn lý do, mô tả, gửi; tạo "Đã tiếp nhận" kèm mã tra soát | Làm | `DisputeService.submit`, `Reason` | `test_missing_reason_rejected`, `test_creates_received_dispute_with_code` |
| REQ-003 (Should) | Tối đa 3 ảnh JPG/PNG, mỗi ảnh ≤ 5MB | Làm | `upload_attachments`; kiểm số ref trong `submit` | `AttachmentTest` (6 test) |
| REQ-004 (Must) | Danh sách yêu cầu của tôi: mã, trạng thái, hạn trả lời | Làm | `list_mine` | `test_list_shows_code_status_due_date_and_result_when_done`, `test_list_only_own_disputes` |
| REQ-005 (Should) | Push khi đổi trạng thái | Làm qua interface `Notifier` | `on_status_changed` | `test_push_has_code_only_and_once_per_change` |
| REQ-006 (Must) | Xác thực PIN khi Gửi, không OTP | Backend chỉ nhận kết quả xác thực (DEC-008) | `PinAuthResult`, `submit` | `test_wrong_pin_creates_nothing`, `test_pin_value_never_sent` |
| REQ-007 (Must) | Trường "kết quả" chỉ có khi "Đã xong" | Làm | `list_mine`, `on_status_changed` | `test_no_result_field_before_done` |
| REQ-008 (Must) | Form điền sẵn mã GD, thời gian, số tiền | Làm | `prefill_form` | `test_prefill_has_tx_id_time_amount` |
| BR-01 | Một giao dịch chỉ có một yêu cầu đang mở | Làm, theo cặp (mã GD, tài khoản) | `DisputeRepo.open_for` | `test_already_open_returns_existing_code`, `test_done_dispute_allows_new_one` |
| BR-02 | Lý do "Không thực hiện" thì gợi ý khoá thẻ | Trả cờ `suggest_lock_card` | `SubmitResult` | `test_not_performed_suggests_lock_card` |
| BR-03 / BR-04 | Loại GD hợp lệ; 90 ngày | Làm | `ELIGIBLE_KINDS`, `DISPUTE_WINDOW_DAYS` | `EligibilityTest` |
| EX-01 | Ảnh lỗi thì vẫn gửi được, báo lý do | Làm | `upload_attachments` | `test_upload_failure_reported_not_raised` |
| EX-02 | Quá 90 ngày | Từ chối khi gửi. Số tổng đài thuộc client và chưa có (ASM-11) | `submit` | `test_over_90_days_rejected_on_submit` |
| EX-03 | Đã có yêu cầu đang mở | Ném `DisputeAlreadyOpen`, kèm mã yêu cầu cũ | `submit` | `test_already_open_returns_existing_code` |
| EX-04 | Sai PIN | Không tạo yêu cầu. Quy tắc khoá PIN thuộc dịch vụ PIN hiện có (ASM-08) | `submit` | `test_wrong_pin_creates_nothing` |
| EX-05 | Gửi lặp | Cùng key thì trả lại yêu cầu cũ (D2) | `submit` | `test_replay_same_key_returns_same_dispute`, `test_key_reused_for_other_tx_conflicts` |
| EX-06 | Lỗi hoặc timeout khi gửi | Ném `DISPUTE_SUBMIT_FAILED`, không lưu gì; gửi lại cùng key không tạo trùng | `submit` | `test_intake_timeout_creates_nothing`, `test_no_dispute_code_is_not_success`, `test_retry_after_failure_succeeds_with_same_key` |
| EX-07 | Thoát form giữa chừng | Không áp dụng ở backend: chưa gọi `submit` thì không có gì được lưu | - | - |
| EX-08 | Push lỗi | Trạng thái mới vẫn được lưu | `on_status_changed` | `test_push_failure_keeps_new_status`, `test_non_io_push_error_not_swallowed` |
| EX-09 | Lỗi tải danh sách | Ném `DISPUTE_LIST_LOAD_FAILED` | `list_mine` | `test_list_load_failure_raises_standard_error` |

Quyết định thiết kế đã áp dụng:
- DEC-006: gọi đồng bộ, có timeout.
- DEC-007: dùng idempotency key do client sinh.
- DEC-008: không nhận và không gửi giá trị PIN, chỉ gửi `pin_session_id`.
- DEC-009: ảnh đi qua interface `AttachmentStore`, hệ thống ngoài chỉ nhận ref.

Quyết định do Developer chốt trong phiên:
- D1: thêm `Transaction.kind`.
- D2: gửi lặp cùng key thì trả lại yêu cầu cũ.
- D3: mã tra soát và hạn trả lời do hệ thống tiếp nhận trả về.

Commit: `6429e8d` (`feat(disputes): gửi yêu cầu tra soát giao dịch [WO-2026-017]`).

## 2. Phạm vi thay đổi

| File | Thay đổi |
|---|---|
| `mbank/disputes.py` | File mới (308 dòng) gồm: enum `Reason` và `Status`; dataclass `Dispute`, `PinAuthResult`, `Attachment`, `IntakeRequest`, `IntakeResult`, `SubmitResult`; Protocol `DisputeIntakeClient`, `AttachmentStore`, `Notifier`; class `DisputeRepo` (in-memory), `DisputeAlreadyOpen`, `DisputeService`; hàm `is_eligible`, `prefill_form`, `upload_attachments` |
| `mbank/errors.py` | Thêm 10 mã lỗi `DISPUTE_*` |
| `mbank/transactions.py` | Thêm trường `kind: str \| None = None` vào `Transaction`. Thêm `from __future__ import annotations` để chạy được trên Python 3.9 |
| `tests/test_disputes.py` | File mới, 35 test |
| `changesets/CS-017-001-tra-soat-giao-dich.md` | File này (chưa commit) |

Không có migration CSDL. Cấu hình mới: xem mục 4.

## 3. Phần do AI sinh

| File / vùng | Nguồn gốc | Developer đã đọc kỹ? | Ghi chú |
|---|---|---|---|
| `mbank/disputes.py` (toàn file) | AI sinh | Chưa xác nhận | Nên đọc kỹ `DisputeService.submit`. Các bước kiểm chạy theo thứ tự: idempotency, lý do, quyền sở hữu, điều kiện tra soát, yêu cầu đang mở, PIN, số ảnh, gọi hệ thống tiếp nhận, lưu, audit. Kiểm idempotency đứng trước kiểm PIN, nên gọi lại cùng key thì không phải xác thực lại |
| `mbank/disputes.py` `on_status_changed` | AI sinh | Chưa xác nhận | Chưa xác thực bên gọi (xem mục 13) |
| `mbank/disputes.py` các khối `except` | AI sinh | Chưa xác nhận | `upload_attachments` và push chỉ bắt `OSError`. `submit` (gọi hệ thống tiếp nhận) và `list_mine` bắt `Exception` rồi ném lại thành mã lỗi chuẩn, giữ nguyên nhân gốc |
| `mbank/errors.py` (10 dòng) | AI sinh | Chưa xác nhận | |
| `mbank/transactions.py` (5 dòng) | AI sinh | Chưa xác nhận | Đổi model dùng chung (D1) |
| `tests/test_disputes.py` | AI sinh | Chưa xác nhận | Dữ liệu bịa: tài khoản 10 chữ số, owner `u1`/`u2`, ảnh giả chỉ có magic bytes |
| `changesets/CS-017-001-tra-soat-giao-dich.md` | AI sinh | Chưa xác nhận | |

Không có phần nào do người viết. Cột "đã đọc kỹ" ghi `Chưa xác nhận` vì Developer chưa nói đã đọc file nào.

## 4. Thay đổi cấu hình

| Tham số | Nguồn | Mặc định | Theo môi trường |
|---|---|---|---|
| `DISPUTE_INTAKE_TIMEOUT_SECONDS` | Biến môi trường | `10` (giây) | Chưa có giá trị cho DEV/UAT/PROD. Số 10 là [GIẢ ĐỊNH]: thiết kế DEC-006 chỉ nói "có timeout", không nêu số |

Không có secret trong hồ sơ và trong code.

## 5. Migration và rollback

Không áp dụng migration: repo chỉ lưu in-memory, không có CSDL. Rollback bằng revert commit `6429e8d`. Thay đổi chỉ thêm code; `Transaction.kind` có giá trị mặc định nên revert không ảnh hưởng dữ liệu.

## 6. Kết quả kiểm tại chỗ

| Việc kiểm | Lệnh | Kết quả |
|---|---|---|
| Unit test | `python3 -m unittest discover -s tests -t .` (Python 3.9.6) | Ran 46 tests, OK (11 test cũ, 35 test mới) |
| Sensor convention | `xdlc sensor` | Lệnh in bộ luật coding_convention v1.0 từ KB. Tôi chạy bằng script regex các luật SEC-01, SEC-02, LOG-02, PII-01..03, ERR-01 trên 4 file đổi: 0 vi phạm. Tôi cũng chạy bằng script regex trong `convention.md` (SEC-001, SEC-002, LOG-003, PII-001, ERR-002, TODO-001...): 0 vi phạm |
| Lệch convention mục 1–2 (rà thủ công) | `xdlc sensor report` | Lần rà đầu có 5 điểm. Đã sửa 2 điểm: bắt lỗi chung chung ở upload ảnh và push; tên nhánh. Đã gửi 3 alert lên Xora DLC (WO-2026-017 · Thực hiện): `CONV-WEBHOOK-SIG` (red), `CONV-RETRY` (yellow), `CONV-ERR-REQID` (yellow) |
| Build | - | Chưa chạy: repo Python thuần, không có bước build |
| Lint | - | Chưa chạy: repo không có cấu hình linter |
| Độ phủ | - | Chưa chạy: repo không có công cụ đo độ phủ |
| Python 3.10+ | - | Chưa chạy: máy chỉ có Python 3.9.6, trong khi convention yêu cầu 3.10+ |

## 7. Quét bảo mật

Chưa chạy SAST, quét phụ thuộc và quét secret, vì repo không có công cụ này. Đã làm ở mức thay thế:
- Chạy regex SEC/PII của sensor (mục 6).
- Không thêm thư viện ngoài, vẫn chỉ dùng thư viện chuẩn.
- Test `test_pin_value_never_sent` và `test_audit_log_masks_account` kiểm rằng PIN và số tài khoản rõ không bị gửi đi hay ghi log.

## 8. Tương thích ngược

- `Transaction` có thêm trường `kind`, mặc định `None`. Code tạo `Transaction` theo vị trí (5 tham số) vẫn chạy, và 11 test cũ vẫn qua. Giao dịch cũ có `kind=None` thì không được tra soát cho tới khi được phân loại.
- `errors.py` chỉ thêm hằng mới.
- Code ngoài repo (nếu có) chưa được kiểm.

## 9. Audit log và giám sát

| Sự kiện | Logger | Trường | Che PII |
|---|---|---|---|
| Gửi yêu cầu thành công | `mbank.audit` | `who` = hash(owner_id), `at`, `tx`, `acct`, `code`, `reason` | owner_id được băm bằng `masking.hash`; tài khoản được che bằng `masking.mask`. Mô tả và ảnh không được ghi log |
| Đổi trạng thái | `mbank.audit` | `who=intake`, `at`, `code`, `status` | Không có PII |
| Lỗi gọi hệ thống tiếp nhận / tải ảnh / push | `mbank.disputes` (warning) | mã GD hoặc mã tra soát, owner băm, tên loại lỗi | Không ghi nội dung request hay response |

Mã giao dịch (`tx`) được ghi rõ. Mức phân loại của "Thông tin GD" chưa được chốt (SEC-D02), nên nếu bị xếp mức Hạn chế thì phải che thêm. Lần gửi bị từ chối (sai PIN, không đủ điều kiện) chưa có audit log riêng.

## 10. Feature flag

Không áp dụng: không có feature flag.

## 11. Hướng dẫn kiểm thử thủ công

Chưa có client hay API, nên chỉ kiểm được ở mức hàm:
1. Chạy `python3 -m unittest tests.test_disputes -v` và xem 35 test.
2. Mở Python, dùng dữ liệu bịa: tạo `AccountRepo` có tài khoản `0000111122` của `u1`, và `Transaction("tx1", "0000111122", -50000, "x", <hôm qua>, "transfer_out")`. Tạo một fake intake trả `IntakeResult("TS-1", <ngày>)`, rồi gọi:
   - `submit(..., PinAuthResult(True, "s1"))` → kết quả có trạng thái `received` và mã `TS-1`.
   - Gọi lại với cùng key → nhận lại cùng đối tượng, intake chỉ bị gọi 1 lần.
   - Gọi với key khác cho cùng giao dịch → ném `DisputeAlreadyOpen`.
   - Giao dịch 91 ngày trước, hoặc `kind="bill_payment"` → ném `DISPUTE_NOT_ELIGIBLE`.
3. QA cần kiểm lại trên client khi có: ẩn/hiện nút, form điền sẵn, PIN, số tổng đài (EX-02), thoát form (EX-07).

## 12. Nợ kỹ thuật cố ý

- `DisputeRepo` và map idempotency key (`_by_key`) đang ở trong bộ nhớ, giống `TransferService._seen`. Khi có CSDL cần lưu bền và cần ràng buộc unique cho key và cho yêu cầu đang mở (BR-01), để tránh race giữa hai request đồng thời.
- Hệ thống tiếp nhận, kho ảnh và push mới chỉ là Protocol, chưa có bản cài đặt thật.
- Không có comment `TODO`, `FIXME` hay `convention-ignore` mới.

## 13. Giới hạn đã biết

- **Chưa xác thực callback trạng thái** (`on_status_changed`, alert `CONV-WEBHOOK-SIG` red). Convention yêu cầu webhook xác minh chữ ký, nhưng thiết kế chưa có cơ chế xác thực API (SEC-A03). Không được mở hàm này ra ngoài trước khi có cơ chế đó.
- **Chưa có client thật cho hệ thống tiếp nhận tra soát.** Còn thiếu API contract (tên field idempotency key, format response), TLS (SEC-A01) và xác thực API (SEC-A03).
- **Chưa có mã hoá at-rest thật cho ảnh** (DEC-009), vì chưa có nơi quản lý khoá (SEC-A02).
- **Chưa tự thử lại khi gọi hệ thống ngoài** (alert `CONV-RETRY`). Theo DEC-006/EX-06, khách gửi lại bằng cùng key. Nếu cần retry có giới hạn thì thiết kế phải chốt.
- **Lỗi trả ra ngoài chưa kèm mã yêu cầu** (alert `CONV-ERR-REQID`). `BankError` dùng chung chưa có trường này, ngoài phạm vi WO.
- **Mâu thuẫn BRD và thiết kế chưa được giải quyết:** BRD ghi "mã PIN đã xác thực", còn DEC-008 ghi chỉ gửi kết quả xác thực. Code theo DEC-008. BA/ATTT chưa xác nhận.
- **DEC-005** (ATTT chỉ cho dùng PIN) mới là lời BA kể lại, chưa có văn bản.
- **ASM-04** (giao dịch đang xử lý hoặc đã trừ tiền nhưng chưa thành công vẫn được tra soát) chưa mô hình hoá, vì `Transaction` không có trạng thái.
- **ASM-08** (số lần khoá PIN), **ASM-11** (số tổng đài), **ASM-17/18** (phân loại và che ảnh), **ASM-19** (thời gian lưu dữ liệu) chưa có giá trị và chưa làm.
- **[GIẢ ĐỊNH]** đã dùng:
  - timeout 10 giây;
  - ngày thứ 90 vẫn được tra soát;
  - BR-01 tính theo cặp (mã GD, tài khoản), vì bên chuyển và bên nhận dùng chung mã GD;
  - giao dịch `kind=None` không được tra soát;
  - định dạng ảnh xét theo magic bytes;
  - kiểm idempotency đứng trước PIN.
- **Chưa test trên Python 3.10+.**
- **Thứ tự thao tác:** `submit` lưu yêu cầu sau khi hệ thống tiếp nhận đã trả mã. Nếu lưu cục bộ thất bại ở bước này, hệ thống ngoài đã có yêu cầu còn app thì không. Lần gửi lại cùng key dựa vào idempotency phía hệ thống tiếp nhận (DEC-007), điều này chưa kiểm được vì thiếu API contract.

## Sai khác so với chuẩn

| Mục chuẩn | Mức | Tình trạng | Người chấp nhận | Thời điểm | Lý do |
|---|---|---|---|---|---|
| 3. Phần do AI sinh (cột đã đọc kỹ) | 🔴 | chưa phản hồi | | | Developer chưa xác nhận đã đọc file nào |
| 4. Thay đổi cấu hình (giá trị theo môi trường) | 🔴 | chưa phản hồi | | | `DISPUTE_INTAKE_TIMEOUT_SECONDS` chưa có giá trị DEV/UAT/PROD; mặc định 10s là giả định |
| 6. Kết quả kiểm tại chỗ (build, lint, độ phủ, Python 3.10+) | 🔴 | chưa phản hồi | | | Repo không có công cụ tương ứng; máy chỉ có Python 3.9.6 |
| 7. Quét bảo mật | 🔴 | chưa phản hồi | | | Chưa chạy SAST, quét phụ thuộc, quét secret |
| 11. Hướng dẫn kiểm thử thủ công | 🟡 | chưa phản hồi | | | Chỉ có hướng dẫn mức hàm, chưa có client / API |

## Nhật ký thay đổi

- v1: bản đầu, `status: draft`.
- v2: Developer yêu cầu commit mà chưa trả lời khối cảnh báo lệch chuẩn. Giữ nguyên nội dung, thêm mục *Sai khác so với chuẩn* với 5 điểm, tình trạng `chưa phản hồi`; cột *Người chấp nhận* và *Thời điểm* để trống.
