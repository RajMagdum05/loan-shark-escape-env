from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


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
