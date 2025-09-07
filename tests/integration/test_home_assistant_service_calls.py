#!/usr/bin/env python3
"""
Real Home Assistant service call integration tests.
Tests the actual service integration with structured output.
"""

import os
import json
import base64
import asyncio
import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock
from PIL import Image
import io

# Import the actual Home Assistant integration code
from custom_components.llmvision import setup, ServiceCallData
from custom_components.llmvision.const import (
    DOMAIN, PROVIDER, MESSAGE, MODEL, MAXTOKENS, 
    CONF_PROVIDER, CONF_API_KEY, CONF_DEFAULT_MODEL,
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
    """Mock Home Assistant instance that behaves like the real thing"""
    
    def __init__(self):
        self.data = {DOMAIN: {}}
        self.services = MockServices()
        self.states = MockStates()
        self.config = MockConfig()
        self.bus = MockBus()
        self._session = None
        
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


class MockServices:
    """Mock services registry"""
    
    def __init__(self):
        self.registered_services = {}
        
    def register(self, domain, service_name, handler, supports_response=None):
        """Register a service handler"""
        if domain not in self.registered_services:
            self.registered_services[domain] = {}
        self.registered_services[domain][service_name] = handler
        print(f"✅ Registered service: {domain}.{service_name}")
        
    async def call_service(self, domain, service_name, service_data):
        """Call a registered service (for testing)"""
        handler = self.registered_services[domain][service_name]
        
        # Create a mock service call object
        mock_call = Mock()
        mock_call.data = service_data
        
        # Call the actual service handler
        return await handler(mock_call)


class MockStates:
    """Mock states registry"""
    
    def get(self, entity_id):
        return None
        
    def async_set(self, entity_id, state, attributes):
        pass


class MockConfig:
    """Mock config"""
    
    def __init__(self):
        self.api = MockAPI()
    
    def path(self, *path_parts):
        return "/tmp/test_llmvision"


class MockAPI:
    """Mock API config"""
    
    def __init__(self):
        self.use_ssl = False
        self.local_ip = "127.0.0.1"
        self.port = 8123


class MockBus:
    """Mock event bus"""
    
    def async_listen_once(self, event_type, callback):
        """Mock event listener registration"""
        pass


def setup_test_provider_config(hass, provider_name, api_key, model):
    """Set up a test provider configuration in hass.data"""
    provider_uid = f"test_{provider_name}_config"
    
    hass.data[DOMAIN][provider_uid] = {
        CONF_PROVIDER: provider_name,
        CONF_API_KEY: api_key, 
        CONF_DEFAULT_MODEL: model,
    }
    
    return provider_uid


@pytest.mark.integration
@pytest.mark.asyncio
class TestHomeAssistantServiceCalls:
    """Test the actual Home Assistant service integration"""
    
    @pytest_asyncio.fixture
    async def mock_hass(self):
        """Set up a mock Home Assistant instance"""
        hass = MockHass()
        
        # Monkey patch the async_get_clientsession to use our mock
        from custom_components.llmvision import providers
        from custom_components.llmvision import media_handlers
        original_get_session = providers.async_get_clientsession  
        original_media_session = media_handlers.async_get_clientsession
        
        providers.async_get_clientsession = lambda h: hass.get_session()
        media_handlers.async_get_clientsession = lambda h: hass.get_session()
        
        # Set up the integration
        await asyncio.get_event_loop().run_in_executor(None, setup, hass, {})
        
        yield hass
        
        # Cleanup
        providers.async_get_clientsession = original_get_session
        media_handlers.async_get_clientsession = original_media_session
        await hass.close_session()

    @pytest.mark.asyncio
    async def test_openai_structured_service_call(self, mock_hass):
        """Test OpenAI structured response through Home Assistant service call"""
        if not os.getenv('OPENAI_API_KEY'):
            pytest.skip("OPENAI_API_KEY not set")
            
        # Set up provider config
        provider_uid = setup_test_provider_config(
            mock_hass, "OpenAI", os.getenv('OPENAI_API_KEY'), "gpt-4o-mini"
        )
        
        # Create test image file
        test_image_path = "/tmp/test_red_image.png"
        img = Image.new('RGB', (100, 100), color='red')
        img.save(test_image_path, 'PNG')
        
        # Define structured output schema
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
        
        # Prepare service call data
        service_data = {
            PROVIDER: provider_uid,
            MESSAGE: "What is the dominant color in this image?",
            "image_file": test_image_path,
            MAXTOKENS: 100,
            RESPONSE_FORMAT: "json_schema",
            STRUCTURE: json.dumps(color_schema)
        }
        
        print("🧪 Testing OpenAI structured response via HA service call...")
        
        # Call the actual Home Assistant service
        response = await mock_hass.services.call_service(
            DOMAIN, "image_analyzer", service_data
        )
        
        print(f"✅ Service call response: {response}")
        
        # Verify the response
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
        
        print("✅ OpenAI Home Assistant service call test passed!")
        
        # Cleanup
        os.remove(test_image_path)

    @pytest.mark.asyncio
    async def test_anthropic_structured_service_call(self, mock_hass):
        """Test Anthropic structured response through Home Assistant service call"""
        if not os.getenv('ANTHROPIC_API_KEY'):
            pytest.skip("ANTHROPIC_API_KEY not set")
            
        # Set up provider config
        provider_uid = setup_test_provider_config(
            mock_hass, "Anthropic", os.getenv('ANTHROPIC_API_KEY'), "claude-3-haiku-20240307"
        )
        
        # Create test image file
        test_image_path = "/tmp/test_blue_image.png"
        img = Image.new('RGB', (100, 100), color='blue')
        img.save(test_image_path, 'PNG')
        
        # Define structured output schema for Anthropic (using tools)
        color_schema = {
            "type": "object",
            "properties": {
                "color_detected": {"type": "boolean"},
                "dominant_color": {"type": "string"}, 
                "confidence": {"type": "number", "minimum": 0, "maximum": 100}
            },
            "required": ["color_detected", "dominant_color", "confidence"]
        }
        
        # Prepare service call data
        service_data = {
            PROVIDER: provider_uid,
            MESSAGE: "What is the dominant color in this image?",
            "image_file": test_image_path,
            MAXTOKENS: 100,
            RESPONSE_FORMAT: "tool_use", 
            STRUCTURE: json.dumps(color_schema)
        }
        
        print("🧪 Testing Anthropic structured response via HA service call...")
        
        # Call the actual Home Assistant service
        response = await mock_hass.services.call_service(
            DOMAIN, "image_analyzer", service_data
        )
        
        print(f"✅ Service call response: {response}")
        
        # Verify the response  
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
        
        print("✅ Anthropic Home Assistant service call test passed!")
        
        # Cleanup
        os.remove(test_image_path)

    @pytest.mark.asyncio
    async def test_google_structured_service_call(self, mock_hass):
        """Test Google structured response through Home Assistant service call"""
        if not os.getenv('GOOGLE_API_KEY'):
            pytest.skip("GOOGLE_API_KEY not set")
            
        # Set up provider config  
        provider_uid = setup_test_provider_config(
            mock_hass, "Google", os.getenv('GOOGLE_API_KEY'), "gemini-1.5-flash"
        )
        
        # Create test image file
        test_image_path = "/tmp/test_green_image.png"
        img = Image.new('RGB', (100, 100), color='green')
        img.save(test_image_path, 'PNG')
        
        # Define structured output schema for Google (without additionalProperties)
        color_schema = {
            "type": "object", 
            "properties": {
                "color_detected": {"type": "boolean"},
                "dominant_color": {"type": "string"},
                "confidence": {"type": "number", "minimum": 0, "maximum": 100}
            },
            "required": ["color_detected", "dominant_color", "confidence"]
        }
        
        # Prepare service call data
        service_data = {
            PROVIDER: provider_uid,
            MESSAGE: "What is the dominant color in this image?",
            "image_file": test_image_path,
            MAXTOKENS: 100,
            RESPONSE_FORMAT: "json_object",
            STRUCTURE: json.dumps(color_schema)
        }
        
        print("🧪 Testing Google structured response via HA service call...")
        
        # Call the actual Home Assistant service
        response = await mock_hass.services.call_service(
            DOMAIN, "image_analyzer", service_data
        )
        
        print(f"✅ Service call response: {response}")
        
        # Verify the response
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
        
        print("✅ Google Home Assistant service call test passed!")
        
        # Cleanup
        os.remove(test_image_path)


if __name__ == "__main__":
    # Run specific tests
    import sys
    if len(sys.argv) > 1:
        provider = sys.argv[1].lower()
        if provider == "openai":
            asyncio.run(TestHomeAssistantServiceCalls().test_openai_structured_service_call(None))
        elif provider == "anthropic": 
            asyncio.run(TestHomeAssistantServiceCalls().test_anthropic_structured_service_call(None))
        elif provider == "google":
            asyncio.run(TestHomeAssistantServiceCalls().test_google_structured_service_call(None))
    else:
        print("Usage: python test_home_assistant_service_calls.py [openai|anthropic|google]")