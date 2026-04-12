import asyncio
import json
import os
import re
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

from client import LoanSharkEscapeEnv

load_dotenv()

# Required Environment Variables (see hackathon dashboard checklist)
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:7860")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
HF_TOKEN = os.getenv("HF_TOKEN")  # No default as per checklist
LOCAL_IMAGE_NAME = os.getenv("LOCAL_IMAGE_NAME", "loan-shark-escape-env")

# Comma-separated task ids (default: all three difficulties for grader enumeration)
TASK_IDS = [
    t.strip()
    for t in os.getenv("TASK_IDS", "lse-easy,lse-medium,lse-hard").split(",")
    if t.strip()
]

def _parse_action(raw_text: str) -> int:
    match = re.search(r"\b([0-4])\b", raw_text)
    if match:
        return int(match.group(1))
    return 1


def _build_prompt(observation: dict[str, Any]) -> str:
    return (
        "You are controlling a borrower in a debt-trap simulation.\n"
        "Choose exactly ONE action digit from 0 to 4.\n"
        "0: pay predatory loan in full if cash allows\n"
        "1: pay minimum rollover fee only\n"
        "2: refinance via credit union if available (use at most once; check credit_union_used)\n"
        "3: seek NGO help if available\n"
        "4: do nothing this month\n\n"
        "Spiral lock: if cash_on_hand is below the sum of weekly_fee on loans with balance>0, you lose.\n"
        "Goal: clear all loans, beat fee baseline, never hit spiral lock.\n"
        f"Observation: {json.dumps(observation, indent=2)}\n\n"
        "Respond with only one digit 0-4."
    )


def _call_llm(prompt: str) -> str:
    client = OpenAI() # Uses OPENAI_API_KEY from env
    
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=10,
        temperature=0,
    )
    return (response.choices[0].message.content or "").strip()


async def run_one_task(env: LoanSharkEscapeEnv, task_id: str) -> dict[str, Any]:
    observation = await env.reset(task_id)
    done = False
    step_count = 0
    while not done and step_count < 60:
        prompt = _build_prompt(observation)
        model_output = _call_llm(prompt)
        action = _parse_action(model_output)

        step_payload = await env.step({"action": action})
        reward = step_payload.get("reward", 0)
        done = bool(step_payload.get("done", False))
        observation = step_payload.get("observation", step_payload)
        metadata = step_payload.get("metadata", {})

        ep_id = metadata.get("episode_id", "N/A")[:8]
        # Keep core fields first for automated log parsers; task id appended.
        print(
            f"[STEP] ep={ep_id} step={step_count:02d} action={action} reward={reward} done={done} task={task_id}"
        )
        step_count += 1

    evaluate_payload = await env.evaluate()
    return {
        "task_id": task_id,
        "steps": step_count,
        "evaluate_response": evaluate_payload,
    }


async def run_episode() -> None:
    print("[START]")

    if HF_TOKEN:
        os.environ.setdefault("HUGGINGFACEHUB_API_TOKEN", HF_TOKEN)

    async with LoanSharkEscapeEnv(API_BASE_URL) as env:
        try:
            for task_id in TASK_IDS:
                print(f"[TASK] task_id={task_id}")
                result = await run_one_task(env, task_id)
                print("grader_result:")
                print(json.dumps(result["evaluate_response"], indent=2))

        except Exception as e:
            print(f"Error during episode: {e}")
            raise

    print("[END]")


if __name__ == "__main__":
    asyncio.run(run_episode())
