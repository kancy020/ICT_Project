import time
import threading
import re
from flask import Flask, render_template_string, request
from abc import ABC, abstractmethod

# ==================== Interfaces ====================
class IDeviceManager(ABC):

    @abstractmethod
    def get_devices(self):
        pass
    
    @abstractmethod
    def toggle_power(self, device_id):
        pass
    
    @abstractmethod
    def toggle_disable(self, device_id):
        pass

class ITaskQueue(ABC):
    """任务队列接口"""
    @abstractmethod
    def add_task(self, func, high_priority=False, **kwargs):
        pass
    
    @abstractmethod
    def get_queue_status(self):
        pass

class IUserPermissionManager(ABC):
    """用户权限接口"""
    @abstractmethod
    def get_users(self):
        pass
    
    @abstractmethod
    def toggle_permission(self, user_id):
        pass
    
    @abstractmethod
    def fetch_permissions(self):
        pass

class ICommandParser(ABC):
    """命令解析接口"""
    @abstractmethod
    def parse(self, text):
        pass

# ==================== Implementations ====================
class DeviceManager(IDeviceManager):
    """Manage Device A and Device B"""
    def __init__(self):
        self.devices = [
            {"id": 0, "name": "Device A", "status": "Idle", "disabled": False, "type": "screen"},
            {"id": 1, "name": "Device B", "status": "Idle", "disabled": False, "type": "screen"}
        ]
        self.lock = threading.Lock()

    def get_devices(self):
        with self.lock:
            return [d.copy() for d in self.devices]

    def toggle_power(self, device_id):
        with self.lock:
            for device in self.devices:
                if device["id"] == device_id:
                    device["status"] = "Off" if device["status"] == "Idle" else "Idle"
                    return True
        return False

    def toggle_disable(self, device_id):
        with self.lock:
            for device in self.devices:
                if device["id"] == device_id:
                    device["disabled"] = not device["disabled"]
                    return True
        return False

class UserPermissionManager(IUserPermissionManager):
    """Manage User A, B, C permissions"""
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
        # Simulate permission changes
        new_users = [
            {"id": 1, "name": "User A", "permission": "Active"},
            {"id": 2, "name": "User B", "permission": "Inactive"},
            {"id": 3, "name": "User C", "permission": "Inactive"}
        ]
        with self.lock:
            self.users = new_users
        return True

class TaskQueue(ITaskQueue):
    """Task queue implementation"""
    def __init__(self, device_manager):
        self.device_manager = device_manager
        self.queue = []
        self.current_tasks = {}
        self.lock = threading.Lock()
        self.task_id = 0

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
                "running": [t.copy() for t in self.current_tasks.values()]
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
                for device in self.device_manager.get_devices():
                    if device["id"] == device_id:
                        device["status"] = "Idle"
                        break

class SlackCommandParser(ICommandParser):
    """Parse Slack-style commands"""
    def __init__(self):
        self.emoji_map = {
            ":smile:": "😊", ":laugh:": "😂", ":party:": "🎉",
            ":balloon:": "🎈", ":art:": "🎨", ":clock:": "⏰"
        }
        self.commands = {
            "show": "show_emoji",
            "turn off": "turn_off",
            "turn on": "turn_on",
            "flip": "flip",
            "sync": "sync_time"
        }

    def parse(self, text):
        for slack_emoji, unicode_emoji in self.emoji_map.items():
            text = text.replace(slack_emoji, unicode_emoji)
        
        delay = 0
        delay_match = re.search(r"in (\d+)s", text)
        if delay_match:
            delay = int(delay_match.group(1))
            text = text.replace(delay_match.group(0), "")

        emoji = None
        emoji_match = re.search(r"[\U0001F300-\U0001F5FF\U0001F600-\U0001F64F\U0001F680-\U0001F6FF]", text)
        if emoji_match:
            emoji = emoji_match.group()

        command = None
        for cmd_key, cmd_value in self.commands.items():
            if cmd_key in text.lower():
                command = cmd_value
                break

        return {
            "command": command,
            "emoji": emoji,
            "delay": delay,
            "text": text
        }

# ==================== Task Functions ====================
def show_emoji(emoji, **kwargs):
    print(f"Displaying emoji: {emoji}")
    time.sleep(2)

def turn_off(**kwargs):
    print("Turning off display")
    time.sleep(1)

def turn_on(**kwargs):
    print("Turning on display")
    time.sleep(1)

def flip(**kwargs):
    print("Flipping display")
    time.sleep(1.5)

def sync_time(**kwargs):
    print("Syncing time")
    time.sleep(1)

# ==================== Web Application ====================
app = Flask(__name__)
device_manager = DeviceManager()
task_queue = TaskQueue(device_manager)
permission_manager = UserPermissionManager()
command_parser = SlackCommandParser()

@app.route('/')
def control_panel():
    devices = device_manager.get_devices()
    queue_status = task_queue.get_queue_status()
    users = permission_manager.get_users()
    
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Control System</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .dashboard { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
                .panel { border: 1px solid #ddd; padding: 15px; border-radius: 5px; }
                .device { margin: 10px 0; padding: 10px; background: #f0f8ff; }
                #user-panel { 
                    height: 300px; 
                    overflow-y: auto;
                    border: 1px solid #eee;
                    padding: 10px;
                }
                .user { margin: 5px 0; padding: 8px; }
                .active { background: #e6ffe6; }
                .inactive { background: #ffe6e6; }
                .task { margin: 5px 0; padding: 8px; }
                .high { background: #ffdddd; }
                button { padding: 5px 10px; margin: 2px; }
            </style>
        </head>
        <body>
            <h1>Control System</h1>
            
            <div class="dashboard">
                <!-- Left Panel -->
                <div class="panel">
                    <h2>Device Management</h2>
                    {% for device in devices %}
                    <div class="device">
                        <h3>{{ device.name }}</h3>
                        <p>Status: {{ device.status }}</p>
                        <p>Disabled: {{ "Yes" if device.disabled else "No" }}</p>
                        <button onclick="location.href='/toggle_power/{{ device.id }}'">
                            Toggle Power
                        </button>
                        <button onclick="location.href='/toggle_disable/{{ device.id }}'">
                            Toggle Disable
                        </button>
                    </div>
                    {% endfor %}
                    
                    <h2>Task Control</h2>
                    <div>
                        <h3>Slack Command</h3>
                        <form action="/command/slack" method="post">
                            <input type="text" name="command" style="width:80%">
                            <button type="submit">Submit</button>
                        </form>
                    </div>
                    <div>
                        <h3>Direct Control</h3>
                        <form action="/command/direct" method="post">
                            <select name="action">
                                <option value="show_emoji">Show Emoji</option>
                                <option value="turn_off">Turn Off</option>
                                <option value="turn_on">Turn On</option>
                                <option value="flip">Flip Display</option>
                                <option value="sync_time">Sync Time</option>
                            </select>
                            <input type="text" name="emoji" placeholder="Emoji">
                            <input type="number" name="delay" placeholder="Delay(s)">
                            <label><input type="checkbox" name="high_priority"> High Priority</label>
                            <button type="submit">Execute</button>
                        </form>
                    </div>
                    
                    <h3>Task Queue</h3>
                    <h4>Running ({{ queue_status.running|length }})</h4>
                    {% for task in queue_status.running %}
                    <div>{{ task.func.__name__ }} @ {{ task.device }}</div>
                    {% endfor %}
                    
                    <h4>Pending ({{ queue_status.pending|length }})</h4>
                    {% for task in queue_status.pending %}
                    <div class="task {% if task.priority == 'High' %}high{% endif %}">
                        {{ task.func.__name__ }} ({{ task.priority }})
                    </div>
                    {% endfor %}
                </div>
                
                <!-- Right Panel -->
                <div class="panel">
                    <h2>User Permissions</h2>
                    <button onclick="location.href='/refresh_permissions'">
                        Refresh Permissions
                    </button>
                    <div id="user-panel">
                        {% for user in users %}
                        <div class="user {{ 'active' if user.permission == 'Active' else 'inactive' }}">
                            <h3>{{ user.name }}</h3>
                            <p>Status: {{ user.permission }}</p>
                            <button onclick="location.href='/toggle_permission/{{ user.id }}'">
                                Toggle Permission
                            </button>
                        </div>
                        {% endfor %}
                    </div>
                </div>
            </div>
        </body>
        </html>
    ''', devices=devices, queue_status=queue_status, users=users)

# ==================== Device Routes ====================
@app.route('/toggle_power/<int:device_id>')
def toggle_power(device_id):
    if device_manager.toggle_power(device_id):
        return "Power toggled", 200
    return "Device not found", 404

@app.route('/toggle_disable/<int:device_id>')
def toggle_disable(device_id):
    if device_manager.toggle_disable(device_id):
        return "Disable toggled", 200
    return "Device not found", 404

# ==================== Permission Routes ====================
@app.route('/toggle_permission/<int:user_id>')
def toggle_permission(user_id):
    if permission_manager.toggle_permission(user_id):
        return "Permission toggled", 200
    return "User not found", 404

@app.route('/refresh_permissions')
def refresh_permissions():
    if permission_manager.fetch_permissions():
        return "Permissions refreshed", 200
    return "Refresh failed", 500

# ==================== Command Routes ====================
@app.route('/command/slack', methods=['POST'])
def handle_slack_command():
    command_text = request.form.get('command', '')
    parsed = command_parser.parse(command_text)
    
    if parsed["command"] == "show_emoji" and parsed["emoji"]:
        task_queue.add_task(
            func=show_emoji,
            high_priority="urgent" in parsed["text"].lower(),
            emoji=parsed["emoji"],
            delay=parsed["delay"]
        )
    elif parsed["command"] == "turn_off":
        task_queue.add_task(func=turn_off)
    elif parsed["command"] == "turn_on":
        task_queue.add_task(func=turn_on)
    elif parsed["command"] == "flip":
        task_queue.add_task(func=flip)
    elif parsed["command"] == "sync_time":
        task_queue.add_task(func=sync_time)
    
    return "Command received", 200

@app.route('/command/direct', methods=['POST'])
def handle_direct_command():
    action = request.form.get('action')
    emoji = request.form.get('emoji', '')
    delay = int(request.form.get('delay', 0))
    high_priority = request.form.get('high_priority') == 'on'
    
    if action == "show_emoji":
        task_queue.add_task(
            func=show_emoji,
            high_priority=high_priority,
            emoji=emoji,
            delay=delay
        )
    elif action == "turn_off":
        task_queue.add_task(func=turn_off, high_priority=high_priority)
    elif action == "turn_on":
        task_queue.add_task(func=turn_on, high_priority=high_priority)
    elif action == "flip":
        task_queue.add_task(func=flip, high_priority=high_priority)
    elif action == "sync_time":
        task_queue.add_task(func=sync_time, high_priority=high_priority)
    
    return "Command executed", 200

# ==================== Background Worker ====================
def background_worker():
    while True:
        task = task_queue.process_next_task()
        if task:
            try:
                if task["kwargs"].get("delay", 0) > 0:
                    time.sleep(task["kwargs"]["delay"])
                task["func"](**task["kwargs"])
            except Exception as e:
                print(f"Task failed: {e}")
            finally:
                device_id = next(
                    d["id"] for d in device_manager.get_devices() 
                    if d["name"] == task["device"]
                )
                task_queue.complete_task(device_id)
        else:
            time.sleep(0.5)

# ==================== Start Application ====================
if __name__ == '__main__':
    threading.Thread(target=background_worker, daemon=True).start()
    app.run(host='0.0.0.0', port=8888, debug=True)
