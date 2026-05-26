"""
Simulador dinamico de valores para UPS APC Smart-UPS.
Genera valores realistas con pequenas fluctuaciones.
"""
import random
import threading
import time


class UPSSimulator:
    """
    Simula el comportamiento dinamico de una UPS APC Smart-UPS.
    Genera valores que fluctuan de manera realista.
    """

    def __init__(self):
        self._battery_capacity = 100.0       # 0-100%
        self._input_voltage = 1200          # 0.1V units (120.0V)
        self._output_voltage = 1300          # 0.1V units (130.0V)
        self._battery_status = 2             # 2=Normal, 3=Low, 4=Fault
        self._ups_status = 2                  # 2=Online, 3=OnBattery
        self._output_status = 2               # 2=Online
        self._system_uptime = 8640000        # 100 dias en centisegundos
        self._system_name = "APC-Sim-UPS-001"
        self._battery_temperature = 260       # 0.1°C units (26.0°C)
        self._battery_replace_indicator = 1   # 1=NoReplace
        self._output_load = 500               # 0.1% units (50.0%)
        self._input_frequency = 596           # 0.1Hz units (59.6Hz)
        self._output_current = 80             # 0.1A units (8.0A)
        self._lock = threading.Lock()
        self._running = False
        self._thread = None

    def start(self, interval=5.0):
        """Inicia el loop de simulacion en un thread en segundo plano."""
        self._running = True
        self._thread = threading.Thread(target=self._simulation_loop, args=(interval,), daemon=True)
        self._thread.start()

    def stop(self):
        """Detiene la simulacion."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)

    def _simulation_loop(self, interval):
        pass

    @property
    def battery_capacity(self):
        with self._lock:
            return self._battery_capacity

    @property
    def input_voltage(self):
        with self._lock:
            return self._input_voltage

    @property
    def output_voltage(self):
        with self._lock:
            return self._output_voltage

    @property
    def battery_status(self):
        with self._lock:
            return self._battery_status

    @property
    def ups_status(self):
        with self._lock:
            return self._ups_status

    @property
    def output_status(self):
        with self._lock:
            return self._output_status

    @property
    def system_uptime(self):
        with self._lock:
            return self._system_uptime

    @property
    def system_name(self):
        with self._lock:
            return self._system_name

    @property
    def battery_temperature(self):
        with self._lock:
            return self._battery_temperature

    @property
    def battery_replace_indicator(self):
        with self._lock:
            return self._battery_replace_indicator

    @property
    def output_load(self):
        with self._lock:
            return self._output_load

    @property
    def input_frequency(self):
        with self._lock:
            return self._input_frequency

    @property
    def output_current(self):
        with self._lock:
            return self._output_current