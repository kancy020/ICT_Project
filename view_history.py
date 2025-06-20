import json
import os

HISTORY_LOG_PATH = os.path.join(os.path.expanduser("~"), "ICT_Project", "emoji_history.json")

if os.path.exists(HISTORY_LOG_PATH):
    with open(HISTORY_LOG_PATH, "r") as f:
        history = json.load(f)

    print("Emoji Display History:\n")
    for entry in history:
        timestamp = entry.get("timestamp", "Unknown Time")
        content = entry.get("content", "Unknown Content")
        user = entry.get("user", "unknown")
        print(f"[{timestamp}] {user} displayed: {content}")
else:
    print("history file found. No emoji display records available.")