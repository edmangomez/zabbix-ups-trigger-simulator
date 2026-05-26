# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

SNMP agent simulator for APC Smart-UPS devices using the APC PowerNet MIB. Includes a Flask web app for manual alert simulation and Zabbix trigger testing.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the web app with embedded SNMP agent (Flask on :5000, SNMP on :161)
py -3.11 app.py

# Run standalone SNMP agent only
py -3.11 agent/snmp_agent.py
```

## Architecture

### Core Components

- **UPSSimulator** (`agent/ups_simulation.py`): Holds base UPS values. Simulation loop is intentionally static in current version, so values change only through alerts/overrides.

- **UPSSimulatorWithOverrides** (`app.py`): Wrapper around UPSSimulator that applies alert overrides when activated from the web UI. When an alert is active, the wrapped properties return simulated alert values instead of the base simulator values.

- **UPSMibInstrumController** (`app.py`, `agent/snmp_agent.py`): Custom MIB controller extending `pysnmp.smi.instrum.AbstractMibInstrumController`. Handles GET (returns current value) and GETNEXT (returns next OID in sequence).

- **UPSAgent** (`agent/snmp_agent.py`): Standalone SNMP agent orchestrating transport (UDP), SNMPv2c community auth, and responders.

- **Flask Web App** (`app.py`): Runs on port 5000. Provides:
  - `/` - Web UI for alert simulation
  - `/api/status` - Current UPS values (with overrides applied)
  - `/api/alerts` - Set/read alert state (POST to activate alerts)
  - `/api/zabbix/config` - Configure Zabbix server connection
  - `/api/oids` - OID reference

### Alert Override Flow

```
Base Simulator (UPSSimulator)
    |
    v
UPSSimulatorWithOverrides  <-- AlertState (thread-safe)
    |
    v
UPSMibInstrumController
    |
    v
SNMP GET/GETNEXT responses  --> Zabbix polling
```

When an alert is activated via the web UI, the override wrapper intercepts property reads and returns alert-specific values. This allows Zabbix triggers to be tested without waiting for natural battery drain.

### OID Reference

**Base**: `1.3.6.1.4.1.318` (APC PowerNet MIB)

| Name | OID | Units |
|------|-----|-------|
| batteryCapacity | 1.3.6.1.4.1.318.1.1.1.2.2.1.0 | 0-100% |
| inputVoltage | 1.3.6.1.4.1.318.1.1.1.3.2.1.0 | 0.1V |
| outputVoltage | 1.3.6.1.4.1.318.1.1.1.4.2.1.0 | 0.1V |
| batteryStatus | 1.3.6.1.4.1.318.1.1.1.2.1.1.0 | 2=Normal, 3=Low, 4=Fault |
| upsStatus | 1.3.6.1.4.1.318.1.1.1.1.1.0 | 2=Online, 3=OnBattery |

### Zabbix Integration

- **Template**: `templates/apc_smart_ups_template.xml` - Zabbix 5.4 template with items, triggers, graphs, and dashboards
- **Triggers**: Battery <20%, input voltage out of range (100-130V)
- **SNMP**: Agent listens on UDP 161, community `public`
- **Validation**: API endpoints in `app.py` validate JSON body and numeric ranges/types
