import time
import os
import json
from datetime import datetime
from pixel_adapter import pi_adapter

# Path to save emoji and text display history
HOME_DIR = os.path.expanduser("~")
LOG_PATH = os.path.join(HOME_DIR, "ICT_Project", "emoji_history.json")

# Log every display-related action into a JSON file
def log_action(content):
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "content": content,
        "user": "remote"
    }
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH, "r") as f:
            history = json.load(f)
    else:
        history = []
    history.append(entry)
    with open(LOG_PATH, "w") as f:
        json.dump(history, f, indent=2)
    print(f"Logged: {entry}")

# Display an emoji image by name using pi_adapter
def show_emoji(emoji: str, **kwargs):
    try:
        pi_adapter.show_emoji(emoji, **kwargs)
        log_action(f"[Image] {emoji}")
        return {"status": "ok", "action": "set_image", "emoji": emoji}, 200
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500

# Display plain text on the pixel display
def show_text(text: str, **kwargs):
    try:
        pi_adapter.show_text(text, **kwargs)
        log_action(f"[Text] {text}")
        return {"status": "ok", "action": "set_text", "text": text}, 200
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500

# Simulate showing a GIF (placeholder function)
def show_GIF(**kwargs):
    print("[i] Show GIF display (not implemented)")
    time.sleep(1.5)
    log_action("[GIF] simulated display")
    return {"status": "ok", "action": "show_gif"}, 200

# Simulate turning off the display
def turn_off(**kwargs):
    print("[i] Turning off display")
    time.sleep(1)
    log_action("[Power] display turned off")
    return {"status": "ok", "action": "turn_off"}, 200

# Simulate turning on the display
def turn_on(**kwargs):
    print("[i] Turning on display")
    time.sleep(1)
    log_action("[Power] display turned on")
    return {"status": "ok", "action": "turn_on"}, 200

# Simulate syncing time with system clock
def sync_time(**kwargs):
    print("[i] Syncing time")
    time.sleep(1)
    log_action("[System] time synced")
    return {"status": "ok", "action": "sync_time"}, 200

# Optional: declare exported function names
__all__ = [
    "show_emoji",
    "show_text",
    "show_GIF",
    "turn_off",
    "turn_on",
    "sync_time",
    "log_action"
]
