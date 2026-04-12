# 🦈 Loan Shark Escape: A Debt-Trap Simulation

> **Submission for Scaler Meta-PyTorch Hackathon**
> **Project:** `loan-shark-escape-env`
> **Goal:** An OpenEnv RL environment modeling predatory lending and strategic escape.

## 📌 Problem Statement
Predatory lending is a global crisis, often trapping vulnerable individuals in a cycle of debt. Traditional payday loans offer "easy" short-term liquidity, but conceal high weekly fees and aggressive compounding. 

The core struggle is a **sequential decision problem**: 
1. **The Trap:** Paying only the minimum fee keeps the borrower "safe" today but mathematically guarantees long-term ruin.
2. **The Escape:** Strategic use of limited windows (NGO grants, Credit Union refinancing) requires long-term planning and temporary cash-flow sacrifice.

## 💡 Why It Matters
This environment provides a playground for RL agents to learn **financial resilience**. It captures the psychological and mathematical "Spiral Lock"—a point of no return where stress level hits 10 and the borrower is permanently trapped. By modeling this, we can test and generate "smart policies" that could eventually inform consumer advisory tools.

## 🛠 Technical Approach
- **OpenEnv Framework:** Fully compliant with OpenEnv standards (FastAPI, Manifest-driven).
- **Custom Simulation Engine:**
  - **Weekly Compounding:** Interest accrues 4 times per month.
  - **Stress Mechanic:** Missed minimums increase stress (+2). Stress 10 triggers `Spiral Lock`.
  - **Action Space (0-4):** Includes `Pay Full`, `Pay Minimum`, `Refinance`, `Seek Help`, and `Wait`.
- **Baseline Policy:** A "Naive" agent that only pays minimum fees, precomputed for every task to provide a strict performance target.

## 🚀 API Endpoints
- `POST /reset`: Initialize a task (easy, medium, hard).
- `POST /step`: Execute one of 5 actions. Returns observation, reward, and stress info.
- `GET /state`: Full snapshot for debugging.
- `POST /evaluate`: Final performance metrics via `grader.py`.
- `GET /health`: Liveness probe.

## 📊 Evaluation & Metrics
The environment is graded on:
1. **Escaped Trap:** Did all balances reach 0?
2. **Efficiency:** Were total fees paid < 85% of the naive baseline?
3. **Resilience:** Did the agent avoid the `Spiral Lock`?

## 📈 Results / Demo Summary
In our tests, a "Smart" LLM-based agent (GPT-4o) successfully identifies the Credit Union window in Task `lse-medium`, refinancing at 18% APR instead of the predatory 260% APR, saving over **₹12,000** in total fees compared to the naive policy.

---
**GitHub Repository:** [https://github.com/RajMagdum05/loan-shark-escape-env.git](https://github.com/RajMagdum05/loan-shark-escape-env.git)
**Deployed Space:** [https://huggingface.co/spaces/RajMagdum05/loan-shark-escape](https://huggingface.co/spaces/RajMagdum05/loan-shark-escape)
