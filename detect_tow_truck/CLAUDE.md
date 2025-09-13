# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Home Assistant automation that detects tow trucks and patrol cars using AI vision analysis and triggers urgent notifications to move parked vehicles.

## Architecture

The automation uses a single YAML configuration file (`detect_tow_truck.yaml`) that implements:

1. **Motion Detection Trigger**: Monitors `binary_sensor.entrance_camera_motion` for activity
2. **AI Vision Analysis**: Uses Home Assistant's `ai_task.generate_data` action with camera feed from `camera.entrance_camera_clear` to detect vehicles
3. **Multi-channel Notifications**: Sends alerts via:
   - Persistent notifications in Home Assistant
   - Text-to-speech announcements on multiple speakers
   - Email and SMS notifications to multiple recipients
   - Volume control for speakers before/after announcements

## Key Components

- **Trigger**: Motion sensor on entrance camera
- **Condition**: Garage occupancy sensor must be active
- **AI Task**: Structured detection for `tow_truck` and `patrol_car` booleans
- **Response Handling**: Conditional actions based on AI detection results

## Entity Dependencies

The automation relies on these Home Assistant entities:
- `binary_sensor.entrance_camera_motion`
- `binary_sensor.garage_camera_smart_occupancy_sensor_occupancysensor`
- `camera.entrance_camera_clear`
- `ai_task.google_ai_task`
- Multiple `media_player` entities for audio notifications
- `notify.richard_ram6_com` for email/SMS

## Testing

### Setup
1. Add `helpers.yaml` to your Home Assistant configuration
2. Copy `test_images/` directory to `/config/www/test_images/` in Home Assistant
3. Add a `tow_truck.jpg` image file to `/config/www/test_images/`
4. Restart Home Assistant to load the new input_boolean entity

### Test Mode
Enable test mode by turning on `input_boolean.test_tow_truck_mode`:
- AI will analyze `/config/www/test_images/tow_truck.jpg` instead of live camera
- Trigger motion on `binary_sensor.entrance_camera_motion`
- Test mode bypasses the occupancy sensor requirement

### Normal Mode
Disable test mode for normal operation using live camera AI detection.

## Changes Made
- Reduced automation from ~145 lines to ~125 lines
- Added YAML anchors for speakers and notification targets
- Consolidated duplicate notification logic
- Added test mode with manual switches
- Fixed typo: `two_truck` → `tow_truck`
- Dynamic message templates based on vehicle type