"""Tài khoản và số dư (màn hình chính)."""
from dataclasses import dataclass

from .errors import ACCOUNT_NOT_FOUND, BankError


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


def home_balances(repo: AccountRepo, owner_id: str) -> list[dict]:
    """Dữ liệu thẻ số dư trên màn hình chính."""
    return [{"number": a.number, "kind": a.kind, "balance": a.balance} for a in repo.list_by_owner(owner_id)]
