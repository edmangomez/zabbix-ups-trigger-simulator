"""Test SNMP GET and GETNEXT against the running agent."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agent'))

from pysnmp.hlapi import getCmd, nextCmd, SnmpEngine, CommunityData, UdpTransportTarget, ContextData, ObjectType, ObjectIdentity

target = UdpTransportTarget(('localhost', 161), timeout=3, retries=2)
community = CommunityData('public')
context = ContextData()

oids = [
    '1.3.6.1.4.1.318.1.1.1.2.2.1.0',  # battery capacity
    '1.3.6.1.4.1.318.1.1.1.3.2.1.0',  # input voltage
    '1.3.6.1.4.1.318.1.1.1.4.2.1.0',  # output voltage
    '1.3.6.1.4.1.318.1.1.1.2.1.1.0',  # battery status
    '1.3.6.1.4.1.318.1.1.1.1.1.0',    # ups status
    '1.3.6.1.2.1.1.3.0',              # system uptime
    '1.3.6.1.4.1.318.1.1.1.4.1.1.0',  # output status
]

print("=== SNMP GET ===")
for oid_str in oids:
    iterator = getCmd(
        SnmpEngine(),
        community,
        target,
        context,
        ObjectType(ObjectIdentity(oid_str))
    )
    errorIndication, errorStatus, errorIndex, varBindTable = next(iterator)
    if errorIndication:
        print(f"ERROR: {errorIndication}")
    else:
        for varBind in varBindTable:
            print(f"  {varBind[0]} = {varBind[1]}")

print("\n=== SNMP GETNEXT ===")
iterator = nextCmd(
    SnmpEngine(),
    community,
    target,
    context,
    ObjectType(ObjectIdentity('1.3.6.1.4.1.318.1.1.1.2.2.1.0')),
    lexicographicMode=False
)
try:
    errorIndication, errorStatus, errorIndex, varBindTable = next(iterator)
    if errorIndication:
        print(f"ERROR: {errorIndication}")
    else:
        for varBind in varBindTable:
            print(f"  {varBind[0]} = {varBind[1]}")
except StopIteration:
    print("No more OIDs")