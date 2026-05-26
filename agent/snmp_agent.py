#!/usr/bin/env python3
"""
SNMP Agent Simulator para APC Smart-UPS usando PowerNet MIB.
Responde a peticiones GET y GETNEXT con valores simulados dinámicamente.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from pysnmp.entity import engine, config
from pysnmp.entity.rfc3413 import cmdrsp, context
from pysnmp.carrier.asyncio.dgram import udp
from pysnmp.proto.api import v2c
from pysnmp.smi import instrum

from ups_simulation import UPSSimulator
from ups_mib import (
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
    UPS_MIB_MAP,
    oid_to_str,
)


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
        for oid, value in var_binds:
            oid_tuple = tuple(oid) if not isinstance(oid, tuple) else oid
            snmp_value = self._get_value(oid_tuple)
            if snmp_value is not None:
                result.append((oid, snmp_value))
            else:
                result.append((oid, v2c.no_such_object()))
        return result

    def read_next_variables(self, *var_binds, **context):
        result = []
        for oid, value in var_binds:
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
        elif oid_tuple == INPUT_VOLTAGE_OID:
            return v2c.Integer32(self.simulator.input_voltage)
        elif oid_tuple == OUTPUT_VOLTAGE_OID:
            return v2c.Integer32(self.simulator.output_voltage)
        elif oid_tuple == BATTERY_STATUS_OID:
            return v2c.Integer32(self.simulator.battery_status)
        elif oid_tuple == UPS_STATUS_OID:
            return v2c.Integer32(self.simulator.ups_status)
        elif oid_tuple == SYSTEM_UPTIME_OID:
            return v2c.TimeTicks(self.simulator.system_uptime)
        elif oid_tuple == SYSTEM_NAME_OID:
            return v2c.OctetString(self.simulator.system_name.encode())
        elif oid_tuple == OUTPUT_STATUS_OID:
            return v2c.Integer32(self.simulator.output_status)
        elif oid_tuple == BATTERY_TEMPERATURE_OID:
            return v2c.Integer32(self.simulator.battery_temperature)
        elif oid_tuple == BATTERY_REPLACE_INDICATOR_OID:
            return v2c.Integer32(self.simulator.battery_replace_indicator)
        elif oid_tuple == OUTPUT_LOAD_OID:
            return v2c.Integer32(self.simulator.output_load)
        elif oid_tuple == INPUT_FREQUENCY_OID:
            return v2c.Integer32(self.simulator.input_frequency)
        elif oid_tuple == OUTPUT_CURRENT_OID:
            return v2c.Integer32(self.simulator.output_current)
        return None

    def _get_next(self, oid):
        oid_tuple = tuple(oid) if not isinstance(oid, tuple) else oid

        for mib_oid in self._oid_list:
            if oid_tuple == mib_oid:
                return mib_oid, self._get_value(mib_oid)
            elif oid_tuple < mib_oid:
                return mib_oid, self._get_value(mib_oid)
        return None, None


class UPSAgent:

    def __init__(self, listen_addr=('0.0.0.0', 161), community='public'):
        self.snmpEngine = engine.SnmpEngine()
        self.community = community
        self.listen_addr = listen_addr
        self.simulator = UPSSimulator()

        self._setup_transport()
        self._setup_auth()
        self._setup_context()
        self._setup_responders()

    def _setup_transport(self):
        config.add_transport(
            self.snmpEngine,
            udp.DOMAIN_NAME,
            udp.UdpTransport().open_server_mode(self.listen_addr)
        )

    def _setup_auth(self):
        config.add_v1_system(
            self.snmpEngine,
            'my-area',
            self.community
        )
        config.add_vacm_user(
            self.snmpEngine,
            2,
            'my-area',
            'noAuthNoPriv',
            (1, 3, 6, 1),
            (1, 3, 6, 1)
        )

    def _setup_context(self):
        self.snmpContext = context.SnmpContext(self.snmpEngine)

        try:
            self.snmpContext.unregister_context_name(v2c.OctetString(b''))
        except Exception:
            pass

        self.mib_controller = UPSMibInstrumController(self.simulator)
        self.snmpContext.register_context_name(
            v2c.OctetString(b''),
            self.mib_controller
        )

    def _setup_responders(self):
        cmdrsp.GetCommandResponder(self.snmpEngine, self.snmpContext)
        cmdrsp.NextCommandResponder(self.snmpEngine, self.snmpContext)

    def start(self):
        self.simulator.start(interval=5.0)
        self.snmpEngine.transport_dispatcher.job_started(1)

        print(f"UPS SNMP Agent iniciado en {self.listen_addr[0]}:{self.listen_addr[1]}")
        print(f"Community string: {self.community}")
        print(f"OIDs disponibles:")
        for name, oid in UPS_MIB_MAP.items():
            print(f"  - {oid_to_str(oid)} ({name})")
        print()

        try:
            self.snmpEngine.transport_dispatcher.run_dispatcher()
        except KeyboardInterrupt:
            print("\nDeteniendo agente...")
            self.simulator.stop()
            self.snmpEngine.transport_dispatcher.close_dispatcher()
            print("Agente detenido.")


def main():
    agent = UPSAgent(
        listen_addr=('0.0.0.0', 161),
        community='public'
    )
    agent.start()


if __name__ == '__main__':
    main()
