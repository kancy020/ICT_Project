# admin_panel/common_state.py
from admin_panel.managers.device_manager import DeviceManager
from admin_panel.managers.task_queue import TaskQueueManager
from admin_panel.managers.user_manager import UserManager
from admin_panel.managers.interface_manager import InterfaceManager

device_mgr    = DeviceManager()
task_queue    = TaskQueueManager()
user_mgr      = UserManager()
interface_mgr = InterfaceManager()
