import json
import os
import threading
import time
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from enum import Enum
import queue

class TaskStatus(Enum):
    WAITING = "waiting"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskPriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4

class TaskQueueManager:
    """
    任务队列类 - 管理任务的存储、分配和执行
    """
    
    def __init__(self, storage_file: str = None):
        import os
        data_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'data'))
        self.storage_file = storage_file or os.path.join(data_dir, "task_storage.json")
        self.tasks = {}  # 所有任务
        self.waiting_queue = queue.PriorityQueue()  # 等待队列
        self.executing_tasks = {}  # 正在执行的任务
        self.completed_tasks = {}  # 历史任务
        self.blocked_users = set()  # 被阻止的用户
        
        # 线程锁
        self.lock = threading.Lock()
        self.storage_lock = threading.Lock()
        
        # 工作线程
        self.worker_thread = None
        self.running = False
        
        # 加载存储的任务
        self._load_tasks()
        
        # 启动工作线程
        self.start_worker()
        
        print(f"[TaskQueueManager] 任务队列管理器初始化完成")
    
    def _load_tasks(self):
        """加载存储的任务"""
        try:
            if os.path.exists(self.storage_file):
                with self.storage_lock:
                    with open(self.storage_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        
                        self.tasks = data.get('tasks', {})
                        self.completed_tasks = data.get('completed_tasks', {})
                        self.blocked_users = set(data.get('blocked_users', []))
                        
                        # 恢复等待队列
                        waiting_tasks = data.get('waiting_tasks', [])
                        for task_data in waiting_tasks:
                            task_id = task_data['id']
                            priority = TaskPriority(task_data.get('priority', TaskPriority.NORMAL.value))
                            self.waiting_queue.put((priority.value * -1, task_id))  # 负值用于优先级排序
                        
                print(f"[TaskQueueManager] 已加载 {len(self.tasks)} 个任务")
        except Exception as e:
            print(f"[TaskQueueManager] 加载任务失败: {e}")
    
    def _save_tasks(self):
        """保存任务到存储文件"""
        try:
            with self.storage_lock:
                # 获取等待队列快照
                waiting_tasks = []
                temp_queue = queue.PriorityQueue()
                while not self.waiting_queue.empty():
                    try:
                        priority, task_id = self.waiting_queue.get_nowait()
                        temp_queue.put((priority, task_id))
                        if task_id in self.tasks:
                            waiting_tasks.append(self.tasks[task_id])
                    except queue.Empty:
                        break
                
                # 恢复队列
                self.waiting_queue = temp_queue
                
                data = {
                    'tasks': self.tasks,
                    'waiting_tasks': waiting_tasks,
                    'completed_tasks': self.completed_tasks,
                    'blocked_users': list(self.blocked_users),
                    'last_updated': datetime.now().isoformat()
                }
                
                with open(self.storage_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[TaskQueueManager] 保存任务失败: {e}")
    
    def add_task(self, task_data: Dict[str, Any], user: str = None, priority: TaskPriority = TaskPriority.NORMAL):
        """添加新任务"""
        try:
            with self.lock:
                # 检查用户是否被阻止
                if user and user in self.blocked_users:
                    print(f"[TaskQueueManager] 用户 {user} 被阻止，忽略任务")
                    return None
                
                # 生成任务ID
                task_id = str(uuid.uuid4())
                
                # 创建任务对象
                task = {
                    'id': task_id,
                    'user': user,
                    'data': task_data,
                    'priority': priority.value,
                    'status': TaskStatus.WAITING.value,
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat(),
                    'retry_count': 0,
                    'max_retries': 3
                }
                
                # 存储任务
                self.tasks[task_id] = task
                
                # 添加到等待队列
                self.waiting_queue.put((priority.value * -1, task_id))  # 负值用于优先级排序
                
                # 保存到文件
                self._save_tasks()
                
                print(f"[TaskQueueManager] 任务已添加: {task_id} (用户: {user}, 优先级: {priority.name})")
                return task_id
                
        except Exception as e:
            print(f"[TaskQueueManager] 添加任务失败: {e}")
            return None
        
    def remove_task(self, task_id: str):
        """删除等待中或已完成的任务"""
        try:
            with self.lock:
                # 1) 如果在当前等待队列中
                if task_id in self.tasks:
                    task = self.tasks.pop(task_id)
                    task['status'] = TaskStatus.CANCELLED.value
                    print(f"[TaskQueueManager] 任务已删除: {task_id}")
                # 2) 如果在完成历史中
                elif task_id in self.completed_tasks:
                    self.completed_tasks.pop(task_id)
                    print(f"[TaskQueueManager] 已完成任务已删除: {task_id}")
                else:
                    print(f"[TaskQueueManager] 任务不存在: {task_id}")
                    return False

                # 保存更新
                self._save_tasks()
                return True
        except Exception as e:
            print(f"[TaskQueueManager] 删除任务失败: {e}")
            return False


    def start_worker(self):
        if not getattr(self, 'running', False):
            self.running = True
            self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
            self.worker_thread.start()
            print("[TaskQueueManager] 工作线程已启动")

    def stop_worker(self):
        self.running = False
        if hasattr(self, 'worker_thread') and self.worker_thread:
            self.worker_thread.join()
            print("[TaskQueueManager] 工作线程已停止")


    def get_waiting_tasks(self):
        """获取等待中的任务列表"""
        return [task for task in self.tasks.values() if task['status'] == TaskStatus.WAITING.value]
    
    def get_executing_tasks(self):
        """获取正在执行的任务列表"""
        return list(self.executing_tasks.values())
    
    def get_completed_tasks(self):
        """获取已完成的任务列表"""
        return list(self.completed_tasks.values())
    

    def _worker_loop(self):
        """工作线程主循环"""
        while self.running:
            try:
                # 从队列获取任务
                priority, task_id = self.waiting_queue.get(timeout=1)
                
                if task_id not in self.tasks:
                    continue
                
                task = self.tasks[task_id]
                # 检查任务是否已被取消
                if task['status'] == TaskStatus.CANCELLED.value:
                    continue
                # 检查用户是否被阻止
                if task.get('user') in self.blocked_users:
                    print(f"[TaskQueueManager] 跳过被阻止用户的任务: {task_id}")
                    continue
                # 执行任务
                self._execute_task(task)
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"[TaskQueueManager] 工作线程错误: {e}")



