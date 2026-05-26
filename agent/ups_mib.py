# APC PowerNet MIB OID Constants
# Reference: APC PowerNet MIB (OID 1.3.6.1.4.1.318)
#
# Battery OIDs:     1.3.6.1.4.1.318.1.1.1.2
# Input OIDs:       1.3.6.1.4.1.318.1.1.1.3
# Output OIDs:      1.3.6.1.4.1.318.1.1.1.4
# UPS Status OIDs:  1.3.6.1.4.1.318.1.1.1.1

APCNET_BASE = (1, 3, 6, 1, 4, 1, 318)
SNMPv2_BASE = (1, 3, 6, 1, 2, 1, 1)

# OID tuples for UPS metrics
BATTERY_CAPACITY_OID = APCNET_BASE + (1, 1, 1, 2, 2, 1, 0)   # 1.3.6.1.4.1.318.1.1.1.2.2.1.0
INPUT_VOLTAGE_OID = APCNET_BASE + (1, 1, 1, 3, 2, 1, 0)        # 1.3.6.1.4.1.318.1.1.1.3.2.1.0
OUTPUT_VOLTAGE_OID = APCNET_BASE + (1, 1, 1, 4, 2, 1, 0)      # 1.3.6.1.4.1.318.1.1.1.4.2.1.0
BATTERY_STATUS_OID = APCNET_BASE + (1, 1, 1, 2, 1, 1, 0)      # 1.3.6.1.4.1.318.1.1.1.2.1.1.0
UPS_STATUS_OID = APCNET_BASE + (1, 1, 1, 1, 1, 0)             # 1.3.6.1.4.1.318.1.1.1.1.1.0

# Additional OIDs for full trigger support
SYSTEM_UPTIME_OID = SNMPv2_BASE + (3, 0)                       # 1.3.6.1.2.1.1.3.0
SYSTEM_NAME_OID = SNMPv2_BASE + (5, 0)                        # 1.3.6.1.2.1.1.5.0
OUTPUT_STATUS_OID = APCNET_BASE + (1, 1, 1, 4, 1, 1, 0)       # 1.3.6.1.4.1.318.1.1.1.4.1.1.0
BATTERY_TEMPERATURE_OID = APCNET_BASE + (1, 1, 1, 2, 3, 2, 0) # 1.3.6.1.4.1.318.1.1.1.2.3.2.0
BATTERY_REPLACE_INDICATOR_OID = APCNET_BASE + (1, 1, 1, 2, 2, 4, 0) # 1.3.6.1.4.1.318.1.1.1.2.2.4.0
OUTPUT_LOAD_OID = APCNET_BASE + (1, 1, 1, 4, 3, 3, 0)          # 1.3.6.1.4.1.318.1.1.1.4.3.3.0
INPUT_FREQUENCY_OID = APCNET_BASE + (1, 1, 1, 3, 3, 4, 0)     # 1.3.6.1.4.1.318.1.1.1.3.3.4.0
OUTPUT_CURRENT_OID = APCNET_BASE + (1, 1, 1, 4, 3, 4, 0)       # 1.3.6.1.4.1.318.1.1.1.4.3.4.0

# MIB name to OID mapping
UPS_MIB_MAP = {
    'batteryCapacity': BATTERY_CAPACITY_OID,
    'inputVoltage': INPUT_VOLTAGE_OID,
    'outputVoltage': OUTPUT_VOLTAGE_OID,
    'batteryStatus': BATTERY_STATUS_OID,
    'upsStatus': UPS_STATUS_OID,
    'systemUptime': SYSTEM_UPTIME_OID,
    'systemName': SYSTEM_NAME_OID,
    'outputStatus': OUTPUT_STATUS_OID,
    'batteryTemperature': BATTERY_TEMPERATURE_OID,
    'batteryReplaceIndicator': BATTERY_REPLACE_INDICATOR_OID,
    'outputLoad': OUTPUT_LOAD_OID,
    'inputFrequency': INPUT_FREQUENCY_OID,
    'outputCurrent': OUTPUT_CURRENT_OID,
}

# Human-readable OID strings (dot notation)
def oid_to_str(oid_tuple):
    return '.'.join(str(x) for x in oid_tuple)

BATTERY_CAPACITY_STR = oid_to_str(BATTERY_CAPACITY_OID)
INPUT_VOLTAGE_STR = oid_to_str(INPUT_VOLTAGE_OID)
OUTPUT_VOLTAGE_STR = oid_to_str(OUTPUT_VOLTAGE_OID)
BATTERY_STATUS_STR = oid_to_str(BATTERY_STATUS_OID)
UPS_STATUS_STR = oid_to_str(UPS_STATUS_OID)
SYSTEM_UPTIME_STR = oid_to_str(SYSTEM_UPTIME_OID)
SYSTEM_NAME_STR = oid_to_str(SYSTEM_NAME_OID)
OUTPUT_STATUS_STR = oid_to_str(OUTPUT_STATUS_OID)
BATTERY_TEMPERATURE_STR = oid_to_str(BATTERY_TEMPERATURE_OID)
BATTERY_REPLACE_INDICATOR_STR = oid_to_str(BATTERY_REPLACE_INDICATOR_OID)
OUTPUT_LOAD_STR = oid_to_str(OUTPUT_LOAD_OID)
INPUT_FREQUENCY_STR = oid_to_str(INPUT_FREQUENCY_OID)
OUTPUT_CURRENT_STR = oid_to_str(OUTPUT_CURRENT_OID)