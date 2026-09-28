import gradio as gr
from datetime import date
from typing import List, Tuple

from tiny_erp.services import (
    CustomerService,
    InventoryService,
    OrderService,
    InvoicingService,
    ReportingService
)

customer_svc = CustomerService()
inventory_svc = InventoryService()
order_svc = OrderService()
invoicing_svc = InvoicingService()
reporting_svc = ReportingService()

CUSTOM_CSS = """
:root {
    --primary-color: #0f172a;
    --accent-color: #3b82f6;
    --bg-color: #f8fafc;
    --card-bg: #ffffff;
    --border-color: #e2e8f0;
    --text-color: #1e293b;
    --text-muted: #64748b;
    --success-color: #10b981;
}

body {
    background-color: var(--bg-color);
    color: var(--text-color);
    font-family: 'Inter', system-ui, -apple-system, sans-serif;
}

.gradio-container {
    max-width: 1280px !important;
    margin: auto;
    padding: 2rem 1rem;
}

h1, h2, h3 {
    color: var(--primary-color);
    font-weight: 700;
}

.erp-header {
    background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%);
    color: white;
    padding: 2rem;
    border-radius: 12px;
    margin-bottom: 2rem;
    box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
}

.erp-header h1 {
    color: white;
    margin-bottom: 0.5rem;
    font-size: 2.25rem;
}

.erp-header p {
    color: #93c5fd;
    font-size: 1.1rem;
    margin: 0;
}

.gr-button-primary {
    background-color: #2563eb !important;
    border-color: #2563eb !important;
    color: white !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    transition: all 0.2s ease !important;
}

.gr-button-primary:hover {
    background-color: #1d4ed8 !important;
}

.tab-nav {
    border-bottom: 2px solid var(--border-color);
    margin-bottom: 1.5rem;
}

.card {
    background: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 10px;
    padding: 1.5rem;
    box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.05);
}
"""

def create_ui():
    with gr.Blocks(css=CUSTOM_CSS, title="Tiny ERP System") as demo:
        
        # Header
        gr.HTML("""
            <div class="erp-header">
                <h1>Tiny ERP System</h1>
                <p>Streamlined inventory, customer management, orders, invoicing, and real-time business reporting.</p>
            </div>
        """)

        with gr.Tabs():
            
            # ----------------------------------------------------
            # TAB 1: CUSTOMERS
            # ----------------------------------------------------
            with gr.TabItem("Customers"):
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("### Create New Customer")
                        cust_name = gr.Textbox(label="Customer Name", placeholder="e.g. Acme Corp")
                        cust_contact = gr.Textbox(label="Contact Info", placeholder="e.g. contact@acme.com / 555-0199")
                        cust_create_btn = gr.Button("Create Customer", variant="primary")
                        cust_create_output = gr.Textbox(label="Status / Result", interactive=False)
                        
                        cust_create_btn.click(
                            fn=lambda n, c: f"Success! Created Customer: {customer_svc.create_customer(n, c)}" if n.strip() else "Error: Name cannot be empty.",
                            inputs=[cust_name, cust_contact],
                            outputs=[cust_create_output]
                        )
                    
                    with gr.Column(scale=2):
                        gr.Markdown("### Customer Directory & Lookup")
                        with gr.Row():
                            lookup_id = gr.Textbox(label="Customer ID Lookup", placeholder="e.g. CUST-1001")
                            lookup_btn = gr.Button("Lookup")
                        lookup_output = gr.JSON(label="Customer Details")
                        
                        lookup_btn.click(
                            fn=lambda cid: customer_svc.get_customer(cid.strip()) or {"error": "Customer not found"},
                            inputs=[lookup_id],
                            outputs=[lookup_output]
                        )
                        
                        gr.Markdown("#### All Customers")
                        list_cust_btn = gr.Button("Refresh Customer List")
                        cust_table = gr.Dataframe(
                            headers=["Customer ID", "Name", "Contact Info", "Created At"],
                            datatype=["str", "str", "str", "str"],
                            interactive=False
                        )
                        
                        def refresh_customers():
                            customers = customer_svc.list_customers()
                            return [[c.customer_id, c.name, c.contact_info, str(c.created_at)] for c in customers]
                        
                        list_cust_btn.click(fn=refresh_customers, outputs=[cust_table])

            # ----------------------------------------------------
            # TAB 2: INVENTORY
            # ----------------------------------------------------
            with gr.TabItem("Inventory"):
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("### Add New Product")
                        prod_sku = gr.Textbox(label="SKU", placeholder="e.g. WIDGET-01")
                        prod_name = gr.Textbox(label="Product Name", placeholder="e.g. Premium Widget")
                        prod_price = gr.Number(label="Unit Price ($)", value=10.0, minimum=0.0)
                        prod_stock = gr.Number(label="Starting Stock Quantity", value=50, minimum=0, precision=0)
                        prod_add_btn = gr.Button("Add Product", variant="primary")
                        prod_add_output = gr.Textbox(label="Status", interactive=False)
                        
                        def handle_add_product(sku, name, price, stock):
                            try:
                                prod = inventory_svc.add_product(sku, name, float(price), int(stock))
                                return f"Success! Added product {prod.sku} - {prod.name} (Stock: {prod.stock_quantity})"
                            except Exception as e:
                                return f"Error: {str(e)}"
                                
                        prod_add_btn.click(
                            fn=handle_add_product,
                            inputs=[prod_sku, prod_name, prod_price, prod_stock],
                            outputs=[prod_add_output]
                        )

                        gr.Markdown("### Restock Product")
                        restock_sku = gr.Textbox(label="Product SKU", placeholder="e.g. WIDGET-01")
                        restock_qty = gr.Number(label="Quantity to Add", value=10, minimum=1, precision=0)
                        restock_btn = gr.Button("Restock Product")
                        restock_output = gr.Textbox(label="Status", interactive=False)

                        def handle_restock(sku, qty):
                            try:
                                prod = inventory_svc.restock_product(sku, int(qty))
                                return f"Success! Restocked {prod.sku}. New stock level: {prod.stock_quantity}"
                            except Exception as e:
                                return f"Error: {str(e)}"

                        restock_btn.click(
                            fn=handle_restock,
                            inputs=[restock_sku, restock_qty],
                            outputs=[restock_output]
                        )

                    with gr.Column(scale=2):
                        gr.Markdown("### Product Catalog & Stock Levels")
                        refresh_inv_btn = gr.Button("Refresh Inventory Catalog")
                        inv_table = gr.Dataframe(
                            headers=["SKU", "Product Name", "Unit Price ($)", "Stock Quantity", "Valuation ($)"],
                            datatype=["str", "str", "number", "number", "number"],
                            interactive=False
                        )

                        def refresh_inventory():
                            products = inventory_svc.list_products()
                            return [[p.sku, p.name, p.unit_price, p.stock_quantity, round(p.stock_quantity * p.unit_price, 2)] for p in products]

                        refresh_inv_btn.click(fn=refresh_inventory, outputs=[inv_table])

            # ----------------------------------------------------
            # TAB 3: ORDERS & INVOICING
            # ----------------------------------------------------
            with gr.TabItem("Orders & Invoicing"):
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("### 1. Create Order")
                        order_cust_id = gr.Textbox(label="Customer ID", placeholder="e.g. CUST-1001")
                        gr.Markdown("Enter Order Line Items (SKU:Quantity, separated by commas or newlines e.g. WIDGET-01:2, GADGET-02:1)")
                        line_items_input = gr.Textbox(label="Line Items", value="WIDGET-01:2", lines=3)
                        create_order_btn = gr.Button("Create Order", variant="primary")
                        order_create_output = gr.Textbox(label="Result / Order ID", interactive=False)

                        def handle_create_order(cust_id, items_str):
                            try:
                                items = []
                                for part in items_str.replace("\n", ",").split(","):
                                    if not part.strip():
                                        continue
                                    if ":" not in part:
                                        return f"Error: Invalid line item format '{part}'. Use SKU:Quantity"
                                    sku, qty = part.split(":")
                                    items.append({"sku": sku.strip(), "quantity": int(qty.strip())})
                                
                                order = order_svc.create_order(cust_id.strip(), items)
                                return f"Success! Created Order ID: {order.order_id} (Status: {order.status})"
                            except Exception as e:
                                return f"Error: {str(e)}"

                        create_order_btn.click(
                            fn=handle_create_order,
                            inputs=[order_cust_id, line_items_input],
                            outputs=[order_create_output]
                        )

                        gr.Markdown("### 2. Order Actions (Confirm / Cancel)")
                        action_order_id = gr.Textbox(label="Order ID", placeholder="e.g. ORD-1001")
                        with gr.Row():
                            confirm_btn = gr.Button("Confirm Order", variant="primary")
                            cancel_btn = gr.Button("Cancel Order", variant="stop")
                        action_output = gr.Textbox(label="Action Result", interactive=False)

                        confirm_btn.click(
                            fn=lambda oid: f"Success! Confirmed {oid}. Stock decremented." if order_svc.confirm_order(oid.strip()) else "",
                            inputs=[action_order_id],
                            outputs=[action_output]
                        )
                        cancel_btn.click(
                            fn=lambda oid: f"Success! Cancelled {oid}. Stock restored if previously confirmed." if order_svc.cancel_order(oid.strip()) else "",
                            inputs=[action_order_id],
                            outputs=[action_output]
                        )

                        gr.Markdown("### 3. Invoicing & Payment")
                        inv_order_id = gr.Textbox(label="Confirmed Order ID", placeholder="e.g. ORD-1001")
                        inv_region = gr.Textbox(label="Region (for tax)", value="US-DEFAULT")
                        generate_inv_btn = gr.Button("Generate Invoice", variant="primary")
                        invoice_output = gr.Textbox(label="Invoice Result", interactive=False)

                        generate_inv_btn.click(
                            fn=lambda oid, reg: f"Success! Generated Invoice: {invoicing_svc.generate_invoice(oid.strip(), reg.strip())}" if invoicing_svc.generate_invoice(oid.strip(), reg.strip()) else "",
                            inputs=[inv_order_id, inv_region],
                            outputs=[invoice_output]
                        )

                        pay_invoice_id = gr.Textbox(label="Invoice ID to Pay", placeholder="e.g. INV-1001")
                        pay_date_input = gr.Textbox(label="Payment Date (YYYY-MM-DD)", value=str(date.today()))
                        pay_btn = gr.Button("Mark Invoice as Paid", variant="primary")
                        pay_output = gr.Textbox(label="Payment Result", interactive=False)

                        def handle_pay(inv_id, p_date_str):
                            try:
                                p_date = date.fromisoformat(p_date_str.strip())
                                inv = invoicing_svc.mark_invoice_paid(inv_id.strip(), p_date)
                                return f"Success! Invoice {inv.invoice_id} marked as Paid on {inv.payment_date}."
                            except Exception as e:
                                return f"Error: {str(e)}"

                        pay_btn.click(
                            fn=handle_pay,
                            inputs=[pay_invoice_id, pay_date_input],
                            outputs=[pay_output]
                        )

                    with gr.Column(scale=2):
                        gr.Markdown("### All Orders & Invoices Overview")
                        refresh_orders_btn = gr.Button("Refresh Orders & Invoices")
                        orders_table = gr.Dataframe(
                            headers=["Order ID", "Customer ID", "Status", "Items", "Invoice ID", "Inv Status", "Grand Total ($)"],
                            datatype=["str", "str", "str", "str", "str", "str", "number"],
                            interactive=False
                        )

                        def refresh_all_orders():
                            orders = order_svc.list_orders()
                            rows = []
                            for o in orders:
                                inv = invoicing_svc.get_invoice_by_order(o.order_id)
                                items_str = ", ".join([f"{i.sku}x{i.quantity}" for i in o.line_items])
                                rows.append([
                                    o.order_id,
                                    o.customer_id,
                                    o.status,
                                    items_str,
                                    inv.invoice_id if inv else "None",
                                    inv.status if inv else "N/A",
                                    inv.grand_total if inv else 0.0
                                ])
                            return rows

                        refresh_orders_btn.click(fn=refresh_all_orders, outputs=[orders_table])

            # ----------------------------------------------------
            # TAB 4: REPORTING & ANALYTICS
            # ----------------------------------------------------
            with gr.TabItem("Reporting & Analytics"):
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("### Customer Order History Report")
                        rep_cust_id = gr.Textbox(label="Customer ID", placeholder="e.g. CUST-1001")
                        rep_cust_btn = gr.Button("Generate Customer Report")
                        rep_cust_output = gr.JSON(label="Customer Orders & Status")

                        rep_cust_btn.click(
                            fn=lambda cid: reporting_svc.get_customer_orders_report(cid.strip()),
                            inputs=[rep_cust_id],
                            outputs=[rep_cust_output]
                        )

                    with gr.Column():
                        gr.Markdown("### Revenue Recognized Report")
                        rev_start = gr.Textbox(label="Start Date (YYYY-MM-DD)", value="2025-01-01")
                        rev_end = gr.Textbox(label="End Date (YYYY-MM-DD)", value=str(date.today()))
                        rev_btn = gr.Button("Calculate Revenue")
                        rev_output = gr.Number(label="Total Recognized Revenue ($)")

                        def handle_revenue(start_str, end_str):
                            try:
                                s = date.fromisoformat(start_str.strip())
                                e = date.fromisoformat(end_str.strip())
                                return reporting_svc.get_revenue_report(s, e)
                            except Exception as ex:
                                return 0.0

                        rev_btn.click(
                            fn=handle_revenue,
                            inputs=[rev_start, rev_end],
                            outputs=[rev_output]
                        )

                        gr.Markdown("### Current Inventory Valuation")
                        val_btn = gr.Button("Calculate Valuation")
                        val_output = gr.Number(label="Total Inventory Valuation ($)")

                        val_btn.click(
                            fn=lambda: reporting_svc.get_inventory_valuation(),
                            outputs=[val_output]
                        )

    return demo

if __name__ == "__main__":
    demo = create_ui()
    demo.launch()
