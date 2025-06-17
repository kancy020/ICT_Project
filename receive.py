import os
from flask import Flask, request, Response, jsonify
import threading
import time
import send
import subprocess
from datetime import datetime
import json
from task_functions import show_emoji

app = Flask(__name__)
SLACK_SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET")

# State enum
class State():
    ON = 1
    OFF = 2
    SLEEPING = 3
    TIMER = 4

status = State.ON
cancel_event = threading.Event()
timer_thread = None

# Print log with timestamp
def print_log(message):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")

# Log emoji usage to a file
def log_emoji(emoji):
    log_entry = {
        "emoji": emoji,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    try:
        with open("emoji_log.json", "r") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = []
    data.append(log_entry)
    with open("emoji_log.json", "w") as f:
        json.dump(data, f, indent=2)

# Test endpoint
@app.route('/', methods=['GET'])
def test():
    return Response('It works!'), 200

# Receive emoji or text via POST
@app.route('/', methods=['POST'])
def receive_emoji():
    data = request.get_json()
    emoji = data.get("emoji")
    text = data.get("text")

    if emoji:
        print_log(f"Received emoji: {emoji}")
        show_emoji(emoji)
        log_emoji(emoji)
        return jsonify({"status": "emoji received", "emoji": emoji}), 200
    elif text:
        print_log(f"Received text: {text}")
        show_emoji(text)
        return jsonify({"status": "text received", "text": text}), 200
    else:
        return jsonify({"error": "No content provided"}), 400

# Slack URL verification
@app.route('/slack/events', methods=['POST'])
def slack_events():
    payload = request.get_json()
    if "challenge" in payload:
        return jsonify({"challenge": payload["challenge"]})
    return Response(), 200

# Handle Slack slash command
@app.route('/slack/command', methods=['POST'])
def slack_command():
    global status, timer_thread

    gathering_text = request.form.get('text', '')
    user = request.form.get('user_name')
    print_log(f"Command from {user}: '{gathering_text}'")

    split_input = gathering_text.split()

    if len(split_input) > 1:
        emoji_input, emoji_input1 = split_input[0], split_input[1]

        if status != State.TIMER:
            if emoji_input in ['coffee', ':coffee:'] and emoji_input1.isdigit():
                minutes = int(emoji_input1)
                status = State.TIMER
                cancel_event.clear()
                timer_thread = threading.Thread(target=coffee_timer, args=(minutes,))
                timer_thread.start()
                return f"{user}: set timer for {minutes} minutes, to cancel type 'cancel timer'", 200

        if status == State.TIMER:
            if gathering_text == 'cancel timer':
                cancel_event.set()
                if timer_thread:
                    timer_thread.join()
                status = State.ON
                return "Timer cancelled.", 200
            return "Timer is running. Type 'cancel timer' to cancel.", 200

    if gathering_text in ['sleep', ':sleeping_face:']:
        status = State.OFF
        return "The pixel display is sleeping. Type 'awaken' to reactivate."

    if status == State.OFF and gathering_text == 'awaken':
        status = State.ON
        return "Pixel display is now active."

    if status == State.OFF:
        return "The pixel display is sleeping. Type 'awaken' to reactivate."

    if gathering_text:
        print_log(f"{user}: sent {gathering_text} to the pixel display")
        show_emoji(gathering_text)
        log_emoji(gathering_text)
        return f"{user}: sent {gathering_text} to the pixel display"
    else:
        return "No text received"

# Countdown timer with cancel support
def coffee_timer(minutes):
    seconds = minutes * 60
    while seconds:
        if cancel_event.is_set():
            print_log("Timer cancelled.")
            return
        mins, secs = divmod(seconds, 60)
        print(f"\r{mins:02d}:{secs:02d}", end='', flush=True)
        time.sleep(1)
        seconds -= 1
    print_log("Timer completed!")
    send.send_emoji("coffee")

# Check connection to pixel display
def check_if_online():
    while True:
        res = subprocess.call(["ping", "192.168.68.110", "-c1", "-W2", "-q"], stdout=subprocess.DEVNULL)
        if res != 0:
            send.slack_alert("Network connection lost to pixel display")
            while True:
                time.sleep(10)
                res = subprocess.call(["ping", "192.168.68.110", "-c1", "-W2", "-q"], stdout=subprocess.DEVNULL)
                if res == 0:
                    send.slack_alert("Network reconnected to pixel display")
                    break
        time.sleep(10)

# Check connection to Slack
def check_slack_connection():
    while True:
        try:
            response = subprocess.run(["ping", "slack.com", "-c", "1", "-W", "2", "-q"], stdout=subprocess.DEVNULL)
            if response.returncode != 0:
                print_log("Slack disconnected")
                send.send_emoji("x")
            else:
                print_log("Slack connected")
        except Exception as e:
            print_log(f"Error checking Slack: {e}")
            send.send_emoji("x")
        time.sleep(10)

# Start Flask app and background threads
if __name__ == "__main__":
    threading.Thread(target=check_if_online, daemon=True).start()
    threading.Thread(target=check_slack_connection, daemon=True).start()
    app.run(host="0.0.0.0", port=8888, debug=True)
