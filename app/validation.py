from typing import List
from app.models import Refund, RefundValidationError, RefundStatus


def calculate_refundable_balance(
    capture_amount: int, executed_and_pending_refunds: List[Refund]
) -> int:
    """
    Calculate the refundable balance for a capture.

    Args:
        capture_amount: Original capture amount in minor units
        executed_and_pending_refunds: List of refunds

    Returns:
        Refundable balance in minor units (only counts Executed or Pending approval refunds)
    """
    # Only count refunds with Executed or Pending approval status
    active_refunds = [
        refund
        for refund in executed_and_pending_refunds
        if refund.status in (RefundStatus.EXECUTED, RefundStatus.PENDING_APPROVAL)
    ]
    total_refunded = sum(refund.amount for refund in active_refunds)
    return capture_amount - total_refunded


def validate_refund_amount(
    refund_amount: int,
    capture_amount: int,
    executed_and_pending_refunds: List[Refund] = None,
) -> None:
    """
    Validate that refund amount is valid.

    Args:
        refund_amount: Requested refund amount in minor units
        capture_amount: Original capture amount in minor units
        executed_and_pending_refunds: List of refunds with Executed or Pending approval status

    Raises:
        RefundValidationError: If validation fails
    """
    if executed_and_pending_refunds is None:
        executed_and_pending_refunds = []

    # Check amount is greater than zero
    if refund_amount <= 0:
        raise RefundValidationError("Refund amount must be greater than zero")

    # Calculate refundable balance
    refundable_balance = calculate_refundable_balance(
        capture_amount, executed_and_pending_refunds
    )

    # Check amount does not exceed refundable balance
    if refund_amount > refundable_balance:
        raise RefundValidationError(
            f"Refund amount {refund_amount} exceeds refundable balance {refundable_balance}"
        )
