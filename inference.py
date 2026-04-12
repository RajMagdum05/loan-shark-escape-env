#!/usr/bin/env python3
"""Baseline LLM agent for Loan Shark Escape (OpenAI-compatible API only).

Hackathon configuration (see Scaler OpenEnv Round 1):
  API_BASE_URL — OpenAI-compatible LLM base URL (e.g. Hugging Face router).
  MODEL_NAME   — Model id for chat completions.
  HF_TOKEN     — API key for the LLM (or use OPENAI_API_KEY for openai.com).

The environment server URL is separate (defaults to local Space port):
  ENV_BASE_URL — Loan Shark FastAPI server (default http://127.0.0.1:7860).

Stdout logs use one line per marker: [START], [STEP], [END] with key=value pairs.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

from client import LoanClient

load_dotenv()

# LLM (OpenAI-compatible client — required variables for submission)
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "openai/gpt-oss-120b:novita")
HF_TOKEN = os.getenv("HF_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Environment HTTP API (FastAPI), not the LLM
ENV_BASE_URL = os.getenv("ENV_BASE_URL", "http://127.0.0.1:7860")

_raw_tasks = os.getenv("TASK_IDS", "lse-easy,lse-medium,lse-hard")
TASK_IDS = [t.strip() for t in _raw_tasks.split(",") if t.strip()]

USE_MOCK_AGENT = os.getenv("USE_MOCK_AGENT", "false").lower() == "true"


def _llm_api_key() -> str | None:
    return HF_TOKEN or OPENAI_API_KEY


def _parse_action(raw_text: str) -> str:
    text = raw_text.lower()
    if "refinance" in text:
        return "refinance"
    if "borrow" in text:
        return "borrow"
    if "ngo" in text:
        return "ngo"
    if "pay" in text:
        return "pay"
    return "wait"


def _build_prompt(observation: dict[str, Any]) -> str:
    return (
        "You are an AI advisor helping a borrower escape a predatory debt trap.\n"
        "Clear all debt without letting stress reach 10 (spiral lock).\n\n"
        "Available actions (reply with exactly one keyword):\n"
        "- pay: pay down debt from income\n"
        "- borrow: more debt (usually bad)\n"
        "- refinance: one-time credit-union relief if score > 620 and not used\n"
        "- ngo: one-time grant (wipes ~35% of principal) if not used\n"
        "- wait: skip payment; interest accrues and stress rises\n\n"
        f"Observation JSON:\n{json.dumps(observation, indent=2)}\n\n"
        "Respond with exactly one word: pay, borrow, refinance, ngo, or wait."
    )


def _mock_agent_logic(obs: dict[str, Any]) -> str:
    debt = float(obs.get("total_debt") or 0.0)
    score = float(obs.get("credit_score") or 0.0)
    stress = int(obs.get("stress_level") or 0)
    allowed = set(obs.get("available_actions") or [])
    if debt <= 0:
        return "wait"
    if stress >= 7:
        return "pay"
    if not obs.get("ngo_help_used") and "ngo" in allowed:
        return "ngo"
    if (
        "refinance" in allowed
        and not obs.get("credit_union_used")
        and score > 620
    ):
        return "refinance"
    return "pay"


def _call_llm(client: OpenAI | None, prompt: str, obs: dict[str, Any]) -> str:
    if USE_MOCK_AGENT or client is None:
        return _mock_agent_logic(obs)
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=32,
            temperature=0,
        )
        return (response.choices[0].message.content or "").strip()
    except Exception as exc:
        print(f"[STEP] event=llm_error msg={json.dumps(str(exc))}")
        return _mock_agent_logic(obs)


def _fmt_kv(pairs: list[tuple[str, Any]]) -> str:
    parts = []
    for k, v in pairs:
        if isinstance(v, bool):
            v_str = "true" if v else "false"
        elif v is None:
            v_str = ""
        else:
            v_str = str(v)
        v_str = re.sub(r"\s+", " ", v_str).strip()
        parts.append(f"{k}={v_str}")
    return " ".join(parts)


async def run_task(
    client: LoanClient,
    task_id: str,
    oa_client: OpenAI | None,
) -> dict[str, Any]:
    obs = await client.reset(task_id)
    step_idx = 0
    max_steps = 24

    while step_idx < max_steps:
        st = await client.get_state()
        if st.get("is_done"):
            break

        prompt = _build_prompt(obs)
        raw_output = _call_llm(oa_client, prompt, obs)
        action = _parse_action(raw_output)

        obs = await client.step(action)

        print(
            "[STEP] "
            + _fmt_kv(
                [
                    ("task_id", task_id),
                    ("step", step_idx),
                    ("action", action),
                    ("debt", obs.get("total_debt")),
                    ("stress", obs.get("stress_level")),
                    ("credit_score", obs.get("credit_score")),
                    ("done", obs.get("is_done")),
                    ("reward", obs.get("reward")),
                ]
            )
        )

        if obs.get("is_done"):
            break
        step_idx += 1

    eval_result = await client.evaluate()
    score = float(eval_result.get("score", 0.01))
    # Clamp to strictly (0, 1) — validator rejects exact 0.0 and 1.0
    score = max(0.01, min(0.99, score))
    print(
        "[STEP] "
        + _fmt_kv(
            [
                ("task_id", task_id),
                ("step", "evaluate"),
                ("score", round(score, 4)),
                ("passed", eval_result.get("passed")),
                ("total", eval_result.get("total")),
            ]
        )
    )
    return {"task_id": task_id, "score": score, "evaluate": eval_result}


async def main() -> None:
    key = _llm_api_key()
    oa_client: OpenAI | None = None
    if key and not USE_MOCK_AGENT:
        oa_client = OpenAI(base_url=API_BASE_URL, api_key=key)

    print(
        "[START] "
        + _fmt_kv(
            [
                ("env_base_url", ENV_BASE_URL),
                ("api_base_url", API_BASE_URL),
                ("model", MODEL_NAME),
                ("tasks", ",".join(TASK_IDS)),
                ("mock", USE_MOCK_AGENT or not key),
            ]
        )
    )

    client = LoanClient(ENV_BASE_URL)
    summary: dict[str, float] = {}

    for tid in TASK_IDS:
        try:
            row = await run_task(client, tid, oa_client)
            summary[row["task_id"]] = row["score"]
        except Exception as exc:
            print(
                "[STEP] "
                + _fmt_kv(
                    [
                        ("task_id", tid),
                        ("step", "error"),
                        ("msg", str(exc)),
                    ]
                )
            )
            summary[tid] = 0.01

    print("[END] " + _fmt_kv([("scores_json", json.dumps(summary, sort_keys=True))]))


if __name__ == "__main__":
    asyncio.run(main())
