#!/usr/bin/env python3
"""
Test Ollama structured output integration.
Note: This test requires a running Ollama instance with vision-capable models.
"""

import sys
import os
import json
import asyncio
import tempfile
import base64
import aiohttp
import pytest

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Set up the custom_components path
custom_components_path = os.path.join(project_root, 'custom_components')
sys.path.insert(0, custom_components_path)

# Now we can import the integration as a package
from custom_components.llmvision_debug import const
from custom_components.llmvision_debug.providers import Ollama

# Import configuration from secrets
try:
    from test_secrets import OLLAMA_BASE_URL
    # Parse OLLAMA_BASE_URL into endpoint format
    import urllib.parse
    parsed = urllib.parse.urlparse(OLLAMA_BASE_URL)
    OLLAMA_ENDPOINT = {
        "ip_address": parsed.hostname or "localhost",
        "port": str(parsed.port or 11434),
        "https": parsed.scheme == "https"
    }
except ImportError:
    print("❌ Please create tests/test_secrets.py from tests/test_secrets.py.template")
    sys.exit(1)

# Load test_image.png from project directory
def load_test_image():
    """Load test_image.png and convert to base64"""
    from PIL import Image
    import io
    import base64
    
    # Load the test image
    test_image_path = os.path.join(os.path.dirname(__file__), 'test_image.png')
    img = Image.open(test_image_path)
    
    # Convert to RGB if needed
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return base64.b64encode(buffer.getvalue()).decode('utf-8')

TEST_IMAGE_BASE64 = load_test_image()

# Test schema for structured output
TEST_SCHEMA = {
    "type": "object",
    "properties": {
        "color_detected": {
            "type": "boolean",
            "description": "Whether any color is detected in the image"
        },
        "dominant_color": {
            "type": "string",
            "description": "The dominant color name"
        },
        "confidence": {
            "type": "number",
            "minimum": 0,
            "maximum": 100,
            "description": "Confidence level 0-100"
        }
    },
    "required": ["color_detected", "confidence", "dominant_color"]
}

class MockCall:
    """Mock service call for testing."""
    def __init__(self, response_format="text", structure=None):
        self.response_format = response_format
        self.structure = structure
        self.base64_images = [TEST_IMAGE_BASE64]
        self.filenames = ["test_image.png"]
        self.message = "What is the dominant color in this image?"
        self.max_tokens = 100
        self.use_memory = False

@pytest.mark.asyncio
async def test_ollama_integration():
    """Test Ollama integration with structured output."""
    
    print("🚀 Running Ollama Structured Output Integration Test")
    print("=" * 60)
    print("Note: This requires a running Ollama instance with vision-capable models")
    print()
    
    # Create shared aiohttp session for all tests
    session = aiohttp.ClientSession()
    
    # Mock the async_get_clientsession function globally
    def mock_get_clientsession(hass):
        return session
    
    # Monkey patch the import
    import custom_components.llmvision_debug.providers as providers_module
    original_get_clientsession = providers_module.async_get_clientsession
    providers_module.async_get_clientsession = mock_get_clientsession
    
    # Test 1: Provider creation
    print("1. Testing provider creation...")
    try:
        # Create a simple mock hass object
        class MockHass:
            def __init__(self):
                self.data = {const.DOMAIN: {}}
        
        mock_hass = MockHass()
        provider = Ollama(mock_hass, "", "PetrosStav/gemma3-tools:12b", OLLAMA_ENDPOINT)
        print("   ✓ Ollama provider created successfully")
    except Exception as e:
        print(f"   ✗ Failed to create provider: {e}")
        await session.close()
        return False
    
    # Test 2: Structured output support detection
    print("2. Testing structured output support...")
    try:
        supports = provider.supports_structured_output()
        if supports:
            print("   ✓ Ollama reports structured output support")
        else:
            print("   ✗ Ollama should support structured output")
            return False
    except Exception as e:
        print(f"   ✗ Error checking support: {e}")
        return False
    
    # Test 3: Text mode payload (backward compatibility)
    print("3. Testing text mode payload generation...")
    try:
        provider._get_default_parameters = lambda call: {"temperature": 0.7, "keep_alive": "5m", "context_window": 2048}
        text_call = MockCall(response_format="text", structure=None)
        text_payload = provider._prepare_vision_data(text_call)
        
        if "format" not in text_payload:
            print("   ✓ Text mode does not add format parameter (backward compatible)")
        else:
            print("   ✗ Text mode incorrectly adds format parameter")
            return False
    except Exception as e:
        print(f"   ✗ Text mode test failed: {e}")
        return False
    
    # Test 4: Structured mode payload
    print("4. Testing structured mode payload generation...")
    try:
        structured_call = MockCall(response_format="json", structure=json.dumps(TEST_SCHEMA))
        structured_payload = provider._prepare_vision_data(structured_call)
        
        # Check format is added
        if "format" in structured_payload and structured_payload["format"] == TEST_SCHEMA:
            print("   ✓ Structured mode adds correct format parameter")
            print("   ✓ Schema correctly embedded in payload")
        else:
            print(f"   ✗ Structured mode missing correct format: {structured_payload.get('format', 'Missing')}")
            return False
    except Exception as e:
        print(f"   ✗ Structured mode test failed: {e}")
        return False
    
    # Test 5: Check if Ollama is running
    print("5. Testing Ollama availability...")
    try:
        test_url = f"http://{OLLAMA_ENDPOINT['ip_address']}:{OLLAMA_ENDPOINT['port']}/api/tags"
        async with session.get(test_url) as response:
            if response.status == 200:
                models_data = await response.json()
                print("   ✓ Ollama is running")
                print(f"   Available models: {len(models_data.get('models', []))}")
                
                # Check for the specific model requested
                model_names = [m.get('name', '') for m in models_data.get('models', [])]
                if "PetrosStav/gemma3-tools:12b" in model_names:
                    print(f"   ✓ Found requested model: PetrosStav/gemma3-tools:12b")
                    print(f"   Using model: {provider.model}")
                else:
                    print("   ⚠ PetrosStav/gemma3-tools:12b model not found")
                    print("   Available models:", [m[:30] + "..." if len(m) > 30 else m for m in model_names[:5]])
                    await session.close()
                    return False
            else:
                print(f"   ✗ Ollama not responding (HTTP {response.status})")
                print("   Start Ollama: ollama serve")
                await session.close()
                return False
    except Exception as e:
        print(f"   ✗ Cannot connect to Ollama: {e}")
        print("   Make sure Ollama is running: ollama serve")
        await session.close()
        return False
    
    # Test 6: Real API call with structured output
    print("6. Testing real Ollama API call with structured output...")
    try:
        print("   📤 Raw Request Payload:")
        print("   " + "="*50)
        print(f"   {json.dumps(structured_payload, indent=2)}")
        print("   " + "="*50)
        
        response_text = await provider._make_request(structured_payload)
        print("   ✓ API call successful")
        print(f"   Response length: {len(response_text)} characters")
        
        print("   📥 Raw Response:")
        print("   " + "="*50)  
        print(f"   {response_text}")
        print("   " + "="*50)
        
        # Test JSON parsing
        try:
            structured_response = json.loads(response_text)
            print("   ✓ Response is valid JSON")
            
            # Verify required fields
            if "color_detected" in structured_response and "confidence" in structured_response:
                print("   ✓ Required fields present")
                print(f"   Color detected: {structured_response['color_detected']}")
                print(f"   Confidence: {structured_response['confidence']}")
                
                if "dominant_color" in structured_response:
                    print(f"   Dominant color: {structured_response['dominant_color']}")
                
                # Validate types and ranges
                if (isinstance(structured_response["color_detected"], bool) and
                    isinstance(structured_response["confidence"], (int, float)) and
                    0 <= structured_response["confidence"] <= 100):
                    print("   ✓ Field types and ranges correct")
                else:
                    print("   ✗ Invalid field types or ranges")
                    return False
            else:
                print("   ✗ Missing required fields")
                return False
            
        except json.JSONDecodeError:
            print(f"   ✗ Response is not valid JSON: {response_text}")
            return False
            
    except Exception as e:
        print(f"   ✗ API call failed: {e}")
        return False
    
    # Test 7: Real API call with text mode
    print("7. Testing real Ollama API call with text mode...")
    try:
        print("   📤 Raw Text Mode Request Payload:")
        print("   " + "="*50)
        print(f"   {json.dumps(text_payload, indent=2)}")
        print("   " + "="*50)
        
        text_response = await provider._make_request(text_payload)
        print("   ✓ Text mode API call successful")
        
        print("   📥 Raw Text Response:")
        print("   " + "="*50)  
        print(f"   {text_response}")
        print("   " + "="*50)
    except Exception as e:
        print(f"   ✗ Text mode API call failed: {e}")
        await session.close()
        return False
    
    # Cleanup
    try:
        await session.close()
        # Restore original function
        providers_module.async_get_clientsession = original_get_clientsession
    except Exception as e:
        print(f"   Warning: Cleanup failed: {e}")
    
    return True

async def main():
    """Run all tests."""
    print("LLM Vision Structured Output - Ollama Integration Test")
    print("Testing with local Ollama instance")
    print()
    
    try:
        success = await test_ollama_integration()
        
        print("\n" + "=" * 60)
        if success:
            print("🎉 ALL OLLAMA INTEGRATION TESTS PASSED!")
            print()
            print("✅ Ollama structured output implementation is working correctly:")
            print("  • Provider correctly reports structured output support")  
            print("  • Text mode maintains backward compatibility")
            print("  • Structured mode adds correct format parameter")
            print("  • Real API calls work with both text and JSON responses")
            print("  • JSON schema validation works as expected")
            print()
            print("Ready for manual testing in Home Assistant!")
        else:
            print("❌ SOME TESTS FAILED!")
            print("Check the output above for details.")
            print()
            print("Common issues:")
            print("  • Ollama not running: ollama serve")
            print("  • No vision models: ollama pull llava:latest")
            
        return success
        
    except Exception as e:
        print(f"❌ Test suite crashed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)