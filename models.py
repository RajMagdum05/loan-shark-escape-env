from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class LoanSharkAction(BaseModel):
    action: int = Field(ge=0, le=4, description="Action id between 0 and 4")


class LoanEntry(BaseModel):
    name: str
    balance: float
    weekly_fee: float
    days_to_rollover: int = 7


class EscapeRoutes(BaseModel):
    credit_union_available: bool
    ngo_help_available: bool


class LoanSharkObservation(BaseModel):
    cash_on_hand: float
    loans: list[LoanEntry]
    escape_routes: EscapeRoutes
    stress_level: int = Field(ge=0, le=10)
    months_remaining: int
    total_fees_paid: float
    spiral_lock: bool
    instruction: str


class LoanSharkState(BaseModel):
    task_id: str
    month: int
    horizon_months: int
    cash_on_hand: float
    monthly_income: float
    fixed_expenses: float
    loans: list[dict[str, Any]]
    stress_level: int = Field(ge=0, le=10)
    total_fees_paid: float
    baseline_fees: float
    spiral_lock: bool
    done: bool
    all_loans_cleared: bool
