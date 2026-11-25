"""WO-2026-043 khoá / mở khoá thẻ tạm thời. Dữ liệu test là dữ liệu bịa."""
import threading
import time
import unittest
from datetime import datetime, timedelta

from mbank.cards import (
    ACTIVE,
    BLOCKED,
    CLOSED,
    EXPIRED,
    LOCK_ACTION,
    TEMP_LOCKED,
    UNLOCK_ACTION,
    Card,
    CardLockService,
    CardService,
    CmsError,
    CmsStatusConflict,
    RequestContext,
)
from mbank.errors import BankError

CARD = "card-0001"
OTHER_CARD = "card-0002"
OWNER = "cust-001"
LAST4 = "9876"


class FakeCms:
    """CMS giả: ACTIVE <-> TEMP_LOCKED, trạng thái khác -> 409; nhớ Idempotency-Key (ADR-03 lớp 2)."""

    def __init__(self, statuses, delay=0.0):
        self.statuses = dict(statuses)
        self.delay = delay
        self.fail_change = 0  # số lần change_status sắp tới ném CmsError
        self.fail_status = False
        self.apply_before_fail = False  # CMS đã đổi trạng thái nhưng trả quá hạn
        self.change_calls = []
        self._seen = {}
        self._lock = threading.Lock()

    def change_status(self, card_id, action, idem_key, timeout):
        self.change_calls.append((card_id, action, idem_key, timeout))
        if self.delay:
            time.sleep(self.delay)
        with self._lock:
            if self.fail_change:
                self.fail_change -= 1
                if self.apply_before_fail:
                    self.statuses[card_id] = TEMP_LOCKED if action == LOCK_ACTION else ACTIVE
                raise CmsError("timeout")
            if (card_id, idem_key) in self._seen:
                return self._seen[(card_id, idem_key)]
            current = self.statuses[card_id]
            if current not in (ACTIVE, TEMP_LOCKED):
                raise CmsStatusConflict(current)
            target = TEMP_LOCKED if action == LOCK_ACTION else ACTIVE
            self.statuses[card_id] = target
            self._seen[(card_id, idem_key)] = (current, target)
            return current, target

    def get_status(self, card_id, timeout):
        if self.fail_status:
            raise CmsError("timeout")
        return self.statuses[card_id]


class FakeStepUp:
    def __init__(self):
        self.tokens = {}  # token -> (customer_id, card_id, purpose)

    def issue(self, token, customer_id=OWNER, card_id=CARD, purpose="CARD_UNLOCK"):
        self.tokens[token] = (customer_id, card_id, purpose)
        return token

    def consume(self, token, customer_id, card_id, purpose):
        bound = self.tokens.pop(token, None)  # dùng một lần
        return bound == (customer_id, card_id, purpose)


class FakeNotifier:
    def __init__(self, fail=False):
        self.sent, self.fail = [], fail

    def push(self, customer_id, text):
        self._send("push", customer_id, text)

    def sms(self, customer_id, text):
        self._send("sms", customer_id, text)

    def _send(self, channel, customer_id, text):
        if self.fail:
            raise ConnectionError("notification hub down")
        self.sent.append((channel, customer_id, text))


class FakeAudit:
    def __init__(self):
        self.entries = []

    def record(self, entry):
        self.entries.append(entry)


class Clock:
    def __init__(self):
        self.t = datetime(2026, 1, 1, 9, 0)

    def __call__(self):
        return self.t


def make(status=ACTIVE, cms_status=None, **kw):
    cards = CardService()
    cards.add(Card(CARD, OWNER, "debit", status, LAST4))
    cards.add(Card(OTHER_CARD, "cust-002", "credit", ACTIVE, "1111"))
    cms = FakeCms({CARD: cms_status or status, OTHER_CARD: ACTIVE}, delay=kw.pop("delay", 0.0))
    env = dict(cards=cards, cms=cms, step_up=FakeStepUp(), notifier=FakeNotifier(kw.pop("notify_fail", False)),
               audit=FakeAudit(), clock=Clock())
    env["svc"] = CardLockService(cards, cms, env["step_up"], env["notifier"], env["audit"], now=env["clock"], **kw)
    return env


def ctx(customer=OWNER):
    return RequestContext(customer, "req-1", "device-x", "10.0.0.1")


class AuthorizeTest(unittest.TestCase):
    def test_rejects_temp_locked_card_with_reason(self):  # REQ-004
        e = make(status=TEMP_LOCKED)
        with self.assertRaises(BankError) as err:
            e["cards"].authorize(CARD, 1000)
        self.assertEqual(err.exception.code, "CARD_LOCKED")

    def test_still_rejects_expired_and_closed(self):
        for status in (EXPIRED, CLOSED):
            e = make(status=status)
            self.assertFalse(e["cards"].authorize(CARD, 1000))

    def test_active_card_passes(self):
        self.assertTrue(make()["cards"].authorize(CARD, 1000))


class LockErrorTest(unittest.TestCase):
    def assertCode(self, code, fn, *args, **kw):
        with self.assertRaises(BankError) as err:
            fn(*args, **kw)
        self.assertEqual(err.exception.code, code)
        return err.exception

    def test_unknown_card(self):
        e = make()
        self.assertCode("CARD_NOT_FOUND", e["svc"].lock, ctx(), "card-9999", "k1")

    def test_card_of_other_customer_looks_not_found(self):
        e = make()
        self.assertCode("CARD_NOT_FOUND", e["svc"].lock, ctx(), OTHER_CARD, "k1")
        self.assertEqual(e["cms"].change_calls, [])

    def test_invalid_reason_or_missing_key(self):
        e = make()
        self.assertCode("VALIDATION_ERROR", e["svc"].lock, ctx(), CARD, "k1", "LOST_FOREVER")
        self.assertCode("VALIDATION_ERROR", e["svc"].lock, ctx(), CARD, "")

    def test_blocked_card_not_allowed(self):  # REQ-009
        e = make(status=BLOCKED)
        exc = self.assertCode("CARD_STATUS_NOT_ALLOWED", e["svc"].lock, ctx(), CARD, "k1")
        self.assertIn("ngân hàng khoá", str(exc))
        self.assertEqual(e["notifier"].sent, [])
        self.assertEqual(e["audit"].entries, [])

    def test_expired_card_not_allowed(self):  # REQ-009
        e = make(status=EXPIRED)
        self.assertCode("CARD_STATUS_NOT_ALLOWED", e["svc"].lock, ctx(), CARD, "k1")

    def test_cms_down_returns_503_and_card_stays_active(self):  # EX-01
        e = make()
        e["cms"].fail_change, e["cms"].fail_status = 2, True
        self.assertCode("CARD_SERVICE_UNAVAILABLE", e["svc"].lock, ctx(), CARD, "k1")
        self.assertEqual(len(e["cms"].change_calls), 2)  # gọi + thử lại đúng 1 lần
        self.assertEqual({c[2] for c in e["cms"].change_calls}, {"k1"})  # cùng Idempotency-Key
        self.assertEqual(e["cards"].get(CARD).status, ACTIVE)
        self.assertEqual(e["notifier"].sent, [])

    def test_same_key_different_payload_conflicts(self):
        e = make()
        e["svc"].lock(ctx(), CARD, "k1", "TEMPORARILY_UNUSED")
        self.assertCode("IDEMPOTENCY_KEY_REUSED", e["svc"].lock, ctx(), CARD, "k1", "CANNOT_FIND_CARD")

    def test_rate_limit_after_ten_per_hour(self):  # ADR-05
        e = make()
        for i in range(10):
            fn = e["svc"].lock if i % 2 == 0 else e["svc"].unlock
            args = () if i % 2 == 0 else (e["step_up"].issue(f"t{i}"),)
            fn(ctx(), CARD, f"k{i}", *args)
        self.assertCode("RATE_LIMITED", e["svc"].lock, ctx(), CARD, "k10")
        e["clock"].t += timedelta(hours=1)
        self.assertTrue(e["svc"].lock(ctx(), CARD, "k11")["changed"])

    def test_rate_limit_is_per_card_config(self):
        e = make(rate_limit_per_hour=1)
        e["svc"].lock(ctx(), CARD, "k1")
        self.assertCode("RATE_LIMITED", e["svc"].unlock, ctx(), CARD, "k2", e["step_up"].issue("t"))


class LockTest(unittest.TestCase):
    def test_lock_active_card(self):  # REQ-001
        e = make()
        r = e["svc"].lock(ctx(), CARD, "k1")
        self.assertEqual((r["previousStatus"], r["status"], r["changed"]), ("ACTIVE", "TEMP_LOCKED", True))
        self.assertEqual(r["statusLabel"], "Đang khoá tạm thời")
        self.assertEqual(r["actions"], ["UNLOCK", "EDIT_ALIAS"])
        self.assertFalse(r["nextSteps"]["showReportLost"])
        self.assertEqual(e["cards"].get(CARD).status, TEMP_LOCKED)
        self.assertEqual(e["cms"].change_calls[0][1:], (LOCK_ACTION, "k1", 5.0))  # ADR-02 timeout 5s

    def test_audit_has_who_when_what_without_raw_ids(self):
        e = make()
        e["svc"].lock(ctx(), CARD, "k1", "SUSPECTED_COMPROMISE")
        [entry] = e["audit"].entries
        self.assertEqual(entry["action"], "CARD_TEMP_LOCK")
        self.assertEqual((entry["deviceId"], entry["ip"], entry["reason"]), ("device-x", "10.0.0.1", "SUSPECTED_COMPROMISE"))
        self.assertEqual(entry["at"], "2026-01-01T09:00:00")
        self.assertNotIn(CARD, str(entry))
        self.assertNotIn(OWNER, str(entry))

    def test_replay_same_key_returns_same_result_once(self):  # REQ-008, ADR-03
        e = make()
        first = e["svc"].lock(ctx(), CARD, "k1")
        again = e["svc"].lock(ctx(), CARD, "k1")
        self.assertEqual(first, again)
        self.assertEqual(len(e["cms"].change_calls), 1)
        self.assertEqual(len(e["notifier"].sent), 2)  # 1 push + 1 sms
        self.assertEqual(len(e["audit"].entries), 1)

    def test_lock_already_locked_is_noop(self):  # REQ-008a, DEC-002
        e = make(status=TEMP_LOCKED)
        r = e["svc"].lock(ctx(), CARD, "k1")
        self.assertEqual((r["status"], r["changed"]), ("TEMP_LOCKED", False))
        self.assertEqual(e["notifier"].sent, [])
        self.assertEqual(e["audit"].entries, [])

    def test_cms_409_on_target_status_is_noop(self):  # [GIẢ ĐỊNH] Q-12
        e = make(status=TEMP_LOCKED)

        def cms_says_409(*args, **kwargs):
            raise CmsStatusConflict(TEMP_LOCKED)

        e["cms"].change_status = cms_says_409
        self.assertFalse(e["svc"].lock(ctx(), CARD, "k1")["changed"])

    def test_report_lost_hint(self):  # REQ-010
        e = make()
        r = e["svc"].lock(ctx(), CARD, "k1", "CANNOT_FIND_CARD")
        self.assertEqual(r["nextSteps"], {"showReportLost": True, "hotline": "1900 0000"})

    def test_cms_timeout_but_applied(self):  # timeout -> hỏi C3 thấy đã khoá -> 200
        e = make()
        e["cms"].fail_change, e["cms"].apply_before_fail = 1, True
        r = e["svc"].lock(ctx(), CARD, "k1")
        self.assertEqual((r["status"], r["changed"]), ("TEMP_LOCKED", True))
        self.assertEqual(len(e["cms"].change_calls), 1)

    def test_cms_timeout_then_retry_succeeds(self):
        e = make()
        e["cms"].fail_change = 1
        self.assertTrue(e["svc"].lock(ctx(), CARD, "k1")["changed"])
        self.assertEqual(len(e["cms"].change_calls), 2)

    def test_cms_is_source_of_truth(self):  # EX-02
        e = make(status=ACTIVE, cms_status=TEMP_LOCKED)
        r = e["svc"].lock(ctx(), CARD, "k1")
        self.assertEqual((r["previousStatus"], r["changed"]), ("TEMP_LOCKED", False))
        e2 = make(status=ACTIVE, cms_status=TEMP_LOCKED)
        self.assertEqual(e2["svc"].get_status(ctx(), CARD)["status"], "TEMP_LOCKED")
        self.assertEqual(e2["cards"].get(CARD).status, TEMP_LOCKED)

    def test_get_status_cms_down(self):
        e = make()
        e["cms"].fail_status = True
        with self.assertRaises(BankError) as err:
            e["svc"].get_status(ctx(), CARD)
        self.assertEqual(err.exception.code, "CARD_SERVICE_UNAVAILABLE")


class UnlockErrorTest(unittest.TestCase):
    def assertCode(self, code, fn, *args):
        with self.assertRaises(BankError) as err:
            fn(*args)
        self.assertEqual(err.exception.code, code)

    def test_missing_token(self):  # REQ-005
        e = make(status=TEMP_LOCKED)
        self.assertCode("STEP_UP_REQUIRED", e["svc"].unlock, ctx(), CARD, "k1", None)
        self.assertEqual(e["cards"].get(CARD).status, TEMP_LOCKED)
        self.assertEqual(e["cms"].change_calls, [])

    def test_wrong_or_foreign_or_reused_token(self):  # REQ-005
        e = make(status=TEMP_LOCKED)
        e["step_up"].issue("t-other-card", card_id=OTHER_CARD)
        e["step_up"].issue("t-other-purpose", purpose="TRANSFER")
        e["step_up"].issue("t-other-customer", customer_id="cust-002")
        for token in ("t-unknown", "t-other-card", "t-other-purpose", "t-other-customer"):
            self.assertCode("STEP_UP_INVALID", e["svc"].unlock, ctx(), CARD, "k1", token)
        ok = e["step_up"].issue("t-ok")
        e["svc"].unlock(ctx(), CARD, "k2", ok)
        e["svc"].lock(ctx(), CARD, "k3")
        self.assertCode("STEP_UP_INVALID", e["svc"].unlock, ctx(), CARD, "k4", ok)  # đã dùng
        self.assertEqual(e["cards"].get(CARD).status, TEMP_LOCKED)

    def test_active_card_still_needs_token(self):  # ADR-04
        e = make()
        self.assertCode("STEP_UP_REQUIRED", e["svc"].unlock, ctx(), CARD, "k1", None)
        self.assertCode("STEP_UP_INVALID", e["svc"].unlock, ctx(), CARD, "k1", "t-bad")

    def test_blocked_card_not_allowed(self):  # REQ-009, ngoài phạm vi mở khoá BLOCKED
        e = make(status=BLOCKED)
        self.assertCode("CARD_STATUS_NOT_ALLOWED", e["svc"].unlock, ctx(), CARD, "k1", e["step_up"].issue("t"))
        self.assertEqual(e["cards"].get(CARD).status, BLOCKED)

    def test_other_customer_card(self):
        e = make()
        self.assertCode("CARD_NOT_FOUND", e["svc"].unlock, ctx(), OTHER_CARD, "k1", "t")


class UnlockTest(unittest.TestCase):
    def test_unlock_locked_card(self):  # REQ-006
        e = make(status=TEMP_LOCKED)
        r = e["svc"].unlock(ctx(), CARD, "k1", e["step_up"].issue("t"))
        self.assertEqual((r["previousStatus"], r["status"], r["changed"]), ("TEMP_LOCKED", "ACTIVE", True))
        self.assertNotIn("nextSteps", r)
        self.assertEqual(e["cms"].change_calls[0][1], UNLOCK_ACTION)
        self.assertTrue(e["cards"].authorize(CARD, 1000))
        self.assertEqual(e["audit"].entries[0]["action"], "CARD_TEMP_UNLOCK")

    def test_unlock_active_card_is_noop(self):  # DEC-001, REQ-008b
        e = make()
        r = e["svc"].unlock(ctx(), CARD, "k1", e["step_up"].issue("t"))
        self.assertEqual((r["status"], r["changed"]), ("ACTIVE", False))
        self.assertEqual(e["notifier"].sent, [])

    def test_lock_then_unlock_round_trip(self):
        e = make()
        e["svc"].lock(ctx(), CARD, "k1")
        with self.assertRaises(BankError):
            e["cards"].authorize(CARD, 1000)
        e["svc"].unlock(ctx(), CARD, "k2", e["step_up"].issue("t"))
        self.assertTrue(e["cards"].authorize(CARD, 1000))


class NotifyTest(unittest.TestCase):
    def test_notifier_failure_does_not_rollback(self):
        e = make(notify_fail=True)
        with self.assertLogs("mbank.cards", "WARNING") as logs:
            r = e["svc"].lock(ctx(), CARD, "k1")
        self.assertTrue(r["changed"])
        self.assertEqual(e["cards"].get(CARD).status, TEMP_LOCKED)
        self.assertNotIn(CARD, "\n".join(logs.output))

    def test_sms_has_no_card_digits_push_has_last4(self):  # DEC-003, REQ-007
        e = make()
        e["svc"].lock(ctx(), CARD, "k1")
        sent = {ch: text for ch, _, text in e["notifier"].sent}
        self.assertEqual(set(sent), {"push", "sms"})
        self.assertIn("****" + LAST4, sent["push"])
        self.assertNotIn(LAST4, sent["sms"])
        for text in sent.values():
            self.assertIn("khoá tạm thời", text)
            self.assertIn("09:00 01/01/2026", text)
            self.assertIn("1900 0000", text)

    def test_logs_do_not_contain_card_id(self):
        e = make()
        with self.assertLogs("mbank.cards", "DEBUG") as logs:
            e["svc"].lock(ctx(), CARD, "k1")
            e["cards"].authorize(OTHER_CARD, 1)
        self.assertNotIn(CARD, "\n".join(logs.output))
        self.assertNotIn(OTHER_CARD, "\n".join(logs.output))


class ConcurrencyTest(unittest.TestCase):  # ADR-06
    def _run(self, e, keys):
        results, errors = [], []

        def worker(k):
            try:
                results.append(e["svc"].lock(ctx(), CARD, k))
            except BankError as exc:
                errors.append(exc)

        threads = [threading.Thread(target=worker, args=(k,)) for k in keys]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(errors, [])
        return results

    def test_same_key_concurrent_calls_cms_once(self):
        e = make(delay=0.05)
        results = self._run(e, ["k1", "k1"])
        self.assertEqual(len(e["cms"].change_calls), 1)
        self.assertEqual(results[0], results[1])

    def test_different_keys_change_once(self):
        e = make(delay=0.05)
        results = self._run(e, ["k1", "k2"])
        self.assertEqual(sorted(r["changed"] for r in results), [False, True])
        self.assertEqual(len(e["notifier"].sent), 2)


if __name__ == "__main__":
    unittest.main()
