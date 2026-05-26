# zabbix-ups-trigger-simulator

Flask + SNMPv2c simulator for APC Smart-UPS (PowerNet MIB), focused on fast Zabbix trigger testing in lab environments.

## Features

- Web dashboard for real-time UPS status and alert activation
- Predefined alert scenarios (battery, voltage, UPS/output status, temperature, load, restart)
- Custom field overrides for controlled trigger validation
- SNMP agent compatible with APC PowerNet MIB-style OIDs
- Ready-to-import Zabbix 5.4 template (`templates/apc_smart_ups_template_v3.yaml`)

## Quick Start

```bash
pip install -r requirements.txt
python app.py
```

- Web UI: `http://localhost:5000`
- SNMP endpoint: `udp://localhost:161`
- Community: `public`

## Windows Run Example

```powershell
& "C:\path\to\python.exe" ".\app.py"
```

## Main API Endpoints

- `GET /api/status` - Current UPS values (with active overrides)
- `GET /api/alerts` - Current alert state
- `POST /api/alerts` - Apply alert scenario
- `POST /api/alerts` with `{"reset": true}` - Clear all alerts/overrides
- `POST /api/override` - Apply one custom field override
- `GET /api/oids` - OID map
- `GET|POST /api/zabbix/config` - View/update Zabbix settings in app

## Example Alert Payloads

```json
{ "type": "battery_low" }
```

```json
{ "type": "on_battery" }
```

```json
{
  "type": "custom",
  "custom_battery": 15,
  "custom_input_voltage": 900,
  "output_status_override": 7
}
```

## Key OIDs (examples)

- `1.3.6.1.4.1.318.1.1.1.2.2.1.0` battery capacity
- `1.3.6.1.4.1.318.1.1.1.3.2.1.0` input voltage
- `1.3.6.1.4.1.318.1.1.1.4.1.1.0` output status
- `1.3.6.1.2.1.1.3.0` system uptime

## Zabbix Notes

- Import: `templates/apc_smart_ups_template_v3.yaml`
- Ensure host SNMP interface uses community `public`
- Fast-testing tuned template is included (shorter polling/triggers for lab validation)

## Project Structure

```text
app.py                          # Flask app + embedded SNMP agent
agent/snmp_agent.py             # Standalone SNMP agent
agent/ups_mib.py                # MIB OID constants
agent/ups_simulation.py         # Base UPS simulator
templates/index.html            # Dashboard UI
templates/apc_smart_ups_template_v3.yaml
```

## License

No license file is included yet. Add one (for example MIT) if you want others to reuse the project.
