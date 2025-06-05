import time
import threading
from abc import ABC, abstractmethod
from typing import List, Dict, Any

class ITaskQueue(ABC):
    @abstractmethod
    def add_task(self, func, high_priority=False, **kwargs):
        pass
    
    @abstractmethod
    def get_queue_status(self) -> Dict[str, List[Dict[str, Any]]]:
        pass

class TaskQueue(ITaskQueue):
    def __init__(self, device_manager):
        self.device_manager = device_manager
        self.queue = []
        self.current_tasks = {}
        self.completed_tasks = []
        self.lock = threading.Lock()
        self.task_id = 0
        self.max_completed_tasks = 10

    def add_task(self, func, high_priority=False, **kwargs):
        with self.lock:
            self.task_id += 1
            task = {
                "id": self.task_id,
                "func": func,
                "kwargs": kwargs,
                "priority": "High" if high_priority else "Normal",
                "status": "Pending",
                "created": time.time()
            }
            if high_priority:
                self.queue.insert(0, task)
            else:
                self.queue.append(task)
            return self.task_id

    def get_queue_status(self):
        with self.lock:
            return {
                "pending": [t.copy() for t in self.queue],
                "running": [t.copy() for t in self.current_tasks.values()],
                "completed": [t.copy() for t in self.completed_tasks]
            }

    def process_next_task(self):
        with self.lock:
            if not self.queue:
                return None

            task = self.queue.pop(0)
            device = next(
                (d for d in self.device_manager.get_devices() 
                 if not d["disabled"] and d["status"] == "Idle"),
                None
            )
            if not device:
                self.queue.insert(0, task)
                return None

            device["status"] = "Busy"
            task["device"] = device["name"]
            task["start_time"] = time.time()
            task["status"] = "Running"
            self.current_tasks[device["id"]] = task
            return task

    def complete_task(self, device_id):
        with self.lock:
            if device_id in self.current_tasks:
                task = self.current_tasks.pop(device_id)
                task["status"] = "Completed"
                task["end_time"] = time.time()
                task["duration"] = task["end_time"] - task["start_time"]
                self.completed_tasks.append(task)
                if len(self.completed_tasks) > self.max_completed_tasks:
                    self.completed_tasks.pop(0)
                
                for device in self.device_manager.get_devices():
                    if device["id"] == device_id:
                        device["status"] = "Idle"
                        break
