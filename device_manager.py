import threading
import json
import os
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
    def __init__(self, config_file="configs/devices.json"):
        self.lock = threading.Lock()
        self.config_file = config_file
        self._load_devices()

    def _load_devices(self):
        """从配置文件加载设备"""
        default_devices = [
            {
                "id": 0,
                "name": "RaspberryPixel",
                "status": "Idle",
                "disabled": False,
                "type": "pixel_screen",
                "ip": "192.168.68.110"
            }
        ]
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file) as f:
                    self.devices = json.load(f)
            else:
                self.devices = default_devices
        except Exception:
            self.devices = default_devices

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
