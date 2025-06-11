from flask import Flask, render_template_string, request, jsonify
import threading
import time
from datetime import datetime
from device_manager import DeviceManager
from task_queue import TaskQueue
from user_permission import UserPermissionManager
from command_parser import SlackCommandParser
from pixel_adapter import RaspberryPixelAdapter

app = Flask(__name__)

# 初始化
device_manager = DeviceManager()
pi_adapter = RaspberryPixelAdapter(device_manager)
task_queue = TaskQueue(device_manager)
permission_manager = UserPermissionManager()
command_parser = SlackCommandParser()

# 完整HTML模板
CONTROL_PANEL_HTML = """<!DOCTYPE html>
<html>
<head>
    <title>Pixel Display Controller</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .dashboard {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 25px;
            margin-top: 20px;
        }
        .panel {
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 20px;
        }
        .device {
            margin: 15px 0;
            padding: 15px;
            border-left: 4px solid #4CAF50;
            background-color: #f9f9f9;
        }
        .device.offline {
            border-left-color: #f44336;
            opacity: 0.7;
        }
        .task {
            padding: 10px;
            margin: 5px 0;
            border-radius: 4px;
            font-size: 14px;
            position: relative;
        }
        .task.running {
            background-color: #e3f2fd;
            border-left: 3px solid #2196F3;
        }
        .task.pending {
            background-color: #fff8e1;
            border-left: 3px solid #ffc107;
        }
        .task.high {
            background-color: #ffebee;
            border-left: 3px solid #f44336;
        }
        .delete-btn {
            position: absolute;
            right: 10px;
            top: 50%;
            transform: translateY(-50%);
            background: #f44336 !important;
            border-radius: 50%;
            width: 20px;
            height: 20px;
            padding: 0;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            cursor: pointer;
            border: none;
            color: white;
        }
        #display-preview {
            position: fixed;
            bottom: 30px;
            right: 30px;
            width: 150px;
            height: 150px;
            border-radius: 10px;
            background: #000;
            color: #FFF;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 60px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        }
        button, input, select {
            padding: 8px 12px;
            margin: 5px 0;
            border-radius: 4px;
            border: 1px solid #ddd;
        }
        button {
            background-color: #4CAF50;
            color: white;
            border: none;
            cursor: pointer;
        }
        button:hover {
            opacity: 0.9;
        }
        form {
            margin-top: 20px;
            display: grid;
            gap: 10px;
        }
        .status-badge {
            display: inline-block;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 12px;
            background: #e0e0e0;
        }
        .status-active {
            background: #c8e6c9;
            color: #2e7d32;
        }
        .user-management {
            grid-column: span 2;
        }
        .user-card {
            display: flex;
            justify-content: space-between;
            padding: 10px;
            margin: 5px 0;
            background: #f9f9f9;
            border-radius: 4px;
        }
        .user-active {
            border-left: 4px solid #4CAF50;
        }
        .user-inactive {
            border-left: 4px solid #f44336;
            opacity: 0.7;
        }
        #content-input-container {
            transition: height 0.3s ease;
        }
    </style>
</head>
<body>
    <h1>Pixel Display Controller</h1>
    <p>Last updated: {{ now.strftime('%Y-%m-%d %H:%M:%S') }}</p>

    <div class="dashboard">
        <!-- 设备管理面板 -->
        <div class="panel">
            <h2>Device Management</h2>
            {% for device in devices %}
            <div class="device {% if device.status != 'Idle' %}offline{% endif %}">
                <h3>{{ device.name }}</h3>
                <p>
                    <span class="status-badge {% if device.status == 'Idle' %}status-active{% endif %}">
                        {{ device.status }}
                    </span>
                    · IP: {{ device.ip }}
                </p>
                <button onclick="toggleDevicePower({{ device.id }})">
                    {{ 'Turn Off' if device.status == 'Idle' else 'Turn On' }}
                </button>
            </div>
            {% endfor %}

            <h2>Send Command</h2>
            <form onsubmit="sendCommand(event); return false;">
                <select name="command_type" id="command-select" required>
                    <option value="">-- Select Command --</option>
                    <option value="show_emoji">Show Emoji</option>
                    <option value="show_text">Show Text</option>
                    <option value="turn_on">Turn On Display</option>
                    <option value="turn_off">Turn Off Display</option>
                    <option value="sync_time">Sync Time</option>
                    <option value="show_GIF">Show GIF</option>
                </select>
                
                <div id="content-input-container">
                    <input type="text" name="content" id="content-input" 
                           placeholder="输入内容..." style="display: none;">
                </div>
                
                <label>
                    <input type="checkbox" name="high_priority"> High Priority
                </label>
                <button type="submit">Submit to Queue</button>
            </form>
        </div>

        <!-- 任务队列面板 -->
        <div class="panel">
            <h2>Task Queue</h2>
            <div id="queue-container">
                <h3>Running ({{ queue_status.running|length }})</h3>
                {% for task in queue_status.running %}
                <div class="task running" data-task-id="{{ task.id }}">
                    {{ task.func }} 
                    {% if task.kwargs.emoji %}{{ task.kwargs.emoji }}
                    {% elif task.kwargs.text %}{{ task.kwargs.text|truncate(10) }}
                    {% endif %}
                    <small>on {{ task.device }}</small>
                    <button class="delete-btn" onclick="deleteTask('{{ task.id }}')">×</button>
                </div>
                {% endfor %}

                <h3>Pending ({{ queue_status.pending|length }})</h3>
                {% for task in queue_status.pending %}
                <div class="task pending {% if task.priority == 'High' %}high{% endif %}" data-task-id="{{ task.id }}">
                    {{ task.func }} 
                    {% if task.kwargs.emoji %}{{ task.kwargs.emoji }}
                    {% elif task.kwargs.text %}{{ task.kwargs.text|truncate(10) }}
                    {% endif %}
                    <small>({{ task.priority }} priority)</small>
                    <button class="delete-btn" onclick="deleteTask('{{ task.id }}')">×</button>
                </div>
                {% endfor %}

                <h3>Completed ({{ queue_status.completed|length }})</h3>
                {% for task in queue_status.completed %}
                <div class="task">
                    {{ task.func }} 
                    {% if task.kwargs.emoji %}{{ task.kwargs.emoji }}
                    {% elif task.kwargs.text %}{{ task.kwargs.text|truncate(10) }}
                    {% endif %}
                    <small>{{ "%.1f"|format(task.duration) }}s</small>
                </div>
                {% endfor %}
            </div>
        </div>

        <!-- 用户管理面板 -->
        <div class="panel user-management">
            <h2>User Management</h2>
            <div id="users-container">
                {% for user in users %}
                <div class="user-card {% if user.permission == 'Active' %}user-active{% else %}user-inactive{% endif %}" 
                     data-user-id="{{ user.id }}">
                    <div>
                        <strong>{{ user.name }}</strong> ({{ user.role }})
                        <span class="status-badge {% if user.permission == 'Active' %}status-active{% endif %}">
                            {{ user.permission }}
                        </span>
                    </div>
                    <div>
                        <button onclick="togglePermission({{ user.id }}, this)">
                            {{ 'Deactivate' if user.permission == 'Active' else 'Activate' }}
                        </button>
                    </div>
                </div>
                {% endfor %}
            </div>
            <button onclick="refreshUsers()" style="margin-top: 10px;">Refresh Users</button>
        </div>
    </div>

    <!-- 实时预览窗口 -->
    <div id="display-preview">
        {% if queue_status.running %}
            {% set task = queue_status.running[0] %}
            {% if task.func == 'show_emoji' %}
                {{ task.kwargs.emoji }}
            {% elif task.func == 'show_text' %}
                {{ task.kwargs.text|truncate(3, True) }}
            {% else %}
                {{ task.func|replace('_', ' ')|title }}
            {% endif %}
        {% else %}
            🌀
        {% endif %}
    </div>

    <script>
        // 命令选择处理
        document.getElementById('command-select').addEventListener('change', function() {
            const inputField = document.getElementById('content-input');
            const needsInput = ['show_emoji', 'show_text'].includes(this.value);
            inputField.style.display = needsInput ? 'block' : 'none';
            inputField.toggleAttribute('required', needsInput);
        });

        // 发送命令
        function sendCommand(event) {
            event.preventDefault();
            const form = event.target;
            const commandType = form.command_type.value;
            const payload = {
                command_type: commandType,
                high_priority: form.high_priority.checked
            };

            if (['show_emoji', 'show_text'].includes(commandType)) {
                if (!form.content.value.trim()) {
                    alert('请输入内容');
                    return;
                }
                payload[commandType === 'show_emoji' ? 'emoji' : 'text'] = form.content.value;
            }

            fetch('/api/command', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            }).then(response => {
                if (response.ok) {
                    alert('任务已添加');
                    form.reset();
                    document.getElementById('content-input').style.display = 'none';
                } else {
                    alert('添加任务失败');
                }
            });
        }

        // 删除任务
        function deleteTask(taskId) {
            if (confirm('确定删除此任务？')) {
                fetch('/api/admin/tasks', {
                    method: 'DELETE',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ task_id: taskId })
                });
            }
        }

        // 切换设备电源
        function toggleDevicePower(deviceId) {
            fetch(`/toggle_power/${deviceId}`)
                .then(response => response.json())
                .then(data => {
                    if (!data.success) {
                        alert('操作失败');
                    }
                });
        }

        // 用户权限切换
        function togglePermission(userId, button) {
            fetch('/api/users/toggle_permission', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: userId })
            }).then(response => response.json())
              .then(data => {
                  if (data.success) {
                      const userCard = button.closest('.user-card');
                      userCard.classList.toggle('user-active');
                      userCard.classList.toggle('user-inactive');
                      
                      const statusBadge = userCard.querySelector('.status-badge');
                      statusBadge.textContent = statusBadge.textContent === 'Active' ? 'Inactive' : 'Active';
                      statusBadge.classList.toggle('status-active');
                      
                      button.textContent = button.textContent === 'Activate' ? 'Deactivate' : 'Activate';
                  } else {
                      alert('操作失败');
                  }
              });
        }

        // 刷新用户列表
        function refreshUsers() {
            fetch('/api/users')
                .then(response => response.json())
                .then(users => {
                    let html = '';
                    users.forEach(user => {
                        html += `
                        <div class="user-card ${user.permission === 'Active' ? 'user-active' : 'user-inactive'}" 
                             data-user-id="${user.id}">
                            <div>
                                <strong>${user.name}</strong> (${user.role})
                                <span class="status-badge ${user.permission === 'Active' ? 'status-active' : ''}">
                                    ${user.permission}
                                </span>
                            </div>
                            <div>
                                <button onclick="togglePermission(${user.id}, this)">
                                    ${user.permission === 'Active' ? 'Deactivate' : 'Activate'}
                                </button>
                            </div>
                        </div>`;
                    });
                    document.getElementById('users-container').innerHTML = html;
                });
        }

        // 自动刷新队列
        function refreshQueue() {
            fetch('/queue_status')
                .then(response => response.json())
                .then(data => {
                    let html = '';
                    
                    // 运行中任务
                    html += `<h3>Running (${data.running.length})</h3>`;
                    data.running.forEach(task => {
                        html += `
                        <div class="task running" data-task-id="${task.id}">
                            ${task.func} 
                            ${task.kwargs.emoji || (task.kwargs.text ? task.kwargs.text.substring(0, 10) : '')}
                            <small>on ${task.device}</small>
                            <button class="delete-btn" onclick="deleteTask('${task.id}')">×</button>
                        </div>`;
                    });

                    // 等待中任务
                    html += `<h3>Pending (${data.pending.length})</h3>`;
                    data.pending.forEach(task => {
                        html += `
                        <div class="task pending ${task.priority === 'High' ? 'high' : ''}" data-task-id="${task.id}">
                            ${task.func} 
                            ${task.kwargs.emoji || (task.kwargs.text ? task.kwargs.text.substring(0, 10) : '')}
                            <small>(${task.priority} priority)</small>
                            <button class="delete-btn" onclick="deleteTask('${task.id}')">×</button>
                        </div>`;
                    });

                    // 已完成任务
                    html += `<h3>Completed (${data.completed.length})</h3>`;
                    data.completed.forEach(task => {
                        html += `
                        <div class="task">
                            ${task.func} 
                            ${task.kwargs.emoji || (task.kwargs.text ? task.kwargs.text.substring(0, 10) : '')}
                            <small>${task.duration.toFixed(1)}s</small>
                        </div>`;
                    });

                    document.getElementById('queue-container').innerHTML = html;

                    // 更新预览
                    const preview = document.getElementById('display-preview');
                    if (data.running.length > 0) {
                        const task = data.running[0];
                        preview.textContent = task.func === 'show_emoji' 
                            ? task.kwargs.emoji 
                            : task.func === 'show_text' 
                                ? task.kwargs.text.substring(0, 3) 
                                : task.func === 'turn_on' ? 'ON' 
                                : task.func === 'turn_off' ? 'OFF' 
                                : task.func === 'sync_time' ? '⏰' 
                                : task.func === 'show_GIF' ? 'GIF' 
                                : '🌀';
                    } else {
                        preview.textContent = '🌀';
                    }
                });
            setTimeout(refreshQueue, 2000);
        }

        // 初始化
        document.addEventListener('DOMContentLoaded', () => {
            refreshQueue();
            document.getElementById('command-select').dispatchEvent(new Event('change'));
        });
    </script>
</body>
</html>"""

# API路由
@app.route('/')
def control_panel():
    return render_template_string(
        CONTROL_PANEL_HTML,
        devices=device_manager.get_devices(),
        queue_status=task_queue.get_queue_status(),
        users=permission_manager.get_users(),
        now=datetime.now()
    )

@app.route('/queue_status')
def get_queue_status():
    status = task_queue.get_queue_status()
    for category in ['pending', 'running', 'completed']:
        for task in status[category]:
            if callable(task.get('func')):
                task['func'] = task['func'].__name__
    return jsonify(status)

@app.route('/toggle_power/<int:device_id>')
def toggle_device_power(device_id):
    """切换设备电源状态"""
    success = device_manager.toggle_power(device_id)
    if success:
        # 更新设备状态后返回最新设备列表
        return jsonify({
            "success": True,
            "devices": device_manager.get_devices()
        })
    return jsonify({
        "success": False,
        "error": "Device not found"
    }), 404


@app.route('/api/command', methods=['POST'])
def handle_command():
    """处理所有6种命令类型"""
    data = request.get_json()
    command_type = data.get('command_type')
    
    if not command_type:
        return jsonify({"error": "Missing command type"}), 400

    func_mapping = {
        'show_emoji': pi_adapter.show_emoji,
        'show_text': pi_adapter.show_text,
        'turn_on': pi_adapter.turn_on,
        'turn_off': pi_adapter.turn_off,
        'sync_time': pi_adapter.sync_time,
        'show_GIF': pi_adapter.show_GIF
    }

    if command_type not in func_mapping:
        return jsonify({"error": "Invalid command type"}), 400

    # 验证必要参数
    if command_type == 'show_emoji' and 'emoji' not in data:
        return jsonify({"error": "Missing emoji"}), 400
    if command_type == 'show_text' and 'text' not in data:
        return jsonify({"error": "Missing text"}), 400

    # 准备任务参数
    kwargs = {}
    if command_type in ['show_emoji', 'show_text']:
        kwargs = {'emoji' if command_type == 'show_emoji' else 'text': data[command_type]}
    
    # 添加任务到队列
    task_id = task_queue.add_task(
        func_mapping[command_type],
        high_priority=data.get('high_priority', False),
        **kwargs
    )

    return jsonify({
        "status": "queued",
        "task_id": task_id,
        "command_type": command_type
    })


@app.route('/api/admin/tasks', methods=['DELETE'])
def admin_remove_task():
    """删除任务（保持原始实现）"""
    data = request.get_json()
    if not data or 'task_id' not in data:
        return jsonify({"error": "Missing task_id"}), 400
        
    success = task_queue.remove_task(data['task_id'])
    return jsonify({"success": success})


@app.route('/api/users')
def get_users():
    """获取用户列表（原始实现）"""
    return jsonify(permission_manager.get_users())


@app.route('/api/users/toggle_permission', methods=['POST'])
def toggle_user_permission():
    """切换用户权限（原始实现）"""
    data = request.get_json()
    if not data or 'user_id' not in data:
        return jsonify({"error": "Missing user_id"}), 400
        
    success = permission_manager.toggle_permission(data['user_id'])
    if success:
        return jsonify({
            "success": True,
            "user": next(
                (u for u in permission_manager.get_users() 
                 if u["id"] == data["user_id"]), 
                None
            )
        })
    return jsonify({"success": False, "error": "User not found"}), 404


def background_worker():
    """后台任务处理器（原始实现）"""
    while True:
        task = task_queue.process_next_task()
        if task:
            try:
                task['func'](**task['kwargs'])
            except Exception as e:
                print(f"Task {task.get('id')} failed: {str(e)}")
            finally:
                if 'device' in task:
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
