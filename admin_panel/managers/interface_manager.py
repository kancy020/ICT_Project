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
    Manages data flow control in different modes
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
        
        # Load configuration
        self._load_config()
        print(f"[InterfaceManager] Initialized, current mode: {self.mode.value}")
    
    def _load_config(self):
        """Load configuration file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    mode_str = config.get('mode', 'local')
                    self.mode = InterfaceMode(mode_str)
            else:
                self._save_config()
        except Exception as e:
            print(f"[InterfaceManager] Failed to load config: {e}")
            self.mode = InterfaceMode.LOCAL
    
    def _save_config(self):
        """Save configuration file"""
        try:
            config = {
                'mode': self.mode.value,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[InterfaceManager] Failed to save config: {e}")
    
    def set_admin_manager(self, admin_manager):
        """Set reference to admin manager class"""
        self.admin_manager = admin_manager
        print(f"[InterfaceManager] Admin manager bound")
    
    def switch_mode(self, mode: InterfaceMode):
        """Switch interface mode"""
        with self.lock:
            old_mode = self.mode
            self.mode = mode
            self._save_config()
            print(f"[InterfaceManager] Mode switched: {old_mode.value} -> {mode.value}")
            
            # If switching from blocked mode to local mode, resume execution
            if old_mode != InterfaceMode.LOCAL and mode == InterfaceMode.LOCAL:
                self.blocked_execution = False
    
    def intercept_execution(self, func: Callable, *args, **kwargs):
        """
        Intercept function execution
        Decides whether to block execution based on current mode
        """
        with self.lock:
            # Get caller information
            caller_frame = inspect.currentframe().f_back
            caller_info = {
                'function_name': func.__name__ if hasattr(func, '__name__') else str(func),
                'args': args,
                'kwargs': kwargs,
                'timestamp': datetime.now().isoformat(),
                'caller_file': caller_frame.f_code.co_filename,
                'caller_line': caller_frame.f_lineno
            }
            
            print(f"[InterfaceManager] Intercepted execution: {caller_info['function_name']}")
            
            if self.mode == InterfaceMode.LOCAL:
                # Local mode - don't interfere, execute directly
                return self._execute_local(func, *args, **kwargs)
            
            elif self.mode == InterfaceMode.NETWORK:
                # Network mode - block execution, transfer to admin manager, wait for return
                return self._execute_network(func, caller_info, *args, **kwargs)
            
            elif self.mode == InterfaceMode.REMOTE:
                # Remote dispatch mode - block execution, transfer to other program, no return
                return self._execute_remote(func, caller_info, *args, **kwargs)
    
    def _execute_local(self, func: Callable, *args, **kwargs):
        """Local mode execution"""
        try:
            result = func(*args, **kwargs)
            print(f"[InterfaceManager] Local execution completed: {func.__name__}")
            return result
        except Exception as e:
            print(f"[InterfaceManager] Local execution failed: {e}")
            return None
    
    def _execute_network(self, func: Callable, caller_info: Dict, *args, **kwargs):
        """Network mode execution"""
        try:
            # Block original execution
            self.blocked_execution = True
            
            # Capture internal variables and commands
            execution_data = {
                'caller_info': caller_info,
                'captured_variables': self._capture_variables(),
                'execution_id': f"exec_{int(time.time())}"
            }
            
            #print(f"[InterfaceManager] Network mode - Data captured, waiting for admin processing")
            
            # Transfer to admin manager for processing
            if self.admin_manager:
                result = self.admin_manager.handle_network_execution(execution_data)
                
                # Wait for admin manager to finish processing
                while self.blocked_execution:
                    time.sleep(0.1)
                
                #print(f"[InterfaceManager] Network mode - Admin processing completed, returning to original execution path")
                return result
            else:
                print(f"[InterfaceManager] Error: Admin manager not bound")
                self.blocked_execution = False
                return None
                
        except Exception as e:
            print(f"[InterfaceManager] Network mode execution failed: {e}")
            self.blocked_execution = False
            return None
    
    def _execute_remote(self, func: Callable, caller_info: Dict, *args, **kwargs):
        """Remote dispatch mode execution"""
        try:
            # Block original execution, no return
            self.blocked_execution = True
            
            # Capture internal variables and commands
            execution_data = {
                'caller_info': caller_info,
                'captured_variables': self._capture_variables(),
                'execution_id': f"remote_{int(time.time())}"
            }
            
            #print(f"[InterfaceManager] Remote mode - Data captured, transferring to other program")
            
            # Transfer to admin manager for processing (no waiting for return)
            if self.admin_manager:
                self.admin_manager.handle_remote_execution(execution_data)
                
            #print(f"[InterfaceManager] Remote mode - Transferred")
            
            # Remote mode doesn't return to original execution path
            return "REMOTE_EXECUTION_TRANSFERRED"
            
        except Exception as e:
            print(f"[InterfaceManager] Remote mode execution failed: {e}")
            return None
    
    def _capture_variables(self):
        """Capture internal variables"""
        try:
            # Get variables from call stack
            frame = inspect.currentframe()
            variables = {}
            
            # Traverse call stack
            while frame:
                if frame.f_locals and frame.f_code.co_filename != __file__:
                    # Filter out sensitive variables and built-ins
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
            print(f"[InterfaceManager] Variable capture failed: {e}")
            return {}
    
    def resume_execution(self):
        """Resume blocked execution"""
        with self.lock:
            self.blocked_execution = False
            print(f"[InterfaceManager] Execution resumed")
    
    def get_current_mode(self):
        """Get current mode"""
        return self.mode
    
    def get_status(self):
        """Get interface status"""
        return {
            'mode': self.mode.value,
            'blocked': self.blocked_execution,
            'admin_connected': self.admin_manager is not None,
            'timestamp': datetime.now().isoformat()
        }

# Global interface manager instance
interface_manager = InterfaceManager()

def intercept(func):
    """
    Decorator - Automatically intercepts function execution
    """
    def wrapper(*args, **kwargs):
        return interface_manager.intercept_execution(func, *args, **kwargs)
    return wrapper
