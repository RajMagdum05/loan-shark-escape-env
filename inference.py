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

from client import LoanClient

load_dotenv()

# --- Configuration ---
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:7860")
MODEL_NAME = os.getenv("MODEL_NAME", "gemini-1.5-flash")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
HF_TOKEN = os.getenv("HF_TOKEN")

# Force Mock Agent if no keys available
USE_MOCK_AGENT = os.getenv("USE_MOCK_AGENT", "false").lower() == "true" or (not OPENAI_API_KEY and not GOOGLE_API_KEY)

# Clients initialization
oa_client = None
if OPENAI_API_KEY and not USE_MOCK_AGENT:
    oa_client = OpenAI(api_key=OPENAI_API_KEY)

if GOOGLE_API_KEY and genai:
    genai.configure(api_key=GOOGLE_API_KEY)

TASK_IDS = ["lse-easy", "lse-medium", "lse-hard"]


# --- Core Inference Logic ---

def _parse_action(raw_text: str) -> str:
    """Parses action string: pay, borrow, refinance, ngo, wait."""
    text = raw_text.lower()
    if "pay" in text: return "pay"
    if "borrow" in text: return "borrow"
    if "refinance" in text: return "refinance"
    if "ngo" in text: return "ngo"
    return "wait"


def _build_prompt(observation: dict[str, Any]) -> str:
    return (
        "You are an AI advisor helping a borrower escape a predatory debt trap.\n"
        "Your goal is to clear the debt while maintaining a good credit score and low stress.\n\n"
        "Available Actions:\n"
        "- 'pay': Pay down debt using current income (Best for survival).\n"
        "- 'borrow': Take more cash but increase debt and stress (High risk).\n"
        "- 'refinance': Use once for debt reduction (Requires credit score > 620).\n"
        "- 'ngo': One-time grant to wipe 35% of principal.\n"
        "- 'wait': Do nothing; interest accumulates and stress rises.\n\n"
        f"Current Observation: {json.dumps(observation, indent=2)}\n\n"
        "Respond with EXACTLY one action keyword: pay, borrow, refinance, ngo, or wait."
    )


def _mock_agent_logic(obs: dict[str, Any]) -> str:
    """Fallback rule-based logic."""
    debt = obs.get("total_debt", 0.0)
    score = obs.get("credit_score", 0.0)
    stress = obs.get("stress_level", 0)

    if debt > 0:
        if obs.get("month") == 1: # High impact early moves
           return "ngo"
        if score > 620:
           return "refinance"
        return "pay"
    return "wait"


def _call_llm(prompt: str, obs: dict[str, Any]) -> str:
    if USE_MOCK_AGENT:
        return _mock_agent_logic(obs)

    # 1. Try Gemini
    if GOOGLE_API_KEY and genai:
        try:
            gemini_model = MODEL_NAME if "gemini" in MODEL_NAME.lower() else "gemini-flash-latest"
            model = genai.GenerativeModel(gemini_model)
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"[WARN] Gemini failed: {e}")

    # 2. Try OpenAI
    if oa_client:
        try:
            response = oa_client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=20,
                temperature=0,
            )
            return (response.choices[0].message.content or "").strip()
        except Exception as e:
            print(f"[WARN] OpenAI failed: {e}")

    return _mock_agent_logic(obs)


async def run_task(client: LoanClient, task_id: str):
    print(f"\n[TASK] {task_id}")
    obs = await client.reset(task_id)
    done = False
    step = 0
    
    while not done and step < 24:
        prompt = _build_prompt(obs)
        raw_output = _call_llm(prompt, obs)
        action = _parse_action(raw_output)
        
        obs = await client.step(action)
        
        # OpenEnv Log Format
        print(f"[STEP] ep={task_id} step={step:02d} action={action} "
              f"debt={obs.get('total_debt')} score={obs.get('credit_score')} msg={obs.get('message')}")
        
        # Termination check (server returns is_done in some specs, or we check obs)
        # For this implementation, we rely on the server message or state
        if "escaped" in obs.get("message", "").lower() or "bankrupt" in obs.get("message", "").lower() or step == 23:
            done = True
        
        step += 1

    result = await client.evaluate()
    print(f"Grader Result: {json.dumps(result, indent=2)}")


async def main():
    print("[START]")
    client = LoanClient(API_BASE_URL)
    
    for tid in TASK_IDS:
        try:
            await run_task(client, tid)
        except Exception as e:
            print(f"Error in {tid}: {e}")
            
    print("[END]")


if __name__ == "__main__":
    asyncio.run(main())
