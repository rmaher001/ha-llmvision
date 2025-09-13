"""LLM Call Logger for LLM Vision Integration"""
import os
import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional
from functools import partial

_LOGGER = logging.getLogger(__name__)


class LLMLogger:
    """Handles detailed logging of all LLM API calls including prompts, images, and responses"""
    
    def __init__(self, hass):
        self.hass = hass
        self.logs_dir = os.path.join(hass.config.path("www"), "llmvision", "logs")
        
    async def _ensure_logs_dir(self):
        """Ensure the logs directory exists"""
        await self.hass.loop.run_in_executor(None, partial(os.makedirs, self.logs_dir, exist_ok=True))
    
    async def log_llm_call(self, 
                          provider: str,
                          model: str, 
                          call_data: Any,
                          request_payload: Dict,
                          response_data: Dict,
                          images: Optional[List[str]] = None,
                          filenames: Optional[List[str]] = None,
                          error: Optional[str] = None):
        """
        Log a complete LLM API call with all relevant data
        
        Args:
            provider: Name of the LLM provider (OpenAI, Anthropic, etc.)
            model: Model name used
            call_data: ServiceCallData object with call parameters
            request_payload: The actual data sent to the LLM API
            response_data: The response received from the LLM API
            images: List of base64 encoded images 
            filenames: List of filenames for the images
            error: Error message if the call failed
        """
        await self._ensure_logs_dir()
        
        timestamp = datetime.now()
        log_filename = f"llm_call_{timestamp.strftime('%Y%m%d_%H%M%S_%f')[:-3]}.json"
        log_path = os.path.join(self.logs_dir, log_filename)
        
        # Save actual images to files
        image_files = []
        if images:
            for i, (image_data, filename) in enumerate(zip(images, filenames or [])):
                try:
                    # Create image filename
                    if filename:
                        safe_filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_')).rstrip()
                        image_filename = f"{timestamp.strftime('%Y%m%d_%H%M%S_%f')[:-3]}_{i:02d}_{safe_filename}.jpg"
                    else:
                        image_filename = f"{timestamp.strftime('%Y%m%d_%H%M%S_%f')[:-3]}_{i:02d}_image.jpg"
                    
                    image_path = os.path.join(self.logs_dir, image_filename)
                    
                    # Save base64 image to file
                    await self.hass.loop.run_in_executor(
                        None,
                        self._save_base64_image,
                        image_data,
                        image_path
                    )
                    
                    image_files.append({
                        "index": i,
                        "filename": image_filename,
                        "original_filename": filename,
                        "size_chars": len(image_data)
                    })
                    
                except Exception as e:
                    _LOGGER.error(f"Failed to save image {i}: {e}")
                    image_files.append({
                        "index": i,
                        "filename": None,
                        "original_filename": filename,
                        "error": str(e),
                        "size_chars": len(image_data) if image_data else 0
                    })
        
        # Prepare log entry
        log_entry = {
            "timestamp": timestamp.isoformat(),
            "provider": provider,
            "model": model,
            "call_info": {
                "message": getattr(call_data, 'message', ''),
                "max_tokens": getattr(call_data, 'max_tokens', 0),
                "temperature": getattr(call_data, 'temperature', 0.0),
                "remember": getattr(call_data, 'remember', False),
                "use_memory": getattr(call_data, 'use_memory', False),
                "image_count": len(images) if images else 0,
                "image_entities": getattr(call_data, 'image_entities', []),
                "video_paths": getattr(call_data, 'video_paths', []),
                "event_id": getattr(call_data, 'event_id', []),
                "sensor_entity": getattr(call_data, 'sensor_entity', ''),
                "generate_title": getattr(call_data, 'generate_title', False),
            },
            "request_payload": self._sanitize_payload_for_logging(request_payload),
            "response": {
                "success": error is None,
                "error": error,
                "response_data": response_data if error is None else None
            },
            "images": {
                "count": len(images) if images else 0,
                "saved_files": image_files,
                "note": "Image files saved alongside this log for debugging purposes"
            }
        }
        
        # Write log entry to file
        try:
            await self.hass.loop.run_in_executor(
                None, 
                self._write_log_file, 
                log_path, 
                log_entry
            )
            _LOGGER.info(f"LLM call logged to: {log_filename}")
        except Exception as e:
            _LOGGER.error(f"Failed to write LLM log: {e}")
    
    def _write_log_file(self, log_path: str, log_entry: Dict):
        """Write log entry to file (sync function for executor)"""
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(log_entry, f, indent=2, ensure_ascii=False)
    
    def _save_base64_image(self, base64_data: str, image_path: str):
        """Save base64 encoded image to file (sync function for executor)"""
        import base64
        try:
            # Decode base64 image data
            image_bytes = base64.b64decode(base64_data)
            
            # Write to file
            with open(image_path, 'wb') as f:
                f.write(image_bytes)
                
        except Exception as e:
            _LOGGER.error(f"Failed to decode/save base64 image to {image_path}: {e}")
            raise
    
    def _sanitize_payload_for_logging(self, payload: Dict) -> Dict:
        """
        Sanitize request payload for logging by truncating large base64 images
        while preserving the structure for debugging
        """
        if not isinstance(payload, dict):
            return payload
            
        sanitized = {}
        for key, value in payload.items():
            if key == "messages" and isinstance(value, list):
                sanitized[key] = []
                for message in value:
                    if isinstance(message, dict):
                        sanitized_message = message.copy()
                        if "content" in sanitized_message and isinstance(sanitized_message["content"], list):
                            sanitized_content = []
                            for content_item in sanitized_message["content"]:
                                if isinstance(content_item, dict):
                                    if content_item.get("type") == "image_url":
                                        # Truncate base64 image data for logging
                                        sanitized_item = content_item.copy()
                                        if "image_url" in sanitized_item and "url" in sanitized_item["image_url"]:
                                            url = sanitized_item["image_url"]["url"]
                                            if url.startswith("data:image/") and "base64," in url:
                                                prefix, data = url.split("base64,", 1)
                                                truncated_data = data[:100] + f"... (truncated, original length: {len(data)} chars)"
                                                sanitized_item["image_url"]["url"] = f"{prefix}base64,{truncated_data}"
                                        sanitized_content.append(sanitized_item)
                                    else:
                                        sanitized_content.append(content_item)
                                else:
                                    sanitized_content.append(content_item)
                            sanitized_message["content"] = sanitized_content
                        sanitized[key].append(sanitized_message)
                    else:
                        sanitized[key].append(message)
            else:
                sanitized[key] = value
                
        return sanitized
    
    async def log_image_processing(self, 
                                  operation: str,
                                  source: str,
                                  image_count: int,
                                  details: Dict):
        """
        Log image processing operations
        
        Args:
            operation: Type of operation (resize, encode, extract_frames, etc.)
            source: Source of images (camera_entity, file_path, etc.)
            image_count: Number of images processed
            details: Additional details about the operation
        """
        await self._ensure_logs_dir()
        
        timestamp = datetime.now()
        log_filename = f"image_processing_{timestamp.strftime('%Y%m%d_%H%M%S_%f')[:-3]}.json"
        log_path = os.path.join(self.logs_dir, log_filename)
        
        log_entry = {
            "timestamp": timestamp.isoformat(),
            "type": "image_processing",
            "operation": operation,
            "source": source,
            "image_count": image_count,
            "details": details
        }
        
        try:
            await self.hass.loop.run_in_executor(
                None, 
                self._write_log_file, 
                log_path, 
                log_entry
            )
            _LOGGER.debug(f"Image processing logged to: {log_filename}")
        except Exception as e:
            _LOGGER.error(f"Failed to write image processing log: {e}")
    
    async def cleanup_old_logs(self, days_to_keep: int = 7):
        """
        Clean up log files older than specified days
        
        Args:
            days_to_keep: Number of days worth of logs to keep
        """
        await self._ensure_logs_dir()
        
        try:
            cutoff_time = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)
            
            def _cleanup():
                removed_count = 0
                for filename in os.listdir(self.logs_dir):
                    if filename.endswith('.json') or filename.endswith('.jpg'):
                        file_path = os.path.join(self.logs_dir, filename)
                        if os.path.getmtime(file_path) < cutoff_time:
                            os.remove(file_path)
                            removed_count += 1
                return removed_count
            
            removed_count = await self.hass.loop.run_in_executor(None, _cleanup)
            if removed_count > 0:
                _LOGGER.info(f"Cleaned up {removed_count} old LLM log files")
                
        except Exception as e:
            _LOGGER.error(f"Failed to cleanup old logs: {e}")