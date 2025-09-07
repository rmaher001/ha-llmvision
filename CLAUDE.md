# CLAUDE.md - LLM Vision Integration

This file provides guidance to Claude Code (claude.ai/code) when working with the LLM Vision Home Assistant custom integration.

## Project Overview

Home Assistant custom integration for AI-powered image/video analysis using multiple LLM providers. This is the debug version that runs alongside the production version with comprehensive logging.

**Key directories:**
- `custom_components/llmvision/` - Main integration code
- `blueprints/` - Home Assistant automation blueprints
- `benchmark_visualization/` - Performance analysis tools
- `tests/` - Comprehensive test suite including structured output validation

## Development Commands

### LLM Vision Integration
No build process required - Home Assistant loads custom components directly.

**Installation:**
1. Copy `custom_components/llmvision/` to Home Assistant's `custom_components/` directory
2. Restart Home Assistant
3. Add integration via Settings > Devices & Services

**Testing Structured Output:**
```bash
cd ha-llmvision
source ~/.zshrc  # Load API keys
source tests/venv/bin/activate
python tests/integration/test_structured_output_integration.py [openai|anthropic|google|ollama]
```

**Debug Logging:**
Enable in Home Assistant configuration.yaml:
```yaml
logger:
  default: info
  logs:
    custom_components.llmvision: debug
```

## Architecture

### Provider Abstraction Pattern
- Supports OpenAI, Anthropic, Google, AWS Bedrock, Groq, Ollama, LocalAI, OpenWebUI
- **✅ Phase 1: Structured JSON Output** - Implemented and validated across all providers using JSON Schema enforcement
- Service-oriented architecture with 5 main services: image_analyzer, video_analyzer, stream_analyzer, data_analyzer, remember
- Memory system for persistent context across calls
- Timeline/calendar integration for event storage
- Comprehensive LLM call logging to `/config/www/llmvision/logs/`

### Structured Output Implementation
**Status: ✅ COMPLETE** - All providers support structured JSON responses via different mechanisms:
- **OpenAI**: JSON Schema with `strict: true` mode
- **Anthropic**: Tool-based structured output approach
- **Google**: `response_json_schema` in generationConfig
- **Ollama**: `format` parameter for structured output

**Testing**: Comprehensive integration tests validate real API calls with schema enforcement. See `tests/README_STRUCTURED_OUTPUT_TESTING.md` for details.

### Service Architecture
- **image_analyzer**: Single image analysis with structured output support
- **video_analyzer**: Video frame extraction and analysis
- **stream_analyzer**: Real-time camera stream processing
- **data_analyzer**: Text/data analysis without vision
- **remember**: Memory management and event storage

### Memory System
- Persistent context across service calls
- Image memory with configurable retention
- Timeline integration for Home Assistant calendar
- Automatic cleanup and rotation

## Testing

### Prerequisites
Set API keys in `~/.zshrc`:
```bash
export OPENAI_API_KEY="your-openai-api-key"
export ANTHROPIC_API_KEY="your-anthropic-api-key" 
export GOOGLE_API_KEY="your-google-api-key"
```

For Ollama testing:
```bash
ollama serve  # Default: localhost:11434
ollama pull llava  # Pull vision model
```

### Running Tests
```bash
# Individual provider tests
source ~/.zshrc && source tests/venv/bin/activate
python tests/integration/test_structured_output_integration.py openai
python tests/integration/test_structured_output_integration.py anthropic
python tests/integration/test_structured_output_integration.py google
python tests/integration/test_structured_output_integration.py ollama

# All providers
source ~/.zshrc && ./tests/run_structured_output_test.sh
```

## Important Notes

- No traditional package managers - dependencies declared in manifest.json
- All components use Home Assistant's async patterns
- Debug version can run side-by-side with production version
- Comprehensive logging available for debugging
- Each provider has unique structured output implementation
- Integration tests validate against real LLM APIs

## File Structure

```
ha-llmvision/
├── custom_components/llmvision/
│   ├── __init__.py              # Integration setup
│   ├── providers.py             # LLM provider implementations
│   ├── const.py                 # Constants and configuration
│   ├── services.py              # Service implementations
│   ├── memory.py                # Memory system
│   └── manifest.json            # Integration metadata
├── tests/
│   ├── integration/
│   │   └── test_structured_output_integration.py
│   ├── README_STRUCTURED_OUTPUT_TESTING.md
│   └── run_structured_output_test.sh
└── CLAUDE.md                    # This file
```