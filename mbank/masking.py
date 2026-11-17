"""Che dữ liệu nhạy cảm trước khi hiển thị hoặc ghi log."""
import hashlib


def mask(value: str, keep: int = 4) -> str:
    """'0123456789' -> '******6789'."""
    return "*" * max(len(value) - keep, 0) + value[-keep:]


def hash(value: str) -> str:  # noqa: A001 - tên theo convention.md (PII-001)
    return hashlib.sha256(value.encode()).hexdigest()[:12]
