# Package Detection Automation

## Overview
Simplified state-based package detection system using LLM Vision's structured output to track package presence at the door.

## Files
- `detect_package_simple.yaml` - Main automation for package detection
- `helpers.yaml` - Input boolean and helper entities
- `detect_package.yaml` - Original complex automation (deprecated)

## How It Works

### State-Based Detection
Instead of trying to interpret activities (delivery vs pickup), the system simply tracks whether a package is present:
- **Package Present** (`input_boolean.package_at_door = on`): Package detected at door
- **No Package** (`input_boolean.package_at_door = off`): No package detected

### Triggers
1. **Motion Detection**: Checks when entrance camera detects motion
2. **Periodic Check**: Hourly checks during delivery hours (7am-10pm)

### Structured Output Schema
```json
{
  "package_present": boolean,    // Is there a package visible?
  "confidence": 0.0-1.0,         // Detection confidence
  "location": enum,              // "door", "porch", "walkway", "none"
  "package_count": integer,      // Number of packages
  "description": string          // Brief description
}
```

### State Changes
- **New Package**: When `package_present=true` and current state is `off` → Send delivery notification
- **Package Removed**: When `package_present=false` and current state is `on` → Send collection notification
- **No Change**: State remains the same, no notification

## Configuration

### Required Entities
- `camera.entrance_camera_clear` - Doorbell camera
- `camera.front_full_camera_main` - Overhead patio camera (4K)
- `camera.front_side_camera_hd_stream` - Side patio camera (2K)
- `binary_sensor.entrance_camera_motion` - Motion sensor trigger

### Helper Entities
Add to Home Assistant's `configuration.yaml`:
```yaml
input_boolean:
  package_at_door:
    name: Package at Door
    icon: mdi:package-variant
    initial: off
```

### Optional Configuration
- Adjust confidence threshold (default: 0.7)
- Modify delivery hours (default: 7am-10pm)
- Change check frequency (default: hourly)
- Select LLM provider via `input_select.llmvision_provider`

## Testing

### Manual Testing
1. Enable the automation in Home Assistant
2. Place a box/package in camera view
3. Trigger motion or wait for periodic check
4. Verify state change and notification
5. Remove package and verify state clears

### Debug Information
Check persistent notifications for:
- Detection results with confidence scores
- State change tracking
- Frame selection from multiple cameras

## Advantages Over Complex Automation

### Simplicity
- No activity interpretation needed
- Binary state: package present or not
- Eliminates false positives from activities

### Reliability
- Structured output ensures consistent responses
- High confidence threshold (0.7) reduces errors
- Multi-camera validation improves accuracy

### Maintainability
- Clear state transitions
- Simple debugging via notifications
- Easy to adjust confidence thresholds

## Known Limitations
- Requires good camera coverage of delivery area
- May miss packages placed outside camera view
- Weather/lighting conditions affect detection
- Does not identify carrier or track specific packages

## Future Enhancements
- Add package image capture for notifications
- Track delivery patterns over time
- Integrate with delivery service APIs
- Add package-specific identification