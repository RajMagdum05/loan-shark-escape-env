import streamlit as st
import pandas as pd
import sys
import os

# Add local paths so we can import from server
sys.path.append(os.path.abspath("."))
from server.environment import LoanSharkEnvironment
from server.models import LoanAction

st.set_page_config(page_title="Loan Shark Escape", page_icon="🦈", layout="wide")

st.title("🦈 Loan Shark Escape")
st.markdown("Escape the predatory debt trap before stress hits 10 or 24 months pass.")

if "env" not in st.session_state:
    st.session_state.env = LoanSharkEnvironment()
    st.session_state.obs = st.session_state.env.reset("lse-medium")
    st.session_state.history = []
    st.session_state.history.append({
        "Month": st.session_state.obs.month,
        "Debt": st.session_state.obs.total_debt,
        "Stress": st.session_state.obs.stress_level,
        "Score": st.session_state.obs.credit_score,
        "Action": "Start",
        "Message": st.session_state.obs.message
    })

env = st.session_state.env
obs = st.session_state.obs

def step_env(action_type):
    if obs.is_done:
        return
    st.session_state.obs = env.step(LoanAction(action_type=action_type, amount=0))
    st.session_state.history.append({
        "Month": st.session_state.obs.month,
        "Debt": st.session_state.obs.total_debt,
        "Stress": st.session_state.obs.stress_level,
        "Score": st.session_state.obs.credit_score,
        "Action": action_type.upper(),
        "Message": st.session_state.obs.message
    })

col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    st.subheader("Your Status")
    st.metric("Total Debt", f"₹{obs.total_debt:.2f}")
    st.metric("Monthly Income", f"₹{obs.income:.2f}")

with col2:
    st.subheader("Vitals")
    st.metric("Stress Level (Max 10)", obs.stress_level)
    st.metric("Credit Score", obs.credit_score)

with col3:
    st.subheader("Game State")
    st.metric("Month", f"{obs.month} / 24")
    if obs.is_done:
        eval_dict = env.evaluate()
        final_score = eval_dict['score']
        st.error(f"GAME OVER: {env.get_state().termination_reason}")
        st.success(f"Final Score: {final_score:.3f}")
    else:
        st.info("Status: Active")

st.divider()

if not obs.is_done:
    st.subheader("Take Action")
    action_cols = st.columns(len(obs.available_actions))
    for i, action in enumerate(obs.available_actions):
        with action_cols[i]:
            if st.button(action.upper(), use_container_width=True):
                step_env(action)
                st.rerun()

st.subheader("Environment Log")
st.info(obs.message)

if st.session_state.history:
    df = pd.DataFrame(st.session_state.history)
    st.dataframe(df, use_container_width=True)

    st.subheader("Debt vs Time")
    st.line_chart(df.set_index("Month")["Debt"])

st.divider()
st.subheader("Controls")
task_select = st.selectbox("Select Scenario", ["lse-easy", "lse-medium", "lse-hard"])
if st.button("Reset Environment", type="primary"):
    st.session_state.env = LoanSharkEnvironment()
    st.session_state.obs = st.session_state.env.reset(task_select)
    st.session_state.history = [{
        "Month": st.session_state.obs.month,
        "Debt": st.session_state.obs.total_debt,
        "Stress": st.session_state.obs.stress_level,
        "Score": st.session_state.obs.credit_score,
        "Action": "Start",
        "Message": st.session_state.obs.message
    }]
    st.rerun()
