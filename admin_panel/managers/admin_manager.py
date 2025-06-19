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
    管理员类 - 负责接收接口类数据并调度其他类
    """
    
    def __init__(self, port: int = 9999):
        self.port = port
        self.interface_manager = None
        self.task_queue = None
        self.user_manager = None
        self.device_manager = None
        
        # Web应用
        self.app = Flask(__name__, template_folder='templates', static_folder='static')
        self.app.secret_key = 'admin_secret_key_2024'
        
        # 执行队列
        self.execution_queue = []
        self.execution_lock = threading.Lock()
        
        # 初始化路由
        self._setup_routes()
        
        print(f"[AdminManager] 管理员类初始化完成，端口: {port}")
    
    def set_components(self, interface_manager, task_queue, user_manager, device_manager):
        """设置组件引用"""
        self.interface_manager = interface_manager
        self.task_queue = task_queue
        self.user_manager = user_manager
        self.device_manager = device_manager
        
        # 反向绑定
        if interface_manager:
            interface_manager.set_admin_manager(self)
        
        print(f"[AdminManager] 组件绑定完成")
    
    def handle_network_execution(self, execution_data: Dict[str, Any]):
        """处理联网模式的执行请求"""
        try:
            print(f"[AdminManager] 处理联网执行: {execution_data['execution_id']}")
            
            # 添加到执行队列
            with self.execution_lock:
                self.execution_queue.append({
                    'id': execution_data['execution_id'],
                    'type': 'network',
                    'data': execution_data,
                    'status': 'pending',
                    'timestamp': datetime.now().isoformat()
                })
            
            # 这里可以添加实际的处理逻辑
            # 例如：添加到任务队列、检查用户权限、设备状态等
            
            result = self._process_execution_data(execution_data)
            
            # 处理完成后恢复执行
            if self.interface_manager:
                self.interface_manager.resume_execution()
            
            return result
            
        except Exception as e:
            print(f"[AdminManager] 处理联网执行失败: {e}")
            if self.interface_manager:
                self.interface_manager.resume_execution()
            return None
    
    def handle_remote_execution(self, execution_data: Dict[str, Any]):
        """处理远程调度模式的执行请求"""
        try:
            print(f"[AdminManager] 处理远程执行: {execution_data['execution_id']}")
            
            # 添加到执行队列
            with self.execution_lock:
                self.execution_queue.append({
                    'id': execution_data['execution_id'],
                    'type': 'remote',
                    'data': execution_data,
                    'status': 'transferred',
                    'timestamp': datetime.now().isoformat()
                })
            
            # 远程模式处理逻辑
            self._process_remote_execution(execution_data)
            
            # 远程模式不恢复原执行路径
            print(f"[AdminManager] 远程执行已转移")
            
        except Exception as e:
            print(f"[AdminManager] 处理远程执行失败: {e}")
    
    def _process_execution_data(self, execution_data: Dict[str, Any]):
        """处理执行数据"""
        try:
            caller_info = execution_data.get('caller_info', {})
            func_name = caller_info.get('function_name', 'unknown')
            
            # 根据函数名称决定处理方式
            if func_name in ['show_emoji', 'send_image_to_display']:
                # 处理显示相关的命令
                return self._handle_display_command(execution_data)
            elif func_name in ['set_timer']:
                # 处理定时器命令
                return self._handle_timer_command(execution_data)
            else:
                # 通用处理
                return self._handle_generic_command(execution_data)
                
        except Exception as e:
            print(f"[AdminManager] 处理执行数据失败: {e}")
            return None
    
    def _handle_display_command(self, execution_data: Dict[str, Any]):
        """处理显示命令"""
        try:
            if self.task_queue:
                # 添加到任务队列
                task_data = {
                    'type': 'display',
                    'data': execution_data,
                    'priority': 'normal'
                }
                self.task_queue.add_task(task_data)
                return {'status': 'added_to_queue', 'task_id': task_data.get('id')}
            
            return {'status': 'processed', 'message': 'Display command handled'}
            
        except Exception as e:
            print(f"[AdminManager] 处理显示命令失败: {e}")
            return None
    
    def _handle_timer_command(self, execution_data: Dict[str, Any]):
        """处理定时器命令"""
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
            print(f"[AdminManager] 处理定时器命令失败: {e}")
            return None
    
    def _handle_generic_command(self, execution_data: Dict[str, Any]):
        """处理通用命令"""
        try:
            return {'status': 'processed', 'message': 'Generic command handled'}
            
        except Exception as e:
            print(f"[AdminManager] 处理通用命令失败: {e}")
            return None
    
    def _process_remote_execution(self, execution_data: Dict[str, Any]):
        """处理远程执行（转移给其他程序）"""
        try:
            # 这里可以实现转移给其他程序的逻辑
            # 例如：发送到远程服务器、保存到共享文件等
            
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
                
                print(f"[AdminManager] 远程执行数据已保存到: {remote_file}")
                
            except Exception as e:
                print(f"[AdminManager] 保存远程执行数据失败: {e}")
                
        except Exception as e:
            print(f"[AdminManager] 处理远程执行失败: {e}")
    
    def switch_interface_mode(self, mode: str):
        """切换接口模式"""
        try:
            if self.interface_manager:
                from interface_manager import InterfaceMode
                mode_enum = InterfaceMode(mode)
                self.interface_manager.switch_mode(mode_enum)
                return True
            return False
        except Exception as e:
            print(f"[AdminManager] 切换接口模式失败: {e}")
            return False
    
    def get_system_status(self):
        """获取系统状态"""
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
            print(f"[AdminManager] 获取系统状态失败: {e}")
            return {}
    
    def _setup_routes(self):
        """设置Web路由"""
        
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
        """启动Web管理界面"""
        try:
            print(f"[AdminManager] 启动Web服务器: http://localhost:{self.port}")
            
            # 在新线程中启动服务器
            def run_server():
                self.app.run(host='0.0.0.0', port=self.port, debug=debug, use_reloader=False)
            
            server_thread = threading.Thread(target=run_server, daemon=True)
            server_thread.start()
            
            # 等待服务器启动
            time.sleep(2)
            
            # 自动打开浏览器
            try:
                webbrowser.open(f'http://localhost:{self.port}')
            except Exception as e:
                print(f"[AdminManager] 无法自动打开浏览器: {e}")
            
            print(f"[AdminManager] Web服务器已启动")
            
        except Exception as e:
            print(f"[AdminManager] 启动Web服务器失败: {e}")
    
    def stop_web_server(self):
        """停止Web服务器"""
        try:
            # Flask的shutdown方法
            print(f"[AdminManager] Web服务器停止请求已发送")
        except Exception as e:
            print(f"[AdminManager] 停止Web服务器失败: {e}")
    
    def get_execution_queue(self):
        """获取执行队列"""
        with self.execution_lock:
            return self.execution_queue.copy()
    
    def clear_execution_queue(self):
        """清空执行队列"""
        with self.execution_lock:
            self.execution_queue.clear()
            print(f"[AdminManager] 执行队列已清空")