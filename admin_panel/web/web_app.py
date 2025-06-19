from flask import Flask, render_template_string, request, jsonify, redirect, url_for
import threading
import time
from datetime import datetime
from admin_panel.managers.device_manager import DeviceManager
from admin_panel.managers.task_queue import TaskQueueManager, TaskPriority
from admin_panel.managers.user_manager import UserManager
from admin_panel.managers.admin_manager import AdminManager
from admin_panel.managers.interface_manager import InterfaceManager

app = Flask(__name__)

# 初始化管理组件
device_manager = DeviceManager()
task_queue = TaskQueueManager()
user_manager = UserManager()
interface_manager = InterfaceManager()
admin_manager = AdminManager()
admin_manager.set_components(interface_manager, task_queue, user_manager, device_manager)

# 页面模板
TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>管理面板</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, sans-serif; margin:20px; }
        h2 { margin-top: 30px; }
        ul { list-style:none; padding:0; }
        li { margin:8px 0; display:flex; align-items:center; }
        .content { flex:1; }
        .btn { margin-left: 10px; }
        form { display:inline; }
    </style>
</head>
<body>
    <h1>管理面板</h1>
    <p>当前时间：{{ now }}</p>

    <h2>设备管理</h2>
    <ul>
    {% for id, dev in devices.items() %}
        <li>
            <div class="content"><strong>{{ dev['name'] }}</strong> ({{ dev['status'] }})</div>
            <form action="/toggle_power/{{ id }}" method="post"><button class="btn">切换电源</button></form>
            <form action="/api/device/disable/{{ id }}" method="post"><button class="btn">禁用</button></form>
            <form action="/api/device/remove/{{ id }}" method="post"><button class="btn">删除</button></form>
        </li>
    {% endfor %}
    </ul>

    <h2>用户管理</h2>
    <ul>
    {% for username in users['users'] %}
        <li>
            <div class="content"><strong>{{ username }}</strong> (禁用: {{ username in users['blocked_users'] }})</div>
            <form action="/api/user/block/{{ username }}" method="post"><button class="btn">禁用</button></form>
            <form action="/api/user/unblock/{{ username }}" method="post"><button class="btn">解禁</button></form>
        </li>
    {% endfor %}
    </ul>

    <h2>创建任务</h2>
    <form action="/api/task/create" method="post">
        <label>类型：
            <select name="type">
                <option value="emoji">Emoji</option>
                <option value="text">文本</option>
                <option value="timer">定时器</option>
            </select>
        </label>
        <label>内容：<input name="content" required placeholder="输入内容"></label>
        <label>高优先：<input type="checkbox" name="high_priority"></label>
        <button type="submit">添加任务</button>
    </form>

    <h2>任务队列</h2>
    {% for title, lst in [('等待执行', queue_waiting), ('正在执行', queue_executing), ('历史记录', queue_completed)] %}
        <h3>{{ title }} ({{ lst|length }})</h3>
        <ul>
        {% for task in lst %}
            <li>
                <div class="content">用户{{ task.user or 'admin' }}：
                    {% if task.data.type=='emoji' %}
                        <span style="font-size:1.5em;">{{ task.data.emoji }}</span>
                    {% elif task.data.type=='text' %}
                        <code>{{ task.data.text }}</code>
                    {% elif task.data.type=='timer' %}
                        <strong>{{ task.data.minutes }} 分钟</strong>
                    {% else %}
                        <em>{{ task.data.type }}</em>
                    {% endif %}
                </div>
                {% if title!='正在执行' %}
                <form action="/api/task/delete" method="post"><input type="hidden" name="task_id" value="{{ task.id }}"><button class="btn">删除</button></form>
                {% endif %}
            </li>
        {% endfor %}
        </ul>
    {% endfor %}
</body>
</html>
'''

@app.route('/')
def dashboard():
    return render_template_string(
        TEMPLATE,
        now=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        devices=device_manager.get_all_devices(),
        users=user_manager.get_all_users(),
        queue_waiting=task_queue.get_waiting_tasks(),
        queue_executing=task_queue.get_executing_tasks(),
        queue_completed=task_queue.get_completed_tasks()
    )

@app.route('/toggle_power/<id>', methods=['POST'])
def toggle_power(id):
    device_manager.send_command_to_device(id, 'turn_on' if device_manager.get_device(id).get('status')!='online' else 'turn_off')
    return redirect(url_for('dashboard'))

@app.route('/api/device/disable/<id>', methods=['POST'])
def disable_device(id):
    device_manager.disable_device(id)
    return redirect(url_for('dashboard'))

@app.route('/api/device/remove/<id>', methods=['POST'])
def remove_device(id):
    device_manager.remove_device(id)
    return redirect(url_for('dashboard'))

@app.route('/api/user/block/<name>', methods=['POST'])
def block_user(name):
    user_manager.block_user(name)
    return redirect(url_for('dashboard'))

@app.route('/api/user/unblock/<name>', methods=['POST'])
def unblock_user(name):
    user_manager.unblock_user(name)
    return redirect(url_for('dashboard'))

@app.route('/api/task/create', methods=['POST'])
def create_task():
    t = request.form.get('type')
    c = request.form.get('content')
    high = 'high_priority' in request.form
    if t=='emoji': data={'type':'emoji','emoji':c}
    elif t=='text': data={'type':'text','text':c}
    elif t=='timer':
        try: data={'type':'timer','minutes':int(c)}
        except: return '无效',400
    else: return '未知类型',400
    task_queue.add_task(data, user='admin', priority=TaskPriority.HIGH if high else TaskPriority.NORMAL)
    return redirect(url_for('dashboard'))

@app.route('/api/task/delete', methods=['POST'])
def delete_task():
    tid = request.form.get('task_id')
    if tid:
        task_queue.remove_task(tid)
    return redirect(url_for('dashboard'))

if __name__=='__main__':
    app.run(host='0.0.0.0', port=9998, debug=True)
