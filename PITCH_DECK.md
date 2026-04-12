# 🦈 Loan Shark Escape — Final Submission Pitch

*(Copy and paste this directly into your Devfolio / Scaler Hackathon submission form)*

---

### 🚀 What is Loan Shark Escape?
**Loan Shark Escape** is a production-ready Reinforcement Learning (RL) environment built perfectly to the OpenEnv specification. It simulates the real-world, high-stress challenge of escaping a predatory debt trap. 

While traditional financial planners rely on static, deterministic rules, real-world marginalized borrowers face adversarial conditions — compounding interest exceeding 200% APR, sudden income shocks, medical emergencies, and psychological "spiral locks". We built an environment to train LLM and RL agents to solve this complex sequential decision-making problem under uncertainty.

### 💡 Why is it Novel? (Creativity & Real-World Utility)
1. **Dynamic ReAct Agent Memory:** We went beyond a simple zero-shot prompt. Our baseline LLM agent utilizes a **ReAct (Reasoning + Acting) architecture**, retaining memory of its past financial decisions to dynamically adjust its strategy month-over-month.
2. **Interactive Visual Dashboard:** We don't just expect judges to read terminal output. We built a fully functional **Streamlit Dashboard** that visualizes the debt curve, income vs. fixed expenses, and stress levels in real-time. It allows judges (and future human users) to play the environment manually against the same adversarial shocks the agent faces.
3. **Compound Stress Mechanics:** We introduced a dual-failure state. The agent doesn't just lose if they run out of money (bankruptcy); they also lose via "Spiral Lock" if their psychological stress meter maxes out at 10. Balancing debt repayment against stress limits fundamentally changes the mathematical strategy.

### ⚙️ Technical Architecture
- **OpenEnv Compliant:** Fully implements the `reset`, `step`, and `evaluate` lifecycle natively via an asynchronous FastAPI backend. Includes strict schema typing using Pydantic.
- **Strict Grader Boundaries:** The custom grader is rigorously bounded to output floats strictly within the Open (0, 1) interval, punishing naïve agent behavior with scores of `0.01` and rewarding mastery with `0.98`.
- **Reproducible Evaluation Engine:** We implemented a seeded internal RNG system tying stochastic shocks directly to the `task_id`, ensuring fair, deterministic runs for hackathon evaluation while preserving variance during massive parallel training.
- **Robust Code Quality:** Achieves high code standards by including an automated `pytest` test suite that rigorously validates state transitions and the strict mathematical bounds of our compound grading function.

### 📊 The Tasks
- **lse-easy:** Favorable debt-to-income ratio. Focuses on testing foundational optimization concepts.
- **lse-medium:** Introduction of the one-time NGO bailout grant. Tests the agent's absolute timing of one-shot lifelines.
- **lse-hard:** Severe adversarial shocks (income drops, sudden medical bills). No credit-union access. Tests survival minimization under "spiral lock" pressure.

### ✅ Verification
All endpoints pass strict Phase 2 criteria. We invite you to clone the repo, run `streamlit run demo.py`, and attempt the escape yourself! 
