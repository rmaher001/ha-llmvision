# Structured Output Integration Testing

## Overview
This document describes the integration test created to validate the Phase 1 structured output implementation in `providers.py`.

## What This Test Does
The `test_structured_output_integration.py` test validates that your Phase 1 structured output implementation works correctly by:

1. **Testing Real Provider Code**: Uses actual provider classes (OpenAI, Anthropic, Google) from your integration
2. **Making Real API Calls**: Uses real aiohttp sessions to make actual HTTP requests to LLM APIs
3. **Validating Structured Responses**: Tests that the JSON schema enforcement works end-to-end
4. **Bypassing Mocks**: No mocking - tests the actual implementation you built

## Key Features

### Real Integration Testing
- Creates provider instances directly: `OpenAI(hass=hass, api_key=api_key, model="gpt-4o-mini")`
- Uses real aiohttp sessions for HTTP requests
- Tests the actual `supports_structured_output()` methods
- Validates the `call.response_format = "json"` and `call.structure` parameters

### Provider-Specific Testing
- **OpenAI**: Tests `json_schema` format with `strict: True` mode
- **Anthropic**: Tests tool-based structured output approach  
- **Google**: Tests `response_json_schema` in generationConfig
- **Ollama**: Tests `format` parameter for structured output

### Schema Validation
Tests a realistic color analysis schema:
```json
{
  "type": "object",
  "properties": {
    "dominant_color": {"type": "string"},
    "confidence": {"type": "number", "minimum": 0, "maximum": 100},
    "is_single_color": {"type": "boolean"}
  },
  "required": ["dominant_color", "confidence", "is_single_color"],
  "additionalProperties": false
}
```

## Running the Tests

### Prerequisites
1. **API Keys**: Set environment variables in `~/.zshrc`:
   ```bash
   export OPENAI_API_KEY="your-openai-api-key"
   export ANTHROPIC_API_KEY="your-anthropic-api-key" 
   export GOOGLE_API_KEY="your-google-api-key"
   ```

2. **Ollama**: Ensure Ollama is running locally:
   ```bash
   ollama serve  # Default: localhost:11434
   ollama pull llava  # Pull the vision model
   ```

3. **Load Environment**: 
   ```bash
   source ~/.zshrc  # Load API keys
   ```

### Option 1: Individual Provider Tests
```bash
cd /Users/richard/ha/ha-llmvision
source ~/.zshrc && source tests/venv/bin/activate
python tests/integration/test_structured_output_integration.py openai
python tests/integration/test_structured_output_integration.py anthropic
python tests/integration/test_structured_output_integration.py google
python tests/integration/test_structured_output_integration.py ollama
```

### Option 2: Automated Test Runner
```bash
cd /Users/richard/ha/ha-llmvision
source ~/.zshrc && ./tests/run_structured_output_test.sh            # Test all providers  
source ~/.zshrc && ./tests/run_structured_output_test.sh openai     # Test specific provider
```

**Note**: Always source `~/.zshrc` first to load API keys into the session.

## What Gets Validated

### 1. Provider Support Detection
```python
assert provider_instance.supports_structured_output(), "Provider should support structured output"
```

### 2. Structured Response Format
Tests that the provider returns a response containing `response_text` with valid JSON:
```python
structured_data = json.loads(response["response_text"])
```

### 3. Schema Compliance
Validates that the response matches the requested schema:
```python
assert "dominant_color" in structured_data
assert isinstance(structured_data["confidence"], (int, float))
assert 0 <= structured_data["confidence"] <= 100
```

### 4. Content Validation
Tests that the AI actually analyzed the test image (red colored):
```python
assert "red" in structured_data["dominant_color"].lower()
```

## Test Output Examples

### Google Gemini
```
🧪 Testing Google structured output via provider implementation...
✅ Provider response: {'structured_response': {'dominant_color': 'red', 'confidence': 1.0, 'is_single_color': True}, 'response_text': '{"dominant_color": "red", "confidence": 1.0, "is_single_color": true}'}
✅ Google structured output integration test passed!
```

### OpenAI GPT-4o-mini
```
🧪 Testing OpenAI structured output via provider implementation...
✅ Provider response: {'structured_response': {'dominant_color': 'red', 'confidence': 1.0, 'is_single_color': True}, 'response_text': '{"dominant_color":"red","confidence":1.0,"is_single_color":true}'}
✅ OpenAI structured output integration test passed!
```

### Anthropic Claude
```
🧪 Testing Anthropic structured output via provider implementation...
✅ Provider response: {'structured_response': {'dominant_color': 'red', 'confidence': 100, 'is_single_color': True}, 'response_text': '{"dominant_color": "red", "confidence": 100, "is_single_color": true}'}
✅ Anthropic structured output integration test passed!
```

### Ollama Llava
```
🧪 Testing Ollama structured output via provider implementation...
✅ Provider response: {'structured_response': {'dominant_color': 'red', 'confidence': 100, 'is_single_color': True}, 'response_text': '{"dominant_color": "red", "confidence": 100, "is_single_color": true} '}
✅ Ollama structured output integration test passed!
```

## Why This Test Matters

### Addresses the Gap
Your existing tests had this issue from `RECOVERY_PLAN.md`:
> ❌ Tests still use MockCall objects instead of real service calls
> ❌ Direct API tests fail with 400 errors on all providers
> ❌ No validation that structured output actually works in Home Assistant
> ❌ Tests bypass the actual integration code entirely

### This Test Fixes That
- ✅ Uses real provider instances from your integration
- ✅ Makes successful API calls (no 400 errors)
- ✅ Validates structured output works through your implementation
- ✅ Tests the actual integration code paths

## Integration with Existing Test Suite

The test is designed to work with your existing test infrastructure:
- Uses the same virtual environment (`tests/venv/`)
- Loads API keys from `tests/test_secrets.py`
- Follows the same pytest patterns as your other tests
- Can be run standalone or integrated with pytest

## Next Steps

1. **Set API Keys**: Add API keys to `~/.zshrc` environment variables
2. **Start Ollama**: Run `ollama serve` and `ollama pull llava` for local testing
3. **Run Tests**: Execute `source ~/.zshrc && ./tests/run_structured_output_test.sh`  
4. **Validate Results**: Confirm all four providers pass structured output tests
5. **Integration Complete**: Your Phase 1 implementation is validated end-to-end

## Validation Status: ✅ COMPLETE

All four providers have been successfully tested and validated:

- ✅ **OpenAI GPT-4o-mini**: Structured output via JSON Schema (strict mode)
- ✅ **Anthropic Claude**: Structured output via tools approach
- ✅ **Google Gemini**: Structured output via response_json_schema  
- ✅ **Ollama Llava**: Structured output via format parameter

This test suite proves that your structured output implementation in `providers.py` works correctly with real LLM APIs and returns properly formatted JSON responses matching the requested schemas.