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
        # Use a seeded RNG for reproducible episodes
        self._rng = random.Random(42)

    def reset(self, task_id: str = "lse-easy") -> LoanObservation:
        # Re-seed for reproducibility across evaluation runs
        self._rng = random.Random(hash(task_id) % 2**32)

        # Defaults
        initial_debt = 5000.0
        income = 2000.0
        credit_score = 650.0
        naive_baseline_fees = 4000.0

        # Mapping task IDs to specific configurations
        if task_id == "lse-easy":
            initial_debt = 3000.0
            income = 2500.0
            credit_score = 700.0
            naive_baseline_fees = 2200.0
        elif task_id == "lse-medium":
            initial_debt = 5000.0
            income = 2000.0
            credit_score = 650.0
            naive_baseline_fees = 3800.0
        elif task_id == "lse-hard":
            initial_debt = 8000.0
            income = 1500.0
            credit_score = 600.0
            naive_baseline_fees = 6200.0

        self._state = LoanState(
            month=0,
            debt=initial_debt,
            income=income,
            credit_score=credit_score,
            stress_level=0,
            credit_union_used=False,
            ngo_help_used=False,
            is_done=False,
            task_id=task_id,
            initial_debt=initial_debt,
            fees_accrued=0.0,
            naive_baseline_fees=naive_baseline_fees,
            max_stress_level=0,
        )

        return self._make_observation("Game started: Escape the predatory debt trap.")

    def step(self, action: LoanAction) -> LoanObservation:
        s = self._state
        if s.is_done:
            return self._make_observation("Environment already terminated.")

        s.month += 1
        msg = "Step executed."

        # 💰 ACTION LOGIC
        atype = action.action_type.lower()

        if atype == "pay":
            # Pay exactly what's owed or everything possible
            payment = min(s.debt, s.income * 0.8)  # Cap payment at 80% income
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
            if s.task_id == "lse-hard":
                msg = "Refinance unavailable in this scenario (no credit union access)."
            elif not s.credit_union_used and s.credit_score > 620:
                s.credit_score += 15
                s.debt *= 0.9
                s.credit_union_used = True
                msg = "Refinanced via Credit Union! Debt reduced by 10%."
            else:
                msg = "Refinance failed (already used or score too low)."

        elif atype == "ngo":
            if not s.ngo_help_used:
                s.debt *= 0.65  # Grants wipe 35% of principal
                s.ngo_help_used = True
                s.stress_level = max(0, s.stress_level - 3)
                msg = "NGO Grant received! 35% debt wiped."
            else:
                msg = "NGO help only available once."

        elif atype == "wait":
            s.stress_level += 2
            msg = "Month skipped. Stress is building..."

        # ⚡ DETERMINISTIC SHOCKS (seeded RNG for reproducibility)
        shock_roll = self._rng.random()
        if shock_roll < 0.10:  # 10% chance, but deterministic per task
            shock_type = self._rng.choice(["job_loss", "medical"])
            if shock_type == "job_loss":
                s.income *= 0.75  # Reduced from 0.6 to be more fair
                s.stress_level += 2
                msg += " WARNING: Temporary income reduction."
            elif shock_type == "medical":
                s.debt += 500  # Reduced from 800
                s.stress_level += 1
                msg += " EMERGENCY: Medical bill added $500 to debt."

        # 📉 INTEREST & AUTO-FEES
        if s.debt > 0:
            interest = s.debt * 0.05
            s.fees_accrued += interest
            s.debt *= 1.05  # 5% monthly interest
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

        s.max_stress_level = max(s.max_stress_level, s.stress_level)
        return self._make_observation(msg)

    def evaluate(self) -> Dict[str, Any]:
        """Aggregate metrics for hackathon graders (also exposed via /evaluate)."""
        s = self._state
        from grader import score_episode

        metrics = {
            "task_id": s.task_id,
            "debt": round(s.debt, 2),
            "initial_debt": s.initial_debt,
            "fees_accrued": round(s.fees_accrued, 2),
            "naive_baseline_fees": s.naive_baseline_fees,
            "max_stress_level": s.max_stress_level,
            "credit_score": s.credit_score,
            "month": s.month,
            "is_done": s.is_done,
            "termination_reason": s.termination_reason,
        }
        score = score_episode(s.task_id, metrics)
        # Ensure score is strictly in (0, 1) — never 0.0 or 1.0
        score = max(0.01, min(0.99, score))
        self.last_grader_result = {
            "task_id": s.task_id,
            "passed": 3 if s.debt <= 0 and s.max_stress_level < 10 else 1,
            "total": 3,
            "score": round(score, 4),
            "reward": round(score, 4),
            "metrics": metrics,
            "termination": s.termination_reason,
        }
        return self.last_grader_result

    def _partial_reward(self) -> float:
        s = self._state
        if s.debt <= 0:
            return 0.99
        if s.initial_debt <= 0:
            return 0.01
        debt_ratio = min(1.0, max(0.0, s.debt / s.initial_debt))
        stress_ratio = min(1.0, s.stress_level / 10.0)
        raw = 0.45 * (1.0 - debt_ratio) + 0.35 * (1.0 - stress_ratio)
        return max(0.01, min(0.99, raw))

    def _make_observation(self, message: str) -> LoanObservation:
        s = self._state
        actions = ["pay", "borrow", "ngo", "wait"]
        if s.task_id != "lse-hard":
            actions.insert(2, "refinance")
        return LoanObservation(
            month=s.month,
            income=round(s.income, 2),
            total_debt=round(s.debt, 2),
            credit_score=s.credit_score,
            stress_level=s.stress_level,
            message=message,
            is_done=s.is_done,
            reward=round(self._partial_reward() if not s.is_done else
                         (0.99 if s.debt <= 0 else 0.05), 4),
            ngo_help_used=s.ngo_help_used,
            credit_union_used=s.credit_union_used,
            task_id=s.task_id,
            available_actions=actions,
        )
