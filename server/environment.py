import random
from typing import Dict, Any, Union

from models import LoanAction, LoanObservation, LoanState, State


# --- Standalone Environment Base Class ---

class Environment:
    """Base class for environment logic."""
    def __init__(self):
        self._state = None

    def reset(self, config: Dict[str, Any] = None) -> LoanObservation:
        raise NotImplementedError

    def step(self, action: LoanAction) -> LoanObservation:
        raise NotImplementedError

    def get_state(self) -> State:
        return self._state


# --- Loan Shark Environment Implementation ---

class LoanSharkEnvironment(Environment):
    def __init__(self):
        super().__init__()
        self._state = LoanState()
        self.last_grader_result = {}

    def reset(self, task_id: str = "lse-easy") -> LoanObservation:
        # Defaults
        initial_debt = 5000.0
        income = 2000.0
        credit_score = 650.0

        # Mapping task IDs to specific configurations (from email requirements)
        if task_id == "lse-easy":
            initial_debt = 3000.0
            income = 2500.0
            credit_score = 700.0
        elif task_id == "lse-medium":
            initial_debt = 5000.0
            income = 2000.0
            credit_score = 650.0
        elif task_id == "lse-hard":
            initial_debt = 8000.0
            income = 1500.0
            credit_score = 600.0

        self._state = LoanState(
            month=0,
            debt=initial_debt,
            income=income,
            credit_score=credit_score,
            stress_level=0,
            credit_union_used=False,
            ngo_help_used=False,
            is_done=False
        )

        return self._make_observation("Game started: Escape the predatory debt trap.")

    def step(self, action: LoanAction) -> LoanObservation:
        s = self._state
        if s.is_done:
            return self._make_observation("Environment already terminated.")

        s.month += 1
        msg = "Step executed."

        # 💰 ACTION LOGIC
        # actions: "pay", "borrow", "refinance", "ngo", "wait"
        atype = action.action_type.lower()

        if atype == "pay":
            # Pay exactly what's owed or everything possible
            payment = min(s.debt, s.income * 0.8) # Cap payment at 80% income for survival
            s.debt -= payment
            s.credit_score += 5
            s.stress_level = max(0, s.stress_level - 1)
        
        elif atype == "borrow":
            # Taking more debt increases stress and drops credit
            s.debt += 1000
            s.credit_score -= 30
            s.stress_level += 2
            msg = "Borrowed more. Stress up, score down."

        elif atype == "refinance":
            if not s.credit_union_used and s.credit_score > 620:
                s.credit_score += 15
                # Lower future interest logic would go here, 
                # for now we simulate a one-time relief
                s.debt *= 0.9 
                s.credit_union_used = True
                msg = "Refinanced via Credit Union! Debt reduced by 10%."
            else:
                msg = "Refinance failed (already used or score too low)."
        
        elif atype == "ngo":
            if not s.ngo_help_used:
                s.debt *= 0.65 # Grants wipe 35% of principal
                s.ngo_help_used = True
                s.stress_level = max(0, s.stress_level - 3)
                msg = "NGO Grant received! 35% debt wiped."
            else:
                msg = "NGO help only available once."
        
        elif atype == "wait":
            s.stress_level += 2
            msg = "Month skipped. Stress is building..."

        # ⚡ RANDOM SHOCKS (Realism 🔥)
        if random.random() < 0.15: # 15% chance of shock
            shock = random.choice(["job_loss", "medical"])
            if shock == "job_loss":
                s.income *= 0.6
                s.stress_level += 3
                msg += " CRITICAL: Job loss! Income slashed by 40%."
            elif shock == "medical":
                s.debt += 800
                s.stress_level += 2
                msg += " EMERGENCY: Medical bill added $800 to debt."

        # 📉 INTEREST & AUTO-FEES
        if s.debt > 0:
            s.debt *= 1.05 # 5% monthly interest
            # Naive auto-deduction of minimums if not paid
            if atype != "pay":
                s.stress_level += 1

        # 🏁 TERMINATION
        if s.debt <= 0:
            s.debt = 0.0
            s.is_done = True
            s.termination_reason = "Success: Debt Cleared"
            msg = "CONGRATULATIONS! You escaped the debt trap."

        elif s.credit_score <= 300:
            s.is_done = True
            s.termination_reason = "Failure: Bankruptcy"
            msg = "BANKRUPTCY: Your credit score collapsed."

        elif s.stress_level >= 10:
            s.is_done = True
            s.termination_reason = "Failure: Spiral Lock"
            msg = "SPIRAL LOCK: Stress levels are critical. Management failed."

        elif s.month >= 24:
            s.is_done = True
            s.termination_reason = "Terminated: Time Limit"
            msg = "TIME LIMIT: 24 months passed without clearing debt."

        return self._make_observation(msg)

    def evaluate(self) -> Dict[str, Any]:
        """Official grader scoring logic."""
        s = self._state
        score = 0.2 # Baseline
        
        if s.debt <= 0:
            score = 0.95
        elif s.debt < 2000:
            score = 0.7
        elif s.credit_score > 600:
            score = 0.5
            
        self.last_grader_result = {
            "passed": 3 if s.debt <= 0 else 1,
            "total": 3,
            "score": score,
            "termination": s.termination_reason
        }
        return self.last_grader_result

    def _make_observation(self, message: str) -> LoanObservation:
        s = self._state
        return LoanObservation(
            month=s.month,
            income=round(s.income, 2),
            total_debt=round(s.debt, 2),
            credit_score=s.credit_score,
            stress_level=s.stress_level,
            message=message,
            available_actions=["pay", "borrow", "refinance", "ngo", "wait"]
        )
