import unittest
from datetime import datetime

from mbank.accounts import Account, AccountRepo
from mbank.errors import BankError
from mbank.transactions import TransactionLog
from mbank.transfers import BANK_DAILY_LIMIT, TransferService


def make(balance=10**10):
    repo = AccountRepo()
    repo.add(Account("0000111122", "u1", "payment", balance))
    repo.add(Account("0000333344", "u2", "payment", 0))
    return TransferService(repo, TransactionLog(), now=lambda: datetime(2026, 1, 1, 9)), repo


class TransferTest(unittest.TestCase):
    def test_rejects_over_daily_limit(self):
        svc, _ = make()
        svc.transfer("k1", "0000111122", "0000333344", BANK_DAILY_LIMIT)
        with self.assertRaises(BankError) as e:
            svc.transfer("k2", "0000111122", "0000333344", 1)
        self.assertEqual(e.exception.code, "TRANSFER_LIMIT_EXCEEDED")

    def test_rejects_insufficient_funds(self):
        svc, _ = make(balance=100)
        with self.assertRaises(BankError):
            svc.transfer("k1", "0000111122", "0000333344", 101)

    def test_rejects_replayed_key(self):
        svc, _ = make()
        svc.transfer("k1", "0000111122", "0000333344", 1)
        with self.assertRaises(BankError):
            svc.transfer("k1", "0000111122", "0000333344", 1)

    def test_moves_money(self):
        svc, repo = make(balance=1000)
        svc.transfer("k1", "0000111122", "0000333344", 400)
        self.assertEqual((repo.get("0000111122").balance, repo.get("0000333344").balance), (600, 400))


if __name__ == "__main__":
    unittest.main()
