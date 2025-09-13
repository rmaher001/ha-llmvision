# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This directory contains a Home Assistant automation for security checking functionality. The automation is defined in `security_check.yaml` following Home Assistant's automation configuration format.

## Architecture

- `security_check.yaml` - Main automation configuration file that defines triggers, conditions, and actions for security monitoring
- This is part of a larger Home Assistant setup located in the parent `/Users/richard/ha/` directory

## Home Assistant Automation Format

Home Assistant automations follow this YAML structure:
- `alias` - Human readable name for the automation  
- `description` - Optional description of what the automation does
- `trigger` - Event(s) that start the automation
- `condition` - Optional conditions that must be met
- `action` - Actions to perform when triggered

## Development Commands

To validate Home Assistant configuration:
```bash
# From Home Assistant installation directory
hass --script check_config
```

To restart Home Assistant after changes:
```bash
# Via Home Assistant service
sudo systemctl restart homeassistant
```

## Testing

Test automations by:
1. Triggering the defined trigger conditions
2. Checking Home Assistant logs for execution
3. Verifying expected actions occur

Access logs via Home Assistant web interface or:
```bash
# View Home Assistant logs
journalctl -u homeassistant -f
```