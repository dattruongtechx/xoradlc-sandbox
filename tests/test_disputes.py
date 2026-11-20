"""Test tra soát giao dịch (WO-2026-017). Dữ liệu bịa."""
import unittest
from datetime import date, datetime, timedelta

from mbank import errors
from mbank.accounts import Account, AccountRepo
from mbank.disputes import (
    MAX_ATTACHMENT_BYTES,
    Attachment,
    DisputeAlreadyOpen,
    DisputeRepo,
    DisputeService,
    IntakeResult,
    PinAuthResult,
    Status,
    is_eligible,
    prefill_form,
    upload_attachments,
)
from mbank.errors import BankError
from mbank.transactions import Transaction

NOW = datetime(2026, 11, 20, 10)
JPG = b"\xff\xd8\xff\xe0" + b"0" * 100
PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 100
PIN_OK = PinAuthResult(True, "pin-sess-1")


def tx(days_ago=1, kind="transfer_out", account="0000111122", tx_id="tx1"):
    return Transaction(tx_id, account, -50_000, "bia", NOW - timedelta(days=days_ago), kind)


class FakeIntake:
    def __init__(self, fail=None, code="TS-0001"):
        self.fail, self.code, self.calls = fail, code, []

    def create(self, req, timeout):
        self.calls.append(req)
        if self.fail:
            raise self.fail
        return IntakeResult(f"{self.code}-{len(self.calls)}" if self.code else "", date(2026, 12, 5))


class FakeNotifier:
    def __init__(self, fail=False):
        self.fail, self.sent = fail, []

    def push(self, owner_id, message):
        if self.fail:
            raise ConnectionError("push down")
        self.sent.append((owner_id, message))


class FakeStore:
    def __init__(self, fail=False):
        self.fail = fail

    def put(self, owner_id, att):
        if self.fail:
            raise IOError("storage down")
        return f"ref://{att.filename}"


class FailingRepo(DisputeRepo):
    def list_by_owner(self, owner_id):
        raise TimeoutError("db timeout")


def make(intake=None, notifier=None, repo=None):
    accts = AccountRepo()
    accts.add(Account("0000111122", "u1", "payment", 1_000_000))
    accts.add(Account("0000333344", "u2", "payment", 0))
    intake, notifier = intake or FakeIntake(), notifier or FakeNotifier()
    return DisputeService(accts, intake, notifier, repo, now=lambda: NOW), intake, notifier


def submit(svc, key="k1", owner="u1", t=None, reason="wrong_transfer", refs=(), pin=PIN_OK):
    return svc.submit(key, owner, t or tx(), reason, "mo ta bia", list(refs), pin)


class EligibilityTest(unittest.TestCase):  # REQ-001, BR-03, BR-04, EX-02
    def test_over_90_days_not_eligible(self):
        self.assertFalse(is_eligible(tx(days_ago=91), NOW))

    def test_bill_payment_not_eligible(self):
        self.assertFalse(is_eligible(tx(kind="bill_payment"), NOW))

    def test_unclassified_legacy_tx_not_eligible(self):
        self.assertFalse(is_eligible(tx(kind=None), NOW))

    def test_day_90_and_each_eligible_kind(self):
        for k in ("transfer_out", "transfer_in", "card"):
            self.assertTrue(is_eligible(tx(days_ago=90, kind=k), NOW), k)


class PrefillTest(unittest.TestCase):  # REQ-008
    def test_prefill_has_tx_id_time_amount(self):
        t = tx()
        self.assertEqual(prefill_form(t), {"tx_id": "tx1", "at": t.at, "amount": -50_000})


class AttachmentTest(unittest.TestCase):  # REQ-003, EX-01
    def test_rejects_wrong_format_even_with_jpg_name(self):
        refs, rej = upload_attachments(FakeStore(), "u1", [Attachment("a.jpg", b"GIF89a....")])
        self.assertEqual((refs, rej[0]["reason"]), ([], "invalid_format"))

    def test_rejects_over_5mb(self):
        big = JPG + b"0" * MAX_ATTACHMENT_BYTES
        _, rej = upload_attachments(FakeStore(), "u1", [Attachment("a.jpg", big)])
        self.assertEqual(rej[0]["reason"], "too_large")

    def test_rejects_fourth_file(self):
        files = [Attachment(f"{i}.png", PNG) for i in range(4)]
        refs, rej = upload_attachments(FakeStore(), "u1", files)
        self.assertEqual((len(refs), rej[0]["reason"]), (3, "too_many"))

    def test_upload_failure_reported_not_raised(self):
        refs, rej = upload_attachments(FakeStore(fail=True), "u1", [Attachment("a.png", PNG)])
        self.assertEqual((refs, rej[0]["reason"]), ([], "upload_failed"))

    def test_submit_rejects_more_than_3_refs(self):
        svc, _, _ = make()
        with self.assertRaises(BankError) as e:
            submit(svc, refs=["r1", "r2", "r3", "r4"])
        self.assertEqual(e.exception.code, errors.DISPUTE_ATTACHMENT_INVALID)

    def test_accepts_jpg_and_png(self):
        refs, rej = upload_attachments(FakeStore(), "u1", [Attachment("a.jpg", JPG), Attachment("b.png", PNG)])
        self.assertEqual((len(refs), rej), (2, []))


class SubmitFailureTest(unittest.TestCase):
    def test_missing_reason_rejected(self):  # REQ-002
        svc, intake, _ = make()
        with self.assertRaises(BankError) as e:
            submit(svc, reason="")
        self.assertEqual(e.exception.code, errors.DISPUTE_INVALID_REASON)
        self.assertEqual(intake.calls, [])

    def test_wrong_pin_creates_nothing(self):  # REQ-006, EX-04
        svc, intake, _ = make()
        with self.assertRaises(BankError) as e:
            submit(svc, pin=PinAuthResult(False, "pin-sess-1"))
        self.assertEqual(e.exception.code, errors.DISPUTE_PIN_FAILED)
        self.assertEqual((intake.calls, svc.list_mine("u1")), ([], []))

    def test_other_users_transaction_rejected(self):
        svc, intake, _ = make()
        with self.assertRaises(BankError) as e:
            submit(svc, owner="u2")
        self.assertEqual(e.exception.code, errors.DISPUTE_NOT_ELIGIBLE)
        self.assertEqual(intake.calls, [])

    def test_over_90_days_rejected_on_submit(self):  # EX-02
        svc, _, _ = make()
        with self.assertRaises(BankError) as e:
            submit(svc, t=tx(days_ago=91))
        self.assertEqual(e.exception.code, errors.DISPUTE_NOT_ELIGIBLE)

    def test_already_open_returns_existing_code(self):  # BR-01, EX-03
        svc, _, _ = make()
        first = submit(svc, key="k1").dispute
        with self.assertRaises(DisputeAlreadyOpen) as e:
            submit(svc, key="k2")
        self.assertEqual((e.exception.code, e.exception.existing_code), (errors.DISPUTE_ALREADY_OPEN, first.code))

    def test_intake_timeout_creates_nothing(self):  # EX-06, DEC-006
        svc, _, _ = make(intake=FakeIntake(fail=TimeoutError()))
        with self.assertRaises(BankError) as e:
            submit(svc)
        self.assertEqual(e.exception.code, errors.DISPUTE_SUBMIT_FAILED)
        self.assertEqual(svc.list_mine("u1"), [])

    def test_no_dispute_code_is_not_success(self):  # DEC-006
        svc, _, _ = make(intake=FakeIntake(code=""))
        with self.assertRaises(BankError) as e:
            submit(svc)
        self.assertEqual(e.exception.code, errors.DISPUTE_SUBMIT_FAILED)
        self.assertEqual(svc.list_mine("u1"), [])

    def test_retry_after_failure_succeeds_with_same_key(self):  # EX-06: gửi lại không trùng
        intake = FakeIntake(fail=ConnectionError())
        svc, _, _ = make(intake=intake)
        with self.assertRaises(BankError):
            submit(svc, key="k1")
        intake.fail = None
        submit(svc, key="k1")
        self.assertEqual(len(svc.list_mine("u1")), 1)

    def test_key_reused_for_other_tx_conflicts(self):
        svc, _, _ = make()
        submit(svc, key="k1")
        with self.assertRaises(BankError) as e:
            submit(svc, key="k1", t=tx(tx_id="tx2"))
        self.assertEqual(e.exception.code, errors.DISPUTE_IDEMPOTENCY_CONFLICT)


class SubmitSuccessTest(unittest.TestCase):
    def test_creates_received_dispute_with_code(self):  # REQ-002
        svc, _, _ = make()
        r = submit(svc)
        self.assertEqual((r.dispute.status, r.dispute.code), (Status.RECEIVED, "TS-0001-1"))
        self.assertFalse(r.suggest_lock_card)

    def test_replay_same_key_returns_same_dispute(self):  # EX-05, DEC-007, D2
        svc, intake, _ = make()
        a = submit(svc, key="k1").dispute
        b = submit(svc, key="k1").dispute
        self.assertIs(a, b)
        self.assertEqual(len(intake.calls), 1)

    def test_pin_value_never_sent(self):  # DEC-008
        svc, intake, _ = make()
        submit(svc)
        fields = vars(intake.calls[0])
        self.assertEqual(fields["pin_session_id"], "pin-sess-1")
        self.assertFalse(any("pin" in k and k != "pin_session_id" for k in fields))

    def test_not_performed_suggests_lock_card(self):  # BR-02
        svc, _, _ = make()
        self.assertTrue(submit(svc, reason="not_performed").suggest_lock_card)

    def test_audit_log_masks_account(self):
        svc, _, _ = make()
        with self.assertLogs("mbank.audit", level="INFO") as cm:
            submit(svc)
        line = cm.output[0]
        self.assertIn("dispute_submit", line)
        self.assertNotIn("0000111122", line)
        self.assertNotIn("who=u1", line)


class ListTest(unittest.TestCase):  # REQ-004, REQ-007, EX-09
    def test_list_load_failure_raises_standard_error(self):
        svc, _, _ = make(repo=FailingRepo())
        with self.assertRaises(BankError) as e:
            svc.list_mine("u1")
        self.assertEqual(e.exception.code, errors.DISPUTE_LIST_LOAD_FAILED)

    def test_no_result_field_before_done(self):
        svc, _, _ = make()
        d = submit(svc).dispute
        svc.on_status_changed(d.code, "in_progress", result="khong duoc hien")
        self.assertNotIn("result", svc.list_mine("u1")[0])

    def test_list_shows_code_status_due_date_and_result_when_done(self):
        svc, _, _ = make()
        d = submit(svc).dispute
        svc.on_status_changed(d.code, "done", result="Da hoan tien")
        row = svc.list_mine("u1")[0]
        self.assertEqual(
            row, {"code": d.code, "tx_id": "tx1", "status": "done", "due_date": date(2026, 12, 5), "result": "Da hoan tien"}
        )

    def test_list_only_own_disputes(self):
        svc, _, _ = make()
        submit(svc)
        self.assertEqual(svc.list_mine("u2"), [])


class StatusPushTest(unittest.TestCase):  # REQ-005, EX-08
    def test_unknown_status_rejected(self):
        svc, _, _ = make()
        d = submit(svc).dispute
        with self.assertRaises(BankError) as e:
            svc.on_status_changed(d.code, "closed")
        self.assertEqual(e.exception.code, errors.DISPUTE_INVALID_STATUS)

    def test_unknown_code_rejected(self):
        svc, _, _ = make()
        with self.assertRaises(BankError) as e:
            svc.on_status_changed("TS-404", "done")
        self.assertEqual(e.exception.code, errors.DISPUTE_NOT_FOUND)

    def test_push_failure_keeps_new_status(self):
        svc, _, _ = make(notifier=FakeNotifier(fail=True))
        d = submit(svc).dispute
        svc.on_status_changed(d.code, "in_progress")
        self.assertEqual(svc.list_mine("u1")[0]["status"], "in_progress")

    def test_non_io_push_error_not_swallowed(self):  # convention: không bắt lỗi chung chung
        class BuggyNotifier:
            def push(self, owner_id, message):
                raise ValueError("bug")

        svc, _, _ = make(notifier=BuggyNotifier())
        d = submit(svc).dispute
        with self.assertRaises(ValueError):
            svc.on_status_changed(d.code, "in_progress")

    def test_push_has_code_only_and_once_per_change(self):
        svc, _, notifier = make()
        d = submit(svc).dispute
        svc.on_status_changed(d.code, "in_progress")
        svc.on_status_changed(d.code, "in_progress")
        self.assertEqual(len(notifier.sent), 1)
        owner, msg = notifier.sent[0]
        self.assertIn(d.code, msg)
        self.assertNotIn("0000111122", msg)

    def test_done_dispute_allows_new_one(self):  # BR-01: chỉ chặn khi đang mở
        svc, _, _ = make()
        d = submit(svc, key="k1").dispute
        svc.on_status_changed(d.code, "done", result="ok")
        self.assertNotEqual(submit(svc, key="k2").dispute.code, d.code)


if __name__ == "__main__":
    unittest.main()
