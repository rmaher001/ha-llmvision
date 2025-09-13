# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This directory contains Home Assistant automation configurations for intelligent security monitoring and vehicle detection. The automations leverage AI vision analysis and event-driven triggers to provide real-time notifications and responses.

## Architecture

### Directory Structure
- `detect_tow_truck/` - AI-powered tow truck and patrol car detection with urgent notifications
- `security_check/` - Human detection and security monitoring for line-crossing events
- `package_detection/` - State-based package delivery/pickup detection with structured output

Each automation directory contains:
- Main YAML automation file
- Individual CLAUDE.md with specific details
- Test assets and helper configurations (where applicable)

### Common Automation Pattern
All automations follow Home Assistant's standard YAML structure:
```yaml
alias: Human-readable name
description: What the automation does
triggers: Event(s) that start the automation
conditions: Optional conditions that must be met
actions: Actions to perform when triggered
```

## Key Features

### AI Vision Integration
- Uses Home Assistant's `ai_task.generate_data` action for intelligent analysis
- Structured data extraction from camera feeds
- Context-aware detection with configurable prompts

### Multi-Channel Notifications
- Persistent notifications in Home Assistant UI
- Text-to-speech announcements across multiple speakers
- Email and SMS notifications via `notify` services
- Dynamic volume control for audio devices

### Testing Infrastructure
- Test mode switches for development validation
- Mock image analysis using static test images
- Bypass conditions for isolated testing

## Development Commands

### Configuration Validation
```bash
# Validate Home Assistant configuration
hass --script check_config
```

### Service Management
```bash
# Restart Home Assistant after changes
sudo systemctl restart homeassistant

# View real-time logs
journalctl -u homeassistant -f
```

### Automation Testing
```bash
# Test automation via Home Assistant service
curl -X POST \
  http://homeassistant.local:8123/api/services/automation/trigger \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"entity_id": "automation.your_automation_alias"}'
```

## Entity Dependencies

### Common Requirements
- Camera entities for image capture
- Binary sensors for motion/occupancy detection
- AI task services for vision analysis
- Media player entities for TTS notifications
- Notification services for alerts

### Specific Automations

**detect_tow_truck:**
- `binary_sensor.entrance_camera_motion`
- `binary_sensor.garage_camera_smart_occupancy_sensor_occupancysensor`
- `camera.entrance_camera_clear`
- `ai_task.google_ai_task`
- Multiple `media_player` entities
- `notify.richard_ram6_com`
- `input_boolean.test_tow_truck_mode` (helper)

**security_check:**
- Dahua camera event system (`dahua_event_received`)
- Line detection events for "Enter-Patio" and "Enter-Door"
- Human object detection triggers

## Testing Strategy

### Test Mode Setup
1. Add helper configurations to Home Assistant
2. Deploy test images to `/config/www/test_images/`
3. Enable test mode via input_boolean entities
4. Trigger motion sensors to test automation flow

### Validation Steps
1. Monitor Home Assistant logs for automation execution
2. Verify AI vision analysis results
3. Confirm notification delivery across all channels
4. Test edge cases with different detection scenarios

## Configuration Notes

- Automations use YAML anchors for code reuse (speakers, notification targets)
- Dynamic message templates based on detection results
- Conditional actions based on AI analysis outcomes
- Volume control sequences for non-disruptive audio notifications

## Important Considerations

- AI vision analysis requires active camera entities
- Network connectivity needed for cloud-based AI services
- Test mode bypasses normal operational conditions
- Each automation can run independently
- Detailed logging available in individual automation directories