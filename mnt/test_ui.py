import pytest
from tiny_erp.ui import create_ui

def test_ui_construction():
    """Validate that the Gradio Blocks UI constructs without error."""
    demo = create_ui()
    assert demo is not None
    # Confirm it has blocks or is a Blocks instance
    assert hasattr(demo, "launch")
