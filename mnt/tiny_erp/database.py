from typing import Dict, List, Optional
from tiny_erp.models import Customer, Product, Order, Invoice, StockTransaction

class InMemoryDatabase:
    def __init__(self):
        self.customers: Dict[str, Customer] = {}
        self.products: Dict[str, Product] = {}
        self.orders: Dict[str, Order] = {}
        self.invoices: Dict[str, Invoice] = {}
        self.stock_transactions: List[StockTransaction] = []
        
        # Counters for IDs
        self._customer_counter = 1000
        self._order_counter = 1000
        self._invoice_counter = 1000
        self._tx_counter = 1000

    def generate_customer_id(self) -> str:
        self._customer_counter += 1
        return f"CUST-{self._customer_counter}"

    def generate_order_id(self) -> str:
        self._order_counter += 1
        return f"ORD-{self._order_counter}"

    def generate_invoice_id(self) -> str:
        self._invoice_counter += 1
        return f"INV-{self._invoice_counter}"

    def generate_tx_id(self) -> str:
        self._tx_counter += 1
        return f"TX-{self._tx_counter}"

    def reset(self):
        self.customers.clear()
        self.products.clear()
        self.orders.clear()
        self.invoices.clear()
        self.stock_transactions.clear()
        self._customer_counter = 1000
        self._order_counter = 1000
        self._invoice_counter = 1000
        self._tx_counter = 1000

# Singleton database instance across the application
db = InMemoryDatabase()
