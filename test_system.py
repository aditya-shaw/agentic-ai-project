"""
Quick verification script to test:
1. Database loading and lookups
2. State mutations (refund execution & reset)
3. Return policy document reading and RAG fallback
"""

import sys
from src.database import load_orders, get_order_by_id, execute_refund, reset_database
from src.rag import get_policy_text, query_policy

def run_tests():
    print("=" * 50)
    print("[*] Running System Component Tests...")
    print("=" * 50)

    # Test 1: Load Orders
    orders = load_orders()
    assert len(orders) >= 6, "Expected at least 6 mock orders"
    print("[PASS] Test 1: Order database loaded successfully.")

    # Test 2: Order Lookup
    order = get_order_by_id("ORD-1001")
    assert order is not None, "Order ORD-1001 should exist"
    assert order["customer_name"] == "Alice Johnson", "Customer name mismatch"
    print(f"[PASS] Test 2: Found order ORD-1001 for {order['customer_name']} (${order['amount']}).")

    # Test 3: Policy Retrieval (RAG text query)
    policy_snippet = query_policy("electronics return window", api_key="")
    assert "14" in policy_snippet or "Electronics" in policy_snippet, "Should mention 14 days or Electronics"
    print("[PASS] Test 3: Policy retrieval successfully returned relevant policy chunks.")

    # Test 4: Refund Execution (State Mutation)
    result = execute_refund("ORD-1001", 189.99, "Test refund verification")
    assert result["success"] is True, "Refund execution should succeed"
    updated_order = get_order_by_id("ORD-1001")
    assert updated_order["refund_status"] == "APPROVED", "Status should be APPROVED"
    print(f"[PASS] Test 4: Refund executed! Ref ID: {result['refund_reference_id']}")

    # Test 5: Database Reset
    reset_database()
    reset_order = get_order_by_id("ORD-1001")
    assert reset_order["refund_status"] == "NONE", "Status should reset back to NONE"
    print("[PASS] Test 5: Database successfully reset back to clean state.")

    print("\n>>> ALL TESTS PASSED! Your core database and RAG components are working perfectly.")

if __name__ == "__main__":
    run_tests()
