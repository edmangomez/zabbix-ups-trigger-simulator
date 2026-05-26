"""
Alerta.app - Web application for UPS alert simulation and Zabbix testing.
Combines a Flask web UI with a pysnmp agent that responds to GET/GETNEXT requests.
"""
import os
import sys
import threading
from copy import deepcopy

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "agent"))

from flask import Flask, jsonify, render_template, request
from pysnmp.carrier.asyncio.dgram import udp
from pysnmp.entity import config, engine
from pysnmp.entity.rfc3413 import cmdrsp, context
from pysnmp.proto.api import v2c
from pysnmp.smi import instrum

from ups_mib import (
    BATTERY_CAPACITY_OID,
    BATTERY_REPLACE_INDICATOR_OID,
    BATTERY_STATUS_OID,
    BATTERY_TEMPERATURE_OID,
    INPUT_FREQUENCY_OID,
    INPUT_VOLTAGE_OID,
    OUTPUT_CURRENT_OID,
    OUTPUT_LOAD_OID,
    OUTPUT_STATUS_OID,
    OUTPUT_VOLTAGE_OID,
    SYSTEM_NAME_OID,
    SYSTEM_UPTIME_OID,
    UPS_MIB_MAP,
    UPS_STATUS_OID,
    oid_to_str,
)
from ups_simulation import UPSSimulator

app = Flask(__name__)

DEFAULT_ALERT_STATE = {
    "active": False,
    "type": None,
    "custom_battery": None,
    "custom_input_voltage": None,
    "custom_output_voltage": None,
    "ups_status_override": None,
    "output_status_override": None,
    "battery_temperature_override": None,
    "battery_replace_indicator_override": None,
    "output_load_override": None,
    "system_uptime_override": None,
}

VALID_ALERT_TYPES = [
    "battery_low",
    "voltage_high",
    "voltage_low",
    "on_battery",
    "custom",
    "high_temperature",
    "battery_replace",
    "high_load",
    "output_timed_sleeping",
    "output_software_bypass",
    "output_sleeping_power_return",
    "output_reboot",
    "output_smart_trim",
    "output_smart_boost",
    "output_off",
    "output_switched_bypass",
    "output_hardware_bypass",
    "output_emergency_bypass",
    "system_restart",
]

OVERRIDE_SPECS = {
    "custom_battery": ("float", 0, 100),
    "custom_input_voltage": ("int", 0, None),
    "custom_output_voltage": ("int", 0, None),
    "ups_status_override": ("int", 1, 5),
    "output_status_override": ("int", 1, 16),
    "battery_temperature_override": ("int", 0, None),
    "battery_replace_indicator_override": ("int", 1, 2),
    "output_load_override": ("int", 0, 1000),
    "system_uptime_override": ("int", 0, None),
}


class AlertState:

    def __init__(self):
        self._state = deepcopy(DEFAULT_ALERT_STATE)
        self._lock = threading.Lock()

    def snapshot(self):
        with self._lock:
            return deepcopy(self._state)

    def reset(self):
        with self._lock:
            self._state = deepcopy(DEFAULT_ALERT_STATE)

    def update(self, updates):
        with self._lock:
            self._state.update(updates)
            return deepcopy(self._state)


_alert_state = AlertState()


class UPSSimulatorWithOverrides:

    def __init__(self, simulator, alert_state):
        self.simulator = simulator
        self._alert_state = alert_state

    @property
    def battery_capacity(self):
        state = self._alert_state.snapshot()
        if state["active"] and state["type"] == "battery_low":
            return 15.0
        if state["active"] and state["type"] == "custom" and state["custom_battery"] is not None:
            return state["custom_battery"]
        return self.simulator.battery_capacity

    @property
    def input_voltage(self):
        state = self._alert_state.snapshot()
        if state["active"] and state["type"] == "voltage_high":
            return 1450
        if state["active"] and state["type"] == "voltage_low":
            return 900
        if state["active"] and state["type"] == "custom" and state["custom_input_voltage"] is not None:
            return state["custom_input_voltage"]
        return self.simulator.input_voltage

    @property
    def output_voltage(self):
        state = self._alert_state.snapshot()
        if state["active"] and state["type"] == "custom" and state["custom_output_voltage"] is not None:
            return state["custom_output_voltage"]
        return self.simulator.output_voltage

    @property
    def battery_status(self):
        state = self._alert_state.snapshot()
        if state["active"] and state["type"] == "battery_low":
            return 3
        return self.simulator.battery_status

    @property
    def ups_status(self):
        state = self._alert_state.snapshot()
        if state["active"] and state["type"] == "on_battery":
            return 3
        if state["active"] and state["ups_status_override"] is not None:
            return state["ups_status_override"]
        return self.simulator.ups_status

    @property
    def output_status(self):
        state = self._alert_state.snapshot()
        if state["active"] and state["type"] == "on_battery":
            return 3
        if state["active"] and state["output_status_override"] is not None:
            return state["output_status_override"]
        return self.simulator.output_status

    @property
    def system_uptime(self):
        state = self._alert_state.snapshot()
        if state["active"] and state["system_uptime_override"] is not None:
            return state["system_uptime_override"]
        return self.simulator.system_uptime

    @property
    def system_name(self):
        return self.simulator.system_name

    @property
    def battery_temperature(self):
        state = self._alert_state.snapshot()
        if state["active"] and state["type"] == "high_temperature":
            return 450
        if state["active"] and state["battery_temperature_override"] is not None:
            return state["battery_temperature_override"]
        return self.simulator.battery_temperature

    @property
    def battery_replace_indicator(self):
        state = self._alert_state.snapshot()
        if state["active"] and state["type"] == "battery_replace":
            return 2
        if state["active"] and state["battery_replace_indicator_override"] is not None:
            return state["battery_replace_indicator_override"]
        return self.simulator.battery_replace_indicator

    @property
    def output_load(self):
        state = self._alert_state.snapshot()
        if state["active"] and state["type"] == "high_load":
            return 900
        if state["active"] and state["output_load_override"] is not None:
            return state["output_load_override"]
        return self.simulator.output_load

    @property
    def input_frequency(self):
        return self.simulator.input_frequency

    @property
    def output_current(self):
        return self.simulator.output_current


_base_simulator = UPSSimulator()
_base_simulator.start(interval=1.0)
effective_simulator = UPSSimulatorWithOverrides(_base_simulator, _alert_state)

ZABBIX_SERVER = os.environ.get("ZABBIX_SERVER", "localhost")
ZABBIX_SNMP_TRAP_HOST = os.environ.get("ZABBIX_SNMP_TRAP_HOST", "localhost")
ZABBIX_SNMP_TRAP_PORT = int(os.environ.get("ZABBIX_SNMP_TRAP_PORT", 162))


class UPSMibInstrumController(instrum.AbstractMibInstrumController):

    def __init__(self, simulator):
        super().__init__()
        self.simulator = simulator
        self._oid_list = [
            BATTERY_CAPACITY_OID,
            INPUT_VOLTAGE_OID,
            OUTPUT_VOLTAGE_OID,
            BATTERY_STATUS_OID,
            UPS_STATUS_OID,
            SYSTEM_UPTIME_OID,
            SYSTEM_NAME_OID,
            OUTPUT_STATUS_OID,
            BATTERY_TEMPERATURE_OID,
            BATTERY_REPLACE_INDICATOR_OID,
            OUTPUT_LOAD_OID,
            INPUT_FREQUENCY_OID,
            OUTPUT_CURRENT_OID,
        ]

    def read_variables(self, *var_binds, **context):
        result = []
        for oid, _ in var_binds:
            oid_tuple = tuple(oid) if not isinstance(oid, tuple) else oid
            snmp_value = self._get_value(oid_tuple)
            if snmp_value is not None:
                result.append((oid, snmp_value))
            else:
                result.append((oid, v2c.no_such_object()))
        return result

    def read_next_variables(self, *var_binds, **context):
        result = []
        for oid, _ in var_binds:
            oid_tuple = tuple(oid) if not isinstance(oid, tuple) else oid
            next_oid, next_value = self._get_next(oid_tuple)
            if next_oid is not None:
                result.append((next_oid, next_value))
            else:
                result.append((oid, v2c.end_of_mib()))
        return result

    def _get_value(self, oid):
        oid_tuple = tuple(oid) if not isinstance(oid, tuple) else oid
        if oid_tuple == BATTERY_CAPACITY_OID:
            return v2c.Integer32(int(self.simulator.battery_capacity))
        if oid_tuple == INPUT_VOLTAGE_OID:
            return v2c.Integer32(self.simulator.input_voltage)
        if oid_tuple == OUTPUT_VOLTAGE_OID:
            return v2c.Integer32(self.simulator.output_voltage)
        if oid_tuple == BATTERY_STATUS_OID:
            return v2c.Integer32(self.simulator.battery_status)
        if oid_tuple == UPS_STATUS_OID:
            return v2c.Integer32(self.simulator.ups_status)
        if oid_tuple == SYSTEM_UPTIME_OID:
            return v2c.TimeTicks(self.simulator.system_uptime)
        if oid_tuple == SYSTEM_NAME_OID:
            return v2c.OctetString(self.simulator.system_name.encode())
        if oid_tuple == OUTPUT_STATUS_OID:
            return v2c.Integer32(self.simulator.output_status)
        if oid_tuple == BATTERY_TEMPERATURE_OID:
            return v2c.Integer32(self.simulator.battery_temperature)
        if oid_tuple == BATTERY_REPLACE_INDICATOR_OID:
            return v2c.Integer32(self.simulator.battery_replace_indicator)
        if oid_tuple == OUTPUT_LOAD_OID:
            return v2c.Integer32(self.simulator.output_load)
        if oid_tuple == INPUT_FREQUENCY_OID:
            return v2c.Integer32(self.simulator.input_frequency)
        if oid_tuple == OUTPUT_CURRENT_OID:
            return v2c.Integer32(self.simulator.output_current)
        return None

    def _get_next(self, oid):
        oid_tuple = tuple(oid) if not isinstance(oid, tuple) else oid
        for mib_oid in self._oid_list:
            if oid_tuple == mib_oid or oid_tuple < mib_oid:
                return mib_oid, self._get_value(mib_oid)
        return None, None


def _json_body_or_400():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None, (jsonify({"error": "Invalid or missing JSON body"}), 400)
    return data, None


def _parse_number(data, field, value_type="float", minimum=None, maximum=None):
    raw = data.get(field)
    if raw is None:
        return None, None
    try:
        value = float(raw) if value_type == "float" else int(raw)
    except (TypeError, ValueError):
        return None, f"Field {field} must be a valid {value_type}"
    if minimum is not None and value < minimum:
        return None, f"Field {field} must be >= {minimum}"
    if maximum is not None and value > maximum:
        return None, f"Field {field} must be <= {maximum}"
    return value, None


def _validate_override_field(field, value):
    if field not in DEFAULT_ALERT_STATE:
        return None, f"Invalid field: {field}"
    if field in {"active", "type"}:
        return None, f"Field {field} cannot be overridden directly"
    if value is None:
        return None, None

    value_type, minimum, maximum = OVERRIDE_SPECS[field]
    parsed, error = _parse_number({"value": value}, "value", value_type, minimum, maximum)
    if error:
        return None, error
    return parsed, None


def setup_snmp_agent(listen_addr=("0.0.0.0", 161), community="public"):
    snmp_engine = engine.SnmpEngine()
    config.add_transport(
        snmp_engine,
        udp.DOMAIN_NAME,
        udp.UdpTransport().open_server_mode(listen_addr),
    )
    config.add_v1_system(snmp_engine, "my-area", community)
    config.add_vacm_user(
        snmp_engine,
        2,
        "my-area",
        "noAuthNoPriv",
        (1, 3, 6, 1),
        (1, 3, 6, 1),
    )

    snmp_context = context.SnmpContext(snmp_engine)
    try:
        snmp_context.unregister_context_name(v2c.OctetString(b""))
    except Exception:
        pass

    mib_controller = UPSMibInstrumController(effective_simulator)
    snmp_context.register_context_name(v2c.OctetString(b""), mib_controller)
    cmdrsp.GetCommandResponder(snmp_engine, snmp_context)
    cmdrsp.NextCommandResponder(snmp_engine, snmp_context)
    return snmp_engine


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/status")
def api_status():
    alert_snapshot = _alert_state.snapshot()
    return jsonify(
        {
            "battery_capacity": effective_simulator.battery_capacity,
            "input_voltage": effective_simulator.input_voltage,
            "output_voltage": effective_simulator.output_voltage,
            "battery_status": effective_simulator.battery_status,
            "ups_status": effective_simulator.ups_status,
            "output_status": effective_simulator.output_status,
            "system_uptime": effective_simulator.system_uptime,
            "system_name": effective_simulator.system_name,
            "battery_temperature": effective_simulator.battery_temperature,
            "battery_replace_indicator": effective_simulator.battery_replace_indicator,
            "output_load": effective_simulator.output_load,
            "input_frequency": effective_simulator.input_frequency,
            "output_current": effective_simulator.output_current,
            "alert_active": alert_snapshot["active"],
            "alert_type": alert_snapshot["type"],
            "base_battery_capacity": _base_simulator.battery_capacity,
            "base_input_voltage": _base_simulator.input_voltage,
            "base_output_voltage": _base_simulator.output_voltage,
        }
    )


@app.route("/api/oids")
def api_oids():
    return jsonify({oid_to_str(oid): name for name, oid in UPS_MIB_MAP.items()})


@app.route("/api/alerts", methods=["GET"])
def api_alerts():
    return jsonify(_alert_state.snapshot())


@app.route("/api/alerts", methods=["POST"])
def api_alerts_post():
    data, error_response = _json_body_or_400()
    if error_response:
        return error_response

    if data.get("reset"):
        _alert_state.reset()
        return jsonify({"status": "reset"})

    alert_type = data.get("type")
    if alert_type not in VALID_ALERT_TYPES:
        return jsonify({"error": f"Invalid alert type. Must be one of: {VALID_ALERT_TYPES}"}), 400

    updates = {"active": True, "type": alert_type}
    if alert_type == "battery_low":
        updates["custom_battery"] = 15.0
    elif alert_type == "voltage_high":
        updates["custom_input_voltage"] = 1450
    elif alert_type == "voltage_low":
        updates["custom_input_voltage"] = 900
    elif alert_type == "on_battery":
        updates["ups_status_override"] = 3
        updates["output_status_override"] = 3
    elif alert_type == "high_temperature":
        updates["battery_temperature_override"] = 450
    elif alert_type == "battery_replace":
        updates["battery_replace_indicator_override"] = 2
    elif alert_type == "high_load":
        updates["output_load_override"] = 900
    elif alert_type == "output_timed_sleeping":
        updates["output_status_override"] = 5
    elif alert_type == "output_software_bypass":
        updates["output_status_override"] = 6
    elif alert_type == "output_off":
        updates["output_status_override"] = 7
    elif alert_type == "output_reboot":
        updates["output_status_override"] = 8
    elif alert_type == "output_switched_bypass":
        updates["output_status_override"] = 9
    elif alert_type == "output_hardware_bypass":
        updates["output_status_override"] = 10
    elif alert_type == "output_sleeping_power_return":
        updates["output_status_override"] = 11
    elif alert_type == "output_smart_trim":
        updates["output_status_override"] = 12
    elif alert_type == "output_smart_boost":
        updates["output_status_override"] = 4
    elif alert_type == "output_emergency_bypass":
        updates["output_status_override"] = 16
    elif alert_type == "system_restart":
        updates["system_uptime_override"] = 100
    elif alert_type == "custom":
        for field, (value_type, minimum, maximum) in OVERRIDE_SPECS.items():
            parsed, error = _parse_number(data, field, value_type, minimum, maximum)
            if error:
                return jsonify({"error": error}), 400
            if field in data:
                updates[field] = parsed

    alert = _alert_state.update(updates)
    return jsonify({"status": "applied", "alert": alert})


@app.route("/api/override", methods=["POST"])
def api_override():
    data, error_response = _json_body_or_400()
    if error_response:
        return error_response
    field = data.get("field")
    raw_value = data.get("value")
    parsed_value, error = _validate_override_field(field, raw_value)
    if error:
        return jsonify({"error": error}), 400

    _alert_state.update({"active": True, "type": "custom", field: parsed_value})
    return jsonify({"status": "ok", "field": field, "value": parsed_value})


@app.route("/api/simulation/interval", methods=["POST"])
def api_simulation_interval():
    data, error_response = _json_body_or_400()
    if error_response:
        return error_response

    interval, error = _parse_number(data, "interval", "float", 0.5, None)
    if error:
        return jsonify({"error": error}), 400
    if interval is None:
        interval = 5.0

    _base_simulator.stop()
    _base_simulator.start(interval=interval)
    return jsonify({"status": "ok", "interval": interval})


@app.route("/api/zabbix/config", methods=["GET"])
def api_zabbix_config():
    return jsonify(
        {
            "server": ZABBIX_SERVER,
            "snmp_trap_host": ZABBIX_SNMP_TRAP_HOST,
            "snmp_trap_port": ZABBIX_SNMP_TRAP_PORT,
        }
    )


@app.route("/api/zabbix/config", methods=["POST"])
def api_zabbix_config_post():
    global ZABBIX_SERVER, ZABBIX_SNMP_TRAP_HOST, ZABBIX_SNMP_TRAP_PORT
    data, error_response = _json_body_or_400()
    if error_response:
        return error_response

    if "server" in data:
        if not isinstance(data["server"], str) or not data["server"].strip():
            return jsonify({"error": "server must be a non-empty string"}), 400
        ZABBIX_SERVER = data["server"]
    if "snmp_trap_host" in data:
        if not isinstance(data["snmp_trap_host"], str) or not data["snmp_trap_host"].strip():
            return jsonify({"error": "snmp_trap_host must be a non-empty string"}), 400
        ZABBIX_SNMP_TRAP_HOST = data["snmp_trap_host"]
    if "snmp_trap_port" in data:
        try:
            port = int(data["snmp_trap_port"])
        except (TypeError, ValueError):
            return jsonify({"error": "snmp_trap_port must be an integer"}), 400
        if port < 1 or port > 65535:
            return jsonify({"error": "snmp_trap_port must be between 1 and 65535"}), 400
        ZABBIX_SNMP_TRAP_PORT = port

    return jsonify(
        {
            "status": "ok",
            "server": ZABBIX_SERVER,
            "snmp_trap_host": ZABBIX_SNMP_TRAP_HOST,
            "snmp_trap_port": ZABBIX_SNMP_TRAP_PORT,
        }
    )


def run_snmp_thread(listen_addr=("0.0.0.0", 161), community="public"):
    import asyncio

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    snmp_engine = setup_snmp_agent(listen_addr, community)
    print(f"[SNMP] Agent iniciado en {listen_addr[0]}:{listen_addr[1]}")
    print(f"[SNMP] Community: {community}")
    print("[SNMP] OIDs:")
    for name, oid in UPS_MIB_MAP.items():
        print(f"[SNMP]   {name}: {oid_to_str(oid)}")
    try:
        loop.run_until_complete(snmp_engine.transport_dispatcher.run_dispatcher())
    except KeyboardInterrupt:
        snmp_engine.transport_dispatcher.close_dispatcher()
    finally:
        loop.close()


if __name__ == "__main__":
    snmp_thread = threading.Thread(target=run_snmp_thread, daemon=True)
    snmp_thread.start()
    print("[WEB] UPS Alert Simulator disponible en http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
