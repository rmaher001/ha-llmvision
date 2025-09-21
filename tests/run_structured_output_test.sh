#!/bin/bash

echo "🧪 Running Structured Output Integration Tests for ALL 8 Providers"
echo "=================================================================="

source ~/.zshrc
source tests/venv/bin/activate

providers=("openai" "anthropic" "google" "bedrock" "azureopenai" "groq" "localai" "ollama")

passed=0
failed=0
skipped=0

for provider in "${providers[@]}"; do
    echo ""
    echo "Testing $provider..."
    output=$(python tests/integration/test_structured_output_integration.py $provider 2>&1)
    
    if echo "$output" | grep -q "✅.*passed!"; then
        echo "$output" | grep "✅"
        ((passed++))
    elif echo "$output" | grep -q "Skipping"; then
        echo "⏭️  Skipped: $provider (not configured)"
        ((skipped++))
    else
        echo "$output"
        ((failed++))
    fi
done

echo ""
echo "======================================="
echo "Test Summary:"
echo "  ✅ Passed: $passed"
echo "  ❌ Failed: $failed"
echo "  ⏭️  Skipped: $skipped"
echo "  📊 Total: 8"
echo "======================================="
