import smbus
import time

class Battery:
    def __init__(self, address=0x10, bus_number=1, cache_duration=5):
        self.addr = address
        self.bus = smbus.SMBus(bus_number)
        self.cache_duration = cache_duration
        self._last_update = 0
        self._voltage = None
        self._percentage = None

    def _update_values(self):
        current_time = time.time()
        if current_time - self._last_update > self.cache_duration:
            self._voltage = self._read_voltage()
            self._percentage = self._read_soc()
            self._last_update = current_time

    def _read_voltage(self):
        vcellH = self.bus.read_byte_data(self.addr, 0x03)
        vcellL = self.bus.read_byte_data(self.addr, 0x04)
        return (((vcellH & 0x0F) << 8) + vcellL) * 0.00125

    def _read_soc(self):
        socH = self.bus.read_byte_data(self.addr, 0x05)
        socL = self.bus.read_byte_data(self.addr, 0x06)
        return ((socH << 8) + socL) * 0.003906

    @property
    def voltage(self):
        self._update_values()
        return self._voltage

    @property
    def percentage(self):
        self._update_values()
        return self._percentage