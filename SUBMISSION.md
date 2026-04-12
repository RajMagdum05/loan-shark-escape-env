# Loan Shark Escape — Hackathon submission summary

**Environment:** Predatory lending / debt-trap escape as a sequential decision process (monthly actions, compounding interest, stress, spiral lock).

**OpenEnv surface:** `openenv.yaml` + FastAPI: `POST /reset`, `POST /step`, `GET /state`, `POST /evaluate`, `GET /health`.

**Tasks:** `lse-easy`, `lse-medium`, `lse-hard` (difficulty via debt, income, shocks, refinance availability).

**Grading:** `grader.py` → aggregate score in **[0.0, 1.0]** from debt cleared, fees vs baseline, and peak stress (no spiral lock).

**Baseline agent:** Root `inference.py` — OpenAI-compatible client (`API_BASE_URL`, `MODEL_NAME`, `HF_TOKEN`); environment URL via `ENV_BASE_URL`. Structured logs: `[START]`, `[STEP]`, `[END]`.

**Deploy:** Dockerfile exposes **7860**; push to **Hugging Face Space** (Docker SDK).

**Repo / Space URLs:** *(fill in before submitting)*

- GitHub: `https://github.com/<you>/loan-shark-escape-env`
- Hugging Face Space: `https://huggingface.co/spaces/<you>/<space-name>`
