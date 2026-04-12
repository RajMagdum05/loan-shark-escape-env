# 🏦 Loan Shark Escape Environment

[![OpenEnv](https://img.shields.io/badge/OpenEnv-Compatible-blue)](https://github.com/meta-pytorch/OpenEnv)
[![FastAPI](https://img.shields.io/badge/FastAPI-Framework-green)](https://fastapi.tiangolo.com/)
[![Hackathon](https://img.shields.io/badge/Hackathon-Ready-orange)](https://scaler.com/school-of-technology/meta-pytorch-hackathon/)

An **OpenEnv-compatible** reinforcement learning environment that simulates a predatory debt trap. Agents must navigate sequential monthly decisions, manage stress, and leverage strategic "escape routes" to survive and clear their debt.

## 🚀 The Core Challenge: The "Spiral Lock"
Predatory payday loans (often 200%+ APR) create a mathematical "event horizon". If a borrower only pays the minimum fee to avoid immediate default, the principal remains untouched, fees compound, and stress rises.
- **Stress ≥ 10**: Triggers a **Spiral Lock** (Terminal Failure).
- **Goal**: Clear all loans with minimal total fee burn.

---

## 🛠 Project Structure

```bash
.
├── server/
│   ├── app.py           # FastAPI Server Endpoints
│   └── environment.py   # Core RL Logic & Simulation
├── tasks/               # Easy, Medium, Hard Scenario Configs
├── models.py            # Pydantic Data Models
├── grader.py            # Evaluation Logic
├── client.py            # Python Async Client SDK
├── inference.py         # Baseline Inference Script
├── openenv.yaml         # OpenEnv Manifest
└── SUBMISSION.md        # Hackathon Dashboard Content
```

---

## 🚦 Getting Started

### 1. Local Setup
```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### 2. Launch the Environment
```bash
# Start the FastAPI server on port 7860
uvicorn server.app:app --host 0.0.0.0 --port 7860
```

### 3. Run a Sample Agent
```bash
# Runs a GPT-powered agent against the medium task
python3 inference.py
```

---

## 🕹 Action Space
| ID | Action | Description |
|---|---|---|
| **0** | **Pay Full** | Pay off principal + fees if cash on hand allows. |
| **1** | **Pay Min** | Pay only the minimum rollover fee (Default/Naive action). |
| **2** | **Refinance** | Switch to a Credit Union rate (Requires window/availability). |
| **3** | **NGO Help** | Apply for a one-time grant to wipe 35% of principal. |
| **4** | **Wait** | Do nothing. Increases stress heavily if minimums missed. |

---

## 📊 Evaluation & Grader
We provide a strictly defined `grader.py` that evaluates agent performance across three dimensions:
- **`test_escaped_trap`**: All loan balances reached zero.
- **`test_fees_below_baseline`**: Total fees paid < 85% of the naive baseline.
- **`test_no_spiral_lock`**: Stress never reached 10.

---

## 🌍 Social Impact Grounding (India Context)
Illegal digital lending apps are a systemic issue. According to RBI reports:
- Over **600 illegal lending apps** identified in early 2021.
- RBI's **Sachet portal** received **2,500+ complaints** in just one year.
- Our "Spiral Lock" mechanic models the real-world cognitive load and exhaustion faced by borrowers in these debt traps.

---

## 🚢 Deployment
Easily deploy to Hugging Face Spaces using the OpenEnv CLI:
```bash
openenv push --repo-id YOUR_USER/loan-shark-escape-env
```
