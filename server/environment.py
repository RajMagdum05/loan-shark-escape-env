import json
import os
import subprocess
from typing import Tuple

from models import LoanSharkObservation, LoanSharkState, LoanSharkAction, LoanDetail, EscapeRoutes

class LoanSharkEnvironment:
    """Core simulation for Loan Shark Escape RL environment."""
    
    def __init__(self):
        self.state: LoanSharkState | None = None
        self.config: dict | None = None

    def reset(self, task_id: str) -> LoanSharkObservation:
        """Initialize the environment state from tasks/{task_id}.json."""
        config_path = os.path.join("tasks", f"{task_id}.json")
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config for task {task_id} not found at {config_path}")
            
        with open(config_path, "r") as f:
            self.config = json.load(f)
        
        # Month 1 surplus
        initial_cash = self.config["monthly_income"] - self.config["fixed_expenses"]
        
        loans = [
            LoanDetail(
                name=l.get("name", f"Loan-{i}"),
                balance=float(l["balance"]),
                weekly_fee=float(l["weekly_fee"]),
                apr_equivalent=float(l.get("apr_equivalent", 0.0)),
                days_to_rollover=l.get("days_to_rollover", 30)
            ) for i, l in enumerate(self.config["loans"])
        ]
        
        routes_config = self.config.get("escape_routes", {})
        routes = EscapeRoutes(
            credit_union_available=routes_config.get("credit_union_available", False),
            ngo_help_available=routes_config.get("ngo_help_available", False)
        )
        
        self.state = LoanSharkState(
            task_id=task_id,
            current_month=1,
            cash=initial_cash,
            loans=loans,
            escape_routes=routes,
            stress_level=0,
            total_fees_paid=0.0,
            baseline_fees=0.0,
            spiral_lock_triggered=False,
            all_loans_cleared=False,
            months_remaining=self.config["horizon_months"],
            last_action=None,
            last_reward=None,
            episode_done=False
        )
        
        # Compute baseline at reset time as requested
        self.state.baseline_fees = self._compute_baseline()
        
        self._update_dynamic_routes()
        return self._get_observation()

    def _update_dynamic_routes(self):
        """Update escape route availability based on current simulation month."""
        if self.config is None or self.state is None:
            return
            
        routes_config = self.config.get("escape_routes", {})
        
        # Calculate dynamic availability
        if "credit_union_available_from_month" in routes_config:
            self.state.escape_routes.credit_union_available = (
                self.state.current_month >= routes_config["credit_union_available_from_month"]
            )
            
        if "ngo_help_months" in routes_config:
            self.state.escape_routes.ngo_help_available = (
                self.state.current_month in routes_config["ngo_help_months"]
            )

    def _get_observation(self) -> LoanSharkObservation:
        """Construct observation for agent based on current month's availability."""
        if self.state is None or self.config is None:
             raise RuntimeError("Environment not reset")

        self._update_dynamic_routes()
        
        return LoanSharkObservation(
            cash_on_hand=self.state.cash,
            loans=self.state.loans,
            escape_routes=self.state.escape_routes,
            stress_level=self.state.stress_level,
            months_remaining=self.state.months_remaining,
            total_fees_paid=self.state.total_fees_paid,
            spiral_lock=self.state.spiral_lock_triggered,
            instruction=self.config.get("description", ""),
            baseline_fees=self.state.baseline_fees
        )

    def step(self, action: int):
        """Processes one month of simulation based on the agent's action."""
        if self.state is None or self.config is None or self.state.episode_done:
            return self._get_observation(), 0.0, True
            
        # 1. Monthly Surplus
        # Income and expenses are handled at the start of next month phase.
        # This month we use current cash.
        
        reward = 0.0
        # 0=pay in full, 1=pay min, 2=CU, 3=NGO, 4=nothing
        
        for loan in self.state.loans:
            if loan.balance <= 0:
                continue
                
            monthly_min_fee = loan.weekly_fee * 4
            
            if action == 0: # Pay in full
                if self.state.cash >= loan.balance:
                    self.state.cash -= loan.balance
                    loan.balance = 0
                else:
                    # Fallback to pay min if possible, else stress
                    if self.state.cash >= monthly_min_fee:
                        self.state.cash -= monthly_min_fee
                        self.state.total_fees_paid += monthly_min_fee
                    else:
                        self.state.stress_level += 2
            
            elif action == 1: # Pay min only
                if self.state.cash >= monthly_min_fee:
                    self.state.cash -= monthly_min_fee
                    self.state.total_fees_paid += monthly_min_fee
                else:
                    self.state.stress_level += 2 # Missing min adds 2 stress
            
            elif action == 2: # Credit Union refinance
                if self.state.escape_routes.credit_union_available:
                    # Clear loan, but adds some stress for paperwork
                    loan.balance = 0
                    self.state.stress_level += 1
                else:
                    self.state.stress_level += 2 # Invalid route penalty
            
            elif action == 3: # NGO Help
                if self.state.escape_routes.ngo_help_available:
                    # NGO negotiates 50% discount on balance
                    loan.balance *= 0.5
                    self.state.stress_level -= 2 # Relief
                else:
                    self.state.stress_level += 2 # Tried help that wasn't there
            
            elif action == 4: # Do nothing
                self.state.stress_level += 2 # Missing min adds 2 stress

        # 2. Weekly Compounding Interest for 4 weeks
        for i, loan in enumerate(self.state.loans):
            if loan.balance > 0:
                # Use apr_equivalent from config if available
                apr = self.config["loans"][i].get("apr_equivalent", 0.0)
                weekly_rate = apr / 52.0
                loan.balance *= (1 + weekly_rate)**4

        # 3. Check Stress Spiral (Spiral Lock)
        if self.state.stress_level >= 10:
            self.state.spiral_lock_triggered = True
            self.state.episode_done = True
            reward = -100.0
            
        # 4. Check Win Condition
        self.state.all_loans_cleared = all(l.balance <= 0 for l in self.state.loans)
        if self.state.all_loans_cleared and not self.state.episode_done:
            self.state.episode_done = True
            reward = 100.0 + (self.state.months_remaining * 10) # Bonus for speed
            
        # 5. Advance Time
        self.state.current_month += 1
        self.state.months_remaining -= 1
        if self.state.months_remaining <= 0 and not self.state.episode_done:
            self.state.episode_done = True
            reward = -50.0 # Time's up penalty
            
        # 6. Next Month Surplus and Shocks
        if not self.state.episode_done and self.config is not None:
            surplus = self.config["monthly_income"] - self.config["fixed_expenses"]
            
            # Apply Income Shocks
            shocks = self.config.get("income_shocks", [])
            for shock in shocks:
                if shock["month"] == self.state.current_month:
                    surplus += shock["amount"]
            
            self.state.cash += surplus
            
        self.state.last_reward = reward
        return self._get_observation(), reward, self.state.episode_done

    def _compute_baseline(self) -> float:
        """Simulate naive agent always paying minimum to set baseline."""
        if self.config is None:
            return 0.0
            
        temp_cash = self.config["monthly_income"] - self.config["fixed_expenses"]
        total_baseline = 0.0
        
        # Simple simulation over horizon
        for m in range(self.config["horizon_months"]):
            for l in self.config["loans"]:
                min_pay = l["weekly_fee"] * 4
                if temp_cash >= min_pay:
                    temp_cash -= min_pay
                    total_baseline += min_pay
            temp_cash += (self.config["monthly_income"] - self.config["fixed_expenses"])
            
        return total_baseline

    def evaluate(self) -> float:
        """Run pytest assertions via grader.py."""
        try:
            # Assumes grader.py exists and has compatible tests
            result = subprocess.run(["pytest", "grader.py"], capture_output=True, text=True)
            if result.returncode == 0:
                return 1.0
            else:
                return 0.0
        except Exception:
            return 0.0
