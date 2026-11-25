---
id: WO-2026-043/changeset-001
version: 2
status: awaiting_review
produced_by: xora-dev
inputs:
  - path: BRD-Khoa-mo-khoa-the-WO-2026-043 (OUT-043-01)
    version: v1 / nội dung v0.2 (AI soạn nháp, BA chưa rà)
  - path: Thiet-ke-Khoa-mo-khoa-the-WO-2026-043 (OUT-043-02)
    version: v2 / nội dung v0.4 (Tech lead; còn 🔴 SEC-A02 chưa xử lý)
  - path: API-card-lock
    version: v0.1 (tài liệu nguồn của OUT-043-02)
commits: [cb4ba38]
approved_by: null
approved_at: null
---

# Changeset: Khoá / mở khoá thẻ tạm thời (WO-2026-043)

Nhánh: `feature/WO-2026-043-khoa-mo-khoa-the`, tạo từ `main` `43d0feb`, đã map bằng `xdlc link WO-2026-043 --step impl`. Commit code: `cb4ba38` (`feat(cards): khoá/mở khoá thẻ tạm thời [WO-2026-043]`). Hồ sơ này ở commit riêng ngay sau. PR: xem mô tả PR trên GitHub.

BRD và thiết kế đều là bản nháp chưa được BA/PO rà (RISK-03). Kết quả có thể phải làm lại khi hai tài liệu được chốt.

## 1. Truy vết

| REQ (BRD v0.2) | Ưu tiên | Trạng thái | Code (`mbank/cards.py`) | Test (`tests/test_cards.py`) |
|---|---|---|---|---|
| REQ-001 Khoá thẻ ACTIVE → TEMP_LOCKED | Must | Làm | `CardLockService.lock` | `LockTest.test_lock_active_card`, `UnlockTest.test_lock_then_unlock_round_trip` |
| REQ-002 Khoá không cần OTP | Must | Làm (L1 không đòi step-up). Q-02 BRD đang chờ ATTT | `lock` | `LockTest.test_lock_active_card` |
| REQ-003 Lý do khoá, mặc định "Tạm không dùng" | Could | Làm | `LOCK_REASONS`, `lock` | `LockErrorTest.test_invalid_reason_or_missing_key`, `LockTest.test_audit_has_who_when_what_without_raw_ids` |
| REQ-004 Từ chối giao dịch khi thẻ khoá | Must | Làm ở `authorize` (`CARD_LOCKED`). Phía CMS từ chối giao dịch POS/ATM nằm ngoài repo | `CardService.authorize` | `AuthorizeTest.*` |
| REQ-005 Mở khoá cần xác thực mạnh | Must | Làm: thiếu token → `STEP_UP_REQUIRED`, sai / hết hạn / đã dùng / khác thẻ → `STEP_UP_INVALID` | `unlock` | `UnlockErrorTest.test_missing_token`, `test_wrong_or_foreign_or_reused_token` |
| REQ-006 Mở khoá thành công → ACTIVE | Must | Làm | `unlock` | `UnlockTest.test_unlock_locked_card` |
| REQ-007 Push + SMS khi đổi trạng thái thật | Must | Làm. Gửi đồng bộ qua `Notifier`, chưa có Notification Hub | `_notify` | `NotifyTest.*` |
| REQ-008 Gọi lặp không lỗi (`changed=false`) | Must | Làm (a) và (b) | `_change`, `_cms_change` | `LockTest.test_lock_already_locked_is_noop`, `test_replay_same_key_returns_same_result_once`, `UnlockTest.test_unlock_active_card_is_noop` |
| REQ-009 Trạng thái không phù hợp → 409 `CARD_STATUS_NOT_ALLOWED` | Must | Làm; BLOCKED có thông điệp riêng | `_cms_change` | `LockErrorTest.test_blocked_card_not_allowed`, `test_expired_card_not_allowed`, `UnlockErrorTest.test_blocked_card_not_allowed` |
| REQ-010 Gợi ý báo mất khi lý do là mất thẻ / nghi lộ | Should | Làm (`nextSteps`) | `_response` | `LockTest.test_report_lost_hint` |
| REQ-011 Hiện trạng thái mới (BA bổ sung, chưa PO xác nhận) | Must (đề xuất) | Phần backend: trả `status`, `statusLabel`, `actions`. Màn hình thuộc client | `_response`, `get_status` | `LockTest.test_lock_active_card`, `test_cms_is_source_of_truth` |
| REQ-012 Sai 3 lần → 423 `STEP_UP_LOCKED` (BA bổ sung) | Must (đề xuất) | **Không làm ở đây.** Theo OUT-043-02, việc đếm sai nằm ở bước S1/S2 của step-up service dùng chung (WO-MB-044) | - | - |

Quyết định và ADR đã áp dụng:

| Mã | Nội dung | Code | Test |
|---|---|---|---|
| DEC-001 / ADR-01 | Mở khoá thẻ đã ACTIVE → 200 `changed=false`, không 409 | `_cms_change` | `UnlockTest.test_unlock_active_card_is_noop` |
| DEC-002 | Chỉ gửi thông báo khi `changed=true` | `_change` | `LockTest.test_lock_already_locked_is_noop`, `UnlockTest.test_unlock_active_card_is_noop` |
| DEC-003 | 4 số cuối thẻ chỉ có trong push, không có trong SMS | `_notify` | `NotifyTest.test_sms_has_no_card_digits_push_has_last4` |
| ADR-02 | Gọi CMS đồng bộ, timeout 5 giây; lỗi → hỏi C3, thử lại 1 lần, vẫn lỗi → 503 | `_call_cms` | `LockErrorTest.test_cms_down_returns_503_and_card_stays_active`, `LockTest.test_cms_timeout_*` |
| ADR-03 | Idempotency 2 lớp: lớp 1 lưu theo (khách, thẻ, key) 24 giờ; lớp 2 gửi cùng key sang CMS | `_change`, `_call_cms` | `LockTest.test_replay_same_key_returns_same_result_once`, `LockErrorTest.test_same_key_different_payload_conflicts` |
| ADR-04 | Mở khoá thẻ ACTIVE vẫn cần step-up hợp lệ | `unlock` | `UnlockErrorTest.test_active_card_still_needs_token` |
| ADR-05 | Rate limit 10 lần/giờ/thẻ (cấu hình được) | `_check_rate` | `LockErrorTest.test_rate_limit_*` |
| ADR-06 | Tuần tự theo `cardId` | `_card_lock` | `ConcurrencyTest.*` |
| EX-01 / EX-02 | CMS lỗi → thông điệp kèm tổng đài; CMS là nguồn chuẩn của trạng thái | `_call_cms`, `get_status` | `LockTest.test_cms_is_source_of_truth`, `test_get_status_cms_down` |

## 2. Phạm vi thay đổi

| File | Thay đổi |
|---|---|
| `mbank/cards.py` | Thêm hằng trạng thái (`temp_locked`, `blocked`), trường `Card.last4`, cấu hình qua biến môi trường; `authorize()` chặn thẻ khoá và thay `print` bằng logger; thêm `CmsClient`, `StepUpVerifier`, `Notifier`, `AuditLog` (Protocol), `RequestContext`, `CardLockService` (`lock`, `unlock`, `get_status`) |
| `mbank/errors.py` | Thêm 9 mã lỗi theo bảng 4.5 của OUT-043-02, cộng `CARD_LOCKED` |
| `tests/test_cards.py` | File mới, 35 test, có CMS / step-up / thông báo / audit giả |
| `changesets/CS-043-001-khoa-mo-khoa-the.md` | File này |

Không đụng migration CSDL. Không thêm thư viện ngoài.

## 3. Phần do AI sinh

| File / vùng | Nguồn gốc | Developer đã đọc kỹ? | Ghi chú |
|---|---|---|---|
| `mbank/cards.py` `CardLockService._change` | AI sinh | Chưa xác nhận | Thứ tự: khoá theo thẻ → idempotency → rate limit → CMS → audit; thông báo gửi sau khi nhả khoá |
| `mbank/cards.py` `_call_cms`, `_cms_change` | AI sinh | Chưa xác nhận | Retry khi CMS timeout và cách quyết định 409 / `changed=false`; chứa 2 `[GIẢ ĐỊNH]` |
| `mbank/cards.py` `unlock` | AI sinh | Chưa xác nhận | Step-up được kiểm và tiêu thụ trước idempotency (theo sequence diagram thiết kế) |
| `mbank/cards.py` `_notify` | AI sinh | Chưa xác nhận | `except Exception` ghi log rồi bỏ qua lỗi gửi; nội dung push/SMS do AI tự viết |
| `mbank/cards.py` `CardService.authorize`, hằng số, Protocol | AI sinh | Chưa xác nhận | |
| `mbank/errors.py` (12 dòng) | AI sinh | Chưa xác nhận | Tên mã lấy theo thiết kế, trừ `CARD_LOCKED` |
| `tests/test_cards.py` | AI sinh | Chưa xác nhận | Dữ liệu bịa (`card-0001`, `cust-001`, IP `10.0.0.1`) |
| `changesets/CS-043-001-khoa-mo-khoa-the.md` | AI sinh | Chưa xác nhận | |

Không có phần nào do người viết. Cột "đã đọc kỹ" để `Chưa xác nhận` vì Developer chưa nói đã đọc.

## 4. Thay đổi cấu hình

| Biến môi trường | Mặc định | DEV / UAT / PROD | Căn cứ |
|---|---|---|---|
| `MBANK_CMS_TIMEOUT_SECONDS` | `5` | Chưa có giá trị riêng theo môi trường | ADR-02 |
| `MBANK_CARD_LOCK_RATE_LIMIT_PER_HOUR` | `10` | Chưa có; ATTT chưa chốt (Q-03) | ADR-05 |
| `MBANK_HOTLINE` | `1900 0000` (giá trị mẫu trong thiết kế) | Cần số tổng đài thật cho UAT / PROD | REQ-007, EX-01 |

Không có secret trong code hay hồ sơ.

## 5. Migration và rollback

Không áp dụng: không có migration CSDL (dữ liệu nằm trong bộ nhớ). Rollback: revert commit của changeset này. Thẻ đang `temp_locked` trên CMS lúc rollback sẽ không mở khoá được qua app cũ; cần mở qua kênh tổng đài.

## 6. Kết quả kiểm tại chỗ

| Việc kiểm | Lệnh | Kết quả |
|---|---|---|
| Unit test toàn bộ | `python3 -m unittest discover -s tests -t .` | Ran 46 tests, OK (11 cũ, 35 mới), Python 3.9.6 |
| Test đồng thời lặp | `python3 -m unittest tests.test_cards.ConcurrencyTest` × 20 | 20/20 OK |
| Kiểm test bắt lỗi thật | Monkeypatch bỏ khoá theo `cardId`, chạy `ConcurrencyTest` | FAILED (failures=1), đúng như mong đợi |
| Sensor convention | `xdlc sensor` rồi đối chiếu regex trên 3 file đổi | 2 kết quả LOG-02 🔴 (dòng 188, 241; xem mục 12). Developer chọn vẫn push; đã gửi bằng `xdlc sensor report` ("sent 2 alert(s) to Xora DLC (WO-2026-043 · Thực hiện)"). Chưa có chấm tự động của plugin |
| Python 3.10+ | - | Chưa chạy: máy chỉ có Python 3.9.6 |
| Build | - | Không áp dụng: Python thuần, không có bước build |
| Lint | - | Chưa chạy: repo không có cấu hình linter |
| Độ phủ | - | Chưa chạy: repo không có công cụ đo độ phủ |

## 7. Quét bảo mật

Chưa chạy SAST, quét phụ thuộc và quét secret: repo không có công cụ này. Không thêm phụ thuộc mới. Chỉ có đối chiếu regex SEC-01, SEC-02, PII-01..03 của sensor: không có kết quả.

Thiết kế OUT-043-02 còn phát hiện 🔴 **SEC-A02** (mã hoá khi lưu tạm `X-Step-Up-Token` 120 giây, nơi quản lý khoá). Code này không lưu token; phần đó thuộc step-up service và chưa có thiết kế.

## 8. Tương thích ngược

- `CardService.authorize()` nay **ném** `BankError(CARD_LOCKED)` với thẻ `temp_locked` thay vì trả `False`. Thẻ `expired` / `closed` vẫn trả `False` như cũ. Trong repo không có nơi gọi `authorize`; nơi gọi ngoài repo (nếu có) cần bắt lỗi mới.
- `Card` có thêm trường `last4` (mặc định rỗng), không phá chỗ tạo `Card` cũ.
- Hai API L1 / L2 là mới. Lớp HTTP chưa có trong repo.

## 9. Audit log và giám sát

- Audit ghi qua `AuditLog.record` mỗi khi trạng thái đổi thật (`changed=true`). Trường: `at`, `actor` (băm mã khách), `action` (`CARD_TEMP_LOCK` / `CARD_TEMP_UNLOCK`), `card` (băm), `previousStatus`, `status`, `reason`, `requestId`, `deviceId`, `ip`.
- Gọi lặp hoặc `changed=false` không ghi audit `[GIẢ ĐỊNH]`. Lần step-up sai không ghi audit, chỉ ghi log mức info.
- Log ứng dụng (`mbank.cards`) chỉ có mã thẻ đã băm hoặc che, không có số thẻ, token, mã khách dạng rõ; có test kiểm (`NotifyTest.test_logs_do_not_contain_card_id`).
- Chưa có metric hay cảnh báo giám sát (tỉ lệ 503 từ CMS, số lần rate limit).

## 10. Feature flag

Không áp dụng: không có feature flag.

## 11. Hướng dẫn kiểm thử thủ công

Chạy `python3 -m unittest tests.test_cards -v`. Kiểm tay trong Python với các lớp giả ở `tests/test_cards.py` (`make()` dựng sẵn thẻ `card-0001` của `cust-001`):

| Ca | Bước | Kết quả mong đợi |
|---|---|---|
| Khoá | `svc.lock(ctx(), "card-0001", "k1")` | `changed=True`, `status=TEMP_LOCKED`, 1 push + 1 SMS, 1 dòng audit |
| Khoá lại | gọi lại với key `k2` | `changed=False`, không thông báo |
| Giao dịch khi khoá | `cards.authorize("card-0001", 1000)` | `BankError` `CARD_LOCKED` |
| Mở khoá thiếu token | `svc.unlock(ctx(), "card-0001", "k3", None)` | `STEP_UP_REQUIRED`, thẻ vẫn khoá |
| Mở khoá | phát token bằng `step_up.issue("t")`, gọi `unlock` | `changed=True`, `status=ACTIVE` |
| CMS sập | đặt `cms.fail_change=2`, `cms.fail_status=True`, gọi `lock` | `CARD_SERVICE_UNAVAILABLE`, thông điệp có số tổng đài |

Chưa kiểm được trên app thật và CMS thật: repo không có client, HTTP layer hay kết nối CMS.

## 12. Nợ kỹ thuật cố ý

| Vị trí | Nội dung | Hướng nâng cấp |
|---|---|---|
| `mbank/cards.py` `authorize` — `TODO WO-2026-043 Q-01` | Chặn mọi giao dịch khi thẻ khoá, kể cả giao dịch định kỳ | Sửa khi PO Thẻ trả lời Q-01 / BR-03 |
| `mbank/cards.py` `StepUpVerifier` — `TODO WO-2026-043 SEC-A02` | Chưa có lưu trữ token mã hoá | Tech lead bổ sung thiết kế; hiện thực trong step-up service |
| `mbank/cards.py` `CardLockService.__init__` — `TODO WO-2026-043 ADR-03/ADR-05/ADR-06` | Idempotency, rate limit, khoá theo thẻ nằm trong bộ nhớ một tiến trình | Chuyển sang kho dùng chung và khoá phân tán khi có hạ tầng |
| `mbank/cards.py` `unlock` — `TODO WO-2026-043 Q-05` | Mọi thẻ `temp_locked` đều cho khách mở khoá | Theo trường CMS (giả định `lockedBy`) khi đội CMS trả lời |
| `mbank/cards.py` `_notify` | Gửi đồng bộ, lỗi chỉ ghi log (bắt `Exception`) | Bắn sự kiện `card.unlocked` / `card.locked` tới Notification Hub bất đồng bộ như thiết kế |
| LOG-02 tại `mbank/cards.py` dòng 188 và 241 | Regex bắt chữ `request=` trong chuỗi format; giá trị là `ctx.request_id`, không phải nguyên request | Developer chọn vẫn push; cảnh báo đã gửi lên Xora DLC. Sửa sau: đổi key thành `request_id=` |

Không có `convention-ignore` mới.

## 13. Giới hạn đã biết

- BRD v0.2 và thiết kế v0.4 là bản nháp, chưa BA/PO rà (RISK-03). REQ-011, REQ-012 chưa được PO xác nhận.
- **Q-12 (mâu thuẫn trong nguồn):** bảng lỗi L1 ghi "khoá thẻ không ở trạng thái ACTIVE → 409", REQ-008a ghi "khoá thẻ đã TEMP_LOCKED → 200 `changed=false`". Code theo REQ-008a và ADR-01, kể cả khi CMS trả 409 với trạng thái đích. Cần Tech lead xác nhận.
- **Q-05:** chưa phân biệt thẻ do khách hay do ngân hàng khoá; khách có thể mở khoá thẻ ngân hàng khoá nếu CMS trả `TEMP_LOCKED` cho cả hai.
- **SEC-A02 🔴** của thiết kế chưa xử lý.
- L2 kiểm và tiêu thụ step-up **trước** idempotency (theo sequence diagram). App gửi lại cùng `Idempotency-Key` với token cũ sẽ nhận 401. Rate limit cũng kiểm sau khi token đã bị tiêu thụ.
- CMS timeout nhưng thực ra đã đổi: `previousStatus` lấy từ trạng thái Mobile Backend đang giữ `[GIẢ ĐỊNH]`.
- REQ-012 (423 sau 3 lần sai) không làm ở đây.
- Body của L2 không có trong thiết kế; code không nhận body.
- Mã `CARD_LOCKED`, nhãn và `actions` cho trạng thái ACTIVE, nội dung push / SMS là AI tự đặt, chưa có trong nguồn.
- Các mã `VALIDATION_ERROR`, `IDEMPOTENCY_KEY_REUSED`, `RATE_LIMITED`, `STEP_UP_*` không theo dạng `<MIỀN>_<LÝ_DO>` của convention; giữ đúng hợp đồng API của thiết kế.
- `BankError` chưa mang mã yêu cầu, trong khi convention KB yêu cầu lỗi trả ra ngoài có mã yêu cầu (cùng vấn đề G-076 của WO-2026-017).
- Không có HTTP layer: chưa kiểm header `Authorization`, `X-Request-Id`, mã HTTP thật, `401 UNAUTHENTICATED`, `422 BIOMETRIC_NOT_ENROLLED`.
- Chưa chạy trên Python 3.10+.

## Sai khác so với chuẩn

| Mục chuẩn | Mức | Tình trạng | Người chấp nhận | Thời điểm | Lý do |
|---|---|---|---|---|---|
| 3. Phần do AI sinh (cột đã đọc kỹ) | 🔴 | chưa phản hồi | | | Developer chưa xác nhận đã đọc vùng nào |
| 4. Thay đổi cấu hình (giá trị theo môi trường) | 🔴 | chưa phản hồi | | | Chưa có giá trị UAT/PROD cho hotline, timeout, rate limit |
| 6. Kết quả kiểm tại chỗ (lint, độ phủ, Python 3.10+) | 🔴 | chưa phản hồi | | | Repo không có linter/công cụ độ phủ; máy chỉ có Python 3.9.6 |
| 7. Quét bảo mật | 🔴 | chưa phản hồi | | | Chưa chạy SAST, quét phụ thuộc, quét secret |

## Nhật ký thay đổi

- v1: bản đầu, `status: draft`.
- v2: Developer chọn "vẫn push" với 2 cảnh báo LOG-02 (đã gửi `xdlc sensor report`) và bảo tạo changeset, không trả lời khối cảnh báo lệch chuẩn. Nộp nguyên trạng, `status: awaiting_review`; thêm mục *Sai khác so với chuẩn* với tình trạng `chưa phản hồi`. Điền commit `cb4ba38`.
