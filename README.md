---
title: Loan Shark Escape Environment Server
emoji: 🦈
colorFrom: red
colorTo: yellow
sdk: docker
pinned: false
app_port: 7860
base_path: /docs
tags:
  - openenv
license: mit
---
# 🦈 Loan Shark Escape Environment

Loan Shark Escape is a production-ready Reinforcement Learning (RL) challenge built strictly to the [OpenEnv](https://github.com/meta-pytorch/OpenEnv) specification. It simulates the real-world, high-stress challenge of escaping a predatory debt trap.

While traditional financial planners rely on static rules, this environment forces an AI agent to handle **sequential decision-making under uncertainty** in an adversarial environment. The agent must successfully balance short-term survival (paying down debt) against long-term freedom (avoiding compound interest and psychological "spiral lock") utilizing a mathematically bounded grading schema.

## 🚀 Key Features

1. **ReAct Agent Memory (Reasoning + Acting)**: Our baseline LLM inference script doesn't just guess blindly—it uses a state-of-the-art ReAct architecture. The agent maintains a memory log of its previous monthly actions, analyzing its past strategic choices to iteratively plot an escape route around shocks.
2. **Interactive Streamlit Dashboard**: To fully realize the *"Real-World Utility"* of this project, we built a fully interactive `demo.py` Streamlit UI. This allows anyone to visually track the debt curve, view vital meters, and manually play the simulation themselves.
3. **Reproducible Evaluation**: A meticulously seeded internal RNG system tying stochastic shocks (job losses, medical bills) directly to the `task_id`, explicitly ensuring fair, deterministic runs during evaluation.
4. **Strict `(0, 1)` Grader Adherence**: Backed by `pytest` unit tests, our `grader.py` leverages a sophisticated multi-variable composite score mathematically bounded to the open interval `(0, 1)`, fiercely punishing naïve AI defaults.

---

## 🛠 Server Setup

### Docker (Recommended)
```bash
docker build -t loan-shark-env:latest .
docker run --rm -p 7860:7860 loan-shark-env:latest
curl http://localhost:7860/health
```
On Server health success response will be:
`{"status":"healthy","service":"loan-shark-env"}`

### Without Docker
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn server.app:app --host 0.0.0.0 --port 7860
```

---

## 💻 Client Setup & Evaluation

### Quick Start (Interactive Demo)
For interactive evaluation and visualizing the debt trap mechanics yourself, run the built-in Streamlit dashboard:
```bash
# Assumes dependencies from requirements.txt are installed
streamlit run demo.py
```

### Configure Scenario (LLM Inference)
To customize the intelligent ReAct agent for automated evaluation, configure these environment variables before running:
- `API_KEY` - Your LLM API key
- `API_BASE_URL` - Provider API URL (e.g., `https://api.openai.com/v1`)
- `MODEL_NAME` - Model name (e.g., `meta-llama-3`)
- `USE_MOCK_AGENT` - Set `true` to test locally without an API key, or `false` to use the LLM
- `ENV_BASE_URL` - The environment server address (e.g., `http://localhost:7860` or your Hugging Face Space URL)

### Run Automated Benchmark
```bash
python3 inference.py
```
Outputs are rigorously formatted following the exact OpenEnv baseline template (`[START]`, `[STEP]`, `[END]`) natively required by the Phase 2 validation script.

---

## ⚙️ Environment Mechanics & Rules

| Component | Description |
|-----------|-------------|
| **State Space** | Monthly income, total debt, credit score, stress level (0–10), available actions |
| **Action Space** | `pay` · `borrow` · `refinance` · `ngo` · `wait` — 5 discrete actions |
| **Reward Signal** | Composite optimization of debt reduction (45%), stress management (35%), and fee efficiency (20%) |
| **Termination** | Debt cleared (Win) · Bankruptcy (credit < 300) · Spiral lock (stress ≥ 10) · Time limit (24mo) |

### 📊 Included Benchmark Tasks

| Task ID | Debt | Income | Escape Routes | Adversarial Shocks | Goal |
|---------|------|--------|---------------|-------------------|------|
| `lse-easy` | ₹3,000 | ₹2,500 | Credit union access | Few | Clear debt in ≤12 months |
| `lse-medium` | ₹5,000 | ₹2,000 | Credit union + NGO | Income shock at month 8 | Clear debt in ≤18 months |
| `lse-hard` | ₹8,000 | ₹1,500 | NGO only (No credit union) | Random extreme shocks | Survive 24 months, minimize debt |

**Grading (`grader.py`):** Calculates an aggregate evaluation score bounded exclusively inside `(0.0, 1.0)`. It penalizes accrued fees vs. the baseline, rewards the percentage of principal cleared, and severely penalizes hitting spiral-lock stress constraints.
