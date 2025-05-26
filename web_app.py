from flask import Flask, render_template_string, request
import threading
import time
from device_manager import DeviceManager
from task_queue import TaskQueue
from user_permission import UserPermissionManager
from command_parser import SlackCommandParser
from task_functions import show_emoji, turn_off, turn_on, flip, sync_time

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
                #user-panel { height: 300px; overflow-y: auto; border: 1px solid #eee; padding: 10px; }
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
                <div class="panel">
                    <h2>Device Management</h2>
                    {% for device in devices %}
                    <div class="device">
                        <h3>{{ device.name }}</h3>
                        <p>Status: {{ device.status }}</p>
                        <p>Disabled: {{ "Yes" if device.disabled else "No" }}</p>
                        <button onclick="location.href='/toggle_power/{{ device.id }}'">Toggle Power</button>
                        <button onclick="location.href='/toggle_disable/{{ device.id }}'">Toggle Disable</button>
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
                
                <div class="panel">
                    <h2>User Permissions</h2>
                    <button onclick="location.href='/refresh_permissions'">Refresh Permissions</button>
                    <div id="user-panel">
                        {% for user in users %}
                        <div class="user {{ 'active' if user.permission == 'Active' else 'inactive' }}">
                            <h3>{{ user.name }}</h3>
                            <p>Status: {{ user.permission }}</p>
                            <button onclick="location.href='/toggle_permission/{{ user.id }}'">Toggle Permission</button>
                        </div>
                        {% endfor %}
                    </div>
                </div>
            </div>
        </body>
        </html>
    ''', devices=devices, queue_status=queue_status, users=users)

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

if __name__ == '__main__':
    threading.Thread(target=background_worker, daemon=True).start()
    app.run(host='0.0.0.0', port=8888, debug=True)
