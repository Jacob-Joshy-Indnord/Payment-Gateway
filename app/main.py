from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from app.models import Refund, RefundStatus, ReasonCode
from app.validation import validate_refund_amount, RefundValidationError

app = FastAPI(
    title="Refund Workflow API",
    description="API for managing payment refunds with validation",
    version="0.1.0",
)


# Request/Response Models
class CreateRefundRequest(BaseModel):
    amount: int
    currency: str
    reason_code: ReasonCode
    reason_note: Optional[str] = None


class CreateRefundResponse(BaseModel):
    refund_id: str
    capture_id: str
    status: RefundStatus
    amount: int


class ValidationErrorResponse(BaseModel):
    error: str
    detail: str


# Mock database
captures = {
    "cap-1": {"amount": 100, "currency": "USD", "created_at": datetime.now()},
    "cap-2": {"amount": 500, "currency": "EUR", "created_at": datetime.now()},
}

refunds_db = {}


@app.post(
    "/captures/{capture_id}/refunds",
    response_model=CreateRefundResponse,
    status_code=201,
    responses={400: {"model": ValidationErrorResponse}},
)
def create_refund(
    capture_id: str, request: CreateRefundRequest
) -> CreateRefundResponse:
    """
    Create a new refund request against a capture.

    Validates that:
    - Capture exists
    - Amount is positive
    - Amount doesn't exceed refundable balance
    - Currency matches capture currency

    Returns the refund with its initial status (auto-approved if below threshold).
    """
    # Verify capture exists
    if capture_id not in captures:
        raise HTTPException(status_code=400, detail="Capture not found")

    capture = captures[capture_id]

    # Verify currency matches
    if request.currency != capture["currency"]:
        raise HTTPException(status_code=400, detail="Currency mismatch")

    # Get existing refunds for this capture
    existing_refunds = [
        r for r in refunds_db.values() if r.capture_id == capture_id
    ]

    # Validate refund amount
    try:
        validate_refund_amount(
            request.amount, capture["amount"], existing_refunds
        )
    except RefundValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Create refund
    refund_id = f"ref-{len(refunds_db) + 1}"

    # Auto-approve if below threshold (50.00 in minor units = 5000)
    status = (
        RefundStatus.APPROVED
        if request.amount <= 5000
        else RefundStatus.PENDING_APPROVAL
    )

    refund = Refund(
        refund_id=refund_id,
        capture_id=capture_id,
        amount=request.amount,
        currency=request.currency,
        status=status,
        reason_code=request.reason_code,
        reason_note=request.reason_note,
        created_by="api",
        created_at=datetime.now(),
    )

    refunds_db[refund_id] = refund

    return CreateRefundResponse(
        refund_id=refund_id,
        capture_id=capture_id,
        status=status,
        amount=request.amount,
    )


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
