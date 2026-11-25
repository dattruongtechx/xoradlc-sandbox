"""Thẻ ghi nợ / tín dụng. Code cũ, chưa theo hết convention.

WO-2026-043: khoá / mở khoá thẻ tạm thời (CardLockService), theo BRD OUT-043-01 v0.2 và
thiết kế OUT-043-02 v0.4. Cả hai đang là bản nháp chưa rà (RISK-03): có thể phải làm lại.
"""
from __future__ import annotations

import logging
import os
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Callable, Optional, Protocol

from .errors import (
    CARD_LOCKED,
    CARD_NOT_FOUND,
    CARD_SERVICE_UNAVAILABLE,
    CARD_STATUS_NOT_ALLOWED,
    IDEMPOTENCY_KEY_REUSED,
    RATE_LIMITED,
    STEP_UP_INVALID,
    STEP_UP_REQUIRED,
    VALIDATION_ERROR,
    BankError,
)
from .masking import hash as hash_value
from .masking import mask

log = logging.getLogger(__name__)

# Trạng thái thẻ. Nội bộ viết thường như code cũ [GIẢ ĐỊNH]; API trả dạng viết hoa theo OUT-043-02.
ACTIVE = "active"
TEMP_LOCKED = "temp_locked"
BLOCKED = "blocked"  # ngân hàng khoá; ngoài phạm vi mở khoá
EXPIRED = "expired"
CLOSED = "closed"

# Cấu hình theo môi trường (biến môi trường, có giá trị mặc định theo thiết kế).
CMS_TIMEOUT_SECONDS = float(os.environ.get("MBANK_CMS_TIMEOUT_SECONDS", "5"))  # ADR-02
CARD_LOCK_RATE_LIMIT_PER_HOUR = int(os.environ.get("MBANK_CARD_LOCK_RATE_LIMIT_PER_HOUR", "10"))  # ADR-05, chờ ATTT (Q-03)
HOTLINE = os.environ.get("MBANK_HOTLINE", "1900 0000")
IDEMPOTENCY_TTL = timedelta(hours=24)  # ADR-03 lớp 1
RATE_LIMIT_WINDOW = timedelta(hours=1)

LOCK_ACTION = "TEMP_LOCK"
UNLOCK_ACTION = "TEMP_UNLOCK"
STEP_UP_PURPOSE = "CARD_UNLOCK"

LOCK_REASONS = ("TEMPORARILY_UNUSED", "CANNOT_FIND_CARD", "SUSPECTED_COMPROMISE")  # REQ-003
DEFAULT_LOCK_REASON = "TEMPORARILY_UNUSED"
REPORT_LOST_REASONS = frozenset({"CANNOT_FIND_CARD", "SUSPECTED_COMPROMISE"})  # REQ-010

STATUS_LABELS = {TEMP_LOCKED: "Đang khoá tạm thời", ACTIVE: "Đang hoạt động"}  # [GIẢ ĐỊNH] nhãn ACTIVE
STATUS_ACTIONS = {TEMP_LOCKED: ("UNLOCK", "EDIT_ALIAS"), ACTIVE: ("LOCK", "EDIT_ALIAS")}  # [GIẢ ĐỊNH] actions ACTIVE

MSG_SERVICE_UNAVAILABLE = "Chưa thực hiện được, vui lòng thử lại hoặc gọi tổng đài " + HOTLINE  # EX-01
MSG_BLOCKED = "Thẻ đang bị ngân hàng khoá, vui lòng liên hệ tổng đài"  # REQ-009


@dataclass
class Card:
    id: str
    owner_id: str
    kind: str  # "debit" | "credit"
    status: str = ACTIVE  # "active" | "temp_locked" | "blocked" | "expired" | "closed"
    last4: str = ""  # 4 số cuối thẻ, chỉ dùng cho push (DEC-003); không lưu số thẻ đầy đủ


class CardService:
    def __init__(self):
        self._cards: dict[str, Card] = {}

    def add(self, card: Card) -> None:
        self._cards[card.id] = card

    def get(self, card_id: str) -> Card:
        try:
            return self._cards[card_id]
        except KeyError:
            raise BankError(CARD_NOT_FOUND)

    def authorize(self, card_id: str, amount: int) -> bool:
        card = self.get(card_id)
        log.debug("authorize card=%s amount=%s", mask(card_id), amount)
        if card.status == TEMP_LOCKED:
            # REQ-004: từ chối với lý do "thẻ bị khoá".
            # TODO WO-2026-043 Q-01: chưa chốt giao dịch định kỳ đã uỷ quyền (BR-03) có được qua không; hiện chặn tất cả.
            raise BankError(CARD_LOCKED, "Thẻ bị khoá")
        return card.status == ACTIVE


# ---- Phụ thuộc bên ngoài (WO-2026-043) ----


class CmsError(Exception):
    """CMS quá hạn hoặc lỗi 5xx: chưa rõ trạng thái thẻ."""


class CmsStatusConflict(Exception):
    """CMS trả 409: thẻ đang ở trạng thái không cho thao tác này."""

    def __init__(self, status: str):
        super().__init__(status)
        self.status = status


class CmsClient(Protocol):
    def change_status(self, card_id: str, action: str, idem_key: str, timeout: float) -> tuple[str, str]:
        """C2: action TEMP_LOCK / TEMP_UNLOCK, gửi kèm Idempotency-Key (ADR-03 lớp 2).

        Trả (previous_status, status). Ném CmsStatusConflict (409) hoặc CmsError (timeout / 5xx).
        """

    def get_status(self, card_id: str, timeout: float) -> str:
        """C3: hỏi trạng thái hiện tại. Ném CmsError."""


class StepUpVerifier(Protocol):
    def consume(self, token: str, customer_id: str, card_id: str, purpose: str) -> bool:
        """Kiểm X-Step-Up-Token (đúng khách, purpose, cardId, chưa dùng, chưa hết hạn) và đánh dấu đã dùng ngay.

        Trả False khi token không hợp lệ. Đếm sai 3 lần -> 423 nằm ở bước S1/S2 của step-up service (REQ-012).
        TODO WO-2026-043 SEC-A02: thiết kế chưa nêu cách mã hoá khi lưu tạm token 120 giây và nơi quản lý
        khoá mã hoá; phần lưu trữ thuộc step-up service, chưa hiện thực ở đây.
        """


class Notifier(Protocol):
    def push(self, customer_id: str, text: str) -> None: ...

    def sms(self, customer_id: str, text: str) -> None: ...


class AuditLog(Protocol):
    def record(self, entry: dict) -> None: ...


@dataclass(frozen=True)
class RequestContext:
    customer_id: str
    request_id: str
    device_id: str = ""
    ip: str = ""


class CardLockService:
    """API L1 POST /cards/{cardId}/lock và L2 POST /cards/{cardId}/unlock ở dạng method service."""

    def __init__(
        self,
        cards: CardService,
        cms: CmsClient,
        step_up: StepUpVerifier,
        notifier: Notifier,
        audit: AuditLog,
        now: Callable[[], datetime] = datetime.now,
        rate_limit_per_hour: int = CARD_LOCK_RATE_LIMIT_PER_HOUR,
        cms_timeout: float = CMS_TIMEOUT_SECONDS,
    ):
        self.cards, self.cms, self.step_up, self.notifier, self.audit = cards, cms, step_up, notifier, audit
        self.now, self.rate_limit_per_hour, self.cms_timeout = now, rate_limit_per_hour, cms_timeout
        # TODO WO-2026-043 ADR-03/ADR-05/ADR-06: bản ghi idempotency, bộ đếm rate limit và khoá theo cardId
        # đang ở bộ nhớ một tiến trình; chạy nhiều instance cần kho dùng chung và khoá phân tán.
        self._idem: dict[tuple[str, str, str], tuple[tuple, dict, datetime]] = {}
        self._attempts: dict[str, list[datetime]] = {}
        self._guard = threading.Lock()
        self._card_locks: dict[str, threading.Lock] = {}

    # ---- API ----

    def lock(self, ctx: RequestContext, card_id: str, idem_key: str, reason: Optional[str] = None) -> dict:
        """L1. Không cần step-up (REQ-002)."""
        reason = reason or DEFAULT_LOCK_REASON
        if not idem_key or reason not in LOCK_REASONS:
            raise BankError(VALIDATION_ERROR)
        self._owned_card(ctx, card_id)
        return self._change(ctx, card_id, idem_key, LOCK_ACTION, reason)

    def unlock(self, ctx: RequestContext, card_id: str, idem_key: str, step_up_token: Optional[str]) -> dict:
        """L2. Luôn bắt buộc step-up hợp lệ, kể cả khi thẻ đã ACTIVE (ADR-04)."""
        if not idem_key:
            raise BankError(VALIDATION_ERROR)
        self._owned_card(ctx, card_id)
        if not step_up_token:
            raise BankError(STEP_UP_REQUIRED)
        if not self.step_up.consume(step_up_token, ctx.customer_id, card_id, STEP_UP_PURPOSE):
            log.info("unlock step-up invalid card=%s request=%s", hash_value(card_id), ctx.request_id)
            raise BankError(STEP_UP_INVALID)
        # TODO WO-2026-043 Q-05: chưa biết CMS phân biệt TEMP_LOCKED do khách hay do ngân hàng khoá; hiện mọi
        # thẻ temp_locked đều cho khách mở khoá.
        return self._change(ctx, card_id, idem_key, UNLOCK_ACTION, None)

    def get_status(self, ctx: RequestContext, card_id: str) -> dict:
        """Trạng thái thẻ lấy từ CMS làm chuẩn và cập nhật lại bản lưu tại Mobile Backend (EX-02)."""
        card = self._owned_card(ctx, card_id)
        try:
            card.status = self.cms.get_status(card_id, timeout=self.cms_timeout)
        except CmsError as exc:
            raise BankError(CARD_SERVICE_UNAVAILABLE, MSG_SERVICE_UNAVAILABLE) from exc
        return {
            "cardId": card_id,
            "status": card.status.upper(),
            "statusLabel": STATUS_LABELS.get(card.status, ""),
            "actions": list(STATUS_ACTIONS.get(card.status, ())),
        }

    # ---- Xử lý chung ----

    def _owned_card(self, ctx: RequestContext, card_id: str) -> Card:
        card = self.cards.get(card_id)
        if card.owner_id != ctx.customer_id:
            raise BankError(CARD_NOT_FOUND)  # EX-09: không lộ việc thẻ có tồn tại
        return card

    def _card_lock(self, card_id: str) -> threading.Lock:
        with self._guard:
            return self._card_locks.setdefault(card_id, threading.Lock())

    def _change(self, ctx: RequestContext, card_id: str, idem_key: str, action: str, reason: Optional[str]) -> dict:
        fingerprint = (action, reason)
        key = (ctx.customer_id, card_id, idem_key)
        with self._card_lock(card_id):  # ADR-06
            now = self.now()
            cached = self._idem.get(key)
            if cached and now - cached[2] < IDEMPOTENCY_TTL:
                if cached[0] != fingerprint:
                    raise BankError(IDEMPOTENCY_KEY_REUSED)
                return dict(cached[1])  # gọi lặp: trả kết quả cũ, không gọi CMS, không gửi thông báo
            self._check_rate(card_id, now)

            card = self.cards.get(card_id)
            previous, status = self._call_cms(card, action, idem_key)
            card.status = status
            changed = previous != status
            result = self._response(ctx, card_id, action, reason, previous, status, changed, self.now())
            self._idem[key] = (fingerprint, dict(result), now)
            if changed:
                self._audit(ctx, card_id, action, reason, previous, status, result["effectiveAt"])

        log.info("card %s ok card=%s changed=%s request=%s", action, hash_value(card_id), changed, ctx.request_id)
        if changed:  # DEC-002
            self._notify(ctx, card, action, result["effectiveAt"])
        return result

    def _check_rate(self, card_id: str, now: datetime) -> None:
        recent = [t for t in self._attempts.get(card_id, []) if now - t < RATE_LIMIT_WINDOW]
        if len(recent) >= self.rate_limit_per_hour:
            self._attempts[card_id] = recent
            raise BankError(RATE_LIMITED)
        recent.append(now)
        self._attempts[card_id] = recent

    def _call_cms(self, card: Card, action: str, idem_key: str) -> tuple[str, str]:
        """Gọi C2; quá hạn / 5xx -> hỏi C3, chưa đổi thì thử lại C2 một lần cùng Idempotency-Key, vẫn lỗi -> 503."""
        target = TEMP_LOCKED if action == LOCK_ACTION else ACTIVE
        try:
            return self._cms_change(card, action, idem_key, target)
        except CmsError:
            log.warning("cms change failed card=%s action=%s, query status", hash_value(card.id), action)
        try:
            current = self.cms.get_status(card.id, timeout=self.cms_timeout)
        except CmsError:
            log.warning("cms status query failed card=%s", hash_value(card.id))
            current = None
        if current == target:
            # [GIẢ ĐỊNH] previous lấy từ trạng thái Mobile Backend đang giữ, vì CMS không trả về ở nhánh này.
            return card.status, target
        try:
            return self._cms_change(card, action, idem_key, target)
        except CmsError as exc:
            raise BankError(CARD_SERVICE_UNAVAILABLE, MSG_SERVICE_UNAVAILABLE) from exc

    def _cms_change(self, card: Card, action: str, idem_key: str, target: str) -> tuple[str, str]:
        try:
            previous, status = self.cms.change_status(card.id, action, idem_key, timeout=self.cms_timeout)
        except CmsStatusConflict as exc:
            if exc.status == target:
                # [GIẢ ĐỊNH] Q-12: thẻ đã ở trạng thái đích -> 200 changed=false (REQ-008, DEC-001), không 409.
                return target, target
            card.status = exc.status  # EX-02: CMS là chuẩn
            raise BankError(CARD_STATUS_NOT_ALLOWED, MSG_BLOCKED if exc.status == BLOCKED else "") from exc
        return previous, status

    def _response(self, ctx, card_id, action, reason, previous, status, changed, at: datetime) -> dict:
        result = {
            "requestId": ctx.request_id,
            "cardId": card_id,
            "previousStatus": previous.upper(),
            "status": status.upper(),
            "statusLabel": STATUS_LABELS.get(status, ""),
            "changed": changed,
            "effectiveAt": at.isoformat(),
            "actions": list(STATUS_ACTIONS.get(status, ())),
        }
        if action == LOCK_ACTION:
            result["nextSteps"] = {"showReportLost": reason in REPORT_LOST_REASONS, "hotline": HOTLINE}
        return result

    def _audit(self, ctx, card_id, action, reason, previous, status, at: str) -> None:
        self.audit.record(
            {
                "at": at,
                "actor": hash_value(ctx.customer_id),
                "action": "CARD_" + action,
                "card": hash_value(card_id),
                "previousStatus": previous.upper(),
                "status": status.upper(),
                "reason": reason,
                "requestId": ctx.request_id,
                "deviceId": ctx.device_id,
                "ip": ctx.ip,
            }
        )

    def _notify(self, ctx: RequestContext, card: Card, action: str, at: str) -> None:
        """REQ-007. DEC-003: 4 số cuối thẻ chỉ có trong push, không có trong SMS."""
        verb = "khoá tạm thời" if action == LOCK_ACTION else "mở khoá"
        when = datetime.fromisoformat(at).strftime("%H:%M %d/%m/%Y")
        tail = f"Không phải bạn thực hiện? Gọi {HOTLINE}."
        messages = (
            ("push", f"Thẻ ****{card.last4} đã được {verb} lúc {when}. {tail}"),
            ("sms", f"Thẻ của Quý khách đã được {verb} lúc {when}. {tail}"),
        )
        for channel, text in messages:
            try:
                getattr(self.notifier, channel)(ctx.customer_id, text)
            except Exception as exc:  # [GIẢ ĐỊNH] lỗi gửi thông báo không rollback trạng thái thẻ
                log.warning("notify failed channel=%s card=%s err=%s", channel, hash_value(card.id), type(exc).__name__)
