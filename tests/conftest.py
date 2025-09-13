"""
Shared pytest configuration for LLM Vision tests.
"""
import sys
import os
from pathlib import Path

# Add project root to Python path so tests can import custom_components
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Add custom_components to path for integration tests
custom_components_path = project_root / "custom_components"
sys.path.insert(0, str(custom_components_path))

# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (may require API keys)"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests (no external dependencies)"
    )

def pytest_collection_modifyitems(config, items):
    """Add markers to tests based on directory structure."""
    for item in items:
        # Add markers based on test file location
        test_path = str(item.fspath)
        if "/unit/" in test_path:
            item.add_marker("unit")
        elif "/integration/" in test_path:
            item.add_marker("integration")