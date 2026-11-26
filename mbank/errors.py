"""Mã lỗi chuẩn của dự án: <MIỀN>_<LÝ_DO>."""


class BankError(Exception):
    def __init__(self, code: str, message: str = ""):
        super().__init__(message or code)
        self.code = code


ACCOUNT_NOT_FOUND = "ACCOUNT_NOT_FOUND"
INSUFFICIENT_FUNDS = "TRANSFER_INSUFFICIENT_FUNDS"
LIMIT_EXCEEDED = "TRANSFER_LIMIT_EXCEEDED"
INVALID_AMOUNT = "TRANSFER_INVALID_AMOUNT"
DUPLICATE_REQUEST = "TRANSFER_DUPLICATE_REQUEST"
CARD_NOT_FOUND = "CARD_NOT_FOUND"
BALANCE_LOAD_FAILED = "ACCOUNT_BALANCE_LOAD_FAILED"

# WO-2026-043 — khoá / mở khoá thẻ tạm thời. Giá trị theo bảng mã lỗi thiết kế OUT-043-02 mục 4.5
# (hợp đồng API). VALIDATION_ERROR, IDEMPOTENCY_KEY_REUSED, RATE_LIMITED, STEP_UP_* không theo dạng
# <MIỀN>_<LÝ_DO>: giữ đúng thiết kế, đã nêu trong changeset.
CARD_LOCKED = "CARD_LOCKED"  # [GIẢ ĐỊNH] mã lý do từ chối giao dịch khi thẻ khoá (REQ-004), thiết kế chưa đặt tên
CARD_STATUS_NOT_ALLOWED = "CARD_STATUS_NOT_ALLOWED"  # 409
CARD_SERVICE_UNAVAILABLE = "CARD_SERVICE_UNAVAILABLE"  # 503
VALIDATION_ERROR = "VALIDATION_ERROR"  # 400
IDEMPOTENCY_KEY_REUSED = "IDEMPOTENCY_KEY_REUSED"  # 409
RATE_LIMITED = "RATE_LIMITED"  # 429
STEP_UP_REQUIRED = "STEP_UP_REQUIRED"  # 401
STEP_UP_INVALID = "STEP_UP_INVALID"  # 401

# WO-2026-041 — xem danh sách thẻ. Giá trị theo bảng lỗi OUT-041-02 mục 4 / API-cards-list.md mục 5;
# không theo dạng <MIỀN>_<LÝ_DO>, giữ đúng thiết kế như WO-2026-043.
UNAUTHENTICATED = "UNAUTHENTICATED"  # 401
FORBIDDEN = "FORBIDDEN"  # 403, thiếu scope cards:read
