import json
import os

def create_config_files():

    os.makedirs('configs', exist_ok=True)
    
    # 设备配置
    devices_config = [
        {
            "id": 0,
            "name": "RaspberryPixel",
            "status": "Idle",
            "disabled": False,
            "type": "pixel_screen",
            "ip": ""
        },
        {
            "id": 1,
            "name": "RaspberryPixel2",
            "status": "Idle",
            "disabled": False,
            "type": "pixel_screen", 
            "ip": ""
        }
    ]
    
    # 用户配置
    users_config = [
        {
            "id": 1,
            "name": "Tao",
            "permission": "Active",
            "role": "admin"
        },
        {
            "id": 2,
            "name": "Chris",
            "permission": "Active", 
            "role": "user"
        },
        {
            "id": 3,
            "name": "Steven",
            "permission": "Inactive",
            "role": "user"
        }
    ]
    
    with open('configs/devices.json', 'w', encoding='utf-8') as f:
        json.dump(devices_config, f, indent=2, ensure_ascii=False)
    
    with open('users_config.json', 'w', encoding='utf-8') as f:
        json.dump(users_config, f, indent=2, ensure_ascii=False)
    
    print("Configuration files created successfully:")
    print("  - configs/devices.json")
    print("  - users_config.json")

if __name__ == "__main__":
    create_config_files()