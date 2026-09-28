# Refund Workflow

A Python/FastAPI service for managing payment refunds with comprehensive validation and audit trails.

## Task: Validate Refund Amount (task-5Z7-t4D75L0)

This module implements validation for refund amounts to ensure:
- Amount is greater than zero
- Amount does not exceed the capture's refundable balance
- Refundable balance correctly accounts for executed and pending refunds

## Features

- **Refund Amount Validation**: Validates refund amounts against capture balance
- **Refundable Balance Calculation**: Accurately calculates remaining refundable balance by subtracting executed/pending refunds from original capture amount
- **Comprehensive Testing**: Full test suite covering all acceptance criteria

## Acceptance Criteria (All Passing ✓)

1. **Request for 30 on 100 capture is accepted** ✓
2. **Request for 0 is rejected** ✓
3. **Request exceeding balance is rejected** ✓
4. **Partial refund reduces refundable balance correctly** ✓

## Project Structure

```
.
├── app/
│   ├── __init__.py
│   ├── models.py          # Data models for Refund, Capture, RefundStatus
│   └── validation.py      # Core validation logic
├── tests/
│   ├── __init__.py
│   └── test_validation.py # Comprehensive test suite
├── pyproject.toml         # Project configuration and dependencies
├── README.md              # This file
└── .gitignore             # Git ignore rules
```

## Installation

### Requirements
- Python 3.11+
- pip

### Setup

```bash
# Clone the repository
git clone <repository-url>
cd refund-workflow

# Install in development mode with dev dependencies
pip install -e ".[dev]"
```

## Testing

Run all tests:

```bash
pytest tests/
```

Run with coverage:

```bash
pytest tests/ --cov=app
```

Run specific test:

```bash
pytest tests/test_validation.py::TestRefundAmountValidation::test_request_for_30_on_100_capture_accepted -v
```

## Implementation Details

### Validation Logic

The validation module provides two main functions:

#### `validate_refund_amount(refund_amount, capture_amount, executed_and_pending_refunds)`

Validates a refund request against business rules:
- Checks amount > 0
- Checks amount ≤ refundable balance
- Raises `RefundValidationError` if validation fails

#### `calculate_refundable_balance(capture_amount, executed_and_pending_refunds)`

Calculates the refundable balance:
- Takes original capture amount
- Subtracts amounts from refunds with status "Executed" or "Pending approval"
- Returns remaining refundable balance

**Important**: Only refunds with `EXECUTED` or `PENDING_APPROVAL` status reduce the refundable balance. Rejected and Failed refunds do not affect the balance.

## Data Models

### RefundStatus Enum
- `PENDING_APPROVAL` - Awaiting finance approval
- `APPROVED` - Finance has approved, ready for execution
- `EXECUTED` - Successfully executed at acquirer
- `FAILED` - Execution failed at acquirer
- `REJECTED` - Manually rejected by finance

### ReasonCode Enum
- `customer_request` - Customer requested refund
- `duplicate` - Duplicate charge
- `fraud` - Fraudulent transaction
- `goods_not_received` - Customer didn't receive goods
- `other` - Other reason (requires free-text note)

## Running Tests

All acceptance criteria are verified through automated tests:

```bash
$ pytest tests/test_validation.py -v

tests/test_validation.py::TestRefundAmountValidation::test_request_for_30_on_100_capture_accepted PASSED
tests/test_validation.py::TestRefundAmountValidation::test_request_for_0_rejected PASSED
tests/test_validation.py::TestRefundAmountValidation::test_request_exceeding_balance_rejected PASSED
tests/test_validation.py::TestRefundAmountValidation::test_partial_refund_reduces_refundable_balance_correctly PASSED
...
```

## Development

### Code Style

Code follows PEP 8 and is formatted with Black:

```bash
black app/ tests/
ruff check app/ tests/
```

### Adding Tests

Add new tests to `tests/test_validation.py` following the existing pattern:

```python
def test_your_scenario(self):
    """Your acceptance criterion here"""
    # Arrange
    capture_amount = 100
    refund_amount = 30
    
    # Act & Assert
    validate_refund_amount(refund_amount, capture_amount)
```

## Task Specification

This implementation satisfies specification task `task-5Z7-t4D75L0` from the Refund Workflow-Rooster project.

**Epic**: Refund Request Creation  
**Story**: Support agent raises refund request  
**Spec**: Refund request validation

See `/workspace/openspec/specs/refund-request-creation/spec.md` for full specification details.

## License

Internal use only.
