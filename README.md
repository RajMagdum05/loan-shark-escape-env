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
# Loan Shark Escape Environment

This environment exposes the **Loan Shark Escape** challenge through the OpenEnv reset/step/state interface. The server runs a FastAPI app that serves the OpenEnv endpoints, confronting an agent with the adversarial, high-stress mechanics of predatory debt traps.

## Server Setup

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

## Client Setup

### Quick Start (Demo)

For a quick demo, we provide a sophisticated baseline inference script built to evaluate the OpenEnv endpoints automatically via a ReAct (Reasoning + Acting) LLM loop or a mock heuristic agent:

```bash
# Run baseline heuristics locally without LLM API
USE_MOCK_AGENT=true ENV_BASE_URL=http://localhost:7860 python3 inference.py
```

For interactive UI evaluation and playing against the environment yourself, run:
```bash
# Assumes dependencies from requirements.txt are installed
streamlit run demo.py
```

### Configure Scenario (LLM Inference)

To customize the agent for your own LLM evaluation, configure the environment variables prior to running `inference.py`:

**LLM Variables:**
- `API_KEY` - Your OpenAI/Anthropic/Local LLM API key
- `API_BASE_URL` - Your LLM Provider API URL (e.g., `https://api.openai.com/v1`)
- `MODEL_NAME` - Model name (e.g., `gpt-4o-mini`, `meta-llama-3`)
- `USE_MOCK_AGENT` - Set to `true` to test entirely locally, or `false` to use the LLM

### Run Client

**Run ReAct scenario-based benchmark:**
```bash
python3 inference.py
```

Outputs will be emitted in strict OpenEnv evaluation format (`[START]`, `[STEP]`, `[END]`) directly to standard output, verifying the agent's performance across all configured tasks.

---

## 🎯 Domain Context: The Problem

Traditional financial planning tools use static rules that fail when marginalized borrowers face dynamic, adversarial conditions — income shocks, medical emergencies, and escalating stress. 

**Why Reinforcement Learning?**
Static rule-based planners cannot handle the *sequential decision-making under uncertainty* that defines real debt escape. An RL agent must:
- Balance short-term survival (paying down debt) vs. long-term freedom (avoiding spiral lock)
- Time one-shot escape routes (NGO grants, credit union refinancing) optimally
- Adapt to stochastic income shocks and compounding interest over 24 months

### Environment Mechanics

| Component | Description |
|-----------|-------------|
| **State Space** | Monthly income, total debt, credit score, stress level (0–10), available actions |
| **Action Space** | `pay` · `borrow` · `refinance` · `ngo` · `wait` — 5 discrete actions |
| **Reward Signal** | Composite: debt reduction (45%) + stress management (35%) + fee efficiency (20%) |
| **Termination** | ✅ Debt cleared · ❌ Bankruptcy (credit < 300) · ❌ Spiral lock (stress ≥ 10) · ⏰ Time limit (24mo) |

### Included Benchmark Tasks

| Task ID | Debt | Income | Escape Routes | Shocks | Goal |
|---------|------|--------|---------------|--------|------|
| `lse-easy` | ₹3,000 | ₹2,500 | Credit union ✓ | Few | Clear debt in ≤12 months |
| `lse-medium` | ₹5,000 | ₹2,000 | Credit union + NGO | Income shock at month 8 | Clear debt in ≤18 months |
| `lse-hard` | ₹8,000 | ₹1,500 | NGO only (no CU) | Multiple | Survive 24 months, minimize debt |

*Grader Note: Each task score is rigorously bounded inside the open interval `(0, 1)` mapping strictly to OpenEnv metrics, punishing naïve defaults and rewarding ReAct reasoning.*
