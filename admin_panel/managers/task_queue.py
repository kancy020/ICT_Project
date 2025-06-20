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
    Task queue class - Manages task storage, distribution and execution
    """
    
    def __init__(self, storage_file: str = None):
        import os
        data_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'data'))
        self.storage_file = storage_file or os.path.join(data_dir, "task_storage.json")
        self.tasks = {}  # All tasks
        self.waiting_queue = queue.PriorityQueue()  # Waiting queue
        self.executing_tasks = {}  # Currently executing tasks
        self.completed_tasks = {}  # Historical tasks
        self.blocked_users = set()  # Blocked users
        
        # Thread locks
        self.lock = threading.Lock()
        self.storage_lock = threading.Lock()
        
        # Worker thread
        self.worker_thread = None
        self.running = False
        
        # Load stored tasks
        self._load_tasks()
        
        # Start worker thread
        self.start_worker()
        
        print(f"[TaskQueueManager] Task queue manager initialized")

    def _load_tasks(self):
        """Load stored tasks"""
        try:
            if os.path.exists(self.storage_file):
                with self.storage_lock:
                    with open(self.storage_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        
                        self.tasks = data.get('tasks', {})
                        self.completed_tasks = data.get('completed_tasks', {})
                        self.blocked_users = set(data.get('blocked_users', []))
                        
                        # Restore waiting queue
                        waiting_tasks = data.get('waiting_tasks', [])
                        for task_data in waiting_tasks:
                            task_id = task_data['id']
                            priority = TaskPriority(task_data.get('priority', TaskPriority.NORMAL.value))
                            self.waiting_queue.put((priority.value * -1, task_id))  # Negative value for priority sorting
                    
                print(f"[TaskQueueManager] Loaded {len(self.tasks)} tasks")
        except Exception as e:
            print(f"[TaskQueueManager] Failed to load tasks: {e}")

    def _save_tasks(self):
        """Save tasks to storage file"""
        try:
            with self.storage_lock:
                # Get waiting queue snapshot
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
                
                # Restore queue
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
            print(f"[TaskQueueManager] Failed to save tasks: {e}")

    def add_task(self, task_data: Dict[str, Any], user: str = None, priority: TaskPriority = TaskPriority.NORMAL):
        """Add new task"""
        try:
            with self.lock:
                # Check if user is blocked
                if user and user in self.blocked_users:
                    print(f"[TaskQueueManager] User {user} is blocked, ignoring task")
                    return None
                
                # Generate task ID
                task_id = str(uuid.uuid4())
                
                # Create task object
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
                
                # Store task
                self.tasks[task_id] = task
                
                # Add to waiting queue
                self.waiting_queue.put((priority.value * -1, task_id))  # Negative value for priority sorting
                
                # Save to file
                self._save_tasks()
                
                print(f"[TaskQueueManager] Task added: {task_id} (User: {user}, Priority: {priority.name})")
                return task_id
                
        except Exception as e:
            print(f"[TaskQueueManager] Failed to add task: {e}")
            return None

    def remove_task(self, task_id: str):
        """Remove waiting or completed task"""
        try:
            with self.lock:
                # 1) If in current waiting queue
                if task_id in self.tasks:
                    task = self.tasks.pop(task_id)
                    task['status'] = TaskStatus.CANCELLED.value
                    print(f"[TaskQueueManager] Task removed: {task_id}")
                # 2) If in completed history
                elif task_id in self.completed_tasks:
                    self.completed_tasks.pop(task_id)
                    print(f"[TaskQueueManager] Completed task removed: {task_id}")
                else:
                    print(f"[TaskQueueManager] Task doesn't exist: {task_id}")
                    return False

                # Save changes
                self._save_tasks()
                return True
        except Exception as e:
            print(f"[TaskQueueManager] Failed to remove task: {e}")
            return False

    def start_worker(self):
        """Start worker thread"""
        if not getattr(self, 'running', False):
            self.running = True
            self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
            self.worker_thread.start()
            print("[TaskQueueManager] Worker thread started")

    def stop_worker(self):
        """Stop worker thread"""
        self.running = False
        if hasattr(self, 'worker_thread') and self.worker_thread:
            self.worker_thread.join()
            print("[TaskQueueManager] Worker thread stopped")

    def get_waiting_tasks(self):
        """Get list of waiting tasks"""
        return [task for task in self.tasks.values() if task['status'] == TaskStatus.WAITING.value]

    def get_executing_tasks(self):
        """Get list of executing tasks"""
        return list(self.executing_tasks.values())

    def get_completed_tasks(self):
        """Get list of completed tasks"""
        return list(self.completed_tasks.values())

    def _worker_loop(self):
        """Worker thread main loop"""
        while self.running:
            try:
                # Get task from queue
                priority, task_id = self.waiting_queue.get(timeout=1)
                
                if task_id not in self.tasks:
                    continue
                
                task = self.tasks[task_id]
                # Check if task was cancelled
                if task['status'] == TaskStatus.CANCELLED.value:
                    continue
                # Check if user is blocked
                if task.get('user') in self.blocked_users:
                    print(f"[TaskQueueManager] Skipping task from blocked user: {task_id}")
                    continue
                # Execute task
                self._execute_task(task)
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"[TaskQueueManager] Worker thread error: {e}")
