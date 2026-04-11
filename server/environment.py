from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from grader import run_grader


class LoanSharkEnvironment:
    def __init__(self, tasks_dir: str | Path = "tasks") -> None:
        self.tasks_dir = Path(tasks_dir)
        self.tasks_dir.mkdir(parents=True, exist_ok=True)

        self.current_task: dict[str, Any] | None = None
        self.state: dict[str, Any] | None = None
        self.done: bool = False
        self.baseline_fees: float = 0.0
        self.last_grader_result: dict[str, Any] | None = None

    def reset(self, task_id: str) -> dict[str, Any]:
        task_path = self.tasks_dir / f"{task_id}.json"
        if not task_path.exists():
            raise FileNotFoundError(f"Task config not found: {task_path}")

        task = json.loads(task_path.read_text())
        self.current_task = task
        self.done = False

        loans = []
        for raw_loan in task.get("loans", []):
            loans.append(
                {
                    "name": raw_loan["name"],
                    "balance": float(raw_loan["balance"]),
                    "weekly_fee": float(raw_loan["weekly_fee"]),
                    "apr_equivalent": float(raw_loan.get("apr_equivalent", 2.6)),
                    "days_to_rollover": 7,
                    "is_refinanced": False,
                }
            )

        self.state = {
            "task_id": task["task_id"],
            "month": 0,
            "horizon_months": int(task["horizon_months"]),
            "cash_on_hand": 0.0,
            "monthly_income": float(task["monthly_income"]),
            "fixed_expenses": float(task["fixed_expenses"]),
            "loans": loans,
            "stress_level": 0,
            "total_fees_paid": 0.0,
            "spiral_lock": False,
            "all_loans_cleared": False,
            "done": False,
            "credit_union_used": False,
            "ngo_uses": 0,
            "escape_routes": copy.deepcopy(task.get("escape_routes", {})),
        }

        # Baseline must be precomputed at reset so gameplay is measured against a fixed target.
        self.baseline_fees = self._compute_baseline(task)
        return self._observation()

    def step(self, action: int) -> dict[str, Any]:
        if self.state is None:
            raise RuntimeError("Call reset(task_id) before step().")

        if self.done:
            return {
                "observation": self._observation(),
                "reward": 0.0,
                "done": True,
                "info": {"message": "Episode already finished."},
            }

        if action < 0 or action > 4:
            raise ValueError("Action must be in range 0..4")

        state = self.state
        state["month"] += 1
        month = state["month"]

        # Monthly cashflow update first: income, expenses, then optional shock.
        state["cash_on_hand"] += state["monthly_income"]
        state["cash_on_hand"] -= state["fixed_expenses"]
        state["cash_on_hand"] += self._income_shock(month)

        active_loans = [loan for loan in state["loans"] if loan["balance"] > 0]
        paid_minimum: dict[str, bool] = {loan["name"]: False for loan in active_loans}

        if action == 0:
            self._apply_action_pay_full(active_loans, paid_minimum)
        elif action == 1:
            self._apply_action_minimum(active_loans, paid_minimum)
        elif action == 2:
            self._apply_action_credit_union(active_loans, paid_minimum)
        elif action == 3:
            self._apply_action_ngo(active_loans, paid_minimum, month)
        elif action == 4:
            pass

        # Missing minimum payment adds stress +2 per unpaid active loan.
        for loan in active_loans:
            if loan["balance"] > 0 and not paid_minimum.get(loan["name"], False):
                state["stress_level"] += 2

        self._apply_weekly_compounding(active_loans)
        state["stress_level"] = min(10, state["stress_level"])

        state["all_loans_cleared"] = all(loan["balance"] <= 0 for loan in state["loans"])

        reward = self._compute_reward()
        done = self._check_done()

        return {
            "observation": self._observation(),
            "reward": reward,
            "done": done,
            "info": {
                "month": state["month"],
                "baseline_fees": round(self.baseline_fees, 2),
            },
        }

    def evaluate(self) -> float:
        if self.state is None:
            raise RuntimeError("Call reset(task_id) before evaluate().")

        session_result = {
            "all_loans_cleared": self.state["all_loans_cleared"],
            "total_fees_paid": round(self.state["total_fees_paid"], 2),
            "baseline_fees": round(self.baseline_fees, 2),
            "spiral_lock_triggered": self.state["spiral_lock"],
        }

        grader_result = run_grader(session_result)
        self.last_grader_result = grader_result

        # Three explicit assertions for the hackathon evaluation contract.
        try:
            assert grader_result["tests"]["test_escaped_trap"]
            assert grader_result["tests"]["test_fees_below_baseline"]
            assert grader_result["tests"]["test_no_spiral_lock"]
            return 1.0
        except AssertionError:
            return 0.0

    def get_state(self) -> dict[str, Any]:
        if self.state is None:
            raise RuntimeError("Call reset(task_id) before get_state().")
        return {
            **self.state,
            "baseline_fees": round(self.baseline_fees, 2),
            "done": self.done,
        }

    def _observation(self) -> dict[str, Any]:
        if self.state is None:
            raise RuntimeError("State not initialized.")

        state = self.state
        month = state["month"]
        months_remaining = max(0, state["horizon_months"] - month)

        credit_union_available = self._credit_union_available(month)
        ngo_available = self._ngo_available(month)

        return {
            "cash_on_hand": round(state["cash_on_hand"], 2),
            "loans": [
                {
                    "name": loan["name"],
                    "balance": round(max(0.0, loan["balance"]), 2),
                    "weekly_fee": round(max(0.0, loan["weekly_fee"]), 2),
                    "days_to_rollover": int(loan.get("days_to_rollover", 7)),
                }
                for loan in state["loans"]
            ],
            "escape_routes": {
                "credit_union_available": credit_union_available,
                "ngo_help_available": ngo_available,
            },
            "stress_level": int(state["stress_level"]),
            "months_remaining": months_remaining,
            "total_fees_paid": round(state["total_fees_paid"], 2),
            "spiral_lock": bool(state["spiral_lock"]),
            "instruction": "Choose an action 0-4 to minimize fees and escape before spiral lock.",
        }

    def _apply_action_pay_full(self, active_loans: list[dict[str, Any]], paid_minimum: dict[str, bool]) -> None:
        assert self.state is not None
        state = self.state

        # Pay highest-fee loans first when cash is limited.
        ordered = sorted(active_loans, key=lambda x: x["weekly_fee"], reverse=True)
        for loan in ordered:
            if loan["balance"] <= 0:
                continue

            if state["cash_on_hand"] >= loan["balance"]:
                state["cash_on_hand"] -= loan["balance"]
                loan["balance"] = 0.0
                loan["weekly_fee"] = 0.0
                paid_minimum[loan["name"]] = True

    def _apply_action_minimum(self, active_loans: list[dict[str, Any]], paid_minimum: dict[str, bool]) -> None:
        assert self.state is not None
        state = self.state

        for loan in active_loans:
            fee = loan["weekly_fee"]
            if state["cash_on_hand"] >= fee:
                state["cash_on_hand"] -= fee
                state["total_fees_paid"] += fee
                paid_minimum[loan["name"]] = True

    def _apply_action_credit_union(self, active_loans: list[dict[str, Any]], paid_minimum: dict[str, bool]) -> None:
        assert self.state is not None
        state = self.state

        if not active_loans:
            return

        if not self._credit_union_available(state["month"]):
            return

        credit_union_rate = float(state["escape_routes"].get("credit_union_rate", 0.18))

        # One-time refinancing: replace predatory terms with lower fee and APR.
        for loan in active_loans:
            if loan["is_refinanced"]:
                continue
            loan["apr_equivalent"] = credit_union_rate
            loan["weekly_fee"] = max(50.0, loan["balance"] * credit_union_rate / 12.0)
            loan["is_refinanced"] = True
            paid_minimum[loan["name"]] = True

        state["credit_union_used"] = True
        state["stress_level"] = max(0, state["stress_level"] - 1)

    def _apply_action_ngo(
        self,
        active_loans: list[dict[str, Any]],
        paid_minimum: dict[str, bool],
        month: int,
    ) -> None:
        assert self.state is not None
        state = self.state

        if not active_loans:
            return

        if not self._ngo_available(month):
            return

        # NGO grant wipes 35% of the most expensive active loan.
        target = max(active_loans, key=lambda x: x["weekly_fee"])
        grant = target["balance"] * 0.35
        target["balance"] = max(0.0, target["balance"] - grant)
        state["ngo_uses"] += 1
        state["stress_level"] = max(0, state["stress_level"] - 2)

        # If borrower has enough cash, also pay this month's minimum on remaining active loans.
        for loan in active_loans:
            if loan["balance"] <= 0:
                paid_minimum[loan["name"]] = True
                continue
            fee = loan["weekly_fee"]
            if state["cash_on_hand"] >= fee:
                state["cash_on_hand"] -= fee
                state["total_fees_paid"] += fee
                paid_minimum[loan["name"]] = True

    def _apply_weekly_compounding(self, active_loans: list[dict[str, Any]]) -> None:
        assert self.state is not None
        state = self.state

        for loan in active_loans:
            if loan["balance"] <= 0:
                continue

            weekly_rate = float(loan["apr_equivalent"]) / 52.0
            for _ in range(4):
                interest = loan["balance"] * weekly_rate
                loan["balance"] += interest
                state["total_fees_paid"] += interest

            loan["days_to_rollover"] = 7

    def _compute_reward(self) -> float:
        assert self.state is not None
        state = self.state

        if state["stress_level"] >= 10:
            state["spiral_lock"] = True
            self.done = True
            return -100.0

        if state["all_loans_cleared"]:
            self.done = True
            months_remaining = max(0, state["horizon_months"] - state["month"])
            return 100.0 + float(months_remaining)

        if state["month"] >= state["horizon_months"]:
            self.done = True
            outstanding = sum(loan["balance"] for loan in state["loans"] if loan["balance"] > 0)
            return -min(100.0, outstanding / 200.0)

        # Dense shaping encourages low stress and lower fee burn while still exploring routes.
        monthly_fee_penalty = min(20.0, state["total_fees_paid"] / 1500.0)
        return -1.0 - monthly_fee_penalty - (state["stress_level"] * 0.25)

    def _check_done(self) -> bool:
        assert self.state is not None
        self.state["done"] = self.done
        return self.done

    def _income_shock(self, month: int) -> float:
        assert self.current_task is not None
        shocks = self.current_task.get("income_shocks", [])
        for shock in shocks:
            if int(shock.get("month", -1)) == month:
                return float(shock.get("amount", 0.0))
        return 0.0

    def _credit_union_available(self, month: int) -> bool:
        assert self.state is not None
        routes = self.state["escape_routes"]
        if routes.get("credit_union_available") is True:
            return True
        open_month = routes.get("credit_union_available_from_month")
        return open_month is not None and month >= int(open_month)

    def _ngo_available(self, month: int) -> bool:
        assert self.state is not None
        routes = self.state["escape_routes"]
        if not bool(routes.get("ngo_help_available", False)):
            return False

        allowed_months = routes.get("ngo_help_months")
        if allowed_months:
            return month in [int(x) for x in allowed_months]
        return True

    def _compute_baseline(self, task: dict[str, Any]) -> float:
        baseline_env = LoanSharkEnvironment(self.tasks_dir)
        baseline_env.current_task = copy.deepcopy(task)
        baseline_env.state = {
            "task_id": task["task_id"],
            "month": 0,
            "horizon_months": int(task["horizon_months"]),
            "cash_on_hand": 0.0,
            "monthly_income": float(task["monthly_income"]),
            "fixed_expenses": float(task["fixed_expenses"]),
            "loans": [
                {
                    "name": loan["name"],
                    "balance": float(loan["balance"]),
                    "weekly_fee": float(loan["weekly_fee"]),
                    "apr_equivalent": float(loan.get("apr_equivalent", 2.6)),
                    "days_to_rollover": 7,
                    "is_refinanced": False,
                }
                for loan in task.get("loans", [])
            ],
            "stress_level": 0,
            "total_fees_paid": 0.0,
            "spiral_lock": False,
            "all_loans_cleared": False,
            "done": False,
            "credit_union_used": False,
            "ngo_uses": 0,
            "escape_routes": copy.deepcopy(task.get("escape_routes", {})),
        }

        for _ in range(int(task["horizon_months"])):
            if baseline_env.state["spiral_lock"]:
                break
            if all(loan["balance"] <= 0 for loan in baseline_env.state["loans"]):
                break
            baseline_env.step(1)

        assert baseline_env.state is not None
        return float(baseline_env.state["total_fees_paid"])
