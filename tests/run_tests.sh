#!/bin/bash
# Modern pytest-based test runner for LLM Vision
# Follows Python testing best practices

set -e

echo "🚀 LLM Vision Test Suite"
echo "========================"
echo ""

# Ensure we're in the project root
cd "$(dirname "$0")/.."

# Check if pytest is available
if ! command -v pytest &> /dev/null; then
    echo "❌ pytest not found. Installing from test requirements..."
    pip install pytest pytest-asyncio
fi

echo "📦 Running Unit Tests (no dependencies required)"
echo "================================================"
pytest tests/unit/ -m unit -v
unit_result=$?

echo ""
echo ""

echo "🔌 Running Integration Tests (requires API keys and venv)"
echo "========================================================="

# Check if virtual environment exists
if [ ! -d "tests/venv" ]; then
    echo "❌ Virtual environment not found. Run 'cd tests && ./setup.sh' first."
    echo "   Skipping integration tests."
    integration_result=1
else
    # Check if secrets file exists
    if [ ! -f "tests/test_secrets.py" ]; then
        echo "❌ tests/test_secrets.py not found."
        echo "   Copy tests/test_secrets.py.template and add your API keys."
        echo "   Skipping integration tests."
        integration_result=1
    else
        # Activate virtual environment and run integration tests
        echo "🔌 Activating virtual environment..."
        source tests/venv/bin/activate
        pytest tests/integration/ -m integration -v
        integration_result=$?
        deactivate
    fi
fi

echo ""
echo "================================================"
echo "Test Results Summary:"
if [ $unit_result -eq 0 ]; then
    echo "  ✅ Unit tests: PASSED"
else
    echo "  ❌ Unit tests: FAILED"
fi

if [ $integration_result -eq 0 ]; then
    echo "  ✅ Integration tests: PASSED"
elif [ $integration_result -eq 1 ] && ([ ! -d "tests/venv" ] || [ ! -f "tests/test_secrets.py" ]); then
    echo "  ⚠️  Integration tests: SKIPPED (missing setup)"
else
    echo "  ❌ Integration tests: FAILED"
fi

echo ""
if [ $unit_result -eq 0 ] && [ $integration_result -eq 0 ]; then
    echo "🎉 All tests passed!"
    exit 0
else
    echo "💥 Some tests failed or were skipped!"
    exit 1
fi