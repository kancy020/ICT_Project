from flask import Flask, render_template_string, request, jsonify
import threading
import time
from datetime import datetime
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
                .panel { border: 1px solid #ddd; padding: 15px; border-radius: 5px; position: relative; }
                .device { margin: 10px 0; padding: 10px; background: #f0f8ff; }
                .user-panel { height: 300px; overflow-y: auto; border: 1px solid #eee; padding: 10px; }
                .user { margin: 5px 0; padding: 8px; }
                .active { background: #e6ffe6; }
                .inactive { background: #ffe6e6; }
                .task { margin: 5px 0; padding: 8px; }
                .high { background: #ffdddd; }
                .completed { opacity: 0.6; }
                button { padding: 5px 10px; margin: 2px; }
                #display-preview {
                    position: fixed;
                    bottom: 20px;
                    right: 20px;
                    width: 200px;
                    height: 200px;
                    border: 2px solid #333;
                    background: #000;
                    color: #FFF;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 48px;
                    border-radius: 10px;
                    z-index: 1000;
                }
                .back-button {
                    display: inline-block;
                    margin-top: 10px;
                    padding: 8px 15px;
                    background: #4CAF50;
                    color: white;
                    text-decoration: none;
                    border-radius: 4px;
                }
                .task-list {
                    max-height: 200px;
                    overflow-y: auto;
                    border: 1px solid #eee;
                    padding: 10px;
                    margin-bottom: 15px;
                }
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
                    <div class="task-list">
                        <h4>Running ({{ queue_status.running|length }})</h4>
                        {% for task in queue_status.running %}
                        <div class="task">
                            {{ task.func.__name__ }} @ {{ task.device }}
                            <small>({{ "%.1f"|format(task.duration) }}s)</small>
                        </div>
                        {% endfor %}
                        
                        <h4>Pending ({{ queue_status.pending|length }})</h4>
                        {% for task in queue_status.pending %}
                        <div class="task {% if task.priority == 'High' %}high{% endif %}">
                            {{ task.func.__name__ }} ({{ task.priority }})
                        </div>
                        {% endfor %}
                        
                        <h4>Completed ({{ queue_status.completed|length }})</h4>
                        {% for task in queue_status.completed %}
                        <div class="task completed">
                            {{ task.func.__name__ }} @ {{ task.device }} 
                            <small>({{ "%.1f"|format(task.duration) }}s)</small>
                        </div>
                        {% endfor %}
                    </div>
                </div>
                
                <div class="panel">
                    <h2>User Permissions</h2>
                    <button onclick="location.href='/refresh_permissions'">Refresh Permissions</button>
                    <div class="user-panel">
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
            
            <div id="display-preview">
                {% if queue_status.running %}
                    {% set current_task = queue_status.running[0] %}
                    {% if current_task.func.__name__ == 'show_matrix_emoji' %}
                        {{ current_task.kwargs.emoji }}
                    {% elif current_task.func.__name__ == 'sync_time' %}
                        {{ now().strftime('%H:%M:%S') }}
                    {% else %}
                        {{ current_task.func.__name__ }}
                    {% endif %}
                {% else %}
                    Idle
                {% endif %}
            </div>
            
            <script>
                function refreshDisplay() {
                    fetch('/queue_status')
                        .then(response => response.json())
                        .then(data => {
                            const preview = document.getElementById('display-preview');
                            if (data.running.length > 0) {
                                const task = data.running[0];
                                if (task.func.includes('show_matrix_emoji')) {
                                    preview.textContent = task.kwargs.emoji || '🔄';
                                } else if (task.func.includes('sync_time')) {
                                    preview.textContent = new Date().toLocaleTimeString();
                                } else {
                                    preview.textContent = task.func.split('.')[-1];
                                }
                            } else {
                                preview.textContent = 'Idle';
                            }
                            
                            // 更新任务列表
                            if (data.running.length > 0) {
                                document.querySelectorAll('.task-list h4:nth-of-type(1)')[0]
                                    .innerHTML = `Running (${data.running.length})`;
                            }
                        });
                    
                    setTimeout(refreshDisplay, 1000);
                }
                
                window.addEventListener('load', refreshDisplay);
            </script>
        </body>
        </html>
    ''', devices=devices, queue_status=queue_status, users=users, now=datetime.now)

@app.route('/queue_status')
def queue_status():
    return jsonify(task_queue.get_queue_status())

@app.route('/toggle_permission/<int:user_id>')
def toggle_permission(user_id):
    success = permission_manager.toggle_permission(user_id)
    return f'''
        <div style="padding: 20px; text-align: center;">
            <h2>{"Permission updated successfully!" if success else "User not found!"}</h2>
            <a href="/" class="back-button">Back to Control Panel</a>
        </div>
    ''', 200 if success else 404

# ... 保持其他路由不变 ...

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
