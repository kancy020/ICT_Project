from flask import Flask, render_template_string, request
import threading
import time
from device_manager import DeviceManager
from task_queue import TaskQueue
from user_permission import UserPermissionManager
from command_parser import SlackCommandParser
from task_functions import *

app = Flask(__name__)
device_manager = DeviceManager()
task_queue = TaskQueue(device_manager)
permission_manager = UserPermissionManager()
command_parser = SlackCommandParser()

# [Include all the route definitions and HTML template from the original code here]
# (The routes and template would be copied exactly as they appear in the original)

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
