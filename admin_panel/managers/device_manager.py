import json
import os
import subprocess
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional

class DeviceManager:
    """设备管理类：管理设备的增删改和状态监控"""
    
    def __init__(self, config_file: str = None):
        import os
        data_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'data'))
        self.config_file = config_file or os.path.join(data_dir, "devices.json")
        self.devices = {}
        self.status_thread = None
        self.monitoring = False
        self.load_devices()
        
    def load_devices(self):
        """从配置文件加载设备列表"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.devices = json.load(f)
                print(f"已加载 {len(self.devices)} 个设备")
            else:
                self.devices = {}
                self.save_devices()
        except Exception as e:
            print(f"加载设备配置失败: {e}")
            self.devices = {}
    
    def save_devices(self):
        """保存设备列表到配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.devices, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存设备配置失败: {e}")
    
    def add_device(self, device_id: str, device_info: Dict) -> bool:
        """
        添加新设备
        :param device_id: 设备ID
        :param device_info: 设备信息字典，包含name, ip, mac, type等
        :return: 是否添加成功
        """
        try:
            if device_id in self.devices:
                print(f"设备 {device_id} 已存在")
                return False
            
            # 固定格式的设备信息
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
            print(f"设备 {device_id} 添加成功")
            return True
            
        except Exception as e:
            print(f"添加设备失败: {e}")
            return False
    
    def remove_device(self, device_id: str) -> bool:
        """删除设备"""
        try:
            if device_id not in self.devices:
                print(f"设备 {device_id} 不存在")
                return False
            
            del self.devices[device_id]
            self.save_devices()
            print(f"设备 {device_id} 删除成功")
            return True
            
        except Exception as e:
            print(f"删除设备失败: {e}")
            return False
    
    def update_device(self, device_id: str, device_info: Dict) -> bool:
        """更新设备信息"""
        try:
            if device_id not in self.devices:
                print(f"设备 {device_id} 不存在")
                return False
            
            # 更新设备信息
            for key, value in device_info.items():
                if key in ["name", "ip", "mac", "type", "enabled"]:
                    self.devices[device_id][key] = value
            
            self.devices[device_id]["updated_at"] = datetime.now().isoformat()
            self.save_devices()
            print(f"设备 {device_id} 更新成功")
            return True
            
        except Exception as e:
            print(f"更新设备失败: {e}")
            return False
    
    def disable_device(self, device_id: str) -> bool:
        """禁用特定设备"""
        try:
            if device_id not in self.devices:
                print(f"设备 {device_id} 不存在")
                return False
            
            self.devices[device_id]["enabled"] = False
            self.devices[device_id]["updated_at"] = datetime.now().isoformat()
            self.save_devices()
            print(f"设备 {device_id} 已禁用")
            return True
            
        except Exception as e:
            print(f"禁用设备失败: {e}")
            return False
    
    def enable_device(self, device_id: str) -> bool:
        """启用特定设备"""
        try:
            if device_id not in self.devices:
                print(f"设备 {device_id} 不存在")
                return False
            
            self.devices[device_id]["enabled"] = True
            self.devices[device_id]["updated_at"] = datetime.now().isoformat()
            self.save_devices()
            print(f"设备 {device_id} 已启用")
            return True
            
        except Exception as e:
            print(f"启用设备失败: {e}")
            return False
    
    def get_device(self, device_id: str) -> Optional[Dict]:
        """获取单个设备信息"""
        return self.devices.get(device_id)
    
    def get_all_devices(self) -> Dict:
        """获取所有设备信息"""
        return self.devices.copy()
    
    def get_enabled_devices(self) -> Dict:
        """获取所有启用的设备"""
        return {k: v for k, v in self.devices.items() if v.get("enabled", True)}
    
    def check_device_status(self, device_id: str) -> str:
        """检查单个设备状态"""
        try:
            device = self.devices.get(device_id)
            if not device:
                return "unknown"
            
            ip = device.get("ip")
            if not ip:
                return "no_ip"
            
            # 使用ping检查设备状态
            result = subprocess.run(
                ["ping", ip, "-c", "1", "-W", "2", "-q"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            status = "online" if result.returncode == 0 else "offline"
            
            # 更新设备状态
            self.devices[device_id]["status"] = status
            if status == "online":
                self.devices[device_id]["last_seen"] = datetime.now().isoformat()
            
            return status
            
        except Exception as e:
            print(f"检查设备状态失败: {e}")
            return "error"
    
    def start_monitoring(self, interval: int = 30):
        """开始监控设备状态"""
        if self.monitoring:
            print("设备监控已在运行")
            return
        
        self.monitoring = True
        self.status_thread = threading.Thread(target=self._monitor_devices, args=(interval,))
        self.status_thread.daemon = True
        self.status_thread.start()
        print("设备状态监控已启动")
    
    def stop_monitoring(self):
        """停止监控设备状态"""
        self.monitoring = False
        if self.status_thread:
            self.status_thread.join(timeout=5)
        print("设备状态监控已停止")
    
    def _monitor_devices(self, interval: int):
        """后台监控设备状态"""
        while self.monitoring:
            try:
                for device_id in list(self.devices.keys()):
                    if not self.monitoring:
                        break
                    
                    if self.devices[device_id].get("enabled", True):
                        old_status = self.devices[device_id].get("status", "unknown")
                        new_status = self.check_device_status(device_id)
                        
                        # 状态变化时记录日志
                        if old_status != new_status:
                            print(f"设备 {device_id} 状态变化: {old_status} -> {new_status}")
                
                # 保存更新的设备状态
                self.save_devices()
                
            except Exception as e:
                print(f"监控设备状态时出错: {e}")
            
            # 等待指定间隔
            for _ in range(interval):
                if not self.monitoring:
                    break
                time.sleep(1)
    
    def send_command_to_device(self, device_id: str, command: str) -> bool:
        """向设备发送特殊命令（开关等）"""
        try:
            device = self.devices.get(device_id)
            if not device:
                print(f"设备 {device_id} 不存在")
                return False
            
            if not device.get("enabled", True):
                print(f"设备 {device_id} 已禁用")
                return False
            
            mac_address = device.get("mac")
            if not mac_address:
                print(f"设备 {device_id} 没有MAC地址")
                return False
            
            # 根据命令类型执行不同操作
            if command == "turn_on":
                cmd = f"python .\\app.py --address {mac_address} --screen on"
            elif command == "turn_off":
                cmd = f"python .\\app.py --address {mac_address} --screen off"
            else:
                print(f"未知命令: {command}")
                return False
            
            result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
            print(f"设备 {device_id} 命令 {command} 执行成功")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"设备命令执行失败: {e}")
            return False
        except Exception as e:
            print(f"发送设备命令时出错: {e}")
            return False
    
    def get_device_statistics(self) -> Dict:
        """获取设备统计信息"""
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

# 使用示例
if __name__ == "__main__":
    dm = DeviceManager()
    
    # 添加示例设备
    dm.add_device("pixel_01", {
        "name": "Pixel Display 1",
        "ip": "192.168.68.110",
        "mac": "AA:BB:CC:DD:EE:FF",
        "type": "pixel_display"
    })
    
    # 开始监控
    dm.start_monitoring(interval=10)
    
    try:
        time.sleep(60)  # 运行1分钟
    except KeyboardInterrupt:
        pass
    finally:
        dm.stop_monitoring()
