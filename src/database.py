import json
import os
import random
import string
from datetime import datetime
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "data" / "orders.json"

DEFAULT_ORDERS = [
    {
        "order_id": "ORD-1001",
        "customer_name": "Alice Johnson",
        "customer_email": "alice@example.com",
        "product_name": "AcousticPro Wireless Headphones",
        "category": "Electronics",
        "purchase_date": "2026-09-28",
        "delivery_date": "2026-09-30",
        "amount": 189.99,
        "status": "DELIVERED",
        "refund_status": "NONE",
        "refund_amount": 0.0,
        "refund_notes": ""
    },
    {
        "order_id": "ORD-1002",
        "customer_name": "Bob Smith",
        "customer_email": "bob@example.com",
        "product_name": "FitPulse Smartwatch v2",
        "category": "Electronics",
        "purchase_date": "2026-08-10",
        "delivery_date": "2026-08-14",
        "amount": 249.50,
        "status": "DELIVERED",
        "refund_status": "NONE",
        "refund_amount": 0.0,
        "refund_notes": ""
    },
    {
        "order_id": "ORD-1003",
        "customer_name": "Carlos Gomez",
        "customer_email": "carlos@example.com",
        "product_name": "Artisan Colombian Coffee Beans (2kg)",
        "category": "Perishable Goods",
        "purchase_date": "2026-10-01",
        "delivery_date": "2026-10-02",
        "amount": 45.00,
        "status": "DELIVERED",
        "refund_status": "NONE",
        "refund_amount": 0.0,
        "refund_notes": ""
    },
    {
        "order_id": "ORD-1004",
        "customer_name": "Diana Prince",
        "customer_email": "diana@example.com",
        "product_name": "ErgoPro Lumbar Office Chair",
        "category": "Furniture",
        "purchase_date": "2026-10-02",
        "delivery_date": None,
        "amount": 350.00,
        "status": "IN_TRANSIT",
        "refund_status": "NONE",
        "refund_amount": 0.0,
        "refund_notes": ""
    },
    {
        "order_id": "ORD-1005",
        "customer_name": "Ethan Hunt",
        "customer_email": "ethan@example.com",
        "product_name": "Apex Titan Gaming Laptop RTX 5080",
        "category": "Electronics",
        "purchase_date": "2026-09-30",
        "delivery_date": "2026-10-02",
        "amount": 2599.00,
        "status": "DELIVERED",
        "refund_status": "NONE",
        "refund_amount": 0.0,
        "refund_notes": ""
    },
    {
        "order_id": "ORD-1006",
        "customer_name": "Fiona Gallagher",
        "customer_email": "fiona@example.com",
        "product_name": "AeroStride Pro Running Shoes (Size 9)",
        "category": "Apparel",
        "purchase_date": "2026-09-20",
        "delivery_date": "2026-09-24",
        "amount": 120.00,
        "status": "DELIVERED",
        "refund_status": "NONE",
        "refund_amount": 0.0,
        "refund_notes": ""
    }
]


def load_orders() -> list[dict]:
    """Load orders from JSON file or return defaults if file doesn't exist."""
    if not DATA_FILE.exists():
        reset_database()
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return DEFAULT_ORDERS


def save_orders(orders: list[dict]):
    """Persist orders list to JSON file."""
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(orders, f, indent=2)


def get_order_by_id(order_id: str) -> dict | None:
    """Find order by ID (case-insensitive, trims '#' or spaces)."""
    clean_id = order_id.strip().upper().replace("#", "")
    orders = load_orders()
    for order in orders:
        if order["order_id"].upper() == clean_id:
            return order
    return None


def execute_refund(order_id: str, amount: float, notes: str) -> dict:
    """Action: Updates database to record an approved refund."""
    clean_id = order_id.strip().upper().replace("#", "")
    orders = load_orders()
    ref_id = "REF-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=6))

    for order in orders:
        if order["order_id"].upper() == clean_id:
            order["refund_status"] = "APPROVED"
            order["refund_amount"] = round(amount, 2)
            order["refund_reference_id"] = ref_id
            order["refund_notes"] = notes
            order["refund_timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_orders(orders)
            return {
                "success": True,
                "message": f"Refund of ${amount:.2f} successfully approved for order {order_id}.",
                "refund_reference_id": ref_id,
                "order": order
            }

    return {"success": False, "message": f"Order {order_id} not found."}


def escalate_order(order_id: str, reason: str) -> dict:
    """Action: Flags an order for human manager escalation."""
    clean_id = order_id.strip().upper().replace("#", "")
    orders = load_orders()

    for order in orders:
        if order["order_id"].upper() == clean_id:
            order["refund_status"] = "ESCALATED_TO_HUMAN"
            order["refund_notes"] = reason
            order["escalation_timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_orders(orders)
            return {
                "success": True,
                "message": f"Order {order_id} escalated to human management: {reason}",
                "order": order
            }

    return {"success": False, "message": f"Order {order_id} not found."}


def reset_database():
    """Resets orders.json back to clean test baseline."""
    save_orders(DEFAULT_ORDERS)
