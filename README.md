---
title: Loan Shark Escape
emoji: 🦈
colorFrom: red
colorTo: yellow
sdk: docker
app_port: 7860
pinned: false
license: mit
---

# 🦈 Loan Shark Escape — Predatory Lending RL Environment

> **Meta PyTorch Hackathon × Scaler School of Technology**
> An OpenEnv-compliant reinforcement learning environment that simulates the real-world challenge of escaping predatory debt traps.

## 🎯 Problem Statement

**400 million people worldwide** are trapped in predatory lending cycles. Loan sharks exploit vulnerable borrowers with hidden fees, compounding interest rates exceeding 200% APR, and psychological pressure tactics. Traditional financial planning tools use static rules that fail when borrowers face dynamic, adversarial conditions — income shocks, medical emergencies, and escalating stress.

**Why Reinforcement Learning?**
Static rule-based planners cannot handle the *sequential decision-making under uncertainty* that defines real debt escape. An RL agent must:
- Balance short-term survival (paying rent) vs. long-term freedom (clearing debt)
- Time one-shot escape routes (NGO grants, credit union refinancing) optimally
- Adapt to stochastic income shocks and compounding interest

## 🏗️ Solution: The Loan Shark Escape Environment

A **production-ready RL environment** where an agent must make monthly financial decisions to escape a predatory debt trap before hitting a "spiral lock" — the point of no return where stress and debt compound irreversibly.

### Core Mechanics

| Component | Description |
|-----------|-------------|
| **State Space** | Monthly income, total debt, credit score, stress level (0–10), available actions |
| **Action Space** | `pay` · `borrow` · `refinance` · `ngo` · `wait` — 5 discrete actions |
| **Reward Signal** | Composite: debt reduction (45%) + stress management (35%) + fee efficiency (20%) |
| **Termination** | ✅ Debt cleared · ❌ Bankruptcy (credit < 300) · ❌ Spiral lock (stress ≥ 10) · ⏰ Time limit (24mo) |
| **Stochastic Events** | Seeded random shocks: job loss (income -25%), medical bills (+$500 debt) |

### Escape Routes (One-Shot Strategic Tools)
- **🏦 Credit Union Refinance** — Reduces debt by 10%, requires credit score > 620. Available in easy/medium tasks only.
- **🤝 NGO Grant** — Wipes 35% of principal debt. Single use per episode.
- **💳 Pay** — Direct debt repayment (up to 80% of monthly income). Reduces stress.

## 📊 Three Tasks with Progressive Difficulty

| Task ID | Debt | Income | Escape Routes | Shocks | Goal |
|---------|------|--------|---------------|--------|------|
| `lse-easy` | ₹3,000 | ₹2,500 | Credit union ✓ | Few | Clear debt in ≤12 months |
| `lse-medium` | ₹5,000 | ₹2,000 | Credit union + NGO | Income shock at month 8 | Clear debt in ≤18 months |
| `lse-hard` | ₹8,000 | ₹1,500 | NGO only (no credit union) | Multiple shocks | Survive 24 months, minimize debt |

Each task has a **grader** that produces a score strictly in `(0, 1)`:
- `0.99` = All debt cleared, no spiral lock, fees below baseline
- `0.50` = Partial debt reduction, some stress management
- `0.01` = Failed to make meaningful progress

## 🧠 Inference Agent

The baseline agent uses an **LLM (OpenAI-compatible API)** to make decisions:

```
Observation → LLM Prompt → Action Selection → Environment Step → Reward
```

A fallback **heuristic agent** is included for offline evaluation:
1. Use NGO grant early (maximum debt reduction)
2. Refinance when credit score allows
3. Always pay to reduce debt and stress
4. Never borrow (increases debt spiral)

## 🏛️ Project Structure

```
loan-shark-escape-env/
├── server/
│   ├── app.py              # FastAPI server (OpenEnv-compliant)
│   └── environment.py      # Core RL environment logic
├── tasks/
│   ├── lse-easy.json        # Task configuration: easy
│   ├── lse-medium.json      # Task configuration: medium
│   └── lse-hard.json        # Task configuration: hard
├── inference.py             # LLM agent + heuristic baseline
├── grader.py                # Scoring functions (strictly 0–1)
├── models.py                # Pydantic data models
├── client.py                # HTTP client for env interaction
├── openenv.yaml             # OpenEnv specification
├── Dockerfile               # Container deployment
├── pyproject.toml           # Python project config
└── requirements.txt         # Dependencies
```

## 🚀 Quick Start

**1. Install dependencies:**
```bash
pip install -r requirements.txt
```

**2. Start the environment server:**
```bash
uvicorn server.app:app --host 0.0.0.0 --port 7860
```

**3. Run the baseline agent:**
```bash
python inference.py
```

**4. API Endpoints:**
```
POST /reset    — Start a new episode (accepts {"task_id": "lse-easy"})
POST /step     — Take an action (accepts {"action_type": "pay", "amount": 0})
GET  /state    — Get current environment state
POST /evaluate — Get graded score for completed episode
GET  /health   — Health check
```

## 📈 Grading Criteria

The grader evaluates three orthogonal metrics:

| Metric | Weight | What it measures |
|--------|--------|-----------------|
| **Debt Escape** | 50% | Did the agent clear all debt? |
| **Fee Efficiency** | 25% | Were total fees below the naive-payment baseline? |
| **Stress Management** | 25% | Did stress stay below the spiral-lock threshold? |

## 🔬 Why This Matters

This environment demonstrates that **RL agents can outperform static financial planning rules** in adversarial, stochastic settings. The implications extend to:
- **Financial literacy tools** — Teaching borrowers optimal escape strategies
- **Policy simulation** — Testing regulatory interventions against predatory lending
- **AI safety** — Studying agent behavior under resource constraints and time pressure

## 📝 License

MIT License — see [LICENSE](LICENSE) for details.

## 👥 Team Neon

Built for the Meta PyTorch Hackathon × Scaler School of Technology, Round 1.
