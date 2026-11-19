import unittest

from mbank.accounts import BALANCE_MASK, Account, AccountRepo, home_balances
from mbank.errors import BALANCE_LOAD_FAILED, BankError


def make_repo():
    repo = AccountRepo()
    repo.add(Account("0000111122", "u1", "payment", 123456))
    repo.add(Account("0000555566", "u1", "saving", 999000))
    repo.add(Account("0000333344", "u2", "payment", 1))
    return repo


class FailingRepo(AccountRepo):
    def list_by_owner(self, owner_id):
        raise TimeoutError("backend timeout")


class HomeBalancesTest(unittest.TestCase):
    # --- nhánh sai ---
    def test_load_failure_when_shown_raises_standard_error(self):  # REQ-007 / EX-01
        with self.assertRaises(BankError) as e:
            home_balances(FailingRepo(), "u1", hidden=False)
        self.assertEqual(e.exception.code, BALANCE_LOAD_FAILED)

    def test_load_failure_when_shown_never_returns_mask(self):  # EX-01: không hiện ****** khi lỗi
        try:
            result = home_balances(FailingRepo(), "u1", hidden=False)
        except BankError:
            return
        self.fail(f"phải ném lỗi, nhưng trả về {result}")

    def test_hidden_state_never_exposes_balance_value(self):  # NFR-001
        for row in home_balances(make_repo(), "u1", hidden=True):
            self.assertEqual(row["balance"], BALANCE_MASK)
            for digits in ("123456", "999000"):
                self.assertNotIn(digits, str(row))

    def test_only_owner_accounts_returned(self):
        numbers = {r["number"] for r in home_balances(make_repo(), "u1", hidden=False)}
        self.assertEqual(numbers, {"0000111122", "0000555566"})

    # --- nhánh thuận ---
    def test_default_is_hidden(self):  # REQ-001 (BRD v2.0)
        rows = home_balances(make_repo(), "u1")
        self.assertTrue(rows)
        self.assertTrue(all(r["balance"] == BALANCE_MASK and r["hidden"] for r in rows))

    def test_shown_returns_real_balances(self):  # REQ-002
        rows = {r["number"]: r["balance"] for r in home_balances(make_repo(), "u1", hidden=False)}
        self.assertEqual(rows, {"0000111122": 123456, "0000555566": 999000})

    def test_one_switch_masks_all_balances(self):  # REQ-004, REQ-005
        rows = home_balances(make_repo(), "u1", hidden=True)
        self.assertEqual({r["balance"] for r in rows}, {BALANCE_MASK})
        self.assertEqual(BALANCE_MASK, "******")


if __name__ == "__main__":
    unittest.main()
