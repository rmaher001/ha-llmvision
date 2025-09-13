#!/usr/bin/env python3
"""
Direct provider integration tests for structured output.
Tests the provider logic directly with real API calls.
"""

import os
import json
import base64
import asyncio
import pytest
import pytest_asyncio
from unittest.mock import Mock
from PIL import Image
import io

# Import the actual provider code
from custom_components.llmvision.providers import Request
from custom_components.llmvision.const import (
    DOMAIN, CONF_PROVIDER, CONF_API_KEY, CONF_DEFAULT_MODEL,
    RESPONSE_FORMAT, STRUCTURE
)


def create_test_image_base64():
    """Create a simple red test image and convert to base64"""
    img = Image.new('RGB', (100, 100), color='red')
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode('utf-8')


class MockHass:
    """Minimal mock Home Assistant for provider testing"""
    
    def __init__(self):
        self.data = {DOMAIN: {}}
        self._session = None
        self.config_entries = MockConfigEntries()
        
    def get_session(self):
        """Return a real aiohttp session for API calls"""
        if self._session is None or self._session.closed:
            import aiohttp
            self._session = aiohttp.ClientSession()
        return self._session
        
    async def close_session(self):
        """Close aiohttp session"""
        if self._session and not self._session.closed:
            await self._session.close()


class MockConfigEntries:
    """Mock config entries registry"""
    
    def async_entries(self, domain):
        """Return empty list of config entries"""
        return []


class MockServiceCall:
    """Mock service call data"""
    
    def __init__(self, provider_uid, response_format="text", structure=None):
        self.provider = provider_uid
        self.response_format = response_format
        self.structure = structure
        self.use_memory = False
        self.remember = False
        self.generate_title = False
        self.max_tokens = 100
        self.model = None
        self.temperature = 0.0
        self.top_p = 0.9
        self.message = "What is the dominant color in this image?"


@pytest.mark.integration
@pytest.mark.asyncio
class TestProviderStructuredOutput:
    """Test provider structured output directly"""
    
    @pytest_asyncio.fixture
    async def mock_hass(self):
        """Set up mock Home Assistant with provider configs"""
        hass = MockHass()
        
        # Set up OpenAI config
        if os.getenv('OPENAI_API_KEY'):
            hass.data[DOMAIN]['openai_test'] = {
                CONF_PROVIDER: 'OpenAI',
                CONF_API_KEY: os.getenv('OPENAI_API_KEY'),
                CONF_DEFAULT_MODEL: 'gpt-4o-mini'
            }
            
        # Set up Anthropic config  
        if os.getenv('ANTHROPIC_API_KEY'):
            hass.data[DOMAIN]['anthropic_test'] = {
                CONF_PROVIDER: 'Anthropic',
                CONF_API_KEY: os.getenv('ANTHROPIC_API_KEY'),
                CONF_DEFAULT_MODEL: 'claude-3-haiku-20240307'
            }
            
        # Set up Google config
        if os.getenv('GOOGLE_API_KEY'):
            hass.data[DOMAIN]['google_test'] = {
                CONF_PROVIDER: 'Google',
                CONF_API_KEY: os.getenv('GOOGLE_API_KEY'),
                CONF_DEFAULT_MODEL: 'gemini-1.5-flash'
            }
            
        yield hass
        
        # Cleanup
        await hass.close_session()

    @pytest.mark.asyncio
    @pytest.mark.enable_socket
    async def test_openai_structured_output(self, mock_hass):
        """Test OpenAI structured output through provider"""
        if 'openai_test' not in mock_hass.data[DOMAIN]:
            pytest.skip("OPENAI_API_KEY not set")
            
        print("🧪 Testing OpenAI structured output via provider...")
        
        # Set up request
        request = Request(
            hass=mock_hass,
            message="What is the dominant color in this image?",
            max_tokens=100,
            temperature=0.0
        )
        
        # Add test image
        request.base64_images = [create_test_image_base64()]
        request.filenames = ["test_red_image.png"]
        
        # Set up service call with structured output
        color_schema = {
            "type": "object",
            "properties": {
                "color_detected": {"type": "boolean"},
                "dominant_color": {"type": "string"},
                "confidence": {"type": "number", "minimum": 0, "maximum": 100}
            },
            "required": ["color_detected", "dominant_color", "confidence"],
            "additionalProperties": False
        }
        
        call = MockServiceCall(
            provider_uid="openai_test",
            response_format="json_schema", 
            structure=json.dumps(color_schema)
        )
        
        # Make the request
        response = await request.call(call)
        
        print(f"✅ OpenAI provider response: {response}")
        
        # Verify response structure
        assert "response_text" in response
        
        # Parse structured response
        structured_data = json.loads(response["response_text"])
        
        # Validate schema compliance
        assert "color_detected" in structured_data
        assert "dominant_color" in structured_data
        assert "confidence" in structured_data
        assert isinstance(structured_data["color_detected"], bool)
        assert isinstance(structured_data["dominant_color"], str)
        assert isinstance(structured_data["confidence"], (int, float))
        assert structured_data["color_detected"] == True
        assert "red" in structured_data["dominant_color"].lower()
        assert 0 <= structured_data["confidence"] <= 100
        
        print("✅ OpenAI structured output test passed!")

    @pytest.mark.asyncio 
    async def test_anthropic_structured_output(self, mock_hass):
        """Test Anthropic structured output through provider"""
        if 'anthropic_test' not in mock_hass.data[DOMAIN]:
            pytest.skip("ANTHROPIC_API_KEY not set")
            
        print("🧪 Testing Anthropic structured output via provider...")
        
        # Set up request
        request = Request(
            hass=mock_hass,
            message="What is the dominant color in this image?",
            max_tokens=100,
            temperature=0.0
        )
        
        # Add test image (blue this time)
        img = Image.new('RGB', (100, 100), color='blue')
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        blue_image = base64.b64encode(buffer.read()).decode('utf-8')
        
        request.base64_images = [blue_image]
        request.filenames = ["test_blue_image.png"]
        
        # Set up service call with structured output (using tool_use for Anthropic)
        color_schema = {
            "type": "object", 
            "properties": {
                "color_detected": {"type": "boolean"},
                "dominant_color": {"type": "string"},
                "confidence": {"type": "number", "minimum": 0, "maximum": 100}
            },
            "required": ["color_detected", "dominant_color", "confidence"]
        }
        
        call = MockServiceCall(
            provider_uid="anthropic_test",
            response_format="tool_use",
            structure=json.dumps(color_schema)
        )
        
        # Make the request
        response = await request.call(call)
        
        print(f"✅ Anthropic provider response: {response}")
        
        # Verify response structure
        assert "response_text" in response
        
        # Parse structured response
        structured_data = json.loads(response["response_text"])
        
        # Validate schema compliance
        assert "color_detected" in structured_data
        assert "dominant_color" in structured_data
        assert "confidence" in structured_data
        assert isinstance(structured_data["color_detected"], bool)
        assert isinstance(structured_data["dominant_color"], str)
        assert isinstance(structured_data["confidence"], (int, float))
        assert structured_data["color_detected"] == True
        assert "blue" in structured_data["dominant_color"].lower()
        assert 0 <= structured_data["confidence"] <= 100
        
        print("✅ Anthropic structured output test passed!")

    @pytest.mark.asyncio
    async def test_google_structured_output(self, mock_hass):
        """Test Google structured output through provider"""
        if 'google_test' not in mock_hass.data[DOMAIN]:
            pytest.skip("GOOGLE_API_KEY not set") 
            
        print("🧪 Testing Google structured output via provider...")
        
        # Set up request
        request = Request(
            hass=mock_hass,
            message="What is the dominant color in this image?",
            max_tokens=100,
            temperature=0.0
        )
        
        # Add test image (green this time)
        img = Image.new('RGB', (100, 100), color='green')
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        green_image = base64.b64encode(buffer.read()).decode('utf-8')
        
        request.base64_images = [green_image]
        request.filenames = ["test_green_image.png"]
        
        # Set up service call with structured output (no additionalProperties for Google)
        color_schema = {
            "type": "object",
            "properties": {
                "color_detected": {"type": "boolean"},
                "dominant_color": {"type": "string"},
                "confidence": {"type": "number", "minimum": 0, "maximum": 100}
            },
            "required": ["color_detected", "dominant_color", "confidence"]
        }
        
        call = MockServiceCall(
            provider_uid="google_test",
            response_format="json_object",
            structure=json.dumps(color_schema)
        )
        
        # Make the request  
        response = await request.call(call)
        
        print(f"✅ Google provider response: {response}")
        
        # Verify response structure
        assert "response_text" in response
        
        # Parse structured response
        structured_data = json.loads(response["response_text"])
        
        # Validate schema compliance
        assert "color_detected" in structured_data
        assert "dominant_color" in structured_data
        assert "confidence" in structured_data
        assert isinstance(structured_data["color_detected"], bool)
        assert isinstance(structured_data["dominant_color"], str)
        assert isinstance(structured_data["confidence"], (int, float))
        assert structured_data["color_detected"] == True
        assert "green" in structured_data["dominant_color"].lower()
        assert 0 <= structured_data["confidence"] <= 100
        
        print("✅ Google structured output test passed!")


if __name__ == "__main__":
    # Run specific tests
    import sys
    if len(sys.argv) > 1:
        provider = sys.argv[1].lower()
        test_class = TestProviderStructuredOutput()
        if provider == "openai":
            asyncio.run(test_class.test_openai_structured_output(None))
        elif provider == "anthropic":
            asyncio.run(test_class.test_anthropic_structured_output(None))
        elif provider == "google":
            asyncio.run(test_class.test_google_structured_output(None))
    else:
        print("Usage: python test_provider_structured_output.py [openai|anthropic|google]")