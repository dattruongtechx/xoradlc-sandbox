"""WO-2026-041: xem danh sách thẻ (API GET /api/v1/cards ở dạng method service).

Theo BRD OUT-041-01 v1 (nội dung v0.1) và thiết kế OUT-041-02 v1 (nội dung v0.1, nháp, Tech lead chưa rà),
contract API-cards-list.md v0.1. Thiết kế còn nháp và còn 2 finding 🔴 (G-091, G-092): có thể phải làm lại.

Tách khỏi cards.py vì cards.py gần giới hạn 500 dòng (SIZE-001).
"""
from __future__ import annotations

import calendar
import logging
import os
import secrets
import threading
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Callable, Optional, Protocol

from .cards import RequestContext
from .errors import (
    CARD_SERVICE_UNAVAILABLE,
    FORBIDDEN,
    RATE_LIMITED,
    UNAUTHENTICATED,
    VALIDATION_ERROR,
    BankError,
)
from .masking import hash as hash_value
from .masking import mask, mask_card_number

log = logging.getLogger(__name__)

# Cấu hình theo môi trường, mặc định theo thiết kế.
CMS_LIST_TIMEOUT_SECONDS = float(os.environ.get("MBANK_CMS_LIST_TIMEOUT_SECONDS", "5"))  # EX-02
ALIAS_TIMEOUT_SECONDS = float(os.environ.get("MBANK_ALIAS_TIMEOUT_SECONDS", "2"))  # ADR-05 (đề xuất, chưa chốt)
CARD_LIST_RATE_LIMIT_PER_MINUTE = int(os.environ.get("MBANK_CARD_LIST_RATE_LIMIT_PER_MINUTE", "30"))  # đề xuất
RATE_LIMIT_WINDOW = timedelta(minutes=1)

REQUIRED_SCOPE = "cards:read"  # EX-10
EXPIRING_SOON_DAYS = 60  # REQ-007

CREDIT = "CREDIT"
DEBIT = "DEBIT"
CARD_TYPES = (CREDIT, DEBIT)  # REQ-005: tín dụng trước, ghi nợ sau

# Trạng thái theo API-cards-list.md mục 4.3.
ACTIVE = "ACTIVE"
TEMP_LOCKED = "TEMP_LOCKED"
BLOCKED = "BLOCKED"
EXPIRED = "EXPIRED"
NOT_ACTIVATED = "NOT_ACTIVATED"
DISPLAYED_STATUSES = frozenset({ACTIVE, TEMP_LOCKED, BLOCKED, EXPIRED, NOT_ACTIVATED})  # BR-01

STATUS_LABELS = {
    "vi": {
        ACTIVE: "Hoạt động",
        TEMP_LOCKED: "Đang khoá tạm thời",
        BLOCKED: "Bị khoá",
        EXPIRED: "Hết hạn",
        NOT_ACTIVATED: "Chưa kích hoạt",
    },
    "en": {
        ACTIVE: "Active",
        TEMP_LOCKED: "Temporarily locked",
        BLOCKED: "Blocked",
        EXPIRED: "Expired",
        NOT_ACTIVATED: "Not activated",
    },
}
# [GIẢ ĐỊNH] nhãn nhóm: thiết kế chỉ nói "theo Accept-Language", không nêu chữ.
GROUP_LABELS = {
    "vi": {CREDIT: "Thẻ tín dụng", DEBIT: "Thẻ ghi nợ"},
    "en": {CREDIT: "Credit cards", DEBIT: "Debit cards"},
}
DEFAULT_LANG = "vi"

STATUS_ACTIONS = {
    ACTIVE: ("VIEW_DETAIL", "LOCK", "CHANGE_PIN"),
    TEMP_LOCKED: ("VIEW_DETAIL", "UNLOCK"),
    BLOCKED: ("VIEW_DETAIL",),
    EXPIRED: ("VIEW_DETAIL",),
    NOT_ACTIVATED: ("VIEW_DETAIL", "ACTIVATE"),
}


# ---- Phụ thuộc bên ngoài ----


class CmsError(Exception):
    """CMS quá hạn hoặc lỗi: không có danh sách thẻ."""


@dataclass(frozen=True)
class CmsCard:
    """[GIẢ ĐỊNH] dữ liệu CMS trả cho một thẻ. API thật của CMS chưa có (Q-06)."""

    ref: str  # mã thẻ nội bộ CMS, không trả ra ngoài
    type: str  # CREDIT | DEBIT
    network: str
    product_name: str
    pan: str  # chỉ dùng để tạo số che, không lưu, không log (PII-C01/02)
    status: str  # trạng thái mục 4.3, hoặc CLOSED / CANCELLED
    issued_at: date
    is_primary_holder: bool = True
    expiry_month: Optional[int] = None
    expiry_year: Optional[int] = None
    linked_account: Optional[str] = None  # thẻ ghi nợ
    currency: Optional[str] = None  # thẻ tín dụng
    credit_limit: Optional[int] = None
    available_limit: Optional[int] = None


class CmsCardClient(Protocol):
    def list_cards(self, customer_id: str, timeout: float) -> list[CmsCard]:
        """Danh sách thẻ của khách. Ném CmsError khi lỗi / quá hạn."""


class CardAliasStore(Protocol):
    def get_aliases(self, customer_id: str, timeout: float) -> dict[str, str]:
        """CSDL Backend: {cardId: alias}. Ném lỗi bất kỳ khi lỗi / quá hạn (ADR-03 không chặn response)."""


class CardIdRegistry(Protocol):
    def card_id_for(self, customer_id: str, cms_ref: str) -> str:
        """cardId ổn định, ngẫu nhiên, không suy ra được số thẻ (REQ-010)."""


class InMemoryCardIdRegistry:
    """Bản trong bộ nhớ.

    TODO WO-2026-041: cần kho dùng chung để cardId ổn định giữa các instance và lần khởi động.
    """

    def __init__(self):
        self._ids: dict[tuple[str, str], str] = {}
        self._lock = threading.Lock()

    def card_id_for(self, customer_id: str, cms_ref: str) -> str:
        with self._lock:
            return self._ids.setdefault((customer_id, cms_ref), "crd_" + secrets.token_hex(12))


# ---- Service ----


class CardListService:
    def __init__(
        self,
        cms: CmsCardClient,
        aliases: CardAliasStore,
        card_ids: CardIdRegistry,
        now: Callable[[], datetime] = datetime.now,
        cms_timeout: float = CMS_LIST_TIMEOUT_SECONDS,
        alias_timeout: float = ALIAS_TIMEOUT_SECONDS,
        rate_limit_per_minute: int = CARD_LIST_RATE_LIMIT_PER_MINUTE,
    ):
        self.cms, self.aliases, self.card_ids, self.now = cms, aliases, card_ids, now
        self.cms_timeout, self.alias_timeout = cms_timeout, alias_timeout
        self.rate_limit_per_minute = rate_limit_per_minute
        # TODO WO-2026-041: bộ đếm rate limit ở bộ nhớ một tiến trình; nhiều instance cần kho dùng chung.
        self._attempts: dict[str, list[datetime]] = {}
        self._guard = threading.Lock()
        self._pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="card-list")

    def list_cards(
        self,
        ctx: RequestContext,
        include_inactive: bool = True,
        card_type: Optional[str] = None,
        lang: str = DEFAULT_LANG,
    ) -> dict:
        """GET /api/v1/cards?includeInactive=&type=. Mã khách chỉ lấy từ ctx (token), BR-02."""
        if not ctx.customer_id:
            raise BankError(UNAUTHENTICATED)  # EX-03
        if REQUIRED_SCOPE not in ctx.scopes:
            raise BankError(FORBIDDEN)  # EX-10
        if not isinstance(include_inactive, bool) or card_type not in (None, *CARD_TYPES):
            raise BankError(VALIDATION_ERROR)
        lang = lang if lang in STATUS_LABELS else DEFAULT_LANG
        now = self.now()
        self._check_rate(ctx.customer_id, now)

        cms_cards, alias_map = self._fetch(ctx)
        today = now.date()
        cards = []
        for raw in cms_cards:
            item = self._card(ctx, raw, alias_map, today, lang)
            if item is None:
                continue
            if card_type and item["type"] != card_type:
                continue
            if not include_inactive and item["status"] != ACTIVE:  # [GIẢ ĐỊNH] "inactive" = khác ACTIVE
                continue
            cards.append(item)

        groups = []
        for kind in CARD_TYPES:
            members = [c for c in cards if c["type"] == kind]
            if not members:
                continue
            members.sort(key=lambda c: c["issuedAt"], reverse=True)
            members.sort(key=lambda c: c["status"] != ACTIVE)  # sort ổn định: ACTIVE trước
            groups.append({"type": kind, "label": GROUP_LABELS[lang][kind], "cards": members})

        log.info("card list ok total=%s request_id=%s", len(cards), ctx.request_id)
        return {"requestId": ctx.request_id, "asOf": now.isoformat(), "total": len(cards), "groups": groups}

    # ---- Xử lý chung ----

    def _check_rate(self, customer_id: str, now: datetime) -> None:
        with self._guard:
            recent = [t for t in self._attempts.get(customer_id, []) if now - t < RATE_LIMIT_WINDOW]
            if len(recent) >= self.rate_limit_per_minute:
                self._attempts[customer_id] = recent
                raise BankError(RATE_LIMITED)
            recent.append(now)
            self._attempts[customer_id] = recent

    def _fetch(self, ctx: RequestContext) -> tuple[list[CmsCard], dict[str, str]]:
        """ADR-02: gọi CMS và CSDL Backend song song. CMS lỗi -> 503; alias lỗi -> bỏ alias (ADR-03)."""
        cms_future = self._pool.submit(self.cms.list_cards, ctx.customer_id, self.cms_timeout)
        alias_future = self._pool.submit(self.aliases.get_aliases, ctx.customer_id, self.alias_timeout)
        try:
            cms_cards = cms_future.result(timeout=self.cms_timeout)
        except (CmsError, FutureTimeout) as exc:
            log.warning("cms list failed err=%s request_id=%s", type(exc).__name__, ctx.request_id)
            alias_future.cancel()
            raise BankError(CARD_SERVICE_UNAVAILABLE, "Chưa tải được danh sách thẻ, vui lòng thử lại") from exc
        try:
            alias_map = alias_future.result(timeout=self.alias_timeout)
        except Exception as exc:  # ADR-03: mọi lỗi alias đều không chặn response
            log.warning("alias load failed err=%s request_id=%s", type(exc).__name__, ctx.request_id)
            alias_map = {}
        return cms_cards, alias_map

    def _card(self, ctx, raw: CmsCard, alias_map: dict[str, str], today: date, lang: str) -> Optional[dict]:
        if not raw.is_primary_holder:  # REQ-001, [GIẢ ĐỊNH] Q-01: chưa hiện thẻ phụ / đồng sở hữu
            return None
        if raw.status not in DISPLAYED_STATUSES:  # BR-01, xem [GIẢ ĐỊNH] về thẻ đóng ≤90 ngày trong changeset
            return None
        if raw.type not in CARD_TYPES:
            log.warning("card skipped reason=type card=%s request_id=%s", hash_value(raw.ref), ctx.request_id)
            return None
        try:
            masked = mask_card_number(raw.pan)
        except ValueError:  # [GIẢ ĐỊNH] maskedNumber không nullable -> bỏ thẻ, không lỗi cả response
            log.warning("card skipped reason=pan card=%s request_id=%s", hash_value(raw.ref), ctx.request_id)
            return None

        card_id = self.card_ids.card_id_for(ctx.customer_id, raw.ref)
        last_day = _expiry_last_day(raw.expiry_month, raw.expiry_year)
        expired = last_day is not None and today > last_day
        status = EXPIRED if expired else raw.status  # REQ-007, [GIẢ ĐỊNH] quá ngày hết hạn -> EXPIRED
        expiring_soon = (
            last_day is not None and not expired and (last_day - today).days <= EXPIRING_SOON_DAYS  # ASM-13
        )
        alias = alias_map.get(card_id) or None
        actions = list(STATUS_ACTIONS[status])
        if status == ACTIVE and raw.type == CREDIT:
            actions.append("VIEW_STATEMENT")

        item = {
            "cardId": card_id,
            "type": raw.type,
            "network": raw.network,
            "productName": raw.product_name,
            "alias": alias,
            "displayName": alias or raw.product_name,  # REQ-008
            "maskedNumber": masked,
            "last4": raw.pan[-4:],
            "status": status,
            "statusLabel": STATUS_LABELS[lang][status],
            "expiry": {"month": raw.expiry_month, "year": raw.expiry_year} if last_day else None,
            "expiringSoon": expiring_soon,
            "isPrimaryHolder": True,
            "issuedAt": raw.issued_at.isoformat(),
            "credit": _credit(raw),
            "actions": actions,
        }
        if raw.type == DEBIT:
            item["linkedAccount"] = {"maskedNumber": mask(raw.linked_account)} if raw.linked_account else None
        return item


def _expiry_last_day(month: Optional[int], year: Optional[int]) -> Optional[date]:
    """Thẻ dùng được đến hết ngày cuối của tháng hết hạn. Thiếu / sai dữ liệu -> None (expiry: null)."""
    if not month or not year or not 1 <= month <= 12:
        return None
    return date(year, month, calendar.monthrange(year, month)[1])


def _credit(raw: CmsCard) -> Optional[dict]:
    """REQ-004 / ASM-12: chỉ thẻ tín dụng có hạn mức; thiếu dữ liệu -> null."""
    if raw.type != CREDIT or raw.credit_limit is None or raw.available_limit is None:
        return None
    return {"currency": raw.currency or "VND", "creditLimit": raw.credit_limit, "availableLimit": raw.available_limit}
