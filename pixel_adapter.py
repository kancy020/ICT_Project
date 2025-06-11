import requests
from typing import Dict, Any
import device_manager  # 修改为模块导入方式

class RaspberryPixelAdapter:
    def __init__(self, device_manager):  # 改为接收device_manager参数
        self.headers = {"Content-Type": "application/json"}
        self.device_manager = device_manager
        
    def _send_to_pi(self, payload: Dict[str, Any], device_id=0):
        """向树莓派发送指令"""
        devices = self.device_manager.get_devices()  # 通过模块访问实例
        device = next((d for d in devices if d["id"] == device_id), None)
        if not device:
            print(f"Device {device_id} not found")
            return False

        try:
            response = requests.post(
                f"http://{device['ip']}:5000/",
                json=payload,
                headers=self.headers,
                timeout=3
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Device {device_id} communication failed: {str(e)}")
            return False

    def show_emoji(self, emoji: str, device_id=0, **kwargs):
        payload = {"emoji": emoji.split('.')[0]}
        return self._send_to_pi(payload, device_id)

    def show_text(self, text: str, device_id=0, **kwargs):
        payload = {"text": text}
        return self._send_to_pi(payload, device_id)


