"""Lịch sử giao dịch."""
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Transaction:
    id: str
    account: str
    amount: int  # âm = tiền ra
    description: str
    at: datetime = field(default_factory=datetime.now)


class TransactionLog:
    def __init__(self):
        self._items: list[Transaction] = []

    def record(self, tx: Transaction) -> None:
        self._items.append(tx)

    def history(self, account: str) -> list[Transaction]:
        return sorted((t for t in self._items if t.account == account), key=lambda t: t.at, reverse=True)

    def outgoing_on(self, account: str, day) -> int:
        """Tổng tiền chuyển đi của tài khoản trong một ngày (số dương)."""
        return -sum(t.amount for t in self._items if t.account == account and t.amount < 0 and t.at.date() == day)
