import time
import threading
from abc import ABC, abstractmethod

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
    def __init__(self):
        self.users = [
            {"id": 1, "name": "User A", "permission": "Active"},
            {"id": 2, "name": "User B", "permission": "Active"},
            {"id": 3, "name": "User C", "permission": "Inactive"}
        ]
        self.lock = threading.Lock()

    def get_users(self):
        with self.lock:
            return [u.copy() for u in self.users]

    def toggle_permission(self, user_id):
        with self.lock:
            for user in self.users:
                if user["id"] == user_id:
                    user["permission"] = "Active" if user["permission"] == "Inactive" else "Inactive"
                    return True
        return False

    def fetch_permissions(self):
        print("Fetching permissions...")
        time.sleep(1)
        new_users = [
            {"id": 1, "name": "User A", "permission": "Active"},
            {"id": 2, "name": "User B", "permission": "Inactive"},
            {"id": 3, "name": "User C", "permission": "Inactive"}
        ]
        with self.lock:
            self.users = new_users
        return True
