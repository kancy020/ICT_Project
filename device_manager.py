import threading
from abc import ABC, abstractmethod

class IDeviceManager(ABC):
    @abstractmethod
    def get_devices(self):
        pass
    
    @abstractmethod
    def toggle_power(self, device_id):
        pass
    
    @abstractmethod
    def toggle_disable(self, device_id):
        pass

class DeviceManager(IDeviceManager):
    def __init__(self):
        self.devices = [
            {"id": 0, "name": "Device A", "status": "Idle", "disabled": False, "type": "screen"},
            {"id": 1, "name": "Device B", "status": "Idle", "disabled": False, "type": "screen"}
        ]
        self.lock = threading.Lock()

    def get_devices(self):
        with self.lock:
            return [d.copy() for d in self.devices]

    def toggle_power(self, device_id):
        with self.lock:
            for device in self.devices:
                if device["id"] == device_id:
                    device["status"] = "Off" if device["status"] == "Idle" else "Idle"
                    return True
        return False

    def toggle_disable(self, device_id):
        with self.lock:
            for device in self.devices:
                if device["id"] == device_id:
                    device["disabled"] = not device["disabled"]
                    return True
        return False
