import os
from flask import Flask, request, Response, jsonify
import threading
import time
import send
import subprocess
from datetime import datetime 

# Initialising the Flask application
app = Flask(__name__)

SLACK_SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET")

@app.route('/slack/events', methods=['POST'])
def slack_events():
    payload = request.get_json()
    if "challenge" in payload:
        return jsonify({"challenge": payload["challenge"]})
    return Response(), 200

@app.route('/slack/command', methods=['POST'])
def slack_command():
    print_log("inside slack command")
    gathering_text = request.form.get('text', '')
    user = request.form.get('user_name')
    print_log(f"gathering_text: '{gathering_text}'")

    split_input = gathering_text.split()
    if len(split_input) > 1:
        emoji_input = split_input[0]
        emoji_input1 = split_input[1]
        if emoji_input == 'coffee' or emoji_input == ':coffee:':
            if emoji_input1.isdigit():
                strToNum = int(emoji_input1)
                threading.Thread(target=coffee_timer, args=(strToNum,)).start()
                return f"{user}: set timer for {strToNum} minutes", 200

    if gathering_text:
        print_log(f"{user}: sent {gathering_text} to the pixel display")
        return f"{user}: sent {gathering_text} to the pixel display"
    else:
        return "No text"

def coffee_timer(minutes=5):
    seconds = minutes * 60
    while seconds:
        mins, secs = divmod(seconds, 60)
        timeformat = f'\r{mins:02d}:{secs:02d}'
        print(timeformat, end='', flush=True)
        time.sleep(1)
        seconds -= 1

# New: Pretty print with timestamp
def print_log(message):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")

def check_if_online():
    while True:
        res = subprocess.call(["ping", "192.168.68.110", "-c1", "-W2", "-q"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)  
        if res == 0:
            time.sleep(10)
        else:
            send.slack_alert("Network connection has been lost to the pixel display")
            while True:
                time.sleep(10)
                res = subprocess.call(["ping", "192.168.68.110", "-c1", "-W2", "-q"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)  
                if res == 0:
                    send.slack_alert("Network is now connected to the pixel display")
                    break

def check_slack_connection():
    while True:
        try:
            response = subprocess.run(["ping", "slack.com", "-c", "1", "-W", "2", "-q"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) 
            if response.returncode == 0:
                print_log("Slack connected")
                time.sleep(10)
            else:
                print_log("Slack disconnected")
                # send.send_emoji("x") 
                time.sleep(10)
        except Exception as e:
            print_log(f"Error checking Slack: {e}")
            # send.send_emoji("x")
            time.sleep(10)

@app.route('/', methods=['GET'])
def test():
    return Response('It works!'), 200

if __name__ == "__main__":
    # send.default_welcome_sign()

    threading.Thread(target=check_if_online, daemon=True).start()
    threading.Thread(target=check_slack_connection, daemon=True).start()

    app.run(debug=True, port=8888)
