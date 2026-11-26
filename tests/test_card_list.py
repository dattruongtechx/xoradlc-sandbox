"""WO-2026-041 xem danh sách thẻ. Dữ liệu test là dữ liệu bịa; số thẻ là số thử công khai của tổ chức thẻ."""
import json
import time
import unittest
from datetime import date, datetime

from mbank.card_list import (
    ACTIVE,
    BLOCKED,
    CREDIT,
    DEBIT,
    EXPIRED,
    NOT_ACTIVATED,
    TEMP_LOCKED,
    CardListService,
    CmsCard,
    CmsError,
    InMemoryCardIdRegistry,
)
from mbank.cards import RequestContext
from mbank.errors import (
    CARD_SERVICE_UNAVAILABLE,
    FORBIDDEN,
    RATE_LIMITED,
    UNAUTHENTICATED,
    VALIDATION_ERROR,
    BankError,
)
from mbank.masking import mask_card_number
from tests.fixtures.card_numbers import MASTERCARD_TEST_PAN, VISA_TEST_PAN

OWNER = "cust-001"
NOW = datetime(2026, 11, 25, 9, 0, 0)
CTX = RequestContext(customer_id=OWNER, request_id="req-1", scopes=frozenset({"cards:read"}))
LINKED_ACCOUNT = "0011223344556677"  # bịa


def cms_card(ref, kind=CREDIT, status=ACTIVE, issued=date(2025, 1, 1), **kw):
    base = dict(
        ref=ref,
        type=kind,
        network="VISA",
        product_name="Thẻ " + ref,
        pan=VISA_TEST_PAN,
        status=status,
        issued_at=issued,
        expiry_month=12,
        expiry_year=2029,
    )
    if kind == CREDIT:
        base.update(currency="VND", credit_limit=50_000_000, available_limit=12_000_000)
    else:
        base.update(linked_account=LINKED_ACCOUNT)
    base.update(kw)
    return CmsCard(**base)


class FakeCms:
    def __init__(self, cards=(), fail=False, delay=0.0):
        self.cards, self.fail, self.delay, self.calls = list(cards), fail, delay, []

    def list_cards(self, customer_id, timeout):
        self.calls.append((customer_id, timeout))
        if self.delay:
            time.sleep(self.delay)
        if self.fail:
            raise CmsError("down")
        return list(self.cards)


class FakeAliases:
    def __init__(self, aliases=None, fail=False, delay=0.0):
        self.aliases, self.fail, self.delay = aliases or {}, fail, delay

    def get_aliases(self, customer_id, timeout):
        if self.delay:
            time.sleep(self.delay)
        if self.fail:
            raise ConnectionError("db down")
        return dict(self.aliases)


def service(cms=None, aliases=None, registry=None, **kw):
    return CardListService(
        cms or FakeCms(), aliases or FakeAliases(), registry or InMemoryCardIdRegistry(), now=lambda: NOW, **kw
    )


def all_cards(result):
    return [c for g in result["groups"] for c in g["cards"]]


# ---- Luồng sai ----


class AccessErrorTest(unittest.TestCase):
    def assert_code(self, code, fn):
        with self.assertRaises(BankError) as cm:
            fn()
        self.assertEqual(cm.exception.code, code)

    def test_missing_customer_is_unauthenticated(self):  # EX-03
        cms = FakeCms([cms_card("a")])
        ctx = RequestContext(customer_id="", request_id="r", scopes=frozenset({"cards:read"}))
        self.assert_code(UNAUTHENTICATED, lambda: service(cms).list_cards(ctx))
        self.assertEqual(cms.calls, [])

    def test_missing_scope_is_forbidden(self):  # EX-10
        cms = FakeCms([cms_card("a")])
        ctx = RequestContext(customer_id=OWNER, request_id="r")
        self.assert_code(FORBIDDEN, lambda: service(cms).list_cards(ctx))
        self.assertEqual(cms.calls, [])

    def test_invalid_params(self):
        svc = service()
        self.assert_code(VALIDATION_ERROR, lambda: svc.list_cards(CTX, card_type="PREPAID"))
        self.assert_code(VALIDATION_ERROR, lambda: svc.list_cards(CTX, include_inactive="yes"))

    def test_rate_limited(self):
        svc = service(rate_limit_per_minute=2)
        svc.list_cards(CTX)
        svc.list_cards(CTX)
        self.assert_code(RATE_LIMITED, lambda: svc.list_cards(CTX))

    def test_customer_id_only_from_token(self):  # BR-02
        cms = FakeCms([])
        service(cms).list_cards(CTX)
        self.assertEqual(cms.calls[0][0], OWNER)


class CmsErrorTest(unittest.TestCase):
    def test_cms_error_returns_503(self):  # EX-02
        with self.assertRaises(BankError) as cm:
            service(FakeCms(fail=True)).list_cards(CTX)
        self.assertEqual(cm.exception.code, CARD_SERVICE_UNAVAILABLE)
        self.assertEqual(str(cm.exception), "Chưa tải được danh sách thẻ, vui lòng thử lại")

    def test_cms_timeout_returns_503(self):  # EX-02
        svc = service(FakeCms([cms_card("a")], delay=0.3), cms_timeout=0.05)
        with self.assertRaises(BankError) as cm:
            svc.list_cards(CTX)
        self.assertEqual(cm.exception.code, CARD_SERVICE_UNAVAILABLE)

    def test_cms_timeouts_passed_to_clients(self):  # ADR-05 mặc định 5s / 2s
        cms = FakeCms([])
        service(cms).list_cards(CTX)
        self.assertEqual(cms.calls[0][1], 5.0)


class AliasDegradeTest(unittest.TestCase):
    def test_alias_error_falls_back_to_product_name(self):  # ADR-03
        result = service(FakeCms([cms_card("a")]), FakeAliases(fail=True)).list_cards(CTX)
        card = all_cards(result)[0]
        self.assertIsNone(card["alias"])
        self.assertEqual(card["displayName"], "Thẻ a")

    def test_alias_timeout_does_not_block(self):  # ADR-03, ADR-05
        svc = service(FakeCms([cms_card("a")]), FakeAliases(delay=0.3), alias_timeout=0.05)
        start = time.monotonic()
        result = svc.list_cards(CTX)
        self.assertLess(time.monotonic() - start, 0.25)
        self.assertEqual(all_cards(result)[0]["displayName"], "Thẻ a")

    def test_cms_and_alias_called_in_parallel(self):  # ADR-02
        svc = service(FakeCms([cms_card("a")], delay=0.2), FakeAliases(delay=0.2), alias_timeout=1)
        start = time.monotonic()
        svc.list_cards(CTX)
        self.assertLess(time.monotonic() - start, 0.35)


class BadCardDataTest(unittest.TestCase):
    def test_missing_expiry_and_limits_are_null(self):  # thiếu dữ liệu một thẻ -> null trường đó
        raw = cms_card("a", expiry_month=None, expiry_year=None, credit_limit=None)
        card = all_cards(service(FakeCms([raw])).list_cards(CTX))[0]
        self.assertIsNone(card["expiry"])
        self.assertFalse(card["expiringSoon"])
        self.assertIsNone(card["credit"])

    def test_invalid_pan_skips_only_that_card(self):
        result = service(FakeCms([cms_card("bad", pan="12ab"), cms_card("ok")])).list_cards(CTX)
        self.assertEqual([c["productName"] for c in all_cards(result)], ["Thẻ ok"])

    def test_mask_rejects_non_card_numbers(self):
        for value in ("", "1234", "4111-1111-1111-1111", "1" * 20):
            with self.assertRaises(ValueError):
                mask_card_number(value)


# ---- Bảo mật ----


class SecurityTest(unittest.TestCase):
    def test_response_has_no_forbidden_data(self):  # mục 5 thiết kế
        cards = [
            cms_card("cms-ref-credit", product_name="Visa Gold"),
            cms_card("cms-ref-debit", kind=DEBIT, pan=MASTERCARD_TEST_PAN, product_name="Debit Classic"),
        ]
        body = json.dumps(service(FakeCms(cards)).list_cards(CTX), ensure_ascii=False)
        for secret in (VISA_TEST_PAN, MASTERCARD_TEST_PAN, LINKED_ACCOUNT, OWNER, "cms-ref-credit", "cms-ref-debit"):
            self.assertNotIn(secret, body)

    def test_card_id_random_and_stable(self):  # REQ-010
        registry = InMemoryCardIdRegistry()
        svc = service(FakeCms([cms_card("a")]), registry=registry)
        first = all_cards(svc.list_cards(CTX))[0]["cardId"]
        second = all_cards(svc.list_cards(CTX))[0]["cardId"]
        self.assertEqual(first, second)
        self.assertNotIn(VISA_TEST_PAN[-4:], first)

    def test_logs_have_no_card_data(self):  # NFR-006
        cards = [cms_card("a", pan=VISA_TEST_PAN), cms_card("b", pan="bad")]
        with self.assertLogs("mbank.card_list", level="DEBUG") as logs:
            service(FakeCms(cards), FakeAliases({"x": "Thẻ đi chợ"}, fail=True)).list_cards(CTX)
        text = "\n".join(logs.output)
        for secret in (VISA_TEST_PAN, mask_card_number(VISA_TEST_PAN), VISA_TEST_PAN[-4:], OWNER, "Thẻ đi chợ"):
            self.assertNotIn(secret, text)


# ---- Luồng thuận ----


class ListTest(unittest.TestCase):
    def test_card_fields(self):  # REQ-002, REQ-003, REQ-004, REQ-006
        registry = InMemoryCardIdRegistry()
        card_id = registry.card_id_for(OWNER, "a")
        result = service(FakeCms([cms_card("a")]), FakeAliases({card_id: "Thẻ đi chợ"}), registry).list_cards(CTX)
        self.assertEqual(result["requestId"], "req-1")
        self.assertEqual(result["asOf"], NOW.isoformat())
        self.assertEqual(result["total"], 1)
        card = all_cards(result)[0]
        self.assertEqual(
            card,
            {
                "cardId": card_id,
                "type": CREDIT,
                "network": "VISA",
                "productName": "Thẻ a",
                "alias": "Thẻ đi chợ",
                "displayName": "Thẻ đi chợ",
                "maskedNumber": "411111******1111",
                "last4": "1111",
                "status": ACTIVE,
                "statusLabel": "Hoạt động",
                "expiry": {"month": 12, "year": 2029},
                "expiringSoon": False,
                "isPrimaryHolder": True,
                "issuedAt": "2025-01-01",
                "credit": {"currency": "VND", "creditLimit": 50_000_000, "availableLimit": 12_000_000},
                "actions": ["VIEW_DETAIL", "LOCK", "CHANGE_PIN", "VIEW_STATEMENT"],
            },
        )

    def test_debit_has_no_limit_and_masked_linked_account(self):  # REQ-004, ASM-12
        card = all_cards(service(FakeCms([cms_card("d", kind=DEBIT)])).list_cards(CTX))[0]
        self.assertIsNone(card["credit"])
        self.assertEqual(card["linkedAccount"], {"maskedNumber": "************6677"})
        self.assertNotIn("VIEW_STATEMENT", card["actions"])

    def test_empty_list(self):  # REQ-011, EX-04
        self.assertEqual(
            service(FakeCms([])).list_cards(CTX),
            {"requestId": "req-1", "asOf": NOW.isoformat(), "total": 0, "groups": []},
        )

    def test_only_primary_holder(self):  # REQ-001, Q-01
        result = service(FakeCms([cms_card("own"), cms_card("sup", is_primary_holder=False)])).list_cards(CTX)
        self.assertEqual([c["productName"] for c in all_cards(result)], ["Thẻ own"])

    def test_closed_cards_excluded_other_statuses_shown(self):  # BR-01
        cards = [cms_card(s, status=s) for s in (ACTIVE, TEMP_LOCKED, BLOCKED, EXPIRED, NOT_ACTIVATED)]
        cards += [cms_card("closed", status="CLOSED"), cms_card("cancel", status="CANCELLED")]
        result = service(FakeCms(cards)).list_cards(CTX)
        self.assertEqual(result["total"], 5)
        labels = {c["status"]: c["statusLabel"] for c in all_cards(result)}
        self.assertEqual(labels[TEMP_LOCKED], "Đang khoá tạm thời")
        self.assertEqual(labels[NOT_ACTIVATED], "Chưa kích hoạt")

    def test_grouping_and_sorting(self):  # REQ-005
        cards = [
            cms_card("debit-new", kind=DEBIT, issued=date(2026, 5, 1)),
            cms_card("credit-old", issued=date(2024, 1, 1)),
            cms_card("credit-locked-new", status=TEMP_LOCKED, issued=date(2026, 6, 1)),
            cms_card("credit-new", issued=date(2026, 1, 1)),
        ]
        result = service(FakeCms(cards)).list_cards(CTX)
        self.assertEqual([g["type"] for g in result["groups"]], [CREDIT, DEBIT])
        self.assertEqual([g["label"] for g in result["groups"]], ["Thẻ tín dụng", "Thẻ ghi nợ"])
        self.assertEqual(
            [c["productName"] for c in result["groups"][0]["cards"]],
            ["Thẻ credit-new", "Thẻ credit-old", "Thẻ credit-locked-new"],
        )

    def test_filters(self):
        cards = [cms_card("c"), cms_card("d", kind=DEBIT), cms_card("l", status=TEMP_LOCKED)]
        svc = service(FakeCms(cards))
        self.assertEqual([c["productName"] for c in all_cards(svc.list_cards(CTX, card_type=DEBIT))], ["Thẻ d"])
        self.assertEqual(
            [c["productName"] for c in all_cards(svc.list_cards(CTX, include_inactive=False))], ["Thẻ c", "Thẻ d"]
        )

    def test_expiring_soon_and_expired(self):  # REQ-007, ASM-13
        cards = [
            cms_card("soon", expiry_month=1, expiry_year=2027),  # hết 31/01/2027, còn 67 ngày
            cms_card("edge", expiry_month=12, expiry_year=2026),  # hết 31/12/2026, còn 36 ngày
            cms_card("gone", expiry_month=10, expiry_year=2026),
        ]
        by_name = {c["productName"]: c for c in all_cards(service(FakeCms(cards)).list_cards(CTX))}
        self.assertFalse(by_name["Thẻ soon"]["expiringSoon"])
        self.assertTrue(by_name["Thẻ edge"]["expiringSoon"])
        self.assertEqual(by_name["Thẻ gone"]["status"], EXPIRED)
        self.assertEqual(by_name["Thẻ gone"]["statusLabel"], "Hết hạn")
        self.assertFalse(by_name["Thẻ gone"]["expiringSoon"])

    def test_english_labels(self):
        result = service(FakeCms([cms_card("a")])).list_cards(CTX, lang="en")
        self.assertEqual(result["groups"][0]["label"], "Credit cards")
        self.assertEqual(all_cards(result)[0]["statusLabel"], "Active")


if __name__ == "__main__":
    unittest.main()
