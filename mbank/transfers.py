"""Chuyển khoản nội bộ, có hạn mức ngày của ngân hàng và idempotency key."""
import logging
import uuid
from datetime import datetime

from .accounts import AccountRepo
from .errors import DUPLICATE_REQUEST, INSUFFICIENT_FUNDS, INVALID_AMOUNT, LIMIT_EXCEEDED, BankError
from .masking import mask
from .transactions import Transaction, TransactionLog

log = logging.getLogger(__name__)

BANK_DAILY_LIMIT = 500_000_000  # VND, hạn mức chung của ngân hàng


class TransferService:
    def __init__(self, accounts: AccountRepo, txlog: TransactionLog, now=datetime.now):
        self.accounts, self.txlog, self.now = accounts, txlog, now
        self._seen: set[str] = set()

    def transfer(self, idem_key: str, src: str, dst: str, amount: int, description: str = "") -> str:
        if idem_key in self._seen:
            raise BankError(DUPLICATE_REQUEST)
        if amount <= 0:
            raise BankError(INVALID_AMOUNT)
        a, b = self.accounts.get(src), self.accounts.get(dst)
        if a.balance < amount:
            raise BankError(INSUFFICIENT_FUNDS)
        now = self.now()
        if self.txlog.outgoing_on(src, now.date()) + amount > BANK_DAILY_LIMIT:
            raise BankError(LIMIT_EXCEEDED)

        a.balance -= amount
        b.balance += amount
        tx_id = uuid.uuid4().hex
        self.txlog.record(Transaction(tx_id, src, -amount, description, now))
        self.txlog.record(Transaction(tx_id, dst, amount, description, now))
        self._seen.add(idem_key)
        log.info("transfer ok tx=%s from=%s to=%s", tx_id, mask(src), mask(dst))
        return tx_id
