from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class LoanSharkAction(BaseModel):
    action: int

class Loan(BaseModel):
    id: str
    balance: float
    weekly_rate: float
    min_payment: float

class LoanSharkObservation(BaseModel):
    total_cash: float
    budget: float
    expenses: float
    disposable_cash: float
    loans: List[Loan]
    stress_level: int
    spiral_lock: bool
    months_passed: int
    total_interest_paid: float

class LoanSharkState(BaseModel):
    observation: LoanSharkObservation
    reward: float
    done: bool
    info: Dict[str, Any]
