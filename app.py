import os
import streamlit as st
from dotenv import load_dotenv

from src.database import load_orders, reset_database
from src.rag import get_policy_text
from src.agent import create_support_agent

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Apex AI - Autonomous Support & Refund Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for polished look
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #64748B;
        margin-bottom: 1.5rem;
    }
    .badge-tag {
        display: inline-block;
        padding: 3px 10px;
        font-size: 0.8rem;
        font-weight: 600;
        border-radius: 12px;
        margin-right: 6px;
        background-color: #E2E8F0;
        color: #334155;
    }
    .stButton>button {
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# ----------------- SIDEBAR -----------------
with st.sidebar:
    st.title("🤖 Apex AI Control Center")
    st.caption("Agentic AI • Gen AI • RAG in Action")
    st.markdown("---")

    # API Key Configuration
    st.subheader("🔑 1. API Configuration")
    env_key = os.getenv("GOOGLE_API_KEY", "")
    api_key_input = st.text_input(
        "Google Gemini API Key",
        value=env_key,
        type="password",
        help="Get a free key from https://aistudio.google.com/"
    )
    api_key = api_key_input.strip() if api_key_input else env_key

    if not api_key:
        st.warning("⚠️ Please provide a Gemini API Key to enable the Agent.")
    else:
        st.success("✅ Gemini API Key detected.")

    st.markdown("---")

    # Live Orders Database Viewer
    st.subheader("📦 2. Live Order Database")
    st.caption("Watch real-time status changes when the agent executes refunds:")
    
    orders = load_orders()
    # Format table for display
    display_rows = []
    for o in orders:
        ref_status = o.get("refund_status", "NONE")
        status_icon = "⚪"
        if ref_status == "APPROVED":
            status_icon = "🟢 APPROVED"
        elif ref_status == "ESCALATED_TO_HUMAN":
            status_icon = "🟡 ESCALATED"
        else:
            status_icon = "⚪ NONE"

        display_rows.append({
            "Order ID": o["order_id"],
            "Item": o["product_name"][:18] + "...",
            "Category": o["category"],
            "Price": f"${o['amount']:.2f}",
            "Delivery": o["delivery_date"] or "In Transit",
            "Refund": status_icon
        })
    st.dataframe(display_rows, use_container_width=True, hide_index=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Refresh DB", use_container_width=True):
            st.rerun()
    with col2:
        if st.button("⚠️ Reset DB", use_container_width=True, help="Reset orders back to original state for new test"):
            reset_database()
            st.toast("Database reset to initial mock state!")
            st.rerun()

    st.markdown("---")
    # Policy Document Viewer (RAG Grounding)
    with st.expander("📖 View RAG Knowledge Base (Policy)"):
        st.markdown(get_policy_text())

# ----------------- MAIN AREA -----------------
st.markdown('<div class="main-header">Autonomous Support & Dispute Agent</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">'
    '<span class="badge-tag">RAG: ChromaDB Policy Search</span>'
    '<span class="badge-tag">Agentic AI: Tool Calling & Safe Execution</span>'
    '<span class="badge-tag">Gen AI: Contextual Reasoning</span>'
    '</div>',
    unsafe_allow_html=True
)

# Quick Demo Scenario Buttons
st.markdown("##### 💡 Quick Interview Demo Scenarios (Click to test):")
chip_cols = st.columns(3)
selected_prompt = None

with chip_cols[0]:
    if st.button("🟢 Eligible Refund (ORD-1001)", use_container_width=True, help="Delivered 4 days ago, defective headphones"):
        selected_prompt = "I want a refund for order ORD-1001. The headphones stopped working after 3 days."
with chip_cols[1]:
    if st.button("🔴 Expired Window (ORD-1002)", use_container_width=True, help="Delivered >45 days ago, smartwatch"):
        selected_prompt = "Can you process a return and refund for my smartwatch order ORD-1002?"
with chip_cols[2]:
    if st.button("🚫 Non-Refundable Item (ORD-1003)", use_container_width=True, help="Coffee beans - perishable food"):
        selected_prompt = "I would like to return order ORD-1003 for the gourmet coffee beans."

chip_cols_2 = st.columns(3)
with chip_cols_2[0]:
    if st.button("🚚 In-Transit Order (ORD-1004)", use_container_width=True, help="Item not yet delivered"):
        selected_prompt = "Please cancel and refund order ORD-1004 for the office chair."
with chip_cols_2[1]:
    if st.button("👔 High-Value Escalation (ORD-1005)", use_container_width=True, help="Gaming laptop over $1500 threshold"):
        selected_prompt = "I need to return my laptop order ORD-1005 ($2,599)."
with chip_cols_2[2]:
    if st.button("📖 General Policy Question", use_container_width=True, help="Direct RAG knowledge query"):
        selected_prompt = "What is your return policy for electronics versus clothing items?"

st.markdown("---")

# Session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Hello! I am your Apex AI Support Specialist. I can check return policies, verify your order details, and process eligible refunds automatically. How may I help you today?",
            "steps": []
        }
    ]

# Display conversation
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if msg.get("steps"):
            with st.expander("🔍 View Agent Thought Process & Tool Calls", expanded=False):
                for step_idx, (action, observation) in enumerate(msg["steps"], start=1):
                    st.markdown(f"**Step {step_idx}: Tool Called ➔ `{action.tool}`**")
                    st.code(f"Inputs: {action.tool_input}", language="python")
                    st.markdown(f"**Tool Output / Observation:**")
                    st.info(f"{observation}")

# Handle user input from either chat input or quick scenario button
user_input = st.chat_input("Type your message or order inquiry here...") or selected_prompt

if user_input:
    if not api_key:
        st.error("Please enter your Google Gemini API Key in the sidebar to run the agent.")
    else:
        # Append user message
        st.session_state.messages.append({"role": "user", "content": user_input, "steps": []})
        with st.chat_message("user"):
            st.write(user_input)

        # Build agent and invoke
        with st.chat_message("assistant"):
            with st.spinner("🤖 Agent is analyzing request, checking policy, and evaluating actions..."):
                try:
                    agent_executor = create_support_agent(api_key=api_key)
                    # Convert history format for LangChain
                    chat_history = []
                    for m in st.session_state.messages[:-1]:
                        if m["role"] == "user":
                            chat_history.append(("human", m["content"]))
                        elif m["role"] == "assistant":
                            chat_history.append(("ai", m["content"]))

                    result = agent_executor.invoke({
                        "input": user_input,
                        "chat_history": chat_history[-6:]  # Keep last 3 turns
                    })

                    output_text = result.get("output", "I processed your request.")
                    if isinstance(output_text, list):
                        parts = []
                        for item in output_text:
                            if isinstance(item, dict) and "text" in item:
                                parts.append(item["text"])
                            else:
                                parts.append(str(item))
                        output_text = "\n\n".join(parts)

                    st.markdown(output_text)

                    if intermediate_steps:
                        with st.expander("🔍 View Agent Thought Process & Tool Calls", expanded=True):
                            for step_idx, (action, observation) in enumerate(intermediate_steps, start=1):
                                st.markdown(f"**Step {step_idx}: Tool Called ➔ `{action.tool}`**")
                                st.code(f"Inputs: {action.tool_input}", language="python")
                                st.markdown(f"**Tool Output / Observation:**")
                                st.info(f"{observation}")

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": output_text,
                        "steps": intermediate_steps
                    })

                except Exception as e:
                    error_msg = f"Error running agent: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg,
                        "steps": []
                    })
