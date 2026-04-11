import json
import os
import copy
from typing import List, Dict, Any

class LoanSharkEnvironment:
    def __init__(self, tasks_dir: str = "tasks"):
        # Ensure the tasks directory exists
        self.tasks_dir = tasks_dir
        if not os.path.exists(self.tasks_dir):
            os.makedirs(self.tasks_dir)
        self.current_task_id = None
        self.state = None
        self.baseline_fees = 0.0

    def reset(self, task_id: str) -> Dict[str, Any]:
        task_path = os.path.join(self.tasks_dir, f"{task_id}.json")
        if not os.path.exists(task_path):
            raise FileNotFoundError(f"Task configuration {task_id}.json not found in {self.tasks_dir}")
            
        with open(task_path, "r") as f:
            task_config = json.load(f)

        self.current_task_id = task_id
        self.state = {
            "total_cash": float(task_config.get("initial_cash", 1000.0)),
            "budget": float(task_config.get("monthly_budget", 3000.0)),
            "expenses": float(task_config.get("monthly_expenses", 2500.0)),
            "loans": copy.deepcopy(task_config.get("loans", [])),
            "stress_level": 0,
            "spiral_lock": False,
            "months_passed": 0,
            "total_interest_paid": 0.0,
            "ngo_help_used": False,
            "refinanced": False
        }
        
        # We need a copy of the state to compute baseline without affecting current state
        self.baseline_fees = self._compute_baseline(task_config)
        return self._get_observation()

    def _get_observation(self) -> Dict[str, Any]:
        obs = {
            "total_cash": round(self.state["total_cash"], 2),
            "budget": self.state["budget"],
            "expenses": self.state["expenses"],
            "disposable_cash": round(self.state["budget"] - self.state["expenses"], 2),
            "loans": self.state["loans"],
            "stress_level": self.state["stress_level"],
            "spiral_lock": self.state["spiral_lock"],
            "months_passed": self.state["months_passed"],
            "total_interest_paid": round(self.state["total_interest_paid"], 2)
        }
        return {"observation": obs}

    def step(self, action: int) -> Dict[str, Any]:
        if self.state["spiral_lock"]:
            return {"reward": -100, "done": True, "observation": self._get_observation()["observation"]}

        # Monthly flow
        self.state["total_cash"] += (self.state["budget"] - self.state["expenses"])
        
        # Action Logic
        if action == 0: # Pay predatory in full
            for loan in self.state["loans"]:
                if self.state["total_cash"] >= loan["balance"]:
                    self.state["total_cash"] -= loan["balance"]
                    loan["balance"] = 0
                else:
                    loan["balance"] -= self.state["total_cash"]
                    self.state["total_cash"] = 0
        elif action == 1: # Pay minimum rollover fee
            for loan in self.state["loans"]:
                fee = loan.get("min_payment", 50.0)
                if self.state["total_cash"] >= fee:
                    self.state["total_cash"] -= fee
                else:
                    self.state["stress_level"] += 2
        elif action == 2: # Refinance
            if self.state["stress_level"] < 5 and not self.state["refinanced"]:
                for loan in self.state["loans"]:
                    loan["weekly_rate"] = 0.002 # Significant reduction
                self.state["refinanced"] = True
                self.state["stress_level"] = max(0, self.state["stress_level"] - 1)
            else:
                self.state["stress_level"] += 1
        elif action == 3: # NGO Help
            if not self.state["ngo_help_used"]:
                for loan in self.state["loans"]:
                    loan["balance"] = max(0, loan["balance"] - 500)
                self.state["ngo_help_used"] = True
                self.state["stress_level"] = max(0, self.state["stress_level"] - 2)
            else:
                self.state["stress_level"] += 1
        elif action == 4: # Do nothing
            self.state["stress_level"] += 2

        # Weekly interest compounding (4 weeks per month)
        for _ in range(4):
            for loan in self.state["loans"]:
                if loan["balance"] > 0:
                    interest = loan["balance"] * loan["weekly_rate"]
                    loan["balance"] += interest
                    self.state["total_interest_paid"] += interest

        self.state["months_passed"] += 1

        # Termination checks
        all_cleared = all(loan["balance"] <= 0 for loan in self.state["loans"])
        if self.state["stress_level"] >= 10:
            self.state["spiral_lock"] = True
            reward = -100.0
            done = True
        elif all_cleared:
            reward = 100.0 + (60 - self.state["months_passed"])
            done = True
        elif self.state["months_passed"] >= 60:
            reward = -self.state["total_interest_paid"] / 100.0
            done = True
        else:
            reward = -1.0 # Step penalty
            done = False

        return {
            "observation": self._get_observation()["observation"],
            "reward": reward,
            "done": done,
            "info": {"baseline_fees": self.baseline_fees}
        }

    def _compute_baseline(self, task_config: Dict[str, Any]) -> float:
        # Simple simulation for naive agent
        temp_state = {
            "total_cash": float(task_config.get("initial_cash", 1000.0)),
            "budget": float(task_config.get("monthly_budget", 3000.0)),
            "expenses": float(task_config.get("monthly_expenses", 2500.0)),
            "loans": copy.deepcopy(task_config.get("loans", [])),
            "stress_level": 0,
            "total_interest_paid": 0.0,
            "months_passed": 0
        }
        
        for _ in range(60):
            temp_state["total_cash"] += (temp_state["budget"] - temp_state["expenses"])
            # Action 1: Pay minimum
            for loan in temp_state["loans"]:
                fee = loan.get("min_payment", 50.0)
                if temp_state["total_cash"] >= fee:
                    temp_state["total_cash"] -= fee
                else:
                    temp_state["stress_level"] += 2
            
            # Compounding
            for _ in range(4):
                for loan in temp_state["loans"]:
                    if loan["balance"] > 0:
                        interest = loan["balance"] * loan["weekly_rate"]
                        loan["balance"] += interest
                        temp_state["total_interest_paid"] += interest
            
            temp_state["months_passed"] += 1
            if all(loan["balance"] <= 0 for loan in temp_state["loans"]) or temp_state["stress_level"] >= 10:
                break
        return temp_state["total_interest_paid"]

    def evaluate(self) -> float:
        try:
            # 1. All loans cleared
            assert all(loan["balance"] <= 0 for loan in self.state["loans"]), "Loans not cleared"
            # 2. Fees below 80% baseline
            assert self.state["total_interest_paid"] < (self.baseline_fees * 0.8), "Interest too high"
            # 3. No spiral lock
            assert not self.state["spiral_lock"], "Spiral lock triggered"
            return 1.0
        except AssertionError as e:
            print(f"Evaluation failed: {e}")
            return 0.0
