# loan-shark-escape-env

An OpenEnv-compatible reinforcement learning environment where an agent must escape a predatory debt trap before hitting a spiral-lock point.

## Why We Are Building This
Predatory lending creates a sequential decision problem: the borrower can survive one month by paying a small rollover fee, but repeating that action can create a mathematically unwinnable path.

This project models that trap directly.

- Local optimum: pay minimum fee and stay alive this month.
- Global failure: principal stays alive, stress rises, and total fees explode.
- Strategic objective: take short-term pain at the right time (credit union window / NGO window) to escape permanently.

## India Context (Grounding Facts)
- In a Lok Sabha reply dated **March 28, 2022**, the Government stated RBI's working group found approximately **600 illegal lending apps** (Jan 1 to Feb 28, 2021), and RBI's Sachet portal received about **2,562 complaints** against digital lending apps (Jan 1, 2020 to Mar 31, 2021).
- In a Lok Sabha reply dated **March 24, 2025**, the Government cited RBI's digital lending guidelines issued on **September 2, 2022** and the FinTech SRO framework issued on **May 30, 2024** as key controls for customer protection and market conduct.
- The same March 24, 2025 reply also references MeitY advisories dated **December 26, 2023** and **March 15, 2024** targeting harms including unregulated lending platforms.

Sources:
- https://sansad.in/getFile/loksabhaquestions/annex/178/AU4113.pdf?source=pqals
- https://sansad.in/getFile/loksabhaquestions/annex/184/AU3856_qCn1J6.pdf?source=pqals

## Project Structure

```
loan-shark-escape-env/
├── server/
│   ├── __init__.py
│   ├── app.py
│   ├── environment.py
│   └── Dockerfile
├── tasks/
│   ├── lse-easy.json
│   ├── lse-medium.json
│   └── lse-hard.json
├── __init__.py
├── models.py
├── client.py
├── grader.py
├── inference.py
├── openenv.yaml
├── pyproject.toml
├── requirements.txt
├── demo.ipynb
├── .env.example
├── .gitignore
└── README.md
```

## Setup

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Set `.env` values:
- `API_BASE_URL=http://localhost:7860`
- `MODEL_NAME=gpt-4.1-mini` (or an Anthropic model)
- `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`
- `HF_TOKEN` (optional, for hackathon workflow)

## Run Server

```bash
uvicorn server.app:app --host 0.0.0.0 --port 7860 --reload
```

## Run Inference Agent

```bash
python3 inference.py
```

## Actions
- `0`: pay predatory loan in full if cash allows
- `1`: pay minimum rollover fee only
- `2`: refinance via credit union (if available)
- `3`: seek NGO help (if available)
- `4`: do nothing this month

## Evaluation Contract
`grader.py` checks exactly three outcomes:
- escaped trap (`all_loans_cleared`)
- total fees below `85%` of baseline
- no spiral lock

## Demo
Open `demo.ipynb` and run all cells to generate the naive-vs-smart comparison table used in judge demos.

## Deployment

```bash
openenv push --repo-id YOURNAME/loan-shark-escape-env
```
