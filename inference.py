import asyncio
import json
import os
import re
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI
try:
    import google.generativeai as genai
except ImportError:
    genai = None

from client import LoanSharkEscapeEnv

load_dotenv()

# Required Environment Variables (see hackathon dashboard checklist)
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:7860")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
HF_TOKEN = os.getenv("HF_TOKEN")
LOCAL_IMAGE_NAME = os.getenv("LOCAL_IMAGE_NAME", "loan-shark-escape-env")

# Toggle for running without OpenAI tokens
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
USE_MOCK_AGENT = os.getenv("USE_MOCK_AGENT", "false").lower() == "true" or (not os.getenv("OPENAI_API_KEY") and not GOOGLE_API_KEY)

# Initialize OpenAI client
client = None
if os.getenv("OPENAI_API_KEY") and not USE_MOCK_AGENT:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize Gemini client
if GOOGLE_API_KEY and genai:
    genai.configure(api_key=GOOGLE_API_KEY)

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


def _mock_agent_logic(observation: dict[str, Any]) -> str:
    """Fallback deterministic logic when out of API tokens."""
    routes = observation.get("escape_routes", {})
    loans = observation.get("loans", [])
    cash = observation.get("cash_on_hand", 0.0)
    stress = observation.get("stress_level", 0)

    # 1. Priority: Use Escape Routes if available
    if routes.get("credit_union_available") and not observation.get("credit_union_used"):
        return "2"
    
    if routes.get("ngo_help_available"):
        return "3"

    # 2. Priority: Pay off high-interest loans if cash allows
    active_loans = [l for l in loans if l["balance"] > 0]
    if active_loans:
        # Sort by best payoff impact: typically the one with highest fee/balance ratio
        target = max(active_loans, key=lambda x: x["weekly_fee"])
        if cash >= target["balance"]:
            return "0"

    # 3. Default: Pay Minimum to avoid stress death
    if stress > 6:
        return "1"
    
    # Simple heuristic fallback
    return "1"


def _call_llm(prompt: str, observation: dict[str, Any]) -> str:
    # 1. Try Gemini first if key available
    if GOOGLE_API_KEY and genai:
        try:
            # Use gemini-flash-latest as default for stability
            gemini_model = MODEL_NAME if "gemini" in MODEL_NAME.lower() else "gemini-flash-latest"
            model = genai.GenerativeModel(gemini_model)
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"[WARN] Gemini call failed: {e}")
            if not client: return _mock_agent_logic(observation)

    # 2. Try OpenAI fallback
    if client:
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=10,
                temperature=0,
            )
            return (response.choices[0].message.content or "").strip()
        except Exception as e:
            print(f"[WARN] OpenAI call failed: {e}")

    # 3. Final Fallback: Mock Agent
    return _mock_agent_logic(observation)

    # 2. Try OpenAI fallback
    if client:
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=10,
                temperature=0,
            )
            return (response.choices[0].message.content or "").strip()
        except Exception as e:
            print(f"[WARN] OpenAI call failed: {e}")

    # 3. Final Fallback: Mock Agent
    return _mock_agent_logic(observation)


async def run_one_task(env: LoanSharkEscapeEnv, task_id: str) -> dict[str, Any]:
    observation = await env.reset(task_id)
    done = False
    step_count = 0
    while not done and step_count < 60:
        prompt = _build_prompt(observation)
        model_output = _call_llm(prompt, observation)
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
        # Standardize on HUGGINGFACEHUB_API_TOKEN for library compatibility
        os.environ["HUGGINGFACEHUB_API_TOKEN"] = HF_TOKEN

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
