from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# --- Standalone OpenEnv Base Classes (for Python 3.9 compatibility) ---

@dataclass
class Action:
    """Base class for all actions."""
    pass

@dataclass
class Observation:
    """Base class for all observations."""
    message: str = ""

@dataclass
class State:
    """Base class for environment state."""
    pass


# --- Loan Shark Escape Specific Models ---


class LoanActionRequest(BaseModel):
    """HTTP body for POST /step (OpenAPI-typed)."""

    action_type: str = Field(
        default="wait",
        description="One of: pay, borrow, refinance, ngo, wait",
    )
    amount: float = Field(default=0.0, ge=0.0)


@dataclass
class LoanAction(Action):
    # Action types: "pay", "borrow", "refinance", "wait", "ngo"
    action_type: str = "wait"
    amount: float = 0.0

@dataclass
class LoanObservation(Observation):
    month: int = 0
    income: float = 0.0
    total_debt: float = 0.0
    credit_score: float = 650.0
    stress_level: int = 0
    message: str = ""
    is_done: bool = False
    reward: float = 0.0
    ngo_help_used: bool = False
    credit_union_used: bool = False
    task_id: str = "lse-easy"

    # Optional metadata for debugging/UI
    available_actions: List[str] = field(default_factory=list)
    loans: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class LoanState(State):
    month: int = 0
    debt: float = 5000.0
    income: float = 2000.0
    credit_score: float = 650.0
    stress_level: int = 0
    credit_union_used: bool = False
    ngo_help_used: bool = False
    is_done: bool = False
    termination_reason: Optional[str] = None
    task_id: str = "lse-easy"
    initial_debt: float = 0.0
    fees_accrued: float = 0.0
    naive_baseline_fees: float = 0.0
    max_stress_level: int = 0
