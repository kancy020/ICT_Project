import json
import os
import threading
import time
import inspect
from enum import Enum
from typing import Dict, Any, Optional, Callable
from datetime import datetime

class InterfaceMode(Enum):
    LOCAL = "local"
    NETWORK = "network"
    REMOTE = "remote"

class InterfaceManager:
    """
    接口类 - 负责管理不同模式下的数据流控制
    """
    
    def __init__(self, config_file: str = None):
        import os
        data_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'data'))
        self.config_file = config_file or os.path.join(data_dir, 'interface_config.json')
        self.mode = InterfaceMode.LOCAL
        self.admin_manager = None
        self.original_execution_callback = None
        self.blocked_execution = False
        self.captured_data = {}
        self.lock = threading.Lock()
        self.execution_queue = []
        
        # 加载配置
        self._load_config()
        print(f"[InterfaceManager] 初始化完成，当前模式: {self.mode.value}")
    
    def _load_config(self):
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    mode_str = config.get('mode', 'local')
                    self.mode = InterfaceMode(mode_str)
            else:
                self._save_config()
        except Exception as e:
            print(f"[InterfaceManager] 加载配置失败: {e}")
            self.mode = InterfaceMode.LOCAL
    
    def _save_config(self):
        """保存配置文件"""
        try:
            config = {
                'mode': self.mode.value,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[InterfaceManager] 保存配置失败: {e}")
    
    def set_admin_manager(self, admin_manager):
        """设置管理员类引用"""
        self.admin_manager = admin_manager
        print(f"[InterfaceManager] 管理员类已绑定")
    
    def switch_mode(self, mode: InterfaceMode):
        """切换接口模式"""
        with self.lock:
            old_mode = self.mode
            self.mode = mode
            self._save_config()
            print(f"[InterfaceManager] 模式切换: {old_mode.value} -> {mode.value}")
            
            # 如果从阻断模式切换到本地模式，恢复执行
            if old_mode != InterfaceMode.LOCAL and mode == InterfaceMode.LOCAL:
                self.blocked_execution = False
    
    def intercept_execution(self, func: Callable, *args, **kwargs):
        """
        拦截函数执行
        根据当前模式决定是否阻断执行
        """
        with self.lock:
            # 获取调用信息
            caller_frame = inspect.currentframe().f_back
            caller_info = {
                'function_name': func.__name__ if hasattr(func, '__name__') else str(func),
                'args': args,
                'kwargs': kwargs,
                'timestamp': datetime.now().isoformat(),
                'caller_file': caller_frame.f_code.co_filename,
                'caller_line': caller_frame.f_lineno
            }
            
            print(f"[InterfaceManager] 拦截执行: {caller_info['function_name']}")
            
            if self.mode == InterfaceMode.LOCAL:
                # 本地模式 - 不干涉数据，直接执行
                return self._execute_local(func, *args, **kwargs)
            
            elif self.mode == InterfaceMode.NETWORK:
                # 联网模式 - 阻断执行，传输给管理员处理，等待返回
                return self._execute_network(func, caller_info, *args, **kwargs)
            
            elif self.mode == InterfaceMode.REMOTE:
                # 远程调度模式 - 阻断执行，传输给其他程序，不返回
                return self._execute_remote(func, caller_info, *args, **kwargs)
    
    def _execute_local(self, func: Callable, *args, **kwargs):
        """本地模式执行"""
        try:
            result = func(*args, **kwargs)
            print(f"[InterfaceManager] 本地执行完成: {func.__name__}")
            return result
        except Exception as e:
            print(f"[InterfaceManager] 本地执行失败: {e}")
            return None
    
    def _execute_network(self, func: Callable, caller_info: Dict, *args, **kwargs):
        """联网模式执行"""
        try:
            # 阻断原本执行
            self.blocked_execution = True
            
            # 爬取内部变量和命令
            execution_data = {
                'caller_info': caller_info,
                'captured_variables': self._capture_variables(),
                'execution_id': f"exec_{int(time.time())}"
            }
            
            print(f"[InterfaceManager] 联网模式 - 数据已爬取，等待管理员处理")
            
            # 传输给管理员类处理
            if self.admin_manager:
                result = self.admin_manager.handle_network_execution(execution_data)
                
                # 等待管理员处理完成
                while self.blocked_execution:
                    time.sleep(0.1)
                
                print(f"[InterfaceManager] 联网模式 - 管理员处理完成，返回原执行路径")
                return result
            else:
                print(f"[InterfaceManager] 错误: 管理员类未绑定")
                self.blocked_execution = False
                return None
                
        except Exception as e:
            print(f"[InterfaceManager] 联网模式执行失败: {e}")
            self.blocked_execution = False
            return None
    
    def _execute_remote(self, func: Callable, caller_info: Dict, *args, **kwargs):
        """远程调度模式执行"""
        try:
            # 阻断原本执行，不返回
            self.blocked_execution = True
            
            # 爬取内部变量和命令
            execution_data = {
                'caller_info': caller_info,
                'captured_variables': self._capture_variables(),
                'execution_id': f"remote_{int(time.time())}"
            }
            
            print(f"[InterfaceManager] 远程模式 - 数据已爬取，传输给其他程序")
            
            # 传输给管理员类处理（不等待返回）
            if self.admin_manager:
                self.admin_manager.handle_remote_execution(execution_data)
                
            print(f"[InterfaceManager] 远程模式 - 已传输，不返回原执行路径")
            
            # 远程模式不返回到原执行路径
            return "REMOTE_EXECUTION_TRANSFERRED"
            
        except Exception as e:
            print(f"[InterfaceManager] 远程模式执行失败: {e}")
            return None
    
    def _capture_variables(self):
        """爬取内部变量"""
        try:
            # 获取调用栈中的变量
            frame = inspect.currentframe()
            variables = {}
            
            # 遍历调用栈
            while frame:
                if frame.f_locals and frame.f_code.co_filename != __file__:
                    # 过滤掉敏感变量和内置变量
                    filtered_vars = {
                        k: str(v) for k, v in frame.f_locals.items() 
                        if not k.startswith('_') and not callable(v)
                        and k not in ['self', 'cls', 'request', 'response']
                    }
                    if filtered_vars:
                        variables[frame.f_code.co_name] = filtered_vars
                frame = frame.f_back
            
            return variables
        except Exception as e:
            print(f"[InterfaceManager] 变量爬取失败: {e}")
            return {}
    
    def resume_execution(self):
        """恢复被阻断的执行"""
        with self.lock:
            self.blocked_execution = False
            print(f"[InterfaceManager] 执行已恢复")
    
    def get_current_mode(self):
        """获取当前模式"""
        return self.mode
    
    def get_status(self):
        """获取接口状态"""
        return {
            'mode': self.mode.value,
            'blocked': self.blocked_execution,
            'admin_connected': self.admin_manager is not None,
            'timestamp': datetime.now().isoformat()
        }

# 全局接口管理器实例
interface_manager = InterfaceManager()

def intercept(func):
    """
    装饰器 - 用于自动拦截函数执行
    """
    def wrapper(*args, **kwargs):
        return interface_manager.intercept_execution(func, *args, **kwargs)
    return wrapper
