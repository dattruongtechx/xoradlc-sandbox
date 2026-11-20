"""Tra soát giao dịch (WO-2026-017).

Nguồn: BRD-Tra-soat-giao-dich-WO-2026-017 v0.1 (nháp), Thiet-ke-Tra-soat-giao-dich-WO-2026-017 v0.2 (nháp).

Phạm vi backend: xét điều kiện tra soát, điền sẵn form, kiểm ảnh, gửi yêu cầu sang hệ thống
tiếp nhận tra soát, danh sách yêu cầu, cập nhật trạng thái + push.

Hệ thống tiếp nhận (DisputeIntakeClient), kho ảnh (AttachmentStore) và push (Notifier) là
interface được inject. Bản cài đặt thật chưa làm vì chưa có API contract, TLS, cơ chế xác thực
API và nơi quản lý khoá mã hoá (cảnh báo SEC-A01/A02/A03 của bước Thiết kế).
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Protocol

from .accounts import AccountRepo
from .errors import (
    DISPUTE_ALREADY_OPEN,
    DISPUTE_ATTACHMENT_INVALID,
    DISPUTE_IDEMPOTENCY_CONFLICT,
    DISPUTE_INVALID_REASON,
    DISPUTE_INVALID_STATUS,
    DISPUTE_LIST_LOAD_FAILED,
    DISPUTE_NOT_ELIGIBLE,
    DISPUTE_NOT_FOUND,
    DISPUTE_PIN_FAILED,
    DISPUTE_SUBMIT_FAILED,
    BankError,
)
from .masking import hash, mask  # noqa: A004 - che dữ liệu trước khi log (convention §4, PII-001)
from .transactions import Transaction

log = logging.getLogger(__name__)
audit = logging.getLogger("mbank.audit")

DISPUTE_WINDOW_DAYS = 90  # BR-04 / DEC-001
ELIGIBLE_KINDS = frozenset({"transfer_out", "transfer_in", "card"})  # BR-03 / DEC-002; bill_payment ngoài phạm vi (ASM-03)

MAX_ATTACHMENTS = 3  # REQ-003
MAX_ATTACHMENT_BYTES = 5 * 1024 * 1024  # REQ-003: mỗi ảnh ≤ 5MB
_MAGIC = {"jpg": (b"\xff\xd8\xff",), "png": (b"\x89PNG\r\n\x1a\n",)}

# DEC-006: gọi đồng bộ có timeout. Giá trị mặc định 10s là giả định, thiết kế chưa nêu số.
INTAKE_TIMEOUT_SECONDS = float(os.environ.get("DISPUTE_INTAKE_TIMEOUT_SECONDS", "10"))


class Reason(str, Enum):  # REQ-002
    WRONG_TRANSFER = "wrong_transfer"  # Chuyển nhầm
    DEBITED_NOT_COMPLETED = "debited_not_completed"  # Đã trừ tiền nhưng chưa thành công
    NOT_PERFORMED = "not_performed"  # Không thực hiện giao dịch này
    OTHER = "other"  # Khác


class Status(str, Enum):  # REQ-004
    RECEIVED = "received"  # Đã tiếp nhận
    IN_PROGRESS = "in_progress"  # Đang xử lý
    DONE = "done"  # Đã xong


@dataclass(frozen=True)
class PinAuthResult:
    """DEC-008: chỉ kết quả xác thực PIN do dịch vụ PIN hiện có trả về. Không có giá trị PIN."""

    passed: bool
    session_id: str


@dataclass(frozen=True)
class Attachment:
    filename: str
    data: bytes


@dataclass(frozen=True)
class IntakeRequest:
    idem_key: str
    owner_id: str
    tx_id: str
    reason: str
    description: str
    attachment_refs: tuple[str, ...]
    pin_session_id: str  # DEC-008: không gửi PIN


@dataclass(frozen=True)
class IntakeResult:
    dispute_code: str  # mã tra soát
    due_date: date  # hạn trả lời dự kiến (D3: do hệ thống tiếp nhận trả về)


class DisputeIntakeClient(Protocol):
    def create(self, req: IntakeRequest, timeout: float) -> IntakeResult: ...


class AttachmentStore(Protocol):
    """DEC-009: lưu nội bộ, mã hoá at-rest; trả tham chiếu (URL có hạn) cho hệ thống ngoài."""

    def put(self, owner_id: str, att: Attachment) -> str: ...


class Notifier(Protocol):
    def push(self, owner_id: str, message: str) -> None: ...


@dataclass
class Dispute:
    code: str
    owner_id: str
    tx_id: str
    account: str
    reason: Reason
    description: str
    attachment_refs: tuple[str, ...]
    due_date: date
    status: Status = Status.RECEIVED
    result: str | None = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass(frozen=True)
class SubmitResult:
    dispute: Dispute
    suggest_lock_card: bool  # BR-02


class DisputeAlreadyOpen(BankError):
    """EX-03: kèm mã yêu cầu đang mở để app chuyển khách tới đó."""

    def __init__(self, existing_code: str):
        super().__init__(DISPUTE_ALREADY_OPEN, "Giao dịch đã có yêu cầu tra soát đang mở")
        self.existing_code = existing_code


class DisputeRepo:
    def __init__(self):
        self._items: dict[str, Dispute] = {}

    def add(self, d: Dispute) -> None:
        self._items[d.code] = d

    def get(self, code: str) -> Dispute:
        if code not in self._items:
            raise BankError(DISPUTE_NOT_FOUND)
        return self._items[code]

    def list_by_owner(self, owner_id: str) -> list[Dispute]:
        return [d for d in self._items.values() if d.owner_id == owner_id]

    def open_for(self, tx_id: str, account: str) -> Dispute | None:
        return next(
            (d for d in self._items.values() if d.tx_id == tx_id and d.account == account and d.status != Status.DONE),
            None,
        )


def is_eligible(tx: Transaction, now: datetime) -> bool:
    """REQ-001: có nút "Tra soát" khi loại hợp lệ (BR-03) và trong 90 ngày (BR-04, tính cả ngày thứ 90)."""
    if tx.kind not in ELIGIBLE_KINDS:
        return False
    age = (now.date() - tx.at.date()).days
    return 0 <= age <= DISPUTE_WINDOW_DAYS


def prefill_form(tx: Transaction) -> dict:
    """REQ-008: thông tin điền sẵn khi mở form tra soát."""
    return {"tx_id": tx.id, "at": tx.at, "amount": tx.amount}


def _image_kind(data: bytes) -> str | None:
    return next((k for k, sigs in _MAGIC.items() if any(data.startswith(s) for s in sigs)), None)


def upload_attachments(store: AttachmentStore, owner_id: str, files: list[Attachment]) -> tuple[list[str], list[dict]]:
    """REQ-003 / EX-01: trả (refs nhận, danh sách bị từ chối kèm lý do). Ảnh lỗi không chặn việc gửi.

    Định dạng xét theo magic bytes, không tin đuôi file hay content-type từ client.
    """
    refs: list[str] = []
    rejected: list[dict] = []
    for i, f in enumerate(files):
        if i >= MAX_ATTACHMENTS:
            rejected.append({"filename": f.filename, "reason": "too_many"})
        elif _image_kind(f.data) is None:
            rejected.append({"filename": f.filename, "reason": "invalid_format"})
        elif len(f.data) > MAX_ATTACHMENT_BYTES:
            rejected.append({"filename": f.filename, "reason": "too_large"})
        else:
            try:
                refs.append(store.put(owner_id, f))
            except OSError as exc:  # EX-01: lỗi I/O / mạng / timeout khi tải ảnh -> báo lý do, vẫn cho gửi không kèm ảnh
                log.warning("dispute attachment upload failed owner=%s err=%s", hash(owner_id), type(exc).__name__)
                rejected.append({"filename": f.filename, "reason": "upload_failed"})
    return refs, rejected


class DisputeService:
    def __init__(
        self,
        accounts: AccountRepo,
        intake: DisputeIntakeClient,
        notifier: Notifier,
        repo: DisputeRepo | None = None,
        now=datetime.now,
    ):
        self.accounts, self.intake, self.notifier, self.now = accounts, intake, notifier, now
        self.repo = repo or DisputeRepo()
        self._by_key: dict[str, Dispute] = {}

    def submit(
        self,
        idem_key: str,
        owner_id: str,
        tx: Transaction,
        reason: str,
        description: str,
        attachment_refs: list[str],
        pin_auth: PinAuthResult,
    ) -> SubmitResult:
        """REQ-002 / REQ-006. `tx` phải do tầng API nạp từ TransactionLog phía server, không lấy từ client."""
        # EX-05 / DEC-007 (D2): gọi lại cùng key -> trả yêu cầu đã tạo, không tạo mới
        if idem_key in self._by_key:
            prev = self._by_key[idem_key]
            if prev.owner_id != owner_id or prev.tx_id != tx.id or prev.account != tx.account:
                raise BankError(DISPUTE_IDEMPOTENCY_CONFLICT)
            return SubmitResult(prev, prev.reason == Reason.NOT_PERFORMED)

        try:
            reason_v = Reason(reason)
        except ValueError:
            raise BankError(DISPUTE_INVALID_REASON, "Cần chọn lý do tra soát") from None

        # Giao dịch phải thuộc tài khoản của người gửi; không phân biệt lỗi để tránh dò giao dịch người khác
        if self.accounts.get(tx.account).owner_id != owner_id or not is_eligible(tx, self.now()):
            raise BankError(DISPUTE_NOT_ELIGIBLE)

        existing = self.repo.open_for(tx.id, tx.account)  # BR-01 / EX-03
        if existing is not None:
            raise DisputeAlreadyOpen(existing.code)

        if not pin_auth.passed or not pin_auth.session_id:  # REQ-006 / EX-04
            raise BankError(DISPUTE_PIN_FAILED)

        if len(attachment_refs) > MAX_ATTACHMENTS:  # REQ-003
            raise BankError(DISPUTE_ATTACHMENT_INVALID)

        req = IntakeRequest(
            idem_key, owner_id, tx.id, reason_v.value, description, tuple(attachment_refs), pin_auth.session_id
        )
        try:
            res = self.intake.create(req, timeout=INTAKE_TIMEOUT_SECONDS)
        except Exception as exc:  # EX-06: mất mạng / timeout -> không tạo yêu cầu, client giữ nội dung để gửi lại
            log.warning("dispute intake failed tx=%s err=%s", tx.id, type(exc).__name__)
            raise BankError(DISPUTE_SUBMIT_FAILED, "Chưa gửi được yêu cầu tra soát") from exc
        if not res or not res.dispute_code:  # DEC-006: không báo "đã gửi" khi chưa có mã tra soát
            raise BankError(DISPUTE_SUBMIT_FAILED, "Chưa gửi được yêu cầu tra soát")

        d = Dispute(
            res.dispute_code, owner_id, tx.id, tx.account, reason_v, description,
            tuple(attachment_refs), res.due_date, created_at=self.now(),
        )
        self.repo.add(d)
        self._by_key[idem_key] = d
        audit.info(
            "dispute_submit who=%s at=%s tx=%s acct=%s code=%s reason=%s",
            hash(owner_id), d.created_at.isoformat(), tx.id, mask(tx.account), d.code, reason_v.value,
        )
        return SubmitResult(d, reason_v == Reason.NOT_PERFORMED)

    def list_mine(self, owner_id: str) -> list[dict]:
        """REQ-004 / REQ-007: trường `result` chỉ có khi trạng thái Đã xong. EX-09: lỗi tải -> mã lỗi chuẩn."""
        try:
            items = self.repo.list_by_owner(owner_id)
        except Exception as exc:
            raise BankError(DISPUTE_LIST_LOAD_FAILED, "Không tải được danh sách yêu cầu tra soát") from exc
        out = []
        for d in sorted(items, key=lambda x: x.created_at, reverse=True):
            row = {"code": d.code, "tx_id": d.tx_id, "status": d.status.value, "due_date": d.due_date}
            if d.status == Status.DONE:
                row["result"] = d.result
            out.append(row)
        return out

    def on_status_changed(self, code: str, status: str, result: str | None = None) -> Dispute:
        """Hệ thống tiếp nhận báo đổi trạng thái -> cập nhật, rồi push (REQ-005).

        EX-08: push lỗi không làm hỏng cập nhật; khách vẫn thấy trạng thái mới ở list_mine.
        """
        try:
            status_v = Status(status)
        except ValueError:
            raise BankError(DISPUTE_INVALID_STATUS) from None
        d = self.repo.get(code)
        changed = d.status != status_v
        d.status = status_v
        d.result = result if status_v == Status.DONE else None
        audit.info("dispute_status who=intake at=%s code=%s status=%s", self.now().isoformat(), code, status_v.value)
        if changed:
            try:
                # NFR-003: push chỉ chứa mã tra soát, không có dữ liệu nhạy cảm
                self.notifier.push(d.owner_id, f"Yêu cầu tra soát {d.code} đã cập nhật trạng thái")
            except OSError as exc:  # EX-08: lỗi mạng / timeout của push -> ghi log, không làm hỏng cập nhật
                log.warning("dispute push failed code=%s err=%s", code, type(exc).__name__)
        return d
