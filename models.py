from typing import List, Optional
from pydantic import BaseModel, Field

class LoanDetail(BaseModel):
    """Represents a single predatory loan."""
    name: str
    balance: float
    weekly_fee: float
    apr_equivalent: float
    days_to_rollover: int = 30

class EscapeRoutes(BaseModel):
    """Available escape routes for the player."""
    credit_union_available: bool
    ngo_help_available: bool

class LoanSharkAction(BaseModel):
    """Action space for the Loan Shark Escape environment."""
    action: int = Field(..., ge=0, le=4)
    # 0 = pay loan in full, 1 = pay rollover fee, 2 = credit union, 3 = NGO help, 4 = nothing

class LoanSharkObservation(BaseModel):
    """Observation space provided to the RL agent."""
    cash_on_hand: float
    loans: List[LoanDetail]
    escape_routes: EscapeRoutes
    stress_level: int = Field(..., ge=0, le=10)
    months_remaining: int
    total_fees_paid: float
    spiral_lock: bool
    instruction: str
    baseline_fees: float = 0.0

class LoanSharkState(BaseModel):
    """Server-side state tracking for the simulation."""
    task_id: str
    current_month: int
    cash: float
    loans: List[LoanDetail]
    escape_routes: EscapeRoutes
    stress_level: int
    total_fees_paid: float
    baseline_fees: float = 0.0
    spiral_lock_triggered: bool
    all_loans_cleared: bool
    months_remaining: int
    last_action: Optional[int] = None
    last_reward: Optional[float] = None
    episode_done: bool = False
