from typing import List, Optional
from datetime import date, datetime
from tiny_erp.models import Customer, Product, Order, OrderLineItem, Invoice, StockTransaction
from tiny_erp.database import db
from tiny_erp.tax import get_tax_rate

class CustomerService:
    def create_customer(self, name: str, contact_info: str) -> Customer:
        if not name.strip():
            raise ValueError("Customer name cannot be empty.")
        cust_id = db.generate_customer_id()
        customer = Customer(customer_id=cust_id, name=name.strip(), contact_info=contact_info.strip())
        db.customers[cust_id] = customer
        return customer

    def list_customers(self) -> List[Customer]:
        return list(db.customers.values())

    def get_customer(self, customer_id: str) -> Optional[Customer]:
        return db.customers.get(customer_id)


class InventoryService:
    def add_product(self, sku: str, name: str, unit_price: float, starting_stock: int) -> Product:
        sku = sku.strip().upper()
        if not sku:
            raise ValueError("SKU cannot be empty.")
        if sku in db.products:
            raise ValueError(f"Product with SKU '{sku}' already exists.")
        if unit_price < 0:
            raise ValueError("Unit price cannot be negative.")
        if starting_stock < 0:
            raise ValueError("Starting stock cannot be negative.")
        
        product = Product(sku=sku, name=name.strip(), unit_price=float(unit_price), stock_quantity=int(starting_stock))
        db.products[sku] = product
        
        if starting_stock > 0:
            tx = StockTransaction(
                transaction_id=db.generate_tx_id(),
                sku=sku,
                change=starting_stock,
                reason="Initial Stock",
                reference_id=sku
            )
            db.stock_transactions.append(tx)
            
        return product

    def restock_product(self, sku: str, quantity: int) -> Product:
        sku = sku.strip().upper()
        product = db.products.get(sku)
        if not product:
            raise ValueError(f"Product with SKU '{sku}' not found.")
        if quantity <= 0:
            raise ValueError("Restock quantity must be greater than zero.")
        
        product.stock_quantity += quantity
        
        tx = StockTransaction(
            transaction_id=db.generate_tx_id(),
            sku=sku,
            change=quantity,
            reason="Restock",
            reference_id=sku
        )
        db.stock_transactions.append(tx)
        return product

    def get_stock_level(self, sku: str) -> int:
        sku = sku.strip().upper()
        product = db.products.get(sku)
        if not product:
            raise ValueError(f"Product with SKU '{sku}' not found.")
        return product.stock_quantity

    def get_product(self, sku: str) -> Optional[Product]:
        return db.products.get(sku.strip().upper())

    def list_products(self) -> List[Product]:
        return list(db.products.values())


class OrderService:
    def create_order(self, customer_id: str, line_items_data: List[dict]) -> Order:
        """
        line_items_data: list of dicts with keys 'sku' and 'quantity'
        """
        customer = db.customers.get(customer_id)
        if not customer:
            raise ValueError(f"Customer '{customer_id}' not found.")
        if not line_items_data:
            raise ValueError("Order must contain at least one line item.")
        
        line_items: List[OrderLineItem] = []
        for item in line_items_data:
            sku = item.get("sku", "").strip().upper()
            qty = int(item.get("quantity", 0))
            if qty <= 0:
                raise ValueError("Line item quantity must be greater than zero.")
            product = db.products.get(sku)
            if not product:
                raise ValueError(f"Product SKU '{sku}' not found.")
            
            line_items.append(OrderLineItem(sku=sku, quantity=qty, unit_price=product.unit_price))

        order_id = db.generate_order_id()
        order = Order(
            order_id=order_id,
            customer_id=customer_id,
            line_items=line_items,
            status="Pending"
        )
        db.orders[order_id] = order
        return order

    def confirm_order(self, order_id: str) -> Order:
        order = db.orders.get(order_id)
        if not order:
            raise ValueError(f"Order '{order_id}' not found.")
        if order.status != "Pending":
            raise ValueError(f"Only Pending orders can be confirmed. Current status: {order.status}")

        # Check stock for all line items before decrementing (prevent negative stock)
        for item in order.line_items:
            product = db.products.get(item.sku)
            if not product:
                raise ValueError(f"Product SKU '{item.sku}' not found.")
            if product.stock_quantity < item.quantity:
                raise ValueError(
                    f"Insufficient stock for SKU '{item.sku}'. Requested: {item.quantity}, Available: {product.stock_quantity}"
                )

        # Decrement stock and record transactions
        for item in order.line_items:
            product = db.products.get(item.sku)
            product.stock_quantity -= item.quantity
            tx = StockTransaction(
                transaction_id=db.generate_tx_id(),
                sku=item.sku,
                change=-item.quantity,
                reason="Order Confirmation",
                reference_id=order_id
            )
            db.stock_transactions.append(tx)

        order.status = "Confirmed"
        return order

    def cancel_order(self, order_id: str) -> Order:
        order = db.orders.get(order_id)
        if not order:
            raise ValueError(f"Order '{order_id}' not found.")
        if order.status == "Cancelled":
            raise ValueError("Order is already cancelled.")
        if order.status == "Invoiced":
            raise ValueError("Cannot cancel an order that has already been invoiced.")

        # If order was Confirmed, restore stock quantities
        if order.status == "Confirmed":
            for item in order.line_items:
                product = db.products.get(item.sku)
                if product:
                    product.stock_quantity += item.quantity
                    tx = StockTransaction(
                        transaction_id=db.generate_tx_id(),
                        sku=item.sku,
                        change=item.quantity,
                        reason="Order Cancellation",
                        reference_id=order_id
                    )
                    db.stock_transactions.append(tx)

        order.status = "Cancelled"
        return order

    def get_order(self, order_id: str) -> Optional[Order]:
        return db.orders.get(order_id)

    def list_orders(self) -> List[Order]:
        return list(db.orders.values())


class InvoicingService:
    def generate_invoice(self, order_id: str, region: str = "US-DEFAULT") -> Invoice:
        order = db.orders.get(order_id)
        if not order:
            raise ValueError(f"Order '{order_id}' not found.")
        if order.status != "Confirmed":
            raise ValueError(f"Order must be Confirmed to generate an invoice. Current status: {order.status}")

        # Check if invoice already exists for this order
        existing_invoice = self.get_invoice_by_order(order_id)
        if existing_invoice:
            raise ValueError(f"Order '{order_id}' has already been invoiced (Invoice ID: {existing_invoice.invoice_id}).")

        # Compute subtotal
        subtotal = sum(item.quantity * item.unit_price for item in order.line_items)
        
        # Get tax rate using plain function get_tax_rate(region)
        tax_rate = get_tax_rate(region)
        tax_amount = round(subtotal * tax_rate, 2)
        grand_total = round(subtotal + tax_amount, 2)
        subtotal = round(subtotal, 2)

        invoice_id = db.generate_invoice_id()
        invoice = Invoice(
            invoice_id=invoice_id,
            order_id=order_id,
            customer_id=order.customer_id,
            subtotal=subtotal,
            tax_rate=tax_rate,
            tax_amount=tax_amount,
            grand_total=grand_total,
            status="Unpaid"
        )
        db.invoices[invoice_id] = invoice

        # Update order status to Invoiced
        order.status = "Invoiced"
        return invoice

    def mark_invoice_paid(self, invoice_id: str, payment_date: date) -> Invoice:
        invoice = db.invoices.get(invoice_id)
        if not invoice:
            raise ValueError(f"Invoice '{invoice_id}' not found.")
        if invoice.status == "Paid":
            raise ValueError(f"Invoice '{invoice_id}' is already marked as paid.")

        invoice.status = "Paid"
        invoice.payment_date = payment_date
        return invoice

    def get_invoice(self, invoice_id: str) -> Optional[Invoice]:
        return db.invoices.get(invoice_id)

    def get_invoice_by_order(self, order_id: str) -> Optional[Invoice]:
        for inv in db.invoices.values():
            if inv.order_id == order_id:
                return inv
        return None

    def list_invoices(self) -> List[Invoice]:
        return list(db.invoices.values())


class ReportingService:
    def get_customer_orders_report(self, customer_id: str) -> List[dict]:
        customer = db.customers.get(customer_id)
        if not customer:
            raise ValueError(f"Customer '{customer_id}' not found.")
        
        report = []
        for order in db.orders.values():
            if order.customer_id == customer_id:
                invoice = InvoicingService().get_invoice_by_order(order.order_id)
                report.append({
                    "order_id": order.order_id,
                    "status": order.status,
                    "created_at": order.created_at,
                    "line_items": [{"sku": i.sku, "quantity": i.quantity, "unit_price": i.unit_price} for i in order.line_items],
                    "invoice_id": invoice.invoice_id if invoice else None,
                    "invoice_status": invoice.status if invoice else None,
                    "grand_total": invoice.grand_total if invoice else None
                })
        return report

    def get_revenue_report(self, start_date: date, end_date: date) -> float:
        total_revenue = 0.0
        for invoice in db.invoices.values():
            if invoice.status == "Paid" and invoice.payment_date:
                # Check if payment_date is inclusively within start_date and end_date
                if start_date <= invoice.payment_date <= end_date:
                    total_revenue += invoice.grand_total
        return round(total_revenue, 2)

    def get_inventory_valuation(self) -> float:
        total_valuation = 0.0
        for product in db.products.values():
            total_valuation += product.stock_quantity * product.unit_price
        return round(total_valuation, 2)
