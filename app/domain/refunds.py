"""Domain model and logic for captures and refunds.

Amounts are always integer minor units (e.g. cents) — never floats — per
the "Store refund amounts in minor units" requirement.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class RefundStatus(str, Enum):
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    EXECUTED = "executed"
    FAILED = "failed"
    REJECTED = "rejected"


# Statuses that still hold funds against the capture: not yet failed/rejected.
BALANCE_REDUCING_STATUSES = frozenset(
    {RefundStatus.PENDING_APPROVAL, RefundStatus.APPROVED, RefundStatus.EXECUTED}
)


@dataclass(frozen=True)
class Capture:
    id: str
    amount_minor: int
    currency: str
    captured_at: datetime


@dataclass(frozen=True)
class Refund:
    id: str
    capture_id: str
    amount_minor: int
    status: RefundStatus


def compute_refundable_balance(capture: Capture, refunds: list[Refund]) -> int:
    """Captured amount minus refunds that are Executed, Pending approval, or Approved.

    Failed and Rejected refunds do not reduce the balance.
    """
    reserved = sum(
        refund.amount_minor
        for refund in refunds
        if refund.capture_id == capture.id and refund.status in BALANCE_REDUCING_STATUSES
    )
    return capture.amount_minor - reserved
