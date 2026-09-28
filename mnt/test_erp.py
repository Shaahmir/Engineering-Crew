import pytest
from datetime import date
from tiny_erp.database import db
from tiny_erp.services import (
    CustomerService,
    InventoryService,
    OrderService,
    InvoicingService,
    ReportingService
)
from tiny_erp.models import Customer, Product, Order, OrderLineItem, Invoice, StockTransaction
from tiny_erp.tax import get_tax_rate

@pytest.fixture(autouse=True)
def run_around_tests():
    db.reset()
    yield

# ============================================================================
# 1. CUSTOMER SERVICE TESTS
# ============================================================================

def test_customer_management():
    cs = CustomerService()
    cust = cs.create_customer("Test Corp", "test@test.com")
    assert cust.customer_id.startswith("CUST-")
    assert cust.name == "Test Corp"
    assert cust.contact_info == "test@test.com"

    fetched = cs.get_customer(cust.customer_id)
    assert fetched is not None
    assert fetched.name == "Test Corp"

    all_custs = cs.list_customers()
    assert len(all_custs) == 1

def test_customer_validation_empty_name():
    cs = CustomerService()
    with pytest.raises(ValueError, match="Customer name cannot be empty"):
        cs.create_customer("   ", "test@test.com")

def test_customer_get_nonexistent():
    cs = CustomerService()
    assert cs.get_customer("NONEXISTENT") is None


# ============================================================================
# 2. INVENTORY SERVICE TESTS
# ============================================================================

def test_inventory_management():
    isvc = InventoryService()
    prod = isvc.add_product("SKU123", "Widget", 19.99, 100)
    assert prod.sku == "SKU123"
    assert isvc.get_stock_level("SKU123") == 100

    isvc.restock_product("sku123", 50)  # test case-insensitivity
    assert isvc.get_stock_level("SKU123") == 150

    fetched = isvc.get_product("SKU123")
    assert fetched is not None
    assert fetched.name == "Widget"

    valuation = ReportingService().get_inventory_valuation()
    assert valuation == 150 * 19.99

def test_inventory_add_product_validations():
    isvc = InventoryService()
    
    # Empty SKU
    with pytest.raises(ValueError, match="SKU cannot be empty"):
        isvc.add_product("", "Widget", 10.0, 10)

    # Duplicate SKU
    isvc.add_product("W1", "Widget 1", 10.0, 10)
    with pytest.raises(ValueError, match="already exists"):
        isvc.add_product("W1", "Widget 2", 15.0, 5)

    # Negative price
    with pytest.raises(ValueError, match="Unit price cannot be negative"):
        isvc.add_product("W2", "Bad Price", -1.0, 10)

    # Negative starting stock
    with pytest.raises(ValueError, match="Starting stock cannot be negative"):
        isvc.add_product("W3", "Bad Stock", 10.0, -5)

def test_inventory_restock_validations():
    isvc = InventoryService()
    isvc.add_product("W1", "Widget", 10.0, 10)

    # Nonexistent product
    with pytest.raises(ValueError, match="not found"):
        isvc.restock_product("UNKNOWN", 5)

    # Non-positive quantity
    with pytest.raises(ValueError, match="Restock quantity must be greater than zero"):
        isvc.restock_product("W1", 0)

    with pytest.raises(ValueError, match="Restock quantity must be greater than zero"):
        isvc.restock_product("W1", -5)

def test_get_stock_level_nonexistent():
    isvc = InventoryService()
    with pytest.raises(ValueError, match="not found"):
        isvc.get_stock_level("NONEXISTENT")


# ============================================================================
# 3. ORDER SERVICE TESTS
# ============================================================================

def test_order_creation_and_stock_validation():
    cs = CustomerService()
    isvc = InventoryService()
    osvc = OrderService()

    cust = cs.create_customer("Buyer Inc", "buyer@inc.com")
    isvc.add_product("ITEM1", "Gizmo", 10.0, 5)

    # Invalid customer
    with pytest.raises(ValueError, match="not found"):
        osvc.create_order("CUST-9999", [{"sku": "ITEM1", "quantity": 1}])

    # Empty line items
    with pytest.raises(ValueError, match="at least one line item"):
        osvc.create_order(cust.customer_id, [])

    # Invalid quantity (<=0)
    with pytest.raises(ValueError, match="greater than zero"):
        osvc.create_order(cust.customer_id, [{"sku": "ITEM1", "quantity": 0}])

    # Nonexistent SKU in order
    with pytest.raises(ValueError, match="not found"):
        osvc.create_order(cust.customer_id, [{"sku": "BADSKU", "quantity": 1}])

    order = osvc.create_order(cust.customer_id, [{"sku": "ITEM1", "quantity": 3}])
    assert order.status == "Pending"
    assert order.order_id.startswith("ORD-")
    # Stock should not decrement on creation
    assert isvc.get_stock_level("ITEM1") == 5

    # Confirm order -> decrements stock
    osvc.confirm_order(order.order_id)
    assert order.status == "Confirmed"
    assert isvc.get_stock_level("ITEM1") == 2

def test_confirm_order_validations():
    cs = CustomerService()
    isvc = InventoryService()
    osvc = OrderService()

    cust = cs.create_customer("Buyer", "b@b.com")
    isvc.add_product("ITEM1", "Gizmo", 10.0, 2)

    # Nonexistent order
    with pytest.raises(ValueError, match="not found"):
        osvc.confirm_order("ORD-999")

    order = osvc.create_order(cust.customer_id, [{"sku": "ITEM1", "quantity": 5}])
    # Cannot exceed current stock on confirmation
    with pytest.raises(ValueError, match="Insufficient stock"):
        osvc.confirm_order(order.order_id)

    # Confirming already confirmed order
    order2 = osvc.create_order(cust.customer_id, [{"sku": "ITEM1", "quantity": 1}])
    osvc.confirm_order(order2.order_id)
    with pytest.raises(ValueError, match="Only Pending orders can be confirmed"):
        osvc.confirm_order(order2.order_id)

def test_order_cancellation_states_and_stock():
    cs = CustomerService()
    isvc = InventoryService()
    osvc = OrderService()

    cust = cs.create_customer("Cancel LLC", "c@llc.com")
    isvc.add_product("ITEM2", "Gadget", 50.0, 10)

    # Nonexistent order
    with pytest.raises(ValueError, match="not found"):
        osvc.cancel_order("ORD-999")

    # Cancel Pending order (no stock change needed)
    pending_ord = osvc.create_order(cust.customer_id, [{"sku": "ITEM2", "quantity": 3}])
    osvc.cancel_order(pending_ord.order_id)
    assert pending_ord.status == "Cancelled"
    assert isvc.get_stock_level("ITEM2") == 10

    # Cancel Confirmed order (restores stock)
    order = osvc.create_order(cust.customer_id, [{"sku": "ITEM2", "quantity": 4}])
    osvc.confirm_order(order.order_id)
    assert isvc.get_stock_level("ITEM2") == 6

    osvc.cancel_order(order.order_id)
    assert order.status == "Cancelled"
    assert isvc.get_stock_level("ITEM2") == 10

    # Cannot cancel already cancelled order
    with pytest.raises(ValueError, match="already cancelled"):
        osvc.cancel_order(order.order_id)

def test_cancel_invoiced_order_fails():
    cs = CustomerService()
    isvc = InventoryService()
    osvc = OrderService()
    inv_svc = InvoicingService()

    cust = cs.create_customer("Cust", "c@c.com")
    isvc.add_product("ITEM1", "Widget", 10.0, 10)
    order = osvc.create_order(cust.customer_id, [{"sku": "ITEM1", "quantity": 2}])
    osvc.confirm_order(order.order_id)
    inv_svc.generate_invoice(order.order_id)

    with pytest.raises(ValueError, match="Cannot cancel an order that has already been invoiced"):
        osvc.cancel_order(order.order_id)


# ============================================================================
# 4. INVOICING SERVICE TESTS
# ============================================================================

def test_invoicing_and_double_invoicing_prevention():
    cs = CustomerService()
    isvc = InventoryService()
    osvc = OrderService()
    inv_svc = InvoicingService()

    cust = cs.create_customer("Invoice Corp", "i@corp.com")
    isvc.add_product("ITEM3", "Tool", 100.0, 10)

    # Generate invoice for non-existent order
    with pytest.raises(ValueError, match="not found"):
        inv_svc.generate_invoice("ORD-999")

    order = osvc.create_order(cust.customer_id, [{"sku": "ITEM3", "quantity": 2}])
    
    # Generate invoice for Pending order (should fail)
    with pytest.raises(ValueError, match="Order must be Confirmed"):
        inv_svc.generate_invoice(order.order_id)

    osvc.confirm_order(order.order_id)

    invoice = inv_svc.generate_invoice(order.order_id, "US-DEFAULT")
    assert invoice.invoice_id.startswith("INV-")
    assert invoice.subtotal == 200.0
    assert invoice.tax_rate == 0.08
    assert invoice.tax_amount == 16.0
    assert invoice.grand_total == 216.0
    assert invoice.status == "Unpaid"

    # Prevent double invoicing
    with pytest.raises(ValueError, match="already been invoiced"):
        inv_svc.generate_invoice(order.order_id, "US-DEFAULT")

    # Mark as paid with validations
    with pytest.raises(ValueError, match="not found"):
        inv_svc.mark_invoice_paid("INV-999", date(2025, 2, 15))

    p_date = date(2025, 2, 15)
    inv_svc.mark_invoice_paid(invoice.invoice_id, p_date)
    assert invoice.status == "Paid"
    assert invoice.payment_date == p_date

    # Marking paid again should fail
    with pytest.raises(ValueError, match="already marked as paid"):
        inv_svc.mark_invoice_paid(invoice.invoice_id, p_date)

    # Revenue report
    rev = ReportingService().get_revenue_report(date(2025, 1, 1), date(2025, 12, 31))
    assert rev == 216.0

def test_tax_rates_different_regions():
    cs = CustomerService()
    isvc = InventoryService()
    osvc = OrderService()
    inv_svc = InvoicingService()

    cust = cs.create_customer("Tax Test", "t@t.com")
    isvc.add_product("PROD-CA", "CA Item", 100.0, 10)
    isvc.add_product("PROD-NY", "NY Item", 100.0, 10)
    isvc.add_product("PROD-ZERO", "Zero Item", 100.0, 10)

    # CA tax (0.09)
    ord_ca = osvc.create_order(cust.customer_id, [{"sku": "PROD-CA", "quantity": 1}])
    osvc.confirm_order(ord_ca.order_id)
    inv_ca = inv_svc.generate_invoice(ord_ca.order_id, "US-CA")
    assert inv_ca.tax_rate == 0.09
    assert inv_ca.tax_amount == 9.0
    assert inv_ca.grand_total == 109.0

    # NY tax (0.08875) -> rounded to 2 decimals
    ord_ny = osvc.create_order(cust.customer_id, [{"sku": "PROD-NY", "quantity": 1}])
    osvc.confirm_order(ord_ny.order_id)
    inv_ny = inv_svc.generate_invoice(ord_ny.order_id, "US-NY")
    assert inv_ny.tax_rate == 0.08875
    assert inv_ny.tax_amount == 8.88  # 100 * 0.08875 = 8.875 -> 8.88

    # Unknown region defaults to US-DEFAULT (0.08)
    ord_zero = osvc.create_order(cust.customer_id, [{"sku": "PROD-ZERO", "quantity": 1}])
    osvc.confirm_order(ord_zero.order_id)
    inv_zero = inv_svc.generate_invoice(ord_zero.order_id, "UNKNOWN-REGION")
    assert inv_zero.tax_rate == 0.08


# ============================================================================
# 5. REPORTING SERVICE TESTS
# ============================================================================

def test_reporting_service():
    cs = CustomerService()
    isvc = InventoryService()
    osvc = OrderService()
    inv_svc = InvoicingService()
    rep_svc = ReportingService()

    cust = cs.create_customer("Reporter Corp", "r@corp.com")
    
    # Nonexistent customer report
    with pytest.raises(ValueError, match="not found"):
        rep_svc.get_customer_orders_report("CUST-999")

    isvc.add_product("REP-1", "Item A", 50.0, 20)
    
    order = osvc.create_order(cust.customer_id, [{"sku": "REP-1", "quantity": 2}])
    osvc.confirm_order(order.order_id)
    invoice = inv_svc.generate_invoice(order.order_id, "US-DEFAULT")
    inv_svc.mark_invoice_paid(invoice.invoice_id, date(2025, 3, 1))

    # Customer orders report
    cust_report = rep_svc.get_customer_orders_report(cust.customer_id)
    assert len(cust_report) == 1
    assert cust_report[0]["order_id"] == order.order_id
    assert cust_report[0]["status"] == "Invoiced"
    assert cust_report[0]["invoice_id"] == invoice.invoice_id
    assert cust_report[0]["invoice_status"] == "Paid"
    assert cust_report[0]["grand_total"] == 108.0

    # Revenue report filtering by date range
    # Inside range
    assert rep_svc.get_revenue_report(date(2025, 2, 1), date(2025, 3, 31)) == 108.0
    # Outside range (before)
    assert rep_svc.get_revenue_report(date(2025, 1, 1), date(2025, 2, 1)) == 0.0
    # Outside range (after)
    assert rep_svc.get_revenue_report(date(2025, 4, 1), date(2025, 5, 1)) == 0.0

    # Unpaid invoice should not count towards revenue
    order2 = osvc.create_order(cust.customer_id, [{"sku": "REP-1", "quantity": 1}])
    osvc.confirm_order(order2.order_id)
    inv_svc.generate_invoice(order2.order_id, "US-DEFAULT")
    assert rep_svc.get_revenue_report(date(2025, 1, 1), date(2025, 12, 31)) == 108.0
