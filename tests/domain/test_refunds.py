from datetime import datetime, timezone

import pytest

from app.domain.refunds import Capture, Refund, RefundStatus, compute_refundable_balance

CAPTURE = Capture(
    id="cap-1",
    amount_minor=10_000,  # 100.00
    currency="USD",
    captured_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
)


def _refund(amount_minor: int, status: RefundStatus, capture_id: str = "cap-1", ref: str = "r1") -> Refund:
    return Refund(id=ref, capture_id=capture_id, amount_minor=amount_minor, status=status)


def test_executed_and_pending_refunds_both_reduce_balance():
    # AC: 100.00 capture, 30.00 executed refund, 10.00 pending refund -> 60.00 balance
    refunds = [
        _refund(3_000, RefundStatus.EXECUTED, ref="r1"),
        _refund(1_000, RefundStatus.PENDING_APPROVAL, ref="r2"),
    ]

    balance = compute_refundable_balance(CAPTURE, refunds)

    assert balance == 6_000


def test_approved_refund_reduces_balance():
    refunds = [_refund(2_000, RefundStatus.APPROVED)]

    assert compute_refundable_balance(CAPTURE, refunds) == 8_000


def test_failed_refund_does_not_reduce_balance():
    refunds = [_refund(2_000, RefundStatus.FAILED)]

    assert compute_refundable_balance(CAPTURE, refunds) == 10_000


def test_rejected_refund_does_not_reduce_balance():
    refunds = [_refund(2_000, RefundStatus.REJECTED)]

    assert compute_refundable_balance(CAPTURE, refunds) == 10_000


def test_no_refunds_leaves_full_balance():
    assert compute_refundable_balance(CAPTURE, []) == 10_000


def test_mixed_statuses_only_reserving_ones_reduce_balance():
    refunds = [
        _refund(3_000, RefundStatus.EXECUTED, ref="r1"),
        _refund(1_000, RefundStatus.PENDING_APPROVAL, ref="r2"),
        _refund(1_500, RefundStatus.APPROVED, ref="r3"),
        _refund(2_000, RefundStatus.FAILED, ref="r4"),
        _refund(500, RefundStatus.REJECTED, ref="r5"),
    ]

    # 10000 - (3000 + 1000 + 1500) = 4500; failed/rejected ignored
    assert compute_refundable_balance(CAPTURE, refunds) == 4_500


def test_refunds_for_other_captures_are_ignored():
    refunds = [_refund(5_000, RefundStatus.EXECUTED, capture_id="cap-other")]

    assert compute_refundable_balance(CAPTURE, refunds) == 10_000


@pytest.mark.parametrize("amount", [3_000, 1_000])
def test_amounts_are_plain_ints_no_float_arithmetic(amount):
    refund = _refund(amount, RefundStatus.EXECUTED)

    assert isinstance(refund.amount_minor, int)
    balance = compute_refundable_balance(CAPTURE, [refund])
    assert isinstance(balance, int)
