import json
import os
import threading
import time
from datetime import datetime
from typing import Dict, Any, Optional
from flask import Flask, render_template, request, jsonify, redirect, url_for
import webbrowser

class AdminManager:
    """
    Administrator class - Responsible for receiving interface data and dispatching to other classes
    """
    
    def __init__(self, port: int = 9999):
        self.port = port
        self.interface_manager = None
        self.task_queue = None
        self.user_manager = None
        self.device_manager = None
        
        # Web application
        self.app = Flask(__name__, template_folder='templates', static_folder='static')
        self.app.secret_key = 'admin_secret_key_2024'
        
        # Execution queue
        self.execution_queue = []
        self.execution_lock = threading.Lock()
        
        # Initialize routes
        self._setup_routes()
        
        print(f"[AdminManager] Administrator initialized, port: {port}")
    
    def set_components(self, interface_manager, task_queue, user_manager, device_manager):
        """Set component references"""
        self.interface_manager = interface_manager
        self.task_queue = task_queue
        self.user_manager = user_manager
        self.device_manager = device_manager
        
        # Reverse binding
        if interface_manager:
            interface_manager.set_admin_manager(self)
        
        print(f"[AdminManager] Components bound successfully")
    
    def handle_network_execution(self, execution_data: Dict[str, Any]):
        """Handle execution requests in network mode"""
        try:
            print(f"[AdminManager] Handling network execution: {execution_data['execution_id']}")
            
            # Add to execution queue
            with self.execution_lock:
                self.execution_queue.append({
                    'id': execution_data['execution_id'],
                    'type': 'network',
                    'data': execution_data,
                    'status': 'pending',
                    'timestamp': datetime.now().isoformat()
                })
            
            # Actual processing logic can be added here
            # For example: add to task queue, check user permissions, device status, etc.
            
            result = self._process_execution_data(execution_data)
            
            # Resume execution after processing
            if self.interface_manager:
                self.interface_manager.resume_execution()
            
            return result
            
        except Exception as e:
            print(f"[AdminManager] Failed to handle network execution: {e}")
            if self.interface_manager:
                self.interface_manager.resume_execution()
            return None
    
    def handle_remote_execution(self, execution_data: Dict[str, Any]):
        """Handle execution requests in remote dispatch mode"""
        try:
            print(f"[AdminManager] Handling remote execution: {execution_data['execution_id']}")
            
            # Add to execution queue
            with self.execution_lock:
                self.execution_queue.append({
                    'id': execution_data['execution_id'],
                    'type': 'remote',
                    'data': execution_data,
                    'status': 'transferred',
                    'timestamp': datetime.now().isoformat()
                })
            
            # Remote mode processing logic
            self._process_remote_execution(execution_data)
            
            # Remote mode doesn't return to original execution path
            print(f"[AdminManager] Remote execution transferred")
            
        except Exception as e:
            print(f"[AdminManager] Failed to handle remote execution: {e}")
    
    def _process_execution_data(self, execution_data: Dict[str, Any]):
        """Process execution data"""
        try:
            caller_info = execution_data.get('caller_info', {})
            func_name = caller_info.get('function_name', 'unknown')
            
            # Determine processing method based on function name
            if func_name in ['show_emoji', 'send_image_to_display']:
                # Handle display-related commands
                return self._handle_display_command(execution_data)
            elif func_name in ['set_timer']:
                # Handle timer commands
                return self._handle_timer_command(execution_data)
            else:
                # Generic handling
                return self._handle_generic_command(execution_data)
                
        except Exception as e:
            print(f"[AdminManager] Failed to process execution data: {e}")
            return None
    
    def _handle_display_command(self, execution_data: Dict[str, Any]):
        """Handle display commands"""
        try:
            if self.task_queue:
                # Add to task queue
                task_data = {
                    'type': 'display',
                    'data': execution_data,
                    'priority': 'normal'
                }
                self.task_queue.add_task(task_data)
                return {'status': 'added_to_queue', 'task_id': task_data.get('id')}
            
            return {'status': 'processed', 'message': 'Display command handled'}
            
        except Exception as e:
            print(f"[AdminManager] Failed to handle display command: {e}")
            return None
    
    def _handle_timer_command(self, execution_data: Dict[str, Any]):
        """Handle timer commands"""
        try:
            if self.task_queue:
                task_data = {
                    'type': 'timer',
                    'data': execution_data,
                    'priority': 'high'
                }
                self.task_queue.add_task(task_data)
                return {'status': 'timer_set', 'task_id': task_data.get('id')}
            
            return {'status': 'processed', 'message': 'Timer command handled'}
            
        except Exception as e:
            print(f"[AdminManager] Failed to handle timer command: {e}")
            return None
    
    def _handle_generic_command(self, execution_data: Dict[str, Any]):
        """Handle generic commands"""
        try:
            return {'status': 'processed', 'message': 'Generic command handled'}
            
        except Exception as e:
            print(f"[AdminManager] Failed to handle generic command: {e}")
            return None
    
    def _process_remote_execution(self, execution_data: Dict[str, Any]):
        """Handle remote execution (transfer to other program)"""
        try:
            # Logic to transfer to other program-Not implemented, switched to localized implementation
            
            remote_file = "remote_execution_queue.json"
            try:
                if os.path.exists(remote_file):
                    with open(remote_file, 'r', encoding='utf-8') as f:
                        remote_queue = json.load(f)
                else:
                    remote_queue = []
                
                remote_queue.append({
                    'execution_data': execution_data,
                    'timestamp': datetime.now().isoformat()
                })
                
                with open(remote_file, 'w', encoding='utf-8') as f:
                    json.dump(remote_queue, f, ensure_ascii=False, indent=2)
                
                print(f"[AdminManager] Remote execution data saved to: {remote_file}")
                
            except Exception as e:
                print(f"[AdminManager] Failed to save remote execution data: {e}")
                
        except Exception as e:
            print(f"[AdminManager] Failed to process remote execution: {e}")
    
    def switch_interface_mode(self, mode: str):
        """Switch interface mode"""
        try:
            if self.interface_manager:
                from interface_manager import InterfaceMode
                mode_enum = InterfaceMode(mode)
                self.interface_manager.switch_mode(mode_enum)
                return True
            return False
        except Exception as e:
            print(f"[AdminManager] Failed to switch interface mode: {e}")
            return False
    
    def get_system_status(self):
        """Get system status"""
        try:
            status = {
                'timestamp': datetime.now().isoformat(),
                'interface': self.interface_manager.get_status() if self.interface_manager else None,
                'task_queue': self.task_queue.get_status() if self.task_queue else None,
                'user_manager': self.user_manager.get_status() if self.user_manager else None,
                'device_manager': self.device_manager.get_status() if self.device_manager else None,
                'execution_queue_size': len(self.execution_queue)
            }
            return status
        except Exception as e:
            print(f"[AdminManager] Failed to get system status: {e}")
            return {}
    
    def _setup_routes(self):
        """Setup web routes"""
        
        @self.app.route('/')
        def index():
            return render_template('admin_index.html')
        
        @self.app.route('/api/status')
        def api_status():
            return jsonify(self.get_system_status())
        
        @self.app.route('/api/switch_mode', methods=['POST'])
        def api_switch_mode():
            try:
                data = request.get_json()
                mode = data.get('mode')
                success = self.switch_interface_mode(mode)
                return jsonify({'success': success})
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)})
        
        @self.app.route('/api/tasks')
        def api_tasks():
            try:
                if self.task_queue:
                    return jsonify(self.task_queue.get_all_tasks())
                return jsonify([])
            except Exception as e:
                return jsonify({'error': str(e)})
        
        @self.app.route('/api/users')
        def api_users():
            try:
                if self.user_manager:
                    return jsonify(self.user_manager.get_all_users())
                return jsonify([])
            except Exception as e:
                return jsonify({'error': str(e)})
        
        @self.app.route('/api/devices')
        def api_devices():
            try:
                if self.device_manager:
                    return jsonify(self.device_manager.get_all_devices())
                return jsonify([])
            except Exception as e:
                return jsonify({'error': str(e)})
    
    def start_web_server(self, debug: bool = False):
        """Start web management interface"""
        try:
            print(f"[AdminManager] Starting web server: http://localhost:{self.port}")
            
            # Start server in new thread
            def run_server():
                self.app.run(host='0.0.0.0', port=self.port, debug=debug, use_reloader=False)
            
            server_thread = threading.Thread(target=run_server, daemon=True)
            server_thread.start()
            
            # Wait for server to start
            time.sleep(2)
            
            # Automatically open browser
            try:
                webbrowser.open(f'http://localhost:{self.port}')
            except Exception as e:
                print(f"[AdminManager] Failed to open browser automatically: {e}")
            
            print(f"[AdminManager] Web server started")
            
        except Exception as e:
            print(f"[AdminManager] Failed to start web server: {e}")
    
    def stop_web_server(self):
        """Stop web server"""
        try:
            # Flask shutdown method
            print(f"[AdminManager] Web server stop request sent")
        except Exception as e:
            print(f"[AdminManager] Failed to stop web server: {e}")
    
    def get_execution_queue(self):
        """Get execution queue"""
        with self.execution_lock:
            return self.execution_queue.copy()
    
    def clear_execution_queue(self):
        """Clear execution queue"""
        with self.execution_lock:
            self.execution_queue.clear()
            print(f"[AdminManager] Execution queue cleared")
