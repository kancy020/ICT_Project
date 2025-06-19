import json
import os
import threading
from datetime import datetime
from typing import Dict, List, Set, Optional

class UserManager:
    """
    用户管理类 - 管理用户列表、权限和状态
    """
    
    def __init__(self, storage_file: str = None):
        import os
        data_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'data'))
        self.storage_file = storage_file or os.path.join(data_dir, "users.json")
        self.users = {}  # 用户信息字典
        self.blocked_users = set()  # 被禁用的用户集合
        self.active_users = set()  # 活跃用户集合
        
        # 线程锁
        self.lock = threading.Lock()
        
        # 加载用户数据
        self._load_users()
        
        print(f"[UserManager] 用户管理器初始化完成，已加载 {len(self.users)} 个用户")
    
    def _load_users(self):
        """从文件加载用户数据"""
        try:
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    self.users = data.get('users', {})
                    self.blocked_users = set(data.get('blocked_users', []))
                    self.active_users = set(data.get('active_users', []))
                    
                print(f"[UserManager] 用户数据加载完成")
        except Exception as e:
            print(f"[UserManager] 加载用户数据失败: {e}")
            # 初始化空数据
            self.users = {}
            self.blocked_users = set()
            self.active_users = set()
    
    def _save_users(self):
        """保存用户数据到文件"""
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
            print(f"[UserManager] 保存用户数据失败: {e}")
    
    def add_user_from_command(self, username: str, command_info: Dict = None):
        """
        从命令中自动添加用户
        当用户执行命令时自动调用此方法
        """
        if not username:
            return False
            
        try:
            with self.lock:
                current_time = datetime.now().isoformat()
                
                if username not in self.users:
                    # 新用户
                    self.users[username] = {
                        'username': username,
                        'first_seen': current_time,
                        'last_active': current_time,
                        'command_count': 1,
                        'is_blocked': username in self.blocked_users,
                        'permissions': ['basic'],  # 默认权限
                        'commands_history': []
                    }
                    print(f"[UserManager] 新用户已自动添加: {username}")
                else:
                    # 更新现有用户信息
                    self.users[username]['last_active'] = current_time
                    self.users[username]['command_count'] += 1
                
                # 记录命令历史（保留最近50条）
                if command_info:
                    command_record = {
                        'timestamp': current_time,
                        'command': command_info
                    }
                    self.users[username].setdefault('commands_history', [])
                    self.users[username]['commands_history'].append(command_record)
                    
                    # 只保留最近50条记录
                    if len(self.users[username]['commands_history']) > 50:
                        self.users[username]['commands_history'] = \
                            self.users[username]['commands_history'][-50:]
                
                # 添加到活跃用户集合
                self.active_users.add(username)
                
                # 保存数据
                self._save_users()
                
                return True
                
        except Exception as e:
            print(f"[UserManager] 添加用户失败: {e}")
            return False
    
    def add_user_manual(self, username: str, permissions: List[str] = None):
        """
        手动添加用户
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
                
                # 从阻止列表中移除（如果存在）
                if username in self.blocked_users:
                    self.blocked_users.remove(username)
                
                # 添加到活跃用户集合
                self.active_users.add(username)
                
                # 保存数据
                self._save_users()
                
                print(f"[UserManager] 手动添加用户成功: {username}")
                return True
                
        except Exception as e:
            print(f"[UserManager] 手动添加用户失败: {e}")
            return False
    
    def remove_user(self, username: str):
        """删除用户"""
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
                    print(f"[UserManager] 用户已删除: {username}")
                    return True
                else:
                    print(f"[UserManager] 用户不存在: {username}")
                    return False
                    
        except Exception as e:
            print(f"[UserManager] 删除用户失败: {e}")
            return False
    
    def block_user(self, username: str):
        """禁用用户"""
        try:
            with self.lock:
                self.blocked_users.add(username)
                
                # 更新用户信息中的状态
                if username in self.users:
                    self.users[username]['is_blocked'] = True
                    self.users[username]['blocked_at'] = datetime.now().isoformat()
                
                # 从活跃用户中移除
                if username in self.active_users:
                    self.active_users.remove(username)
                
                self._save_users()
                
                print(f"[UserManager] 用户已禁用: {username}")
                return True
                
        except Exception as e:
            print(f"[UserManager] 禁用用户失败: {e}")
            return False
    
    def unblock_user(self, username: str):
        """解除用户禁用"""
        try:
            with self.lock:
                if username in self.blocked_users:
                    self.blocked_users.remove(username)
                    
                    # 更新用户信息中的状态
                    if username in self.users:
                        self.users[username]['is_blocked'] = False
                        self.users[username]['unblocked_at'] = datetime.now().isoformat()
                    
                    # 添加到活跃用户中
                    self.active_users.add(username)
                    
                    self._save_users()
                    
                    print(f"[UserManager] 用户禁用已解除: {username}")
                    return True
                else:
                    print(f"[UserManager] 用户未被禁用: {username}")
                    return False
                    
        except Exception as e:
            print(f"[UserManager] 解除用户禁用失败: {e}")
            return False
    
    def is_user_blocked(self, username: str) -> bool:
        """检查用户是否被禁用"""
        return username in self.blocked_users
    
    def get_user_info(self, username: str) -> Optional[Dict]:
        """获取用户信息"""
        return self.users.get(username)
    
    def get_all_users(self) -> Dict:
        """获取所有用户信息"""
        return {
            'users': self.users,
            'blocked_users': list(self.blocked_users),
            'active_users': list(self.active_users),
            'total_count': len(self.users),
            'blocked_count': len(self.blocked_users),
            'active_count': len(self.active_users)
        }
    
    def get_blocked_users(self) -> Set[str]:
        """获取被禁用的用户列表"""
        return self.blocked_users.copy()
    
    def get_active_users(self) -> Set[str]:
        """获取活跃用户列表"""
        return self.active_users.copy()
    
    def update_user_permissions(self, username: str, permissions: List[str]) -> bool:
        """更新用户权限"""
        try:
            with self.lock:
                if username in self.users:
                    self.users[username]['permissions'] = permissions
                    self.users[username]['permissions_updated'] = datetime.now().isoformat()
                    self._save_users()
                    
                    print(f"[UserManager] 用户权限已更新: {username} -> {permissions}")
                    return True
                else:
                    print(f"[UserManager] 用户不存在，无法更新权限: {username}")
                    return False
                    
        except Exception as e:
            print(f"[UserManager] 更新用户权限失败: {e}")
            return False
    
    def check_user_permission(self, username: str, required_permission: str) -> bool:
        """检查用户是否拥有特定权限"""
        if username in self.users:
            user_permissions = self.users[username].get('permissions', [])
            return required_permission in user_permissions or 'admin' in user_permissions
        return False
    
    def get_user_statistics(self) -> Dict:
        """获取用户统计信息"""
        try:
            total_commands = sum(user.get('command_count', 0) for user in self.users.values())
            
            # 最活跃用户
            most_active_user = None
            max_commands = 0
            for username, user_info in self.users.items():
                if user_info.get('command_count', 0) > max_commands:
                    max_commands = user_info.get('command_count', 0)
                    most_active_user = username
            
            return {
                'total_users': len(self.users),
                'blocked_users': len(self.blocked_users),
                'active_users': len(self.active_users),
                'total_commands': total_commands,
                'most_active_user': most_active_user,
                'max_commands': max_commands
            }
            
        except Exception as e:
            print(f"[UserManager] 获取用户统计失败: {e}")
            return {}
    
    def cleanup_inactive_users(self, days: int = 30):
        """清理非活跃用户（超过指定天数未活动）"""
        try:
            from datetime import timedelta
            
            with self.lock:
                current_time = datetime.now()
                cutoff_time = current_time - timedelta(days=days)
                
                inactive_users = []
                for username, user_info in self.users.items():
                    try:
                        last_active = datetime.fromisoformat(user_info.get('last_active', ''))
                        if last_active < cutoff_time and not user_info.get('manually_added', False):
                            inactive_users.append(username)
                    except:
                        # 如果时间格式有问题，跳过
                        continue
                
                # 删除非活跃用户
                for username in inactive_users:
                    del self.users[username]
                    if username in self.active_users:
                        self.active_users.remove(username)
                    if username in self.blocked_users:
                        self.blocked_users.remove(username)
                
                if inactive_users:
                    self._save_users()
                    print(f"[UserManager] 已清理 {len(inactive_users)} 个非活跃用户")
                
                return len(inactive_users)
                
        except Exception as e:
            print(f"[UserManager] 清理非活跃用户失败: {e}")
            return 0
    
    def get_status(self):
        """获取用户管理器状态"""
        return {
            'total_users': len(self.users),
            'blocked_users': len(self.blocked_users),
            'active_users': len(self.active_users),
            'storage_file': self.storage_file,
            'timestamp': datetime.now().isoformat()
        }