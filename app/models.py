from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class RefundStatus(str, Enum):
    PENDING_APPROVAL = "Pending approval"
    APPROVED = "Approved"
    EXECUTED = "Executed"
    FAILED = "Failed"
    REJECTED = "Rejected"


class ReasonCode(str, Enum):
    CUSTOMER_REQUEST = "customer_request"
    DUPLICATE = "duplicate"
    FRAUD = "fraud"
    GOODS_NOT_RECEIVED = "goods_not_received"
    OTHER = "other"


class Capture(BaseModel):
    capture_id: str
    amount: int
    currency: str
    created_at: datetime


class Refund(BaseModel):
    refund_id: str
    capture_id: str
    amount: int
    currency: str
    status: RefundStatus
    reason_code: ReasonCode
    reason_note: Optional[str] = None
    created_by: str
    created_at: datetime
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    approval_note: Optional[str] = None
    executed_at: Optional[datetime] = None
    acquirer_ref: Optional[str] = None
    retry_count: int = 0


class RefundValidationError(Exception):
    """Exception raised when refund validation fails."""
    pass
