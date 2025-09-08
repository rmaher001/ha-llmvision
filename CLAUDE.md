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
**Status: ✅ COMPLETE** - All services now support structured JSON responses:
- **image_analyzer**: ✅ Single image analysis with structured output
- **stream_analyzer**: ✅ Multi-camera stream analysis with structured output  
- **video_analyzer**: ✅ Video frame analysis with structured output

**Provider Support** - All providers support structured JSON via different mechanisms:
- **OpenAI**: JSON Schema with `strict: true` mode
- **Anthropic**: Tool-based structured output approach
- **Google**: `response_json_schema` in generationConfig
- **Ollama**: `format` parameter for structured output

**Testing**: Comprehensive integration tests validate real API calls with schema enforcement. See `tests/README_STRUCTURED_OUTPUT_TESTING.md` for details.

### Using Structured Output in Automations

**How It Works:**
1. Set `response_format: json` and provide a JSON `structure` schema
2. LLM returns raw JSON string matching the schema
3. LLM Vision parses this into `response.structured_response` object
4. Access fields directly: `{{ response.structured_response.field_name }}`

**Response Structure:**
```yaml
response:
  title: "Event Detected"                    # Generated title
  structured_response:                       # Parsed JSON object
    people_count: 0
    objects_detected: ["plant", "grill"] 
    activity_level: "low"
    scene_description: "Front porch view..."
  response_text: "{ ... }"                   # Raw JSON string (for debugging)
  key_frame: "/path/to/image.jpg"           # Selected frame path
```

**Automation Usage Examples:**
```yaml
# Condition based on structured data
- condition: template
  value_template: "{{ response.structured_response.people_count > 0 }}"

# Use in notifications  
- service: notify.mobile_app
  data:
    message: "Detected {{ response.structured_response.objects_detected | length }} objects"

# Loop through detected objects
- service: script.process_objects
  data:
    objects: "{{ response.structured_response.objects_detected }}"

# Access individual fields
- service: input_number.set_value
  target:
    entity_id: input_number.people_count
  data:
    value: "{{ response.structured_response.people_count }}"
```

**Comparison with Raw JSON:**
```yaml
# With structured output (clean)
{{ response.structured_response.people_count }}

# Without structured output (requires JSON parsing)
{{ (response.response_text | from_json).people_count }}
```

The structured approach eliminates the need for JSON parsing filters and provides direct field access in automations.

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