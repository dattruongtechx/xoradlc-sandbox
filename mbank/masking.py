"""Che dữ liệu nhạy cảm trước khi hiển thị hoặc ghi log."""
import hashlib


def mask(value: str, keep: int = 4) -> str:
    """'0123456789' -> '******6789'."""
    return "*" * max(len(value) - keep, 0) + value[-keep:]


def mask_card_number(pan: str) -> str:
    """WO-2026-041 REQ-003: giữ 6 số đầu + 4 số cuối, '4111111111111111' -> '411111******1111'.

    PAN chỉ đi qua hàm này, không lưu, không log. Ném ValueError khi không phải số thẻ hợp lệ (12-19 chữ số).
    """
    if not pan.isdigit() or not 12 <= len(pan) <= 19:
        raise ValueError("invalid card number")
    return pan[:6] + "*" * (len(pan) - 10) + pan[-4:]


def hash(value: str) -> str:  # noqa: A001 - tên theo convention.md (PII-001)
    return hashlib.sha256(value.encode()).hexdigest()[:12]
