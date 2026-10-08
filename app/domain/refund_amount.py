"""Refund amount validation (task-5Z7-t4D75L0).

Amounts are always integer minor units (e.g. cents) — never floats.
"""

from __future__ import annotations

from enum import Enum
from typing import Iterable, Mapping


class RefundStatus(str, Enum):
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    EXECUTED = "executed"
    FAILED = "failed"
    REJECTED = "rejected"


# Refunds in these statuses still hold funds against the capture; failed and
# rejected refunds release their amount back to the refundable balance.
BALANCE_RESERVING_STATUSES = frozenset(
    {RefundStatus.PENDING_APPROVAL, RefundStatus.APPROVED, RefundStatus.EXECUTED}
)


class RefundAmountError(ValueError):
    """Raised when a requested refund amount fails validation."""


def compute_refundable_balance(
    capture_amount_minor: int, existing_refunds: Iterable[Mapping[str, object]]
) -> int:
    """Return the capture's refundable balance.

    `existing_refunds` are the refunds already raised against this capture,
    each with an "amount_minor" and a "status". Only amounts of refunds in a
    balance-reserving status (pending approval, approved, executed) are
    subtracted from the capture amount.
    """
    reserved = sum(
        refund["amount_minor"]
        for refund in existing_refunds
        if refund["status"] in BALANCE_RESERVING_STATUSES
    )
    return capture_amount_minor - reserved


def validate_refund_amount(
    amount_minor: int,
    capture_amount_minor: int,
    existing_refunds: Iterable[Mapping[str, object]] = (),
) -> int:
    """Validate a requested refund amount against the capture's refundable balance.

    Raises RefundAmountError if the amount is not greater than zero, or if it
    exceeds the refundable balance. Returns the refundable balance that was
    validated against.
    """
    if amount_minor <= 0:
        raise RefundAmountError("Refund amount must be greater than zero")

    balance = compute_refundable_balance(capture_amount_minor, existing_refunds)

    if amount_minor > balance:
        raise RefundAmountError(
            f"Refund amount {amount_minor} exceeds refundable balance {balance}"
        )

    return balance
