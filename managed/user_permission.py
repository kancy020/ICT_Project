import threading
from abc import ABC, abstractmethod
import json
import os
import time

class IUserPermissionManager(ABC):
    @abstractmethod
    def get_users(self):
        pass
    
    @abstractmethod
    def toggle_permission(self, user_id):
        pass
    
    @abstractmethod
    def fetch_permissions(self):
        pass

class UserPermissionManager(IUserPermissionManager):
    def __init__(self, config_file="users_config.json"):
        self.lock = threading.Lock()
        self.config_file = config_file
        self._load_users()  # 新增动态加载

    def _load_users(self):
        """从配置文件加载用户（新增方法）"""
        default_users = [
            {"id": 1, "name": "Admin", "permission": "Active", "role": "admin"},
            {"id": 2, "name": "Operator", "permission": "Active", "role": "operator"}
        ]
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file) as f:
                    self.users = json.load(f)
            else:
                self.users = default_users
        except Exception:
            self.users = default_users

    def save_users(self):
        """保存用户配置（新增方法）"""
        with self.lock:
            with open(self.config_file, 'w') as f:
                json.dump(self.users, f, indent=2)

    # 修改原有方法支持动态保存
    def get_users(self):
        with self.lock:
            return [u.copy() for u in self.users]

    def toggle_permission(self, user_id):
        with self.lock:
            for user in self.users:
                if user["id"] == user_id:
                    user["permission"] = "Active" if user["permission"] == "Inactive" else "Inactive"
                    self.save_users()  # 状态变更后保存
                    return True
        return False

    def fetch_permissions(self):
        print("Fetching permissions...")
        time.sleep(1)
        self._load_users()  # 改为重新加载配置
        return True

