# Hackathon Submission Copy

## Project Title
Loan Shark Escape Environment (OpenEnv)

## One-Line Summary
A reinforcement learning environment where an agent must escape predatory debt before reaching a spiral-lock point of no return.

## Problem Statement
Predatory loans create a debt trap where the local monthly choice (pay minimum fee and survive now) is globally catastrophic (principal persists, fees compound, stress rises).

## Why This Matters
This environment models debt-trap dynamics as a sequential decision problem, not a one-step classification task. The agent must identify an escape sequence using limited timing windows (credit union and NGO support).

## Key Mechanics
- 5 actions (`0..4`) with real trade-offs
- Weekly compounding costs on outstanding loans
- Stress dynamics with hard terminal condition (`spiral_lock` at stress 10)
- Escape-route availability windows by month
- Baseline simulation (naive minimum-fee behavior) for objective comparison

## Environment Endpoints
- `POST /reset`
- `POST /step`
- `GET /state`
- `POST /evaluate`
- `GET /health`

## Tasks
- `lse-easy`
- `lse-medium`
- `lse-hard`

## Evaluation
`grader.py` validates:
1. Escaped trap (`all_loans_cleared`)
2. Fees below baseline threshold (`< 85%`)
3. No spiral lock

## Repository
https://github.com/RajMagdum05/loan-shark-escape-env.git

## Demo Pitch (Judges)
- Naive policy (always minimum fee) tends toward trap dynamics and high fee burn.
- Strategic policy (uses credit-union/NGO windows) exits earlier with lower total cost.

## Run Commands
```bash
pip install -r requirements.txt
uvicorn server.app:app --host 0.0.0.0 --port 7860
python3 inference.py
```

## Deploy Command
```bash
openenv push --repo-id YOURNAME/loan-shark-escape-env
```
