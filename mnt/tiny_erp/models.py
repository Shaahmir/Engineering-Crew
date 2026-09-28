from dataclasses import dataclass, field
from datetime import date, datetime
from typing import List, Optional

@dataclass
class Customer:
    customer_id: str
    name: str
    contact_info: str
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class Product:
    sku: str
    name: str
    unit_price: float
    stock_quantity: int

@dataclass
class OrderLineItem:
    sku: str
    quantity: int
    unit_price: float

@dataclass
class Order:
    order_id: str
    customer_id: str
    line_items: List[OrderLineItem]
    status: str  # "Pending", "Confirmed", "Cancelled", "Invoiced"
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class Invoice:
    invoice_id: str
    order_id: str
    customer_id: str
    subtotal: float
    tax_rate: float
    tax_amount: float
    grand_total: float
    status: str  # "Unpaid", "Paid"
    issued_date: datetime = field(default_factory=datetime.utcnow)
    payment_date: Optional[date] = None

@dataclass
class StockTransaction:
    transaction_id: str
    sku: str
    change: int
    reason: str
    reference_id: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
