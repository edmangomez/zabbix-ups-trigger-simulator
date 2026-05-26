# AGENTS.md

## Quick Start

```bash
pip install -r requirements.txt
py -3.11 app.py
```

- Web UI: http://localhost:5000
- SNMP agent: UDP port 161 (community: public)

## Running the App (Windows)

Prefer launcher-based execution:
```powershell
py -3.11 .\app.py
```

If `py` is not available, use your installed Python path:
```powershell
& "C:\path\to\python.exe" ".\app.py"
```

## Key OIDs (all values in 0.1 units - e.g., 1200 = 120V)

| OID | Key | Normal Value |
|-----|-----|---------------|
| 1.3.6.1.4.1.318.1.1.1.2.2.1.0 | battery.capacity | 100 |
| 1.3.6.1.4.1.318.1.1.1.2.1.1.0 | battery.status | 2 (Normal) |
| 1.3.6.1.4.1.318.1.1.1.3.2.1.0 | input.voltage | 1200 (120V) |
| 1.3.6.1.4.1.318.1.1.1.4.2.1.0 | output.voltage | 1300 (130V) |
| 1.3.6.1.4.1.318.1.1.1.1.1.0 | ups.status | 2 (Online) |
| 1.3.6.1.4.1.318.1.1.1.4.1.1.0 | output.status | 2 (Online) |
| 1.3.6.1.4.1.318.1.1.1.2.3.2.0 | battery.temperature | 260 (26°C) |
| 1.3.6.1.4.1.318.1.1.1.4.3.3.0 | output.load | 500 (50%) |
| 1.3.6.1.4.1.318.1.1.1.2.2.4.0 | battery.replace.indicator | 1 (No Replace) |
| 1.3.6.1.2.1.1.3.0 | system.uptime | 8640000 (100 days) |

## Zabbix Template Import

When importing YAML templates to Zabbix 5.4:
- All UUIDs must be 32 hex characters (no dashes)
- Use template: `templates/apc_smart_ups_template_v3.yaml`
- Trigger thresholds use 0.1V units (e.g., >1300 for >130V)

## Alert Values for Testing Triggers

| Alert Type | battery.capacity | input.voltage | ups.status | output.status |
|------------|------------------|---------------|------------|---------------|
| battery_low | 15 | - | - | - |
| voltage_high | - | 1450 | - | - |
| voltage_low | - | 900 | - | - |
| on_battery | - | - | 3 | 3 |
| high_temperature | - | - | - | - (battery.temp=430) |
| high_load | - | - | - | - (output.load=900) |
| output_off | - | - | - | 7 |
| output_smart_boost | - | - | - | 4 |
| output_smart_trim | - | - | - | 12 |

## API Endpoints

- `GET /api/status` - Current values with overrides
- `GET /api/alerts` - Current alert/override state
- `POST /api/alerts` - Activate alerts: `{"type": "battery_low"}`
- `POST /api/alerts` - Reset: `{"reset": true}`
- `POST /api/override` - Custom value: `{"field": "custom_battery", "value": 15}`

## Known Issues

- pysnmp 7.x changed import paths - use `from pysnmp.entity import engine, config`
- SNMPv2c community "public" required for Zabbix
- Values are static by default (no simulation loop) - use web UI/APIs to set alerts
- API POST endpoints now enforce JSON body and field/range validation
