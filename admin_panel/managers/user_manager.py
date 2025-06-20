import json
import os
import threading
from datetime import datetime
from typing import Dict, List, Set, Optional

class UserManager:
    """
    User management class - Manages user list, permissions and status
    """
    
    def __init__(self, storage_file: str = None):
        import os
        data_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'data'))
        self.storage_file = storage_file or os.path.join(data_dir, "users.json")
        self.users = {}  # User info dictionary
        self.blocked_users = set()  # Set of blocked users
        self.active_users = set()  # Set of active users
        
        # Thread lock
        self.lock = threading.Lock()
        
        # Load user data
        self._load_users()
        
        print(f"[UserManager] User manager initialized, loaded {len(self.users)} users")

    def _load_users(self):
        """Load user data from file"""
        try:
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    self.users = data.get('users', {})
                    self.blocked_users = set(data.get('blocked_users', []))
                    self.active_users = set(data.get('active_users', []))
                    
                print(f"[UserManager] User data loaded")
        except Exception as e:
            print(f"[UserManager] Failed to load user data: {e}")
            # Initialize empty data
            self.users = {}
            self.blocked_users = set()
            self.active_users = set()

    def _save_users(self):
        """Save user data to file"""
        try:
            data = {
                'users': self.users,
                'blocked_users': list(self.blocked_users),
                'active_users': list(self.active_users),
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"[UserManager] Failed to save user data: {e}")

    def add_user_from_command(self, username: str, command_info: Dict = None):
        """
        Automatically add user from command
        Called automatically when user executes command
        """
        if not username:
            return False
            
        try:
            with self.lock:
                current_time = datetime.now().isoformat()
                
                if username not in self.users:
                    # New user
                    self.users[username] = {
                        'username': username,
                        'first_seen': current_time,
                        'last_active': current_time,
                        'command_count': 1,
                        'is_blocked': username in self.blocked_users,
                        'permissions': ['basic'],  # Default permissions
                        'commands_history': []
                    }
                    print(f"[UserManager] New user automatically added: {username}")
                else:
                    # Update existing user info
                    self.users[username]['last_active'] = current_time
                    self.users[username]['command_count'] += 1
                
                # Record command history (keep last 50)
                if command_info:
                    command_record = {
                        'timestamp': current_time,
                        'command': command_info
                    }
                    self.users[username].setdefault('commands_history', [])
                    self.users[username]['commands_history'].append(command_record)
                    
                    # Keep only last 50 records
                    if len(self.users[username]['commands_history']) > 50:
                        self.users[username]['commands_history'] = \
                            self.users[username]['commands_history'][-50:]
                
                # Add to active users set
                self.active_users.add(username)
                
                # Save data
                self._save_users()
                
                return True
                
        except Exception as e:
            print(f"[UserManager] Failed to add user: {e}")
            return False

    def add_user_manual(self, username: str, permissions: List[str] = None):
        """
        Manually add user
        """
        if not username:
            return False
            
        try:
            with self.lock:
                current_time = datetime.now().isoformat()
                
                if permissions is None:
                    permissions = ['basic']
                
                self.users[username] = {
                    'username': username,
                    'first_seen': current_time,
                    'last_active': current_time,
                    'command_count': 0,
                    'is_blocked': False,
                    'permissions': permissions,
                    'commands_history': [],
                    'manually_added': True
                }
                
                # Remove from blocked list (if exists)
                if username in self.blocked_users:
                    self.blocked_users.remove(username)
                
                # Add to active users set
                self.active_users.add(username)
                
                # Save data
                self._save_users()
                
                print(f"[UserManager] User added manually: {username}")
                return True
                
        except Exception as e:
            print(f"[UserManager] Failed to add user manually: {e}")
            return False

    def remove_user(self, username: str):
        """Remove user"""
        try:
            with self.lock:
                removed = False
                
                if username in self.users:
                    del self.users[username]
                    removed = True
                
                if username in self.blocked_users:
                    self.blocked_users.remove(username)
                    removed = True
                
                if username in self.active_users:
                    self.active_users.remove(username)
                    removed = True
                
                if removed:
                    self._save_users()
                    print(f"[UserManager] User removed: {username}")
                    return True
                else:
                    print(f"[UserManager] User doesn't exist: {username}")
                    return False
                    
        except Exception as e:
            print(f"[UserManager] Failed to remove user: {e}")
            return False

    def block_user(self, username: str):
        """Block user"""
        try:
            with self.lock:
                self.blocked_users.add(username)
                
                # Update user info status
                if username in self.users:
                    self.users[username]['is_blocked'] = True
                    self.users[username]['blocked_at'] = datetime.now().isoformat()
                
                # Remove from active users
                if username in self.active_users:
                    self.active_users.remove(username)
                
                self._save_users()
                
                print(f"[UserManager] User blocked: {username}")
                return True
                
        except Exception as e:
            print(f"[UserManager] Failed to block user: {e}")
            return False

    def unblock_user(self, username: str):
        """Unblock user"""
        try:
            with self.lock:
                if username in self.blocked_users:
                    self.blocked_users.remove(username)
                    
                    # Update user info status
                    if username in self.users:
                        self.users[username]['is_blocked'] = False
                        self.users[username]['unblocked_at'] = datetime.now().isoformat()
                    
                    # Add to active users
                    self.active_users.add(username)
                    
                    self._save_users()
                    
                    print(f"[UserManager] User unblocked: {username}")
                    return True
                else:
                    print(f"[UserManager] User not blocked: {username}")
                    return False
                    
        except Exception as e:
            print(f"[UserManager] Failed to unblock user: {e}")
            return False

    def is_user_blocked(self, username: str) -> bool:
        """Check if user is blocked"""
        return username in self.blocked_users

    def get_user_info(self, username: str) -> Optional[Dict]:
        """Get user info"""
        return self.users.get(username)

    def get_all_users(self) -> Dict:
        """Get all user info"""
        return {
            'users': self.users,
            'blocked_users': list(self.blocked_users),
            'active_users': list(self.active_users),
            'total_count': len(self.users),
            'blocked_count': len(self.blocked_users),
            'active_count': len(self.active_users)
        }

    def get_blocked_users(self) -> Set[str]:
        """Get list of blocked users"""
        return self.blocked_users.copy()

    def get_active_users(self) -> Set[str]:
        """Get list of active users"""
        return self.active_users.copy()

    def update_user_permissions(self, username: str, permissions: List[str]) -> bool:
        """Update user permissions"""
        try:
            with self.lock:
                if username in self.users:
                    self.users[username]['permissions'] = permissions
                    self.users[username]['permissions_updated'] = datetime.now().isoformat()
                    self._save_users()
                    
                    print(f"[UserManager] User permissions updated: {username} -> {permissions}")
                    return True
                else:
                    print(f"[UserManager] User doesn't exist, can't update permissions: {username}")
                    return False
                    
        except Exception as e:
            print(f"[UserManager] Failed to update user permissions: {e}")
            return False

    def check_user_permission(self, username: str, required_permission: str) -> bool:
        """Check if user has specific permission"""
        if username in self.users:
            user_permissions = self.users[username].get('permissions', [])
            return required_permission in user_permissions or 'admin' in user_permissions
        return False

    def get_status(self):
        """Get user manager status"""
        return {
            'total_users': len(self.users),
            'blocked_users': len(self.blocked_users),
            'active_users': len(self.active_users),
            'storage_file': self.storage_file,
            'timestamp': datetime.now().isoformat()
        }