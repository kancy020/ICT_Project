import json
import os
import subprocess
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional

class DeviceManager:
    """Device management class: manages device CRUD and status monitoring"""
    """This class requires the administrator to manually enter device information"""
    
    def __init__(self, config_file: str = None):
        import os
        data_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'data'))
        self.config_file = config_file or os.path.join(data_dir, "devices.json")
        self.devices = {}
        self.status_thread = None
        self.monitoring = False
        self.load_devices()
        
    def load_devices(self):
        """Load device list from config file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.devices = json.load(f)
                print(f"Loaded {len(self.devices)} devices")
            else:
                self.devices = {}
                self.save_devices()
        except Exception as e:
            print(f"Failed to load device config: {e}")
            self.devices = {}
    
    def save_devices(self):
        """Save device list to config file"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.devices, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Failed to save device config: {e}")
    
    def add_device(self, device_id: str, device_info: Dict) -> bool:
        """
        Add new device
        :param device_id: Device ID
        :param device_info: Device info dict containing name, ip, mac, type etc.
        :return: Whether addition was successful
        """
        try:
            if device_id in self.devices:
                print(f"Device {device_id} already exists")
                return False
            
            # Standardized device info format
            device_data = {
                "name": device_info.get("name", device_id),
                "ip": device_info.get("ip", ""),
                "mac": device_info.get("mac", ""),
                "type": device_info.get("type", "pixel_display"),
                "enabled": device_info.get("enabled", True),
                "status": "unknown",  # online/offline/unknown
                "last_seen": None,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            self.devices[device_id] = device_data
            self.save_devices()
            print(f"Device {device_id} added successfully")
            return True
            
        except Exception as e:
            print(f"Failed to add device: {e}")
            return False
    
    def remove_device(self, device_id: str) -> bool:
        """Remove device"""
        try:
            if device_id not in self.devices:
                print(f"Device {device_id} doesn't exist")
                return False
            
            del self.devices[device_id]
            self.save_devices()
            print(f"Device {device_id} removed successfully")
            return True
            
        except Exception as e:
            print(f"Failed to remove device: {e}")
            return False
    
    def update_device(self, device_id: str, device_info: Dict) -> bool:
        """Update device information"""
        try:
            if device_id not in self.devices:
                print(f"Device {device_id} doesn't exist")
                return False
            
            # Update device info
            for key, value in device_info.items():
                if key in ["name", "ip", "mac", "type", "enabled"]:
                    self.devices[device_id][key] = value
            
            self.devices[device_id]["updated_at"] = datetime.now().isoformat()
            self.save_devices()
            print(f"Device {device_id} updated successfully")
            return True
            
        except Exception as e:
            print(f"Failed to update device: {e}")
            return False
    
    def disable_device(self, device_id: str) -> bool:
        """Disable specific device"""
        try:
            if device_id not in self.devices:
                print(f"Device {device_id} doesn't exist")
                return False
            
            self.devices[device_id]["enabled"] = False
            self.devices[device_id]["updated_at"] = datetime.now().isoformat()
            self.save_devices()
            print(f"Device {device_id} disabled")
            return True
            
        except Exception as e:
            print(f"Failed to disable device: {e}")
            return False
    
    def enable_device(self, device_id: str) -> bool:
        """Enable specific device"""
        try:
            if device_id not in self.devices:
                print(f"Device {device_id} doesn't exist")
                return False
            
            self.devices[device_id]["enabled"] = True
            self.devices[device_id]["updated_at"] = datetime.now().isoformat()
            self.save_devices()
            print(f"Device {device_id} enabled")
            return True
            
        except Exception as e:
            print(f"Failed to enable device: {e}")
            return False
    
    def get_device(self, device_id: str) -> Optional[Dict]:
        """Get single device info"""
        return self.devices.get(device_id)
    
    def get_all_devices(self) -> Dict:
        """Get all device info"""
        return self.devices.copy()
    
    def get_enabled_devices(self) -> Dict:
        """Get all enabled devices"""
        return {k: v for k, v in self.devices.items() if v.get("enabled", True)}
    
    def check_device_status(self, device_id: str) -> str:
        """Check single device status"""
        try:
            device = self.devices.get(device_id)
            if not device:
                return "unknown"
            
            ip = device.get("ip")
            if not ip:
                return "no_ip"
            
            # Use ping to check device status
            result = subprocess.run(
                ["ping", ip, "-c", "1", "-W", "2", "-q"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            status = "online" if result.returncode == 0 else "offline"
            
            # Update device status
            self.devices[device_id]["status"] = status
            if status == "online":
                self.devices[device_id]["last_seen"] = datetime.now().isoformat()
            
            return status
            
        except Exception as e:
            print(f"Failed to check device status: {e}")
            return "error"
    
    def start_monitoring(self, interval: int = 30):
        """Start monitoring device status"""
        if self.monitoring:
            print("Device monitoring already running")
            return
        
        self.monitoring = True
        self.status_thread = threading.Thread(target=self._monitor_devices, args=(interval,))
        self.status_thread.daemon = True
        self.status_thread.start()
        print("Device status monitoring started")
    
    def stop_monitoring(self):
        """Stop monitoring device status"""
        self.monitoring = False
        if self.status_thread:
            self.status_thread.join(timeout=5)
        print("Device status monitoring stopped")
    
    def _monitor_devices(self, interval: int):
        """Background device status monitoring"""
        while self.monitoring:
            try:
                for device_id in list(self.devices.keys()):
                    if not self.monitoring:
                        break
                    
                    if self.devices[device_id].get("enabled", True):
                        old_status = self.devices[device_id].get("status", "unknown")
                        new_status = self.check_device_status(device_id)
                        
                        # Log when status changes
                        if old_status != new_status:
                            print(f"Device {device_id} status changed: {old_status} -> {new_status}")
                
                # Save updated device status
                self.save_devices()
                
            except Exception as e:
                print(f"Error while monitoring device status: {e}")
            
            # Wait for specified interval
            for _ in range(interval):
                if not self.monitoring:
                    break
                time.sleep(1)
    
    def send_command_to_device(self, device_id: str, command: str) -> bool:
        """Send special command to device (turn on/off etc.)"""
        try:
            device = self.devices.get(device_id)
            if not device:
                print(f"Device {device_id} doesn't exist")
                return False
            
            if not device.get("enabled", True):
                print(f"Device {device_id} is disabled")
                return False
            
            mac_address = device.get("mac")
            if not mac_address:
                print(f"Device {device_id} has no MAC address")
                return False
            
            # Execute different operations based on command type
            if command == "turn_on":
                cmd = f"python .\\app.py --address {mac_address} --screen on"
            elif command == "turn_off":
                cmd = f"python .\\app.py --address {mac_address} --screen off"
            else:
                print(f"Unknown command: {command}")
                return False
            
            result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
            print(f"Command {command} executed successfully for device {device_id}")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"Failed to execute device command: {e}")
            return False
        except Exception as e:
            print(f"Error sending command to device: {e}")
            return False
    
    def get_device_statistics(self) -> Dict:
        """Get device statistics"""
        total = len(self.devices)
        enabled = sum(1 for d in self.devices.values() if d.get("enabled", True))
        online = sum(1 for d in self.devices.values() if d.get("status") == "online")
        offline = sum(1 for d in self.devices.values() if d.get("status") == "offline")
        unknown = sum(1 for d in self.devices.values() if d.get("status") == "unknown")
        
        return {
            "total": total,
            "enabled": enabled,
            "disabled": total - enabled,
            "online": online,
            "offline": offline,
            "unknown": unknown
        }

# Usage example
if __name__ == "__main__":
    dm = DeviceManager()
    
    # Add example device
    dm.add_device("pixel_01", {
        "name": "Pixel Display 1",
        "ip": "192.168.68.110",
        "mac": "AA:BB:CC:DD:EE:FF",
        "type": "pixel_display"
    })
    
    # Start monitoring
    dm.start_monitoring(interval=10)
    
    try:
        time.sleep(60)  # Run for 1 minute
    except KeyboardInterrupt:
        pass
    finally:
        dm.stop_monitoring()

def toggle_power(self, device_id: str) -> bool:
        """Toggle power state of a device"""
        device = self.get_device(device_id)
        if not device:
            print(f"Device {device_id} not found")
            return False

        if device.get("enabled", True):
            return self.send_command_to_device(device_id, "turn_off")
        else:
            return self.send_command_to_device(device_id, "turn_on")
