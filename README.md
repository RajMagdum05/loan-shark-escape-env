# Loan Shark Escape RL Environment

A predatory lending escape RL environment for the Meta PyTorch OpenEnv Hackathon.

## Description
An agent must navigate a series of financial monthly decisions to pay off predatory loans before spiraling into a debt trap ("Spiral Lock").

## Features
- Weekly compounding interest.
- Stress mechanics for missed payments.
- Dynamic escape routes (Credit Unions, NGOs).
- Income shocks (Employment gaps, medical bills).

## Setup
```bash
pip install -r requirements.txt
```

## Running the Server
```bash
uvicorn server.app:app --reload
```

## Running Tests
```bash
pytest grader.py
```

## OpenEnv Manifest
Refer to `openenv.yaml` for environment metadata.
