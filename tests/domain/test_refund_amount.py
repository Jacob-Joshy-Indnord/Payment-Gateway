"""Tests for task-5Z7-t4D75L0: Validate refund amount.

Covers the acceptance criteria: amount must be greater than zero and must not
exceed the capture's refundable balance (captured amount minus refunds that
are executed, approved, or pending approval).
"""

import pytest

from app.domain.refund_amount import (
    RefundAmountError,
    RefundStatus,
    compute_refundable_balance,
    validate_refund_amount,
)


def _refund(amount_minor: int, status: RefundStatus):
    return {"amount_minor": amount_minor, "status": status}


# AC: Request for 30 on 100 capture is accepted
def test_request_within_balance_is_accepted():
    validate_refund_amount(amount_minor=30_00, capture_amount_minor=100_00)


# AC: Request for 0 is rejected
def test_zero_amount_is_rejected():
    with pytest.raises(RefundAmountError, match="greater than zero"):
        validate_refund_amount(amount_minor=0, capture_amount_minor=100_00)


def test_negative_amount_is_rejected():
    with pytest.raises(RefundAmountError, match="greater than zero"):
        validate_refund_amount(amount_minor=-10_00, capture_amount_minor=100_00)


# AC: Request exceeding balance is rejected
def test_amount_exceeding_balance_is_rejected():
    with pytest.raises(RefundAmountError, match="exceeds"):
        validate_refund_amount(amount_minor=150_00, capture_amount_minor=100_00)


def test_amount_equal_to_balance_is_accepted():
    validate_refund_amount(amount_minor=100_00, capture_amount_minor=100_00)


# AC: Partial refund reduces refundable balance correctly
def test_executed_refund_reduces_balance_and_blocks_over_requests():
    existing = [_refund(30_00, RefundStatus.EXECUTED)]

    balance = compute_refundable_balance(100_00, existing)
    assert balance == 70_00

    with pytest.raises(RefundAmountError, match="exceeds"):
        validate_refund_amount(80_00, 100_00, existing)

    # still within the reduced balance
    validate_refund_amount(70_00, 100_00, existing)


def test_pending_approval_refund_also_reduces_balance():
    existing = [_refund(20_00, RefundStatus.PENDING_APPROVAL)]
    assert compute_refundable_balance(100_00, existing) == 80_00


def test_approved_refund_also_reduces_balance():
    existing = [_refund(20_00, RefundStatus.APPROVED)]
    assert compute_refundable_balance(100_00, existing) == 80_00


def test_failed_and_rejected_refunds_do_not_reduce_balance():
    existing = [
        _refund(30_00, RefundStatus.FAILED),
        _refund(20_00, RefundStatus.REJECTED),
    ]
    assert compute_refundable_balance(100_00, existing) == 100_00
    validate_refund_amount(100_00, 100_00, existing)


def test_multiple_reserving_refunds_accumulate():
    existing = [
        _refund(30_00, RefundStatus.EXECUTED),
        _refund(10_00, RefundStatus.PENDING_APPROVAL),
        _refund(5_00, RefundStatus.APPROVED),
    ]
    assert compute_refundable_balance(100_00, existing) == 55_00
