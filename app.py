from flask import Flask, request, jsonify
import os
import json
from datetime import datetime
from task_functions import (
    show_emoji,
    show_text,
    show_GIF,
    turn_off,
    turn_on,
    sync_time
)
# python imports
import argparse
import asyncio
import logging

# idotmatrix imports
from core.cmd import CMD

HOME_DIR = os.path.expanduser("~")
LOG_PATH = os.path.join(HOME_DIR, "ICT_Project", "emoji_history.json")

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

@app.route('/', methods=['POST'])
def receive_data():
    data = request.get_json()
    print(f"Received data: {data}")

    try:
        if "emoji" in data:
            emoji_name = data["emoji"]
            response, status = show_emoji(emoji_name)
            log_action(f"[Image] {emoji_name}")
            return jsonify(response), status

        elif "text" in data:
            message = data["text"]
            response, status = show_text(message)
            log_action(f"[Text] {message}")
            return jsonify(response), status

        elif "action" in data:
            action = data["action"]

            if action == "show_gif":
                response, status = show_GIF()
                log_action("[Action] show_gif")
                return jsonify(response), status

            elif action == "turn_off":
                response, status = turn_off()
                log_action("[Action] turn_off")
                return jsonify(response), status

            elif action == "turn_on":
                response, status = turn_on()
                log_action("[Action] turn_on")
                return jsonify(response), status

            elif action == "sync_time":
                response, status = sync_time()
                log_action("[Action] sync_time")
                return jsonify(response), status

            else:
                return jsonify({
                    "status": "error",
                    "message": f"Unknown action: {action}"
                }), 400

        else:
            return jsonify({
                "status": "error",
                "message": "Expected 'emoji', 'text', or 'action' in JSON"
            }), 400

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    print(" Flask server starting on http://0.0.0.0:5000 ...")
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)

def log():
    # set basic logging
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s :: %(levelname)s :: %(name)s :: %(message)s",
        datefmt="%d.%m.%Y %H:%M:%S",
        handlers=[logging.StreamHandler()],
    )
    # set log level of asyncio
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    # set log level of bleak
    logging.getLogger("bleak").setLevel(logging.WARNING)


def main():
    cmd = CMD()
    parser = argparse.ArgumentParser(
        description="control all your 16x16 or 32x32 pixel displays"
    )
    # global argument
    parser.add_argument(
        "--address",
        action="store",
        help="the bluetooth address of the device",
    )
    # add cmd arguments
    cmd.add_arguments(parser)
    # parse arguments
    args = parser.parse_args()
    # run command
    asyncio.run(cmd.run(args))


if __name__ == "__main__":
    log()
    log = logging.getLogger("idotmatrix")
    log.info("initialize app")
    try:
        main()
    except KeyboardInterrupt:
        log.info("Caught keyboard interrupt. Stopping app.")
