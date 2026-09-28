#!/usr/bin/env python
import sys
import warnings
from datetime import datetime
from engineering_crew.crew import EngineeringCrew
from .tools.sandbox_tools import start_sandbox, stop_sandbox

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

requirements = """
A tiny ERP system for a small business that sells physical products to customers.

Customers:
- The system should allow creating a customer record with a name and contact info.
- The system should allow listing all customers and looking up a single customer by ID.

Inventory:
- The system should allow adding a product to inventory with a SKU, name, unit price, and
  starting stock quantity.
- The system should allow restocking an existing product (increasing quantity on hand).
- The system should be able to report current stock level for any product at any point in time.

Orders:
- The system should allow creating an order for a customer containing one or more line items
  (product + quantity).
- The system must reject an order, or an individual line item, if the requested quantity
  exceeds current stock for that product - it must not allow stock to go negative.
- Placing an order must decrement stock for each product in the order at the moment the order
  is confirmed, not before.
- The system should allow cancelling an order that has not yet been invoiced, which must
  restore the stock quantities it had reserved.

Invoicing:
- The system should allow generating an invoice from a confirmed order, computing a line-item
  subtotal, a flat-rate tax of 8%, and a grand total.
- An order can only be invoiced once - the system must prevent double-invoicing the same order.
- The system should allow marking an invoice as paid, and record the payment date.
- Tax rate is obtained via a plain function get_tax_rate(region), living in backend business
  logic (not a tool, not an external service call) - it takes a region string and returns a
  float rate. The initial implementation is a stub returning a fixed 8% for every region;
  invoicing must call this function rather than hardcoding the rate, so it can later be
  swapped for a real rate lookup without changing invoicing logic.

Reporting:
- The system should be able to report all orders (and their status: pending, confirmed,
  cancelled, invoiced, paid) for a given customer at any point in time.
- The system should be able to report total revenue recognized (sum of paid invoices) over
  a given date range.
- The system should be able to report current inventory valuation (stock quantity x unit
  price, summed across all products) at any point in time.

User Interface:
- The system must have a Gradio-based UI as the primary way a user interacts with it - not a
  CLI, not a bare script. Every capability above (customers, inventory, orders, invoicing,
  reporting) must be reachable through it.
- The UI must be visually polished, not a default-styled Gradio app: custom CSS, a deliberate
  color palette and typography, clear layout/spacing, and a cohesive visual identity - this is
  a real design requirement, not an afterthought.
- Third-party libraries are allowed and encouraged where they genuinely improve the system
  (UI, testing, data validation, etc.) - engineers are not restricted to the standard library
  except where a specific engineer's constraints say otherwise in the design.
"""

def run():
    """
    Run the crew.
    """
    inputs = {
        'requirements': requirements,
        'current_year': str(datetime.now().year)
    }

    start_sandbox()
    
    try:
        EngineeringCrew().crew().kickoff(inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")

    finally:
        stop_sandbox()

def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = {
        "topic": "AI LLMs",
        'current_year': str(datetime.now().year)
    }
    try:
        EngineeringCrew().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")

def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        EngineeringCrew().crew().replay(task_id=sys.argv[1])

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")

def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = {
        "topic": "AI LLMs",
        "current_year": str(datetime.now().year)
    }

    try:
        EngineeringCrew().crew().test(n_iterations=int(sys.argv[1]), eval_llm=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")

def run_with_trigger():
    """
    Run the crew with trigger payload.
    """
    import json

    if len(sys.argv) < 2:
        raise Exception("No trigger payload provided. Please provide JSON payload as argument.")

    try:
        trigger_payload = json.loads(sys.argv[1])
    except json.JSONDecodeError:
        raise Exception("Invalid JSON payload provided as argument")

    inputs = {
        "crewai_trigger_payload": trigger_payload,
        "topic": "",
        "current_year": ""
    }

    try:
        result = EngineeringCrew().crew().kickoff(inputs=inputs)
        return result
    except Exception as e:
        raise Exception(f"An error occurred while running the crew with trigger: {e}")
