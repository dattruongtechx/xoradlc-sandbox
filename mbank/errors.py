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
