---
id: WO-2026-041/changeset-001
version: 1
status: draft
produced_by: xora-dlc
inputs:
  - path: BRD-Xem-danh-sach-the-WO-2026-041 (OUT-041-01)
    version: v1 / nội dung v0.1 (ghi "AI soạn nháp, BA chưa rà"; BA xác nhận finalize qua OQ-001 ngày 25/11/2026)
  - path: Thiet-ke-Xem-danh-sach-the-WO-2026-041 (OUT-041-02)
    version: v1 / nội dung v0.1 (nháp, Tech lead chưa rà; còn 🔴 G-091 SEC-D03, G-092 SEC-A02)
  - path: API-cards-list
    version: v0.1 (AI soạn nháp, cần người rà)
commits: []
approved_by: null
approved_at: null
---

# Changeset: Xem danh sách thẻ (WO-2026-041)

Thiết kế và contract đang là bản nháp chưa rà. Kết quả có thể phải làm lại khi hai tài liệu được chốt.

## 1. Thông tin

| Mục | Giá trị |
|---|---|
| Work order | WO-2026-041 – Xem danh sách thẻ |
| Bước | Thực hiện |
| Nhánh | `feature/WO-2026-041-xem-danh-sach-the`, tạo từ `origin/main` `c632205` |
| Commit | Chưa commit |
| PR | Chưa tạo |
| Map WO (`xdlc link`) | Đã map nhánh → WO-2026-041 · Thực hiện |
| Hướng làm | Hướng B: code ngay theo thiết kế nháp, điểm chưa chốt ghi `[GIẢ ĐỊNH]` (Developer chọn) |
| **Liên quan bảo mật** | **Có**: xử lý PAN (chỉ để tạo số che), số thẻ đã che, hạn mức, tài khoản liên kết; kiểm scope `cards:read` |
| Phần do AI sinh | Toàn bộ code, test và hồ sơ này (xem mục 4) |

## 2. Truy vết REQ ↔ trạng thái

| REQ | Ưu tiên | Trạng thái | Code (`mbank/card_list.py`) | Test (`tests/test_card_list.py`) |
|---|---|---|---|---|
| REQ-001 Danh sách thẻ khách đứng tên chính | Must | Làm. Bỏ thẻ `is_primary_holder=False` `[GIẢ ĐỊNH]` Q-01 | `list_cards`, `_card` | `ListTest.test_only_primary_holder`, `test_card_fields` |
| REQ-002 Các trường của thẻ | Must | Làm phần backend (trường theo API-cards-list.md mục 4). Logo do app vẽ theo `network` | `_card` | `ListTest.test_card_fields` |
| REQ-003 Che số thẻ 6 + 4 | Must | Làm | `masking.mask_card_number` | `ListTest.test_card_fields`, `BadCardDataTest.test_mask_rejects_non_card_numbers`, `SecurityTest.*` |
| REQ-004 Hạn mức còn lại cho thẻ tín dụng | Must | Làm. Thẻ ghi nợ `credit: null` (ASM-12) | `_credit` | `ListTest.test_card_fields`, `test_debit_has_no_limit_and_masked_linked_account` |
| REQ-005 Nhóm và sắp xếp | Should | Làm | `list_cards` | `ListTest.test_grouping_and_sorting` |
| REQ-006 Trạng thái nhãn màu + chữ | Must | Làm phần backend (`status`, `statusLabel` vi/en). Màu thuộc app | `STATUS_LABELS` | `ListTest.test_closed_cards_excluded_other_statuses_shown`, `test_english_labels` |
| REQ-007 Sắp hết hạn ≤ 60 ngày / Hết hạn | Should | Làm (ASM-13) | `_card`, `_expiry_last_day` | `ListTest.test_expiring_soon_and_expired` |
| REQ-008 Tên gợi nhớ, mặc định tên sản phẩm | Should | Làm | `_card`, `_fetch` | `ListTest.test_card_fields`, `AliasDegradeTest.*` |
| REQ-009 Kéo để làm mới | Should | **Không làm ở đây**: thuộc app (EX-06, EX-07) | - | - |
| REQ-010 Chạm thẻ mở chi tiết theo `cardId` | Must | Làm phần backend: `cardId` ngẫu nhiên, ổn định, không lộ mã CMS. Màn chi tiết thuộc WO-MB-042 | `InMemoryCardIdRegistry` | `SecurityTest.test_card_id_random_and_stable`, `test_response_has_no_forbidden_data` |
| REQ-011 Trạng thái trống | Must | Làm: `total=0`, `groups=[]` | `list_cards` | `ListTest.test_empty_list` |

Luật, ngoại lệ, thiết kế đã áp dụng:

| Mã | Nội dung | Code | Test |
|---|---|---|---|
| BR-01 | Loại thẻ huỷ / đóng; hiện 5 trạng thái | `DISPLAYED_STATUSES` | `ListTest.test_closed_cards_excluded_other_statuses_shown` |
| BR-02 | Mã khách chỉ lấy từ token (`ctx`) | `list_cards` | `AccessErrorTest.test_customer_id_only_from_token` |
| EX-02 | CMS lỗi / quá 5 giây → 503 `CARD_SERVICE_UNAVAILABLE` | `_fetch` | `CmsErrorTest.*` |
| EX-03 | Token thiếu → `UNAUTHENTICATED` | `list_cards` | `AccessErrorTest.test_missing_customer_is_unauthenticated` |
| EX-04 | Không có thẻ → không lỗi | `list_cards` | `ListTest.test_empty_list` |
| EX-10 | Thiếu scope `cards:read` → `FORBIDDEN` | `list_cards` | `AccessErrorTest.test_missing_scope_is_forbidden` |
| ADR-01 | Gọi trực tiếp CMS + CSDL Backend | `CmsCardClient`, `CardAliasStore` | - |
| ADR-02 (chưa chốt) | Gọi song song | `_fetch` | `AliasDegradeTest.test_cms_and_alias_called_in_parallel` |
| ADR-03 (chưa chốt) | Alias lỗi → dùng `productName` | `_fetch` | `AliasDegradeTest.*` |
| ADR-05 (chưa chốt) | Timeout CSDL Backend 2s, CMS 5s | hằng cấu hình | `CmsErrorTest.test_cms_timeouts_passed_to_clients` |
| ADR-06 | Không cache ở Mobile Backend | `list_cards` | - |
| Rate limit (đề xuất) | 30 lần / phút / khách → `RATE_LIMITED` | `_check_rate` | `AccessErrorTest.test_rate_limited` |

EX-01, EX-05 đến EX-09 thuộc app (dữ liệu trong phiên, mất mạng, kéo làm mới, rời màn, mở chi tiết lỗi). NFR-005 phía backend chỉ là trả 503 để app hiện dữ liệu phiên.

## 3. Phạm vi thay đổi

| File | Thay đổi |
|---|---|
| `mbank/card_list.py` | File mới: `CardListService.list_cards`, Protocol `CmsCardClient` / `CardAliasStore` / `CardIdRegistry`, `CmsCard`, `InMemoryCardIdRegistry`, cấu hình qua biến môi trường |
| `mbank/masking.py` | Thêm `mask_card_number` (6 + 4) |
| `mbank/errors.py` | Thêm `UNAUTHENTICATED`, `FORBIDDEN` |
| `mbank/cards.py` | `RequestContext` thêm trường `scopes` (mặc định rỗng) |
| `tests/test_card_list.py` | File mới, 26 test |
| `tests/fixtures/card_numbers.py`, `tests/fixtures/__init__.py` | Đã có sẵn trên máy, chưa track; test mới dùng số thẻ thử công khai trong đó. **Cần commit cùng**, Developer xác nhận nguồn gốc file |
| `changesets/CS-041-001-xem-danh-sach-the.md` | File này |

**Lệch plan đã duyệt:** plan ghi code ở `mbank/cards.py`; thực tế tách sang `mbank/card_list.py` vì `cards.py` đã 330 dòng, thêm ~300 dòng sẽ vượt SIZE-001 (500 dòng). Convention mục 1 ghi cấu trúc `mbank/<miền>.py`; file mới vẫn thuộc miền thẻ nhưng tên khác mẫu. Developer quyết giữ hay gộp.

Không có migration CSDL. Không thêm thư viện ngoài.

## 4. Phần do AI sinh

| File / vùng | Nguồn gốc | Developer đã đọc kỹ? | Ghi chú |
|---|---|---|---|
| `mbank/card_list.py` toàn bộ | AI sinh | Chưa xác nhận | Chứa các `[GIẢ ĐỊNH]` ở mục 13 |
| `mbank/card_list.py` `_fetch` | AI sinh | Chưa xác nhận | `except Exception` cho alias (ADR-03); thread CMS / alias quá hạn vẫn chạy nền tới khi client tự timeout |
| `mbank/masking.py` `mask_card_number` | AI sinh | Chưa xác nhận | |
| `mbank/errors.py` (4 dòng) | AI sinh | Chưa xác nhận | |
| `mbank/cards.py` `RequestContext.scopes` (1 dòng) | AI sinh | Chưa xác nhận | |
| `tests/test_card_list.py` | AI sinh | Chưa xác nhận | Dữ liệu bịa; PAN thử công khai Visa / Mastercard |
| File hồ sơ này | AI sinh | Chưa xác nhận | |

## 5. Thay đổi cấu hình

| Biến môi trường | Mặc định | DEV / UAT / PROD | Căn cứ |
|---|---|---|---|
| `MBANK_CMS_LIST_TIMEOUT_SECONDS` | `5` | Chưa có | EX-02 |
| `MBANK_ALIAS_TIMEOUT_SECONDS` | `2` | Chưa có | ADR-05 (đề xuất) |
| `MBANK_CARD_LIST_RATE_LIMIT_PER_MINUTE` | `30` | Chưa có | Bảng lỗi 429 (đề xuất) |

Không có secret.

## 6. Migration và rollback

Không có migration. Rollback: revert commit. `cardId` trong bộ nhớ mất khi khởi động lại (xem mục 12).

## 7. Kết quả kiểm thử

| Việc kiểm | Lệnh | Kết quả |
|---|---|---|
| Unit test toàn bộ | `python3 -m unittest discover -s tests -t .` | Ran 72 tests, OK (46 cũ, 26 mới), Python 3.9.6. Lần chạy đầu 1 test fail do fixture test đặt `productName` chứa mã CMS; đã sửa test, không sửa code |
| Soát nhanh LOG-003, ERR-002, TODO-001 | `grep` trên `mbank/card_list.py` | Không có `print`, `except: pass`; 2 `TODO` có mã `WO-2026-041` |
| Sensor convention (`xdlc sensor`) | `xdlc sensor` + `xdlc sensor report` | Đã chạy, gửi 4 cảnh báo 🔴, Developer chọn vẫn commit: PII-02 ở `tests/test_card_list.py:35` (`LINKED_ACCOUNT`, số bịa) và `mbank/masking.py:11` (docstring có PAN thử Visa), nằm ngoài `fixtures/`; LOG-02 ở `mbank/cards.py:189,242` nhiều khả năng báo nhầm (chuỗi `request=%s`, code WO-043 cũ) |
| Python 3.10+ | - | Chưa chạy: máy chỉ có Python 3.9.6 |
| Lint, độ phủ, build | - | Chưa chạy: repo không có công cụ; Python thuần không có bước build |

Bảng test chi tiết:

| Test | Loại | REQ / mã | Kiểm gì |
|---|---|---|---|
| `AccessErrorTest.test_missing_customer_is_unauthenticated` | Sai | EX-03 | Không có khách → `UNAUTHENTICATED`, không gọi CMS |
| `AccessErrorTest.test_missing_scope_is_forbidden` | Sai | EX-10 | Thiếu `cards:read` → `FORBIDDEN`, không gọi CMS |
| `AccessErrorTest.test_invalid_params` | Sai | 400 | `type` lạ, `includeInactive` không phải bool → `VALIDATION_ERROR` |
| `AccessErrorTest.test_rate_limited` | Sai | 429 | Quá ngưỡng → `RATE_LIMITED` |
| `AccessErrorTest.test_customer_id_only_from_token` | Sai | BR-02 | CMS nhận mã khách từ `ctx` |
| `CmsErrorTest.test_cms_error_returns_503` | Sai | EX-02 | CMS lỗi → 503, đúng thông điệp BRD |
| `CmsErrorTest.test_cms_timeout_returns_503` | Sai | EX-02 | CMS quá hạn → 503 |
| `CmsErrorTest.test_cms_timeouts_passed_to_clients` | Sai | ADR-05 | Timeout CMS mặc định 5s |
| `AliasDegradeTest.test_alias_error_falls_back_to_product_name` | Sai | ADR-03, REQ-008 | Alias lỗi → `alias=null`, `displayName=productName` |
| `AliasDegradeTest.test_alias_timeout_does_not_block` | Sai | ADR-03, ADR-05 | Alias chậm không giữ response |
| `AliasDegradeTest.test_cms_and_alias_called_in_parallel` | Sai | ADR-02 | Hai lời gọi chạy song song |
| `BadCardDataTest.test_missing_expiry_and_limits_are_null` | Sai | Thiết kế mục 4 | Thiếu dữ liệu → `null` trường đó |
| `BadCardDataTest.test_invalid_pan_skips_only_that_card` | Sai | `[GIẢ ĐỊNH]` | PAN lỗi → bỏ thẻ đó, các thẻ khác vẫn trả |
| `BadCardDataTest.test_mask_rejects_non_card_numbers` | Sai | REQ-003 | Giá trị không phải số thẻ → `ValueError` |
| `SecurityTest.test_response_has_no_forbidden_data` | Bảo mật | Thiết kế mục 5 | Response không có PAN, số tài khoản đầy đủ, mã khách, mã CMS |
| `SecurityTest.test_card_id_random_and_stable` | Bảo mật | REQ-010 | `cardId` ổn định, không chứa số thẻ |
| `SecurityTest.test_logs_have_no_card_data` | Bảo mật | NFR-006 | Log không có PAN, số che, 4 số cuối, mã khách, alias |
| `ListTest.test_card_fields` | Thuận | REQ-002/003/004/006/008 | Đủ và đúng trường của thẻ tín dụng |
| `ListTest.test_debit_has_no_limit_and_masked_linked_account` | Thuận | REQ-004, ASM-12 | Thẻ ghi nợ: `credit=null`, tài khoản liên kết đã che |
| `ListTest.test_empty_list` | Thuận | REQ-011, EX-04 | `total=0`, `groups=[]` |
| `ListTest.test_only_primary_holder` | Thuận | REQ-001 | Chỉ thẻ đứng tên chính |
| `ListTest.test_closed_cards_excluded_other_statuses_shown` | Thuận | BR-01, REQ-006 | 5 trạng thái hiện, CLOSED / CANCELLED bị loại |
| `ListTest.test_grouping_and_sorting` | Thuận | REQ-005 | Tín dụng trước; ACTIVE trước, rồi `issuedAt` giảm dần |
| `ListTest.test_filters` | Thuận | Tham số API | `type`, `includeInactive=false` |
| `ListTest.test_expiring_soon_and_expired` | Thuận | REQ-007, ASM-13 | 36 ngày → sắp hết hạn; 67 ngày → không; quá hạn → `EXPIRED`, không cờ sắp hết hạn |
| `ListTest.test_english_labels` | Thuận | Accept-Language | Nhãn tiếng Anh |

## 8. Quét bảo mật

Chưa chạy SAST, quét phụ thuộc, quét secret: repo không có công cụ. Không thêm phụ thuộc.

Thiết kế còn 2 finding 🔴 chưa xử lý:
- **G-091 SEC-D03**: chưa nêu căn cứ thu thập / mục đích cho dữ liệu mức Hạn chế. Việc của thiết kế; code không đổi được.
- **G-092 SEC-A02**: mức phân loại `maskedNumber` (Nội bộ hay Hạn chế, Q-05). Code chọn hướng thận trọng: không lưu, không log, không cache số che; nên đúng với cả hai mức. Nếu sau này cần lưu thì phải bổ sung mã hoá.

## 9. Tương thích ngược

- `RequestContext` thêm `scopes` có mặc định; chỗ tạo cũ (WO-2026-043) không đổi, 46 test cũ vẫn OK.
- `mbank.card_list` định nghĩa lại hằng trạng thái dạng viết hoa (`ACTIVE = "ACTIVE"`), khác hằng viết thường trong `mbank.cards`. Hai module không dùng chung hằng; cần lưu ý khi import.
- API mới; chưa có HTTP layer.

## 10. Audit log và giám sát

- Xem danh sách thẻ không ghi audit `[GIẢ ĐỊNH]`: thiết kế không yêu cầu; Q-09 (thời gian lưu nhật ký truy cập) chưa có số.
- Log `mbank.card_list` chỉ có `total`, `request_id`, tên lỗi, mã CMS đã băm. Có test kiểm.
- Chưa có metric (tỉ lệ 503, thời gian p95 cho NFR-004).

## 11. Feature flag

Không áp dụng.

## 12. Nợ kỹ thuật cố ý

| Vị trí | Nội dung | Hướng nâng cấp |
|---|---|---|
| `InMemoryCardIdRegistry` — `TODO WO-2026-041` | `cardId` trong bộ nhớ một tiến trình; khởi động lại hoặc nhiều instance → `cardId` khác, alias theo `cardId` cũ không khớp | Lưu bảng ánh xạ ở CSDL Backend |
| `CardListService.__init__` — `TODO WO-2026-041` | Rate limit trong bộ nhớ một tiến trình | Kho dùng chung / API gateway |
| `_fetch` | Hết hạn chờ không huỷ được thread đang gọi; dựa vào client tự tôn trọng `timeout` | Client thật phải đặt timeout socket |

## 13. Giới hạn đã biết và giả định

- `[GIẢ ĐỊNH]` **Contract CMS (Q-06)**: `CmsCard` do AI đặt; API thật của CMS chưa có.
- `[GIẢ ĐỊNH]` **CSDL Backend** trả `{cardId: alias}` theo mã khách; thiết kế không nêu chi tiết.
- `[GIẢ ĐỊNH]` **Q-01**: không hiện thẻ phụ / đồng sở hữu.
- **BR-01 mâu thuẫn trong nguồn, cần BA / Tech lead xác nhận (Q-02)**: BRD BR-01 ngầm cho thẻ huỷ / đóng **≤ 90 ngày** vẫn hiện, nhưng enum trạng thái API-cards-list.md mục 4.3 không có `CLOSED` / `CANCELLED`, nên không trả được. Code loại **mọi** thẻ huỷ / đóng.
- `[GIẢ ĐỊNH]` `includeInactive=false` chỉ trả thẻ `ACTIVE`; tài liệu không định nghĩa "inactive".
- `[GIẢ ĐỊNH]` Thẻ quá ngày cuối tháng hết hạn → `EXPIRED` dù CMS trả trạng thái khác.
- `[GIẢ ĐỊNH]` PAN lỗi định dạng → bỏ thẻ đó (vì `maskedNumber` không nullable).
- `[GIẢ ĐỊNH]` Nhãn nhóm "Thẻ tín dụng" / "Thẻ ghi nợ" (en "Credit cards" / "Debit cards"); `currency` mặc định `VND` khi CMS không trả.
- ADR-02, ADR-03, ADR-05 chưa thành DEC; rate limit 30/phút là đề xuất.
- Q-03 (thời hạn giữ dữ liệu phiên) thuộc app; backend không cache.
- Chưa làm: `426 APP_UPDATE_REQUIRED`, `500 INTERNAL_ERROR` (thuộc HTTP layer / gateway); header `Accept-Language` chỉ nhận qua tham số `lang`.
- `UNAUTHENTICATED`, `FORBIDDEN` không theo dạng `<MIỀN>_<LÝ_DO>`; giữ đúng contract API.
- `BankError` chưa mang mã yêu cầu (cùng vấn đề G-076).
- NFR-004 (p95 ≤ 800ms) chưa đo.
- Không tra được template changeset chuẩn và convention KB từ Xora DLC (trả về rỗng); hồ sơ theo cấu trúc CS-043 và sửa các điểm bị cảnh báo G-077..G-081, G-089.

## Sai khác so với chuẩn

| Mục chuẩn | Mức | Tình trạng | Lý do |
|---|---|---|---|
| 4. Phần do AI sinh (đã đọc kỹ) | 🔴 | chưa phản hồi | Developer chưa xác nhận |
| 5. Cấu hình theo môi trường | 🔴 | chưa phản hồi | Chưa có giá trị UAT / PROD |
| 7. Sensor, lint, độ phủ, Python 3.10+ | 🔴 | chưa phản hồi | Sensor chạy khi commit; repo không có công cụ; máy có Python 3.9.6 |
| 8. Quét bảo mật | 🔴 | chưa phản hồi | Chưa chạy SAST / quét phụ thuộc / quét secret |
| Nguồn thiết kế | 🔴 | chưa phản hồi | Thiết kế nháp, còn G-091, G-092 |

## Nhật ký thay đổi

- v1: bản đầu, `status: draft`.
