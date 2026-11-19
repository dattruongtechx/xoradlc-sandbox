"""Tài khoản và số dư (màn hình chính)."""
from dataclasses import dataclass

from .errors import ACCOUNT_NOT_FOUND, BALANCE_LOAD_FAILED, BankError

BALANCE_MASK = "******"  # REQ-004: giá trị thay cho số dư khi ở trạng thái ẩn


@dataclass
class Account:
    number: str
    owner_id: str
    kind: str  # "payment" | "saving"
    balance: int  # VND


class AccountRepo:
    def __init__(self):
        self._items: dict[str, Account] = {}

    def add(self, acc: Account) -> None:
        self._items[acc.number] = acc

    def get(self, number: str) -> Account:
        if number not in self._items:
            raise BankError(ACCOUNT_NOT_FOUND)
        return self._items[number]

    def list_by_owner(self, owner_id: str) -> list[Account]:
        return [a for a in self._items.values() if a.owner_id == owner_id]


def home_balances(repo: AccountRepo, owner_id: str, hidden: bool = True) -> list[dict]:
    """Dữ liệu thẻ số dư trên màn hình chính.

    hidden=True (mặc định, REQ-001): mọi số dư thành BALANCE_MASK; giá trị thật không
    nằm trong kết quả trả ra (NFR-001). hidden=False: trả số dư thật.
    Lỗi tải khi đang hiện (REQ-007 / EX-01): ném BankError(BALANCE_LOAD_FAILED), không trả mask.
    Cờ hidden do client giữ và truyền vào; backend không lưu (WO-MB-001 mục 5: lưu cục bộ trên thiết bị).
    """
    try:
        accounts = repo.list_by_owner(owner_id)
    except Exception as exc:  # lỗi hạ tầng (timeout, I/O) -> mã lỗi chuẩn, giữ nguyên nguyên nhân
        raise BankError(BALANCE_LOAD_FAILED, "Không tải được số dư") from exc
    return [
        {"number": a.number, "kind": a.kind, "balance": BALANCE_MASK if hidden else a.balance, "hidden": hidden}
        for a in accounts
    ]
