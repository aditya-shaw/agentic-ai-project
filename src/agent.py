from typing import Any, Dict, List
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI
try:
    from langchain.agents import create_tool_calling_agent, AgentExecutor
except ImportError:
    from langchain_classic.agents import create_tool_calling_agent, AgentExecutor

from src.database import get_order_by_id, execute_refund, escalate_order
from src.rag import query_policy

SYSTEM_PROMPT = """You are Apex Retail's Autonomous Customer Support & Dispute Resolution Agent.
Your job is to assist customers with return, refund, policy inquiries, and dispute tickets.

You have access to 4 specialized tools:
1. `check_return_policy`: Query the company's official return, refund, and warranty policy using semantic search (RAG).
2. `lookup_customer_order`: Retrieve real-time order data from the customer database.
3. `execute_order_refund`: Approve and process an immediate refund in the database for eligible orders.
4. `escalate_order_to_management`: Escalate complex cases, orders over $1500, or in-transit delivery disputes to a human supervisor.

STRICT OPERATIONAL GUIDELINES:
1. ORDER LOOKUP: If the customer mentions an Order ID or asks about a specific purchase, look up their order first with `lookup_customer_order`.
2. POLICY VERIFICATION (RAG): Always consult `check_return_policy` to verify:
   - The specific category return window (e.g. 14 days for Electronics, 30 days for Apparel/General).
   - Exclusions (e.g. Perishable Goods, digital keys, intimate wear are NON-REFUNDABLE).
   - Condition requirements and timelines.
3. DECISION & ACTION EXECUTION:
   - If the order is DELIVERED, within window, not excluded, and <= $1500: Call `execute_order_refund` and generate the refund.
   - If the order value is > $1500: Automated limit exceeded. Call `escalate_order_to_management`.
   - If the order is marked 'IN_TRANSIT': It cannot be returned before delivery. Inform the customer or escalate if package is delayed.
   - If the return window has expired or the item is non-refundable: Reject politely, explaining the exact policy clause.
4. RESPONSE FORMAT:
   - Maintain an empathetic, clear, and professional tone.
   - Mention the specific policy clause applied.
   - If refunded, provide the refund reference ID, amount, and the 3-5 business days banking timeline.
"""


def build_tools(api_key: str):
    """Build the suite of tools for the agent."""
    @tool
    def check_return_policy(query: str) -> str:
        """Search the official company return, refund, and cancellation policies (RAG knowledge base).
        Use this to verify return windows, warranty terms, restocking fees, and non-refundable categories."""
        return query_policy(query, api_key=api_key)

    @tool
    def lookup_customer_order(order_id: str) -> str:
        """Retrieve customer order data from the database by Order ID (e.g., 'ORD-1001', 'ORD-1002').
        Returns customer name, product, category, delivery date, amount, order status, and refund status."""
        order = get_order_by_id(order_id)
        if not order:
            return f"Order '{order_id}' was not found in the database. Please verify the ID."
        return str(order)

    @tool
    def execute_order_refund(order_id: str, amount: float, reason: str) -> str:
        """Approve and process an official financial refund in the database.
        Sets refund status to APPROVED, updates database, and generates a Refund Reference ID.
        Only call this if the order meets the return policy criteria and amount <= $1500."""
        result = execute_refund(order_id, amount, reason)
        return str(result)

    @tool
    def escalate_order_to_management(order_id: str, reason: str) -> str:
        """Escalate an order ticket to a human manager in the database.
        Call this when an order exceeds the $1500 automated threshold, or is IN_TRANSIT,
        or requires a human policy exception."""
        result = escalate_order(order_id, reason)
        return str(result)

    return [check_return_policy, lookup_customer_order, execute_order_refund, escalate_order_to_management]


def create_support_agent(api_key: str):
    """Creates a LangChain Tool-Calling Agent with Gemini and returns the executor."""
    tools = build_tools(api_key)

    llm = ChatGoogleGenerativeAI(
        model="gemini-3.8-flash",
        google_api_key=api_key,
        temperature=0.2
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        return_intermediate_steps=True,
        handle_parsing_errors=True,
        max_iterations=6
    )
    return agent_executor
