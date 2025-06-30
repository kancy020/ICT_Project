from flask import Flask, Blueprint, render_template_string, request, jsonify, redirect, url_for, Response
admin_bp = Blueprint('admin', __name__)
import threading
import time
from datetime import datetime
from admin_panel.managers.device_manager import DeviceManager
from admin_panel.managers.task_queue import TaskQueueManager, TaskPriority
from admin_panel.managers.user_manager import UserManager
from admin_panel.managers.admin_manager import AdminManager

app = Flask(__name__)

# Initialize management components
device_manager     = DeviceManager()
task_queue_manager = TaskQueueManager()
user_manager       = UserManager()
admin_manager      = AdminManager(port=9999)
# If using InterfaceManager:
# from admin_panel.managers.interface_manager import interface_manager
# admin_manager.set_components(interface_manager, task_queue_manager, user_manager, device_manager)

TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Admin Dashboard</title>
  <!-- Bootstrap CSS -->
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
  <nav class="navbar navbar-dark bg-primary">
    <div class="container-fluid">
      <span class="navbar-brand mb-0 h1">Admin Dashboard</span>
      <span class="text-white">Current time: {{ now }}</span>
    </div>
  </nav>
  <div class="container my-4">
    <div class="row gy-4">

      <!-- Device Management -->
      <div class="col-12 col-md-6">
        <h2 class="h4">Device Management</h2>
        <ul class="list-group">
        {% for id, dev in devices.items() %}
          <li class="list-group-item d-flex justify-content-between align-items-center">
            <div><strong>{{ dev['name'] }}</strong> — {{ dev['status'] }}</div>
            <div class="btn-group btn-group-sm">
              <a href="{{ url_for('toggle_device_power', device_id=id) }}" class="btn btn-outline-secondary">Toggle Power</a>
              <a href="{{ url_for('api_disable_device', device_id=id) }}" class="btn btn-outline-warning">Disable</a>
              <a href="{{ url_for('api_remove_device', device_id=id) }}" class="btn btn-outline-danger">Remove</a>
            </div>
          </li>
        {% endfor %}
        </ul>
      </div>

      <!-- User Management -->
      <div class="col-12 col-md-6">
        <h2 class="h4">User Management</h2>
        <ul class="list-group">
        {% for username in users['users'] %}
          <li class="list-group-item d-flex justify-content-between align-items-center">
            <div><strong>{{ username }}</strong>
              <span class="badge bg-{{ 'danger' if username in users['blocked_users'] else 'success' }} ms-2">
                {{ 'Blocked' if username in users['blocked_users'] else 'Active' }}
              </span>
            </div>
            <div class="btn-group btn-group-sm">
              <a href="{{ url_for('api_block_user', username=username) }}" class="btn btn-outline-warning">Block</a>
              <a href="{{ url_for('api_unblock_user', username=username) }}" class="btn btn-outline-success">Unblock</a>
            </div>
          </li>
        {% endfor %}
        </ul>
      </div>

      <!-- Create Task -->
      <div class="col-12">
        <h2 class="h4">Create Task</h2>
        <form class="row g-2" action="{{ url_for('api_create_task') }}" method="post">
          <div class="col-auto">
            <select name="type" class="form-select form-select-sm" required>
              <option value="">-- Select Task Type --</option>
              <option value="emoji">Emoji</option>
              <option value="text">Text</option>
              <option value="timer">Timer</option>
              <option value="control">Control</option>
            </select>
          </div>
          <div class="col-auto">
            <input name="content" class="form-control form-control-sm" placeholder="Enter content" required>
          </div>
          <div class="col-auto form-check">
            <input type="checkbox" name="high_priority" class="form-check-input" id="hp">
            <label class="form-check-label" for="hp">High Priority</label>
          </div>
          <div class="col-auto">
            <button type="submit" class="btn btn-primary btn-sm">Add Task</button>
          </div>
        </form>
      </div>

      <!-- Task Queue -->
      <div class="col-12">
        <h2 class="h4">Task Queue</h2>
        {% for title, lst in [('Pending', waiting), ('Running', executing), ('Completed', completed)] %}
          <h5 class="mt-3">{{ title }} <small class="text-muted">({{ lst|length }})</small></h5>
          <ul class="list-group">
          {% for task in lst %}
            <li class="list-group-item d-flex justify-content-between align-items-center">
              <div>
                <strong>{{ task['user'] or 'admin' }}:</strong>
                {% if task['data']['type']=='emoji' %}
                  <span class="fs-3">{{ task['data']['emoji'] }}</span>
                {% elif task['data']['type']=='text' %}
                  <code>{{ task['data']['text'] }}</code>
                {% elif task['data']['type']=='timer' %}
                  <strong>{{ task['data']['minutes'] }} min</strong>
                {% else %}
                  <em>{{ task['data']['type'] }}</em>
                {% endif %}
              </div>
              {% if title!='Running' %}
                <a href="{{ url_for('api_delete_task') }}?task_id={{task['id']}}" class="btn btn-outline-danger btn-sm">Delete</a>
              {% endif %}
            </li>
          {% endfor %}
          </ul>
        {% endfor %}
      </div>

    </div>
  </div>

  <!-- Bootstrap JS Bundle -->
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
'''

@admin_bp.route('/')
def dashboard():
    return render_template_string(
        TEMPLATE,
        now=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        devices=device_manager.get_all_devices(),
        users=user_manager.get_all_users(),
        waiting=task_queue_manager.get_waiting_tasks(),
        executing=task_queue_manager.get_executing_tasks(),
        completed=task_queue_manager.get_completed_tasks()
    )

@admin_bp.route('/toggle_power/<device_id>')
def toggle_device_power(device_id):
    success = device_manager.toggle_power(device_id)
    return redirect(url_for('dashboard'))

@admin_bp.route('/api/device/disable/<device_id>')
def api_disable_device(device_id):
    device_manager.disable_device(device_id)
    return redirect(url_for('dashboard'))

@admin_bp.route('/api/device/remove/<device_id>')
def api_remove_device(device_id):
    device_manager.remove_device(device_id)
    return redirect(url_for('dashboard'))

@admin_bp.route('/api/user/block/<username>')
def api_block_user(username):
    user_manager.block_user(username)
    return redirect(url_for('dashboard'))

@admin_bp.route('/api/user/unblock/<username>')
def api_unblock_user(username):
    user_manager.unblock_user(username)
    return redirect(url_for('dashboard'))

@admin_bp.route('/api/task/create', methods=['POST'])
def api_create_task():
    ttype = request.form['type']
    content = request.form['content']
    high = 'high_priority' in request.form
    data = {'type': ttype}
    if ttype=='emoji': data['emoji']=content
    if ttype=='text': data['text']=content
    if ttype=='timer': data['minutes']=int(content)
    # control type: extend as needed
    priority = TaskPriority.HIGH if high else TaskPriority.NORMAL
    task_queue_manager.add_task(data, user='admin', priority=priority)
    return redirect(url_for('dashboard'))

@admin_bp.route('/api/task/delete')
def api_delete_task():
    tid = request.args.get('task_id')
    task_queue_manager.remove_task(tid)
    return redirect(url_for('dashboard'))


def register_routes(app):
    """Register all routes for the admin dashboard"""
    if 'admin' not in app.blueprints:
        app.register_blueprint(admin_bp)


if __name__ == '__main__':
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=9999, debug=False), daemon=True).start()
    print("Admin Dashboard running on http://0.0.0.0:9999")
