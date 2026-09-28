import pytest
from datetime import datetime
from app.models import Refund, RefundStatus, ReasonCode
from app.validation import (
    validate_refund_amount,
    calculate_refundable_balance,
    RefundValidationError,
)


class TestRefundAmountValidation:
    """Test suite for refund amount validation (task-5Z7-t4D75L0)"""

    def test_request_for_30_on_100_capture_accepted(self):
        """Acceptance Criterion: Request for 30 on 100 capture is accepted"""
        capture_amount = 100
        refund_amount = 30

        # Should not raise an exception
        validate_refund_amount(refund_amount, capture_amount)

    def test_request_for_0_rejected(self):
        """Acceptance Criterion: Request for 0 is rejected"""
        capture_amount = 100
        refund_amount = 0

        with pytest.raises(RefundValidationError) as exc_info:
            validate_refund_amount(refund_amount, capture_amount)

        assert "greater than zero" in str(exc_info.value)

    def test_request_for_negative_amount_rejected(self):
        """Request for negative amount should be rejected"""
        capture_amount = 100
        refund_amount = -10

        with pytest.raises(RefundValidationError) as exc_info:
            validate_refund_amount(refund_amount, capture_amount)

        assert "greater than zero" in str(exc_info.value)

    def test_request_exceeding_balance_rejected(self):
        """Acceptance Criterion: Request exceeding balance is rejected"""
        capture_amount = 100
        refund_amount = 101

        with pytest.raises(RefundValidationError) as exc_info:
            validate_refund_amount(refund_amount, capture_amount)

        assert "exceeds refundable balance" in str(exc_info.value)

    def test_partial_refund_reduces_refundable_balance_correctly(self):
        """
        Acceptance Criterion: Partial refund reduces refundable balance correctly.
        When 30 refund is executed on 100 capture, refundable balance becomes 70;
        subsequent 80 request is rejected.
        """
        capture_amount = 100

        # Scenario 1: First refund of 30 should be accepted
        validate_refund_amount(30, capture_amount)

        # Scenario 2: After a 30 refund is executed, the refundable balance is 70
        executed_refund = Refund(
            refund_id="ref-1",
            capture_id="cap-1",
            amount=30,
            currency="USD",
            status=RefundStatus.EXECUTED,
            reason_code=ReasonCode.CUSTOMER_REQUEST,
            created_by="agent-1",
            created_at=datetime.now(),
        )

        refundable_balance = calculate_refundable_balance(
            capture_amount, [executed_refund]
        )
        assert refundable_balance == 70

        # Scenario 3: A request for 80 should be rejected (exceeds new balance)
        with pytest.raises(RefundValidationError) as exc_info:
            validate_refund_amount(80, capture_amount, [executed_refund])

        assert "exceeds refundable balance" in str(exc_info.value)

    def test_pending_approval_refund_reduces_balance(self):
        """Pending approval refunds also reduce the refundable balance"""
        capture_amount = 100

        pending_refund = Refund(
            refund_id="ref-1",
            capture_id="cap-1",
            amount=30,
            currency="USD",
            status=RefundStatus.PENDING_APPROVAL,
            reason_code=ReasonCode.CUSTOMER_REQUEST,
            created_by="agent-1",
            created_at=datetime.now(),
        )

        # Balance should be 70 (100 - 30)
        refundable_balance = calculate_refundable_balance(
            capture_amount, [pending_refund]
        )
        assert refundable_balance == 70

        # Request for 80 should be rejected
        with pytest.raises(RefundValidationError):
            validate_refund_amount(80, capture_amount, [pending_refund])

    def test_rejected_and_failed_refunds_do_not_reduce_balance(self):
        """Rejected and Failed refunds should not reduce the refundable balance"""
        capture_amount = 100

        rejected_refund = Refund(
            refund_id="ref-1",
            capture_id="cap-1",
            amount=30,
            currency="USD",
            status=RefundStatus.REJECTED,
            reason_code=ReasonCode.CUSTOMER_REQUEST,
            created_by="agent-1",
            created_at=datetime.now(),
        )

        failed_refund = Refund(
            refund_id="ref-2",
            capture_id="cap-1",
            amount=20,
            currency="USD",
            status=RefundStatus.FAILED,
            reason_code=ReasonCode.DUPLICATE,
            created_by="agent-1",
            created_at=datetime.now(),
        )

        # Balance should remain 100
        refundable_balance = calculate_refundable_balance(
            capture_amount, [rejected_refund, failed_refund]
        )
        assert refundable_balance == 100

        # Should be able to request 100
        validate_refund_amount(100, capture_amount, [rejected_refund, failed_refund])

    def test_multiple_executed_refunds_reduce_balance_correctly(self):
        """Multiple executed refunds should correctly accumulate and reduce balance"""
        capture_amount = 100

        refund1 = Refund(
            refund_id="ref-1",
            capture_id="cap-1",
            amount=30,
            currency="USD",
            status=RefundStatus.EXECUTED,
            reason_code=ReasonCode.CUSTOMER_REQUEST,
            created_by="agent-1",
            created_at=datetime.now(),
        )

        refund2 = Refund(
            refund_id="ref-2",
            capture_id="cap-1",
            amount=20,
            currency="USD",
            status=RefundStatus.EXECUTED,
            reason_code=ReasonCode.DUPLICATE,
            created_by="agent-1",
            created_at=datetime.now(),
        )

        # Balance should be 50 (100 - 30 - 20)
        refundable_balance = calculate_refundable_balance(
            capture_amount, [refund1, refund2]
        )
        assert refundable_balance == 50

        # Request for 50 should be accepted
        validate_refund_amount(50, capture_amount, [refund1, refund2])

        # Request for 51 should be rejected
        with pytest.raises(RefundValidationError):
            validate_refund_amount(51, capture_amount, [refund1, refund2])

    def test_request_equal_to_refundable_balance_accepted(self):
        """A request for exactly the refundable balance should be accepted"""
        capture_amount = 100
        refund_amount = 100

        validate_refund_amount(refund_amount, capture_amount)

    def test_request_equal_to_remaining_balance_after_executed_refund(self):
        """A request for exactly the remaining balance should be accepted"""
        capture_amount = 100

        executed_refund = Refund(
            refund_id="ref-1",
            capture_id="cap-1",
            amount=50,
            currency="USD",
            status=RefundStatus.EXECUTED,
            reason_code=ReasonCode.CUSTOMER_REQUEST,
            created_by="agent-1",
            created_at=datetime.now(),
        )

        # Should accept request for exactly 50 (remaining balance)
        validate_refund_amount(50, capture_amount, [executed_refund])
